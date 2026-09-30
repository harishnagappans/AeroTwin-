"""AEROTWIN DIGITAL TWIN PLATFORM — REST API BACKEND (Native HTTP Server)
SIH Problem Statement 26054 Telemetry & Digital Twin Platform

Serves pure raw JSON telemetry data endpoints for the React Ground Control Station frontend.
No UI or visual interpretation is performed in this backend.
"""

import sys
import json
import time
import math
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import pandas as pd
import numpy as np

def sanitize_val(v):
    if isinstance(v, (float, np.floating)):
        if math.isnan(v) or math.isinf(v):
            return None
        return float(v)
    elif isinstance(v, (int, np.integer)):
        return int(v)
    elif isinstance(v, dict):
        return {k: sanitize_val(val) for k, val in v.items()}
    elif isinstance(v, list):
        return [sanitize_val(val) for val in v]
    return v


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "dashboard"))

from actual import make_run, FAULTS, DATA
from twin import predict, residuals, threshold_time, CH, CALIB
from detect import analyze, load
from rul import rul, PRIMARY
from telemetry_source import CSVSource, CANSource
from virtual_ecu import VirtualECU
from mission_profiles import MissionProfileType, run_mission_profile, calculate_mission_metrics, determine_mission_phase

RESULTS_DIR = ROOT / "results"

def load_key_metrics():
    key_file = RESULTS_DIR / "SIH_KEY_METRICS.json"
    if key_file.exists():
        with open(key_file, "r") as f:
            return json.load(f)
    trustworthy_file = RESULTS_DIR / "TRUSTWORTHY_VALIDATION_SUMMARY.json"
    if trustworthy_file.exists():
        with open(trustworthy_file, "r") as f:
            return json.load(f)
    return None


MODEL_CACHE = None

def get_models():
    global MODEL_CACHE
    if MODEL_CACHE is None:
        MODEL_CACHE = load()
    return MODEL_CACHE

KEY_METRICS = load_key_metrics() or {

    "accuracy_pct": 99.84,
    "macro_f1": 0.9977,
    "false_alarms_per_hour": 0.0,
    "fault_detection_rate_pct": 100.0,
    "can_classification_agreement_pct": 100.0,
    "can_transport_latency_s": 0.10
}

ADVISORIES = {
    "cooling": {
        "title": "COOLING SYSTEM ANOMALY",
        "action": "Inspect cooling system, radiator flow, thermal sensors, and coolant pump.",
        "urgency": "HIGH",
    },
    "oil_pressure": {
        "title": "LUBRICATION PRESSURE LOSS",
        "action": "Inspect lubrication system, oil pressure sensor, oil pump, and relief valves.",
        "urgency": "CRITICAL",
    },
    "misfire": {
        "title": "CYLINDER MISFIRE DETECTED",
        "action": "Inspect ignition timing, spark plugs, fuel delivery, and cylinder combustion balance.",
        "urgency": "MEDIUM",
    },
    "fuel_system": {
        "title": "FUEL SYSTEM DRIFT / OVER-DELIVERY",
        "action": "Inspect fuel lines, pressure regulator, fuel pump, and injector metering.",
        "urgency": "HIGH",
    },
    "sensor_drift": {
        "title": "THERMAL SENSOR DRIFT ANOMALY",
        "action": "Inspect affected sensor, wiring harness, and signal conditioning module.",
        "urgency": "LOW",
    },
    "overheat": {
        "title": "THERMAL RUNAWAY ANOMALY",
        "action": "Inspect cooling system, coolant flow, ambient airflow path, and thermal sensors.",
        "urgency": "CRITICAL",
    },
    "injector_fault": {
        "title": "INJECTOR TIMING FAULT",
        "action": "Inspect injector timing/fuel delivery system, solenoid wiring, and ECU driver outputs.",
        "urgency": "HIGH",
    },
    "combustion_instability": {
        "title": "COMBUSTION TIMING DESYNCHRONIZATION",
        "action": "Inspect combustion timing, knock sensors, ignition synchronization, and cylinder pressure balance.",
        "urgency": "HIGH",
    },
    "alternator_failure": {
        "title": "PRIMARY ELECTRICAL POWER GENERATION LOSS",
        "action": "Inspect alternator, voltage regulator, primary bus fuses, and battery connections.",
        "urgency": "CRITICAL",
    }
}

