# AEROTWIN Prototype CAN Protocol Specification

## Project Disclaimer
> [!IMPORTANT]
> **AEROTWIN Prototype CAN Protocol is a project-defined telemetry protocol for simulation and hardware-in-the-loop demonstration. It is not claimed to be the proprietary CAN protocol of the Rotax 912 S/ULS ECU.**

---

## 1. Overview
The AEROTWIN Prototype CAN Protocol defines an 11-bit Standard Identifier CAN Bus transport format for high-speed MALE UAV engine telemetry streams. It provides lossy integer-scaled serialization and deserialization across 11 message types with a default bus speed of 500 kbps over Linux SocketCAN (`vcan0` / `can0`).

---

## 2. CAN Protocol Signal Dictionary Table

| CAN ID | Message Name | Signal Name | Bytes | Data Type | Scale | Offset | Physical Unit | Valid Range | Update Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `0x100` | `ENGINE_SPEED` | `rpm` | 0-1 | uint16 | 1.0 | 0.0 | RPM | 0 to 7000 RPM | 50 Hz |
| `0x100` | `ENGINE_SPEED` | `thr` | 2-3 | uint16 | 0.0001| 0.0 | fraction | 0.0 to 1.0 | 50 Hz |
| `0x100` | `ENGINE_SPEED` | `frame_counter`| 4-5 | uint16 | 1.0 | 0.0 | count | 0 to 65535 | 50 Hz |
| `0x101` | `ENGINE_PRESSURE`| `map` | 0-1 | uint16 | 0.01 | 0.0 | inHg | 0.0 to 40.0 inHg | 20 Hz |
| `0x101` | `ENGINE_PRESSURE`| `oil_p` | 2-3 | uint16 | 0.001 | 0.0 | bar | 0.0 to 10.0 bar | 20 Hz |
| `0x102` | `ENGINE_TEMP` | `cht` | 0-1 | uint16 | 0.1 | -40.0 | °C | -40.0 to 250.0 °C | 10 Hz |
| `0x102` | `ENGINE_TEMP` | `egt` | 2-3 | uint16 | 0.1 | 0.0 | °C | 0.0 to 1200.0 °C | 10 Hz |
| `0x103` | `ENGINE_OIL` | `oil_t` | 0-1 | uint16 | 0.1 | -40.0 | °C | -40.0 to 200.0 °C | 10 Hz |
| `0x104` | `ENGINE_FUEL` | `fuel` | 0-1 | uint16 | 0.01 | 0.0 | L/h | 0.0 to 60.0 L/h | 10 Hz |
| `0x105` | `ENGINE_VIBRATION`| `vib` | 0-1 | uint16 | 0.001 | 0.0 | mm/s | 0.0 to 30.0 mm/s | 50 Hz |
| `0x106` | `ENGINE_ELECTRICAL`| `battery_v` | 0-1 | uint16 | 0.001 | 0.0 | V | 0.0 to 25.0 V | 10 Hz |
| `0x107` | `ENGINE_INJECTION`| `inj_timing` | 0-1 | uint16 | 0.1 | -50.0 | deg | -50.0 to 60.0 deg | 20 Hz |
| `0x108` | `ENVIRONMENT` | `alt` | 0-1 | int16 | 1.0 | -500.0| m | -500 to 15000 m | 5 Hz |
| `0x108` | `ENVIRONMENT` | `t_amb` | 2-3 | int16 | 0.1 | 0.0 | °C | -60.0 to 70.0 °C | 5 Hz |
| `0x109` | `ENGINE_CONTROL` | `frame_counter`| 0-3 | uint32 | 1.0 | 0.0 | count | 0 to 4294967295 | 10 Hz |
| `0x109` | `ENGINE_CONTROL` | `status_flags` | 4-7 | uint32 | 1.0 | 0.0 | bitfield | 0 to 4294967295 | 10 Hz |
| `0x10A` | `ENGINE_STATUS` | `fault_flags` | 0-3 | uint32 | 1.0 | 0.0 | bitfield | 0 to 4294967295 | 10 Hz |

---

## 3. Serialization Encoding Equations

For any physical signal $S_{phys}$, raw integer byte value $N_{raw}$ is computed as:

$$N_{raw} = \text{round}\left( \frac{\text{clamp}(S_{phys}, S_{min}, S_{max}) - \text{Offset}}{\text{Scale}} \right)$$

Deserialization in `src/can_decoder.py` performs the exact inverse operation:

$$S_{phys} = (N_{raw} \times \text{Scale}) + \text{Offset}$$

---

## 4. SocketCAN Commands & Linux Quickstart

### Create & Activate Virtual CAN (`vcan0`)
```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

### Transmit Test Telemetry Frame (`candump` / `cansend`)
```bash
# Send ENGINE_SPEED (0x100) frame: RPM=5000 (0x1388), Throttle=0.85 (0x2134)
cansend vcan0 100#1388213400010000
```

### Monitor Live CAN Traffic
```bash
candump -c -t a vcan0
```
