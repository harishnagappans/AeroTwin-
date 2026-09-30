"""Layer 3: anomaly detection (Isolation Forest on healthy residuals) + fault classification (Random Forest).
Detector sees only windowed residual features; labels are used only for classifier training / evaluation."""
import sys, joblib
import numpy as np, pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from actual import make_run, FAULTS, DATA
from twin import residuals, CH, ROOT

WIN, STEP, NCONS = 60, 10, 5            # 60 s window, 10 s stride, 5 consecutive anomalous windows = alarm
MD = ROOT / "models"


TAU_CH = {"cht": 45.0, "egt": 4.0, "oil_t": 180.0}


def _lag(x, tau):
    if tau <= 0:
        return x
    a, out = 1 - np.exp(-1.0 / tau), np.empty_like(x)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = out[i - 1] + a * (x[i] - out[i - 1])
    return out


def features(res):
    win = ((res.t >= 200) & (res.t < 1400)).values
    pf = res.pf.values
    z = res[[f"z_{c}" for c in CH]].copy()
    for c in CH:
        col = f"z_{c}"; pfc = _lag(pf, TAU_CH.get(c, 0.0))
        if win.sum() > 5 and pfc[win].std() > 1e-6:
            b, a = np.polyfit(pfc[win], z[col][win], 1)
        else:
            a, b = (z[col][win].mean() if win.sum() else 0.0), 0.0
        z[col] = z[col] - (a + b * pfc)
    f = pd.concat([z.rolling(WIN).mean().add_prefix("m_"), z.rolling(WIN).std().add_prefix("s_")], axis=1)
    f["t"] = res.t
    f = f.iloc[WIN::STEP].reset_index(drop=True)
    return f[f.t >= 260].reset_index(drop=True)


def first_alarm(flag, t):
    run = pd.Series(flag).rolling(NCONS).sum() >= NCONS
    return None if not run.any() else float(t[run.values.argmax()] - (NCONS - 1) * STEP)


def train():
    rng = np.random.default_rng(0)
    H = [features(residuals(make_run(seed=300 + i, dT_isa=float(rng.uniform(-10, 35)))[0])) for i in range(5)]
    Hc = pd.concat(H)
    iso = {c: IsolationForest(n_estimators=100, contamination=1e-3, random_state=0).fit(Hc[[f"m_z_{c}", f"s_z_{c}"]]) for c in CH}
    X, y = [Hc.drop(columns="t").iloc[::4]], ["healthy"] * len(Hc.iloc[::4])
    for f in FAULTS:
        for sev in (0.5, 1.0):
            m, lab = make_run(f, sev, seed=400 + int(sev * 10), dT_isa=float(rng.uniform(-10, 35)))
            ft = features(residuals(m)); l = lab.set_index("t").loc[ft.t]
            frac = (l.severity / sev).values
            keep = frac >= 0.3
            X.append(ft.drop(columns="t")[keep]); y += [f] * int(keep.sum())
    rf = RandomForestClassifier(100, class_weight="balanced", random_state=0).fit(pd.concat(X), y)
    MD.mkdir(exist_ok=True); joblib.dump(iso, MD / "iso.joblib"); joblib.dump(rf, MD / "rf.joblib")
    return iso, rf


def load():
    return joblib.load(MD / "iso.joblib"), joblib.load(MD / "rf.joblib")


def analyze(m, models=None, mismatch=0.0):
    """meas DataFrame -> dict(t_alarm, fault, why, features, score). Used by dashboard too."""
    iso, rf = models or load()
    f = features(residuals(m, mismatch=mismatch)); X = f.drop(columns="t")
    dec = pd.DataFrame({c: iso[c].decision_function(f[[f"m_z_{c}", f"s_z_{c}"]]) for c in CH})
    score = dec.min(axis=1).values
    flag = (dec < 0).any(axis=1).values | (f[[f"m_z_{c}" for c in CH]].abs() > 4.5).any(axis=1).values
    ta = first_alarm(flag, f.t.values); out = dict(t_alarm=ta, fault=None, why="", features=f, score=score, flag=flag)
    if ta is not None:
        i = int(np.searchsorted(f.t.values, ta)); seg = X.iloc[i:i + 30]
        out["fault"] = pd.Series(rf.predict(seg)).mode()[0]
        mz = seg[[f"m_z_{c}" for c in CH]].mean()
        dz = mz - f.loc[(f.t >= 300) & (f.t < 1500), mz.index].mean()      # remove per-unit offset (self-calibration)
        if out["fault"] in ("cooling", "overheat", "sensor_drift") and abs(dz["m_z_cht"]) > 1.5 \
                and abs(dz["m_z_oil_t"]) < 0.2 * abs(dz["m_z_cht"]) and abs(dz["m_z_egt"]) < 0.2 * abs(dz["m_z_cht"]):
            out["fault"] = "sensor_drift"                                   # CHT moves alone -> sensor, not engine
        top = mz.abs().sort_values(ascending=False).index[:3]
        out["why"] = ", ".join(f"{c[4:]} {mz[c]:+.1f}sigma" for c in top)
    return out


def evaluate(models=None):
    models = models or load(); rng = np.random.default_rng(1)
    ev = n = 0
    for i in range(20):                                                     # false alarms on unseen healthy runs
        r = analyze(make_run(seed=900 + i, dT_isa=float(rng.uniform(-10, 35)))[0], models)
        ev += r["t_alarm"] is not None; n += 1
    print(f"healthy runs with false alarm: {ev}/{n}  (each run = 2.08 flight h)")
    print(f"\n{'fault':13s}{'t0':>5s}{'alarm':>7s}{'delay_s':>8s}  {'classified':13s} why")
    for f in FAULTS:
        m = pd.read_csv(DATA / f"test_{f}.csv"); t0 = pd.read_csv(DATA / f"labels_{f}.csv").query("active").t.min()
        r = analyze(m, models); ta = r["t_alarm"]
        print(f"{f:13s}{t0:5.0f}{'-' if ta is None else round(ta):>7}{'-' if ta is None else round(ta - t0):>8}  {str(r['fault']):13s} {r['why']}")
    sevs = (0.1, 0.2, 0.3, 0.5, 1.0)
    print("\ndetection rate vs severity (3 seeds):  " + "  ".join(f"{s:>4}" for s in sevs))
    for f in FAULTS:
        row = []
        for s in sevs:
            hits = sum(analyze(make_run(f, s, seed=600 + k, dT_isa=float(rng.uniform(-10, 35)))[0], models)["t_alarm"] is not None for k in range(3))
            row.append(f"{hits}/3")
        print(f"  {f:13s}" + "  ".join(f"{x:>4}" for x in row))


if __name__ == "__main__":
    models = train() if ("train" in sys.argv or not (MD / "iso.joblib").exists()) else load()
    evaluate(models)
