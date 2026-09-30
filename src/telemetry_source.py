"""AEROTWIN Telemetry Source Abstraction Layer.
SIH Problem Statement 26054 Telemetry Transport Layer.

Provides unified telemetry access across SYNTHETIC, FDR CSV, and CAN BUS modes.
All sources output the identical AEROTWIN schema:
[t, rpm, thr, alt, t_amb, map, cht, egt, oil_t, oil_p, fuel, battery_v, inj_timing, vib]
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import pandas as pd

from actual import make_run, DATA
from can_interface import CANInterface
from can_decoder import CANDecoder
from can_simulator import CANSimulator


class TelemetrySource(ABC):
    """Abstract base class for all AEROTWIN telemetry streams."""

    @abstractmethod
    def get_dataframe(self) -> pd.DataFrame:
        """Returns full telemetry dataframe adhering to AEROTWIN schema."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset stream pointer or session state."""
        pass


class SyntheticSource(TelemetrySource):
    """Generates synthetic physics telemetry using actual.make_run()."""

    def __init__(self, fault: Optional[str] = None, sev: float = 1.0, t0: float = 3000, seed: int = 0, dT_isa: float = 0.0):
        self.fault = fault
        self.sev = sev
        self.t0 = t0
        self.seed = seed
        self.dT_isa = dT_isa
        self._df: Optional[pd.DataFrame] = None
        self._labels: Optional[pd.DataFrame] = None
        self.reset()

    def reset(self) -> None:
        m, lab = make_run(
            fault=self.fault,
            sev=self.sev,
            t0=self.t0,
            seed=self.seed,
            dT_isa=self.dT_isa
        )
        self._df = m
        self._labels = lab

    def get_dataframe(self) -> pd.DataFrame:
        return self._df.copy() if self._df is not None else pd.DataFrame()

    def get_labels(self) -> pd.DataFrame:
        return self._labels.copy() if self._labels is not None else pd.DataFrame()


class CSVSource(TelemetrySource):
    """Reads telemetry from recorded FDR CSV log files."""

    def __init__(self, filepath_or_name: Union[str, Path]):
        if not filepath_or_name:
            fdr_files = sorted(p.name for p in DATA.glob("*.csv")) if DATA.exists() else []
            filepath_or_name = fdr_files[0] if fdr_files else "healthy_train_0.csv"
        p = Path(filepath_or_name)
        if not p.is_absolute():
            data_p = DATA / filepath_or_name
            if data_p.is_file():
                p = data_p
        self.filepath = p
        self._df: Optional[pd.DataFrame] = None
        self.reset()

    def reset(self) -> None:
        if self.filepath.is_file():
            self._df = pd.read_csv(self.filepath)
        else:
            fallback = list(DATA.glob("*.csv")) if DATA.exists() else []
            if fallback:
                self.filepath = fallback[0]
                self._df = pd.read_csv(self.filepath)
            else:
                raise FileNotFoundError(f"FDR CSV log file not found: {self.filepath}")

    def get_dataframe(self) -> pd.DataFrame:
        return self._df.copy() if self._df is not None else pd.DataFrame()



class CANSource(TelemetrySource):
    """Transmits telemetry via CAN simulator and reconstructs it via CANDecoder."""

    def __init__(self, source_df: pd.DataFrame, bus_interface: Optional[CANInterface] = None, packet_loss: float = 0.0, burst_loss: bool = False):
        self.source_df = source_df
        self.packet_loss = packet_loss
        self.burst_loss = burst_loss
        self.bus = bus_interface or CANInterface(interface="virtual", channel="vcan_source", auto_connect=True)
        self.simulator = CANSimulator(self.bus)
        self.decoder = CANDecoder()
        self._reconstructed_df: Optional[pd.DataFrame] = None
        self.reset()

    def reset(self) -> None:
        import random

        self.decoder = CANDecoder()
        rows: List[Dict[str, Any]] = []
        burst_counter = 0

        for idx, row in self.source_df.iterrows():
            row_dict = row.to_dict()
            mission_t = row_dict.get("t", float(idx))

            # Simulate burst packet loss (e.g. drop 10 consecutive frames)
            if self.burst_loss and (100 <= idx <= 110 or 300 <= idx <= 310):
                self.bus.status.dropped_frames += 11
                continue

            # Simulate random packet loss
            if self.packet_loss > 0.0 and random.random() < self.packet_loss:
                self.bus.status.dropped_frames += 1
                continue

            # Send over CAN interface
            self.simulator.send_telemetry_sample(row_dict)

            # Receive and decode all messages from bus
            for _ in range(11):
                msg = self.bus.recv(timeout=0.0001)
                if msg:
                    cid, data, ts = msg
                    self.decoder.decode_frame(cid, data, ts)

            # Extract snapshot from decoder state
            snapshot = self.decoder.get_telemetry_dict()
            # Retain mission time t from source dataframe
            snapshot["t"] = mission_t
            snapshot["can_receive_timestamp"] = self.decoder.can_receive_timestamp
            rows.append(snapshot)

        self._reconstructed_df = pd.DataFrame(rows)

    def get_dataframe(self) -> pd.DataFrame:
        return self._reconstructed_df.copy() if self._reconstructed_df is not None else pd.DataFrame()
