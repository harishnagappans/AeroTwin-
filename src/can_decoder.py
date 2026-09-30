"""AEROTWIN CAN Telemetry Decoder & Signal Validation Layer.
SIH Problem Statement 26054 Telemetry Transport Layer.

Outputs standardized telemetry dictionary compatible with existing AEROTWIN schema.
"""

import time
import struct
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List

from can_protocol import (
    VALID_CAN_IDS,
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
    SIGNAL_RANGES,
)

logger = logging.getLogger("AEROTWIN_CAN")


@dataclass
class CANStatus:
    """Tracks CAN bus health, performance, and validation statistics."""
    received_frames: int = 0
    transmitted_frames: int = 0
    valid_frames: int = 0
    invalid_frames: int = 0
    unknown_ids: int = 0
    dropped_frames: int = 0
    timeout_count: int = 0
    frames_per_sec: float = 0.0
    last_timestamp: float = 0.0
    _fps_window: List[float] = field(default_factory=list)

    def record_rx(self, timestamp: Optional[float] = None) -> None:
        now = timestamp or time.time()
        self.received_frames += 1
        self.last_timestamp = now
        self._fps_window.append(now)
        # Keep window within trailing 1.0 second
        cutoff = now - 1.0
        self._fps_window = [t for t in self._fps_window if t >= cutoff]
        self.frames_per_sec = float(len(self._fps_window))


