# AEROTWIN System Scope & Technical Limitations
**SIH Problem Statement 26054 Telemetry & Digital Twin Platform**

To ensure absolute technical transparency for judges, evaluators, and system architects, this document details all known limitations, simplified assumptions, and architectural boundaries of the AEROTWIN platform.

---

## 1. Physical Model & Telemetry Scope

1. **Synthetic Telemetry Generation**: All telemetry streams are generated via mathematical simulation models inspired by the Rotax 912 S/ULS engine. No real flight recorder (FDR) or engine data management (EDM) log files were used.
2. **Synthetic Fault Injection**: Engine faults (cooling loss, oil pressure drop, misfire, etc.) are injected via parametric differential equations (`make_run()`). Real-world physical fault dynamics may display complex non-linear behaviors not captured in these models.
3. **No Real Flight Recorder Validation**: Performance metrics have not been validated against historical flight recorder datasets from operational aircraft.
4. **Rotax Terminology Discipline**: The engine model is a "Rotax 912 S/ULS-inspired physics model" and does NOT represent an official, flight-certified Rotax OEM digital twin or proprietary manufacturer calibration map.

---

## 2. Hardware & Interface Scope

5. **No Certified ECU/FADEC Integration**: The ECU is emulated via a software state machine (`VirtualECU`). The platform does not interface with physical FADEC hardware or certified engine control units.
6. **Prototype CAN Protocol**: The CAN bus protocol (`AEROTWIN Prototype CAN`) uses custom 11-bit identifier mappings (`0x100`–`0x103`) and standard payload packing. It does NOT use proprietary OEM Rotax or CANaerospace message structures.
7. **Platform Virtual CAN Socket Support**: On Windows OS environments, the CAN interface falls back to an in-memory broadcast queue (`VirtualBus`). Physical CAN bus operation requires Linux `SocketCAN` support and compatible USB-CAN/SPI CAN transceiver hardware.

---

## 3. Algorithm & Machine Learning Scope

8. **Digital Twin Model Mismatch Sensitivity**: The physics digital twin maintains zero false alarms up to $\pm 15\%$ gain mismatch. Mismatches $\ge \pm 20\%$ introduce static residual offsets that trigger false positive anomaly alarms in the Isolation Forest detector.
9. **Sensor Noise Vulnerability (3x Noise)**: The feature extraction pipeline functions reliably up to 1.5x nominal sensor noise. Extreme sensor noise (3.0x nominal) degrades fixed z-score thresholds ($|z| > 4.5$), leading to false alarms or missed detections without adaptive filtering.
10. **Single-Label Compound Fault Classification**: The Random Forest classifier (`models/rf.joblib`) performs single-label multi-class classification. When multiple dual faults occur simultaneously (e.g., cooling loss + overheat), the classifier outputs the single dominant primary class while classifier confidence probability drops.
11. **RUL 90% Confidence Interval Coverage**: While Remaining Useful Life (RUL) point estimates achieve a Mean Absolute Error of $0.91\text{ min}$, the theoretical 90% Confidence Interval (CI) coverage is **NOT ESTABLISHED** due to uncalibrated synthetic regression noise bounds.

---

## 4. Cyber & System Integration Scope

12. **No Federated Learning Implementation**: Fleet-wide federated learning for decentralized model updates is documented strictly as an architectural concept and is **NOT IMPLEMENTED** in code.
13. **Secure Telemetry Cryptography**: TLS 1.3 / AES-256 frame encryption is an architectural design recommendation and is **NOT IMPLEMENTED** in the current plaintext memory socket transport layers.
14. **No Airworthiness Certification**: AEROTWIN is a prototype research software platform and is **NOT CERTIFIED** by FAA, EASA, or DGCA for operational aircraft use.
