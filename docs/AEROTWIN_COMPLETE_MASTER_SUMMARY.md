# AEROTWIN Complete Engineering & Validation Master Report
**SIH Problem Statement SIH26054 | Team HYDROVEX**

> [!IMPORTANT]
> **COMPREHENSIVE PROJECT DOCUMENTATION:**
> This document details the complete end-to-end engineering, software implementation, machine learning validation, and evidence packaging executed across **Steps 1 through 10** for project **AEROTWIN** (Digital Twin Telemetry & Predictive Maintenance Platform for MALE UAV Propulsion Systems).

---

## 1. Executive Summary

AEROTWIN is a specialized digital twin, real-time CAN bus telemetry transport, and AI-driven predictive maintenance platform designed for Medium-Altitude Long-Endurance (MALE) UAV propulsion systems.

By combining a **first-principles thermodynamic digital twin** (inspired by the Rotax 912 S/ULS engine) with **machine learning anomaly detection on standardized residuals** ($z$-scores), AEROTWIN isolates physical engine degradation from ambient flight variations (altitude pressure drops, OAT temperature shifts).

In clean mission-level holdout validation across 100 independent test missions (seeds 500–599), AEROTWIN achieved an **overall classification accuracy of 99.84%**, a **macro F1 score of 0.9977**, **100% fault detection rate**, **0.00 false alarms/hour** under nominal conditions, and a **Mean Absolute RUL Error of 0.91 minutes**.

---

## 2. Problem Statement & Objectives (SIH26054)

- **Continuous Engine Health Monitoring**: MALE UAVs perform extended 24+ hour missions where in-flight propulsion failure leads to total aircraft loss.
- **The Environmental False Alarm Challenge**: Naive machine learning models trained directly on raw sensor values mistake high-altitude climbs or hot ambient weather for engine health degradation.
- **Objectives**:
  1. Real-time CAN bus telemetry transport and virtual FADEC/ECU simulation.
  2. Physics digital twin baseline calculation under exact current flight conditions.
  3. Two-stage AI anomaly detection (Isolation Forest) and multi-class fault classification (Random Forest).
  4. Explainable AI (XAI) feature attribution.
  5. Remaining Useful Life (RUL) linear trend forecasting.
  6. Aerospace Ground Control Station (GCS) Command Center dashboard.
  7. Rigorous data-leakage auditing and mission-level holdout validation.

---

## 3. Step-by-Step Chronology & Implementation Log

```
STEP 1 ──► STEP 2 ──► STEP 3 ──► STEP 4 ──► STEP 5 ──► STEP 6 ──► STEP 7 ──► STEP 8 ──► STEP 9 ──► STEP 10
Audit      CAN Spec    CAN Transport Virtual ECU  Mission Engine  Dashboard   Robustness  ML Audit   Hardening  SIH Package
```

### Step 1: Architecture Audit & Codebase Baseline Cleanup
- Audited legacy codebase (`src/detect.py`, `src/twin.py`, `src/actual.py`, `src/rul.py`, `src/engine.py`).
- Established strict directory hierarchy: `src/` (core logic), `tests/` (unit tests), `models/` (ML artifacts), `docs/` (documentation), `results/` (validation artifacts), `dashboard/` (web app).

### Step 2: AEROTWIN Prototype CAN Protocol Specification
- Designed custom 11-bit CAN 2.0B frame protocol broadcasting at 10 Hz:
  - `0x100` **ENGINE_PRIMARY**: RPM (16-bit), MAP (16-bit), Throttle (8-bit), Engine State (8-bit).
  - `0x101` **ENGINE_THERMAL**: CHT (16-bit), EGT (16-bit), Oil Temp (16-bit).
  - `0x102` **ENGINE_FLUIDS**: Oil Pressure (16-bit), Fuel Flow (16-bit).
  - `0x103` **ENGINE_AUXILIARY**: Battery Voltage (16-bit), Injection Timing (16-bit), Vibration RMS (16-bit).
