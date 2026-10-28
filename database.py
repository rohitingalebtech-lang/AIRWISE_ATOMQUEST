"""
AirWise - SQLite Database Management
====================================
Handles persistent storage for recommendations, user feedback, and personalisation history.
Strictly uses parameterised queries to prevent SQL injection vulnerabilities.
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import (
    DATABASE_PATH,
    SIMILARITY_TEMP_THRESHOLD,
    SIMILARITY_HUMIDITY_THRESHOLD,
    MAX_FEEDBACK_CONSIDERED
)


import os


def get_db_connection():
    """Establishes and returns a connection to the SQLite database with Row mapping."""
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enables column access by name (dict-like)
    return conn


def init_db():
    """Initialises the database tables and indexes if they do not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Enable WAL mode for concurrent multi-worker reads/writes
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass

    # Create table for predictions and feedback history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            time_of_day TEXT NOT NULL,
            ml_speed INTEGER NOT NULL,
            rule_speed INTEGER NOT NULL,
            personalized_speed INTEGER NOT NULL,
            adjustment_applied INTEGER NOT NULL DEFAULT 0,
            explanation TEXT NOT NULL,
            preferred_speed INTEGER DEFAULT NULL,
            feedback_type TEXT DEFAULT NULL,
            feedback_timestamp TEXT DEFAULT NULL
        );
    """)

    # Create indexes for fast lookup during personalisation and history filtering
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_predictions_timestamp 
        ON predictions(timestamp DESC);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_predictions_conditions 
        ON predictions(temperature, humidity, time_of_day);
    """)

    conn.commit()
    conn.close()


def save_prediction(
    temperature: float,
    humidity: float,
    time_of_day: str,
    ml_speed: int,
    rule_speed: int,
    personalized_speed: int,
    adjustment_applied: int,
    explanation: str
) -> int:
    """
    Saves a new recommendation record to the database.
    Returns the newly created record ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO predictions (
            timestamp,
            temperature,
            humidity,
            time_of_day,
            ml_speed,
            rule_speed,
            personalized_speed,
            adjustment_applied,
            explanation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        now_str,
        float(temperature),
        float(humidity),
        str(time_of_day),
        int(ml_speed),
        int(rule_speed),
        int(personalized_speed),
        int(adjustment_applied),
        str(explanation)
    ))

    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def save_feedback(
    record_id: int,
    preferred_speed: int,
    feedback_type: str
) -> bool:
    """
    Attaches user comfort feedback to an existing recommendation record.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE predictions
        SET preferred_speed = ?,
            feedback_type = ?,
            feedback_timestamp = ?
        WHERE id = ?;
    """, (
        int(preferred_speed),
        str(feedback_type),
        now_str,
        int(record_id)
    ))

    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0


def get_history(limit: int = 50, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the history of recommendations and feedback.
    Optionally filters by feedback status ('all', 'feedback_only', 'no_feedback').
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if filter_type == "feedback_only":
        cursor.execute("""
            SELECT * FROM predictions
            WHERE feedback_type IS NOT NULL
            ORDER BY id DESC
            LIMIT ?;
        """, (limit,))
    elif filter_type == "no_feedback":
        cursor.execute("""
            SELECT * FROM predictions
            WHERE feedback_type IS NULL
            ORDER BY id DESC
            LIMIT ?;
        """, (limit,))
    else:
        cursor.execute("""
            SELECT * FROM predictions
            ORDER BY id DESC
            LIMIT ?;
        """, (limit,))

    rows = cursor.fetchall()
    history = [dict(row) for row in rows]
    conn.close()
    return history


def get_feedback_count() -> int:
    """Counts the total number of feedback records stored."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM predictions
        WHERE feedback_type IS NOT NULL;
    """)
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_total_prediction_count() -> int:
    """Counts total predictions logged."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM predictions;")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_relevant_feedback(
    temperature: float,
    humidity: float,
    time_of_day: str
) -> List[Dict[str, Any]]:
    """
    Finds past user feedback under similar environmental conditions.
    Used by the Personalisation Engine to adjust future recommendations.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query records with valid feedback within the temperature and humidity bounds
    cursor.execute("""
        SELECT id, temperature, humidity, time_of_day, ml_speed,
               personalized_speed, preferred_speed, feedback_type, feedback_timestamp
        FROM predictions
        WHERE feedback_type IS NOT NULL
          AND preferred_speed IS NOT NULL
          AND temperature BETWEEN ? AND ?
          AND humidity BETWEEN ? AND ?
        ORDER BY id DESC
        LIMIT ?;
    """, (
        temperature - SIMILARITY_TEMP_THRESHOLD,
        temperature + SIMILARITY_TEMP_THRESHOLD,
        humidity - SIMILARITY_HUMIDITY_THRESHOLD,
        humidity + SIMILARITY_HUMIDITY_THRESHOLD,
        MAX_FEEDBACK_CONSIDERED
    ))

    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def clear_history() -> bool:
    """Clears all prediction and feedback records (useful for test resets)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions;")
    conn.commit()
    conn.close()
    return True
