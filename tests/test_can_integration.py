"""AEROTWIN Master Integration & Regression Test Suite.
SIH Problem Statement 26054 Telemetry Transport Layer.

Executes all 12 required integration and regression test cases.
"""

import sys
import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from actual import make_run, DATA
from detect import load, analyze
from twin import residuals
from can_protocol import CAN_ID_ENGINE_SPEED, encode_engine_speed
from can_decoder import CANDecoder
from can_interface import CANInterface
from can_simulator import CANSimulator
from telemetry_source import SyntheticSource, CSVSource, CANSource


class TestMasterCANIntegration(unittest.TestCase):

    def setUp(self):
        self.models = load()

    # 1. Synthetic -> CAN -> telemetry reconstruction
    def test_01_synthetic_to_can_reconstruction(self):
        synth = SyntheticSource(seed=77)
        df_orig = synth.get_dataframe()
        can_source = CANSource(df_orig)
        df_recon = can_source.get_dataframe()
        self.assertEqual(len(df_orig), len(df_recon))
        self.assertAlmostEqual(df_orig["rpm"].mean(), df_recon["rpm"].mean(), delta=1.0)

    # 2. CSV -> CAN -> telemetry reconstruction
    def test_02_csv_to_can_reconstruction(self):
        csv_file = DATA / "test_cooling.csv"
        if csv_file.exists():
            csv_source = CSVSource(csv_file)
            df_orig = csv_source.get_dataframe()
            can_source = CANSource(df_orig)
            df_recon = can_source.get_dataframe()
            self.assertEqual(len(df_orig), len(df_recon))
            self.assertAlmostEqual(df_orig["cht"].iloc[-1], df_recon["cht"].iloc[-1], delta=0.2)

    # 3. Fault -> CAN -> detector
    def test_03_fault_to_can_detector(self):
        m_orig, _ = make_run(fault="oil_pressure", seed=88)
        can_source = CANSource(m_orig)
        m_can = can_source.get_dataframe()
        res = analyze(m_can, self.models)
        self.assertIsNotNone(res["t_alarm"])
        self.assertEqual(res["fault"], "oil_pressure")

    # 4. Missing CAN frame
    def test_04_missing_can_frame(self):
        bus = CANInterface(interface="virtual", channel="int_test_4", auto_connect=True)
        rx = bus.recv(timeout=0.01)
        self.assertIsNone(rx)
        self.assertGreaterEqual(bus.status.timeout_count, 1)
        bus.disconnect()

    # 5. Stale signal
    def test_05_stale_signal(self):
        decoder = CANDecoder()
        decoder.decode_frame(CAN_ID_ENGINE_SPEED, encode_engine_speed(5000, 0.8), timestamp=10.0)
        self.assertEqual(decoder.get_signal_status("rpm", now=10.05), "CURRENT")
        self.assertEqual(decoder.get_signal_status("rpm", now=15.0), "STALE")

    # 6. Packet loss
    def test_06_packet_loss(self):
        m_orig, _ = make_run(seed=99)
        can_source = CANSource(m_orig, packet_loss=0.05)
        df_recon = can_source.get_dataframe()
        self.assertGreater(len(df_recon), 0)
        self.assertTrue(can_source.bus.status.dropped_frames > 0)

    # 7. Burst packet loss
    def test_07_burst_packet_loss(self):
        m_orig, _ = make_run(seed=101)
        can_source = CANSource(m_orig, burst_loss=True)
        df_recon = can_source.get_dataframe()
        self.assertGreater(len(df_recon), 0)

    # 8. CAN timeout
    def test_08_can_timeout(self):
        bus = CANInterface(interface="virtual", channel="int_test_8", auto_connect=True)
        rx = bus.recv(timeout=0.05)
        self.assertIsNone(rx)
        self.assertEqual(bus.status.timeout_count, 1)
        bus.disconnect()

    # 9. Unknown CAN ID
    def test_09_unknown_can_id(self):
        decoder = CANDecoder()
        res = decoder.decode_frame(0x700, b"\x00" * 8)
        self.assertIsNone(res)
        self.assertEqual(decoder.status.unknown_ids, 1)

    # 10. Invalid payload
    def test_10_invalid_payload(self):
        decoder = CANDecoder()
        res = decoder.decode_frame(CAN_ID_ENGINE_SPEED, b"\x00\x01")
        self.assertIsNone(res)
        self.assertEqual(decoder.status.invalid_frames, 1)

    # 11. Existing simulation regression
    def test_11_existing_simulation_regression(self):
        m_orig, lab_orig = make_run(fault="overheat", seed=202)
        self.assertIn("cht", m_orig.columns)
        self.assertIn("oil_t", m_orig.columns)
        self.assertEqual(len(m_orig), len(lab_orig))

    # 12. Existing ML pipeline regression
    def test_12_existing_ml_pipeline_regression(self):
        m_orig, _ = make_run(fault="misfire", seed=303)
        res = analyze(m_orig, self.models)
        self.assertIsNotNone(res["t_alarm"])
        self.assertEqual(res["fault"], "misfire")


if __name__ == "__main__":
    unittest.main()
