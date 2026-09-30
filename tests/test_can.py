"""AEROTWIN CAN Telemetry Test Suite.
SIH Problem Statement 26054 Telemetry Transport Layer.

Tests all 10 required CAN transport layer cases:
1. Encode -> Decode round trip
2. Minimum signal value
3. Maximum signal value
4. Typical operating value
5. Invalid payload length
6. Unknown CAN ID
7. Out-of-range value
8. Missing frame
9. CAN timeout
10. Multiple telemetry frames
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

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
    encode_engine_speed,
    encode_engine_pressure,
    encode_engine_temp,
    encode_engine_oil,
    encode_engine_fuel,
    encode_engine_vibration,
    encode_engine_electrical,
    encode_engine_injection,
    encode_environment,
)
from can_decoder import CANDecoder, CANStatus
from can_interface import CANInterface
from can_simulator import CANSimulator


class TestCANTransportLayer(unittest.TestCase):

    def setUp(self):
        self.decoder = CANDecoder()
        self.bus = CANInterface(interface="virtual", channel="test_channel", auto_connect=True)

    def tearDown(self):
        if self.bus:
            self.bus.disconnect()

    # 1. Encode -> Decode round trip
    def test_01_encode_decode_roundtrip(self):
        payload = encode_engine_speed(rpm=5000.0, thr=0.85, frame_cnt=100)
        decoded = self.decoder.decode_frame(CAN_ID_ENGINE_SPEED, payload)
        self.assertIsNotNone(decoded)
        self.assertAlmostEqual(decoded["rpm"], 5000.0, delta=1.0)
        self.assertAlmostEqual(decoded["thr"], 0.85, delta=0.001)
        self.assertEqual(decoded["frame_counter"], 100)

    # 2. Minimum signal value
    def test_02_minimum_signal_value(self):
        payload = encode_engine_speed(rpm=0.0, thr=0.0, frame_cnt=0)
        decoded = self.decoder.decode_frame(CAN_ID_ENGINE_SPEED, payload)
        self.assertIsNotNone(decoded)
        self.assertAlmostEqual(decoded["rpm"], 0.0, delta=1.0)
        self.assertAlmostEqual(decoded["thr"], 0.0, delta=0.001)

    # 3. Maximum signal value
    def test_03_maximum_signal_value(self):
        payload = encode_engine_speed(rpm=7000.0, thr=1.0, frame_cnt=65535)
        decoded = self.decoder.decode_frame(CAN_ID_ENGINE_SPEED, payload)
        self.assertIsNotNone(decoded)
        self.assertAlmostEqual(decoded["rpm"], 7000.0, delta=1.0)
        self.assertAlmostEqual(decoded["thr"], 1.0, delta=0.001)

    # 4. Typical operating value
    def test_04_typical_operating_value(self):
        payload_speed = encode_engine_speed(rpm=5500.0, thr=0.95)
        payload_temp = encode_engine_temp(cht_c=115.5, egt_c=820.0)
        payload_oil = encode_engine_oil(oil_t_c=95.2)

        d1 = self.decoder.decode_frame(CAN_ID_ENGINE_SPEED, payload_speed)
        d2 = self.decoder.decode_frame(CAN_ID_ENGINE_TEMP, payload_temp)
        d3 = self.decoder.decode_frame(CAN_ID_ENGINE_OIL, payload_oil)

        self.assertIsNotNone(d1)
        self.assertIsNotNone(d2)
        self.assertIsNotNone(d3)
        self.assertAlmostEqual(d1["rpm"], 5500.0, delta=1.0)
        self.assertAlmostEqual(d2["cht"], 115.5, delta=0.2)
        self.assertAlmostEqual(d2["egt"], 820.0, delta=0.2)
        self.assertAlmostEqual(d3["oil_t"], 95.2, delta=0.2)

    # 5. Invalid payload length
    def test_05_invalid_payload_length(self):
        short_payload = b"\x01\x02\x03"
        decoded = self.decoder.decode_frame(CAN_ID_ENGINE_SPEED, short_payload)
        self.assertIsNone(decoded)
        self.assertEqual(self.decoder.status.invalid_frames, 1)

    # 6. Unknown CAN ID
    def test_06_unknown_can_id(self):
        unknown_id = 0x7FF
        payload = b"\x00" * 8
        decoded = self.decoder.decode_frame(unknown_id, payload)
        self.assertIsNone(decoded)
        self.assertEqual(self.decoder.status.unknown_ids, 1)

    # 7. Out-of-range value
    def test_07_out_of_range_value(self):
        # Payload with raw RPM out of valid bounds (e.g. raw RPM = 99999)
        import struct
        bad_payload = struct.pack(">HHHH", 60000, 0, 0, 0)
        decoded = self.decoder.decode_frame(CAN_ID_ENGINE_SPEED, bad_payload)
        self.assertIsNone(decoded)
        self.assertEqual(self.decoder.status.invalid_frames, 1)

    # 8. Missing frame / None handling
    def test_08_missing_frame(self):
        # Bus receive timeout returns None
        rx = self.bus.recv(timeout=0.01)
        self.assertIsNone(rx)
        self.assertGreaterEqual(self.bus.status.timeout_count, 1)

    # 9. CAN timeout
    def test_09_can_timeout(self):
        start_t = self.bus.status.last_timestamp
        rx = self.bus.recv(timeout=0.05)
        self.assertIsNone(rx)
        self.assertEqual(self.bus.status.timeout_count, 1)

    # 10. Multiple telemetry frames round trip via bus simulator
    def test_10_multiple_telemetry_frames(self):
        sim = CANSimulator(self.bus)
        sample = {
            "rpm": 5200.0,
            "thr": 0.88,
            "map": 26.5,
            "oil_p": 4.1,
            "cht": 110.0,
            "egt": 810.0,
            "oil_t": 92.0,
            "fuel": 22.5,
            "vib": 1.2,
            "battery_v": 13.9,
            "inj_timing": 22.0,
            "alt": 2500.0,
            "t_amb": 12.0,
        }

        sent = sim.send_telemetry_sample(sample)
        self.assertEqual(sent, 11)

        # Receive and decode all 11 messages from bus
        for _ in range(11):
            frame = self.bus.recv(timeout=0.5)
            self.assertIsNotNone(frame)
            cid, data, ts = frame
            self.decoder.decode_frame(cid, data, ts)

        state = self.decoder.get_telemetry_dict()
        self.assertAlmostEqual(state["rpm"], 5200.0, delta=1.0)
        self.assertAlmostEqual(state["map"], 26.5, delta=0.05)
        self.assertAlmostEqual(state["cht"], 110.0, delta=0.2)
        self.assertAlmostEqual(state["egt"], 810.0, delta=0.2)
        self.assertAlmostEqual(state["battery_v"], 13.9, delta=0.01)
        self.assertAlmostEqual(state["alt"], 2500.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
