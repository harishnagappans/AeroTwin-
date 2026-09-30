"""Layer 5: RUL = time until the fault's primary residual (degradation index) reaches a maintenance threshold.
Linear trend over the trailing 300 s, OLS slope uncertainty -> 90% band. Simple and explainable by design.
Timescale is compressed (synthetic ramps last ~25 min); thresholds are [ASM] engineering assumptions."""
import json
import numpy as np, pandas as pd
from twin import residuals, CALIB
from detect import analyze, load
from actual import FAULTS, DATA

# fault -> (primary channel, sign, maintenance threshold in physical residual units) [ASM]
PRIMARY = {"cooling": ("cht", 1, 30.0), "oil_pressure": ("oil_p", -1, 1.0), "misfire": ("vib", 1, 2.0),
           "fuel_system": ("fuel", 1, 4.0), "sensor_drift": ("cht", 1, 20.0), "overheat": ("cht", 1, 25.0),
           "injector_fault": ("inj_timing", 1, 4.0), "combustion_instability": ("vib", 1, 3.0), "alternator_failure": ("battery_v", -1, 2.5)}


def rul(res, fault, t, sd, span=600, ta=None):
    """Returns dict(health %, rul_s, lo_s, hi_s) at time t. Smooth, realistic, robust to sensor noise."""
    ch, sgn, dfail = PRIMARY[fault]
    
    # Select slice: from alarm onset ta to t if available, else trailing 600s window
    if ta is not None and t > ta + 30:
        m = res[(res.t >= ta) & (res.t <= t)].copy()
    else:
        m = res[(res.t > t - span) & (res.t <= t)].copy()
        
    if len(m) < 5:
        return dict(health=100.0, rul_s=None, lo_s=None, hi_s=None)
        
    # Smooth noisy residual signal using 30s rolling mean
    y_raw = sgn * m[f"z_{ch}"].values * sd[ch]
    y = pd.Series(y_raw).rolling(window=30, min_periods=1).mean().values
    x = m.t.values - t
    
    slope, icpt = np.polyfit(x, y, 1)
    
    # Calculate noise variance and standard error
    y_pred = slope * x + icpt
    resids = y - y_pred
    dof = max(1, len(x) - 2)
    s2 = (resids ** 2).sum() / dof
    x_var = x.var()
    se = np.sqrt(s2 / (len(x) * x_var)) if (x_var > 0 and len(x) > 2) else 0.0
    
    gap = dfail - icpt
    
    # For active alarms, enforce physical minimum degradation slope so RUL doesn't explode
    if ta is not None and t >= ta + 300:
        min_slope = (dfail * 0.4) / 1500.0
        if slope < min_slope:
            slope = min_slope
            
    f = lambda s: 0.0 if gap <= 0 else (gap / s if s > 0 else None)
    
    rul_val = f(slope)
    lo_val = f(slope + 1.64 * se)
    hi_val = f(max(1e-6, slope - 1.64 * se))
    
    # Max realistic horizon cap (45 mins = 2700s) for active structural fault degradation
    if rul_val is not None and ta is not None and t >= ta + 300:
        rul_val = min(2700.0, rul_val)
        if lo_val is not None: lo_val = min(2700.0, lo_val)
        if hi_val is not None: hi_val = min(2700.0, hi_val)
        
    health_pct = 100.0 * (1.0 - np.clip(icpt / dfail, 0.0, 1.0))
    
    return dict(health=health_pct, rul_s=rul_val, lo_s=lo_val, hi_s=hi_val)



def true_fail_time(res, fault, sd):
    ch, sgn, dfail = PRIMARY[fault]
    d = pd.Series(sgn * res[f"z_{ch}"].values * sd[ch]).rolling(120, center=True).mean()
    return None if not (d >= dfail).any() else float(res.t[(d >= dfail).values.argmax()])


if __name__ == "__main__":
    sd = json.loads(CALIB.read_text())["sd"]; models = load()
    print(f"{'fault':13s}{'at':>6s}{'health%':>8s}{'RUL min (90% band)':>24s}{'true min':>10s}  in-band")
    for f in FAULTS:
        m = pd.read_csv(DATA / f"test_{f}.csv"); a = analyze(m, models); res = residuals(m)
        if a["t_alarm"] is None: print(f"{f:13s} no alarm"); continue
        tf = true_fail_time(res, a["fault"] if a["fault"] in PRIMARY else f, sd)
        for off in (300, 600):
            t = a["t_alarm"] + off; r = rul(res, a["fault"], t, sd)
            mn = lambda v: "inf" if v is None else f"{v / 60:.1f}"
            true = None if tf is None else (tf - t) / 60
            ok = "-" if (true is None or r["lo_s"] is None) else ("yes" if r["lo_s"] / 60 <= true <= (r["hi_s"] or 1e9) / 60 else "no")
            print(f"{f:13s}{t:6.0f}{r['health']:8.0f}{mn(r['rul_s']):>10s} ({mn(r['lo_s'])}-{mn(r['hi_s'])}){'':>4s}{'-' if true is None else f'{true:.1f}':>10s}  {ok}")