- Documented protocol in [`docs/CAN_PROTOCOL.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/CAN_PROTOCOL.md).

### Step 3: CAN Telemetry Transport Layer Integration
- Built [`src/can_protocol.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/can_protocol.py), [`src/can_decoder.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/can_decoder.py), [`src/can_interface.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/can_interface.py), and [`src/telemetry_source.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/telemetry_source.py).
- Implemented `CANSource` reading from python-can `VirtualBus` (in-memory socket for Windows compatibility, SocketCAN on Linux).

### Step 4: Virtual ECU / FADEC Simulation Layer
- Created [`src/virtual_ecu.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/virtual_ecu.py) emulating FADEC operational states (`OFF`, `STARTING`, `RUNNING`, `FAULT`) and Built-In Self-Test (BIST) fault bitmask flags (`ECU_FAULT_COOLING`, `ECU_FAULT_OIL_PRESSURE`, etc.).
- Documented layer in [`docs/VIRTUAL_ECU.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/VIRTUAL_ECU.md).

### Step 5: Mission & Environmental Stress Simulation Engine
- Created [`src/mission_profiles.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/mission_profiles.py) offering 6 flight trajectory profiles (`CRUISE`, `HIGH_ALTITUDE`, `HOT_WEATHER`, `ENDURANCE`, `RAPID_THROTTLE`, `COMBINED_STRESS`).
- Implemented barometric altimeter pressure drops and ISA temperature lapse rate calculations ($T_{amb} = T_0 - L \cdot h$).
- Documented engine in [`docs/MISSION_SIMULATION.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/MISSION_SIMULATION.md).

### Step 6: Full Command Center Integration
- Built interactive Streamlit GCS Command Center Dashboard [`dashboard/app.py`](file:///c:/Users/haris/Desktop/Aerotwin/dashboard/app.py).
- Integrated live telemetry charts, 3D digital twin visualization, CAN packet monitor, virtual ECU state gauges, real-time XAI alerts, and historical flight replay (`MissionReplayer`).

### Step 7: Robustness & Model Mismatch Execution Suite
- Developed [`src/validation_suite.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/validation_suite.py) testing digital twin gain mismatches (-30% to +30%), sensor noise (1x to 3x), sensor bias drift, seed variations, and CAN quantization impact.
- Documented in [`docs/VALIDATION_AND_ROBUSTNESS.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/VALIDATION_AND_ROBUSTNESS.md).

### Step 8: ML Validation Audit, Data-Leakage Fix & Trustworthy Metrics
- Audited training pipeline and documented 11 lifecycle questions in [`docs/ML_VALIDATION_AUDIT.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/ML_VALIDATION_AUDIT.md).
- Created strict **mission-level holdout dataset split**:
  - **TRAIN**: Seeds 100–399 (Whole mission trajectories).
  - **VALIDATION**: Seeds 400–449 (50 independent missions).
  - **TEST Holdout**: Seeds 500–599 (100 independent test missions evaluated once).
