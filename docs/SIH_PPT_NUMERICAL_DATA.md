# AEROTWIN Presentation Numerical Claim Audit Sheet
**SIH Problem Statement SIH26054 | Team HYDROVEX**

This document provides an explicit numerical audit of every metric presented in the AEROTWIN slide deck and technical documentation. For each numerical claim, the exact source artifact, validation method, safe compliant wording, and prohibited unsafe wording are specified.

---

| Metric Value | Source Artifact File | Validation Method | Safe Compliant Wording | Prohibited Unsafe Wording |
| :--- | :--- | :--- | :--- | :--- |
| **99.84%** | `results/TRUSTWORTHY_VALIDATION_SUMMARY.json` | Synthetic mission-level holdout (100 test seeds 500–599) using `models/rf_validation.joblib`. | "99.84% accuracy in synthetic mission-level holdout validation" | "99.84% real-world accuracy", "99.84% flight-validated accuracy" |
| **0.9977** | `results/TRUSTWORTHY_VALIDATION_SUMMARY.json` | Macro-averaged F1 across 10 engine state classes on holdout test set. | "Clean holdout macro F1 score of 0.9977" | "Perfect real-world macro F1 score" |
| **100.0%** | `results/clean_mismatch_robustness.csv` | Anomaly detection evaluation across 9 synthetic fault scenarios under nominal conditions. | "100.0% fault detection rate in controlled synthetic fault scenarios" | "100% guaranteed real-world fault detection" |
| **0.00 / hr** | `results/clean_mismatch_robustness.csv` | 20 independent healthy flight missions (41.6 total flight hours). | "0.00 false alarms/hour observed in healthy synthetic holdout missions" | "Guaranteed zero false alarms on operational aircraft" |
| **0.9500** | `results/TRUSTWORTHY_VALIDATION_SUMMARY.json` | Synthetic cross-condition validation across High Alt, Hot, Throttle, Endurance profiles. | "Cross-condition macro F1 of 0.9500 in synthetic cross-condition validation" | "95% real-world operational generalization" |
| **99.82%** | `results/severity_generalization.csv` | Trained on LOW/MED severities; evaluated on HIGH severity synthetic runs. | "99.82% accuracy in synthetic fault-severity generalization experiments" | "Guaranteed arbitrary fault-severity generalization" |
| **0.91 min** | `results/clean_rul_validation.csv` | Trailing OLS regression evaluated at 300 s and 600 s post-alarm with future data hidden. | "Mean absolute RUL error of 0.91 min in synthetic holdout benchmark" | "RUL is guaranteed accurate to 0.91 min in real flight" |
| **11.64%** | `results/clean_rul_validation.csv` | Relative error against true simulated failure crossing time over 12 min horizon. | "Mean relative RUL error of 11.64% in synthetic holdout benchmark" | "Guaranteed 11.6% RUL error bound" |
| **NOT ESTABLISHED** | `results/clean_rul_validation.csv` | Theoretical 90% Confidence Interval coverage calculation. | "RUL 90% CI coverage: not established" | "90% CI coverage is 95%", "Guaranteed confidence bounds" |
| **100.0%** | `results/clean_can_fidelity.csv` | Direct telemetry vs CAN-decoded telemetry across 45 test runs. | "100.0% classification agreement between direct and CAN-decoded telemetry" | "CAN bus guarantees 100% real-world reliability" |
| **0.10 s** | `results/latency_breakdown.csv` | Physical transmission calculation for 10 Hz CAN frame broadcast. | "0.10 s CAN transport latency for 10 Hz frame broadcast" | "0.10 s total system diagnostic latency" |
| **136.56 s** | `results/latency_breakdown.csv` | Window accumulation (60 s) + 5 consecutive confirmation windows (50 s) + signal ramp. | "136.56 s mean AI algorithmic detection & confirmation latency" | "AI detects faults instantly in 0.1 s" |
| **136.67 s** | `results/latency_breakdown.csv` | CAN transport latency (0.10 s) + AI detection latency (136.56 s). | "136.67 s total diagnostic latency from fault injection to advisory display" | "Total flight latency is 0.10 s" |
| **±15%** | `results/clean_mismatch_robustness.csv` | Twin gain mismatch scaled from -30% to +30% on clean holdout. | "0 false alarms/hour observed up to ±15% mismatch in controlled synthetic validation" | "±15% guaranteed model tolerance on real engines" |
| **0.0%** | `results/clean_noise_robustness.csv` | 3.0x nominal Gaussian noise applied to clean holdout test set. | "3.0x noise degrades fixed z-score thresholds (0.0% accuracy without adaptive filtering)" | "Immune to arbitrary 3x sensor noise" |
