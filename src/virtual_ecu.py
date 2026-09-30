"""AEROTWIN Virtual ECU / FADEC Simulation Layer.
SIH Problem Statement 26054 Telemetry Transport Layer.

DISCLAIMER:
The Virtual ECU/FADEC is a software simulation used to demonstrate the AEROTWIN architecture.
It is not a production aircraft ECU/FADEC and has not been certified or validated for flight use.
"""

import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("AEROTWIN_VIRTUAL_ECU")


class ECUState(Enum):
    """Virtual ECU / FADEC Operational States."""
    OFF = 0
    STARTING = 1
    IDLE = 2
    RUNNING = 3
    HIGH_LOAD = 4
    TRANSIENT = 5
    SHUTDOWN = 6
    FAULT = 7


class SensorHealth(Enum):
    """Sensor Health Status."""
    VALID = 0
    DEGRADED = 1
    FAILED = 2


# Virtual ECU BIST Fault Bitmasks
ECU_FAULT_NONE = 0x0000
ECU_FAULT_COOLING = 0x0001
ECU_FAULT_OIL_PRESSURE = 0x0002
ECU_FAULT_MISFIRE = 0x0004
ECU_FAULT_FUEL_SYSTEM = 0x0008
ECU_FAULT_SENSOR_DRIFT = 0x0010
ECU_FAULT_OVERHEAT = 0x0020
ECU_FAULT_INJECTOR = 0x0040
ECU_FAULT_COMBUSTION_INSTABILITY = 0x0080
ECU_FAULT_ALTERNATOR = 0x0100


