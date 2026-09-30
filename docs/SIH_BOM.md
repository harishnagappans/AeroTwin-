# AEROTWIN Bill of Materials (BOM) & Software Cost Estimate
**SIH Problem Statement SIH26054 | Team HYDROVEX**

---

## 1. Overview

This document presents the complete Bill of Materials (BOM) for the AEROTWIN platform. It explicitly categorizes components into **CURRENT PROTOTYPE HARDWARE/SOFTWARE** (demonstrated in this submission) and **FUTURE PHYSICAL AIRCRAFT DEPLOYMENT HARDWARE**. Unquoted hardware items are designated as `PRICE TO BE QUOTED`.

---

## 2. Current Prototype Hardware & Software BOM

| Category | Component Name | Description / Specification | Quantity | Unit Price | Total Estimated Cost | Notes / Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Compute Hardware** | Development Workstation | x86_64 Host Processor (16 GB RAM, Dual Core+) | 1 | Existing Asset | $0.00 | Local host workstation running simulation |
| **Software Stack** | Python 3.9 Runtime | Open-source Python programming language | 1 | Open Source | $0.00 | Core runtime platform |
| **Software Library** | NumPy / Pandas / SciPy | Numerical computation & dataframe processing | 1 | Open Source | $0.00 | Core mathematical processing libraries |
| **Software Library** | scikit-learn | Isolation Forest & Random Forest ML framework | 1 | Open Source | $0.00 | Machine learning model training & inference |
| **Software Library** | Streamlit | Web application framework for GCS dashboard | 1 | Open Source | $0.00 | Command Center user interface |
| **Software Library** | Plotly | Interactive aerospace telemetry visualization | 1 | Open Source | $0.00 | Real-time telemetry graphing |
| **Software Library** | python-can | CAN bus abstraction library (`VirtualBus`) | 1 | Open Source | $0.00 | Virtual CAN socket transport layer |
| **Software Library** | joblib | Serialized binary model artifact storage | 1 | Open Source | $0.00 | Model persistence (`rf_validation.joblib`) |
| **TOTAL PROTOTYPE COST**| | | | | **$0.00** | Open-source prototype software stack |

---

## 3. Future Physical Aircraft Deployment Hardware BOM (Target Specification)

| Category | Component Name | Recommended Specification | Quantity | Unit Price | Total Estimated Cost | Deployment Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Edge Compute** | NVIDIA Jetson Orin Industrial | Ruggedized ARM + GPU edge processor (8 GB RAM) | 1 | PRICE TO BE QUOTED | PRICE TO BE QUOTED | Target Hardware Roadmap |
| **Avionics Transceiver**| Dual CAN 2.0B Controller | ISO 11898-2 Galvanically Isolated SPI-CAN Module | 1 | PRICE TO BE QUOTED | PRICE TO BE QUOTED | Target Hardware Roadmap |
| **Physical Sensors** | Thermocouple Sensors (CHT/EGT) | Aviation-grade K-Type CHT & EGT thermocouples | 6 | PRICE TO BE QUOTED | PRICE TO BE QUOTED | Existing Aircraft Equipment |
| **Physical Sensors** | Oil Pressure Transducer | Piezoresistive 0–10 bar pressure sensor | 1 | PRICE TO BE QUOTED | PRICE TO BE QUOTED | Existing Aircraft Equipment |
| **Physical Sensors** | Turbine Fuel Flow Meter | High-precision aviation fuel flow transducer | 1 | PRICE TO BE QUOTED | PRICE TO BE QUOTED | Existing Aircraft Equipment |
| **Physical Sensors** | Accelerometer | Single-axis piezo vibration sensor | 1 | PRICE TO BE QUOTED | PRICE TO BE QUOTED | Target Hardware Roadmap |
| **Enclosure** | IP67 Rugged Enclosure | Conductive-cooled aluminum IP67 chassis | 1 | PRICE TO BE QUOTED | PRICE TO BE QUOTED | Target Hardware Roadmap |
| **Wiring Harness** | MIL-SPEC Cable Assembly | Shielded twisted-pair MIL-STD-1553/CAN harness | 1 | PRICE TO BE QUOTED | PRICE TO BE QUOTED | Target Hardware Roadmap |
| **TOTAL DEPLOYMENT COST**| | | | | **PRICE TO BE QUOTED** | Subject to OEM procurement quotes |
