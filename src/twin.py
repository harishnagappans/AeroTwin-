"""Layers 2: twin runs on the SAME measured inputs as the engine; residual = actual - predicted.
Twin never sees labels or fault parameters. Vibration baseline is an [ASM] healthy expectation."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from engine import HealthyEngine

ROOT = Path(__file__).resolve().parent.parent
CALIB = ROOT / "models" / "twin_calib.json"
CH = ["map", "cht", "egt", "oil_t", "oil_p", "fuel", "vib", "battery_v", "inj_timing", "iat", "fuel_p", "alt_i", "wastegate"]


def predict(m, mismatch=0.0):
    """Healthy twin driven by measured rpm/throttle/altitude/ambient temp."""
    dT = m.t_amb.values - (15 - 0.0065 * m.alt.values)
    eng = HealthyEngine(m.t_amb.iloc[0], gain_mismatch=mismatch)
    rows = [eng.step(r, th, a, d) for r, th, a, d in zip(m.rpm, m.thr, m.alt, dT)]
    p = pd.DataFrame(rows)[["map", "cht", "egt", "oil_t", "oil_p", "fuel", "battery_v", "inj_timing", "iat", "fuel_p", "alt_i", "wastegate", "power"]]
    p["vib"] = 0.6 + 0.9 * (m.rpm.values / 5800) ** 2
    return p


def raw_residuals(m, mismatch=0.0):
    return m[CH].reset_index(drop=True) - predict(m, mismatch)[CH]


def calibrate(healthy_frames):
    """Healthy residual mean/std per channel (pooled over units and conditions)."""
    r = pd.concat([raw_residuals(m) for m in healthy_frames])
    c = {"mu": r.mean().to_dict(), "sd": r.std().to_dict()}
    CALIB.parent.mkdir(exist_ok=True); CALIB.write_text(json.dumps(c, indent=1))
    return c


def kalman(z, q=1e-3, r=1.0):
    """Scalar random-walk Kalman filter on a normalised residual."""
    x, p, out = z[0], r, np.empty_like(z)
    for i, zi in enumerate(z):
        p += q; k = p / (p + r); x += k * (zi - x); p *= 1 - k; out[i] = x
    return out


def residuals(m, calib=None, mismatch=0.0):
    """Returns DataFrame: t, pf (power fraction), z_<ch>, kf_<ch>."""
    from engine import P_MAX
    c = calib or json.loads(CALIB.read_text())
    p = predict(m, mismatch)
    r = m[CH].reset_index(drop=True) - p[CH]
    out = pd.DataFrame({"t": m.t.values, "pf": (p["power"] / P_MAX).values})
    for ch in CH:
        z = ((r[ch] - c["mu"][ch]) / c["sd"][ch]).values
        out[f"z_{ch}"] = z; out[f"kf_{ch}"] = kalman(z)
    return out


def alarm_time(res, thr=5.0, n=20):
    """First t where any smoothed |z| > thr for n consecutive samples (None if never)."""
    hit = (res[[f"kf_{c}" for c in CH]].abs() > thr).any(axis=1).astype(int)
    run = hit.rolling(n).sum() >= n
    return None if not run.any() else float(res.t[run.idxmax()] - n + 1)


def threshold_time(m):
    """Conventional monitor: manual limits only (CHT 135, EGT 880, oil T 130, oil P low)."""
    low = np.where(m.rpm < 3500, 0.8, 2.0)
    bad = (m.cht > 135) | (m.egt > 880) | (m.oil_t > 130) | (m.oil_p < low)
    return None if not bad.any() else float(m.t[bad.idxmax()])


if __name__ == "__main__":
    from actual import FAULTS, DATA, make_run
    calibrate([pd.read_csv(DATA / f"healthy_train_{i}.csv") for i in range(5)])
    fa = alarm_time(residuals(make_run(seed=999, dT_isa=15)[0]))
    print(f"held-out healthy run: false alarm at {fa}")
    print(f"{'fault':13s} {'t0':>5s} {'twin':>7s} {'threshold':>10s}  lead(min)")
    for f in FAULTS:
        m = pd.read_csv(DATA / f"test_{f}.csv"); t0 = pd.read_csv(DATA / f"labels_{f}.csv").query("active").t.min()
        tw, th = alarm_time(residuals(m)), threshold_time(m)
        lead = "n/a (threshold never)" if th is None else f"{(th - tw) / 60:.1f}"
        fmt = lambda v: "never" if v is None else str(round(v))
        print(f"{f:13s} {t0:5.0f} {fmt(tw):>7} {fmt(th):>10}  {lead}")
