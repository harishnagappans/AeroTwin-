"""Robustness test: checks whether the twin's clean numbers survive a realistic gain-only model error
(mismatch=0.15 means the twin's thermal gains are 15% off reality; time constants stay matched, since
tau is identifiable from flight-test step response, unlike gain). Uses the SAME trained iso/rf models,
no retraining -- this is the honesty check for whether results depend on the twin matching reality exactly."""
import numpy as np, pandas as pd
from actual import make_run, FAULTS, DATA
from detect import load, analyze


def run_case(mismatch, models):
    rng = np.random.default_rng(1)
    fa = sum(analyze(make_run(seed=900 + i, dT_isa=float(rng.uniform(-10, 35)))[0], models, mismatch)["t_alarm"] is not None
             for i in range(20))
    rows = []
    for f in FAULTS:
        m = pd.read_csv(DATA / f"test_{f}.csv")
        t0 = pd.read_csv(DATA / f"labels_{f}.csv").query("active").t.min()
        r = analyze(m, models, mismatch)
        rows.append((f, None if r["t_alarm"] is None else round(r["t_alarm"] - t0), r["fault"] == f))
    return fa, rows


if __name__ == "__main__":
    models = load()
    print(f"{'mismatch':>9s}  {'false_alarms/20':>16s}   correctly_classified/9   mean_delay_s (detected)")
    for k in (0.0, 0.15, -0.15, 0.30, -0.30):
        fa, rows = run_case(k, models)
        ok = sum(c for _, _, c in rows)
        delays = [d for _, d, _ in rows if d is not None]
        md = "n/a" if not delays else f"{sum(delays) / len(delays):.0f}"
        print(f"{k:+9.2f}  {fa:16d}   {ok:22d}   {md}")
        if k in (0.15, -0.15):
            for f, d, c in rows:
                if not c:
                    print(f"    misclassified at {k:+.2f}: {f:22s} delay={d}")
