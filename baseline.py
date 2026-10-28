"""
AirWise - Rule-Based Baseline Engine
====================================
Implements a deterministic, heuristic rule-based recommendation algorithm using the
exact same input features (temperature, relative humidity, time of day).

Provides a fair engineering baseline to compare against the DecisionTreeClassifier.
Evaluates on the exact same held-out test split for transparent benchmarking.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
from config import FAN_SPEED_LEVELS, TIME_OF_DAY_DECODING


def rule_based_predict(temperature: float, humidity: float, time_of_day: str) -> int:
    """
    Deterministic rule-based logic for fan speed recommendation.

    Heuristic Rules:
    1. Base Temperature thresholding:
       - < 20°C: Level 1
       - 20°C to 24.9°C: Level 2
       - 25°C to 29.9°C: Level 3
       - 30°C to 34.9°C: Level 4
       - >= 35°C: Level 5
    2. Humidity correction:
       - Humidity >= 70%: +1 speed level (if < 5) to assist evaporative cooling
       - Humidity <= 30%: -1 speed level (if > 1) to prevent dry throat / irritation
    3. Night quiet-mode reduction:
       - If Night and speed > 1: -1 speed level for acoustic sleep comfort
    """
    # 1. Base temperature rule
    if temperature < 20.0:
        speed = 1
    elif temperature < 25.0:
        speed = 2
    elif temperature < 30.0:
        speed = 3
    elif temperature < 35.0:
        speed = 4
    else:
        speed = 5

    # 2. Humidity offset
    if humidity >= 70.0 and speed < 5:
        speed += 1
    elif humidity <= 30.0 and speed > 1:
        speed -= 1

    # 3. Night acoustic/metabolic offset
    if str(time_of_day).lower() == "night" and speed > 1:
        speed -= 1

    # Clamp strictly between 1 and 5
    return int(max(1, min(5, speed)))


def rule_based_predict_details(temperature: float, humidity: float, time_of_day: str) -> Dict[str, Any]:
    """
    Returns full details and rule trace for comparison displays.
    """
    speed = rule_based_predict(temperature, humidity, time_of_day)
    return {
        "speed": speed,
        "speed_info": FAN_SPEED_LEVELS.get(speed, {}),
        "method": "Rule-Based Heuristic Baseline",
        "rule_summary": (
            f"Evaluated static temperature threshold, humidity shift (+1 if >=70%, -1 if <=30%), "
            f"and nocturnal reduction (-1 for Night)."
        )
    }


def evaluate_baseline_on_test_set(X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
    """
    Evaluates the rule-based baseline on the exact same held-out test split
    used by the Decision Tree model for an unbiased, honest comparison.
    """
    preds = []
    for row in X_test:
        temp = float(row[0])
        hum = float(row[1])
        time_code = int(row[2])
        time_str = TIME_OF_DAY_DECODING.get(time_code, "Morning")
        preds.append(rule_based_predict(temp, hum, time_str))

    y_pred = np.array(preds)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=[1, 2, 3, 4, 5]).tolist()

    return {
        "accuracy": round(float(acc) * 100, 2),
        "precision_macro": round(float(prec) * 100, 2),
        "recall_macro": round(float(rec) * 100, 2),
        "f1_macro": round(float(f1) * 100, 2),
        "test_sample_count": len(y_test),
        "confusion_matrix": cm,
        "method_name": "Rule-Based Heuristic"
    }
