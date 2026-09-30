"""Unit and integration tests for AEROTWIN Robustness & Validation Suite."""
import unittest
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

RESULTS_DIR = ROOT / "results"


class TestRobustnessValidationSuite(unittest.TestCase):

    def test_01_results_directory_and_artifacts_exist(self):
        """14 & 15: Test that machine-readable CSV, JSON, and PNG plot artifacts exist."""
        self.assertTrue(RESULTS_DIR.exists(), "results/ directory must exist.")
        
        required_csvs = [
            "robustness_results.csv",
            "confusion_matrix.csv",
            "seed_robustness.csv",
            "mismatch_results.csv",
            "rul_validation.csv"
        ]
        for csv_name in required_csvs:
            csv_path = RESULTS_DIR / csv_name
            self.assertTrue(csv_path.exists(), f"Missing required output file: {csv_name}")
            self.assertGreater(csv_path.stat().st_size, 50, f"File {csv_name} is empty.")
            
        json_path = RESULTS_DIR / "validation_summary.json"
        self.assertTrue(json_path.exists(), "validation_summary.json must exist.")
        summary = json.loads(json_path.read_text())
        self.assertIn("critical_metrics", summary)
        self.assertIn("disclaimer", summary)

        required_pngs = [
            "false_alarms_vs_mismatch.png",
            "detection_rate_vs_mismatch.png",
            "macro_f1_vs_sensor_noise.png",
            "rul_error_vs_noise.png",
            "detection_latency_by_fault.png",
            "confusion_matrix.png",
            "seed_variation.png"
        ]
        for png_name in required_pngs:
            png_path = RESULTS_DIR / png_name
            self.assertTrue(png_path.exists(), f"Missing required visualization artifact: {png_name}")
            self.assertGreater(png_path.stat().st_size, 500, f"Plot artifact {png_name} is invalid.")

    def test_02_model_mismatch_tolerance(self):
        """2 & 3: Test model mismatch metrics at baseline 0% mismatch."""
        json_path = RESULTS_DIR / "validation_summary.json"
        if not json_path.exists():
            self.skipTest("validation_summary.json not yet generated.")
        summary = json.loads(json_path.read_text())
        crit = summary["critical_metrics"]
        
        self.assertEqual(crit["baseline_healthy_false_alarm_rate_per_hr"], 0.0)
        self.assertGreaterEqual(crit["fault_detection_rate_pct"], 80.0)

    def test_03_can_diagnostic_fidelity(self):
        """10: Test CAN transport diagnostic equivalence."""
        json_path = RESULTS_DIR / "validation_summary.json"
        if not json_path.exists():
            self.skipTest("validation_summary.json not yet generated.")
        summary = json.loads(json_path.read_text())
        can_summary = summary["can_transport_summary"]
        
        self.assertEqual(can_summary["total_faults_tested"], can_summary["classification_matches"])
        self.assertLess(can_summary["mean_residual_mae"], 0.1)


if __name__ == "__main__":
    unittest.main()
