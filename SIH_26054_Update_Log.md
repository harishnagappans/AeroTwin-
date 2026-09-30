# AEROTWIN: SIH 26054 Update Log

## Rationale for Changes
The official DRDO problem statement (SIH26054) explicitly mandates monitoring specific parameters and faults that were missing from the previous prototype. 

**Missing Parameters Mandated:**
- Battery / Alternator health
- Injection timing parameters

**Missing Faults Mandated:**
- Injector abnormalities
- Combustion instability

**Missing Dashboard Features:**
- Explainable AI (XAI) / Autonomous Maintenance Advisory
- Explicit Engine Efficiency Trends / Specific Mission Profile Simulations (High Altitude, Hot Weather, Rapid Throttle)

---

## 1. Data Foundation Updates
To comply with the PS, the following engine layers were modified:

### `src/engine.py` (Layer 1: Physics Model)
- Added `battery_v` (battery voltage) simulation. The physics logic assumes voltage drops slightly with power load and drops severely if RPM < 1200.
- Added `inj_timing` (injection timing) simulation. Assumed nominal timing varies linearly with RPM (e.g., 15 to 25 degrees BTDC).

### `src/actual.py` (Layer 4: Fault Injection)
- **Data Generation:** Added standard deviation noise profiles for `battery_v` ($\sigma=0.1$) and `inj_timing` ($\sigma=0.2$).
- **New Faults Injected:**
  1. `injector_fault`: Gradually skews injection timing, causes over-fuelling, and increases EGT.
  2. `combustion_instability`: Induces heavy RPM fluctuations, raises engine vibration, and slightly increases CHT.
  3. `alternator_failure`: Rapidly drops battery voltage.

### `src/twin.py` (Layer 2: Twin Sync)
- Updated the channel tracking list (`CH`) to include `battery_v` and `inj_timing`. The twin now computes residuals (actual minus predicted) for 9 parameters instead of 7.

### `src/detect.py` (Layer 3: ML Anomaly Detection)
- Retrained the **Isolation Forest** (unsupervised anomaly detection) and **Random Forest** (supervised fault classification) to ingest the new 9-dimensional state vector. The classifier now accurately identifies 9 distinct engine faults.

### `src/rul.py` (Layer 5: RUL Estimation)
- Defined primary degradation indices and thresholds for the new faults:
  - `injector_fault` uses `inj_timing` drift threshold (4.0 $\sigma$).
  - `combustion_instability` uses `vib` drift threshold (3.0 $\sigma$).
  - `alternator_failure` uses `battery_v` drop threshold (-2.5 $\sigma$).

## 2. Next-Gen 13-Channel Subsystem Parameter Suite & CAN Expansion
To provide comprehensive UAV propulsion and auxiliary power health monitoring, the telemetry vector was expanded from 9 to 13 physical parameters:

### Expanded Physics Telemetry Parameters:
1. **Intake Air Temperature (`iat`)**: Real-time intake temperature (°C) modeling ambient temperature, ram air compression, and manifold heat.
2. **Fuel Rail Pressure (`fuel_p`)**: High-pressure fuel rail supply (bar) for vapor lock and injector clog monitoring.
3. **Alternator Charging Current (`alt_i`)**: Auxiliary generator output current (Amps) to monitor power draw and alternator health.
4. **Turbo Wastegate Position (`wastegate`)**: Servo actuator position (%) tracking boost pressure regulation at high altitudes.

### System Updates Across Layers:
- **`src/engine.py`**: Added thermodynamic formulas for `iat`, `fuel_p`, `alt_i`, and `wastegate`.
- **`src/actual.py`**: Added noise profile standard deviations (`SIGMA`) and updated fault injection behaviors (e.g. `fuel_system` drops rail pressure; `alternator_failure` drops output current).
- **`src/twin.py` & `models/twin_calib.json`**: Expanded channel list `CH` to 13 parameters and re-calibrated nominal residual means ($\mu$) and standard deviations ($\sigma$).
- **`src/can_protocol.py` & `src/can_decoder.py`**: Packed new signals into reserved CAN frame payloads (`0x104` Fuel Rail P, `0x106` Alternator Current, `0x107` Wastegate Pos, `0x108` Intake Temp).
- **`src/detect.py`**: Retrained Isolation Forest and Random Forest classifiers across all 13 residual channels.
- **`backend/server.py`**: Updated REST API telemetry payload structure, operating limits, sensor health diagnostics, and CAN message schema.
- **`frontend/index.html`**: Expanded Ground Control Station UI with a 14-card Subsystem Telemetry Grid and interactive 13-channel chart plotting selectors.
