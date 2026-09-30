"""AEROTWIN SocketCAN Interface & Transport Layer.
SIH Problem Statement 26054 Telemetry Transport Layer.

Wraps python-can with configurable SocketCAN (vcan0/can0) support and virtual bus fallback.
"""

import sys
import time
import logging
from typing import Optional, List, Dict, Any, Tuple

import can
from can_decoder import CANStatus

logger = logging.getLogger("AEROTWIN_CAN")


class CANInterface:
    """Configurable CAN bus wrapper supporting SocketCAN (Linux vcan0/can0) and Virtual fallback."""

    def __init__(self, interface: str = "vcan0", channel: str = "vcan0", bitrate: int = 500000, auto_connect: bool = True):
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus: Optional[can.BusABC] = None
        self.status = CANStatus()
        self.is_connected = False

        if auto_connect:
            self.connect()

    def connect(self) -> bool:
        """Initialize CAN bus connection."""
        try:
            # 1. Attempt primary requested interface (SocketCAN on Linux by default)
            if self.interface in ("vcan0", "can0", "socketcan"):
                self.bus = can.interface.Bus(
                    interface="socketcan",
                    channel=self.channel,
                    bitrate=self.bitrate,
                    receive_own_messages=True
                )
            else:
                self.bus = can.interface.Bus(
                    interface=self.interface,
                    channel=self.channel,
                    bitrate=self.bitrate,
                    receive_own_messages=True
                )
            self.is_connected = True
            logger.info(f"Connected to CAN bus: bustype='{self.interface}', channel='{self.channel}', bitrate={self.bitrate}")
            return True

        except Exception as e:
            logger.warning(f"Failed to connect to primary CAN bus ('{self.interface}':'{self.channel}'): {e}")
            # 2. Virtual bus fallback for Windows / cross-platform testing
            try:
                logger.info("Initializing fallback virtual CAN bus ('virtual' interface)...")
                self.bus = can.interface.Bus(
                    bustype="virtual",
                    channel="vcan_fallback",
                    receive_own_messages=True
                )
                self.is_connected = True
                logger.info("Successfully connected to virtual CAN bus.")
                return True
            except Exception as ve:
                logger.error(f"Failed to initialize virtual CAN bus fallback: {ve}")
                self.is_connected = False
                return False

    def disconnect(self) -> None:
        """Close CAN bus socket connection."""
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down CAN bus: {e}")
            self.bus = None
        self.is_connected = False

    def set_filters(self, can_ids: List[int]) -> None:
        """Apply standard 11-bit CAN ID filters."""
        if self.bus:
            filters = [{"can_id": cid, "can_mask": 0x7FF, "extended": False} for cid in can_ids]
            self.bus.set_filters(filters)

    def send(self, can_id: int, data: bytes, timeout: float = 1.0) -> bool:
        """Transmit a raw 8-byte CAN frame."""
        if not self.bus or not self.is_connected:
            logger.error("Cannot send frame: CAN bus not connected.")
            self.status.dropped_frames += 1
            return False

        try:
            msg = can.Message(
                arbitration_id=can_id,
                data=data,
                is_extended_id=False,
                timestamp=time.time()
            )
            self.bus.send(msg, timeout=timeout)
            self.status.transmitted_frames += 1
            return True
        except can.CanError as e:
            logger.error(f"Failed to transmit CAN frame 0x{can_id:03X}: {e}")
            self.status.dropped_frames += 1
            return False

    def recv(self, timeout: float = 0.1) -> Optional[Tuple[int, bytes, float]]:
        """Receive a CAN frame. Returns (can_id, data, timestamp) or None on timeout."""
        if not self.bus or not self.is_connected:
            return None

        msg = self.bus.recv(timeout=timeout)
        if msg is None:
            self.status.timeout_count += 1
            return None

        return msg.arbitration_id, bytes(msg.data), msg.timestamp
