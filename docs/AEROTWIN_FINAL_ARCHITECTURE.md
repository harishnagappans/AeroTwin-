# AEROTWIN Final Architecture Specification
**SIH Problem Statement 26054 Telemetry & Digital Twin Platform**

---

## Complete End-to-End System Block Diagram

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

## Detailed Component Specifications

### 1. Mission Environment
- **Input**: Mission Profile type (CRUISE, HIGH_ALTITUDE, HOT_WEATHER, ENDURANCE, RAPID_THROTTLE, COMBINED_STRESS), random seed, flight duration.
- **Processing**: Evaluates barometric pressure formula $p(h)$, temperature lapse rate $T(h) = T_0 - L \cdot h$, and dynamic throttle profile.
- **Output**: Ambient temperature ($T_{amb}$), pressure altitude ($h$), density ratio ($\rho/\rho_0$), pilot throttle command.
- **Purpose**: Provides environmental and operational flight conditions driving engine simulation.

### 2. Physics Engine
- **Input**: Environmental parameters ($T_{amb}, h$), throttle lever position, fault injection controls (fault type, severity).
- **Processing**: Simulates Rotax 912 S/ULS thermodynamic equations, polytropic expansion, friction torque, thermal mass dissipation, and fault deviations.
- **Output**: Raw physical telemetry (RPM, CHT, EGT, Oil P, Oil T, MAP, Fuel Flow, Vibration, Battery V, Inj Timing).
- **Purpose**: Generates high-fidelity ground truth engine physical sensor signals.

### 3. Virtual ECU / FADEC
- **Input**: Raw physical telemetry signals, fault state indicators.
- **Processing**: Executes ECU state machine (`OFF`, `STARTUP`, `RUNNING`, `FAULT_DEGRADED`), performs Sensor BIST checks, and applies sensor range validation.
- **Output**: ECU health flags, active DTC diagnostic fault codes, validated telemetry buffer.
- **Purpose**: Emulates electronic FADEC engine control unit logic and diagnostic trouble code generation.

### 4. AEROTWIN Prototype CAN Protocol
- **Input**: Validated telemetry dictionary from Virtual ECU.
- **Processing**: Packs physical floating-point signals into standard 8-byte CAN data frames using 11-bit IDs (`0x100` Engine Primary, `0x101` Thermal, `0x102` Fluids, `0x103` Auxiliary).
- **Output**: Encoded CAN bus message frames broadcast over memory socket / virtual CAN bus.
- **Purpose**: Standardizes avionics bus transport using industrial CAN bus frame structures.

### 5. CAN Decoder
- **Input**: 11-bit CAN frame payloads (`can.Message` / byte arrays).
- **Processing**: Unpacks bit-fields, applies signal scale/offset factors, and validates signal boundaries.
- **Output**: Reconstructed decoded sensor value dictionary.
- **Purpose**: Recovers physical telemetry values from CAN avionics bus messages.

### 6. Canonical Telemetry
- **Input**: Decoded sensor values from CAN Decoder.
- **Processing**: Formats signals into standardized pandas DataFrame schema indexed by timestamp `t`.
- **Output**: Canonical Telemetry DataStream.
- **Purpose**: Provides clean, uniformly formatted input to the digital twin and diagnostic pipeline.

### 7. Physics Digital Twin
- **Input**: Operating driver variables (RPM, Throttle, MAP, Ambient Temperature, Altitude).
- **Processing**: Computes theoretical nominal engine baseline predictions ($\hat{x}$) using first-principles heat transfer and thermodynamic equations.
- **Output**: Predicted baseline sensor signals ($\hat{T}_{cht}, \hat{T}_{egt}, \hat{P}_{oil}, \hat{F}_{fuel}$, etc.).
- **Purpose**: Serves as the nominal reference baseline representing a healthy engine under identical operating conditions.

### 8. Residual Engine & Calibration
- **Input**: Measured telemetry ($x$) and Digital Twin baseline ($\hat{x}$).
- **Processing**: Computes raw residuals ($r = x - \hat{x}$) and normalizes using healthy baseline calibration ($z = \frac{r - \mu}{\sigma}$). Applies power-fraction detrending.
- **Output**: Standardized residual z-scores ($z_{cht}, z_{egt}, z_{oil\_p}$, etc.).
- **Purpose**: Isolates engine health anomalies by eliminating ambient environmental and operating point variations.

### 9. Isolation Forest Anomaly Detector
- **Input**: Rolling 60-second windowed residual features (`m_z`, `s_z`).
- **Processing**: Evaluates Isolation Forest anomaly score ($score < 0$) and hard threshold checks ($|z| > 4.5$) across 5 consecutive windows.
- **Output**: Binary anomaly flag (`flag`), anomaly trigger timestamp ($t_{alarm}$).
- **Purpose**: Provides ultra-low false-alarm anomaly detection without requiring prior fault labels.

### 10. Random Forest Fault Classifier
- **Input**: 30-window feature segment following anomaly trigger.
- **Processing**: Evaluates 300-tree Random Forest classifier (`rf.joblib` / `rf_validation.joblib`) with balanced class weights.
- **Output**: Multi-class fault prediction (`cooling`, `oil_pressure`, `misfire`, etc.) and probability vector.
- **Purpose**: Classifies specific engine failure modes from windowed residual feature signatures.

### 11. Explainable AI (XAI) Engine
- **Input**: Segment residual mean values (`m_z`).
- **Processing**: Ranks residual channels by absolute z-score magnitude ($|z|$) and computes online self-calibration zero-offset subtraction (`dz`).
- **Output**: Human-readable feature attribution breakdown (e.g. `cht +4.5sigma, oil_t +1.8sigma`).
- **Purpose**: Provides transparent, auditable feature attribution explaining why the AI raised a specific fault alert.

### 12. RUL Degradation Estimator
- **Input**: Standardized residual time series for primary fault channel, baseline calibration variance (`SD_CALIB`).
- **Processing**: Applies trailing 600-second OLS linear regression to estimate degradation slope ($m$) and projects time until threshold crossing ($z_{fail}$).
- **Output**: Estimated Remaining Useful Life in minutes ($RUL_{min}$) and 90% confidence interval.
- **Purpose**: Forecasts remaining flight time before catastrophic failure threshold crossing.

### 13. Maintenance Advisory Generator
- **Input**: Predicted fault class, RUL estimate, XAI top features.
- **Processing**: Maps fault class to engineering action plan, urgency level (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), and inspection procedures.
- **Output**: Structured Maintenance Advisory.
- **Purpose**: Translates AI telemetry alerts into actionable maintenance instructions for flight crews and ground engineers.

### 14. Command Center GCS Dashboard
- **Input**: Telemetry DataStream, Digital Twin baselines, Anomaly flags, RF predictions, XAI features, RUL estimates, Advisories.
- **Processing**: Renders interactive Streamlit UI, Plotly real-time telemetry graphs, 3D twin status visuals, and ECU state gauges.
- **Output**: Web-based Aerospace Ground Control Station (GCS) user interface.
- **Purpose**: Delivers real-time operational situation awareness to pilots, ground engineers, and fleet operators.