- Trained validation-only Random Forest model [`models/rf_validation.joblib`](file:///c:/Users/haris/Desktop/Aerotwin/models/rf_validation.joblib) without touching production binary [`models/rf.joblib`](file:///c:/Users/haris/Desktop/Aerotwin/models/rf.joblib).
- Generated clean 10x10 confusion matrix [`results/holdout_confusion_matrix.png`](file:///c:/Users/haris/Desktop/Aerotwin/results/holdout_confusion_matrix.png) and trustworthy summary [`results/TRUSTWORTHY_VALIDATION_SUMMARY.json`](file:///c:/Users/haris/Desktop/Aerotwin/results/TRUSTWORTHY_VALIDATION_SUMMARY.json).

### Step 9: Final Engineering Hardening & SIH Evidence Package
- Created reproducible benchmark runner [`src/run_sih_benchmark.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/run_sih_benchmark.py) generating [`results/SIH_FINAL_BENCHMARK.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/SIH_FINAL_BENCHMARK.csv) and [`results/SIH_KEY_METRICS.json`](file:///c:/Users/haris/Desktop/Aerotwin/results/SIH_KEY_METRICS.json).
- Created deterministic CLI demo scenario script [`src/sih_demo.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/sih_demo.py) supporting `--fault` selection across all 9 faults.
- Created fault coverage matrix [`results/SIH_FAULT_COVERAGE.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/SIH_FAULT_COVERAGE.csv), requirements traceability matrix [`docs/SIH_REQUIREMENTS_TRACEABILITY.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_REQUIREMENTS_TRACEABILITY.md), and system dataflow traceability table [`docs/SYSTEM_TRACEABILITY.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SYSTEM_TRACEABILITY.md).

### Step 10: Final SIH Presentation & Technical Evidence Package
- Authored 12-slide presentation content [`docs/SIH_FINAL_PPT_CONTENT.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_FINAL_PPT_CONTENT.md).
- Authored numerical claim audit sheet [`docs/SIH_PPT_NUMERICAL_DATA.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_PPT_NUMERICAL_DATA.md) enforcing strict claim discipline.
- Created hardware architecture specification [`docs/SIH_HARDWARE_ARCHITECTURE.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_HARDWARE_ARCHITECTURE.md), Bill of Materials [`docs/SIH_BOM.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_BOM.md), 3-minute live judge demo script [`docs/SIH_3_MINUTE_DEMO_SCRIPT.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_3_MINUTE_DEMO_SCRIPT.md), 30-question Judge Q&A master sheet [`docs/SIH_FINAL_QA.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_FINAL_QA.md), and single source of truth fact sheet [`docs/AEROTWIN_FACT_SHEET.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/AEROTWIN_FACT_SHEET.md).
- Verified full regression test suite (43 unit tests passing in 24.9s).

---

## 4. End-to-End System Architecture

```
[ Mission Environment ]
         │
         ▼
[ Physics Engine ] ──► (Virtual Sensors)
         │
         ▼
[ Virtual ECU / FADEC ]
         │
         ▼
[ AEROTWIN Prototype CAN ] ──► (11-bit CAN Frames 0x100 - 0x103)
         │
         ▼
[ CAN Decoder ]
         │
         ▼
[ Canonical Telemetry ]
         │
         ▼
[ Physics Digital Twin ] ──► (Theoretical Baseline Predictions)
         │
         ▼
[ Residual Engine & Calibration ] ──► (Standardized z-scores)
         │
         ▼
[ Isolation Forest Anomaly Detector ] ──► (Anomaly Score & Alarm Flag)
         │
         ▼
[ Random Forest Fault Classifier ] ──► (10-Class Fault Prediction)
         │
         ▼
[ Explainable AI (XAI) Engine ] ──► (Top-3 Feature Attribution)
         │
         ▼
[ RUL Degradation Estimator ] ──► (Time-to-Threshold Horizon)
         │
         ▼
[ Maintenance Advisory Generator ] ──► (Engineering Action Plan)
         │
         ▼
[ Command Center GCS Dashboard ] ──► (Streamlit Web Interface)
```

---

## 5. Implemented Fault Coverage Matrix (9 Fault Classes)

| Fault Name | Primary Sensor Signatures | Physics Residual Signature | Anomaly Detection | RF Classification | XAI Explanation | RUL Channel | Maintenance Advisory | CAN Tested |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`cooling`** | CHT elevation (+45°C), Oil Temp (+10°C) | `z_cht > +3.0 & z_oil_t > +1.5` | TRUE | TRUE | `cht +4.5sigma, oil_t +1.8sigma` | `cht` | TRUE | TRUE |
| **`oil_pressure`** | Oil Pressure drop (-1.8 bar) | `z_oil_p < -3.0` | TRUE | TRUE | `oil_p -4.2sigma` | `oil_p` | TRUE | TRUE |
| **`misfire`** | Vibration (+3.5 g), EGT drop (-120°C) | `z_vib > +3.0 & z_egt < -2.0` | TRUE | TRUE | `vib +3.8sigma, egt -2.4sigma` | `vib` | TRUE | TRUE |
| **`fuel_system`** | Fuel Flow elevation (+4.5 L/h) | `z_fuel > +3.0` | TRUE | TRUE | `fuel +4.1sigma` | `fuel` | TRUE | TRUE |
| **`sensor_drift`** | CHT isolated drift (+35°C, Oil/EGT normal) | `z_cht > +3.0 & z_oil_t normal` | TRUE | TRUE | `cht +3.9sigma (isolated)` | `cht` | TRUE | TRUE |
| **`overheat`** | CHT severe (+70°C), Oil Temp (+35°C) | `z_cht > +5.0 & z_oil_t > +3.0` | TRUE | TRUE | `cht +6.2sigma, oil_t +3.5sigma` | `cht` | TRUE | TRUE |
| **`injector_fault`** | Inj Timing (+5.0 deg), MAP (+2.0 inHg) | `z_inj_timing > +3.0 & z_map > +1.5` | TRUE | TRUE | `inj_timing +4.0sigma, map +2.1sigma` | `inj_timing` | TRUE | TRUE |
| **`combustion_instability`**| EGT fluctuation (+80°C), MAP (+3.0 inHg) | `z_egt > +2.5 & z_map > +2.0` | TRUE | TRUE | `egt +3.2sigma, map +2.4sigma` | `egt` | TRUE | TRUE |
| **`alternator_failure`**| Battery Voltage drop (-3.5 V) | `z_battery_v < -3.5` | TRUE | TRUE | `battery_v -4.8sigma` | `battery_v` | TRUE | TRUE |

---

## 6. Final Validated Performance Metrics

```text
Clean Holdout Classification Accuracy: 99.84% (evaluating rf_validation.joblib on 100 test seeds 500-599)
Clean Holdout Macro F1 Score: 0.9977
Fault Detection Rate: 100.0%
Healthy False Alarm Rate: 0.00 false alarms / flight hour (over 41.6 flight hours)
Cross-Condition Macro F1: 0.9500 (Synthetic cross-condition validation across 5 flight profiles)
Severity Generalization Accuracy: 99.82% (trained on LOW/MED; evaluated on HIGH severities)
Mean Absolute RUL Error: 0.91 min (evaluated in synthetic holdout benchmark)
Mean Relative RUL Error: 11.64%
RUL 90% Confidence Interval Coverage: NOT ESTABLISHED
CAN Diagnostic Agreement: 100.0% (Direct vs CAN-decoded telemetry comparison)
CAN Transport Latency: 0.10 s (10 Hz nominal broadcast rate)
AI Algorithmic Detection Latency: 136.56 s (including 60s window + 5-consecutive window confirmation)
Total Diagnostic Latency: 136.67 s
Digital Twin Model Mismatch Tolerance: ±15% (0 false alarms/hr observed up to ±15% gain error)
3x Sensor Noise Result: 0.0% (Requires adaptive filtering for extreme noise environments)
Data Leakage Status: ELIMINATED VIA MISSION-LEVEL HOLDOUT SEPARATION
Regression Tests: PASS (All 43 unit tests passing in 24.9s)
```

---

## 7. Complete Project Artifact Index

### Core Source Modules (`src/`)
- [`src/engine.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/engine.py) — Rotax 912 S/ULS-inspired physics engine
- [`src/twin.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/twin.py) — Physics digital twin baseline predictor & residual generator
- [`src/detect.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/detect.py) — Isolation Forest & Random Forest diagnostic pipeline
- [`src/rul.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/rul.py) — OLS linear regression Remaining Useful Life estimator
- [`src/actual.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/actual.py) — Parametric fault injection telemetry runner (`make_run()`)
- [`src/can_protocol.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/can_protocol.py) — AEROTWIN Prototype CAN 11-bit frame packing
- [`src/can_decoder.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/can_decoder.py) — CAN message frame unpacker
- [`src/can_interface.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/can_interface.py) — `python-can` `VirtualBus` abstraction
- [`src/can_simulator.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/can_simulator.py) — Virtual CAN bus message broadcast thread
- [`src/telemetry_source.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/telemetry_source.py) — Telemetry input abstraction (`SyntheticSource`, `CSVSource`, `CANSource`)
- [`src/virtual_ecu.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/virtual_ecu.py) — Virtual ECU / FADEC state machine & BIST logic
- [`src/mission_profiles.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/mission_profiles.py) — Flight profile trajectory generator & `MissionReplayer`
- [`src/validation_suite.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/validation_suite.py) — Step 7 robustness & mismatch execution suite
- [`src/ml_validation_audit.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/ml_validation_audit.py) — Step 8 ML validation audit & holdout builder
- [`src/run_sih_benchmark.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/run_sih_benchmark.py) — Step 9 reproducible benchmark runner
- [`src/sih_demo.py`](file:///c:/Users/haris/Desktop/Aerotwin/src/sih_demo.py) — Step 9 deterministic CLI demo scenario script

### Command Center Dashboard (`dashboard/`)
- [`dashboard/app.py`](file:///c:/Users/haris/Desktop/Aerotwin/dashboard/app.py) — Streamlit GCS Command Center Web Application

### Test Suite (`tests/`)
- [`tests/test_can.py`](file:///c:/Users/haris/Desktop/Aerotwin/tests/test_can.py) — CAN bus encoding & decoding unit tests
- [`tests/test_virtual_ecu.py`](file:///c:/Users/haris/Desktop/Aerotwin/tests/test_virtual_ecu.py) — Virtual ECU state machine unit tests
- [`tests/test_mission_profiles.py`](file:///c:/Users/haris/Desktop/Aerotwin/tests/test_mission_profiles.py) — Mission profile trajectory unit tests
- [`tests/test_robustness_validation.py`](file:///c:/Users/haris/Desktop/Aerotwin/tests/test_robustness_validation.py) — Robustness & mismatch unit tests
- [`tests/test_ml_validation_audit.py`](file:///c:/Users/haris/Desktop/Aerotwin/tests/test_ml_validation_audit.py) — Data-leakage audit unit tests
- [`tests/test_sih_demo.py`](file:///c:/Users/haris/Desktop/Aerotwin/tests/test_sih_demo.py) — SIH demo scenario unit tests

### Documentation Package (`docs/`)
- [`docs/CAN_PROTOCOL.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/CAN_PROTOCOL.md) — CAN protocol specification
- [`docs/VIRTUAL_ECU.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/VIRTUAL_ECU.md) — Virtual ECU / FADEC specification
- [`docs/MISSION_SIMULATION.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/MISSION_SIMULATION.md) — Flight profile simulation guide
- [`docs/VALIDATION_AND_ROBUSTNESS.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/VALIDATION_AND_ROBUSTNESS.md) — Step 7 robustness report
- [`docs/ML_VALIDATION_AUDIT.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/ML_VALIDATION_AUDIT.md) — Step 8 data-leakage audit report
- [`docs/TRUSTWORTHY_VALIDATION_REPORT.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/TRUSTWORTHY_VALIDATION_REPORT.md) — Clean holdout report (Sections A–Q)
- [`docs/SIH_REQUIREMENTS_TRACEABILITY.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_REQUIREMENTS_TRACEABILITY.md) — SIH 26054 requirements traceability
- [`docs/SYSTEM_TRACEABILITY.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SYSTEM_TRACEABILITY.md) — Hardware/software data flow traceability
- [`docs/SIH_DEMO_GUIDE.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_DEMO_GUIDE.md) — Dashboard & CLI judging guide
- [`docs/SIH_METRICS.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_METRICS.md) — Claim-safe metrics report
- [`docs/LIMITATIONS.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/LIMITATIONS.md) — Technical scope & limitations
- [`docs/AEROTWIN_FINAL_ARCHITECTURE.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/AEROTWIN_FINAL_ARCHITECTURE.md) — End-to-end architecture block specification
- [`docs/SIH_JUDGE_TALKING_POINTS.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_JUDGE_TALKING_POINTS.md) — SIH evaluation Q&A guide
- [`docs/SIH_FINAL_PPT_CONTENT.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_FINAL_PPT_CONTENT.md) — 12-slide presentation content
- [`docs/SIH_PPT_NUMERICAL_DATA.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_PPT_NUMERICAL_DATA.md) — Presentation numerical claim audit sheet
- [`docs/SIH_HARDWARE_ARCHITECTURE.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_HARDWARE_ARCHITECTURE.md) — Physical deployment architecture
- [`docs/SIH_BOM.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_BOM.md) — Bill of Materials & cost estimate
- [`docs/SIH_3_MINUTE_DEMO_SCRIPT.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_3_MINUTE_DEMO_SCRIPT.md) — 3-minute judge demo narration script
- [`docs/SIH_FINAL_QA.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/SIH_FINAL_QA.md) — 30-question Judge Q&A master sheet
- [`docs/AEROTWIN_FACT_SHEET.md`](file:///c:/Users/haris/Desktop/Aerotwin/docs/AEROTWIN_FACT_SHEET.md) — Single source of truth fact sheet

### Result Artifacts (`results/`)
- [`results/holdout_confusion_matrix.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/holdout_confusion_matrix.csv) & [`holdout_confusion_matrix.png`](file:///c:/Users/haris/Desktop/Aerotwin/results/holdout_confusion_matrix.png)
- [`results/severity_generalization.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/severity_generalization.csv)
- [`results/compound_fault_validation.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/compound_fault_validation.csv)
- [`results/clean_seed_robustness.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/clean_seed_robustness.csv)
- [`results/clean_noise_robustness.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/clean_noise_robustness.csv)
- [`results/clean_mismatch_robustness.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/clean_mismatch_robustness.csv)
- [`results/clean_rul_validation.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/clean_rul_validation.csv)
- [`results/latency_breakdown.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/latency_breakdown.csv)
- [`results/clean_can_fidelity.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/clean_can_fidelity.csv)
- [`results/TRUSTWORTHY_VALIDATION_SUMMARY.json`](file:///c:/Users/haris/Desktop/Aerotwin/results/TRUSTWORTHY_VALIDATION_SUMMARY.json)
- [`results/SIH_FINAL_BENCHMARK.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/SIH_FINAL_BENCHMARK.csv)
- [`results/SIH_KEY_METRICS.json`](file:///c:/Users/haris/Desktop/Aerotwin/results/SIH_KEY_METRICS.json)
- [`results/SIH_FAULT_COVERAGE.csv`](file:///c:/Users/haris/Desktop/Aerotwin/results/SIH_FAULT_COVERAGE.csv)

---

## 8. Technical Scope & Limitations

1. **Simulation Scope**: Telemetry streams are generated via physical digital twin simulation models. No real flight recorder (FDR) datasets were used.
2. **Software Prototype Scope**: The Virtual ECU is a software state machine (`VirtualECU`), and CAN frames use standard 11-bit identifiers (not official Rotax OEM CAN IDs).
3. **Compound Dual Faults**: Dual faults trigger anomaly alerts, but the Random Forest classifier outputs the dominant single class with reduced confidence.
4. **RUL 90% Confidence Interval Coverage**: Point estimates achieve $0.91\text{ min}$ MAE, but 90% CI coverage is **NOT ESTABLISHED**.
5. **Airworthiness Certification**: AEROTWIN is a research software prototype and is **NOT CERTIFIED** by DGCA/FAA/EASA for flight use.
