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

---

## Next Immediate Steps
1. **Dashboard Overhaul (`dashboard/app.py`):** 
   - Integrate the new channels into the live telemetry view.
   - Implement an explicit **Explainable AI (XAI)** module that parses the `detect.py` reasoning into an autonomous maintenance advisory.
   - Add explicit SIH-mandated simulation buttons (e.g., "Simulate Hot-Weather Takeoff", "Simulate High-Altitude Loiter").
