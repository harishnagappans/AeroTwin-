"""AEROTWIN Prototype CAN Protocol Specification & Encoding Layer.
SIH Problem Statement 26054 Telemetry Transport Layer.

DISCLAIMER:
AEROTWIN Prototype CAN Protocol is a project-defined telemetry protocol for simulation
and hardware-in-the-loop demonstration. It is not claimed to be the proprietary CAN
protocol of the Rotax 912 S/ULS ECU.
"""

import struct
from typing import Dict, Any, Tuple, Optional

# CAN Message IDs (11-bit Standard Identifiers)
CAN_ID_ENGINE_SPEED = 0x100
CAN_ID_ENGINE_PRESSURE = 0x101
CAN_ID_ENGINE_TEMP = 0x102
CAN_ID_ENGINE_OIL = 0x103
CAN_ID_ENGINE_FUEL = 0x104
CAN_ID_ENGINE_VIBRATION = 0x105
CAN_ID_ENGINE_ELECTRICAL = 0x106
CAN_ID_ENGINE_INJECTION = 0x107
CAN_ID_ENVIRONMENT = 0x108
CAN_ID_ENGINE_CONTROL = 0x109
CAN_ID_ENGINE_STATUS = 0x10A

VALID_CAN_IDS = {
    CAN_ID_ENGINE_SPEED,
    CAN_ID_ENGINE_PRESSURE,
    CAN_ID_ENGINE_TEMP,
    CAN_ID_ENGINE_OIL,
    CAN_ID_ENGINE_FUEL,
    CAN_ID_ENGINE_VIBRATION,
    CAN_ID_ENGINE_ELECTRICAL,
    CAN_ID_ENGINE_INJECTION,
    CAN_ID_ENVIRONMENT,
    CAN_ID_ENGINE_CONTROL,
    CAN_ID_ENGINE_STATUS,
}

# Signal physical range bounds
# Signal physical range bounds
SIGNAL_RANGES: Dict[str, Tuple[float, float]] = {
    "rpm": (0.0, 7000.0),            # RPM
    "thr": (0.0, 1.0),               # Throttle fraction (0.0 to 1.0)
    "map": (0.0, 40.0),              # inHg
    "oil_p": (0.0, 10.0),            # bar
    "cht": (-40.0, 250.0),           # °C
    "egt": (0.0, 1200.0),            # °C
    "oil_t": (-40.0, 200.0),         # °C
    "fuel": (0.0, 60.0),             # L/h
    "vib": (0.0, 30.0),              # mm/s
    "battery_v": (0.0, 25.0),        # V
    "inj_timing": (-50.0, 60.0),     # deg BTDC
    "iat": (-40.0, 150.0),           # °C
    "fuel_p": (0.0, 10.0),           # bar
    "alt_i": (0.0, 60.0),            # Amps
    "wastegate": (0.0, 100.0),       # %
    "alt": (-500.0, 15000.0),        # meters
    "t_amb": (-60.0, 70.0),          # °C
    "frame_counter": (0, 65535),
    "status_flags": (0, 65535),
    "fault_flags": (0, 4294967295),
}


def _clamp(val: float, min_v: float, max_v: float) -> float:
    return max(min_v, min(val, max_v))


# -----------------------------------------------------------------------------
# Encoder Functions (Physical -> CAN 8-Byte Payload)
# -----------------------------------------------------------------------------

def encode_engine_speed(rpm: float, thr: float, frame_cnt: int = 0) -> bytes:
    """ID: 0x100 (8 Bytes)
    rpm: uint16 (scale 1.0, 0..7000)
    thr: uint16 (scale 0.0001, 0.0..1.0 -> 0..10000)
    frame_cnt: uint16 (0..65535)
    reserved: uint16 (0)
    """
    rpm_raw = int(round(_clamp(rpm, 0.0, 7000.0)))
    thr_raw = int(round(_clamp(thr, 0.0, 1.0) * 10000.0))
    cnt_raw = int(frame_cnt) & 0xFFFF
    return struct.pack(">HHHH", rpm_raw, thr_raw, cnt_raw, 0)


def encode_engine_pressure(map_inhg: float, oil_p_bar: float) -> bytes:
    """ID: 0x101 (8 Bytes)
    map: uint16 (scale 0.01, 0..40 inHg -> 0..4000)
    oil_p: uint16 (scale 0.001, 0..10 bar -> 0..10000)
    reserved: uint32 (0)
    """
    map_raw = int(round(_clamp(map_inhg, 0.0, 40.0) * 100.0))
    oil_p_raw = int(round(_clamp(oil_p_bar, 0.0, 10.0) * 1000.0))
    return struct.pack(">HHI", map_raw, oil_p_raw, 0)


