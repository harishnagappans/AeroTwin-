# AEROTWIN SIH Final Judge Q&A Master Sheet (30 Questions)
**SIH Problem Statement SIH26054 | Team HYDROVEX**

---

### Q1: What is the primary novelty of AEROTWIN?
**Answer**: Combining a first-principles thermodynamic digital twin with ML anomaly detection on standardized residuals ($z$-scores) rather than training ML directly on raw sensor values. This isolates physical degradation from ambient flight shifts.

### Q2: Why use a Digital Twin instead of pure machine learning?
**Answer**: Pure ML trained on raw telemetry confuses normal ambient changes (climbing, hot OAT) with engine faults. The Digital Twin calculates a real-time theoretical reference baseline under exact current operating conditions.

### Q3: Why not rely exclusively on physics models without ML?
**Answer**: Physics models cannot easily classify complex non-linear multi-channel fault modes or compute remaining useful life. Coupling physics residuals with Isolation Forest and Random Forest enables rapid multi-class fault classification and trend regression.

### Q4: How is physics used in the pipeline?
**Answer**: First-principles thermodynamic equations predict baseline values ($\hat{x}$) for CHT, EGT, Oil P, Fuel Flow, etc. Raw residuals ($r = x - \hat{x}$) are normalized into standardized z-scores ($z = \frac{r - \mu}{\sigma}$) to remove operating point variations.

### Q5: How are engine faults generated in simulation?
**Answer**: Faults are injected parametrically in `make_run()` by modifying physical parameters (e.g. reducing cooling effectiveness, dropping oil pump pressure, shifting injection timing) starting at $t_0 = 3000\text{ s}$ during mission cruise.

### Q6: Are these real aircraft flight data?
**Answer**: No. All telemetry streams are generated via physics-based digital twin simulation inspired by the Rotax 912 S/ULS engine. We strictly disclaim that no real flight recorder logs were used.

### Q7: Is the Rotax engine model official or OEM-certified?
**Answer**: No. It is a "Rotax 912 S/ULS-inspired reduced-order physics model" built from public thermodynamic literature. It does NOT represent an official Rotax OEM digital twin or proprietary calibration map.

### Q8: Is the CAN protocol an official Rotax CAN specification?
**Answer**: No. It is the "AEROTWIN Prototype CAN Protocol" using standard 11-bit CAN 2.0B frame packing (`0x100` to `0x103`). It does not use proprietary OEM CAN IDs.

### Q9: Is the ECU real physical hardware?
**Answer**: No. The ECU is a software simulation layer (`VirtualECU`) running a FADEC state machine (`STARTUP`, `RUNNING`, `FAULT`) and sensor health BIST logic.

### Q10: How does CAN integration work in code?
**Answer**: Physical sensor signals are packed into 8-byte CAN frames (`0x100` Engine Primary, `0x101` Thermal, `0x102` Fluids, `0x103` Auxiliary) at 10 Hz over a virtual memory socket (`python-can` `VirtualBus`). A `CANDecoder` unpacks frames back into canonical telemetry with $100\%$ classification agreement.

### Q11: How is Remaining Useful Life (RUL) calculated?
**Answer**: Trailing OLS linear regression fits the primary fault channel's residual degradation slope over a 600-second window and projects time remaining until threshold crossing ($z_{fail}$) to calculate RUL in minutes.

### Q12: What does Explainable AI (XAI) provide?
**Answer**: XAI ranks residual channels by absolute z-score magnitude (e.g. `cht +4.5sigma, oil_t +1.8sigma`), providing transparent physical feature attribution explaining why the alert was raised.

### Q13: How do you handle high altitude operating conditions?
**Answer**: Pressure altitude drops according to the barometric formula. The Digital Twin adjusts baseline MAP and EGT expectations downward, preventing climbs from triggering false temperature alarms.

### Q14: How do you handle hot weather operating conditions?
**Answer**: Hot ISA offsets (+25°C) elevate ambient baseline temperatures. The Digital Twin incorporates OAT into its heat transfer balance, keeping normal residuals near zero and preventing false alerts.

