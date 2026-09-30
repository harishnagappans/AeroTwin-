"""AEROTWIN CAN Fault Propagation Test.
SIH Problem Statement 26054 Telemetry Transport Layer.

Proves that CAN transport layer preserves downstream AI/RUL diagnostic performance across all 9 fault types.
"""

import sys
import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from actual import make_run, FAULTS, DATA
from detect import load, analyze
from telemetry_source import CANSource


class TestCANFaultPropagation(unittest.TestCase):

    def setUp(self):
        self.models = load()

    def test_fault_propagation_over_can(self):
        print("\n" + "=" * 105)
        print("AEROTWIN CAN END-TO-END FAULT PROPAGATION COMPARISON REPORT")
        print("=" * 105)
        print(f"{'Fault':22s} {'Orig Alarm (s)':>15s} {'CAN Alarm (s)':>15s} {'Latency Diff (s)':>18s} {'Orig Class':>15s} {'CAN Class':>15s}")
        print("-" * 105)

        for f in FAULTS:
            # 1. Load test telemetry file
            m_orig = pd.read_csv(DATA / f"test_{f}.csv")
            t0 = pd.read_csv(DATA / f"labels_{f}.csv").query("active").t.min()

            # 2. Process via original direct telemetry stream
            res_orig = analyze(m_orig, self.models)
            ta_orig = res_orig["t_alarm"]
            class_orig = res_orig["fault"]

            # 3. Process via CAN transport layer
            can_source = CANSource(m_orig)
            m_can = can_source.get_dataframe()
            res_can = analyze(m_can, self.models)
            ta_can = res_can["t_alarm"]
            class_can = res_can["fault"]

            # Compare alarm latency
            del_orig = (ta_orig - t0) if ta_orig is not None else None
            del_can = (ta_can - t0) if ta_can is not None else None
            lat_diff = (del_can - del_orig) if (del_orig is not None and del_can is not None) else 0.0

            str_orig_alarm = f"{round(ta_orig):d}s" if ta_orig is not None else "None"
            str_can_alarm = f"{round(ta_can):d}s" if ta_can is not None else "None"
            str_lat_diff = f"{lat_diff:+.1f}s" if (ta_orig is not None and ta_can is not None) else "N/A"

            print(f"{f:22s} {str_orig_alarm:>15s} {str_can_alarm:>15s} {str_lat_diff:>18s} {str(class_orig):>15s} {str(class_can):>15s}")

            # Verification assertions
            self.assertEqual(class_orig, class_can, f"Classification mismatch for fault {f}: {class_orig} vs {class_can}")
            if ta_orig is not None and ta_can is not None:
                self.assertLessEqual(abs(lat_diff), 30.0, f"Alarm latency shift too large for fault {f}: {lat_diff}s")

        print("=" * 105 + "\n")


if __name__ == "__main__":
    unittest.main()