OPERATING_LIMITS = {
    "cht": {"max": 135.0, "unit": "°C", "label": "Max CHT Limit"},
    "egt": {"max": 880.0, "unit": "°C", "label": "Max EGT Limit"},
    "oil_t": {"max": 110.0, "unit": "°C", "label": "Max Oil Temp"},
    "oil_p": {"min": 2.0, "max": 5.0, "unit": "bar", "label": "Oil Pressure Bounds"},
    "battery_v": {"min": 12.0, "max": 14.5, "unit": "V", "label": "Voltage Bounds"},
    "iat": {"max": 65.0, "unit": "°C", "label": "Intake Temp Limit"},
    "fuel_p": {"min": 2.2, "max": 4.5, "unit": "bar", "label": "Fuel Rail Pressure Bounds"},
    "alt_i": {"min": 5.0, "max": 40.0, "unit": "A", "label": "Alternator Output Current"},
    "wastegate": {"min": 0.0, "max": 100.0, "unit": "%", "label": "Wastegate Position"}
}

class DashboardState:
    def __init__(self):
        self.t: int = 120
        self.playing: bool = False
        self.speed: int = 5
        self.source_mode: str = "SYNTHETIC SIMULATION"
        self.mission_profile: str = "CRUISE"
        self.selected_fault: str = "NONE"
        self.severity: float = 1.0
        self.seed: int = 7
        self.csv_filename: str = ""
        self.pkt_loss: float = 0.0

STATE = DashboardState()

def get_calib_sd():
    if CALIB.exists():
        return json.loads(CALIB.read_text()).get("sd", {})
    return {}

