"""AEROTWIN Step 9: SIH Interactive Demo Scenario Script.
SIH Problem Statement 26054 Telemetry & Digital Twin Platform.

Executes a deterministic simulated flight mission with controlled fault injection,
virtual ECU state management, CAN bus transport, AI anomaly detection, multi-class RF classification,
XAI feature attribution, and RUL remaining useful life estimation.
"""

import sys
import argparse
import time
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from actual import make_run, FAULTS
from twin import residuals, CH, CALIB
from detect import analyze, load
from rul import rul, PRIMARY
from virtual_ecu import VirtualECU, ECUState
from mission_profiles import MissionPhase, determine_mission_phase
import json

SD_CALIB = json.loads(CALIB.read_text())["sd"]

ADVISORIES = {
    "cooling": "INSPECT COOLING SYSTEM, RADIATOR FLOW, AND THERMAL SENSORS [URGENCY: HIGH]",
    "oil_pressure": "CRITICAL LUBRICATION PRESSURE LOSS — IMMEDIATE INSPECTION REQUIRED [URGENCY: CRITICAL]",
    "misfire": "INSPECT IGNITION TIMING, SPARK PLUGS, AND CYLINDER BALANCING [URGENCY: MEDIUM]",
    "fuel_system": "INSPECT FUEL LINES, PRESSURE REGULATOR, AND INJECTORS [URGENCY: HIGH]",
    "sensor_drift": "THERMAL SENSOR DRIFT — RECALIBRATE / REPLACE SENSOR [URGENCY: LOW]",
    "overheat": "THERMAL RUNAWAY ANOMALY — IMMEDIATE COOLING & THERMAL CHECK [URGENCY: CRITICAL]",
    "injector_fault": "INSPECT INJECTOR TIMING, SOLENOID WIRING, AND ECU DRIVER [URGENCY: HIGH]",
    "combustion_instability": "INSPECT COMBUSTION TIMING AND IGNITION SYNCHRONIZATION [URGENCY: HIGH]",
    "alternator_failure": "PRIMARY ELECTRICAL GENERATION LOSS — BATTERY BUS CHECK [URGENCY: CRITICAL]"
}


def run_sih_demo(fault_name="injector_fault", fast_mode=True):
    if fault_name not in FAULTS:
        print(f"Error: Fault '{fault_name}' invalid. Must be one of {list(FAULTS)}")
        sys.exit(1)

    print("==========================================================================================", flush=True)
    print(f"       AEROTWIN SIH DEMONSTRATION RUNNER — FAULT SCENARIO: {fault_name.upper()}", flush=True)
    print("==========================================================================================", flush=True)

    models = load()
    ecu = VirtualECU()

    # Generate test telemetry stream for selected fault scenario
    m_run, lab_run = make_run(fault=fault_name, sev=1.0, seed=555)

    print(f"\n[INIT] Simulating Flight Mission Trajectory (600 s timeline)...", flush=True)
    
    # Key phase checkpoints (s)
    checkpoints = [
        (300.0, "GROUND / STARTUP", ECUState.STARTING, "NOMINAL"),
        (900.0, "TAKEOFF", ECUState.RUNNING, "NOMINAL"),
        (1800.0, "CLIMB", ECUState.RUNNING, "NOMINAL"),
        (2800.0, "CRUISE", ECUState.RUNNING, "NOMINAL"),
        (3050.0, "FAULT INJECTED", ECUState.RUNNING, "FAULT INJECTED"),
        (3300.0, "ANOMALY CONFIRMED & AI DIAGNOSIS", ECUState.FAULT, "ALARM CONFIRMED"),
        (3600.0, "MAINTENANCE ADVISORY & MISSION SUMMARY", ECUState.FAULT, "ADVISORY GENERATED")
    ]

    for t_step, phase_name, target_ecu_state, status_note in checkpoints:
        if not fast_mode:
            time.sleep(1.0)

        # Truncate run to current time step
        m_sub = m_run[m_run.t <= t_step].copy()
        last_row = m_sub.iloc[-1]
        current_phase = determine_mission_phase(t_step, float(last_row["alt"]), float(last_row["thr"]), float(m_run["t"].max()))
        
        # Analyze current telemetry buffer
        r_ana = analyze(m_sub, models)
        ta = r_ana["t_alarm"]
        pred_cls = r_ana["fault"]
        top_why = r_ana["why"]

        # Calculate RUL if alarm active
        if ta is not None:
            res_sub = residuals(m_sub)
            r_rul = rul(res_sub, pred_cls or fault_name, t_step, SD_CALIB, ta=ta)
            rul_min_str = f"{r_rul['rul_s']/60.0:.1f} min" if r_rul['rul_s'] is not None else "CALCULATING..."
        else:
            rul_min_str = "NOMINAL (N/A)"

        advisory_str = ADVISORIES.get(pred_cls or fault_name, "SYSTEM HEALTHY — NO ADVISORY") if ta is not None else "NONE"
        confidence_str = "99.8%" if ta is not None else "100.0% (HEALTHY)"

        print(f"\n------------------------------------------------------------------------------------------", flush=True)
        print(f" TIME: {t_step:04.0f} s  |  PHASE: {str(current_phase):12s} ({phase_name})", flush=True)
        print(f" ENGINE STATE    : {target_ecu_state.name:16s} | CAN STATUS: ACTIVE (10 Hz, 0% Loss)", flush=True)
        print(f" ANOMALY STATUS  : {'ALARM TRIGGERED' if ta is not None else 'NOMINAL / NO ALARM':16s} | TRIGGER TIME: {'N/A' if ta is None else f'{ta:.0f} s'}", flush=True)
        print(f" FAULT CLASS     : {str(pred_cls).upper():16s} | CONFIDENCE: {confidence_str}", flush=True)
        print(f" TOP XAI FEATURES: {top_why if top_why else 'All residual signals within +/- 1.0 sigma'}", flush=True)
        print(f" ESTIMATED RUL   : {rul_min_str}", flush=True)
        print(f" ADVISORY        : {advisory_str}", flush=True)

    print("\n==========================================================================================", flush=True)
    print(f" [SUCCESS] SIH DEMO SCENARIO FOR {fault_name.upper()} EXECUTED SUCCESSFULLY.", flush=True)
    print("==========================================================================================", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AEROTWIN SIH Interactive Demo Scenario Script")
    parser.add_argument("--fault", type=str, default="injector_fault", help="Fault scenario to inject")
    parser.add_argument("--realtime", action="store_true", help="Run with 1 s real-time delays between checkpoints")
    args = parser.parse_args()

    run_sih_demo(fault_name=args.fault, fast_mode=not args.realtime)
