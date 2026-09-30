"""AEROTWIN Mission Profiles & Environmental Simulation Test Suite.
SIH Problem Statement 26054 Telemetry Transport Layer.

Tests all 12 required mission profile and environmental adaptation scenarios.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from mission_profiles import (
    MissionProfileType,
    get_mission_trajectory,
    run_mission_profile,
    calculate_mission_metrics,
    MissionReplayer,
)
from detect import load, analyze


class TestMissionProfiles(unittest.TestCase):

    def setUp(self):
        self.models = load()

    # 1. Cruise generation
    def test_01_cruise_generation(self):
        t, rpm, thr, alt, dT = get_mission_trajectory(MissionProfileType.CRUISE)
        self.assertGreater(len(t), 0)
        self.assertEqual(dT, 0.0)

    # 2. High-altitude generation
    def test_02_high_altitude_generation(self):
        t, rpm, thr, alt, dT = get_mission_trajectory(MissionProfileType.HIGH_ALTITUDE)
        self.assertEqual(max(alt), 6000.0)
        self.assertEqual(dT, -10.0)

    # 3. Hot-weather generation
    def test_03_hot_weather_generation(self):
        t, rpm, thr, alt, dT = get_mission_trajectory(MissionProfileType.HOT_WEATHER)
        self.assertEqual(dT, 35.0)

    # 4. Endurance generation
    def test_04_endurance_generation(self):
        t, rpm, thr, alt, dT = get_mission_trajectory(MissionProfileType.ENDURANCE)
        self.assertAlmostEqual(max(t), 14400.0, delta=2.0)

    # 5. Rapid throttle generation
    def test_05_rapid_throttle_generation(self):
        t, rpm, thr, alt, dT = get_mission_trajectory(MissionProfileType.RAPID_THROTTLE)
        self.assertIn(1.0, thr)
        self.assertIn(0.2, thr)

    # 6. Combined-stress generation
    def test_06_combined_stress_generation(self):
        t, rpm, thr, alt, dT = get_mission_trajectory(MissionProfileType.COMBINED_STRESS)
        self.assertEqual(max(alt), 5000.0)
        self.assertEqual(dT, 25.0)

    # 7. Mission phase transitions
    def test_07_mission_phase_transitions(self):
        m, _ = run_mission_profile(MissionProfileType.CRUISE, fault=None)
        phases = set(m["mission_phase"].unique())
        self.assertIn("GROUND", phases)
        self.assertIn("TAKEOFF", phases)
        self.assertIn("CLIMB", phases)
        self.assertIn("CRUISE", phases)

    # 8. Environmental parameter propagation
    def test_08_environmental_parameter_propagation(self):
        m_hot, _ = run_mission_profile(MissionProfileType.HOT_WEATHER, fault=None)
        m_norm, _ = run_mission_profile(MissionProfileType.CRUISE, fault=None)
        self.assertGreater(m_hot["t_amb"].mean(), m_norm["t_amb"].mean())
        self.assertGreater(m_hot["cht"].mean(), m_norm["cht"].mean())

    # 9. Healthy Digital Twin response (verifies no false alarms on healthy environment)
    def test_09_healthy_digital_twin_response(self):
        for profile in (MissionProfileType.CRUISE, MissionProfileType.HOT_WEATHER, MissionProfileType.HIGH_ALTITUDE):
            m, _ = run_mission_profile(profile, fault=None, seed=55)
            res = analyze(m, self.models)
            self.assertIsNone(res["t_alarm"], f"False alarm triggered on healthy {profile.name} mission")

    # 10. Fault injection during environmental stress (verifies detection across 6 fault-environment pairs)
    def test_10_fault_injection_during_mission(self):
        env_fault_pairs = [
            (MissionProfileType.HIGH_ALTITUDE, "oil_pressure"),
            (MissionProfileType.HOT_WEATHER, "cooling"),
            (MissionProfileType.HOT_WEATHER, "overheat"),
            (MissionProfileType.RAPID_THROTTLE, "misfire"),
            (MissionProfileType.ENDURANCE, "fuel_system"),
            (MissionProfileType.COMBINED_STRESS, "combustion_instability"),
        ]

        print("\n" + "=" * 105)
        print("AEROTWIN FAULT DIAGNOSIS UNDER ENVIRONMENTAL STRESS DEMONSTRATION")
        print("=" * 105)
        print(f"{'Profile':20s} {'Injected Fault':24s} {'Alarm Time (s)':>15s} {'AI Diagnosis':>24s} {'Match':>10s}")
        print("-" * 105)

        for profile, f in env_fault_pairs:
            m, _ = run_mission_profile(profile, fault=f, seed=99)
            res = analyze(m, self.models)
            ta = res["t_alarm"]
            diag = res["fault"]

            print(f"{profile.name:20s} {f:24s} {f'{round(ta):d}s' if ta else 'None':>15s} {str(diag):>24s} {'YES' if diag == f else 'NO':>10s}")
            self.assertIsNotNone(ta, f"Failed to detect {f} under {profile.name} stress")
            self.assertEqual(diag, f, f"Misclassified {f} as {diag} under {profile.name} stress")

        print("=" * 105 + "\n")

    # 11. Mission replay
    def test_11_mission_replay(self):
        m, _ = run_mission_profile(MissionProfileType.CRUISE, fault="misfire", seed=77)
        replayer = MissionReplayer(self.models)
        ai_res, metrics = replayer.replay_mission(m)
        self.assertIsNotNone(ai_res["t_alarm"])
        self.assertEqual(ai_res["fault"], "misfire")
        self.assertEqual(metrics["diagnosed_fault"], "misfire")

    # 12. Mission metrics calculation
    def test_12_mission_metrics_calculation(self):
        m, _ = run_mission_profile(MissionProfileType.CRUISE, fault=None)
        metrics = calculate_mission_metrics(m)
        self.assertGreater(metrics["duration_seconds"], 0)
        self.assertGreater(metrics["total_fuel_consumed_l"], 0)
        self.assertEqual(metrics["diagnosed_fault"], "NOMINAL")


if __name__ == "__main__":
    unittest.main()