class VirtualECU:
    """AEROTWIN Virtual ECU / FADEC Simulation Layer.

    Acts as the electronic control and measurement layer between the engine physics
    and the CAN bus transport layer. Does NOT replace engine physics model (`src/engine.py`).
    """

    def __init__(self, sample_rate_hz: float = 10.0):
        self.sample_rate_hz = sample_rate_hz
        self.state = ECUState.OFF
        self.frame_counter = 0
        self.heartbeat_tick = 0
        self.last_thr: Optional[float] = None
        self.last_time = time.time()
        self.communication_active = True

        # Sensor health states
        self.sensor_health: Dict[str, SensorHealth] = {
            "cht": SensorHealth.VALID,
            "egt": SensorHealth.VALID,
            "oil_t": SensorHealth.VALID,
            "oil_p": SensorHealth.VALID,
            "fuel": SensorHealth.VALID,
            "vib": SensorHealth.VALID,
            "battery_v": SensorHealth.VALID,
        }

        # Simulated ECU Internal Diagnostic Flags (BIST)
        self.fault_flags = ECU_FAULT_NONE

    def power_on(self) -> None:
        """Powers on the Virtual ECU."""
        self.state = ECUState.STARTING
        self.communication_active = True
        logger.info("[VIRTUAL ECU] Powering ON. Initiating ECU self-test...")

    def power_off(self) -> None:
        """Powers off the Virtual ECU."""
        self.state = ECUState.OFF
        self.communication_active = False
        logger.info("[VIRTUAL ECU] Powering OFF.")

    def set_sensor_health(self, sensor_name: str, health: SensorHealth) -> None:
        """Sets simulated health state for an ECU sensor."""
        if sensor_name in self.sensor_health:
            self.sensor_health[sensor_name] = health
            logger.info(f"[VIRTUAL ECU] Sensor '{sensor_name}' health set to {health.name}")

    def compute_injection_timing(self, rpm: float, map_in: float, t_amb: float) -> float:
        """Calculates ECU injection/ignition timing advance based on operating parameters.
        Nominal 15 to 25 deg BTDC scaled with RPM, MAP, and ambient conditions.
        """
        base_timing = 15.0 + 10.0 * (min(rpm, 5800.0) / 5800.0)
        map_corr = 2.0 * ((map_in - 29.92) / 10.0)
        temp_corr = -0.05 * (t_amb - 15.0)
        return max(-50.0, min(60.0, base_timing + map_corr + temp_corr))

    def evaluate_state_machine(self, rpm: float, thr: float) -> ECUState:
        """Evaluates ECU state transitions based on RPM and throttle dynamics."""
        if self.last_thr is None:
            d_thr = 0.0
        else:
            d_thr = abs(thr - self.last_thr)
        self.last_thr = thr

        if not self.communication_active or self.state == ECUState.OFF:
            return ECUState.OFF

        if self.fault_flags != ECU_FAULT_NONE and (self.fault_flags & (ECU_FAULT_OIL_PRESSURE | ECU_FAULT_OVERHEAT)):
            return ECUState.FAULT

        if rpm < 100.0:
            return ECUState.OFF if thr == 0.0 else ECUState.STARTING
        elif 100.0 <= rpm < 1200.0:
            return ECUState.STARTING
        elif 1200.0 <= rpm < 2000.0:
            return ECUState.IDLE
        elif d_thr > 0.15:
            return ECUState.TRANSIENT
        elif rpm >= 5200.0 or thr >= 0.9:
            return ECUState.HIGH_LOAD
        else:
            return ECUState.RUNNING

    def evaluate_bist_fault_flags(self, telemetry: Dict[str, Any]) -> int:
        """Evaluates simulated ECU Built-In Self-Test (BIST) diagnostic flags.
        NOTE: These flags represent what the ECU believes it detects. They do NOT replace
        the independent downstream AEROTWIN AI diagnosis!
        """
        flags = ECU_FAULT_NONE
        cht = float(telemetry.get("cht", 15.0))
        oil_t = float(telemetry.get("oil_t", 15.0))
        oil_p = float(telemetry.get("oil_p", 2.0))
        rpm = float(telemetry.get("rpm", 0.0))
        vib = float(telemetry.get("vib", 0.6))
        fuel = float(telemetry.get("fuel", 2.5))
        bat_v = float(telemetry.get("battery_v", 14.1))
        inj = float(telemetry.get("inj_timing", 15.0))

        if oil_p < 1.5 and rpm > 2000.0:
            flags |= ECU_FAULT_OIL_PRESSURE
        if cht > 130.0 and oil_t > 120.0:
            flags |= ECU_FAULT_OVERHEAT
        elif cht > 130.0 and oil_t <= 120.0:
            flags |= ECU_FAULT_COOLING
        if abs(inj - 20.0) > 4.5:
            flags |= ECU_FAULT_INJECTOR
        if vib > 3.0:
            flags |= ECU_FAULT_COMBUSTION_INSTABILITY
        elif vib > 2.0:
            flags |= ECU_FAULT_MISFIRE
        if fuel > 28.0:
            flags |= ECU_FAULT_FUEL_SYSTEM
        if bat_v < 11.5:
            flags |= ECU_FAULT_ALTERNATOR

        self.fault_flags = flags
        return flags

    def process_telemetry_step(self, engine_sample: Dict[str, Any]) -> Dict[str, Any]:
        """Ingests engine physics sample, applies ECU control logic, and outputs ECU telemetry schema."""
        self.frame_counter += 1
        self.heartbeat_tick = (self.heartbeat_tick + 1) % 65536

        rpm = float(engine_sample.get("rpm", 0.0))
        thr = float(engine_sample.get("thr", 0.0))
        map_in = float(engine_sample.get("map", 29.92))
        t_amb = float(engine_sample.get("t_amb", 15.0))
        alt = float(engine_sample.get("alt", 0.0))

        # Evaluate state machine
        self.state = self.evaluate_state_machine(rpm, thr)

        # Compute injection timing control
        inj_timing_computed = self.compute_injection_timing(rpm, map_in, t_amb)

        # Construct ECU telemetry output
        ecu_output = dict(engine_sample)
        if "inj_timing" not in engine_sample:
            ecu_output["inj_timing"] = inj_timing_computed
        ecu_output["engine_status"] = self.state.value
        ecu_output["frame_counter"] = self.frame_counter

        # Evaluate ECU BIST fault flags
        fault_flags = self.evaluate_bist_fault_flags(ecu_output)
        ecu_output["fault_flags"] = fault_flags

        # Apply sensor health status overrides
        for sensor, health in self.sensor_health.items():
            if health == SensorHealth.FAILED and sensor in ecu_output:
                # Sensor failure produces extreme/out-of-range value
                ecu_output[sensor] = -999.0

        return ecu_output

    def get_heartbeat_summary(self) -> Dict[str, Any]:
        """Returns ECU heartbeat summary dictionary."""
        return {
            "ecu_alive": self.communication_active and self.state != ECUState.OFF,
            "ecu_state": self.state.name,
            "frame_counter": self.frame_counter,
            "fault_flags": self.fault_flags,
            "sensor_health": {k: v.name for k, v in self.sensor_health.items()}
        }