def encode_engine_temp(cht_c: float, egt_c: float) -> bytes:
    """ID: 0x102 (8 Bytes)
    cht: uint16 (scale 0.1, offset -40°C -> raw = (cht + 40) * 10)
    egt: uint16 (scale 0.1, 0..1200°C -> raw = egt * 10)
    reserved: uint32 (0)
    """
    cht_raw = int(round((_clamp(cht_c, -40.0, 250.0) + 40.0) * 10.0))
    egt_raw = int(round(_clamp(egt_c, 0.0, 1200.0) * 10.0))
    return struct.pack(">HHI", cht_raw, egt_raw, 0)


def encode_engine_oil(oil_t_c: float) -> bytes:
    """ID: 0x103 (8 Bytes)
    oil_t: uint16 (scale 0.1, offset -40°C -> raw = (oil_t + 40) * 10)
    reserved: 6 bytes
    """
    oil_t_raw = int(round((_clamp(oil_t_c, -40.0, 200.0) + 40.0) * 10.0))
    return struct.pack(">HHI", oil_t_raw, 0, 0)


def encode_engine_fuel(fuel_lh: float, fuel_p_bar: float = 3.2) -> bytes:
    """ID: 0x104 (8 Bytes)
    fuel: uint16 (scale 0.01, 0..60 L/h -> raw = fuel * 100)
    fuel_p: uint16 (scale 0.001, 0..10 bar -> raw = fuel_p * 1000)
    reserved: uint32 (0)
    """
    fuel_raw = int(round(_clamp(fuel_lh, 0.0, 60.0) * 100.0))
    fuel_p_raw = int(round(_clamp(fuel_p_bar, 0.0, 10.0) * 1000.0))
    return struct.pack(">HHI", fuel_raw, fuel_p_raw, 0)


def encode_engine_vibration(vib_mms: float) -> bytes:
    """ID: 0x105 (8 Bytes)
    vib: uint16 (scale 0.001, 0..30 mm/s -> raw = vib * 1000)
    reserved: 6 bytes
    """
    vib_raw = int(round(_clamp(vib_mms, 0.0, 30.0) * 1000.0))
    return struct.pack(">HHI", vib_raw, 0, 0)


def encode_engine_electrical(battery_v: float, alt_i_amp: float = 12.0) -> bytes:
    """ID: 0x106 (8 Bytes)
    battery_v: uint16 (scale 0.001, 0..25 V -> raw = battery_v * 1000)
    alt_i: uint16 (scale 0.01, 0..60 A -> raw = alt_i * 100)
    reserved: uint32 (0)
    """
    bat_raw = int(round(_clamp(battery_v, 0.0, 25.0) * 1000.0))
    alt_i_raw = int(round(_clamp(alt_i_amp, 0.0, 60.0) * 100.0))
    return struct.pack(">HHI", bat_raw, alt_i_raw, 0)


def encode_engine_injection(inj_timing_deg: float, wastegate_pct: float = 50.0) -> bytes:
    """ID: 0x107 (8 Bytes)
    inj_timing: uint16 (scale 0.1, offset -50 deg -> raw = (inj_timing + 50) * 10)
    wastegate: uint16 (scale 0.1, 0..100% -> raw = wastegate * 10)
    reserved: uint32 (0)
    """
    inj_raw = int(round((_clamp(inj_timing_deg, -50.0, 60.0) + 50.0) * 10.0))
    wg_raw = int(round(_clamp(wastegate_pct, 0.0, 100.0) * 10.0))
    return struct.pack(">HHI", inj_raw, wg_raw, 0)


def encode_environment(alt_m: float, t_amb_c: float, iat_c: float = 20.0) -> bytes:
    """ID: 0x108 (8 Bytes)
    alt: int16 (scale 1.0, offset -500 m -> raw = alt + 500)
    t_amb: int16 (scale 0.1, -60..70°C -> raw = t_amb * 10)
    iat: int16 (scale 0.1, offset -40°C -> raw = (iat + 40) * 10)
    reserved: uint16 (0)
    """
    alt_raw = int(round(_clamp(alt_m, -500.0, 15000.0) + 500.0))
    t_amb_raw = int(round(_clamp(t_amb_c, -60.0, 70.0) * 10.0))
    iat_raw = int(round((_clamp(iat_c, -40.0, 150.0) + 40.0) * 10.0))
    return struct.pack(">hhhH", alt_raw, t_amb_raw, iat_raw, 0)


def encode_engine_control(frame_cnt: int, status_flags: int = 0) -> bytes:
    """ID: 0x109 (8 Bytes)
    frame_cnt: uint32
    status_flags: uint32
    """
    return struct.pack(">II", int(frame_cnt) & 0xFFFFFFFF, int(status_flags) & 0xFFFFFFFF)


def encode_engine_status(fault_flags: int) -> bytes:
    """ID: 0x10A (8 Bytes)
    fault_flags: uint32
    reserved: uint32
    """
    return struct.pack(">II", int(fault_flags) & 0xFFFFFFFF, 0)
