# AEROTWIN Virtual ECU / FADEC Simulation Layer

## Mandatory Project Disclaimer
> [!IMPORTANT]
> **The Virtual ECU/FADEC is a software simulation used to demonstrate the AEROTWIN architecture. It is not a production aircraft ECU/FADEC and has not been certified or validated for flight use.**

---

## 1. Overview & Purpose
The `VirtualECU` (`src/virtual_ecu.py`) operates as an electronic engine control unit and sensor measurement abstraction layer positioned between the physics engine model (`src/engine.py`) and the CAN transport layer (`src/can_simulator.py`).

It models realistic electronic control unit behavior, including state transitions, ignition/injection timing calculations, sensor health tracking, periodic heartbeat generation, and simulated Built-In Self-Test (BIST) fault flags.

---

## 2. Architecture & Data Flow

```
+------------------------------------+
|  Physics Engine Model              |
|  (src/engine.py / actual.make_run) |
+-----------------+------------------+
                  |  Physical Engine Measurements
                  v
+------------------------------------+
|  Virtual ECU / FADEC Layer         |
|  (src/virtual_ecu.py)              |
|  - State Machine (IDLE, RUNNING...) |
|  - Injection Timing Control        |
|  - Sensor Health (VALID, FAILED)   |
|  - Simulated BIST Fault Flags      |
+-----------------+------------------+
                  |  ECU Telemetry Schema
                  v
+------------------------------------+
|  AEROTWIN Prototype CAN Protocol   |
|  (src/can_protocol.py & simulator) |
+-----------------+------------------+
                  |  CAN Bus Frames (0x100 - 0x10A)
                  v
+------------------------------------+
|  CAN Transport & Receiver          |
|  (src/can_interface.py & decoder)  |
+-----------------+------------------+
                  |  Reconstructed Dataframe (CANSource)
                  v
+------------------------------------+
|  Existing Digital Twin & AI        |
|  (src/twin.py & src/detect.py)     |
+------------------------------------+
```

---

## 3. Inputs & Outputs

### Inputs (from Physics Telemetry):
- `rpm`, `thr`, `alt`, `t_amb`, `map`, `cht`, `egt`, `oil_t`, `oil_p`, `fuel`, `vib`, `battery_v`

### Outputs (Standard AEROTWIN Schema):
- All 13 core telemetry channels + `engine_status` (ECU state enum), `fault_flags` (BIST bitmask), `frame_counter`, and `sensor_health`.

---

## 4. State Machine Definition (`ECUState`)

| State Value | State Name | Entry Conditions |
| :--- | :--- | :--- |
| `0` | `OFF` | Engine stopped (`rpm < 100` and `thr == 0.0`) or ECU unpowered |
| `1` | `STARTING` | Starter engaged (`100 <= rpm < 1200`) |
| `2` | `IDLE` | Ground/flight idle (`1200 <= rpm < 2000`) |
| `3` | `RUNNING` | Normal steady-state operation (`2000 <= rpm < 5200`) |
| `4` | `HIGH_LOAD` | Max continuous or takeoff power (`rpm >= 5200` or `thr >= 0.9`) |
| `5` | `TRANSIENT` | Rapid throttle movement (`|d(thr)/dt| > 0.15/s`) |
| `6` | `SHUTDOWN` | Engine spooling down to zero RPM |
| `7` | `FAULT` | Internal ECU fault or severe engine limit trip |

---

## 5. Control Logic & Calculations

### Injection / Ignition Timing Control:
Calculates dynamic advance based on RPM, manifold pressure, and ambient density:
$$\text{inj\_timing} = 15.0 + 10.0 \times \left( \frac{\min(\text{rpm}, 5800)}{5800} \right) + 2.0 \times \left( \frac{\text{map} - 29.92}{10.0} \right) - 0.05 \times (\text{t\_amb} - 15.0)$$

---

## 6. Simulated ECU BIST Fault Flags vs. AEROTWIN Independent AI Diagnosis

> [!CRITICAL]
> **Separation of Concerns:**
> The Virtual ECU's fault flags represent what the simulated ECU's built-in self-test (BIST) detects using static threshold rules. 
> 
> The **AEROTWIN AI Engine** (`src/detect.py` Isolation Forest + Random Forest) independently analyzes normalized residuals ($z$-scores) and thermal lag dynamics without relying on the ECU's internal fault flags.
> 
> This architecture proves that AEROTWIN can independently diagnose subtle mechanical degradations long before simple ECU threshold lights trigger.

---

## 7. Sensor Health Tracking
Each ECU sensor (`cht`, `egt`, `oil_t`, `oil_p`, `fuel`, `vib`, `battery_v`) is assigned a health status:
- `VALID`: Normal operational measurement.
- `DEGRADED`: Measurement experiencing noise/drift.
- `FAILED`: Sensor open-circuit / hardware failure (produces invalid payload flag `-999.0`).
