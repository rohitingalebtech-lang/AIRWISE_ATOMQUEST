"""
AirWise - Personalisation and Feedback Learning Engine
======================================================
Implements a transparent, instance-based memory adjustment mechanism that personalises
future recommendations based on saved user comfort feedback for similar environmental conditions.

IMPORTANT ARCHITECTURAL NOTE:
This engine uses feedback-based memory adjustment rather than in-place retraining of the Decision Tree.
In embedded/edge fan controllers, instance-based personalization avoids catastrophic forgetting,
maintains baseline safety boundaries, and allows immediate adaptation to individual user preferences
without requiring heavy model retraining runs.
"""

from typing import Dict, Any, List, Tuple
import math
from config import (
    SIMILARITY_TEMP_THRESHOLD,
    SIMILARITY_HUMIDITY_THRESHOLD,
    FAN_SPEED_LEVELS
)
from database import get_relevant_feedback


def compute_condition_distance(
    temp1: float, hum1: float, time1: str,
    temp2: float, hum2: float, time2: str
) -> float:
    """
    Computes normalized Euclidean distance between two environmental condition states.
    Includes a penalty for differing times of day.
    """
    norm_temp_diff = (temp1 - temp2) / SIMILARITY_TEMP_THRESHOLD
    norm_hum_diff = (hum1 - hum2) / SIMILARITY_HUMIDITY_THRESHOLD

    # Time-of-day discrepancy penalty
    time_penalty = 0.0 if time1.lower() == time2.lower() else 0.75

    return math.sqrt(norm_temp_diff**2 + norm_hum_diff**2 + time_penalty**2)


def get_personalized_recommendation(
    temperature: float,
    humidity: float,
    time_of_day: str,
    base_ml_speed: int
) -> Dict[str, Any]:
    """
    Evaluates whether past user feedback under similar conditions should adjust
    the baseline Machine Learning recommendation.

    Returns:
    - personalized_speed: Final recommended speed (1 to 5)
    - adjustment: Integer delta applied to base ML speed (-2 to +2)
    - has_personalization: Boolean indicating if adjustment occurred
    - similar_records: Details of historical feedback records considered
    - explanation: Clear, transparent explanation of the adjustment rationale
    """
    # Query database for recent feedback under similar temperature & humidity
    records = get_relevant_feedback(temperature, humidity, time_of_day)

    if not records:
        return {
            "personalized_speed": base_ml_speed,
            "adjustment": 0,
            "has_personalization": False,
            "matched_count": 0,
            "similar_records": [],
            "explanation": (
                "Standard ML baseline applied. No matching feedback records found "
                f"within ±{SIMILARITY_TEMP_THRESHOLD}°C and ±{SIMILARITY_HUMIDITY_THRESHOLD}% humidity."
            ),
            "mechanism": "Pure Decision Tree Inference (No feedback offset)"
        }

    # Weight feedback by proximity in environmental space
    total_weight = 0.0
    weighted_offset_sum = 0.0
    matching_details = []

    for rec in records:
        dist = compute_condition_distance(
            temperature, humidity, time_of_day,
            rec["temperature"], rec["humidity"], rec["time_of_day"]
        )

        weight = 1.0 / (1.0 + dist)
        total_weight += weight

        # Compute desired user offset from the original ML speed
        rec_ml_speed = rec["ml_speed"]
        preferred_speed = rec["preferred_speed"]
        offset = preferred_speed - rec_ml_speed

        # If user marked 'Too fast' but didn't change speed, ensure negative offset
        if rec["feedback_type"] == "too_fast" and offset == 0:
            offset = -1
        elif rec["feedback_type"] == "too_slow" and offset == 0:
            offset = 1
        elif rec["feedback_type"] == "comfortable":
            offset = 0

        weighted_offset_sum += weight * offset

        matching_details.append({
            "id": rec["id"],
            "temperature": rec["temperature"],
            "humidity": rec["humidity"],
            "time_of_day": rec["time_of_day"],
            "feedback_type": rec["feedback_type"],
            "preferred_speed": preferred_speed,
            "distance": round(dist, 2),
            "weight": round(weight, 2)
        })

    # Average offset weighted by environmental similarity
    avg_offset = weighted_offset_sum / total_weight if total_weight > 0 else 0.0

    # Round to nearest discrete integer speed level adjustment
    adjustment = int(round(avg_offset))

    # Clamp adjustment within [-2, +2] to avoid extreme runaway shifts
    adjustment = max(-2, min(2, adjustment))

    # Apply adjustment to baseline ML speed and clamp strictly to 1..5
    raw_personalized = base_ml_speed + adjustment
    final_speed = int(max(1, min(5, raw_personalized)))

    # Re-calculate effective adjustment after boundary clamping
    effective_adjustment = final_speed - base_ml_speed

    # Generate transparent explanation
    if effective_adjustment != 0:
        direction = "increased" if effective_adjustment > 0 else "decreased"
        sign_str = f"+{effective_adjustment}" if effective_adjustment > 0 else f"{effective_adjustment}"
        explanation = (
            f"Personalisation Active: Based on {len(records)} previous feedback record(s) under "
            f"similar ambient conditions (avg distance: {sum(r['distance'] for r in matching_details)/len(matching_details):.2f}), "
            f"the recommendation was {direction} by {sign_str} level(s) (from Level {base_ml_speed} to Level {final_speed}) "
            f"to reflect your recorded comfort preference."
        )
    else:
        explanation = (
            f"Personalisation Checked: Found {len(records)} previous feedback record(s) under similar conditions. "
            f"Your past preferences align with the ML recommendation (Level {base_ml_speed}), so no offset was applied."
        )

    return {
        "personalized_speed": final_speed,
        "adjustment": effective_adjustment,
        "has_personalization": effective_adjustment != 0,
        "matched_count": len(records),
        "similar_records": matching_details,
        "explanation": explanation,
        "mechanism": "Contextual Instance-Based Personalisation (Memory Offset)"
    }
