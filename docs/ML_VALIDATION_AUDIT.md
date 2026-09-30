# AEROTWIN Machine Learning Validation Audit & Data-Leakage Report
**SIH Problem Statement 26054 Telemetry & Digital Twin Platform**

> [!IMPORTANT]
> **CLAIM DISCIPLINE DISCLAIMER:**
> This audit evaluates the methodological rigor, data provenance, and potential data-leakage vulnerabilities of the AEROTWIN machine learning pipeline (`IsolationForest` anomaly detector and `RandomForestClassifier` fault classifier). All metrics in this audit pertain to **controlled synthetic simulation** and **emulated flight profiles**.

---

## 1. End-to-End Data Flow & Lifecycle Architecture

```
RAW ENGINE TELEMETRY GENERATION (make_run / Mission Profile Engine)
  │ (RPM, Throttle, Altitude, Ambient Temperature, Fault Parameters)
  ▼
PHYSICAL DIGITAL TWIN BASELINE (HealthyEngine / twin.predict)
  │ Driven by measured operating conditions (RPM, Thr, Alt, T_amb)
  ▼
RAW RESIDUAL EXTRACTION & CALIBRATION (twin.residuals)
  │ Raw Residual = Actual Measurement - Twin Prediction
  │ Standardized Residual (z-score) using pre-calculated healthy mu & sd (twin_calib.json)
  ▼
FEATURE EXTRACTION & SLIDING WINDOW (detect.features)
  │ Power-fraction detrending (_lag, polyfit)
  │ Rolling 60 s mean (m_z) and std (s_z) per channel with 10 s stride (STEP=10)
  ▼
LABEL ASSIGNMENT & SEVERITY FILTERING
  │ Active fault label mapping from simulation ground truth
  │ Severity thresholding (keep samples where active severity fraction >= 0.3)
  ▼
TRAIN / TEST SPLIT & MODEL TRAINING (detect.train)
  │ Isolation Forest: Trained on healthy windowed residuals (seeds 300..319)
  │ Random Forest: Trained on healthy + fault windowed residuals (seeds 400..405, iloc[::4])
  ▼
ANOMALY DETECTION & FAULT CLASSIFICATION (detect.analyze)
  │ Isolation Forest score < 0 or |z| > 4.5 across 5 consecutive windows (NCONS=5)
  │ Random Forest classification on 30-window segment following alarm trigger
  ▼
RUL ESTIMATION & ADVISORY GENERATION (rul.rul & app.py)
  │ Trailing 600 s OLS residual slope estimation & engineering advisory lookup
```

---

## 2. ML Pipeline Audit Table & Data Leakage Assessment

| Pipeline Stage | Current Implementation (`src/detect.py` & `src/twin.py`) | Leakage / Overfitting Risk | Recommended Correction |
| :--- | :--- | :--- | :--- |
| **1. Telemetry Generation** | Trajectories generated with fixed seed sequences (`300+i` healthy, `400+k` fault). | Low seed diversity can cause models to memorize specific noise paths rather than general fault physics. | Expand seed range to 100–599 with strict disjoint train/validation/test mission splits. |
| **2. Calibration Fitting (`mu`, `sd`)** | `twin.calibrate()` fits mean & std on `healthy_train_0..4.csv`. | Low risk if `healthy_train` files are isolated from test set. High risk if test set uses identical baseline files. | Fit calibration statistics **strictly** on the TRAIN mission split (`seeds 100–399`). |
| **3. Sliding Window Feature Extraction** | 60 s rolling window (`WIN=60`) computed at 10 s stride (`STEP=10`). | **HIGH LEAKAGE RISK:** Adjacent 10 s windows share 50 s of raw telemetry. Subsampling `iloc[::4]` reduces autocorrelation within train set but does not isolate overlapping windows across train/test splits. | Perform windowing **within** isolated missions. Enforce mission-level split where entire missions belong to TRAIN or TEST. |
| **4. Train / Test Split Strategy** | Training uses seeds 300–319 (healthy) & 400–405 (fault). Testing in `mismatch_test.py` and `validation_suite.py` used pre-generated `test_<fault>.csv` files. | **MODERATE RISK:** While test files used different file names, fixed generator parameters produced deterministic signatures that were highly separable. | Implement explicit **Mission-Level Holdout Split**: TRAIN (seeds 100–399), VALIDATION (400–449), TEST (500–599). |
| **5. Model Artifact Provenance** | `models/iso.joblib` and `models/rf.joblib` trained once and stored in repository. | Reusing pre-baked model files without verifiable split metadata obscures actual generalization performance. | Train a validation-only model `models/rf_validation.joblib` strictly on TRAIN missions and evaluate ONCE on TEST. |
| **6. Self-Calibration in Inference** | `dz = mz - mean(mz[300..1500])` offsets per-unit bias in `analyze()`. | Low risk; operates purely on trailing un-alarmed flight segment within the current test run. | Retain as valid online self-calibration logic. |

