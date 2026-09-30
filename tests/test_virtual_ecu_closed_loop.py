"""AEROTWIN Virtual ECU Closed-Loop & Fault Demonstration Test.
SIH Problem Statement 26054 Telemetry Transport Layer.

Demonstrates closed-loop throttle dynamics and explicit separation between
Virtual ECU BIST fault flags and independent AEROTWIN AI diagnosis.
"""

import sys
import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from actual import make_run
from virtual_ecu import VirtualECU
from telemetry_source import CANSource
from detect import load, analyze
from rul import rul, PRIMARY


class TestVirtualECUClosedLoop(unittest.TestCase):

    def setUp(self):
        self.models = load()
        self.ecu = VirtualECU()

    def test_01_closed_loop_throttle_transitions(self):
        print("\n" + "=" * 90)
        print("AEROTWIN VIRTUAL ECU CLOSED-LOOP THROTTLE TRANSITION DEMONSTRATION")
        print("=" * 90)

        self.ecu.power_on()
        m_base, _ = make_run(seed=100)

        # Apply closed-loop throttle profile transitions
        sample_rows = []
        for i, row in m_base.iterrows():
            r_dict = row.to_dict()
            # Override throttle profile for transition test
            if i < 50:
                r_dict["thr"] = 0.25
            elif i < 100:
                r_dict["thr"] = 0.50
            elif i < 150:
                r_dict["thr"] = 0.75
            elif i < 200:
                r_dict["thr"] = 1.00
            elif i < 250:
                r_dict["thr"] = 0.50  # Rapid 100% -> 50%
            elif i < 300:
                r_dict["thr"] = 0.80  # Rapid 50% -> 80%
            else:
                r_dict["thr"] = 0.30  # Rapid 80% -> 30%

            ecu_out = self.ecu.process_telemetry_step(r_dict)
            sample_rows.append(ecu_out)

        ecu_df = pd.DataFrame(sample_rows)

        # Pass through CAN -> Decoder -> Digital Twin -> AI
        can_source = CANSource(ecu_df)
        recon_df = can_source.get_dataframe()
        res = analyze(recon_df, self.models)

        print(f"Executed {len(recon_df)} steps of closed-loop throttle transitions.")
        print(f"Final ECU State: {self.ecu.state.name} | Frame Counter: {self.ecu.frame_counter}")
        print(f"AEROTWIN AI Diagnostic Output: Anomaly Alarm={res['t_alarm']} | Fault={res['fault']}")
        print("=" * 90 + "\n")

    def test_02_fault_demonstration_and_ai_separation(self):
        demo_faults = ["healthy", "misfire", "injector_fault", "oil_pressure", "overheat"]
        sd = {"cht": 1.54, "egt": 8.40, "oil_t": 0.68, "oil_p": 0.03, "fuel": 0.22, "vib": 0.05, "battery_v": 0.10, "inj_timing": 0.20}

        print("\n" + "=" * 115)
        print("AEROTWIN VIRTUAL ECU BIST FLAGS vs INDEPENDENT AEROTWIN AI DIAGNOSIS DEMONSTRATION")
        print("=" * 115)
        print(f"{'Injected Fault':18s} {'ECU BIST Flag':>18s} {'CAN Alarm (s)':>15s} {'AEROTWIN AI Diagnosis':>24s} {'RUL Est (min)':>16s}")
        print("-" * 115)

        for f in demo_faults:
            self.ecu = VirtualECU()
            self.ecu.power_on()
            m_orig, _ = make_run(fault=None if f == "healthy" else f, seed=505)

            ecu_rows = [self.ecu.process_telemetry_step(r.to_dict()) for _, r in m_orig.iterrows()]
            ecu_df = pd.DataFrame(ecu_rows)

            # Transport over CAN
            can_source = CANSource(ecu_df)
            recon_df = can_source.get_dataframe()

            # Process via independent AEROTWIN AI Pipeline
            res = analyze(recon_df, self.models)
            ta = res["t_alarm"]
            ai_class = res["fault"] or "healthy"

            # Check ECU BIST flag string
            ecu_bist_flag = f"0x{self.ecu.fault_flags:04X}"

            # Calculate RUL estimate if fault detected
            rul_str = "N/A"
            if ai_class in PRIMARY and ta is not None:
                from twin import residuals as twin_residuals
                res_df = twin_residuals(recon_df)
                rul_res = rul(res_df, ai_class, ta + 300, sd, ta=ta)
                if rul_res["rul_s"] is not None:
                    rul_str = f"{rul_res['rul_s']/60:.1f} min"

            str_alarm = f"{round(ta):d}s" if ta is not None else "Nominal"

            print(f"{f:18s} {ecu_bist_flag:>18s} {str_alarm:>15s} {ai_class:>24s} {rul_str:>16s}")

            if f != "healthy":
                self.assertIsNotNone(ta)
                self.assertEqual(ai_class, f)

        print("=" * 115 + "\n")


if __name__ == "__main__":
    unittest.main()
