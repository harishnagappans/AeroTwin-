# AEROTWIN Next-Gen Subsystem Specification & Telemetry Protocol

## Executive Overview
This document specifies the enlarged **13-Channel Physical Telemetry Architecture** and **AEROTWIN Prototype CAN Protocol Specification** for the Rotax 912 S/ULS Digital Twin system, complying with Smart India Hackathon (SIH) Problem Statement 26054 requirements.

---

## 1. Complete 13-Channel Physical Parameter Matrix

| Channel Symbol | Parameter Description | Physical Unit | Nominal Range | Sensor Type & Location | Fault Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `rpm` | Engine Crankshaft Speed | RPM | 1400 – 5800 RPM | Inductive Pickup (Flywheel) | Combustion Instability, Misfire |
| `map` | Manifold Absolute Pressure | inHg | 20.0 – 28.5 inHg | Piezoresistive MAP Sensor | Turbo Leak, Altitude Loss |
| `cht` | Cylinder Head Temperature | °C | 60.0 – 115.0 °C | Thermocouple (Cylinder 2/3) | Cooling Failure, Overheat |
| `egt` | Exhaust Gas Temperature | °C | 550.0 – 850.0 °C | K-Type Thermocouple (Header) | Misfire, Fuel System Drift |
| `oil_t` | Engine Oil Temperature | °C | 50.0 – 95.0 °C | PT100 Resistance Thermometer | Cooling Failure, Lube Breakdown |
| `oil_p` | Lubrication Oil Pressure | bar | 2.0 – 6.0 bar | Piezoresistive Pressure Transducer | Oil Pump Wear, Valve Relief |
| `fuel` | Fuel Mass Flow Rate | L/h | 2.5 – 27.0 L/h | Turbine Flow Meter | Fuel Line Leak, Injector Clog |
| `fuel_p` | Fuel Rail Pressure | bar | 2.5 – 4.5 bar | High-Pressure Rail Sensor | Fuel Pump Failure, Vapor Lock |
| `iat` | Intake Air Temperature | °C | 15.0 – 45.0 °C | Intake Manifold NTC Sensor | Density Altitude Loss, Intercooler |
| `vib` | Vibration Spectrum RMS | mm/s | 0.6 – 1.8 mm/s | Tri-Axial Accelerometer | Bearing Wear, Misfire |
| `battery_v` | Avionics DC Bus Voltage | V | 13.8 – 14.2 V | Voltage Divider / ADC | Battery Degradation |
| `alt_i` | Alternator Charging Current | A | 10.0 – 35.0 A | Hall-Effect Current Transducer | Alternator Stator Breakdown |
| `inj_timing` | Electronic Injection Timing | deg BTDC | 15.0 – 25.0° | ECU Optical Shaft Encoder | ECU Driver Drift, Misfire |
| `wastegate` | Turbo Wastegate Position | % | 5.0 – 95.0 % | Servo Feedback Potentiometer | Turbo Wastegate Binding |

---

## 2. CAN Bus Message Payload Specification (11-Bit Standard Frame)

AEROTWIN encodes all 13 physical parameters into standard 8-byte CAN data frames broadcasted over a 500 kbps differential bus (`vcan0`).

```
+---------------------------------------------------------------------------------+
| CAN ID  | Frame Name         | Byte 0 - Byte 1    | Byte 2 - Byte 3    | Reserved|
+---------------------------------------------------------------------------------+
| 0x100   | ENGINE_PRIMARY     | RPM (uint16)       | Throttle (uint16)  | 4 Bytes |
| 0x101   | ENGINE_PRESSURE    | MAP (uint16, 0.01) | Oil P (uint16)     | 4 Bytes |
| 0x102   | ENGINE_TEMP        | CHT (uint16, +40)  | EGT (uint16, 0.1)  | 4 Bytes |
| 0x103   | ENGINE_LUBRICATION | Oil Temp (uint16)  | Reserved (uint16)  | 4 Bytes |
| 0x104   | FUEL_SYSTEM        | Fuel Flow (uint16) | Fuel Rail P(uint16)| 4 Bytes |
| 0x105   | ELECTRICAL_BUS     | Battery V (uint16) | Alt Current(uint16)| 4 Bytes |
| 0x106   | TURBO_INJECTION    | Inj Timing(uint16) | Wastegate % (uint16| 4 Bytes |
| 0x107   | ENVIRONMENT_AIR    | Altitude (int16)   | Ambient T (int16)  | IAT (H) |
+---------------------------------------------------------------------------------+
```

---

## 3. Physical Twin Thermodynamics & Physics Formulas

$$\text{Intake Air Temp (IAT): } T_{\text{iat}} = T_{\text{amb}} + 5.0 + 8.0 \cdot \left(\frac{P_{\text{map}}}{29.92}\right) \quad [^\circ\text{C}]$$

$$\text{Fuel Rail Pressure: } P_{\text{fuel\_p}} = 3.2 + 0.4 \cdot P_{\text{fraction}} \quad [\text{bar}]$$

$$\text{Alternator Current: } I_{\text{alt\_i}} = 12.0 + 18.0 \cdot P_{\text{fraction}} \quad [\text{Amps}]$$

$$\text{Turbo Wastegate Position: } \text{WG}_{\text{pct}} = \text{clamp}\left(100 \cdot \left(1.0 - 0.75 \cdot \frac{P_{\text{map}}}{29.92}\right), 5.0, 95.0\right) \quad [\%]$$

---

## 4. Verification & Validation Summary
- **REST API Backend**: Serves all 13 channels live on `http://localhost:8000/api/telemetry`.
- **GCS Frontend UI**: Renders a 14-card Subsystem Telemetry Grid on `http://localhost:3000/`.
- **Statistical Calibration**: Re-calibrated baseline residual means ($\mu$) and standard deviations ($\sigma$) saved in `models/twin_calib.json`.
- **AI Classification**: Retrained Isolation Forest and Random Forest models in `models/iso.joblib` and `models/rf.joblib`.
