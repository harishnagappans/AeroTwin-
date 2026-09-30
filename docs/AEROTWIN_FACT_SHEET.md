# AEROTWIN Single Source of Truth Project Fact Sheet
**SIH Problem Statement SIH26054 | Team HYDROVEX**

---

## 1. PROJECT
- **Project Name**: AEROTWIN
- **Full Title**: Digital Twin Telemetry & Predictive Maintenance Platform for MALE UAV Propulsion Systems
- **SIH Problem Statement**: SIH26054
- **Team**: HYDROVEX
- **Repository Domain**: `c:\Users\haris\Desktop\Aerotwin`

---

## 2. PROBLEM
- Continuous in-flight engine health monitoring is critical for Medium-Altitude Long-Endurance (MALE) UAVs.
- Ambient environmental variations (altitude pressure drops, OAT shifts) alter baseline sensor values, causing naive ML models to trigger frequent false alarms.
- Need for real-time anomaly detection, multi-class fault classification, explainable feature attribution, and predictive Remaining Useful Life (RUL) estimation.

---

## 3. SOLUTION
- Combines a first-principles thermodynamic digital twin with machine learning residual analysis.
- Standardized residuals ($z = \frac{x - \hat{x}}{\sigma}$) isolate physical degradation from ambient flight conditions.
- Integrates virtual CAN bus transport, software Virtual ECU state management, 2-stage AI diagnostics, RUL forecasting, and a web-based Aerospace Command Center Ground Control Station (GCS) UI.

---

## 4. ARCHITECTURE
- `Mission Environment` → `Physics Engine` → `Virtual ECU` → `Prototype CAN` → `CAN Decoder` → `Canonical Telemetry` → `Physics Digital Twin` → `Residual Engine` → `Isolation Forest` → `Random Forest` → `XAI` → `RUL` → `Maintenance Advisory` → `Command Center GCS`

---

## 5. INPUT PARAMETERS (13 Channels)
1. `rpm` — Engine Speed (RPM)
2. `throttle` — Pilot Throttle Position (%)
3. `alt` — Pressure Altitude (m)
4. `dT_isa` — Ambient Temperature ISA Offset (°C)
5. `map` — Manifold Absolute Pressure (inHg)
6. `cht` — Cylinder Head Temperature (°C)
7. `egt` — Exhaust Gas Temperature (°C)
8. `oil_t` — Lubrication Oil Temperature (°C)
9. `oil_p` — Lubrication Oil Pressure (bar)
10. `fuel` — Fuel Flow Rate (L/h)
11. `battery_v` — Electrical Bus Voltage (V)
12. `inj_timing` — Electronic Injection Timing (deg BTDC)
13. `vib` — Engine Vibration RMS (g)

---

## 6. FAULT COVERAGE (9 Fault Classes)
1. `cooling` — Cooling System Heat Transfer Loss
2. `oil_pressure` — Lubrication Oil Pressure Loss
3. `misfire` — Cylinder Combustion Misfire
4. `fuel_system` — Fuel Metering System Drift
5. `sensor_drift` — Isolated CHT Thermal Sensor Drift
6. `overheat` — Severe Thermal Runaway
7. `injector_fault` — Electronic Injector Timing Offset
8. `combustion_instability` — Combustion Timing Fluctuation
9. `alternator_failure` — Primary Electrical Power Generation Loss

---

## 7. AI METHODS
- **Anomaly Detector**: `Isolation Forest` (`n_estimators=200`, `contamination=1e-3`) on 60 s rolling mean/std residual features (`m_z`, `s_z`). Requires 5 consecutive windows ($|z| > 4.5$) for alarm confirmation.
- **Fault Classifier**: `Random Forest Classifier` (`n_estimators=300`, `class_weight="balanced"`) evaluating 30-window feature segment post-alarm.
- **Explainable AI (XAI)**: Deviation-based feature attribution ranking top-3 residual z-score channels (`why` string output).

---

## 8. RUL METHOD
- Trailing 600-second Ordinary Least Squares (OLS) linear regression on primary fault channel residual time series.
- Projects time-to-threshold crossing ($z_{fail}$) to calculate RUL in minutes ($RUL_{min}$).

---

## 9. CAN BUS
- **Specification**: AEROTWIN Prototype CAN Protocol (11-bit CAN 2.0B).
- **Frame Identifiers**: `0x100` Engine Primary, `0x101` Thermal, `0x102` Fluids, `0x103` Auxiliary.
- **Frame Rate**: 10 Hz broadcast rate.
- **Verified Metrics**: CAN Classification Agreement = `100.0%`, CAN Transport Latency = `0.10 s`.

---

## 10. MISSION PROFILES
- `CRUISE`: Nominal level flight
- `HIGH_ALTITUDE`: Low ambient pressure & temperature
- `HOT_WEATHER`: ISA +25°C ambient thermal stress
- `ENDURANCE`: 3-hour extended flight
- `RAPID_THROTTLE`: Dynamic transient throttle cycles
- `COMBINED_STRESS`: High altitude + Hot weather + Rapid throttle

---

## 11. VALIDATION METRICS (Clean Mission-Level Holdout)
- **Train Split**: Mission seeds 100–399
- **Validation Split**: Mission seeds 400–449
- **Test Holdout Split**: Mission seeds 500–599 (100 independent test missions)
- **Holdout Accuracy**: `99.84%`
- **Macro F1 Score**: `0.9977`
- **Fault Detection Rate**: `100.0%`
- **Healthy False Alarm Rate**: `0.00 / hr` (over 41.6 flight hours)
- **Cross-Condition Macro F1**: `0.9500`
- **Severity Generalization Accuracy**: `99.82%`
- **Mean Absolute RUL Error**: `0.91 min`
- **RUL Relative Error**: `11.64%`
- **Model Mismatch Tolerance**: `±15%` (0 false alarms/hr)

---

## 12. KNOWN LIMITATIONS
1. Synthetic physics simulation telemetry; no real flight recorder (FDR) dataset used.
2. Software Virtual ECU simulation; prototype CAN protocol (not OEM Rotax CAN IDs).
3. Single-label multi-class output for compound dual faults.
4. RUL 90% Confidence Interval coverage is NOT ESTABLISHED.
5. Extreme sensor noise (3x) degrades static z-score thresholds.
6. Mismatches $\ge \pm 20\%$ increase false alarm rates.
7. No airworthiness certification (FAA/EASA/DGCA).

---

## 13. DEMO
- **Command**: `python src/sih_demo.py --fault injector_fault`
- **Options**: `--fault <fault_name>`, `--realtime`
- **Dashboard**: `streamlit run dashboard/app.py`

---

## 14. FUTURE DEPLOYMENT ROADMAP
- Phase 1: Software Prototype (COMPLETED)
- Phase 2: Hardware-in-the-Loop (HIL) CAN Testbed Integration
- Phase 3: Physical Engine Test Bench Data Recording
- Phase 4: Flight Test Telemetry Replay & Calibration
- Phase 5: Airworthiness Certification Pathway (DO-178C / DO-254)
