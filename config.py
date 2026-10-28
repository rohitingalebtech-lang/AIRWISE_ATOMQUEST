"""
AirWise - Configuration Module
===============================
Project: AirWise — A Personalised Comfort Learning System for Fans
Team: Rohit Ingale, Sarthak Avhad, Gargi Rane, Hitesh Yuvare
College: Nutan Maharashtra Institute of Engineering and Technology (NMIET), Pune
Track: Track 1 — Fan (AtomQUEST 2026 Round 2)
"""

import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Database configuration (supports environment variable override, e.g. for Render persistent disks)
DATABASE_PATH = os.environ.get("DATABASE_PATH", str(os.path.join(BASE_DIR, "airwise.db")))

# Machine Learning & Synthetic Data Configuration
RANDOM_SEED = 42
SYNTHETIC_DATASET_SIZE = 1200
TRAIN_TEST_SPLIT_RATIO = 0.20  # 80% train, 20% test

# Valid Time of Day Categories
TIME_OF_DAY_CATEGORIES = ["Morning", "Afternoon", "Evening", "Night"]

# Mapping between string categories and numerical values for ML
TIME_OF_DAY_ENCODING = {
    "Morning": 0,
    "Afternoon": 1,
    "Evening": 2,
    "Night": 3
}

TIME_OF_DAY_DECODING = {v: k for k, v in TIME_OF_DAY_ENCODING.items()}

# Input Validation Limits (Reasonable ambient indoor comfort ranges)
TEMP_MIN_C = 12.0
TEMP_MAX_C = 45.0
HUMIDITY_MIN_PCT = 10.0
HUMIDITY_MAX_PCT = 95.0

# Fan Speed Descriptions (Levels 1 to 5)
FAN_SPEED_LEVELS = {
    1: {
        "level": 1,
        "name": "Level 1 — Whisper Breeze",
        "description": "Gentle, near-silent circulation for cool or resting conditions.",
        "rpm_range": "300 - 450 RPM (Simulated)",
        "color": "#38bdf8"
    },
    2: {
        "level": 2,
        "name": "Level 2 — Gentle Breeze",
        "description": "Mild airflow maintaining steady indoor thermal equilibrium.",
        "rpm_range": "450 - 650 RPM (Simulated)",
        "color": "#06b6d4"
    },
    3: {
        "level": 3,
        "name": "Level 3 — Moderate Flow",
        "description": "Balanced comfort cooling for typical warm ambient rooms.",
        "rpm_range": "650 - 900 RPM (Simulated)",
        "color": "#00f0ff"
    },
    4: {
        "level": 4,
        "name": "Level 4 — High Cooling",
        "description": "Strong convective airflow to accelerate sweat evaporation in hot/humid air.",
        "rpm_range": "900 - 1150 RPM (Simulated)",
        "color": "#f59e0b"
    },
    5: {
        "level": 5,
        "name": "Level 5 — Turbo Airflow",
        "description": "Maximum air displacement for severe heat discomfort.",
        "rpm_range": "1150 - 1400 RPM (Simulated)",
        "color": "#ef4444"
    }
}

# Personalisation Parameters
SIMILARITY_TEMP_THRESHOLD = 3.0       # within +/- 3.0 degrees Celsius
SIMILARITY_HUMIDITY_THRESHOLD = 15.0  # within +/- 15.0% relative humidity
MAX_FEEDBACK_CONSIDERED = 10          # Most recent relevant feedback items to inspect
