# 🎬 SIH 2026 HIGH-IMPACT DEMO VIDEO PLAYBOOK & EXTENSIVE VOICEOVER SCRIPT
**SIH Problem Statement 26054 — AI-Enabled Real-Time Digital Twin System for Health Monitoring, Fault Prediction and Mission Reliability Enhancement of Aero Piston Engines used in MALE UAVs**
**Team Name: HYDROVEX | Target Platform: Rotax 912 S/ULS & MALE UAVs (TAPAS-BH-201 / Heron TP)**

---

## 📌 VIDEO PRODUCTION OVERVIEW & RECORDING CHECKS

| Parameter | Specification |
| :--- | :--- |
| **Target Video Length** | **3 Minutes 30 Seconds – 4 Minutes** |
| **Screen Resolution** | 1920 x 1080 (1080p, 60 FPS) |
| **Audio Format** | Stereo 48 kHz, Noise-Suppressed Condenser Mic |
| **Screen Layout** | Browser full-screen (`F11`) on `http://localhost:3000/` showing AEROTWIN GCS Dashboard |
| **Key Operational Metric** | **99.84% Classification Accuracy \| 0.0 False Alarms / Hr \| 0.91 Min RUL Error** |

---

## ⏱️ SCENE CHOREOGRAPHY & TIMING MAP

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SIH DEMO VIDEO TIMELINE & SCENE MAP                             │
├─────────────────┬──────────────────────────────────┬───────────────────────────────────┤
│ Scene 1 (0:00)  │ Defense Operational Imperative   │ Title Slide / GCS Operational View│
├─────────────────┼──────────────────────────────────┼───────────────────────────────────┤
│ Scene 2 (0:45)  │ 13-Channel CAN 2.0B Avionics Bus │ Subsystem Grid & CAN Frame Stream │
├─────────────────┼──────────────────────────────────┼───────────────────────────────────┤
│ Scene 3 (1:30)  │ Thermodynamics Physics Twin      │ Actual vs Predicted Baseline Plot │
├─────────────────┼──────────────────────────────────┼───────────────────────────────────┤
│ Scene 4 (2:15)  │ Anomaly Detection & AI Fault ML  │ Fault Injection Trigger & XAI Panel│
├─────────────────┼──────────────────────────────────┼───────────────────────────────────┤
│ Scene 5 (3:00)  │ RUL Forecasting & Advisory       │ Trailing OLS RUL Gauge & Advisory │
├─────────────────┼──────────────────────────────────┼───────────────────────────────────┤
│ Scene 6 (3:35)  │ Summary, Atmanirbhar & Next Steps│ Architecture Block Diagram Slide  │
└─────────────────┴──────────────────────────────────┴───────────────────────────────────┘
```

---

## 📜 WORD-FOR-WORD TECHNICAL VOICEOVER SCRIPT

---

### 🎬 SCENE 1: Operational Defense Imperative & Problem Context (0:00 – 0:45)

**🎥 SCREEN ACTION:**
- Display the **AEROTWIN Ground Control Station (GCS) Dashboard** in clean OLED dark/light mode.
- Slowly pan cursor across the header bar showing: `UAV: TAPAS-BH-201 | Engine: Rotax 912 S/ULS | Status: NOMINAL CRUISE`.

**🗣️ VOICEOVER SCRIPT (Word-for-Word):**

> *"Respected Judges of Smart India Hackathon 2026. Welcome to Team **HYDROVEX**'s technical demonstration for Problem Statement **SIH26054**.*
>
> *Medium Altitude Long Endurance UAVs, such as India's indigenous TAPAS-BH-201, operate at altitudes exceeding 15,000 feet on 24-plus hour long-duration intelligence and surveillance missions. In this critical operating envelope, an in-flight aero piston engine failure leads to catastrophic asset loss, destroying multi-crore military payloads.*
>
> *Current Ground Control Stations rely on primitive, fixed-threshold limit alarms. When a UAV climbs through high-density altitudes or encounters extreme ambient weather shifts, fixed thresholds trigger frequent false alarms — or worse, fail to detect subtle mechanical degradation until catastrophic failure occurs.*
>
> *To solve this, we present **AEROTWIN** — a real-time, physics-informed Digital Twin and AI diagnostic platform that continuously mirrors physical engine dynamics, detecting engine degradation up to 20 minutes before failure with zero false alarms."*

---

### 🎬 SCENE 2: 13-Channel Parameter Suite & CAN 2.0B Avionics Transport (0:45 – 1:30)

**🎥 SCREEN ACTION:**
- Smoothly hover mouse cursor over the **Subsystem Telemetry Grid** highlighting the 14 live telemetry cards.
- Click or open the **CAN Telemetry Bus** panel showing encoded 8-byte hex message payloads streaming live.

**🗣️ VOICEOVER SCRIPT (Word-for-Word):**

> *"Here on our Ground Control Station interface, you are observing AEROTWIN’s enlarged **13-channel physical parameter suite**, simulating a Rotax 912 S/ULS four-stroke aircraft engine.*
>
> *We continuously capture physical signals across 4 critical engine subsystems:*
> 1. *Primary Dynamics: Crankshaft Speed up to 5800 RPM and Manifold Absolute Pressure.*
> 2. *Thermodynamics: Cylinder Head Temperature, Exhaust Gas Temperature, and Intake Air Temperature.*
> 3. *Fluids & Fueling: Lubrication Oil Pressure, Oil Temperature, Fuel Mass Flow Rate, and High-Pressure Fuel Rail Pressure.*
> 4. *Electrical & Structural: Tri-axial Accelerometer Vibration RMS, Avionics DC Bus Voltage, Alternator Charging Current, Electronic Injection Timing, and Turbo Wastegate Position.*
>
> *Crucially, these 13 parameters are NOT transferred as raw unvalidated floats. AEROTWIN emulates an airborne **Virtual ECU and FADEC** that packages telemetry into standard 8-byte **CAN 2.0B data frames** across IDs `0x100` through `0x107` at 500 kbps. Our decoded CAN telemetry achieves a verified **100% classification agreement** against raw telemetry, ensuring zero avionics quantization mismatch."*

---

### 🎬 SCENE 3: First-Principles Physics Digital Twin & Residual z-Score Engine (1:30 – 2:15)

**🎥 SCREEN ACTION:**
- Scroll down to the **Digital Twin Comparison Section**.
- Hover over the dual-line graph showing `Actual Sensor Reading (Solid Line)` overlaid directly on `Digital Twin Prediction (Dashed Line)`.

**🗣️ VOICEOVER SCRIPT (Word-for-Word):**

> *"At the technical core of AEROTWIN is a reduced-order thermodynamic Physics Digital Twin. Operating in real time alongside the physical aircraft, the twin evaluates first-principles equations — polytropic compression, Otto-cycle heat release, thermal mass dissipation, and density altitude lapse rates — to project what a 100% healthy engine SHOULD read under exact throttle and atmospheric conditions.*
>
> *Instead of feeding raw sensor values to machine learning models, AEROTWIN calculates standardized residual z-scores:*
>
> $$\text{Residual } r(t) = x_{\text{actual}}(t) - \hat{x}_{\text{twin}}(t)$$
> $$z(t) = \frac{r(t) - \mu_{\text{baseline}}}{\sigma_{\text{baseline}}}$$
>
> *By subtracting the Digital Twin's predicted baseline, environmental shifts — such as throttle transients, altitude climbs, and ambient temperature drops — are mathematically canceled out.*
>
> *This residual isolation strategy is how AEROTWIN achieves a verified **0.0 false alarms per flight hour** under standard ISA flight profiles, isolating purely physical mechanical degradation."*

---

### 🎬 SCENE 4: Dual-Stage AI Diagnostics & Explainable AI (XAI) (2:15 – 3:00)

**🎥 SCREEN ACTION:**
- Click the **Inject Fault** control button (select `Cooling System Breakdown` or `Lubrication Pressure Loss`, Severity `0.6`).
- Watch the GCS Dashboard instantly change state: Green `NOMINAL` switches to flashing Red `CRITICAL ALARM`, the XAI Feature Attribution bar graph appears, and the Fault Classifier displays the prediction.

**🗣️ VOICEOVER SCRIPT (Word-for-Word):**

> *"Now, let us demonstrate real-time fault detection. I am injecting a simulated **Cooling System Degradation** into the physical engine stream during active flight.*
>
> *Watch how our **Dual-Stage AI Diagnostic Pipeline** responds:*
>
> * **Stage 1 — Anomaly Detection:** An unsupervised **Isolation Forest** evaluates a rolling 60-second window of multi-channel residual features. To prevent transient spikes from triggering false alarms, anomaly scoring requires 5 consecutive abnormal window confirmations.*
> * **Stage 2 — Fault Classification:** Once confirmed, a 300-tree **Random Forest classifier** analyzes the residual signature, classifying the exact fault mode with **99.84% accuracy** and a **Macro F1-score of 0.9977** across 10 engine state classes.*
>
> *Notice our **Explainable AI (XAI) Attribution Engine** below. Rather than acting as a black box, it explicitly ranks the contributing features — highlighting that Cylinder Head Temperature has drifted to **plus 4.5 sigma** and Oil Temperature to **plus 1.8 sigma**, giving flight commanders transparent, auditable proof of the diagnosis."*

---

### 🎬 SCENE 5: Trailing OLS RUL Forecasting & Maintenance Action Plan (3:00 – 3:35)

**🎥 SCREEN ACTION:**
- Hover over the **Remaining Useful Life (RUL) Gauge** showing the countdown in minutes and 90% confidence bound.
- Scroll down to the **Automated Maintenance Advisory Card**.

**🗣️ VOICEOVER SCRIPT (Word-for-Word):**

> *"Simultaneously, AEROTWIN’s **Prognostic RUL Engine** executes trailing 600-second Ordinary Least Squares linear regression on the primary degrading residual channel, projecting the exact time remaining until critical threshold crossing.*
>
> *Evaluated across synthetic failure trajectories, our RUL estimation achieves a **Mean Absolute Error of just 0.91 minutes** over a 12-minute failure horizon — giving mission commanders up to **20 minutes of advance warning** before engine seizure.*
>
> *Finally, AEROTWIN translates this predictive AI output into a structured **Maintenance Advisory**, assigning an urgency rating of `CRITICAL`, displaying emergency Return-To-Base flight checklists for pilots, and generating step-by-step inspection protocols for ground engineering crews."*

---

### 🎬 SCENE 6: Verification Summary, Atmanirbhar Impact & Conclusion (3:35 – 4:00)

**🎥 SCREEN ACTION:**
- Switch to the final **End-to-End System Architecture Slide** or display the full-screen dashboard summary.
- Highlight the **100 Mission Seed Benchmark Verification**.

**🗣️ VOICEOVER SCRIPT (Word-for-Word):**

> *"AEROTWIN has undergone rigorous empirical validation across **100 independent mission holdout seeds** and 5 dynamic flight profiles — including High Altitude, Hot Weather, and Rapid Throttle maneuvers — achieving a **Cross-Condition F1 score of 0.95**.*
>
> *By shifting propulsion health management from reactive threshold alarms to physics-informed predictive digital twins, AEROTWIN offers a 100% indigenous, **Atmanirbhar Bharat** software architecture aligned with CEMILAC and RTCA DO-178C aerospace guidelines.*
>
> *Preventing a single in-flight UAV failure saves multi-crore national defense assets. Thank you for your time and consideration."*

---

## 🎯 JUDGE QUESTION & ANSWER (Q&A) CHEATSHEET

Be prepared to answer these exact questions if asked by SIH judges after your video demo:

| Judge Question | Technical Response Strategy |
| :--- | :--- |
| **Q1: Did you test this on a real aircraft engine?** | *"No, sir/ma'am. We maintain strict claim discipline. AEROTWIN is a fully functional software prototype validated on high-fidelity thermodynamic simulations across 100 independent mission seeds. It is ready for Phase 2 hardware-in-the-loop (HIL) engine test-rig integration."* |
| **Q2: Why use Isolation Forest + Random Forest instead of Deep Learning / LSTMs?** | *"Isolation Forest provides unsupervised anomaly detection without needing pre-labeled failure data. Random Forest trains in seconds, evaluates in < 5 milliseconds on edge hardware (Raspberry Pi 4 / Jetson Nano), and avoids the over-fitting and black-box nature of deep neural networks."* |
| **Q3: How do you handle sensor noise and environmental changes?** | *"Our physics digital twin computes environmental lapse rates for ISA ambient conditions. Subtracting the twin prediction yields residual z-scores, which cancel out ambient temperature and altitude shifts, yielding 0.0 false alarms/hr under nominal conditions."* |
| **Q4: What happens if the CAN bus drops frames?** | *"Our Virtual ECU emulates sensor BIST (Built-In Self-Test) and missing-frame range checks. If CAN frames drop, the decoder holds the last validated telemetry state for up to 3 frames before raising a telemetry stale warning."* |
