"""Unit and integration tests for AEROTWIN Step 9: SIH Demo Scenario Execution."""

import unittest
from pathlib import Path
import sys
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sih_demo import run_sih_demo
from actual import make_run
from twin import residuals, CALIB
from detect import analyze, load
from rul import rul
import json

SD_CALIB = json.loads(CALIB.read_text())["sd"]


class TestSIHDemoSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.models = load()

    def test_01_injector_fault_demo_execution(self):
        """Test complete SIH demo execution flow for injector_fault scenario."""
        m_run, _ = make_run(fault="injector_fault", sev=1.0, seed=555)
        
        # Analyze post-injection segment at t=480 s
        m_sub = m_run[m_run.t <= 3300.0].copy()
        r_ana = analyze(m_sub, self.models)
        
        # 1. Anomaly detection verification
        self.assertIsNotNone(r_ana["t_alarm"], "Injector fault anomaly must trigger an alarm.")
        
        # 2. Fault classification verification
        self.assertEqual(r_ana["fault"], "injector_fault", "Classifier must identify injector_fault.")
        
        # 3. XAI output verification
        self.assertTrue(len(r_ana["why"]) > 0, "XAI explanation string must be present.")
        
        # 4. RUL calculation verification
        res_sub = residuals(m_sub)
        r_rul = rul(res_sub, "injector_fault", 3300.0, SD_CALIB, ta=r_ana["t_alarm"])
        self.assertIsNotNone(r_rul["rul_s"], "RUL estimation must return a valid numerical horizon.")

    def test_02_oil_pressure_demo_execution(self):
        """Test complete SIH demo execution flow for oil_pressure scenario."""
        m_run, _ = make_run(fault="oil_pressure", sev=1.0, seed=555)
        m_sub = m_run[m_run.t <= 3300.0].copy()
        r_ana = analyze(m_sub, self.models)
        
        self.assertIsNotNone(r_ana["t_alarm"], "Oil pressure anomaly must trigger an alarm.")
        self.assertEqual(r_ana["fault"], "oil_pressure", "Classifier must identify oil_pressure.")
        self.assertIn("oil_p", r_ana["why"], "XAI attribution must highlight oil_p channel.")

    def test_03_overheat_demo_execution(self):
        """Test complete SIH demo execution flow for overheat scenario."""
        m_run, _ = make_run(fault="overheat", sev=1.0, seed=555)
        m_sub = m_run[m_run.t <= 3300.0].copy()
        r_ana = analyze(m_sub, self.models)
        
        self.assertIsNotNone(r_ana["t_alarm"], "Overheat anomaly must trigger an alarm.")
        self.assertEqual(r_ana["fault"], "overheat", "Classifier must identify overheat.")
        self.assertIn("cht", r_ana["why"], "XAI attribution must highlight CHT channel.")

    def test_04_run_sih_demo_script_runner(self):
        """Test that run_sih_demo() executes without raising exceptions for all 3 required faults."""
        for f in ["injector_fault", "oil_pressure", "overheat"]:
            try:
                run_sih_demo(fault_name=f, fast_mode=True)
            except Exception as e:
                self.fail(f"run_sih_demo failed for fault '{f}' with exception: {e}")


if __name__ == "__main__":
    unittest.main()
