# AEROTWIN Final SIH 2026 Presentation Content (12-Slide Deck)
**SIH Problem Statement SIH26054 | Team HYDROVEX**

> [!IMPORTANT]
> **CLAIM DISCIPLINE DIRECTIVE:**
> All presentation slides strictly adhere to technical claim discipline. Metrics are identified as **synthetic mission-level holdout validation** and components are labeled as **prototypes or software simulations**.

---

## SLIDE 1 — TITLE

### AEROTWIN
**Digital Twin Telemetry & Predictive Maintenance Platform for MALE UAV Propulsion Systems**

- **SIH Problem Statement ID**: SIH26054
- **Team Name**: HYDROVEX
- **Category**: Avionics, AI/ML & Propulsion Health Management

---

## SLIDE 2 — PROBLEM STATEMENT

### MALE UAV Propulsion Health Management Challenges

- **In-Flight Engine Monitoring Needs**: Medium-Altitude Long-Endurance (MALE) UAVs perform extended 24+ hour missions where unseen engine degradation risks catastrophic in-flight failure.
- **Environmental Variations vs. Health Degradation**: Altitude pressure drops and ambient temperature shifts cause baseline sensor changes that look like engine faults.
- **Early Anomaly & Fault Detection**: Detecting minor thermal drifts, lubrication drops, or ignition misfires long before critical failure threshold crossing.
- **Remaining Useful Life (RUL)**: Providing pilots and ground crews with precise remaining operational time before threshold failure.
- **Post-Flight Diagnostic Decision Support**: Automating telemetry log processing into actionable maintenance advisories.

---

## SLIDE 3 — OUR SOLUTION

### The AEROTWIN Concept: Physics + Telemetry + AI + Predictive Maintenance

```
[ Mission Environment ] ──► [ Physics Digital Twin ] ──► [ Residual Extraction ] ──► [ AI Diagnostics ] ──► [ RUL & Advisories ]
```

### Why AEROTWIN Combines Physics Digital Twin + AI:
- **Pure ML Flaw**: Black-box ML trained on raw telemetry mistakes high-altitude climbs or hot weather for engine faults.
- **Physics Twin Solution**: Calculates real-time theoretical reference baseline under exact current operating conditions.
- **Residual Engine**: Standardized residuals ($z = \frac{x - \hat{x}}{\sigma}$) remove ambient baseline shifts, enabling zero false alarms up to $\pm 15\%$ twin mismatch.

---

## SLIDE 4 — SYSTEM ARCHITECTURE

### AEROTWIN End-to-End Pipeline Architecture

```
Mission Environment       ──► Evaluates barometric pressure & ISA ambient temperature shifts (Simulation)
      │
      ▼
Physics Engine            ──► Rotax 912 S/ULS-inspired reduced-order thermodynamic model (Simulation)
      │
      ▼
Virtual ECU / FADEC       ──► Software-emulated FADEC state machine & Sensor Health BIST (Prototype)
      │
      ▼
AEROTWIN Prototype CAN    ──► 11-bit CAN bus frame packing (0x100-0x103) at 10 Hz (Prototype Protocol)
      │
      ▼
CAN Decoder               ──► Frame unpacking & canonical telemetry reconstruction
      │
      ▼
Canonical Telemetry       ──► Standardized pandas DataStream schema
      │
      ▼
Physics Digital Twin      ──► Real-time theoretical baseline predictions
      │
      ▼
Residual & Calibration    ──► Standardized z-score residual generation
      │
      ▼
Isolation Forest          ──► Unsupervised anomaly detection & 5-window confirmation check
      │
      ▼
Random Forest             ──► 10-class fault classification (healthy + 9 fault classes)
      │
      ▼
Explainable AI (XAI)      ──► Deviation-based feature attribution breakdown
      │
      ▼
RUL Estimator             ──► Trailing OLS regression time-to-threshold forecasting
      │
      ▼
Maintenance Advisory      ──► Actionable engineering maintenance instructions
      │
      ▼
Command Center GCS        ──► Real-time Streamlit Aerospace Ground Control Station UI
```

---

## SLIDE 5 — DIGITAL TWIN & PHYSICS MODEL

### Physics-Informed Residual Layer

- **Modeled Engine Signals (13 Channels)**: RPM, Throttle, Altitude, Ambient Temp, MAP, CHT, EGT, Oil Temp, Oil Pressure, Fuel Flow, Battery Voltage, Injection Timing, Vibration.
- **Residual Formulation**: $\text{Raw Residual} = \text{Telemetry Measurement} - \text{Twin Baseline Prediction}$
- **Standardization & Calibration**: $z_{col} = \frac{r_{col} - \mu_{col}}{\sigma_{col}}$ using pre-calculated healthy calibration parameters (`twin_calib.json`).
- **Power-Fraction Detrending**: Inline polynomial detrending removes transient throttle lag offsets.
- **Model Identity**: Rotax 912 S/ULS-inspired reduced-order physics model.

---

## SLIDE 6 — AI FAULT DETECTION & XAI

### Two-Stage AI Diagnostic Pipeline & Explainability

1. **Isolation Forest (Anomaly Detector)**:
   - Evaluates windowed residual features (`m_z`, `s_z`).
   - Requires 5 consecutive anomalous windows to confirm alarm ($|z| > 4.5$), preventing false positive spikes.
2. **Random Forest (Fault Classifier)**:
   - 300-tree classifier (`models/rf_validation.joblib`) with balanced class weights.
   - Evaluates 30-window feature segment following alarm trigger.
3. **9 Implemented Fault Classes**:
   1. `cooling` | 2. `oil_pressure` | 3. `misfire` | 4. `fuel_system` | 5. `sensor_drift` | 6. `overheat` | 7. `injector_fault` | 8. `combustion_instability` | 9. `alternator_failure`
