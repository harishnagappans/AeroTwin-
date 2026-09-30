"""Dashboard Metrics Loader.
SIH Problem Statement 26054 Telemetry & Digital Twin Platform.

Loads verified performance metrics dynamically from repository result artifacts:
- results/SIH_KEY_METRICS.json
- results/SIH_FINAL_BENCHMARK.csv
- results/TRUSTWORTHY_VALIDATION_SUMMARY.json
"""

import json
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"


@st.cache_data
def load_key_metrics():
    key_metrics_file = RESULTS_DIR / "SIH_KEY_METRICS.json"
    if key_metrics_file.exists():
        with open(key_metrics_file, "r") as f:
            return json.load(f)
    
    trustworthy_file = RESULTS_DIR / "TRUSTWORTHY_VALIDATION_SUMMARY.json"
    if trustworthy_file.exists():
        with open(trustworthy_file, "r") as f:
            return json.load(f)
            
    return None


@st.cache_data
def load_final_benchmark():
    benchmark_file = RESULTS_DIR / "SIH_FINAL_BENCHMARK.csv"
    if benchmark_file.exists():
        return pd.read_csv(benchmark_file)
    return None

