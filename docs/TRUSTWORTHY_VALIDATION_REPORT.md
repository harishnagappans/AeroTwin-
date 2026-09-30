# AEROTWIN Trustworthy ML Validation Report & Data-Leakage Audit
**SIH Problem Statement 26054 Telemetry & Digital Twin Platform**

> [!IMPORTANT]
> **CLAIM DISCIPLINE DISCLAIMER:**
> All validation metrics reported in this document are derived from **controlled synthetic simulation** and **emulated flight profile holdouts**. These results represent **synthetic validation**, **simulation-based evaluation**, and **prototype performance**. They DO NOT constitute flight validation, real-world aircraft certification, or operational flight readiness.

---

## A. Dataset Generation
Dataset generation uses the physics-based Rotax 912 S/ULS digital twin combined with synthetic fault injection routines (`make_run()`). Telemetry streams incorporate ambient temperature variations, unit-to-unit calibration offsets, baseline vibration, and channel-specific Gaussian sensor noise.

## B. Mission-Level Dataset Split
To eliminate temporal sliding-window data leakage, telemetry streams are partitioned strictly by entire mission trajectories using independent simulation seeds:
- **TRAIN Set**: Mission seeds 100–399 (Independent mission trajectories).
- **VALIDATION Set**: Mission seeds 400–449 (50 independent mission trajectories).
- **TEST Holdout Set**: Mission seeds 500–599 (100 independent mission trajectories evaluated exactly once).

No overlapping rolling feature windows or telemetry samples from the same mission appear across multiple dataset splits.

## C. Training Methodology
Validation fault classifier `models/rf_validation.joblib` was trained exclusively on feature windows extracted from TRAIN set missions (seeds 100–399). Model hyperparameters ($N_{est}=300$, `class_weight="balanced"`) were held fixed, and no test set telemetry influenced training.

## D. Leakage Audit
- **Sliding Window Overlap**: Corrected by splitting by entire mission IDs rather than individual feature rows.
- **Model Provenance**: Validation model `models/rf_validation.joblib` is isolated from the production binary `models/rf.joblib`.
- **Inference Self-Calibration**: Retained trailing window zero-offset subtraction (`dz`) operating purely on un-alarmed segments within individual test runs.

## E. Holdout Confusion Matrix
The 10x10 fault classifier confusion matrix was generated exclusively on the TEST set (seeds 500–599). Artifacts saved to:
- `results/holdout_confusion_matrix.csv`
- `results/holdout_confusion_matrix.png`

## F. Clean Holdout Accuracy
- **Overall Accuracy**: 99.84%

## G. Macro F1 & Classification Metrics
- **Macro Precision**: 99.85%
- **Macro Recall**: 99.69%
- **Macro F1**: 0.9977
- **Weighted F1**: 0.9984

## H. Synthetic Cross-Condition Validation
Generalization was evaluated across 5 non-cruise mission profiles (HIGH_ALTITUDE, HOT_WEATHER, RAPID_THROTTLE, ENDURANCE, COMBINED_STRESS) generated with independent seeds.

## I. Severity Generalization
Classifier trained on LOW + MEDIUM severity fault runs maintained robust classification accuracy when evaluated on HIGH severity runs and vice-versa. Artifact saved to `results/severity_generalization.csv`.

## J. Compound-Fault Behavior
Under dual-fault compound scenarios (e.g. cooling + overheat, misfire + fuel system), the single-label Random Forest classifier outputs the dominant primary fault while the Isolation Forest anomaly detector flags the event. Output probability distributions indicate increased ambiguity. Artifact saved to `results/compound_fault_validation.csv`.

## K. Sensor Noise Robustness
Evaluated under 1.0x to 3.0x nominal sensor noise multipliers on the clean holdout TEST set. Artifact saved to `results/clean_noise_robustness.csv`.

## L. Model Mismatch Robustness
Evaluated across physics twin gain mismatches from -30% to +30%. The ±15% mismatch tolerance bound holds under independent mission-level holdout testing. Artifact saved to `results/clean_mismatch_robustness.csv`.

## M. RUL Validation Without Data Leakage
RUL estimation was evaluated by truncating telemetry at evaluation time `eval_t` to hide future degradation.
- **RUL MAE**: 0.91 min
- **RUL Relative Error**: 11.64%
- **90% CI Coverage**: 0.0%
Artifact saved to `results/clean_rul_validation.csv`.

## N. Detection Latency Breakdown
Diagnostic latency breakdown:
- **CAN Transport Latency**: 0.10 s
- **AI Algorithmic Detection Latency**: 136.6 s
- **Total Diagnostic Latency**: 136.7 s
Artifact saved to `results/latency_breakdown.csv`.

## O. CAN Diagnostic Fidelity
Direct vs CAN-bus decoded telemetry comparison demonstrated 100% classification agreement and <0.03 sigma residual error. Artifact saved to `results/clean_can_fidelity.csv`.

## P. Limitations
1. Single-label classification does not explicitly output multi-label probability vectors for compound faults.
2. Synthetic simulation models use idealized thermodynamic equations and simplified sensor noise distributions.

## Q. Recommended Future Validation
1. Hardware-in-the-Loop (HIL) CAN testbed validation with physical ECU hardware.
2. Integration of real-world flight test dataset recordings from operational Rotax 912 engines.
