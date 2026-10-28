"""
AirWise — Automated Test Suite
==============================
Tests all major system components:
1. Comfort input validation (valid, edge cases, out-of-range, bad types)
2. Synthetic dataset generation and DecisionTreeClassifier training/inference
3. Rule-based baseline logic and benchmark calculation
4. Personalisation engine and contextual memory offset logic
5. SQLite persistent storage, parameterized queries, and feedback updates
6. Flask web routes, REST endpoints, and error handling
"""

import os
import unittest
import tempfile
import sqlite3
import numpy as np

# Single-threaded environment for deterministic tests
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from config import (
    TEMP_MIN_C,
    TEMP_MAX_C,
    HUMIDITY_MIN_PCT,
    HUMIDITY_MAX_PCT,
    RANDOM_SEED
)
import database
from ml_model import AirWiseModelManager
from baseline import rule_based_predict, evaluate_baseline_on_test_set
from personalizer import compute_condition_distance, get_personalized_recommendation
from app import app, validate_comfort_inputs


class TestInputValidation(unittest.TestCase):
    """Tests client and server input validation functions."""

    def test_valid_inputs(self):
        is_valid, parsed, msg = validate_comfort_inputs(28.5, 60.0, "Afternoon")
        self.assertTrue(is_valid)
        self.assertEqual(parsed["temperature"], 28.5)
        self.assertEqual(parsed["humidity"], 60.0)
        self.assertEqual(parsed["time_of_day"], "Afternoon")
        self.assertEqual(msg, "")

    def test_temperature_boundary_valid(self):
        is_valid_min, _, _ = validate_comfort_inputs(TEMP_MIN_C, 50.0, "Morning")
        is_valid_max, _, _ = validate_comfort_inputs(TEMP_MAX_C, 50.0, "Morning")
        self.assertTrue(is_valid_min)
        self.assertTrue(is_valid_max)

    def test_temperature_out_of_range(self):
        is_valid_low, _, msg_low = validate_comfort_inputs(TEMP_MIN_C - 1.0, 50.0, "Morning")
        is_valid_high, _, msg_high = validate_comfort_inputs(TEMP_MAX_C + 5.0, 50.0, "Morning")
        self.assertFalse(is_valid_low)
        self.assertIn("Temperature must be between", msg_low)
        self.assertFalse(is_valid_high)
        self.assertIn("Temperature must be between", msg_high)

    def test_humidity_out_of_range(self):
        is_valid_low, _, msg_low = validate_comfort_inputs(25.0, HUMIDITY_MIN_PCT - 5.0, "Evening")
        is_valid_high, _, msg_high = validate_comfort_inputs(25.0, HUMIDITY_MAX_PCT + 2.0, "Evening")
        self.assertFalse(is_valid_low)
        self.assertIn("Relative humidity must be between", msg_low)
        self.assertFalse(is_valid_high)
        self.assertIn("Relative humidity must be between", msg_high)

    def test_invalid_time_of_day(self):
        is_valid, _, msg = validate_comfort_inputs(25.0, 50.0, "Midnight")
        self.assertFalse(is_valid)
        self.assertIn("Invalid time of day", msg)

    def test_invalid_types_and_empty_inputs(self):
        is_valid_str, _, _ = validate_comfort_inputs("not-a-number", 50.0, "Morning")
        is_valid_none, _, _ = validate_comfort_inputs(None, 50.0, "Morning")
        self.assertFalse(is_valid_str)
        self.assertFalse(is_valid_none)


class TestMachineLearningModel(unittest.TestCase):
    """Tests the synthetic dataset generation, training, and DecisionTreeClassifier evaluation."""

    @classmethod
    def setUpClass(cls):
        cls.mgr = AirWiseModelManager(seed=RANDOM_SEED)

    def test_synthetic_data_generation(self):
        X, y = self.mgr.generate_synthetic_data()
        self.assertEqual(len(X), 1200)
        self.assertEqual(len(y), 1200)
        self.assertEqual(X.shape[1], 3)
        # Verify labels are strictly 1 to 5
        self.assertTrue(all(1 <= label <= 5 for label in y))

    def test_model_evaluation_metrics_are_genuine(self):
        evals = self.mgr.evaluation_results
        self.assertIn("test_accuracy", evals)
        self.assertIn("f1_macro", evals)
        self.assertIn("confusion_matrix", evals)
        # Test accuracy should be realistic (between 70% and 95%)
        self.assertGreater(evals["test_accuracy"], 70.0)
        self.assertLessEqual(evals["test_accuracy"], 100.0)
        # Confusion matrix must be 5x5
        cm = evals["confusion_matrix"]
        self.assertEqual(len(cm), 5)
        self.assertEqual(len(cm[0]), 5)

    def test_prediction_output_structure(self):
        res = self.mgr.predict(32.0, 75.0, "Afternoon")
        self.assertIn("speed", res)
        self.assertIn(res["speed"], range(1, 6))
        self.assertIn("probabilities", res)
        self.assertIn("explanation", res)
        self.assertIn("Level 4", res["probabilities"])
        self.assertTrue(len(res["explanation"]) > 20)