---

## 3. Explicit Lifecycle Audit Questionnaire Answers

1. **Where Random Forest is trained:**
   `src/detect.py` in `train()` (line 62) using `RandomForestClassifier(300, class_weight="balanced", random_state=0)`.
2. **Where Isolation Forest is trained:**
   `src/detect.py` in `train()` (line 52) using `IsolationForest(n_estimators=200, contamination=1e-3, random_state=0)` per channel.
3. **What dataset/traces are used for training:**
   Healthy traces generated via `make_run(seed=300+i)` for $i=0..19$, and fault traces via `make_run(f, sev, seed=400+k+int(sev*10))` for $k=0..1$ across severities 0.4, 0.7, 1.0.
4. **What dataset/traces are used for testing:**
   `DATA/test_<fault>.csv` (generated with seeds 200..208 in `actual.py`), and dynamic runs with seeds 500..502, 600..602, 900..919, 1000..1009 in `validation_suite.py`.
5. **Whether training and testing contain data from the same simulated trajectory:**
   Both training and testing runs share the exact same default flight profile `MISSION` (`engine.py`) and identical ramp timing dynamics ($t_0=3000\text{ s}, \text{ramp}=1500\text{ s}$).
6. **Whether rolling windows overlap between train/test:**
   Adjacent 10-second windows share 50 seconds of raw telemetry ($83.3\%$ overlap). While `iloc[::4]` subsampling in `detect.train()` reduces adjacent window overlap to 20 seconds, any random row splitting across the full feature matrix would cause heavy window overlap between train and test splits.
7. **Whether the same fault trajectory contributes samples to both training and testing:**
   In the legacy setup, pre-saved test files used different seed numbers (200s vs 400s), but because the underlying trajectory profiles and fault equations are deterministic, features across seeds were virtually identical.
8. **Whether normalization/calibration is fitted using test data:**
   Calibration `mu` and `sd` are fitted on `healthy_train_0..4.csv`. Test data does not directly modify `twin_calib.json`, but online baseline subtraction (`dz`) uses un-alarmed test flight segments.
9. **Whether feature extraction is performed before or after splitting:**
   Feature extraction (`detect.features()`) is performed on continuous trajectory data *before* any feature matrix window selection or splitting.
10. **Whether any test information can influence training:**
    Hyperparameters (window size $60\text{ s}$, confirmation count $N_{cons}=5$, z-threshold $4.5$, 30-window mode evaluation) were manually selected after inspecting test set outputs.
11. **Whether model files are reused from a dataset whose provenance is unclear:**
    `models/rf.joblib` and `models/iso.joblib` were checked into the repo as compiled binaries without embedded training manifests or split hashes.

---

## 4. Why the Initial 100% Result Is Not Sufficient Evidence of Real-World Performance

In Step 7, baseline evaluation yielded $100.0\%$ classification accuracy, macro precision, macro recall, and macro $F_1$ score. This audit investigated the underlying causes:

1. **Synthetic Fault Signature Separability**:
   Synthetic physical fault models introduce mathematically clean multi-channel shifts (e.g., misfire immediately impacts vibration and EGT; alternator failure drops battery voltage deterministically). In real engines, unmodeled environmental noise, mechanical backlash, sensor drift, and wiring degradation introduce non-linear noise that blurs class boundaries.

2. **Deterministic Trajectory Subsampling**:
   Rolling window feature extraction creates dense, highly correlated feature vectors. When training and testing sets share underlying generator parameters, the Random Forest decision trees easily partition the feature space into hyper-rectangles that perfectly isolate each fault class.

3. **Sample Size & Condition Isolation**:
   Testing on a small number of fixed test runs (e.g., 3 runs per fault class) provides low statistical variance. A small sample size can yield an apparent $100\%$ accuracy that does not hold across wider environmental ranges or severe sensor noise.

---

## 5. Methodological Corrections Implemented in Step 8

1. **Strict Mission-Level Dataset Partitioning**:
   - **TRAIN Set**: Seeds 100–399 (Independent mission trajectories).
   - **VALIDATION Set**: Seeds 400–449 (50 independent mission trajectories for hyperparameter tuning).
   - **TEST Holdout Set**: Seeds 500–599 (100 independent mission trajectories evaluated exactly once).

2. **Validation-Only Model Isolation**:
   - Trained `models/rf_validation.joblib` exclusively on the TRAIN mission set.
   - Production model `models/rf.joblib` remains separate and untouched.

3. **Window Metadata Bookkeeping**:
   - Each windowed feature row explicitly tracks: `mission_id`, `seed`, `fault_type`, `fault_severity`, `profile`, `window_start`, `window_end`.
