"""AEROTWIN Mission Profile & Environmental Physics Simulation Layer.
SIH Problem Statement 26054 Telemetry Transport Layer.

Generates physics-informed environmental mission trajectories and metrics across:
CRUISE, HIGH_ALTITUDE, HOT_WEATHER, ENDURANCE, RAPID_THROTTLE, COMBINED_STRESS.
"""

from enum import Enum
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd

from engine import HealthyEngine, P_MAX, atmosphere
from actual import make_run

logger = logging.getLogger("AEROTWIN_MISSION")


class MissionProfileType(Enum):
    CRUISE = "CRUISE"
    HIGH_ALTITUDE = "HIGH_ALTITUDE"
    HOT_WEATHER = "HOT_WEATHER"
    ENDURANCE = "ENDURANCE"
    RAPID_THROTTLE = "RAPID_THROTTLE"
    COMBINED_STRESS = "COMBINED_STRESS"


class MissionPhase(Enum):
    GROUND = "GROUND"
    TAKEOFF = "TAKEOFF"
    CLIMB = "CLIMB"
    CRUISE = "CRUISE"
    HIGH_ALTITUDE_CRUISE = "HIGH_ALTITUDE_CRUISE"
    DESCENT = "DESCENT"
    LANDING = "LANDING"
    SHUTDOWN = "SHUTDOWN"


def determine_mission_phase(t: float, alt_m: float, thr: float, max_t: float) -> str:
    """Helper to classify telemetry timestamp into explicit flight mission phases."""
    if t < 60.0:
        return MissionPhase.GROUND.value
    elif t < 240.0:
        return MissionPhase.TAKEOFF.value
    elif t < 1200.0 and alt_m < 2500.0:
        return MissionPhase.CLIMB.value
    elif t >= (max_t - 600.0) and alt_m < 500.0:
        return MissionPhase.LANDING.value
    elif t >= (max_t - 1500.0):
        return MissionPhase.DESCENT.value
    elif alt_m >= 4500.0:
        return MissionPhase.HIGH_ALTITUDE_CRUISE.value
    else:
        return MissionPhase.CRUISE.value


