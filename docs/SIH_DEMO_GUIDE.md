# AEROTWIN SIH Demonstration Guide & Judging Playbook
**SIH Problem Statement 26054 Telemetry & Digital Twin Platform**

> [!IMPORTANT]
> **CLAIM DISCIPLINE DISCLAIMER:**
> All telemetry streams, environmental variations, and engine fault dynamics demonstrated in this platform are generated via **controlled physical digital twin simulation**. This demonstration is intended for **software evaluation**, **prototype presentation**, and **simulation-based benchmarking**. It does not constitute flight-certified aircraft performance.

---

## 1. How to Launch the Web Command Center Dashboard

To start the interactive Streamlit GCS Command Center Dashboard:

```bash
streamlit run dashboard/app.py
```

The web dashboard will launch at `http://localhost:8501`.

---

## 2. How to Run the Deterministic CLI Demo Script

For automated, deterministic evaluation during judging panels:

```bash
python src/sih_demo.py --fault injector_fault
```

To run with 1-second real-time delays between mission checkpoints:

```bash
python src/sih_demo.py --fault injector_fault --realtime
```

---

## 3. Default Scenario & Available Fault Injection Options

The default scenario injects an **`injector_fault`** at $t = 3000\text{ s}$ during mission cruise.

Judges can test any of the 9 supported single-fault scenarios using the `--fault` flag:

```bash
python src/sih_demo.py --fault cooling
python src/sih_demo.py --fault oil_pressure
python src/sih_demo.py --fault misfire
python src/sih_demo.py --fault fuel_system
python src/sih_demo.py --fault sensor_drift
python src/sih_demo.py --fault overheat
python src/sih_demo.py --fault injector_fault
python src/sih_demo.py --fault combustion_instability
python src/sih_demo.py --fault alternator_failure
```

---

## 4. Key Highlights for SIH Evaluation Panel

When presenting to judges, highlight the following operational capabilities:

### A. Real-Time CAN Bus Architecture (CAN Protocol Demonstration)
- Observe the **`CAN STATUS`** indicator (`0x100`, `0x101`, `0x102`, `0x103` frames broadcasting at 10 Hz).
- Direct memory-queue to virtual CAN socket decoding demonstrates zero loss and low transport latency ($0.10\text{ s}$).

### B. Virtual ECU / FADEC State Machine
- Watch the Virtual ECU state transition:
  `OFF` → `STARTUP` → `RUNNING` → `FAULT_DEGRADED`
- Health flags update dynamically as sensor bounds or residual thresholds are crossed.

### C. Physics Digital Twin Residual Generation
- Ground truth engine sensors are continuously compared against theoretical baseline predictions ($z_{col} = \frac{x_{col} - \hat{x}_{col}}{\sigma_{col}}$).
- Standardized residuals isolate physical anomalies from ambient ISA temperature shifts and altitude pressure drops.

### D. AI Anomaly Detection & Random Forest Classification
- **Isolation Forest** flags non-zero anomaly scores when standardized residuals exceed threshold limits.
- **Random Forest** multi-class classifier identifies the specific fault category with high confidence.

### E. Explainable AI (XAI) Attribution
- The **`TOP XAI FEATURES`** output lists the exact physical sensors contributing most to the anomaly trigger (e.g., `cht +4.5sigma, oil_t +1.8sigma`).

### F. Remaining Useful Life (RUL) Estimation
- The RUL estimator computes degradation trajectory slope via trailing Ordinary Least Squares (OLS) regression to estimate time-to-threshold crossing in minutes.

### G. Mission Replay Capability
- Past flight logs can be loaded and replayed step-by-step in the Command Center dashboard to audit past telemetry anomalies.

---

## 5. Simulation Boundaries vs. Real-World Limitations

| Feature | Demonstrated Prototype | Real Aircraft Requirement |
| :--- | :--- | :--- |
| **Engine Physics** | Rotax 912 S/ULS-inspired thermodynamic twin | Physical Rotax engine bench testing |
| **CAN Bus** | AEROTWIN Prototype 11-bit CAN frame spec | OEM manufacturer CAN bus protocol |
| **ECU Interface** | Software-emulated FADEC state machine | Physical ARINC/CAN hardware FADEC connector |
| **Telemetry** | Physics-generated synthetic telemetry stream | Physical DAQ hardware sensor recording |
| **Validation** | Synthetic mission-level holdout ($99.84\%$ acc) | Flight test validation & airworthiness certification |
