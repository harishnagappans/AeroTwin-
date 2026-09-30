"""AEROTWIN CAN Telemetry Simulator & Transmitter.
SIH Problem Statement 26054 Telemetry Transport Layer.

Simulates ECU telemetry transmission over CAN bus by encoding physical telemetry values.
"""

import time
import logging
from typing import Dict, Any, Optional
import pandas as pd

from can_interface import CANInterface
from can_protocol import (
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
    encode_engine_speed,
    encode_engine_pressure,
    encode_engine_temp,
    encode_engine_oil,
    encode_engine_fuel,
    encode_engine_vibration,
    encode_engine_electrical,
    encode_engine_injection,
    encode_environment,
    encode_engine_control,
    encode_engine_status,
)

logger = logging.getLogger("AEROTWIN_CAN")


class CANSimulator:
    """Encodes physical telemetry samples into CAN frames and broadcasts them over CANInterface."""

    def __init__(self, interface: Optional[CANInterface] = None):
        self.interface = interface or CANInterface()
        self.frame_counter = 0

    def send_telemetry_sample(self, row: Dict[str, Any]) -> int:
        """Encodes and transmits a full set of 11-bit CAN messages for a single telemetry sample.
        Returns the number of successfully transmitted frames.
        """
        self.frame_counter += 1
        cnt = self.frame_counter
        sent = 0

        # Extract values with safe defaults adhering to AEROTWIN schema
        rpm = float(row.get("rpm", 0.0))
        thr = float(row.get("thr", 0.0))
        map_in = float(row.get("map", 29.92))
        oil_p = float(row.get("oil_p", 2.0))
        cht = float(row.get("cht", 15.0))
        egt = float(row.get("egt", 15.0))
        oil_t = float(row.get("oil_t", 15.0))
        fuel = float(row.get("fuel", 2.5))
        vib = float(row.get("vib", 0.6))
        bat_v = float(row.get("battery_v", 14.1))
        inj = float(row.get("inj_timing", 15.0))
        alt = float(row.get("alt", 0.0))
        t_amb = float(row.get("t_amb", 15.0))

        # Encode payloads
        msgs = [
            (CAN_ID_ENGINE_SPEED, encode_engine_speed(rpm, thr, cnt)),
            (CAN_ID_ENGINE_PRESSURE, encode_engine_pressure(map_in, oil_p)),
            (CAN_ID_ENGINE_TEMP, encode_engine_temp(cht, egt)),
            (CAN_ID_ENGINE_OIL, encode_engine_oil(oil_t)),
            (CAN_ID_ENGINE_FUEL, encode_engine_fuel(fuel)),
            (CAN_ID_ENGINE_VIBRATION, encode_engine_vibration(vib)),
            (CAN_ID_ENGINE_ELECTRICAL, encode_engine_electrical(bat_v)),
            (CAN_ID_ENGINE_INJECTION, encode_engine_injection(inj)),
            (CAN_ID_ENVIRONMENT, encode_environment(alt, t_amb)),
            (CAN_ID_ENGINE_CONTROL, encode_engine_control(cnt, 0)),
            (CAN_ID_ENGINE_STATUS, encode_engine_status(0)),
        ]

        for cid, payload in msgs:
            if self.interface.send(cid, payload):
                sent += 1

        return sent

    def stream_dataframe(self, df: pd.DataFrame, fps: float = 10.0, max_rows: Optional[int] = None) -> int:
        """Broadcasts a DataFrame row by row onto the CAN bus."""
        delay = 1.0 / max(1.0, fps)
        rows_to_send = len(df) if max_rows is None else min(len(df), max_rows)
        total_sent = 0

        logger.info(f"Starting CAN telemetry stream for {rows_to_send} rows at {fps} Hz...")
        for i in range(rows_to_send):
            row_dict = df.iloc[i].to_dict()
            sent = self.send_telemetry_sample(row_dict)
            total_sent += sent
            time.sleep(delay)

        logger.info(f"Completed CAN telemetry stream. Sent {total_sent} frames total.")
        return total_sent
