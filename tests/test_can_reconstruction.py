"""AEROTWIN CAN Reconstruction Test.
SIH Problem Statement 26054 Telemetry Transport Layer.

Encodes synthetic mission telemetry into CAN frames, streams through CAN bus,
decodes, reconstructs the dataset, and computes signal quantization errors (MAE, Max Error, Rel Error).
"""

import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from actual import make_run
from telemetry_source import SyntheticSource, CANSource

SIGNALS = ["rpm", "map", "cht", "egt", "oil_t", "oil_p", "fuel", "vib", "battery_v", "inj_timing", "alt", "t_amb", "thr"]


class TestCANReconstruction(unittest.TestCase):

    def test_can_telemetry_reconstruction(self):
        # 1. Generate original synthetic mission telemetry
        synth_source = SyntheticSource(seed=42)
        orig_df = synth_source.get_dataframe()
        self.assertGreater(len(orig_df), 0)

        # 2. Transmit through CAN transport layer and decode
        can_source = CANSource(orig_df)
        recon_df = can_source.get_dataframe()
        self.assertEqual(len(orig_df), len(recon_df))

        print("\n" + "=" * 80)
        print("AEROTWIN CAN TELEMETRY RECONSTRUCTION ERROR REPORT")
        print("=" * 80)
        print(f"{'Signal':15s} {'MAE':>12s} {'Max Error':>12s} {'Mean Orig':>12s} {'Rel Error (%)':>15s}")
        print("-" * 80)

        for col in SIGNALS:
            orig = orig_df[col].values
            recon = recon_df[col].values

            err = np.abs(orig - recon)
            mae = float(np.mean(err))
            max_err = float(np.max(err))
            mean_orig = float(np.mean(np.abs(orig)))
            rel_err = (mae / mean_orig * 100.0) if mean_orig > 1e-6 else 0.0

            print(f"{col:15s} {mae:12.4f} {max_err:12.4f} {mean_orig:12.4f} {rel_err:14.2f}%")

            # Verify quantization error bounds
            if col == "rpm":
                self.assertLess(mae, 1.0)
            elif col == "thr":
                self.assertLess(mae, 0.001)
            elif col == "map":
                self.assertLess(mae, 0.02)
            elif col in ("cht", "egt", "oil_t", "t_amb", "inj_timing"):
                self.assertLess(mae, 0.1)
            elif col in ("oil_p", "vib", "battery_v"):
                self.assertLess(mae, 0.005)

        print("=" * 80 + "\n")


if __name__ == "__main__":
    unittest.main()
