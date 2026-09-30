"""AEROTWIN CAN Loss & Communication Degradation Test.
SIH Problem Statement 26054 Telemetry Transport Layer.

Tests 1%, 5%, 10% packet loss, burst loss, and CAN timeouts to ensure robustness.
"""

import sys
import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from actual import make_run
from telemetry_source import CANSource
from can_decoder import CANDecoder


class TestCANDegradation(unittest.TestCase):

    def setUp(self):
        m, _ = make_run(seed=123)
        self.source_df = m

    def test_01_packet_loss_1_percent(self):
        can_source = CANSource(self.source_df, packet_loss=0.01)
        df = can_source.get_dataframe()
        self.assertGreater(len(df), 0)
        self.assertFalse(can_source.decoder.is_degraded())

    def test_02_packet_loss_5_percent(self):
        can_source = CANSource(self.source_df, packet_loss=0.05)
        df = can_source.get_dataframe()
        self.assertGreater(len(df), 0)

    def test_03_packet_loss_10_percent(self):
        can_source = CANSource(self.source_df, packet_loss=0.10)
        df = can_source.get_dataframe()
        self.assertGreater(len(df), 0)
        self.assertTrue(can_source.bus.status.dropped_frames > 0)

    def test_04_burst_packet_loss(self):
        can_source = CANSource(self.source_df, burst_loss=True)
        df = can_source.get_dataframe()
        self.assertGreater(len(df), 0)
        self.assertTrue(can_source.bus.status.dropped_frames >= 10)

    def test_05_stale_signal_detection(self):
        decoder = CANDecoder()
        # Decode frame for RPM at t=100.0
        decoder.decode_frame(0x100, b"\x13\x88\x21\x34\x00\x01\x00\x00", timestamp=100.0)
        # Check status 0.05s later -> CURRENT
        self.assertEqual(decoder.get_signal_status("rpm", now=100.05), "CURRENT")
        # Check status 2.0s later -> STALE
        self.assertEqual(decoder.get_signal_status("rpm", now=102.0), "STALE")
        # Unreceived signal -> MISSING
        self.assertEqual(decoder.get_signal_status("cht", now=100.0), "MISSING")

    def test_06_degraded_communication_alert(self):
        decoder = CANDecoder()
        # Simulate invalid frames threshold
        decoder.status.invalid_frames = 10
        self.assertTrue(decoder.is_degraded())


if __name__ == "__main__":
    unittest.main()
