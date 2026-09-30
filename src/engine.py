"""Healthy Rotax 912 S/ULS reduced-order twin (Layer 1).
Data tags: [MFR]=manufacturer (OM-912 Ed.4), [DER]=derived, [ASM]=engineering assumption."""
import numpy as np, pandas as pd

# [MFR] prop-curve calibration: rpm, MAP inHg, power kW, torque Nm
CAL = np.array([[4300, 24.0, 38.0, 84.3], [4800, 26.0, 44.6, 88.7], [5000, 26.0, 51.0, 97.4],
                [5500, 27.0, 69.0, 119.8], [5800, 27.5, 73.5, 121.0]])
P_MAX = 73.5
# [MFR] fuel flow vs power (kW -> l/h); idle point is [ASM]
FUEL = np.array([[0, 2.5], [51.0, 18.5], [69.0, 25.0], [73.5, 27.0]])

# [DER] sanity check: P = T*omega must reproduce the manual's power column
_w = 2 * np.pi * CAL[:, 0] / 60
assert np.allclose(CAL[:, 3] * _w / 1000, CAL[:, 2], rtol=0.01), "calibration inconsistent"


def atmosphere(alt_m, dT_isa=0.0):
    """[DER] ISA troposphere -> (ambient K, pressure inHg, density ratio)."""
    T = 288.15 - 0.0065 * alt_m
    p = 29.92 * (T / 288.15) ** 5.2559
    T_amb = T + dT_isa
    return T_amb, p, (p / 29.92) * (288.15 / T_amb)


def torque(rpm, map_inhg, t_amb_k):
    """[DER] interpolate manual torque, scale by MAP; [ASM] T~rpm^2 below 4300, sqrt intake-temp correction."""
    r = np.clip(rpm, CAL[0, 0], CAL[-1, 0])
    t = np.interp(r, CAL[:, 0], CAL[:, 3]) * map_inhg / np.interp(r, CAL[:, 0], CAL[:, 1])
    if rpm < CAL[0, 0]:
        t *= (rpm / CAL[0, 0]) ** 2
    return max(0.0, t * np.sqrt(288.15 / t_amb_k))


def oil_pressure(rpm, oil_t):
    """[MFR] 0.8 bar @<3500 rising to 2-5 bar band above; [ASM] linear ramp + viscosity droop with oil temp."""
    base = 0.8 + 1.2 * (rpm - 1400) / 2100 if rpm < 3500 else 2.0 + 3.0 * (rpm - 3500) / 2300
    return max(0.0, base * np.clip(1 - 0.006 * (oil_t - 90), 0.6, 1.2))


class HealthyEngine:
    TAU_BASE = {"cht": 45.0, "egt": 4.0, "oil": 180.0}  # [ASM] thermal time constants, s

    def __init__(self, t_amb_c=15.0, mismatch=0.0, gain_mismatch=None):
        # mismatch: affects TAU+gain together (worst case, used only in stress tests).
        # gain_mismatch: gain only, TAU untouched (used for the realistic mismatch test).
        gm = mismatch if gain_mismatch is None else gain_mismatch
        self.mismatch = gm
        self.TAU = {k: v * (1 + mismatch) for k, v in self.TAU_BASE.items()}
        self.cht = self.egt = self.oil = t_amb_c

    def step(self, rpm, thr, alt_m, dT_isa=0.0, dt=1.0):
        T_k, p_in, rho = atmosphere(alt_m, dT_isa)
        t_c = T_k - 273.15
        map_in = p_in * (0.30 + 0.62 * thr)
        tq = torque(rpm, map_in, T_k)
        pw = tq * 2 * np.pi * rpm / 60 / 1000
        pf = pw / P_MAX
        fuel = np.interp(pw, FUEL[:, 0], FUEL[:, 1])
        g = 1 + self.mismatch
        ss = {"cht": t_c + 25 + 75 * g * pf * rho ** -0.5,
              "egt": 550 + 250 * g * pf,
              "oil": 60 + 45 * g * pf + 0.5 * (t_c - 15)}
        for k, v in ss.items():
            setattr(self, k, getattr(self, k) + (1 - np.exp(-dt / self.TAU[k])) * (v - getattr(self, k)))
        battery_v = 12.2 if rpm < 1200 else 14.1 - 0.1 * pf
        inj_timing = 15.0 + 10.0 * (rpm / 5800)
        iat = t_c + 5.0 + 8.0 * (map_in / 29.92)
        fuel_p = 3.2 + 0.4 * pf
        alt_i = 12.0 + 18.0 * pf if rpm >= 1200 else 2.0
        wastegate = float(np.clip(100.0 * (1.0 - (map_in / 29.92) * 0.75), 5.0, 95.0))
        return dict(rpm=rpm, thr=thr, alt=alt_m, t_amb=t_c, map=map_in, torque=tq, power=pw,
                    cht=self.cht, egt=self.egt, oil_t=self.oil, oil_p=oil_pressure(rpm, self.oil), fuel=fuel,
                    battery_v=battery_v, inj_timing=inj_timing, iat=iat, fuel_p=fuel_p, alt_i=alt_i, wastegate=wastegate)


# (t_s, rpm, throttle, alt_m) breakpoints: takeoff, climb, cruise, loiter, descent
MISSION = np.array([[0, 5800, 1.0, 0], [300, 5800, 1.0, 300], [1200, 5500, 0.95, 3000],
                    [4800, 5000, 0.75, 3000], [6600, 4300, 0.62, 3000], [7500, 3500, 0.30, 100]])


def run(mission=MISSION, dT_isa=0.0, dt=1.0):
    t = np.arange(0, mission[-1, 0], dt)
    rpm, thr, alt = (np.interp(t, mission[:, 0], mission[:, i]) for i in (1, 2, 3))
    eng = HealthyEngine(15.0 + dT_isa)
    df = pd.DataFrame([eng.step(rpm[i], thr[i], alt[i], dT_isa, dt) for i in range(len(t))])
    df.insert(0, "t", t)
    return df


if __name__ == "__main__":
    for name, d in [("ISA", 0), ("HOT +20C", 20)]:
        df = run(dT_isa=d)
        print(f"{name}: peak CHT {df.cht.max():.0f}C (lim 135) | peak EGT {df.egt.max():.0f}C (lim 880) | "
              f"peak oilT {df.oil_t.max():.0f}C (lim 130) | oilP {df.oil_p.min():.1f}-{df.oil_p.max():.1f} bar | "
              f"fuel {df.fuel.sum() / 3600:.1f} L | peak P {df.power.max():.1f} kW")
    df.to_csv("healthy_mission.csv", index=False)