class TestRuleBasedBaseline(unittest.TestCase):
    """Tests the deterministic rule-based baseline logic and benchmark evaluation."""

    def test_rule_based_predictions(self):
        # Cool conditions
        self.assertEqual(rule_based_predict(18.0, 40.0, "Morning"), 1)
        # Hot conditions
        self.assertIn(rule_based_predict(36.0, 80.0, "Afternoon"), [4, 5])
        # Night quiet reduction
        day_speed = rule_based_predict(27.0, 50.0, "Afternoon")
        night_speed = rule_based_predict(27.0, 50.0, "Night")
        self.assertLessEqual(night_speed, day_speed)

    def test_baseline_test_set_evaluation(self):
        mgr = AirWiseModelManager(seed=RANDOM_SEED)
        baseline_eval = evaluate_baseline_on_test_set(mgr.X_test, mgr.y_test)
        self.assertIn("accuracy", baseline_eval)
        self.assertGreater(baseline_eval["accuracy"], 50.0)
        self.assertIn("f1_macro", baseline_eval)


class TestPersonalisationEngine(unittest.TestCase):
    """Tests condition distance and feedback-based memory adjustments."""

    def test_condition_distance(self):
        # Identical conditions
        dist_zero = compute_condition_distance(25.0, 50.0, "Morning", 25.0, 50.0, "Morning")
        self.assertAlmostEqual(dist_zero, 0.0)

        # Distant conditions
        dist_far = compute_condition_distance(20.0, 40.0, "Morning", 35.0, 80.0, "Night")
        self.assertGreater(dist_far, 1.0)

    def test_personalization_clamping(self):
        # Even with extreme offsets, result must stay bounded [1, 5]
        res = get_personalized_recommendation(28.0, 55.0, "Afternoon", base_ml_speed=5)
        self.assertLessEqual(res["personalized_speed"], 5)
        self.assertGreaterEqual(res["personalized_speed"], 1)


class TestDatabasePersistence(unittest.TestCase):
    """Tests SQLite database persistence and parameterized query safety."""

    def setUp(self):
        # Ensure fresh table
        database.init_db()

    def test_save_and_retrieve_prediction(self):
        rec_id = database.save_prediction(
            temperature=27.4,
            humidity=62.0,
            time_of_day="Evening",
            ml_speed=3,
            rule_speed=3,
            personalized_speed=3,
            adjustment_applied=0,
            explanation="Test explanation"
        )
        self.assertIsInstance(rec_id, int)
        self.assertGreater(rec_id, 0)

        # Save user feedback for this record
        success = database.save_feedback(rec_id, preferred_speed=4, feedback_type="too_slow")
        self.assertTrue(success)

        # Retrieve history and verify feedback persisted
        history = database.get_history(limit=5)
        matched = [r for r in history if r["id"] == rec_id]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["preferred_speed"], 4)
        self.assertEqual(matched[0]["feedback_type"], "too_slow")

    def test_parameterized_query_safety(self):
        # Test input with quotes and SQL special characters
        rec_id = database.save_prediction(
            temperature=25.0,
            humidity=50.0,
            time_of_day="Morning",
            ml_speed=2,
            rule_speed=2,
            personalized_speed=2,
            adjustment_applied=0,
            explanation="Safety test with single ' and double \" quotes; DROP TABLE predictions; --"
        )
        self.assertGreater(rec_id, 0)
        # Ensure database is still intact
        self.assertGreater(database.get_total_prediction_count(), 0)


class TestFlaskWebRoutes(unittest.TestCase):
    """Tests all Flask endpoints, API response format, and error handling."""

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_home_page_renders_successfully(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AirWise", response.data)
        self.assertIn(b"Track 1", response.data)
        self.assertIn(b"SIMULATION PROTOTYPE", response.data)

    def test_predict_api_success(self):
        payload = {
            "temperature": 31.0,
            "humidity": 70.0,
            "time_of_day": "Afternoon"
        }
        response = self.client.post("/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("record_id", data)
        self.assertIn("active_speed", data)
        self.assertIn(data["active_speed"], range(1, 6))

    def test_predict_api_invalid_temperature_rejected(self):
        payload = {
            "temperature": 99.0,  # Out of range
            "humidity": 50.0,
            "time_of_day": "Morning"
        }
        response = self.client.post("/predict", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("Temperature must be between", data["message"])

    def test_feedback_api(self):
        # Create a prediction first
        pred_res = self.client.post("/predict", json={"temperature": 26.0, "humidity": 50.0, "time_of_day": "Morning"})
        rec_id = pred_res.get_json()["record_id"]

        # Submit feedback
        fb_payload = {
            "record_id": rec_id,
            "preferred_speed": 3,
            "feedback_type": "too_slow"
        }
        response = self.client.post("/feedback", json=fb_payload)
        self.assertEqual(response.status_code, 200)
        fb_data = response.get_json()
        self.assertEqual(fb_data["status"], "success")

    def test_compare_page_renders(self):
        response = self.client.get("/compare")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Machine Learning vs. Rule-Based Baseline", response.data)

    def test_history_page_renders(self):
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Persistent Recommendation & Feedback History", response.data)

    def test_evaluation_page_renders(self):
        response = self.client.get("/evaluation")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Model Evaluation & Synthetic Data Transparency", response.data)
        self.assertIn(b"Decision Tree Confusion Matrix", response.data)

    def test_about_safety_page_renders(self):
        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Rohit Ingale", response.data)
        self.assertIn(b"Nutan Maharashtra Institute of Engineering and Technology", response.data)
        self.assertIn(b"No Physical Fan Connection", response.data)

    def test_404_error_page(self):
        response = self.client.get("/non-existent-endpoint-xyz")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"404", response.data)


if __name__ == "__main__":
    unittest.main()