### Q15: How do you prevent false alarms?
**Answer**: By using standardized twin residuals and requiring Isolation Forest anomaly flags to persist across 5 consecutive windows ($|z| > 4.5$), suppressing transient sensor noise spikes.

### Q16: What happens under digital twin model mismatch?
**Answer**: Online self-calibration zero-offset subtraction (`dz`) absorbs static model offsets. The system maintains $0.00\text{ false alarms/hr}$ up to $\pm 15\%$ gain mismatch. Mismatches $\ge \pm 20\%$ elevate false alarms.

### Q17: What happens with noisy sensors?
**Answer**: Feature extraction (rolling mean and standard deviation) smooths Gaussian noise up to 1.5x nominal noise. Extreme noise (3.0x nominal) degrades static z-score thresholds and requires adaptive filtering.

### Q18: What is your validated classification accuracy?
**Answer**: In clean mission-level holdout validation across 100 independent test seeds (500–599), the validation Random Forest classifier achieved **99.84% accuracy** and a **macro F1 score of 0.9977**.

### Q19: How did you prevent machine learning data leakage?
**Answer**: We enforced a **strict mission-level holdout split**. Entire flight missions (seeds 100–399 TRAIN, 400–449 VAL, 500–599 TEST) were separated cleanly. Overlapping rolling windows never span splits.

### Q20: Why is RUL 90% Confidence Interval coverage marked "not established"?
**Answer**: Synthetic degradation linear regressions lack empirical multi-seed variance calibration. Point estimates achieved $0.91\text{ min}$ MAE, but interval bounds require empirical variance tuning.

### Q21: What is the biggest current technical limitation?
**Answer**: Reliance on synthetic simulation telemetry without real-world flight recorder (FDR) validation or physical hardware-in-the-loop (HIL) testbed integration.

### Q22: How would you deploy this on an operational UAV?
**Answer**: Compile the python Digital Twin and ML feature extraction logic into lightweight C/C++ / ONNX binaries and execute on an on-board ruggedized edge computer (e.g. NVIDIA Jetson Orin Industrial) connected to the aircraft CAN bus.

### Q23: What hardware would be required for edge deployment?
**Answer**: An IP67 ruggedized edge processing computer with dual galvanically isolated CAN 2.0B transceivers, MIL-STD-704F power supply, and MIL-SPEC wiring harness.

### Q24: Can this platform work with a real physical ECU?
**Answer**: Yes. Replacing the software `VirtualECU` with a physical CAN bus transceiver reading real ECU broadcast messages allows direct pipeline execution.

### Q25: How would you validate it on a real aircraft?
**Answer**: Via a phased airworthiness roadmap: (1) HIL CAN testbed simulation; (2) Ground engine test bench data recording; (3) Operational flight test telemetry replay; (4) DO-178C / DO-254 software certification.

### Q26: Can it handle multiple simultaneous compound faults?
**Answer**: The Isolation Forest detects compound anomalies. However, the Random Forest classifier is single-label and outputs the dominant primary fault class while classifier confidence probability drops.

### Q27: Why use both Isolation Forest AND Random Forest?
**Answer**: Isolation Forest provides unsupervised, label-free anomaly detection (answering *"Is something wrong?"*), while Random Forest provides supervised multi-class fault diagnosis (answering *"What is wrong?"*).

### Q28: What is the AI algorithmic detection latency?
**Answer**: Mean AI detection latency is $136.56\text{ s}$, which includes rolling window accumulation (60 s), 5-consecutive window confirmation (50 s), and physical fault ramp progression.

### Q29: What is the CAN bus transport latency?
**Answer**: Physical CAN transport latency is $0.10\text{ s}$ for 10 Hz frame broadcast. CAN transport is NOT responsible for the 136 s algorithmic confirmation delay.

### Q30: How does the system distinguish environmental effects from true faults?
**Answer**: Environmental shifts alter raw sensor values and twin predictions equally, keeping residuals ($z = \frac{x - \hat{x}}{\sigma}$) near zero. True physical faults cause raw sensors to deviate from twin predictions, creating large non-zero residual spikes ($|z| > 4.5$).
