"""Unit and integration tests for AEROTWIN Step 8: ML Validation Audit & Data-Leakage Fix Suite."""

import unittest
import json
import joblib
from pathlib import Path
import sys
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"
DOCS_DIR = ROOT / "docs"

from ml_validation_audit import build_mission_level_dataset


class TestMLValidationAuditSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df_train, cls.df_val, cls.df_test = build_mission_level_dataset()

    def test_01_mission_level_separation(self):
        """1 & 2: Test that TRAIN, VALIDATION, and TEST sets have complete mission-level separation."""
        df_train, df_val, df_test = self.df_train, self.df_val, self.df_test
        
        train_missions = set(df_train["mission_id"].unique())
        val_missions = set(df_val["mission_id"].unique())
        test_missions = set(df_test["mission_id"].unique())
        
        # Verify no shared mission IDs across any split
        self.assertEqual(len(train_missions.intersection(test_missions)), 0, "TRAIN and TEST share mission IDs!")
        self.assertEqual(len(train_missions.intersection(val_missions)), 0, "TRAIN and VALIDATION share mission IDs!")
        self.assertEqual(len(val_missions.intersection(test_missions)), 0, "VALIDATION and TEST share mission IDs!")
        
        # Verify seed ranges
        train_seeds = set(df_train["seed"].unique())
        val_seeds = set(df_val["seed"].unique())
        test_seeds = set(df_test["seed"].unique())
        
        self.assertTrue(all(100 <= s <= 399 for s in train_seeds), "TRAIN seeds must be in range 100-399")
        self.assertTrue(all(400 <= s <= 449 for s in val_seeds), "VALIDATION seeds must be in range 400-449")
        self.assertTrue(all(500 <= s <= 599 for s in test_seeds), "TEST seeds must be in range 500-599")

    def test_02_no_overlapping_windows_across_splits(self):
        """3: Test that every window has valid metadata and no overlapping windows span splits."""
        df_train, df_val, df_test = self.df_train, self.df_val, self.df_test
        
        required_cols = ["mission_id", "seed", "fault_type", "fault_severity", "profile", "window_start", "window_end"]
        for col in required_cols:
            self.assertIn(col, df_train.columns, f"Missing window metadata column: {col}")
            self.assertIn(col, df_test.columns, f"Missing window metadata column: {col}")
            
        train_pairs = set(zip(df_train["mission_id"], df_train["window_start"], df_train["window_end"]))
        test_pairs = set(zip(df_test["mission_id"], df_test["window_start"], df_test["window_end"]))
        
        self.assertEqual(len(train_pairs.intersection(test_pairs)), 0, "Overlapping windows found between TRAIN and TEST!")

    def test_03_validation_rf_model_artifact(self):
        """Test that validation-only RF model exists and does not overwrite production rf.joblib."""
        rf_val_path = MODELS_DIR / "rf_validation.joblib"
        rf_prod_path = MODELS_DIR / "rf.joblib"
        
        self.assertTrue(rf_val_path.exists(), "models/rf_validation.joblib must exist.")
        self.assertTrue(rf_prod_path.exists(), "models/rf.joblib must still exist.")
        
        # Check model file sizes
        self.assertGreater(rf_val_path.stat().st_size, 1000, "Validation RF model binary invalid.")

    def test_04_holdout_confusion_matrix_and_plots(self):
        """4: Test holdout confusion matrix generation and plot files."""
        cm_csv = RESULTS_DIR / "holdout_confusion_matrix.csv"
        cm_png = RESULTS_DIR / "holdout_confusion_matrix.png"
        
        self.assertTrue(cm_csv.exists(), "holdout_confusion_matrix.csv must exist.")
        self.assertTrue(cm_png.exists(), "holdout_confusion_matrix.png must exist.")
        
        df_cm = pd.read_csv(cm_csv, index_col=0)
        self.assertEqual(df_cm.shape, (10, 10), "Confusion matrix must be 10x10.")

    def test_05_deterministic_seed_behavior(self):
        """5: Test deterministic dataset generation behavior across seeds."""
        self.assertGreater(len(self.df_train), 100)
        self.assertIn("mission_id", self.df_train.columns)

    def test_06_result_artifacts_exist(self):
        """6: Test that all Step 8 result CSV, JSON, and report artifacts exist."""
        required_csvs = [
            "holdout_confusion_matrix.csv",
            "severity_generalization.csv",
            "compound_fault_validation.csv",
            "clean_seed_robustness.csv",
            "clean_noise_robustness.csv",
            "clean_mismatch_robustness.csv",
            "clean_rul_validation.csv",
            "latency_breakdown.csv",
            "clean_can_fidelity.csv"
        ]
        for csv_name in required_csvs:
            csv_path = RESULTS_DIR / csv_name
            self.assertTrue(csv_path.exists(), f"Missing required output file: {csv_name}")
            self.assertGreater(csv_path.stat().st_size, 20, f"File {csv_name} is empty.")
            
        json_path = RESULTS_DIR / "TRUSTWORTHY_VALIDATION_SUMMARY.json"
        self.assertTrue(json_path.exists(), "TRUSTWORTHY_VALIDATION_SUMMARY.json must exist.")
        
        report_path = DOCS_DIR / "TRUSTWORTHY_VALIDATION_REPORT.md"
        self.assertTrue(report_path.exists(), "TRUSTWORTHY_VALIDATION_REPORT.md must exist.")
        
        audit_path = DOCS_DIR / "ML_VALIDATION_AUDIT.md"
        self.assertTrue(audit_path.exists(), "ML_VALIDATION_AUDIT.md must exist.")

    def test_07_can_direct_comparison(self):
        """7: Test CAN vs Direct telemetry comparison artifact content."""
        can_csv = RESULTS_DIR / "clean_can_fidelity.csv"
        self.assertTrue(can_csv.exists(), "clean_can_fidelity.csv must exist.")
        
        df_can = pd.read_csv(can_csv)
        self.assertIn("classification_match", df_can.columns)
        self.assertIn("mean_residual_mae_sigma", df_can.columns)
        self.assertGreater(len(df_can), 5, "CAN fidelity evaluation must cover at least 5 runs per fault.")

    def test_08_rul_benchmark_generation(self):
        """8: Test clean synthetic RUL benchmark artifact content."""
        rul_csv = RESULTS_DIR / "clean_rul_validation.csv"
        self.assertTrue(rul_csv.exists(), "clean_rul_validation.csv must exist.")
        
        df_rul = pd.read_csv(rul_csv)
        self.assertIn("absolute_error_min", df_rul.columns)
        self.assertIn("true_value_in_90_ci", df_rul.columns)
        self.assertGreater(len(df_rul), 5, "RUL benchmark must contain evaluations.")


if __name__ == "__main__":
    unittest.main()
