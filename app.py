"""
AirWise — Flask Web Application
================================
Project: AirWise — A Personalised Comfort Learning System for Fans
Team: Rohit Ingale, Sarthak Avhad, Gargi Rane, Hitesh Yuvare
College: Nutan Maharashtra Institute of Engineering and Technology (NMIET), Pune
Track: Track 1 — Fan (AtomQUEST 2026 Round 2)

Main entry point providing web routes, RESTful APIs, strict validation, and rendering.
"""

import os
# Ensure deterministic single-threaded execution for scikit-learn on Windows
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from typing import Dict, Any, Tuple

from config import (
    TEMP_MIN_C,
    TEMP_MAX_C,
    HUMIDITY_MIN_PCT,
    HUMIDITY_MAX_PCT,
    TIME_OF_DAY_CATEGORIES,
    FAN_SPEED_LEVELS
)
from database import (
    init_db,
    save_prediction,
    save_feedback,
    get_history,
    get_feedback_count,
    get_total_prediction_count,
    clear_history
)
from ml_model import model_manager
from baseline import rule_based_predict_details, evaluate_baseline_on_test_set
from personalizer import get_personalized_recommendation

# Initialize Flask application
app = Flask(__name__)
# Use environment secret key if provided, otherwise generate random bytes (safe, no hardcoded secrets)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# Ensure database is initialised on startup
init_db()


