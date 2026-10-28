"""
AirWise - Machine Learning Comfort Model
========================================
Implements a genuine scikit-learn DecisionTreeClassifier trained on a reproducible
synthetic thermal comfort dataset based on psychrometric and heat-index principles.

IMPORTANT SIMULATION NOTICE:
This model operates on synthetic data simulating simplified thermal comfort assumptions.
It does NOT directly measure human physiological sensation or control hardware.
"""

import os
# Ensure deterministic, single-threaded execution on Windows environments
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)
from typing import Dict, Any, Tuple

from config import (
    RANDOM_SEED,
    SYNTHETIC_DATASET_SIZE,
    TRAIN_TEST_SPLIT_RATIO,
    TIME_OF_DAY_ENCODING,
    TIME_OF_DAY_DECODING,
    FAN_SPEED_LEVELS,
    TEMP_MIN_C,
    TEMP_MAX_C,
    HUMIDITY_MIN_PCT,
    HUMIDITY_MAX_PCT
)


class AirWiseModelManager:
    """
    Manages synthetic data generation, model training, evaluation, and inference.
    Maintains reproducibility via a fixed random seed.
    """
    def __init__(self, seed: int = RANDOM_SEED):
        self.seed = seed
        self.model: DecisionTreeClassifier = None
        self.evaluation_results: Dict[str, Any] = {}
        self.dataset_summary: Dict[str, Any] = {}
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self._is_trained = False

        # Initialize and train upon instantiation
        self.train_and_evaluate()

    def generate_synthetic_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates a synthetic thermal comfort dataset using documented thermodynamic
        and psychrometric assumptions.

        Assumptions:
        1. Temperature ranges between 14°C and 42°C (indoor ambient).
        2. Relative Humidity ranges between 20% and 90%.
        3. Time of day introduces circadian and metabolic factors:
           - Night: Lower metabolic rate, desire for quieter airflow (-2.0 comfort offset).
           - Morning: Neutral circadian baseline (0.0 offset).
           - Afternoon: Peak solar irradiance & alertness (+1.5 offset).
           - Evening: Residual indoor warmth (+0.5 offset).
        4. Heat index proxy S = Temp + 0.14 * (Humidity - 40) + Time_Offset.
        5. Stochastic variance (~10% noise) simulates natural human comfort variability.
        """
        rng = np.random.RandomState(self.seed)

        # 1. Synthesize temperatures: continuous uniform distribution
        temperatures = rng.uniform(15.0, 41.0, size=SYNTHETIC_DATASET_SIZE)

        # 2. Synthesize relative humidity: continuous uniform distribution
        humidities = rng.uniform(20.0, 90.0, size=SYNTHETIC_DATASET_SIZE)

        # 3. Synthesize time of day (0: Morning, 1: Afternoon, 2: Evening, 3: Night)
        time_categories = rng.choice([0, 1, 2, 3], size=SYNTHETIC_DATASET_SIZE)

        # Time offsets for thermal comfort
        time_offsets = np.array([0.0, 1.5, 0.5, -2.0])

        # 4. Compute synthetic thermal discomfort score
        discomfort_score = (
            temperatures
            + 0.14 * (humidities - 40.0)
            + time_offsets[time_categories]
        )

        # 5. Map discomfort score to standard 5-level fan speeds
        labels = np.zeros(SYNTHETIC_DATASET_SIZE, dtype=int)
        for i in range(SYNTHETIC_DATASET_SIZE):
            score = discomfort_score[i]
            if score < 21.0:
                base_speed = 1
            elif score < 25.5:
                base_speed = 2
            elif score < 30.5:
                base_speed = 3
            elif score < 36.0:
                base_speed = 4
            else:
                base_speed = 5

            # Introduce ~10% stochastic human preference variation (±1 speed level)
            if rng.rand() < 0.10:
                noise = rng.choice([-1, 1])
                base_speed = int(np.clip(base_speed + noise, 1, 5))

            labels[i] = base_speed

        # Assemble feature matrix: [Temperature, Humidity, Time_Of_Day]
        X = np.column_stack([temperatures, humidities, time_categories])
        y = labels

        # Store summary metadata
        self.dataset_summary = {
            "total_samples": SYNTHETIC_DATASET_SIZE,
            "features": ["Temperature (°C)", "Relative Humidity (%)", "Time of Day (Encoded)"],
            "target": "Recommended Fan Speed Level (1 to 5)",
            "class_distribution": {
                f"Level {k}": int(np.sum(y == k)) for k in range(1, 6)
            },
            "temp_range": [round(float(np.min(temperatures)), 1), round(float(np.max(temperatures)), 1)],
            "humidity_range": [round(float(np.min(humidities)), 1), round(float(np.max(humidities)), 1)],
            "random_seed": self.seed
        }

        return X, y

    def train_and_evaluate(self):
        """
        Trains the DecisionTreeClassifier on the training split and calculates
        actual measured performance metrics on the held-out test split.
        Never hardcodes results.
        """
        X, y = self.generate_synthetic_data()

        # Stratified train-test split ensures proportional representation of all 5 speed classes
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y,
            test_size=TRAIN_TEST_SPLIT_RATIO,
            random_state=self.seed,
            stratify=y
        )

        # Train a scikit-learn DecisionTreeClassifier
        # Constrained max_depth avoids overfitting while capturing multi-feature interaction
        self.model = DecisionTreeClassifier(
            max_depth=5,
            min_samples_leaf=4,
            random_state=self.seed
        )
        self.model.fit(self.X_train, self.y_train)

        # Predict on held-out test set
        y_test_pred = self.model.predict(self.X_test)

        # Calculate genuine, measured metrics
        test_acc = accuracy_score(self.y_test, y_test_pred)
        train_acc = accuracy_score(self.y_train, self.model.predict(self.X_train))
        precision_macro = precision_score(self.y_test, y_test_pred, average="macro", zero_division=0)
        recall_macro = recall_score(self.y_test, y_test_pred, average="macro", zero_division=0)
        f1_macro = f1_score(self.y_test, y_test_pred, average="macro", zero_division=0)
        cm = confusion_matrix(self.y_test, y_test_pred, labels=[1, 2, 3, 4, 5]).tolist()

        # Detailed per-class metrics
        report_dict = classification_report(
            self.y_test,
            y_test_pred,
            labels=[1, 2, 3, 4, 5],
            target_names=[f"Level {i}" for i in range(1, 6)],
            output_dict=True,
            zero_division=0
        )

        per_class_metrics = {}
        for i in range(1, 6):
            key = f"Level {i}"
            if key in report_dict:
                per_class_metrics[key] = {
                    "precision": round(report_dict[key]["precision"] * 100, 1),
                    "recall": round(report_dict[key]["recall"] * 100, 1),
                    "f1_score": round(report_dict[key]["f1-score"] * 100, 1),
                    "support": int(report_dict[key]["support"])
                }

        self.evaluation_results = {
            "test_accuracy": round(float(test_acc) * 100, 2),
            "train_accuracy": round(float(train_acc) * 100, 2),
            "precision_macro": round(float(precision_macro) * 100, 2),
            "recall_macro": round(float(recall_macro) * 100, 2),
            "f1_macro": round(float(f1_macro) * 100, 2),
            "test_sample_count": len(self.y_test),
            "train_sample_count": len(self.y_train),
            "confusion_matrix": cm,
            "per_class": per_class_metrics,
            "model_type": "DecisionTreeClassifier (scikit-learn)",
            "hyperparameters": {
                "criterion": "gini",
                "max_depth": 5,
                "min_samples_leaf": 4,
                "random_state": self.seed
            }
        }
        self._is_trained = True

    def predict(self, temperature: float, humidity: float, time_of_day_str: str) -> Dict[str, Any]:
        """
        Executes inference for user-specified ambient conditions.
        Returns predicted speed, confidence, probabilities, and an objective comfort explanation.
        """
        if not self._is_trained:
            self.train_and_evaluate()

        time_code = TIME_OF_DAY_ENCODING.get(time_of_day_str, 0)
        feature_vector = np.array([[temperature, humidity, time_code]])

        # Execute scikit-learn prediction
        pred_level = int(self.model.predict(feature_vector)[0])
        probabilities = self.model.predict_proba(feature_vector)[0]

        # Extract class probabilities for all 5 levels
        classes = self.model.classes_
        prob_dict = {f"Level {c}": round(float(probabilities[idx]) * 100, 1) for idx, c in enumerate(classes)}

        # Formulate objective explanation
        explanation = self._generate_explanation(temperature, humidity, time_of_day_str, pred_level)

        return {
            "speed": pred_level,
            "speed_info": FAN_SPEED_LEVELS.get(pred_level, {}),
            "probabilities": prob_dict,
            "explanation": explanation,
            "inputs": {
                "temperature": temperature,
                "humidity": humidity,
                "time_of_day": time_of_day_str
            }
        }

    def _generate_explanation(
        self,
        temperature: float,
        humidity: float,
        time_of_day: str,
        speed: int
    ) -> str:
        """
        Constructs an objective physical explanation for the recommendation
        without claiming direct sensory access to human feelings.
        """
        time_lower = time_of_day.lower()

        # Categorize temperature regime
        if temperature < 20.0:
            temp_desc = "cool ambient conditions"
        elif temperature < 26.0:
            temp_desc = "moderate room temperature"
        elif temperature < 32.0:
            temp_desc = "warm conditions"
        else:
            temp_desc = "elevated thermal stress"

        # Categorize humidity regime
        if humidity < 40.0:
            hum_desc = "low humidity promoting rapid natural evaporation"
        elif humidity < 65.0:
            hum_desc = "moderate humidity"
        else:
            hum_desc = "high moisture restricting cutaneous evaporative cooling"

        # Time of day physical context
        if time_lower == "night":
            circadian_note = "During the night, resting metabolic rates are lower and quieter air movement is typically suitable."
        elif time_lower == "afternoon":
            circadian_note = "In the afternoon, active indoor occupancy and radiant heat increase the need for ventilation."
        else:
            circadian_note = f"Under {time_lower} conditions, steady air circulation maintains indoor air balance."

        speed_intent = FAN_SPEED_LEVELS[speed]["description"]

        return (
            f"Based on {temperature:.1f}°C ({temp_desc}) and {humidity:.1f}% relative humidity ({hum_desc}), "
            f"the synthetic comfort model recommends {FAN_SPEED_LEVELS[speed]['name']}. "
            f"{speed_intent} {circadian_note} "
            f"(Note: This recommendation is derived from a synthetic thermal index model, not direct biological sensing.)"
        )


# Global singleton instance for clean reuse across Flask requests
model_manager = AirWiseModelManager()