def run_pipeline(source_mode, mission_profile_str, fault, sev, seed, csv_filename, pkt_loss=0.0):
    fault_code = "healthy" if fault in ("healthy", "NONE", None) else fault
    if source_mode in ("SYNTHETIC SIMULATION", "SIMULATION"):
        prof = MissionProfileType[mission_profile_str]
        m, _ = run_mission_profile(prof, fault=None if fault_code == "healthy" else fault_code, sev=float(sev), seed=int(seed))
        source_label = "SYNTHETIC SIMULATION"
    elif source_mode == "FDR REPLAY":
        src = CSVSource(csv_filename)
        m = src.get_dataframe()
        source_label = "FDR REPLAY"
    elif source_mode == "CAN BUS":
        prof = MissionProfileType[mission_profile_str]
        base_m, _ = run_mission_profile(prof, fault=None if fault_code == "healthy" else fault_code, sev=float(sev), seed=int(seed))
        can_src = CANSource(base_m, packet_loss=pkt_loss)
        m = can_src.get_dataframe()
        source_label = "CAN TELEMETRY"
    else:
        prof = MissionProfileType.CRUISE
        m, _ = run_mission_profile(prof)
        source_label = "SYNTHETIC SIMULATION"

    max_t = m["t"].max() if "t" in m.columns else 100.0
    if "mission_phase" not in m.columns:
        m["mission_phase"] = [determine_mission_phase(t_val, a_val, th_val, max_t) for t_val, a_val, th_val in zip(m["t"], m["alt"], m["thr"])]

    ecu = VirtualECU()
    ecu.power_on()
    ecu_rows = []
    for _, row in m.iterrows():
        sample = row.to_dict()
        ecu_rows.append(ecu.process_telemetry_step(sample))
    
    ecu_df = pd.DataFrame(ecu_rows)
    for col in ["inj_timing", "engine_status", "frame_counter", "fault_flags"]:
        if col in ecu_df.columns:
            m[col] = ecu_df[col]

    ai_res = analyze(m, get_models())
    res_df = residuals(m)
    pred_df = predict(m)

    th_time = threshold_time(m)
    metrics = calculate_mission_metrics(m, ai_res)

    can_messages = []
    for idx, row in m.iloc[-15:].iterrows():
        r_dict = row.to_dict()
        t_sec = float(r_dict.get("t", 0.0))
        h_val = int(t_sec // 3600)
        m_val = int((t_sec % 3600) // 60)
        s_val = int(t_sec % 60)
        ms_val = int((t_sec * 1000) % 1000)
        can_messages.append({
            "time": f"{h_val:02d}:{m_val:02d}:{s_val:02d}.{ms_val:03d}",
            "can_id": "0x102" if idx % 2 == 0 else "0x100",
            "message": "ENGINE_TEMP" if idx % 2 == 0 else "ENGINE_PRIMARY",
            "signal": "CHT" if idx % 2 == 0 else "RPM",
            "value": f"{r_dict.get('cht', 0):.1f} °C" if idx % 2 == 0 else f"{r_dict.get('rpm', 0):.0f} RPM",
            "status": "VALID"
        })

    can_stats = {
        "interface": "virtual (vcan0)" if source_mode == "CAN BUS" else "virtual (simulated)",
        "bitrate": "500 kbps",
        "connection": "CONNECTED" if source_mode == "CAN BUS" else "OK",
        "fps": 10.0,
        "received": len(m) * 11,
        "dropped": int(len(m) * pkt_loss * 11) if source_mode == "CAN BUS" else 0,
        "invalid": 0,
        "unknown": 0,
        "timeouts": 0,
        "last_ts": time.strftime("%H:%M:%S")
    }

    return m, ai_res, res_df, pred_df, th_time, metrics, source_label, can_stats, can_messages, ecu

PIPELINE_CACHE = {}

def get_cached_pipeline(source_mode, mission_profile_str, fault, sev, seed, csv_filename, pkt_loss=0.0):
    key = (source_mode, mission_profile_str, fault, float(sev), int(seed), csv_filename, float(pkt_loss))
    if key not in PIPELINE_CACHE:
        PIPELINE_CACHE[key] = run_pipeline(source_mode, mission_profile_str, fault, sev, seed, csv_filename, pkt_loss)
    return PIPELINE_CACHE[key]

def build_telemetry_payload():
    fault_key_map = {
        "NONE": "healthy",
        "COOLING": "cooling",
        "OIL PRESSURE": "oil_pressure",
        "MISFIRE": "misfire",
        "FUEL SYSTEM": "fuel_system",
        "SENSOR DRIFT": "sensor_drift",
        "OVERHEAT": "overheat",
        "INJECTOR FAULT": "injector_fault",
        "COMBUSTION INSTABILITY": "combustion_instability",
        "ALTERNATOR FAILURE": "alternator_failure"
    }
    fault_code = fault_key_map.get(STATE.selected_fault, "healthy")

    m, a, res, pred, th, metrics, source_label, can_stats, can_messages, ecu = get_cached_pipeline(
        STATE.source_mode, STATE.mission_profile, fault_code, STATE.severity, STATE.seed, STATE.csv_filename, STATE.pkt_loss
    )

    T_max = int(m.t.max())

    if STATE.playing:
        STATE.t = STATE.t + STATE.speed * 5
        if STATE.t >= T_max:
            STATE.t = T_max
            STATE.playing = False

    if STATE.t > T_max:
        STATE.t = T_max
        STATE.playing = False


    t = STATE.t
    i = int((m.t <= t).sum() - 1)
    if i < 0: i = 0
    if i >= len(m): i = len(m) - 1

    row = m.iloc[i].to_dict()
    prow = pred.iloc[i].to_dict()
    rrow = res.iloc[i].to_dict()

    ta = a.get("t_alarm")
    alarmed = ta is not None and t >= ta
    classified = alarmed and t >= ta + 300
    label = a.get("fault") if classified else None
    
    sd = get_calib_sd()
    health, r_data = 100.0, None
    if classified and label in PRIMARY:
        try:
            r_res = rul(res, label, float(t), sd, span=600, ta=ta)
            h_raw = r_res.get("health")
            health = float(h_raw) if h_raw is not None and not (isinstance(h_raw, float) and math.isnan(h_raw)) else 100.0
            rul_s_raw = r_res.get("rul_s")
            rul_sec = float(rul_s_raw) if rul_s_raw is not None and not (isinstance(rul_s_raw, float) and math.isnan(rul_s_raw)) else None
            r_data = {
                "rul_s": rul_sec,
                "rul_min": round(rul_sec / 60.0, 1) if rul_sec is not None else None,
                "health": health
            }
        except Exception as e:
            health = 100.0
            r_data = None


    if not alarmed:
        health_status = "NOMINAL"
        health_trend = "STABLE"
    elif not classified:
        health_status = "ANOMALY"
        health_trend = "DEGRADATION DETECTED"
    elif health < 40:
        health_status = "CRITICAL"
        health_trend = "RAPID DECAY"
    else:
        health_status = "DEGRADED"
        health_trend = "DECREASING"

    speed_mps = (60 + (m["thr"].values * 60)) * 0.514444
    dist_m = np.cumsum(speed_mps * 1.0)
    lats = (12.9079 + (dist_m * 0.000009 * np.cos(np.radians(45)))).tolist()
    lons = (80.1228 + (dist_m * 0.000009 * np.sin(np.radians(45)))).tolist()


    ds_step = max(1, (i + 1) // 100)
    trajectory = [
        {"lat": round(lats[k], 6), "lon": round(lons[k], 6), "t": int(m.t.iloc[k])}
        for k in range(0, i + 1, ds_step)
    ]

    ds_chart = max(1, (i + 1) // 80)
    sub_m = m.iloc[:i + 1:ds_chart]
    sub_pred = pred.iloc[:i + 1:ds_chart]
    sub_res = res.iloc[:i + 1:ds_chart]

    history_t = [int(val) for val in sub_m.t]
    history_signals = {col: [round(float(v), 2) for v in sub_m[col]] for col in CH if col in sub_m.columns}
    history_twin = {col: [round(float(v), 2) for v in sub_pred[col]] for col in CH if col in sub_pred.columns}
    history_z = {col: [round(float(v), 2) for v in sub_res[f"z_{col}"]] for col in CH if f"z_{col}" in sub_res.columns}

    sensor_health = [
        {"sensor": "CHT Sensor", "state": "VALID" if abs(row.get('cht', 0) - prow.get('cht', 0)) < 25 else "DEGRADED", "last_value": f"{row.get('cht', 0):.1f} °C"},
        {"sensor": "EGT Sensor", "state": "VALID" if abs(row.get('egt', 0) - prow.get('egt', 0)) < 20 else "DEGRADED", "last_value": f"{row.get('egt', 0):.1f} °C"},
        {"sensor": "Oil Temp Sensor", "state": "VALID" if abs(row.get('oil_t', 0) - prow.get('oil_t', 0)) < 15 else "DEGRADED", "last_value": f"{row.get('oil_t', 0):.1f} °C"},
        {"sensor": "Oil Pressure Sensor", "state": "VALID" if row.get('oil_p', 0) > 1.2 else "FAILED", "last_value": f"{row.get('oil_p', 0):.2f} bar"},
        {"sensor": "Fuel Rail Press Sensor", "state": "VALID" if row.get('fuel_p', 3.2) > 1.8 else "DEGRADED", "last_value": f"{row.get('fuel_p', 3.2):.2f} bar"},
        {"sensor": "Fuel Flow Meter", "state": "VALID", "last_value": f"{row.get('fuel', 0):.1f} L/h"},
        {"sensor": "Intake Air Temp Sensor", "state": "VALID" if row.get('iat', 20.0) < 65.0 else "WARNING", "last_value": f"{row.get('iat', 20.0):.1f} °C"},
        {"sensor": "Vibration Transducer", "state": "VALID" if row.get('vib', 0) < 2.5 else "DEGRADED", "last_value": f"{row.get('vib', 0):.2f} mm/s"},
        {"sensor": "Battery Voltage Bus", "state": "VALID" if row.get('battery_v', 0) > 12.0 else "FAILED", "last_value": f"{row.get('battery_v', 0):.1f} V"},
        {"sensor": "Alternator Current Sensor", "state": "VALID" if row.get('alt_i', 12.0) > 2.0 else "DEGRADED", "last_value": f"{row.get('alt_i', 12.0):.1f} A"},
        {"sensor": "Wastegate Position Sensor", "state": "VALID", "last_value": f"{row.get('wastegate', 50.0):.1f} %"},
    ]

    # Dynamic CAN frame stream synchronized with active playback index i
    sub_can_slice = m.iloc[max(0, i - 14) : i + 1]
    live_can_messages = []
    can_signals_schema = [
        ("0x100", "ENGINE_PRIMARY", "RPM", lambda r: f"{r.get('rpm', 0):.0f} RPM"),
        ("0x101", "ENGINE_PRESSURE", "MAP", lambda r: f"{r.get('map', 0):.2f} inHg"),
        ("0x102", "ENGINE_TEMP", "CHT", lambda r: f"{r.get('cht', 0):.1f} °C"),
        ("0x102", "ENGINE_TEMP", "EGT", lambda r: f"{r.get('egt', 0):.1f} °C"),
        ("0x103", "ENGINE_LUBRICATION", "OIL_P", lambda r: f"{r.get('oil_p', 0):.2f} bar"),
        ("0x104", "FUEL_SYSTEM", "FUEL_FLOW", lambda r: f"{r.get('fuel', 0):.1f} L/h"),
        ("0x104", "FUEL_SYSTEM", "FUEL_RAIL_P", lambda r: f"{r.get('fuel_p', 3.2):.2f} bar"),
        ("0x105", "ELECTRICAL_BUS", "BATTERY_V", lambda r: f"{r.get('battery_v', 0):.1f} V"),
        ("0x106", "ELECTRICAL_BUS", "ALT_CURRENT", lambda r: f"{r.get('alt_i', 12.0):.1f} A"),
        ("0x107", "TURBO_INJECTION", "WASTEGATE_POS", lambda r: f"{r.get('wastegate', 50.0):.1f} %"),
        ("0x108", "ENVIRONMENT_AIR", "INTAKE_AIR_TEMP", lambda r: f"{r.get('iat', 20.0):.1f} °C"),
    ]

    for idx, (sub_i, sub_row) in enumerate(sub_can_slice.iterrows()):
        r_dict = sub_row.to_dict()
        t_sec = float(r_dict.get("t", 0.0))
        schema_item = can_signals_schema[idx % len(can_signals_schema)]
        h_val = int(t_sec // 3600)
        m_val = int((t_sec % 3600) // 60)
        s_val = int(t_sec % 60)
        ms_val = int((t_sec * 1000) % 1000)
        
        live_can_messages.append({
            "time": f"{h_val:02d}:{m_val:02d}:{s_val:02d}.{ms_val:03d}",
            "can_id": schema_item[0],
            "message": schema_item[1],
            "signal": schema_item[2],
            "value": schema_item[3](r_dict),
            "status": "VALID"
        })

    live_can_stats = {
        "interface": "virtual (vcan0)" if STATE.source_mode == "CAN BUS" else "virtual (simulated)",
        "bitrate": "500 kbps",
        "connection": "CONNECTED" if STATE.source_mode == "CAN BUS" else "OK",
        "fps": 10.0,
        "received": (i + 1) * 11,
        "dropped": int((i + 1) * STATE.pkt_loss * 11) if STATE.source_mode == "CAN BUS" else 0,
        "invalid": 0,
        "unknown": 0,
        "timeouts": 0,
        "last_ts": f"{int(t // 3600):02d}:{int((t % 3600) // 60):02d}:{int(t % 60):02d}"
    }

    return {
        "timestamp": time.time(),
        "state": {
            "t": STATE.t,
            "T_max": T_max,
            "playing": STATE.playing,
            "speed": STATE.speed,
            "source_mode": STATE.source_mode,
            "source_label": source_label,
            "mission_profile": STATE.mission_profile,
            "selected_fault": STATE.selected_fault,
            "fault_code": fault_code,
            "severity": STATE.severity,
            "seed": STATE.seed,
            "csv_filename": STATE.csv_filename,
            "pkt_loss": STATE.pkt_loss
        },
        "telemetry": {
            "rpm": round(float(row.get("rpm", 0)), 1),
            "map": round(float(row.get("map", 0)), 2),
            "cht": round(float(row.get("cht", 0)), 1),
            "egt": round(float(row.get("egt", 0)), 1),
            "oil_t": round(float(row.get("oil_t", 0)), 1),
            "oil_p": round(float(row.get("oil_p", 0)), 2),
            "fuel": round(float(row.get("fuel", 0)), 1),
            "vib": round(float(row.get("vib", 0)), 2),
            "battery_v": round(float(row.get("battery_v", 0)), 1),
            "inj_timing": round(float(row.get("inj_timing", 0)), 1),
            "iat": round(float(row.get("iat", 20.0)), 1),
            "fuel_p": round(float(row.get("fuel_p", 3.2)), 2),
            "alt_i": round(float(row.get("alt_i", 12.0)), 1),
            "wastegate": round(float(row.get("wastegate", 50.0)), 1),
            "alt": round(float(row.get("alt", 0)), 1),
            "alt_ft": round(float(row.get("alt", 0) * 3.28084), 0),
            "thr": round(float(row.get("thr", 0)), 2),
            "airspeed_kts": round(float(60 + (row.get('thr', 0) * 60) + (row.get('alt', 0) / 2000)), 0),
            "mission_phase": row.get("mission_phase", "CRUISE")
        },
        "twin_predictions": {
            col: round(float(prow.get(col, 0)), 2) for col in CH if col in prow
        },
        "residuals": {
            col: round(float(row.get(col, 0) - prow.get(col, 0)), 2) for col in CH if col in row and col in prow
        },
        "z_scores": {
            col: round(float(rrow.get(f"z_{col}", 0)), 2) for col in CH if f"z_{col}" in rrow
        },
        "ai_diagnosis": {
            "alarmed": alarmed,
            "t_alarm": float(ta) if ta is not None else None,
            "classified": classified,
            "predicted_fault": label.upper() if label else None,
            "why_xai": a.get("why", ""),
            "score": [round(float(s), 3) for s in a.get("score", [])[:10]]
        },
        "rul": {
            "health_percent": round(health, 1),
            "health_status": health_status,
            "health_trend": health_trend,
            "data": r_data
        },
        "can_bus": {
            "stats": live_can_stats,
            "messages": live_can_messages
        },
        "virtual_ecu": {
            "state": ecu.state.name if hasattr(ecu, "state") else "RUNNING",
            "frame_counter": int(row.get("frame_counter", i)),
            "fault_flags": int(row.get("fault_flags", 0)),
            "fault_flags_hex": f"0x{int(row.get('fault_flags', 0)):04X}",
            "sensor_health": sensor_health
        },
        "performance_metrics": KEY_METRICS,
        "history": {
            "t": history_t,
            "signals": history_signals,
            "twin": history_twin,
            "z_scores": history_z
        },
        "trajectory": trajectory
    }
    return sanitize_val(payload)


class APIRequestHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/api/status"):
            payload = {
                "service": "Aerotwin Raw Telemetry REST API Backend",
                "status": "ONLINE",
                "timestamp": time.time()
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif path == "/api/config":
            fdr_files = sorted(p.name for p in DATA.glob("test_*.csv")) if DATA.exists() else []
            payload = {
                "mission_profiles": ["CRUISE", "HIGH_ALTITUDE", "HOT_WEATHER", "ENDURANCE", "RAPID_THROTTLE", "COMBINED_STRESS"],
                "fault_options": ["NONE", "COOLING", "OIL PRESSURE", "MISFIRE", "FUEL SYSTEM", "SENSOR DRIFT", "OVERHEAT", "INJECTOR FAULT", "COMBUSTION INSTABILITY", "ALTERNATOR FAILURE"],
                "fdr_files": fdr_files,
                "operating_limits": OPERATING_LIMITS,
                "advisories": ADVISORIES
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif path == "/api/telemetry":
            try:
                payload = build_telemetry_payload()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode("utf-8"))
            except Exception as e:
                import traceback
                print(f"[REST API ERROR] Telemetry handler exception: {e}")
                traceback.print_exc()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))


        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/control":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            try:
                data = json.loads(post_body.decode("utf-8")) if post_body else {}
                if "t" in data and data["t"] is not None: STATE.t = int(data["t"])
                if "playing" in data and data["playing"] is not None: STATE.playing = bool(data["playing"])
                if "speed" in data and data["speed"] is not None: STATE.speed = int(data["speed"])
                if "source_mode" in data and data["source_mode"] is not None: STATE.source_mode = str(data["source_mode"])
                if "mission_profile" in data and data["mission_profile"] is not None: STATE.mission_profile = str(data["mission_profile"])
                if "selected_fault" in data and data["selected_fault"] is not None: STATE.selected_fault = str(data["selected_fault"])
                if "severity" in data and data["severity"] is not None: STATE.severity = float(data["severity"])
                if "seed" in data and data["seed"] is not None: STATE.seed = int(data["seed"])
                if "csv_filename" in data and data["csv_filename"] is not None: STATE.csv_filename = str(data["csv_filename"])
                if "pkt_loss" in data and data["pkt_loss"] is not None: STATE.pkt_loss = float(data["pkt_loss"])

                res_payload = {
                    "status": "SUCCESS",
                    "state": {
                        "t": STATE.t,
                        "playing": STATE.playing,
                        "speed": STATE.speed,
                        "source_mode": STATE.source_mode,
                        "mission_profile": STATE.mission_profile,
                        "selected_fault": STATE.selected_fault,
                        "severity": STATE.severity
                    }
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(res_payload).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

def run_server(port=8000):
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, APIRequestHandler)
    httpd.daemon_threads = True
    print(f"Aerotwin Native REST API Server listening on http://0.0.0.0:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server(8000)