def validate_comfort_inputs(
    temp_raw: Any,
    hum_raw: Any,
    time_raw: Any
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Validates user comfort input values on the server side.
    Returns: (is_valid, parsed_dict, error_message)
    """
    # 1. Temperature validation
    try:
        if temp_raw is None or str(temp_raw).strip() == "":
            return False, {}, "Room temperature is required."
        temp = float(temp_raw)
        if temp < TEMP_MIN_C or temp > TEMP_MAX_C:
            return False, {}, (
                f"Temperature must be between {TEMP_MIN_C}°C and {TEMP_MAX_C}°C. "
                f"Received: {temp}°C."
            )
    except (ValueError, TypeError):
        return False, {}, "Invalid temperature value. Please provide a numeric decimal."

    # 2. Humidity validation
    try:
        if hum_raw is None or str(hum_raw).strip() == "":
            return False, {}, "Relative humidity is required."
        hum = float(hum_raw)
        if hum < HUMIDITY_MIN_PCT or hum > HUMIDITY_MAX_PCT:
            return False, {}, (
                f"Relative humidity must be between {HUMIDITY_MIN_PCT}% and {HUMIDITY_MAX_PCT}%. "
                f"Received: {hum}%."
            )
    except (ValueError, TypeError):
        return False, {}, "Invalid humidity value. Please provide a numeric decimal."

    # 3. Time of Day validation
    if not time_raw or str(time_raw).strip() not in TIME_OF_DAY_CATEGORIES:
        valid_options = ", ".join(TIME_OF_DAY_CATEGORIES)
        return False, {}, (
            f"Invalid time of day '{time_raw}'. Valid choices are: {valid_options}."
        )

    parsed = {
        "temperature": round(temp, 1),
        "humidity": round(hum, 1),
        "time_of_day": str(time_raw).strip()
    }
    return True, parsed, ""


@app.context_processor
def inject_global_metadata():
    """Injects project metadata and metrics into all Jinja2 templates."""
    return {
        "project_name": "AirWise",
        "project_tagline": "A Personalised Comfort Learning System for Fans",
        "team_members": ["Rohit Ingale", "Sarthak Avhad", "Gargi Rane", "Hitesh Yuvare"],
        "college_name": "Nutan Maharashtra Institute of Engineering and Technology (NMIET), Pune",
        "track_name": "Track 1 — Fan (AtomQUEST 2026)",
        "fan_levels": FAN_SPEED_LEVELS,
        "temp_min": TEMP_MIN_C,
        "temp_max": TEMP_MAX_C,
        "hum_min": HUMIDITY_MIN_PCT,
        "hum_max": HUMIDITY_MAX_PCT,
        "time_categories": TIME_OF_DAY_CATEGORIES,
        "total_feedback_count": get_feedback_count()
    }


@app.route("/")
def index():
    """
    FEATURE 1 & 2: Professional Engineering Dashboard.
    Displays inputs form, fan speed recommendation, feedback widget, and statistics.
    """
    feedback_count = get_feedback_count()
    total_preds = get_total_prediction_count()

    # Default initial state for interactive dashboard demonstration
    default_inputs = {
        "temperature": 28.5,
        "humidity": 65.0,
        "time_of_day": "Afternoon"
    }

    # Generate initial sample prediction for immediate visual feedback
    ml_res = model_manager.predict(
        default_inputs["temperature"],
        default_inputs["humidity"],
        default_inputs["time_of_day"]
    )
    rule_res = rule_based_predict_details(
        default_inputs["temperature"],
        default_inputs["humidity"],
        default_inputs["time_of_day"]
    )
    pers_res = get_personalized_recommendation(
        default_inputs["temperature"],
        default_inputs["humidity"],
        default_inputs["time_of_day"],
        ml_res["speed"]
    )

    initial_state = {
        "inputs": default_inputs,
        "ml": ml_res,
        "rule": rule_res,
        "personalization": pers_res,
        "active_speed": pers_res["personalized_speed"],
        "active_speed_info": FAN_SPEED_LEVELS[pers_res["personalized_speed"]],
        "record_id": None  # Will be created upon explicit user submission
    }

    return render_template(
        "index.html",
        initial_state=initial_state,
        feedback_count=feedback_count,
        total_predictions=total_preds
    )


@app.route("/predict", methods=["POST"])
def predict():
    """
    Processes comfort inputs, executes ML prediction, rule-based baseline,
    and personalization engine, storing the record in SQLite.
    Supports both JSON API and HTML Form submissions.
    """
    is_json = request.is_json
    data = request.get_json() if is_json else request.form

    temp_raw = data.get("temperature")
    hum_raw = data.get("humidity")
    time_raw = data.get("time_of_day")

    is_valid, parsed, error_msg = validate_comfort_inputs(temp_raw, hum_raw, time_raw)

    if not is_valid:
        if is_json:
            return jsonify({"status": "error", "message": error_msg}), 400
        flash(error_msg, "error")
        return redirect(url_for("index"))

    temperature = parsed["temperature"]
    humidity = parsed["humidity"]
    time_of_day = parsed["time_of_day"]

    # 1. Decision Tree ML Prediction
    ml_result = model_manager.predict(temperature, humidity, time_of_day)
    ml_speed = ml_result["speed"]

    # 2. Rule-Based Baseline Prediction
    rule_result = rule_based_predict_details(temperature, humidity, time_of_day)
    rule_speed = rule_result["speed"]

    # 3. Personalisation Logic (Contextual Memory Offset)
    pers_result = get_personalized_recommendation(
        temperature, humidity, time_of_day, ml_speed
    )
    personalized_speed = pers_result["personalized_speed"]
    adjustment_applied = pers_result["adjustment"]

    # 4. Save Prediction Record into SQLite
    record_id = save_prediction(
        temperature=temperature,
        humidity=humidity,
        time_of_day=time_of_day,
        ml_speed=ml_speed,
        rule_speed=rule_speed,
        personalized_speed=personalized_speed,
        adjustment_applied=adjustment_applied,
        explanation=ml_result["explanation"]
    )

    response_data = {
        "status": "success",
        "record_id": record_id,
        "inputs": parsed,
        "ml": ml_result,
        "rule": rule_result,
        "personalization": pers_result,
        "active_speed": personalized_speed,
        "active_speed_info": FAN_SPEED_LEVELS[personalized_speed],
        "feedback_count": get_feedback_count()
    }

    if is_json:
        return jsonify(response_data)

    return render_template(
        "index.html",
        initial_state=response_data,
        feedback_count=get_feedback_count(),
        total_predictions=get_total_prediction_count()
    )


@app.route("/feedback", methods=["POST"])
def submit_feedback():
    """
    FEATURE 5: Attaches user comfort feedback to a prediction record.
    Accepts preferred fan speed (1 to 5) and feedback category (too_slow, comfortable, too_fast).
    """
    data = request.get_json() if request.is_json else request.form

    record_id = data.get("record_id")
    preferred_speed = data.get("preferred_speed")
    feedback_type = data.get("feedback_type")

    # Validate Record ID
    try:
        record_id = int(record_id)
        if record_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid or missing recommendation record ID."}), 400

    # Validate Preferred Speed
    try:
        preferred_speed = int(preferred_speed)
        if preferred_speed not in range(1, 6):
            return jsonify({"status": "error", "message": "Preferred speed must be an integer between 1 and 5."}), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid preferred speed level."}), 400

    # Validate Feedback Category
    valid_feedback_types = ["too_slow", "comfortable", "too_fast"]
    if feedback_type not in valid_feedback_types:
        return jsonify({
            "status": "error",
            "message": f"Invalid feedback category '{feedback_type}'. Choose from: {', '.join(valid_feedback_types)}."
        }), 400

    # Persist in SQLite
    success = save_feedback(record_id, preferred_speed, feedback_type)

    if not success:
        return jsonify({
            "status": "error",
            "message": f"Record #{record_id} could not be updated or was not found."
        }), 404

    return jsonify({
        "status": "success",
        "message": f"Feedback saved! Preferred Level {preferred_speed} ({feedback_type.replace('_', ' ').title()}) recorded.",
        "record_id": record_id,
        "new_feedback_count": get_feedback_count()
    })


@app.route("/compare")
def compare():
    """
    FEATURE 4: Side-by-side comparison page between the Machine Learning Decision Tree
    and the Rule-Based Baseline.
    """
    # Evaluate baseline against the held-out test set
    baseline_eval = evaluate_baseline_on_test_set(
        model_manager.X_test,
        model_manager.y_test
    )
    ml_eval = model_manager.evaluation_results

    return render_template(
        "compare.html",
        ml_eval=ml_eval,
        baseline_eval=baseline_eval
    )


@app.route("/history")
def history():
    """
    FEATURE 6: Displays persistent recommendation and feedback history.
    """
    filter_type = request.args.get("filter", "all")
    records = get_history(limit=100, filter_type=filter_type)
    return render_template(
        "history.html",
        records=records,
        filter_type=filter_type,
        total_count=len(records)
    )


@app.route("/history/clear", methods=["POST"])
def clear_all_history():
    """Allows resetting the history for fresh competition demonstrations."""
    clear_history()
    flash("History records have been cleared successfully.", "success")
    return redirect(url_for("history"))


@app.route("/evaluation")
def evaluation():
    """
    FEATURE 7: Dedicated Model Evaluation and Synthetic Data Transparency page.
    Displays genuine held-out test metrics, confusion matrix, and class distributions.
    """
    ml_eval = model_manager.evaluation_results
    dataset_summary = model_manager.dataset_summary
    baseline_eval = evaluate_baseline_on_test_set(
        model_manager.X_test,
        model_manager.y_test
    )

    return render_template(
        "evaluation.html",
        ml_eval=ml_eval,
        baseline_eval=baseline_eval,
        dataset_summary=dataset_summary
    )


@app.route("/about")
def about():
    """
    FEATURE 8 & TEAM: Project overview, college information, team roster,
    and crucial hardware safety and simulation limitations notice.
    """
    return render_template("about.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html", error=str(error)), 500


if __name__ == "__main__":
    # Read port and host from environment variables (standard for Render and local environments)
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    # Keep debug mode disabled by default in production
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ["true", "1", "t"]

    print("==================================================================")
    print("AirWise — A Personalised Comfort Learning System for Fans")
    print("Track 1 — Fan | AtomQUEST 2026 Round 2")
    print("Team: Rohit Ingale, Sarthak Avhad, Gargi Rane, Hitesh Yuvare")
    print("Nutan Maharashtra Institute of Engineering and Technology (NMIET)")
    print(f"Server starting on {host}:{port} (Debug: {debug_mode})")
    print("==================================================================")
    app.run(host=host, port=port, debug=debug_mode)