4. **Explainable AI (XAI)**:
   - Ranks top-3 residual deviations (e.g., `cht +4.5sigma, oil_t +1.8sigma`).
   - *Limitation Note*: Compound dual-faults output single dominant class with reduced classifier probability.

---

## SLIDE 7 — MISSION & ENVIRONMENTAL SIMULATION

### Flight Profile Generalization

- **Supported Flight Profiles**:
  - `CRUISE`: Standard level cruise flight
  - `HIGH_ALTITUDE`: Low barometric pressure & low ambient temperature
  - `HOT_WEATHER`: ISA +25°C ambient thermal stress
  - `ENDURANCE`: Extended 3-hour flight profile
  - `RAPID_THROTTLE`: Dynamic transient throttle cycles
  - `COMBINED_STRESS`: High altitude + Hot weather + Rapid throttle
- **Environmental Compensation**:
  $\text{Environment} \rightarrow \text{Operating Point} \rightarrow \text{Physics Baseline} \rightarrow \text{Residual} \rightarrow \text{Diagnosis}$
- Prevents ambient thermal shifts from being misclassified as engine faults.

---

## SLIDE 8 — CAN BUS & VIRTUAL ECU INTEGRATION

### Avionics Transport Layer & ECU State Machine

- **Virtual ECU / FADEC (Software Prototype)**:
  - Manages operational state transitions: `OFF` → `STARTING` → `RUNNING` → `FAULT`.
  - Executes Sensor BIST logic and active Diagnostic Trouble Code (DTC) bitmask flags.
- **AEROTWIN Prototype CAN Protocol**:
  - 11-bit CAN frames (`0x100` Engine Primary, `0x101` Thermal, `0x102` Fluids, `0x103` Auxiliary) broadcast at 10 Hz.
- **Verified Avionics Metrics**:
  - **CAN Classification Agreement**: `100.0%`
  - **CAN Bus Transport Latency**: `0.10 s`
  - *Disclaimer*: Software Virtual CAN simulation; not official Rotax CAN identifiers or certified hardware.

---

## SLIDE 9 — RUL ESTIMATION & MAINTENANCE ADVISORIES

### Predictive Remaining Useful Life & Engineering Decision Support

- **Degradation Trend Forecasting**:
  - Trailing 600-second OLS linear regression fits degradation slope on primary fault residual channel.
  - Projects time-to-threshold crossing ($z_{fail}$) to calculate RUL in minutes.
- **Verified RUL Accuracy**:
  - **Mean Absolute RUL Error**: `0.91 min` (in synthetic mission-level holdout benchmark)
  - **Mean Relative Error**: `11.64%`
  - **RUL 90% Confidence Interval Coverage**: `NOT ESTABLISHED` (Requires multi-seed variance calibration)
- **Maintenance Advisories**:
  - Automatically generates actionable maintenance actions and urgency ratings (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).

---

## SLIDE 10 — VALIDATION RESULTS

### Clean Mission-Level Holdout Performance

| Performance Metric | Verified Result | Validation Basis |
| :--- | :--- | :--- |
| **Overall Classification Accuracy** | **99.84%** | Synthetic mission-level holdout (100 test seeds 500–599) |
| **Macro F1 Score** | **0.9977** | Balanced across healthy + 9 fault classes |
| **Fault Detection Rate** | **100.0%** | All synthetic fault runs detected |
| **Healthy False Alarm Rate** | **0.00 / hr** | 20 independent healthy flight missions (41.6 hrs) |
| **Cross-Condition Macro F1** | **0.9500** | Synthetic cross-condition validation across 5 profiles |
| **Severity Generalization Accuracy**| **99.82%** | Trained on LOW/MED; evaluated on HIGH severities |
| **CAN Diagnostic Agreement** | **100.0%** | Direct vs CAN decoded telemetry comparison |
| **Digital Twin Model Mismatch** | **0.00 / hr** | 0 false alarms/hr observed up to ±15% gain error |

---

## SLIDE 11 — LIMITATIONS & DEPLOYMENT PATHWAY

### Technical Limitations & Airworthiness Roadmap

#### Current Technical Limitations:
- **Simulation Scope**: Synthetic physics telemetry; no real flight recorder (FDR) dataset used.
- **Hardware/Protocol Scope**: Software Virtual ECU; prototype CAN protocol (not OEM Rotax CAN IDs).
- **Algorithm Scope**: Single-label compound fault output; RUL 90% CI coverage not established; extreme noise (3x) degrades static thresholds; mismatches $>20\%$ increase false alarms.
- **Certification Scope**: No airworthiness certification; federated learning not implemented; secure telemetry is architectural.

#### Future Deployment Roadmap:
```
Software Prototype ──► Hardware-in-the-Loop ──► Ground Bench Testing ──► Flight Test Telemetry ──► Airworthiness Certification
   (CURRENT)              (HIL CAN Testbed)       (Physical Engine)         (Real UAV Telemetry)     (DO-178C / DO-254)
```

---

## SLIDE 12 — IMPACT & CONCLUSION

### Summary of AEROTWIN Value Proposition

- **End-to-End Synergy**:
  $\text{Physics Digital Twin} + \text{CAN Telemetry} + \text{Virtual ECU} + \text{AI Diagnostics} + \text{XAI} + \text{RUL} + \text{GCS Dashboard}$
- **Core Value**:
  Translates continuous multi-channel engine telemetry into immediate, auditable, and actionable propulsion health intelligence.
- **Final Position**:
  A robust, mathematically sound, software-validated prototype architecture ready for Hardware-in-the-Loop (HIL) testbed integration.

*"From raw telemetry to actionable propulsion health intelligence."*