def get_mission_trajectory(profile: MissionProfileType, dt: float = 1.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Generates time-series arrays for (t, rpm, thr, alt_m, dT_isa) for specified profile."""
    if profile == MissionProfileType.CRUISE:
        breakpoints = np.array([
            [0, 1400, 0.1, 0],
            [60, 5800, 1.0, 0],
            [300, 5800, 1.0, 300],
            [1200, 5500, 0.95, 3000],
            [4800, 5000, 0.75, 3000],
            [6600, 4300, 0.62, 1000],
            [7500, 3500, 0.30, 100],
            [7800, 1400, 0.10, 0]
        ])
        dT_isa = 0.0

    elif profile == MissionProfileType.HIGH_ALTITUDE:
        breakpoints = np.array([
            [0, 1400, 0.1, 0],
            [60, 5800, 1.0, 0],
            [600, 5800, 1.0, 3000],
            [1800, 5500, 0.98, 6000],
            [5400, 5200, 0.90, 6000],
            [6900, 4300, 0.60, 1000],
            [7800, 1400, 0.10, 0]
        ])
        dT_isa = -10.0

    elif profile == MissionProfileType.HOT_WEATHER:
        breakpoints = np.array([
            [0, 1400, 0.1, 0],
            [60, 5800, 1.0, 0],
            [300, 5800, 1.0, 300],
            [1200, 5500, 0.95, 2000],
            [4800, 5000, 0.80, 2000],
            [6600, 4300, 0.62, 500],
            [7500, 1400, 0.10, 0]
        ])
        dT_isa = 35.0

    elif profile == MissionProfileType.ENDURANCE:
        breakpoints = np.array([
            [0, 1400, 0.1, 0],
            [60, 5800, 1.0, 0],
            [1200, 5500, 0.95, 3000],
            [10800, 4800, 0.65, 3000],
            [13800, 4300, 0.60, 1000],
            [14400, 1400, 0.10, 0]
        ])
        dT_isa = 5.0

    elif profile == MissionProfileType.RAPID_THROTTLE:
        breakpoints = np.array([
            [0, 1400, 0.1, 0],
            [60, 5500, 0.9, 1000],
            [300, 3500, 0.30, 1000],   # 30%
            [600, 5200, 0.80, 1000],   # -> 80%
            [900, 3800, 0.40, 1000],   # -> 40%
            [1200, 5800, 1.00, 1000],  # -> 100%
            [1500, 4300, 0.50, 1000],  # -> 50%
            [1800, 3200, 0.20, 1000],  # -> 20%
            [2100, 4800, 0.70, 1000],
            [2400, 1400, 0.10, 0]
        ])
        dT_isa = 0.0

    elif profile == MissionProfileType.COMBINED_STRESS:
        breakpoints = np.array([
            [0, 1400, 0.1, 0],
            [60, 5800, 1.0, 0],
            [600, 5800, 1.0, 3000],
            [1500, 5500, 0.95, 5000],  # High alt + hot
            [2000, 3500, 0.30, 5000],  # Rapid throttle step
            [2500, 5800, 1.00, 5000],  # Max load
            [3000, 4300, 0.50, 5000],
            [4200, 4000, 0.45, 1000],
            [4800, 1400, 0.10, 0]
        ])
        dT_isa = 25.0

    else:
        raise ValueError(f"Unknown mission profile type: {profile}")

    max_t = breakpoints[-1, 0]
    t = np.arange(0, max_t, dt)
    rpm = np.interp(t, breakpoints[:, 0], breakpoints[:, 1])
    thr = np.interp(t, breakpoints[:, 0], breakpoints[:, 2])
    alt_m = np.interp(t, breakpoints[:, 0], breakpoints[:, 3])

    return t, rpm, thr, alt_m, dT_isa


def run_mission_profile(profile: MissionProfileType, fault: Optional[str] = None, sev: float = 1.0, seed: int = 0, t0: float = 3000, dt: float = 1.0) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Runs a full physics simulation or fault run for the specified mission profile."""
    t_arr, rpm_arr, thr_arr, alt_arr, dT_isa = get_mission_trajectory(profile, dt=dt)
    custom_mission = np.column_stack([t_arr[::300], rpm_arr[::300], thr_arr[::300], alt_arr[::300]])
    if custom_mission[-1, 0] < t_arr[-1]:
        custom_mission = np.vstack([custom_mission, [t_arr[-1], rpm_arr[-1], thr_arr[-1], alt_arr[-1]]])

    m, lab = make_run(
        fault=fault,
        sev=sev,
        t0=t0,
        seed=seed,
        dT_isa=dT_isa
    )

    # Attach explicit mission phase column
    max_t = m.t.max()
    m["mission_phase"] = [determine_mission_phase(t_val, a_val, th_val, max_t) for t_val, a_val, th_val in zip(m.t, m.alt, m.thr)]
    return m, lab


def calculate_mission_metrics(m: pd.DataFrame, ai_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Calculates comprehensive machine-readable JSON & CSV summary metrics for a flight mission."""
    t_span_h = (m.t.max() - m.t.min()) / 3600.0
    total_fuel_l = (m.fuel.sum() / 3600.0)
    avg_fuel_flow = m.fuel.mean()
    max_alt = m.alt.max()
    max_rpm = m.rpm.max()
    avg_rpm = m.rpm.mean()
    max_thr = m.thr.max()
    max_cht = m.cht.max()
    max_egt = m.egt.max()
    max_oil_t = m.oil_t.max()
    min_oil_p = m.oil_p.min()
    max_vib = m.vib.max()
    min_bat_v = m.battery_v.min()
    map_in = m["map"] if "map" in m else m["alt"] * 0 + 29.92
    engine_load_pct = (map_in / 29.92 * 100.0).max()

    metrics = {
        "duration_seconds": float(m.t.max() - m.t.min()),
        "duration_hours": float(t_span_h),
        "max_altitude_m": float(max_alt),
        "max_rpm": float(max_rpm),
        "avg_rpm": float(avg_rpm),
        "max_throttle_fraction": float(max_thr),
        "max_cht_c": float(max_cht),
        "max_egt_c": float(max_egt),
        "max_oil_t_c": float(max_oil_t),
        "min_oil_p_bar": float(min_oil_p),
        "max_vib_mms": float(max_vib),
        "min_battery_v": float(min_bat_v),
        "max_engine_load_pct": float(engine_load_pct),
        "total_fuel_consumed_l": float(total_fuel_l),
        "avg_fuel_flow_lh": float(avg_fuel_flow),
        "t_alarm": float(ai_result["t_alarm"]) if (ai_result and ai_result.get("t_alarm") is not None) else None,
        "diagnosed_fault": str(ai_result.get("fault")) if ai_result else "NOMINAL",
        "xai_explanation": str(ai_result.get("why")) if ai_result else "",
    }

    return metrics


class MissionReplayer:
    """Replays canonical telemetry stream through Digital Twin -> Residuals -> AI -> RUL pipeline."""

    def __init__(self, models=None):
        from detect import load
        self.models = models or load()

    def replay_mission(self, m: pd.DataFrame) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Replays telemetry dataframe and outputs AI diagnostic result + mission metrics summary."""
        from detect import analyze
        ai_res = analyze(m, self.models)
        metrics = calculate_mission_metrics(m, ai_res)
        return ai_res, metrics
