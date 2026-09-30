# AEROTWIN 3-Minute Live Judge Demonstration Script
**SIH Problem Statement SIH26054 | Team HYDROVEX**

---

### Demonstration Overview
- **Objective**: Present a concise, live 3-minute technical walkthrough of the AEROTWIN platform to the SIH evaluation panel.
- **Primary Live Demo Command**: `python src/sih_demo.py --fault injector_fault`
- **Fallback Live Demo Command**: `python src/sih_demo.py --fault oil_pressure`
- **Web Dashboard Command**: `streamlit run dashboard/app.py`

---

## Minute-by-Minute Live Presentation Script

### 0:00 – 0:20 | Introduction & Problem Context
> **Presenter Speaking**:
> "Respected judges, welcome to AEROTWIN — a Digital Twin and Predictive Maintenance Platform for MALE UAV Propulsion Systems built for SIH Problem Statement 26054. In long-endurance UAV missions, undetected engine degradation risks catastrophic in-flight failure. However, standard AI models trained directly on raw sensors trigger frequent false alarms because ambient altitude pressure drops and OAT changes look like engine faults. AEROTWIN solves this by combining a physics-based digital twin with machine learning residual analysis."

---

### 0:20 – 0:50 | Mission & Environmental Simulation
> **Presenter Action**: Open the Command Center Web Dashboard (`app.py`) or initiate the CLI demo script (`sih_demo.py`). Point to the **`MISSION PROFILE`** indicator.
> **Presenter Speaking**:
> "Here, our platform simulates a full flight profile — moving from Ground Startup through Takeoff, Climb, and Level Cruise. As the aircraft climbs, ambient pressure drops according to the barometric formula, and temperatures shift. Notice that our system explicitly models these environmental dynamics to establish a true physics baseline."

---

### 0:50 – 1:20 | Live Telemetry & Physics Digital Twin Baselines
> **Presenter Action**: Point to the **`REAL-TIME TELEMETRY`** and **`DIGITAL TWIN RESIDUALS`** graphs.
> **Presenter Speaking**:
> "In real time, 13 physical engine channels (RPM, CHT, EGT, Oil Pressure, Fuel Flow, Vibration, Injection Timing, etc.) are compared against our Rotax 912 S/ULS-inspired physics twin. The twin predicts theoretical baseline values under exact current operating conditions. By subtracting the twin prediction, we generate standardized residual z-scores ($z = \frac{x - \hat{x}}{\sigma}$). Under healthy flight, all residuals remain near zero."

---

### 1:20 – 1:50 | In-Flight Fault Injection
> **Presenter Action**: Trigger fault injection in the CLI demo (`--fault injector_fault`) or click the fault injection button in the dashboard.
> **Presenter Speaking**:
> "Now, at $t = 3000\text{ s}$ during cruise, we inject an **`injector_fault`** scenario — representing electronic fuel injector timing drift and manifold pressure instability. Watch how the raw telemetry signals immediately begin to deviate from the twin reference baseline."

---

### 1:50 – 2:15 | AI Anomaly Detection, Multi-Class Classification & XAI
> **Presenter Action**: Highlight the **`ANOMALY ALERT`**, **`FAULT CLASSIFICATION`**, and **`TOP XAI FEATURES`** widgets.
> **Presenter Speaking**:
> "Our two-stage AI pipeline triggers. First, **Isolation Forest** detects the anomaly after a 5-window confirmation check, eliminating false positive spikes. Second, our **Random Forest** classifier identifies the exact fault mode as `INJECTOR_FAULT` with 99.8% confidence. Crucially, our Explainable AI engine highlights the root cause: `inj_timing +5.4sigma, map +2.1sigma` — giving ground engineers instant physical transparency."

---

### 2:15 – 2:35 | Remaining Useful Life (RUL) & Maintenance Advisories
> **Presenter Action**: Point to the **`ESTIMATED RUL`** meter and **`MAINTENANCE ADVISORY`** banner.
> **Presenter Speaking**:
> "Simultaneously, our RUL estimator executes trailing OLS regression to project the degradation trajectory slope. It calculates an estimated Remaining Useful Life of **10.7 minutes** before critical failure threshold crossing, and automatically issues a structured engineering advisory: *'Inspect injector timing, solenoid wiring, and ECU driver outputs [Urgency: High]'*."

---

### 2:35 – 2:50 | CAN Bus & Virtual ECU Status
> **Presenter Action**: Point to the **`CAN BUS STATUS`** and **`VIRTUAL ECU STATE`** indicators.
> **Presenter Speaking**:
> "Notice our **AEROTWIN Prototype CAN Protocol** broadcasting 11-bit frames (`0x100` to `0x103`) at 10 Hz with 100% diagnostic agreement and $0.10\text{ s}$ bus transport latency. The software Virtual ECU transitions seamlessly to `FAULT` state."

---

### 2:50 – 3:00 | Validation Metrics & Limitations Transparency
> **Presenter Action**: Display the Summary Slide / Fact Sheet.
> **Presenter Speaking**:
> "In clean synthetic mission-level holdout validation across 100 independent test missions, AEROTWIN achieved **99.84% accuracy**, **0.9977 macro F1**, and **0 false alarms/hour** up to ±15% twin mismatch. We strictly disclaim that this represents synthetic prototype validation on software simulation, providing a complete, auditable foundation for Hardware-in-the-Loop testbed integration. Thank you!"
