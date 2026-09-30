"""AEROTWIN Virtual ECU Unit Test Suite.
SIH Problem Statement 26054 Telemetry Transport Layer.

Tests all 14 required Virtual ECU features and state transitions.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from virtual_ecu import VirtualECU, ECUState, SensorHealth, ECU_FAULT_OIL_PRESSURE
from can_interface import CANInterface
from can_decoder import CANDecoder
from can_simulator import CANSimulator


class TestVirtualECU(unittest.TestCase):

    def setUp(self):
        self.ecu = VirtualECU()

    # 1. ECU startup
    def test_01_ecu_startup(self):
        self.ecu.power_on()
        self.assertEqual(self.ecu.state, ECUState.STARTING)
        self.assertTrue(self.ecu.communication_active)

    # 2. ECU shutdown
    def test_02_ecu_shutdown(self):
        self.ecu.power_on()
        self.ecu.power_off()
        self.assertEqual(self.ecu.state, ECUState.OFF)
        self.assertFalse(self.ecu.communication_active)

    # 3. Idle state
    def test_03_idle_state(self):
        self.ecu.power_on()
        sample = {"rpm": 1500.0, "thr": 0.1, "map": 15.0}
        out = self.ecu.process_telemetry_step(sample)
        self.assertEqual(self.ecu.state, ECUState.IDLE)
        self.assertEqual(out["engine_status"], ECUState.IDLE.value)

    # 4. Running state
    def test_04_running_state(self):
        self.ecu.power_on()
        sample = {"rpm": 4500.0, "thr": 0.7, "map": 24.0}
        out = self.ecu.process_telemetry_step(sample)
        self.assertEqual(self.ecu.state, ECUState.RUNNING)

    # 5. High-load state
    def test_05_high_load_state(self):
        self.ecu.power_on()
        sample = {"rpm": 5500.0, "thr": 0.95, "map": 27.5}
        out = self.ecu.process_telemetry_step(sample)
        self.assertEqual(self.ecu.state, ECUState.HIGH_LOAD)

    # 6. Throttle transition
    def test_06_throttle_transition(self):
        self.ecu.power_on()
        self.ecu.process_telemetry_step({"rpm": 3000.0, "thr": 0.3})
        # Sudden throttle jump from 0.3 to 0.8
        out = self.ecu.process_telemetry_step({"rpm": 3200.0, "thr": 0.8})
        self.assertEqual(self.ecu.state, ECUState.TRANSIENT)

    # 7. Injection timing response
    def test_07_injection_timing_response(self):
        inj_low = self.ecu.compute_injection_timing(rpm=1500.0, map_in=20.0, t_amb=15.0)
        inj_high = self.ecu.compute_injection_timing(rpm=5800.0, map_in=27.5, t_amb=15.0)
        self.assertGreater(inj_high, inj_low)

    # 8. Fuel control response
    def test_08_fuel_control_response(self):
        sample = {"rpm": 5000.0, "fuel": 22.5}
        out = self.ecu.process_telemetry_step(sample)
        self.assertAlmostEqual(out["fuel"], 22.5)

    # 9. Heartbeat
    def test_09_heartbeat(self):
        self.ecu.power_on()
        self.ecu.process_telemetry_step({"rpm": 3000.0, "thr": 0.5})
        summary = self.ecu.get_heartbeat_summary()
        self.assertTrue(summary["ecu_alive"])
        self.assertGreater(summary["frame_counter"], 0)

    # 10. Fault flags
    def test_10_fault_flags(self):
        self.ecu.power_on()
        # Simulate low oil pressure at high RPM
        sample = {"rpm": 4000.0, "oil_p": 0.8}
        out = self.ecu.process_telemetry_step(sample)
        self.assertTrue(out["fault_flags"] & ECU_FAULT_OIL_PRESSURE)

    # 11. Sensor health state
    def test_11_sensor_health_state(self):
        self.ecu.power_on()
        self.ecu.set_sensor_health("cht", SensorHealth.FAILED)
        out = self.ecu.process_telemetry_step({"rpm": 3000.0, "cht": 110.0})
        self.assertEqual(out["cht"], -999.0)

    # 12. CAN integration
    def test_12_can_integration(self):
        self.ecu.power_on()
        bus = CANInterface(interface="virtual", channel="ecu_test_12", auto_connect=True)
        sim = CANSimulator(bus)
        decoder = CANDecoder()

        ecu_sample = self.ecu.process_telemetry_step({"rpm": 4800.0, "thr": 0.8, "map": 25.0})
        sim.send_telemetry_sample(ecu_sample)

        for _ in range(11):
            msg = bus.recv(timeout=0.2)
            if msg:
                cid, data, ts = msg
                decoder.decode_frame(cid, data, ts)

        state = decoder.get_telemetry_dict()
        self.assertAlmostEqual(state["rpm"], 4800.0, delta=1.0)
        bus.disconnect()

    # 13. ECU communication loss
    def test_13_ecu_communication_loss(self):
        self.ecu.power_off()
        summary = self.ecu.get_heartbeat_summary()
        self.assertFalse(summary["ecu_alive"])

    # 14. ECU reset
    def test_14_ecu_reset(self):
        self.ecu.power_on()
        self.ecu.process_telemetry_step({"rpm": 3000.0})
        self.assertGreater(self.ecu.frame_counter, 0)
        # Power off and back on
        self.ecu.power_off()
        self.ecu.power_on()
        self.assertEqual(self.ecu.state, ECUState.STARTING)


if __name__ == "__main__":
    unittest.main()
