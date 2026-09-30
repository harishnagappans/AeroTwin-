# AEROTWIN SIH Judging Q&A & Key Talking Points
**SIH Problem Statement 26054 Telemetry & Digital Twin Platform**

---

### Q1: What is novel about AEROTWIN?
**Answer**: AEROTWIN combines a **first-principles thermodynamic digital twin** with **machine learning anomaly detection** on standardized residual signals ($z$-scores), rather than training ML models directly on raw sensor values. This ensures that ambient flight variations (altitude pressure drops, OAT shifts) do not trigger false alarms.

### Q2: Why use a Digital Twin instead of only machine learning?
**Answer**: Pure machine learning models trained on raw telemetry tend to confuse normal flight condition changes (e.g. climbing to high altitude) with engine health degradation. The Digital Twin provides a real-time theoretical reference baseline representing how a healthy engine *should* behave under exact current operating conditions.

### Q3: Why not use only a physics model without machine learning?
**Answer**: Pure physics models cannot easily classify multi-channel non-linear fault interactions or compute remaining useful life. Coupling physics residuals with Isolation Forest and Random Forest enables rapid multi-class fault classification and trend regression.

### Q4: How does the physics model help?
**Answer**: The physics model subtracts expected operating baseline shifts from raw sensor data. The resulting residual signal represents pure health degradation, allowing ML models to operate with higher accuracy and zero false alarms up to $\pm 15\%$ twin model mismatch.

### Q5: How does CAN integration work?
**Answer**: Physical sensor signals are packed into standard 11-bit CAN bus data frames (`0x100` Engine Primary, `0x101` Thermal, `0x102` Fluids, `0x103` Auxiliary) at 10 Hz. A `CANDecoder` unpacks CAN messages back into canonical telemetry with $100\%$ classification fidelity and $<0.03\sigma$ quantization error.

### Q6: Is the ECU real hardware?
**Answer**: No. The ECU is a software-emulated Virtual ECU (`VirtualECU`) running a FADEC state machine (`STARTUP`, `RUNNING`, `FAULT_DEGRADED`) and sensor health BIST logic. It provides realistic software interfaces without requiring physical avionics hardware during testing.

### Q7: Is this real aircraft telemetry data?
**Answer**: No. All telemetry streams are generated via physics-based digital twin simulation inspired by the Rotax 912 S/ULS engine. We strictly disclose that no real flight recorder data or operational aircraft logs were used.

### Q8: How do you detect faults?
**Answer**: Standardized residuals ($z = \frac{x - \hat{x}}{\sigma}$) are windowed (60 s rolling window, 10 s stride). An **Isolation Forest** detector combined with a 5-consecutive window confirmation check ($|z| > 4.5$) triggers an anomaly alarm. A **Random Forest** classifier then identifies the specific fault class.

### Q9: How do you estimate Remaining Useful Life (RUL)?
**Answer**: Once an anomaly is confirmed, trailing OLS regression fits the degradation trajectory slope ($m$) on standardized residuals. The estimator projects time remaining until threshold crossing ($z_{fail}$) to calculate RUL in minutes.

### Q10: What happens under high altitude operating conditions?
**Answer**: At high altitude, ambient air pressure drops according to the barometric formula. The Digital Twin adjusts theoretical MAP and EGT baselines downward, preventing altitude climbs from triggering false temperature alarms.

### Q11: What happens under hot weather operating conditions?
**Answer**: Under hot ISA offsets (+25°C), CHT and oil temperatures increase. The Digital Twin accounts for elevated ambient temperature in its heat transfer balance, maintaining normal residual levels and zero false alarms.

### Q12: What happens under model mismatch between the Digital Twin and real engine?
**Answer**: Under digital twin gain mismatches up to $\pm 15\%$, inline self-calibration (`dz`) removes static offsets. The system maintains $0.00\text{ false alarms/hr}$. Mismatches exceeding $\pm 20\%$ begin to elevate false alarm rates.

### Q13: What happens under noisy sensor conditions?
**Answer**: Feature extraction (rolling mean and standard deviation) smooths Gaussian noise up to 1.5x nominal noise. Extreme noise (3.0x nominal) degrades fixed z-score thresholds and requires adaptive filtering.

### Q14: How do you prevent machine learning data leakage?
**Answer**: We enforce a **strict mission-level holdout split**. Entire flight trajectories (seeds 100–399 TRAIN, 400–449 VAL, 500–599 TEST) are separated cleanly. Overlapping rolling feature windows never span across train and test sets.

### Q15: What is your validated classification accuracy?
**Answer**: In clean mission-level holdout testing on 100 independent test seeds (500–599), the validation Random Forest classifier achieved **99.84% accuracy** and a **macro F1 score of 0.9977**.

### Q16: What are the main system limitations?
**Answer**: Key limitations include: (1) synthetic simulation data; (2) single-label multi-class output for compound faults; (3) unestablished 90% RUL confidence interval coverage; and (4) prototype software implementation requiring airworthiness certification for physical flight deployment.

### Q17: Can this platform be deployed on a real aircraft today?
**Answer**: AEROTWIN is a prototype research software platform. Deployment on operational aircraft would require physical CAN/ARINC hardware interfaces, real-world engine flight test dataset tuning, and DGCA/FAA/EASA software certification (DO-178C / DO-254).