class CANDecoder:
    """Decodes raw CAN frames into AEROTWIN standard telemetry dictionary."""

    # Expected update intervals in seconds (1 / Hz)
    UPDATE_INTERVALS: Dict[str, float] = {
        "rpm": 0.02,        # 50 Hz
        "thr": 0.02,        # 50 Hz
        "vib": 0.02,        # 50 Hz
        "map": 0.05,        # 20 Hz
        "oil_p": 0.05,      # 20 Hz
        "inj_timing": 0.05, # 20 Hz
        "cht": 0.10,        # 10 Hz
        "egt": 0.10,        # 10 Hz
        "oil_t": 0.10,      # 10 Hz
        "fuel": 0.10,       # 10 Hz
        "battery_v": 0.10,  # 10 Hz
        "alt": 0.20,        # 5 Hz
        "t_amb": 0.20,      # 5 Hz
    }

    def __init__(self):
        self.status = CANStatus()
        # Default nominal state adhering to AEROTWIN schema
        self.state: Dict[str, Any] = {
            "t": 0.0,
            "rpm": 0.0,
            "thr": 0.0,
            "alt": 0.0,
            "t_amb": 15.0,
            "map": 29.92,
            "cht": 15.0,
            "egt": 15.0,
            "oil_t": 15.0,
            "oil_p": 2.0,
            "fuel": 2.5,
            "battery_v": 14.1,
            "inj_timing": 15.0,
            "vib": 0.6,
            "engine_status": 0,
            "fault_flags": 0,
            "frame_counter": 0,
        }
        self.signal_timestamps: Dict[str, float] = {}
        self.can_receive_timestamp: float = 0.0

    def get_signal_status(self, key: str, now: Optional[float] = None) -> str:
        """Classify signal as CURRENT, STALE, or MISSING."""
        if key not in self.signal_timestamps:
            return "MISSING"
        t_now = now or time.time()
        last_t = self.signal_timestamps[key]
        expected = self.UPDATE_INTERVALS.get(key, 0.1)
        # Mark STALE if missing for > 5x expected interval or > 1.0s
        if (t_now - last_t) > max(1.0, 5.0 * expected):
            return "STALE"
        return "CURRENT"

    def is_degraded(self) -> bool:
        """Check if communication is degraded due to invalid frames or stale signals."""
        if self.status.invalid_frames > 5 or self.status.unknown_ids > 5 or self.status.timeout_count > 10:
            return True
        now = time.time()
        stale_cnt = sum(1 for k in self.UPDATE_INTERVALS if self.get_signal_status(k, now) != "CURRENT")
        return stale_cnt > 3

    def decode_frame(self, can_id: int, data: bytes, timestamp: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Decode a single CAN frame. Returns updated signal dictionary or None if invalid."""
        ts = timestamp or time.time()
        self.can_receive_timestamp = ts
        self.status.record_rx(ts)

        # 1. Unknown ID check
        if can_id not in VALID_CAN_IDS:
            self.status.unknown_ids += 1
            self.status.invalid_frames += 1
            logger.warning(f"[CAN UNKNOWN ID] Received unrecognized CAN ID: 0x{can_id:03X}")
            return None

        # 2. Payload length check (must be 8 bytes)
        if len(data) != 8:
            self.status.invalid_frames += 1
            logger.warning(f"[CAN INVALID] Invalid payload length ({len(data)} B, expected 8 B) for ID: 0x{can_id:03X}")
            return None

        try:
            signals = self._unpack_payload(can_id, data)
            if signals is None:
                self.status.invalid_frames += 1
                return None

            # 3. Validate physical ranges
            valid = True
            for k, val in signals.items():
                if k in SIGNAL_RANGES:
                    lo, hi = SIGNAL_RANGES[k]
                    if not (lo <= val <= hi):
                        logger.warning(f"[CAN WARNING] Signal {k}={val} out of valid range [{lo}, {hi}] for ID 0x{can_id:03X}")
                        valid = False

            if not valid:
                self.status.invalid_frames += 1
                return None

            # Update telemetry state and signal timestamps
            for k, val in signals.items():
                self.state[k] = val
                self.signal_timestamps[k] = ts

            self.status.valid_frames += 1
            return dict(self.state)

        except struct.error as e:
            self.status.invalid_frames += 1
            logger.warning(f"[CAN INVALID] Malformed payload structure for ID 0x{can_id:03X}: {e}")
            return None

    def _unpack_payload(self, can_id: int, data: bytes) -> Optional[Dict[str, Any]]:
        """Internal unpacker per CAN ID."""
        if can_id == CAN_ID_ENGINE_SPEED:
            rpm_raw, thr_raw, cnt_raw, _ = struct.unpack(">HHHH", data)
            return {
                "rpm": float(rpm_raw),
                "thr": float(thr_raw) / 10000.0,
                "frame_counter": int(cnt_raw),
            }

        elif can_id == CAN_ID_ENGINE_PRESSURE:
            map_raw, oil_p_raw, _ = struct.unpack(">HHI", data)
            return {
                "map": float(map_raw) / 100.0,
                "oil_p": float(oil_p_raw) / 1000.0,
            }

        elif can_id == CAN_ID_ENGINE_TEMP:
            cht_raw, egt_raw, _ = struct.unpack(">HHI", data)
            return {
                "cht": (float(cht_raw) / 10.0) - 40.0,
                "egt": float(egt_raw) / 10.0,
            }

        elif can_id == CAN_ID_ENGINE_OIL:
            oil_t_raw, _, _ = struct.unpack(">HHI", data)
            return {
                "oil_t": (float(oil_t_raw) / 10.0) - 40.0,
            }

        elif can_id == CAN_ID_ENGINE_FUEL:
            fuel_raw, _, _ = struct.unpack(">HHI", data)
            return {
                "fuel": float(fuel_raw) / 100.0,
            }

        elif can_id == CAN_ID_ENGINE_VIBRATION:
            vib_raw, _, _ = struct.unpack(">HHI", data)
            return {
                "vib": float(vib_raw) / 1000.0,
            }

        elif can_id == CAN_ID_ENGINE_ELECTRICAL:
            bat_raw, _, _ = struct.unpack(">HHI", data)
            return {
                "battery_v": float(bat_raw) / 1000.0,
            }

        elif can_id == CAN_ID_ENGINE_INJECTION:
            inj_raw, _, _ = struct.unpack(">HHI", data)
            return {
                "inj_timing": (float(inj_raw) / 10.0) - 50.0,
            }

        elif can_id == CAN_ID_ENVIRONMENT:
            alt_raw, t_amb_raw, _ = struct.unpack(">hhI", data)
            return {
                "alt": float(alt_raw) - 500.0,
                "t_amb": float(t_amb_raw) / 10.0,
            }

        elif can_id == CAN_ID_ENGINE_CONTROL:
            cnt_raw, status_raw = struct.unpack(">II", data)
            return {
                "frame_counter": int(cnt_raw),
                "engine_status": int(status_raw),
            }

        elif can_id == CAN_ID_ENGINE_STATUS:
            fault_raw, _ = struct.unpack(">II", data)
            return {
                "fault_flags": int(fault_raw),
            }

        return None

    def get_telemetry_dict(self) -> Dict[str, Any]:
        """Returns a snapshot dictionary formatted exactly for AEROTWIN pipeline."""
        return dict(self.state)
