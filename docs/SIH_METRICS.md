# AEROTWIN SIH Verified Performance Metrics & Claim Discipline Report
**SIH Problem Statement 26054 Telemetry & Digital Twin Platform**

> [!IMPORTANT]
> **STRICT CLAIM DISCIPLINE DIRECTIVE:**
> All performance metrics presented in this table are derived exclusively from **synthetic mission-level holdout benchmarks** and **controlled simulation experiments**. They represent **prototype performance under synthetic validation**. Do NOT claim flight validation or real-world aircraft certification.

---

| Metric Name | Verified Value | Validation Methodology | Engineering Interpretation | Strict Technical Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **Clean Holdout Classification Accuracy** | **99.84%** | Evaluated on 100 independent mission seeds (500–599) using `models/rf_validation.joblib`. | High separability of synthetic multi-channel fault signatures across independent flight trajectories. | Pertains strictly to synthetic simulation data; unmodeled real-world environmental noise may degrade accuracy. |
| **Clean Holdout Macro F1 Score** | **0.9977** | Macro-averaged F1 across all 10 engine state classes (healthy + 9 fault classes). | Balanced performance across all fault categories without class bias. | Evaluated on balanced synthetic mission distributions. |
| **Healthy False Alarm Rate** | **0.00 / hr** | 20 independent healthy flight missions (41.6 total flight hours). | Zero false alarms under nominal flight operating conditions. | Assumes calibrated sensors and standard ISA ambient noise distributions. |
| **Fault Detection Rate** | **100.0%** | Evaluated across all 9 fault classes under nominal operating conditions. | Every injected fault triggered anomaly detection. | Evaluated at single-fault severity $\ge 0.4$. |
| **Cross-Condition Macro F1** | **0.9500** | Evaluated across High Altitude, Hot Weather, Rapid Throttle, Endurance, and Stress profiles. | Stable performance across dynamic non-cruise flight profiles. | Labeled strictly as **Synthetic cross-condition validation**. |
| **Severity Generalization Accuracy** | **99.82%** | Trained on LOW + MEDIUM severities; tested on HIGH severity runs (and vice-versa). | Classifier learns fundamental fault signature shapes rather than simple magnitude thresholds. | Evaluated within synthetic parameter ranges. |
| **Mean Absolute RUL Error** | **0.91 min** | Trailing OLS regression evaluated at $300\text{ s}$ and $600\text{ s}$ post-alarm with future data hidden. | Mean absolute RUL estimation error of $0.91\text{ min}$ on synthetic failure trajectories. | Evaluated on synthetic linear degradation trends. |
| **RUL Relative Error** | **11.64%** | Absolute error relative to true remaining simulated time to failure. | Relative estimation error stays within $12\%$ over a $12\text{ min}$ failure horizon. | Depends on steady-state degradation assumption. |
| **RUL 90% Confidence Interval Coverage** | **NOT ESTABLISHED** | Comparison of true failure times against estimated 90% CI bounds. | Empirical variance calibration required across multi-seed regression runs. | **NOT ESTABLISHED**; synthetic baseline variance requires empirical tuning. |
| **CAN Classification Agreement** | **100.0%** | Direct telemetry vs CAN-decoded telemetry across 45 test runs. | CAN bus frame quantization and encoding introduce zero diagnostic discrepancy. | Evaluated at 10 Hz nominal CAN frame rate. |
| **CAN Transport Latency** | **0.10 s** | Physical transmission time for 10 Hz CAN frame broadcast. | Deterministic bus transport latency. | Software virtual CAN socket latency. |
| **AI Algorithmic Detection Latency** | **136.56 s** | Rolling window accumulation (60 s) + 5 consecutive window confirmation (50 s) + signal ramp. | Algorithmic detection and confirmation time following fault injection. | CAN transport is NOT responsible for confirmation window delay. |
| **Total Diagnostic Latency** | **136.67 s** | CAN transport latency ($0.10\text{ s}$) + AI detection latency ($136.56\text{ s}$). | Total elapsed time from fault injection to advisory display. | Dominated by confirmation window requirement. |
| **Model Mismatch Tolerance** | **±15%** | Digital twin gain mismatch scaled from -30% to +30%. | 0 false alarms/hour observed up to ±15% mismatch in controlled synthetic validation. | Mismatches $>20\%$ increase false alarm rates due to model drift. |
| **Sensor Noise Robustness (3x)** | **0.0%** | 3.0x nominal Gaussian noise applied to clean holdout test set. | 3.0x noise overwhelms fixed z-score thresholds without adaptive filtering. | Standard thresholds require adaptive noise filtering for extreme noise environments. |
| **Data Leakage Status** | **ELIMINATED** | Strict whole-mission partitioning by seeds (100–399 TRAIN, 400–449 VAL, 500–599 TEST). | Overlapping window leakage eliminated across train/test splits. | Verified via mission ID and window timestamp auditing. |
| **Real Aircraft Validation** | **FALSE** | Ground truth real-world flight test verification. | Platform represents software prototype digital twin system. | **NO REAL AIRCRAFT DATA USED.** |
