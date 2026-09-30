# AEROTWIN System Traceability Matrix
**SIH Problem Statement 26054 Telemetry & Digital Twin Platform**

This document traces sensor input data from raw signal generation through CAN encoding, physics twin estimation, residual extraction, ML feature generation, fault diagnosis, RUL estimation, and user interface display.

---

## Complete Signal Data Flow Traceability

| Sensor / Physical Input | CAN Message ID | CAN Decoder Field | Canonical Telemetry Field | Physics Twin Baseline Model | Residual Signal (`z_col`) | ML Feature (`m_z` / `s_z`) | AI Diagnosis & XAI Output | RUL Degradation Channel | Dashboard Display Widget |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Engine Tachometer** (Hall sensor) | `0x100` (ENGINE_PRIMARY) | `rpm` | `rpm` | Input variable `rpm` | N/A (Driving input) | N/A | Operational state condition | N/A | `RPM Gauge` |
| **Manifold Pressure Sensor** (MAP) | `0x100` (ENGINE_PRIMARY) | `map` | `map` | Input variable `map` | `z_map` | `m_z_map`, `s_z_map` | Misfire / Injector Fault | N/A | `MAP Telemetry Chart` |
| **Cylinder Head Temp** (Thermocouple) | `0x101` (ENGINE_THERMAL) | `cht` | `cht` | Thermal mass heat balance $Q_{in} - Q_{cool}$ | `z_cht` | `m_z_cht`, `s_z_cht` | Cooling / Overheat / Sensor Drift (`cht +4.5sigma`) | `cht` | `CHT Temperature Gauge & Residual Plot` |
| **Exhaust Gas Temp** (K-Type Thermocouple) | `0x101` (ENGINE_THERMAL) | `egt` | `egt` | Polytropic expansion $T_{amb} \cdot (p_{ratio})^{(\gamma-1)/\gamma}$ | `z_egt` | `m_z_egt`, `s_z_egt` | Misfire / Combustion Instability (`egt -2.4sigma`) | `egt` | `EGT Exhaust Plot` |
| **Oil Pressure Sensor** (Piezoresistive) | `0x102` (ENGINE_FLUIDS) | `oil_p` | `oil_p` | Linear engine speed relation $p_0 + k \cdot rpm$ | `z_oil_p` | `m_z_oil_p`, `s_z_oil_p` | Lubrication Pressure Loss (`oil_p -4.2sigma`) | `oil_p` | `Oil Pressure Warning Metric` |
| **Oil Temp Sensor** (RTD) | `0x102` (ENGINE_FLUIDS) | `oil_t` | `oil_t` | Coupled CHT heat dissipation model | `z_oil_t` | `m_z_oil_t`, `s_z_oil_t` | Cooling / Overheat (`oil_t +1.8sigma`) | `oil_t` | `Oil Temperature Indicator` |
| **Fuel Flow Meter** (Turbine sensor) | `0x102` (ENGINE_FLUIDS) | `fuel` | `fuel` | BSFC power fraction curve $P \cdot BSFC$ | `z_fuel` | `m_z_fuel`, `s_z_fuel` | Fuel System Drift (`fuel +4.1sigma`) | `fuel` | `Fuel Flow Meter Widget` |
| **Engine Vibration** (Piezo Accelerometer) | `0x103` (ENGINE_AUXILIARY) | `vib` | `vib` | Baseline mechanical vibration amplitude | `z_vib` | `m_z_vib`, `s_z_vib` | Cylinder Misfire (`vib +3.8sigma`) | `vib` | `Vibration RMS Graph` |
| **Bus Voltage** (ECU ADC sense) | `0x103` (ENGINE_AUXILIARY) | `battery_v` | `battery_v` | Nominal 14.0 V DC alternator output | `z_battery_v` | `m_z_battery_v`, `s_z_battery_v` | Alternator Failure (`battery_v -4.8sigma`) | `battery_v` | `Electrical System Metric` |
| **Injector Timing** (Hall crank sensor) | `0x103` (ENGINE_AUXILIARY) | `inj_timing` | `inj_timing` | Advanced injection timing map | `z_inj_timing` | `m_z_inj_timing`, `s_z_inj_timing` | Injector Fault (`inj_timing +4.0sigma`) | `inj_timing` | `ECU Injection Timing Widget` |
| **Pressure Altitude** (Barometric altimeter) | N/A (Flight Env) | N/A | `alt` | ISA Barometric pressure correction $p(h)$ | N/A | N/A | Environmental condition scaling | N/A | `Altitude Indicator` |
| **Ambient Temperature** (OAT sensor) | N/A (Flight Env) | N/A | `dT_isa` | Standard Atmosphere offset $T_{amb} - T_{ISA}$ | N/A | N/A | Thermal baseline shift compensation | N/A | `OAT Offset Meter` |
| **Pilot Throttle Lever** (TPS potentiometer) | `0x100` (ENGINE_PRIMARY) | `throttle` | `throttle` | Power fraction $PF = f(throttle, rpm)$ | N/A | N/A | Digital Twin driver input | N/A | `Throttle Position Bar` |

---

## Pipeline Execution Stages

```
1. Physical Sensor Sampling (10 Hz)
   │
   ▼
2. CAN Frame Packing (0x100 - 0x103)
   │
   ▼
3. CANDecoder Unpacking -> Canonical Telemetry DataFrame
   │
   ▼
4. Physics Digital Twin (twin.predict) -> Theoretical Baseline
   │
   ▼
5. Residual Engine (twin.residuals) -> Standardized z-scores
   │
   ▼
6. Feature Extractor (detect.features) -> Rolling 60s Mean & Std
   │
   ▼
7. Anomaly Detector (Isolation Forest) -> Anomaly Score & Trigger Flag
   │
   ▼
8. Fault Classifier (Random Forest) -> Predicted Fault Class & XAI Explanation
   │
   ▼
9. RUL Estimator (rul.rul) -> OLS Slope & RUL (minutes)
   │
   ▼
10. Command Center Dashboard (app.py) -> Real-Time Telemetry & Advisory Display
```
