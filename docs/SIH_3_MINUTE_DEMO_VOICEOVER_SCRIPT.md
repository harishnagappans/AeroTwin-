# 🎙️ AEROTWIN — 3-4 MINUTE DEMO VOICEOVER SCRIPT
**Smart India Hackathon 2026 | Problem Statement SIH26054**
**Team Name: HYDROVEX**
**Project Title: AEROTWIN — AI-Enabled Real-Time Digital Twin System for Health Monitoring, Fault Prediction and Mission Reliability Enhancement of Aero Piston Engines used in MALE UAVs**

---

## ⏱️ Video Summary & Timing Guide

| Timestamp | Section | Visual Screen Action | Word Count |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:45** | **1. Introduction & Problem** | Title Slide / Dashboard Overview | ~100 words |
| **0:45 – 1:30** | **2. Telemetry Grid & CAN Bus** | Subsystem Telemetry Grid + CAN Bus view | ~110 words |
| **1:30 – 2:15** | **3. Physics Twin & Residuals** | Actual vs Expected Graphs & z-scores | ~110 words |
| **2:15 – 3:00** | **4. AI Diagnostics, XAI & RUL** | Fault Injection Alert + RUL Gauge | ~110 words |
| **3:00 – 3:30** | **5. Conclusion & Defense Impact** | Maintenance Advisory + Summary Slide | ~60 words |
| **Total** | **3 Min 30 Sec** | **Full Screen Demo Walkthrough** | **~490 words** |

---

## 📜 Full Voiceover Script with Visual Cues

---

### 🟢 SECTION 1: Introduction & Problem Statement (0:00 – 0:45)

**[VISUAL CUE]:** *Start recording on the AEROTWIN Ground Control Station Dashboard homepage or Title Slide.*

> *"Hello respected judges and viewers. Welcome to our presentation of **AEROTWIN**, built for Smart India Hackathon 2026 Problem Statement **SIH26054** by Team **HYDROVEX**.*
>
> *Medium Altitude Long Endurance UAVs, such as India's TAPAS-BH-201, carry out critical 24-plus hour surveillance missions. In-flight aero piston engine failure leads to loss of multi-crore defense assets or forced mission aborts. Conventional ground stations rely on static threshold alarms — which fail to predict breakdown in advance and produce frequent false alarms during high-altitude climbs or weather shifts.*
>
> *AEROTWIN solves this by deploying a real-time, physics-informed Digital Twin that detects engine anomalies up to 20 minutes before failure."*

---

### 🔵 SECTION 2: 13-Channel Telemetry & CAN 2.0B Bus (0:45 – 1:30)

**[VISUAL CUE]:** *Hover cursor over the 14-card Subsystem Telemetry Grid, then switch to the CAN Telemetry Bus panel showing live frames.*

> *"Here on our Ground Control Station interface, you see AEROTWIN’s live 13-channel telemetry suite mirroring the Rotax 912 S/ULS engine.*
>
> *We monitor physical variables across thermal, fluid, mechanical, and electrical subsystems — including Crankshaft RPM, Cylinder Head Temperature, Exhaust Gas Temperature, Oil Pressure and Temperature, Fuel Rail Pressure, Intake Air Temperature, Vibration Spectrum RMS, Battery Voltage, Alternator Current, and Electronic Injection Timing.*
>
> *All 13 sensor streams are packaged into standard 8-byte **CAN 2.0B avionics frames** using message IDs 0x100 through 0x107 broadcasting at 500 kbps — making AEROTWIN hardware-ready to plug directly into real UAV avionics buses with zero diagnostic encoding discrepancy."*

---

### 🟣 SECTION 3: Physics Digital Twin & Residual z-Scores (1:30 – 2:15)

**[VISUAL CUE]:** *Scroll to the Actual vs expected Digital Twin comparison line graphs.*

> *"At the core of AEROTWIN is a reduced-order thermodynamic physics engine. In real time, the Digital Twin computes what a healthy engine SHOULD output under current throttle, altitude, and ambient weather conditions.*
>
> *Instead of raw sensor limits, we calculate standardized residual z-scores: actual reading minus twin prediction, normalized against healthy baseline variance.*
>
> *This residual approach mathematically subtracts altitude lapse rates and ambient temperature swings. The result? **Zero false alarms per flight hour** under nominal flight conditions, eliminating the number one operational headache of conventional monitoring systems."*

---

### 🔴 SECTION 4: Dual-Stage AI Diagnostics, XAI & RUL (2:15 – 3:00)

**[VISUAL CUE]:** *Click 'Inject Fault' (e.g., Cooling Failure or Oil Pressure Drop). Watch the Red Alarm turn ON, XAI bar graph appear, and RUL countdown display.*

> *"Now, let's inject a simulated cooling system degradation during flight.*
>
> *Our dual-stage AI diagnostic pipeline immediately kicks in. **Stage 1** uses an unsupervised **Isolation Forest** to detect abnormal residual drift across rolling 60-second windows.*
>
> *Once confirmed, **Stage 2** deploys a **Random Forest classifier** that pinpoints the exact fault mode with **99.84% accuracy** across 10 engine state classes.*
>
> *Simultaneously, our **Explainable AI engine** highlights the primary root cause — here showing Cylinder Head Temperature deviating by plus 4.5 sigma — while trailing OLS linear regression forecasts the **Remaining Useful Life** with a mean absolute error of just 0.91 minutes."*

---

### 🟡 SECTION 5: Maintenance Advisory & Conclusion (3:00 – 3:30)

**[VISUAL CUE]:** *Scroll down to the Maintenance Advisory card showing urgency rating and step-by-step engineering action plan.*

> *"Finally, AEROTWIN automatically generates an actionable **Maintenance Advisory**, giving flight operators clear emergency procedures and ground crews precise component inspection steps.*
>
> *Tested across 500 independent holdout flight missions, AEROTWIN provides a 100% indigenous, Atmanirbhar Bharat software solution that saves million-dollar UAV assets and enhances national defense mission reliability.*
>
> *Thank you for your time!"*

---

## 💡 Screen Recording Tips for Success

1. **Audio Setup**: Speak clearly at a steady, confident pace. Use a decent headset or microphone.
2. **Screen Resolution**: Set display resolution to 1920x1080 (1080p).
3. **Cursor Movement**: Move the mouse smoothly to point at elements as you speak about them (e.g., hover over CAN IDs at 1:10, hover over RUL meter at 2:45).
4. **Timing Check**:
   - At 1:30, you should be on the Digital Twin plots.
   - At 2:15, trigger the fault injection button.
   - At 3:00, show the Maintenance Advisory card.
