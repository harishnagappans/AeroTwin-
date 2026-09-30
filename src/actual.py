"""Simulated 'real' engine stream = healthy physics + unit offsets + sensor noise + injected faults.
All fault/vibration/noise data is [SYN] synthetic. Labels are returned/saved SEPARATELY from measurements."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from engine import run

DATA = Path(__file__).resolve().parent.parent / "data"
SIGMA = dict(rpm=8, map=0.1, cht=0.8, egt=4, oil_t=0.5, oil_p=0.03, fuel=0.15, vib=0.05, battery_v=0.1, inj_timing=0.2)
FAULTS = ["cooling", "oil_pressure", "misfire", "fuel_system", "sensor_drift", "overheat", "injector_fault", "combustion_instability", "alternator_failure"]


def make_run(fault=None, sev=1.0, t0=3000, ramp_s=1500, seed=0, dT_isa=0.0):
    """Returns (measurements, labels). Detectors must only ever see `measurements`."""
    rng = np.random.default_rng(seed)
    d = run(dT_isa=dT_isa)
    t = d.t.values
    ramp = np.clip((t - t0) / ramp_s, 0, 1) * sev if fault else np.zeros(len(t))
    m = d[["t", "rpm", "thr", "alt", "t_amb", "map", "cht", "egt", "oil_t", "oil_p", "fuel", "battery_v", "inj_timing"]].copy()
    m["vib"] = 0.6 + 0.9 * (d.rpm / 5800) ** 2                                    # [SYN] baseline vibration, mm/s
    for k, s in dict(cht=1.5, egt=5, oil_t=0.8, fuel=0.2).items():                 # [SYN] unit-to-unit offset
        m[k] += rng.normal(0, s)
    if fault == "cooling":
        m.cht += 40 * ramp; m.oil_t += 10 * ramp
    elif fault == "oil_pressure":
        m.oil_p *= 1 - 0.5 * ramp
    elif fault == "misfire":
        m.egt -= 120 * ramp * (rng.random(len(t)) < 0.5)                          # intermittent
        m.vib += 2.5 * ramp; m.rpm += rng.normal(0, 30, len(t)) * ramp
    elif fault == "fuel_system":
        m.fuel *= 1 + 0.25 * ramp; m.egt += 40 * ramp
    elif fault == "sensor_drift":
        m.cht += 25 * ramp                                                         # sensor only: oil_t unaffected
    elif fault == "overheat":
        m.cht += 30 * ramp; m.oil_t += 20 * ramp; m.egt += 50 * ramp
    elif fault == "injector_fault":
        m.inj_timing += 5.0 * ramp; m.fuel += 0.5 * ramp; m.egt += 30 * ramp
    elif fault == "combustion_instability":
        m.rpm += rng.normal(0, 40, len(t)) * ramp; m.vib += 3.0 * ramp; m.cht += 15 * ramp
    elif fault == "alternator_failure":
        m.battery_v -= 3.0 * ramp
    for k, s in SIGMA.items():
        m[k] += rng.normal(0, s, len(t))
    lab = pd.DataFrame({"t": t, "fault": fault or "healthy", "severity": ramp, "active": ramp > 0})
    return m, lab


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    for i, dT in enumerate([-10, 0, 10, 20, 30]):                                  # healthy training set
        make_run(seed=100 + i, dT_isa=dT)[0].to_csv(DATA / f"healthy_train_{i}.csv", index=False)
    for j, f in enumerate(FAULTS):                                                 # test set, one per fault
        m, lab = make_run(f, seed=200 + j)
        m.to_csv(DATA / f"test_{f}.csv", index=False); lab.to_csv(DATA / f"labels_{f}.csv", index=False)
    print("wrote", len(list(DATA.glob("*.csv"))), "files to", DATA)
