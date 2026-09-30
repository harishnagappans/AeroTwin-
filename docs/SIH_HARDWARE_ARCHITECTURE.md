# AEROTWIN Hardware Architecture & Physical Deployment Specification
**SIH Problem Statement SIH26054 | Team HYDROVEX**

---

## 1. Overview & System Block Comparison

This document specifies the hardware architecture and physical data pathways for the AEROTWIN platform. It explicitly distinguishes between the **CURRENT SOFTWARE PROTOTYPE** (demonstrated in this submission) and the **FUTURE PHYSICAL AIRCRAFT DEPLOYMENT** (roadmap for operational UAV integration).

---

## 2. Current Prototype vs. Future Aircraft Deployment Architecture

```
CURRENT SOFTWARE PROTOTYPE (Implemented)
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ Physics Digital Twin &  │ ──►  │ Virtual ECU / FADEC     │ ──►  │ AEROTWIN Virtual CAN    │
│ Engine Simulation       │      │ State Machine (Python)  │      │ Memory Socket (vcan)    │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
                                                                               │
┌─────────────────────────┐      ┌─────────────────────────┐                   │
│ Command Center GCS      │ ◄──  │ Isolation Forest + RF   │ ◄───────────────────┘
│ Streamlit Web Dashboard │      │ ML Runtime (Python)     │
└─────────────────────────┘      └─────────────────────────┘

========================================================================================

FUTURE PHYSICAL AIRCRAFT DEPLOYMENT (Hardware Roadmap)
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ Physical Engine Sensors │ ──►  │ Physical Engine ECU /   │ ──►  │ Avionics CAN Bus /      │
│ (Thermocouples, Piezo)  │      │ FADEC Unit (Physical)   │      │ ARINC 825 Transceiver   │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
                                                                               │
┌─────────────────────────┐      ┌─────────────────────────┐                   │
│ Ground Control Station  │ ◄──  │ On-Board Edge Compute   │ ◄───────────────────┘
│ Datalink Radio Display  │      │ (NVIDIA Jetson / C-rt)  │
└─────────────────────────┘      └─────────────────────────┘
```

---

## 3. Detailed Dataflow & Component Mapping

| Architectural Block | Current Software Prototype | Future Physical Aircraft Deployment | Interface / Protocol |
| :--- | :--- | :--- | :--- |
| **Physical Sensors** | Simulated differential equations (`src/actual.py`) | Physical Thermocouples, RTDs, Piezoresistive pressure transducers | Analog 0–5 V / 4–20 mA wiring harness |
| **Engine ECU / FADEC** | Python `VirtualECU` state machine (`src/virtual_ecu.py`) | Certified Physical Engine Control Unit / FADEC hardware | Sensor ADC sampling & internal BIST |
| **Avionics Bus** | Virtual memory socket / `python-can` `VirtualBus` | Physical CAN 2.0B / ARINC 825 dual redundant bus | High-speed differential CAN (500 kbps) |
| **Edge Compute Node** | Local host workstation running Python runtime | On-Board Ruggedized Edge Computer (e.g. NVIDIA Jetson Orin Industrial / ARM Cortex-R5) | SPI / CAN controller interface |
| **Digital Twin Engine** | Python `twin.predict()` reduced-order model | Compiled C/C++ / ONNX lightweight reduced-order model runtime | Real-time POSIX thread loop (10 Hz) |
| **AI Diagnostic Core** | `scikit-learn` Isolation Forest & Random Forest binaries | C-exported ONNX Runtime / TensorRT optimized binaries | Embedded inference pipeline |
| **Ground Station Display**| Localhost Streamlit web dashboard (`dashboard/app.py`) | Integrated Tactical Ground Control Station (GCS) telemetry display | Radio Telemetry Link (Mavlink / Micro-Air-Data) |

---

## 4. Hardware Component Specifications for Edge Deployment

### A. Sensor Inputs & Sampling Rates
- **Engine Speed (RPM)**: Hall effect crank sensor (0–7000 RPM, 10 Hz)
- **Temperatures (CHT, EGT, Oil T)**: K-Type Thermocouples & RTDs (0–1000°C, 5 Hz)
- **Pressures (MAP, Oil P)**: Piezoresistive pressure transducers (0–10 bar, 10 Hz)
- **Fluid Flow (Fuel Flow)**: Turbine flow meter (0–50 L/h, 5 Hz)
- **Vibration**: Single-axis piezo accelerometer (0–10 g RMS, 20 Hz)

### B. On-Board Edge Processing Computer (Target Specification)
- **Processor**: Quad-core ARM Cortex-A72 / NVIDIA Jetson Orin Nano Industrial
- **Memory**: 8 GB LPDDR5 RAM with ECC error correction
- **Avionics Interface**: Dual CAN 2.0B ports (ISO 11898-2 compliant with galvanic isolation)
- **Power Supply**: 18–36 V DC wide-input MIL-STD-704F aircraft power supply
- **Enclosure**: IP67 ruggedized aluminum chassis with passive conduction cooling (-40°C to +85°C operating range)

---

## 5. Security & Isolation Architecture (Target State)

1. **Galvanic Isolation**: Physical optocouplers isolate edge compute CAN transceivers from engine control wiring to prevent ground loops.
2. **Read-Only Telemetry Bus**: The edge compute node operates strictly as a read-only passive CAN bus listener (`listen-only mode`), ensuring no diagnostic command can interfere with engine control FADEC actuation.
3. **Hardware Root of Trust**: Secure Boot & TPM 2.0 chip ensure only signed, verified firmware and model binaries execute on the edge processing computer.
