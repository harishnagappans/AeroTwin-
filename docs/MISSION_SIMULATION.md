# AEROTWIN Advanced Mission & Environmental Digital Twin Simulation

## Mandatory Project Disclaimer
> [!IMPORTANT]
> **Simulated mission datasets are generated via physics engine mathematical models for demonstration purposes and do not represent actual flight recorder logs from certified aircraft.**

---

## 1. Overview & Physics-Informed Philosophy

The AEROTWIN Mission Simulation Layer (`src/mission_profiles.py`) tests the Digital Twin's physics adaptability across extreme environmental stressors (High Altitude, Hot Weather, Endurance, Rapid Throttle Dynamics, Combined Environmental Stress).

### The Key Principle:
When an aircraft operates in extreme ambient conditions (e.g., $45^\circ\text{C}$ ground ambient or $6000\text{m}$ pressure altitude), cylinder head temperatures and exhaust gas temperatures naturally increase due to reduced air density and elevated intake temperatures.

**A naive static threshold system would trigger false overheat alarms.**  
**The AEROTWIN Digital Twin adapts its healthy physics baseline to the environment.** Because the twin computes the expected thermal rise, the residual ($\text{Actual} - \text{Twin}$) remains near $0\sigma$, preventing false alarms while remaining hypersensitive to true mechanical degradation.

---

## 2. Mission Profile Matrix

| Profile Name | Altitude Stress | Ambient Temp Stress | Dynamic Stress | Primary Objective |
| :--- | :--- | :--- | :--- | :--- |
| `CRUISE` | Standard (0 - 3000m) | ISA Baseline ($15^\circ\text{C}$) | Nominal | Baseline comparison mission |
| `HIGH_ALTITUDE` | High ($6000\text{m}$ DA) | ISA Troposphere ($-15^\circ\text{C}$) | Sustained Cruise | Stress engine density & MAP limits |
| `HOT_WEATHER` | Standard ($2000\text{m}$) | Extreme ($+35^\circ\text{C}$ ISA) | High Load | Test healthy thermal twin adaptation |
| `ENDURANCE` | Standard ($3000\text{m}$) | Mild ($+5^\circ\text{C}$) | Long Duration (4h) | Fuel & electrical drain tracking |
| `RAPID_THROTTLE` | Moderate ($1000\text{m}$) | Nominal | Rapid Steps (30% to 100%) | Test first-order thermal lag (`_lag`) |
| `COMBINED_STRESS` | Extreme ($5000\text{m}$) | Hot ($+25^\circ\text{C}$ ISA) | High Load + Rapid Steps | Maximum combined environmental stress |

---

## 3. Mission Phase Schema (`MissionPhase`)

Every telemetry sample is assigned an explicit flight phase:
- `GROUND`: Engine warmup (`t < 60s`)
- `TAKEOFF`: Full throttle ground roll (`60s <= t < 240s`)
- `CLIMB`: Max continuous power climb (`240s <= t < 1200s`)
- `CRUISE`: Steady-state cruise flight
- `HIGH_ALTITUDE_CRUISE`: Cruise at pressure altitude $\ge 4500\text{m}$
- `DESCENT`: Reduced power descent (`max_t - 1500s`)
- `LANDING`: Final approach & touch down (`alt < 500m`)
- `SHUTDOWN`: Engine spooling down

---

## 4. Machine-Readable Mission Metrics Schema (JSON)

Each mission execution produces a JSON summary dictionary:

```json
{
  "duration_seconds": 7800.0,
  "duration_hours": 2.17,
  "max_altitude_m": 3000.0,
  "max_rpm": 5800.0,
  "avg_rpm": 4850.2,
  "max_throttle_fraction": 1.0,
  "max_cht_c": 118.5,
  "max_egt_c": 835.0,
  "max_oil_t_c": 98.2,
  "min_oil_p_bar": 2.1,
  "max_vib_mms": 1.4,
  "min_battery_v": 13.8,
  "max_engine_load_pct": 91.9,
  "total_fuel_consumed_l": 48.6,
  "avg_fuel_flow_lh": 22.4,
  "t_alarm": 3050.0,
  "diagnosed_fault": "oil_pressure",
  "xai_explanation": "oil_p -8.0sigma, inj_timing +0.2sigma"
}
```

---

## 5. Replay Architecture (`MissionReplayer`)

`MissionReplayer` ingests any historical or synthetic CSV telemetry dataframe containing canonical fields:
`[t, rpm, thr, alt, t_amb, map, cht, egt, oil_t, oil_p, fuel, battery_v, inj_timing, vib, mission_phase]`

It routes the stream through the exact same Digital Twin -> Residual Normalization -> Isolation Forest -> Random Forest -> RUL pipeline, ensuring 100% diagnostic consistency across real-time and post-flight modes.
