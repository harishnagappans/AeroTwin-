"""Unit and integration tests for AEROTWIN Dashboard Backend Pipeline."""
import unittest
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "dashboard"))

from app import pipeline
from twin import CALIB
from rul import rul


class TestDashboardBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sd = json.loads(CALIB.read_text())["sd"]

    def test_01_simulation_mode_healthy(self):
        """1 & 4: Test simulation mode with healthy mission profile."""
        m, ai_res, res_df, pred_df, th_time, metrics, source_label, can_stats, can_messages, ecu = pipeline(
            source_mode="SIMULATION",
            mission_profile_str="CRUISE",
            fault="healthy",
            sev=1.0,
            seed=42,
            csv_filename=""
        )
        self.assertEqual(source_label, "SIMULATION")
        self.assertIn("t", m.columns)
        self.assertIn("cht", m.columns)
        self.assertIn("mission_phase", m.columns)
        self.assertIn(ai_res["fault"], (None, "healthy"))
        self.assertIsNotNone(metrics)

    def test_02_simulation_mode_fault(self):
        """5 & 9: Test simulation mode with cooling fault mission."""
        m, ai_res, res_df, pred_df, th_time, metrics, source_label, can_stats, can_messages, ecu = pipeline(
            source_mode="SIMULATION",
            mission_profile_str="HOT_WEATHER",
            fault="cooling",
            sev=1.0,
            seed=7,
            csv_filename=""
        )
        self.assertEqual(source_label, "SIMULATION")
        self.assertIsNotNone(ai_res["t_alarm"])
        self.assertEqual(ai_res["fault"], "cooling")

    def test_03_fdr_mode(self):
        """2: Test FDR CSV mode."""
        m, ai_res, res_df, pred_df, th_time, metrics, source_label, can_stats, can_messages, ecu = pipeline(
            source_mode="FDR REPLAY",
            mission_profile_str="CRUISE",
            fault="healthy",
            sev=1.0,
            seed=0,
            csv_filename="healthy_train_0.csv"
        )
        self.assertEqual(source_label, "FDR REPLAY")
        self.assertGreater(len(m), 10)

    def test_04_can_mode(self):
        """3 & 7: Test CAN mode and CAN status."""
        m, ai_res, res_df, pred_df, th_time, metrics, source_label, can_stats, can_messages, ecu = pipeline(
            source_mode="CAN BUS",
            mission_profile_str="CRUISE",
            fault="healthy",
            sev=1.0,
            seed=7,
            csv_filename="",
            pkt_loss=0.05
        )
        self.assertEqual(source_label, "CAN TELEMETRY")
        self.assertEqual(can_stats["connection"], "CONNECTED")
        self.assertGreater(can_stats["dropped"], 0)
        self.assertGreater(len(can_messages), 0)

    def test_05_ecu_status(self):
        """6: Test ECU status and state machine."""
        m, ai_res, res_df, pred_df, th_time, metrics, source_label, can_stats, can_messages, ecu = pipeline(
            source_mode="SIMULATION",
            mission_profile_str="CRUISE",
            fault="healthy",
            sev=1.0,
            seed=0,
            csv_filename=""
        )
        self.assertIsNotNone(ecu)
        self.assertIn("engine_status", m.columns)
        self.assertIn("fault_flags", m.columns)

    def test_06_twin_telemetry(self):
        """8: Test Twin predictions and residuals."""
        m, ai_res, res_df, pred_df, th_time, metrics, source_label, can_stats, can_messages, ecu = pipeline(
            source_mode="SIMULATION",
            mission_profile_str="HIGH_ALTITUDE",
            fault="healthy",
            sev=1.0,
            seed=0,
            csv_filename=""
        )
        self.assertEqual(len(m), len(pred_df))
        self.assertIn("z_cht", res_df.columns)

    def test_07_rul_display(self):
        """10: Test RUL estimation display logic."""
        m, ai_res, res_df, pred_df, th_time, metrics, source_label, can_stats, can_messages, ecu = pipeline(
            source_mode="SIMULATION",
            mission_profile_str="CRUISE",
            fault="cooling",
            sev=1.0,
            seed=7,
            csv_filename=""
        )
        ta = ai_res["t_alarm"]
        self.assertIsNotNone(ta)
        r = rul(res_df, "cooling", ta + 300, self.sd, ta=ta)
        self.assertIn("health", r)
        self.assertIn("rul_s", r)
        self.assertLess(r["health"], 100.0)

    def test_08_mission_summary(self):
        """11: Test mission summary metrics generation."""
        m, ai_res, res_df, pred_df, th_time, metrics, source_label, can_stats, can_messages, ecu = pipeline(
            source_mode="SIMULATION",
            mission_profile_str="ENDURANCE",
            fault="healthy",
            sev=1.0,
            seed=0,
            csv_filename=""
        )
        self.assertIn("duration_seconds", metrics)
        self.assertIn("total_fuel_consumed_l", metrics)
        self.assertIn("max_cht_c", metrics)

    def test_09_export(self):
        """12: Test post-flight report export format."""
        m, ai_res, res_df, pred_df, th_time, metrics, source_label, can_stats, can_messages, ecu = pipeline(
            source_mode="SIMULATION",
            mission_profile_str="CRUISE",
            fault="healthy",
            sev=1.0,
            seed=0,
            csv_filename=""
        )
        report_dict = {
            "disclaimer": f"AEROTWIN DECISION SUPPORT SYSTEM - {source_label} DATA ONLY.",
            "metrics": metrics,
            "can_stats": can_stats,
            "ai_diagnosis": {
                "status": "ANOMALY DETECTED" if ai_res["t_alarm"] else "NOMINAL",
                "fault": ai_res["fault"],
                "t_alarm": ai_res["t_alarm"],
                "xai_explanation": ai_res.get("why", "")
            }
        }
        json_str = json.dumps(report_dict)
        csv_str = m.to_csv(index=False)
        self.assertTrue(len(json_str) > 50)
        self.assertTrue(len(csv_str) > 100)


if __name__ == "__main__":
    unittest.main()

