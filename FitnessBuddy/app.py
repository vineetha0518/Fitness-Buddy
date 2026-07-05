"""
FitnessBuddy — Flask Application Entry Point
=============================================
Production-ready Flask app with modular route structure,
session-based progress tracking, and IBM Watsonx.ai integration.
"""
import os
import json
import logging
from datetime import datetime, date

from flask import (
    Flask, render_template, request, jsonify, session
)
from flask_cors import CORS
from dotenv import load_dotenv

# ── Load environment variables before anything else ───────────────────────────
load_dotenv()

# ── Service & utility imports ──────────────────────────────────────────────────
from services import fitness_agent
from services.granite_client import is_configured
from utils.bmi import calculate_bmi, calculate_ideal_weight
from utils.calorie import calculate_tdee, ACTIVITY_LEVELS, GOAL_ADJUSTMENTS
from utils.workout import get_workout_plan, get_warmup, get_cooldown

# ── App factory ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-fallback-change-in-prod")
CORS(app)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Load static datasets once ──────────────────────────────────────────────────
_BASE = os.path.dirname(__file__)

with open(os.path.join(_BASE, "data", "indian_meals.json"), encoding="utf-8") as _f:
    MEALS_DB: dict = json.load(_f)

with open(os.path.join(_BASE, "data", "workouts.json"), encoding="utf-8") as _f:
    WORKOUTS_DB: dict = json.load(_f)


# ════════════════════════════════════════════════════════════════════════════════
#  Helper — session initialisation
# ════════════════════════════════════════════════════════════════════════════════

def _init_session():
    """Ensure all required session keys exist with sensible defaults."""
    defaults = {
        "profile": {
            "name": "Fitness Enthusiast",
            "age": 25,
            "gender": "not specified",
            "weight_kg": 70,
            "height_cm": 170,
            "fitness_level": "beginner",
            "goal": "general fitness",
            "diet": "vegetarian",
            "available_time_min": 30,
            "equipment": "none",
        },
        "chat_history":      [],
        "workout_log":       [],
        "calorie_log":       [],
        "streak":            0,
        "total_workouts":    0,
        "last_workout_date": None,
        "achievements":      [],
        "target_calories":   2000,
        "daily_tip_shown":   None,
    }
    for key, value in defaults.items():
        session.setdefault(key, value)


def _update_streak():
    """Update daily workout streak based on last workout date."""
    today_str = str(date.today())
    last = session.get("last_workout_date")

    if last is None:
        session["streak"] = 1
    elif last == today_str:
        pass   # Already counted today
    else:
        last_date = date.fromisoformat(last)
        delta = (date.today() - last_date).days
        if delta == 1:
            session["streak"] = session.get("streak", 0) + 1
        elif delta > 1:
            session["streak"] = 1    # Streak broken

    session["last_workout_date"] = today_str


def _check_achievements(session_data: dict) -> list[str]:
    """Return list of newly earned achievement labels."""
    new = []
    total = session_data.get("total_workouts", 0)
    streak = session_data.get("streak", 0)

    milestones = {
        1:   "🎉 First Workout Complete!",
        5:   "💪 5 Workouts Done — You're Building a Habit!",
        10:  "🔥 10 Workouts — On Fire!",
        25:  "🏅 25 Workouts — Dedicated Athlete!",
        50:  "🏆 50 Workouts — Champion Level!",
        100: "🌟 100 Workouts — Legend Status!",
    }
    streak_milestones = {
        3:  "🔥 3-Day Streak!",
        7:  "⚡ 7-Day Streak — One Full Week!",
        14: "💥 14-Day Streak — Two Weeks Strong!",
        30: "🏅 30-Day Streak — Monthly Champion!",
    }

    existing = session_data.get("achievements", [])
    for count, label in milestones.items():
        if total == count and label not in existing:
            new.append(label)
    for count, label in streak_milestones.items():
        if streak == count and label not in existing:
            new.append(label)

    return new


# ════════════════════════════════════════════════════════════════════════════════
#  Routes — Pages
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Landing page / main application."""
    _init_session()
    api_ready = is_configured()
    return render_template(
        "index.html",
        profile=session["profile"],
        streak=session["streak"],
        total_workouts=session["total_workouts"],
        achievements=session["achievements"],
        api_ready=api_ready,
        app_name=os.getenv("APP_NAME", "Fitness Buddy"),
    )


# ════════════════════════════════════════════════════════════════════════════════
#  Routes — Chat API
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Main conversational chat endpoint."""
    _init_session()
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    history = session.get("chat_history", [])
    response = fitness_agent.chat(user_message, history)

    # Append to history (keep last 20 turns)
    history.append({"role": "user",      "content": user_message})
    history.append({"role": "assistant", "content": response})
    session["chat_history"] = history[-20:]

    return jsonify({"response": response, "timestamp": datetime.now().isoformat()})


@app.route("/api/chat/clear", methods=["POST"])
def api_chat_clear():
    """Clear chat history."""
    _init_session()
    session["chat_history"] = []
    return jsonify({"status": "cleared"})


# ════════════════════════════════════════════════════════════════════════════════
#  Routes — Profile
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/api/profile", methods=["GET", "POST"])
def api_profile():
    """Get or update user profile."""
    _init_session()

    if request.method == "GET":
        return jsonify(session["profile"])

    data = request.get_json(silent=True) or {}

    # Sanitise numeric fields
    int_fields   = ["age", "available_time_min"]
    float_fields = ["weight_kg", "height_cm"]

    for field in int_fields:
        if field in data:
            try:
                data[field] = int(data[field])
            except (ValueError, TypeError):
                pass

    for field in float_fields:
        if field in data:
            try:
                data[field] = float(data[field])
            except (ValueError, TypeError):
                pass

    session["profile"].update(data)

    # Recalculate calorie target after profile update
    try:
        p = session["profile"]
        tdee_data = calculate_tdee(
            weight_kg=p["weight_kg"],
            height_cm=p["height_cm"],
            age=p["age"],
            gender=p.get("gender", "male"),
            activity_level="moderate",
            goal=p.get("goal", "maintenance").lower().replace(" ", "_"),
        )
        session["target_calories"] = tdee_data["target_calories"]
    except Exception as exc:
        logger.warning("TDEE recalculation failed: %s", exc)

    return jsonify({"status": "updated", "profile": session["profile"]})


# ════════════════════════════════════════════════════════════════════════════════
#  Routes — BMI Calculator
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/api/bmi", methods=["POST"])
def api_bmi():
    """Calculate BMI from weight and height."""
    data = request.get_json(silent=True) or {}
    try:
        weight_kg = float(data["weight_kg"])
        height_cm = float(data["height_cm"])
        gender    = data.get("gender", "male")

        bmi_result   = calculate_bmi(weight_kg, height_cm)
        ideal_weight = calculate_ideal_weight(height_cm, gender)

        return jsonify({**bmi_result, "ideal_weight": ideal_weight})

    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": f"Invalid input: {exc}"}), 400


# ════════════════════════════════════════════════════════════════════════════════
#  Routes — Calorie Calculator
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/api/calories", methods=["POST"])
def api_calories():
    """Calculate TDEE and macronutrient targets."""
    data = request.get_json(silent=True) or {}
    try:
        result = calculate_tdee(
            weight_kg=float(data["weight_kg"]),
            height_cm=float(data["height_cm"]),
            age=int(data["age"]),
            gender=data.get("gender", "male"),
            activity_level=data.get("activity_level", "moderate"),
            goal=data.get("goal", "maintenance"),
        )
        return jsonify(result)

    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": f"Invalid input: {exc}"}), 400


# ════════════════════════════════════════════════════════════════════════════════
#  Routes — Workout Recommendations
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/api/workout/recommend", methods=["POST"])
def api_workout_recommend():
    """Generate AI-powered workout recommendation."""
    _init_session()
    data = request.get_json(silent=True) or {}

    profile = {**session["profile"], **data}

    # Structured data from utility
    structured = get_workout_plan(
        level=profile.get("fitness_level", "beginner"),
        goal=profile.get("goal", "general fitness"),
        available_time_min=int(profile.get("available_time_min", 30)),
    )

    # AI narrative
    ai_response = fitness_agent.get_workout_recommendation(profile)

    return jsonify({
        "structured_plan": structured,
        "ai_narrative": ai_response,
    })


@app.route("/api/workout/log", methods=["POST"])
def api_workout_log():
    """Log a completed workout session."""
    _init_session()
    data = request.get_json(silent=True) or {}

    log_entry = {
        "date":          str(date.today()),
        "workout_name":  data.get("workout_name", "General Workout"),
        "duration_min":  data.get("duration_min", 30),
        "calories_burned": data.get("calories_burned", 200),
        "exercises":     data.get("exercises", []),
        "notes":         data.get("notes", ""),
        "timestamp":     datetime.now().isoformat(),
    }

    session["workout_log"] = session.get("workout_log", [])
    session["workout_log"].append(log_entry)
    session["total_workouts"] = session.get("total_workouts", 0) + 1

    _update_streak()

    new_achievements = _check_achievements(session)
    session["achievements"] = session.get("achievements", []) + new_achievements

    return jsonify({
        "status":          "logged",
        "streak":          session["streak"],
        "total_workouts":  session["total_workouts"],
        "new_achievements": new_achievements,
    })


@app.route("/api/workout/history", methods=["GET"])
def api_workout_history():
    """Return the last 30 workout log entries."""
    _init_session()
    return jsonify(session.get("workout_log", [])[-30:])


# ════════════════════════════════════════════════════════════════════════════════
#  Routes — Nutrition
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/api/nutrition/meals", methods=["GET"])
def api_meals():
    """Return the Indian meals dataset."""
    category = request.args.get("category", "all")
    if category == "all":
        return jsonify(MEALS_DB)
    return jsonify(MEALS_DB.get(category, []))


@app.route("/api/nutrition/recommend", methods=["POST"])
def api_nutrition_recommend():
    """Generate AI-powered nutrition recommendation."""
    _init_session()
    data = request.get_json(silent=True) or {}

    profile = {
        **session["profile"],
        "target_calories": session.get("target_calories", 2000),
        **data,
    }
    query = data.get("query", "")

    ai_response = fitness_agent.get_nutrition_advice(profile, query)
    return jsonify({"recommendation": ai_response})


@app.route("/api/calorie/log", methods=["POST"])
def api_calorie_log():
    """Log food intake for the day."""
    _init_session()
    data = request.get_json(silent=True) or {}

    entry = {
        "date":     str(date.today()),
        "meal":     data.get("meal", "Unknown Meal"),
        "calories": data.get("calories", 0),
        "protein":  data.get("protein", 0),
        "carbs":    data.get("carbs", 0),
        "fat":      data.get("fat", 0),
        "timestamp": datetime.now().isoformat(),
    }

    session["calorie_log"] = session.get("calorie_log", [])
    session["calorie_log"].append(entry)

    # Calculate today's totals
    today = str(date.today())
    today_entries = [e for e in session["calorie_log"] if e["date"] == today]
    totals = {
        "calories": sum(e["calories"] for e in today_entries),
        "protein":  sum(e["protein"]  for e in today_entries),
        "carbs":    sum(e["carbs"]    for e in today_entries),
        "fat":      sum(e["fat"]      for e in today_entries),
    }

    return jsonify({"status": "logged", "today_totals": totals})


@app.route("/api/calorie/today", methods=["GET"])
def api_calorie_today():
    """Return today's calorie totals."""
    _init_session()
    today = str(date.today())
    today_entries = [
        e for e in session.get("calorie_log", [])
        if e["date"] == today
    ]
    totals = {
        "calories": sum(e["calories"] for e in today_entries),
        "protein":  sum(e.get("protein", 0) for e in today_entries),
        "carbs":    sum(e.get("carbs", 0)   for e in today_entries),
        "fat":      sum(e.get("fat", 0)     for e in today_entries),
        "entries":  today_entries,
        "target":   session.get("target_calories", 2000),
    }
    return jsonify(totals)


# ════════════════════════════════════════════════════════════════════════════════
#  Routes — Daily Plan & Motivation
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/api/daily-plan", methods=["POST"])
def api_daily_plan():
    """Generate a full daily fitness + nutrition plan."""
    _init_session()
    data    = request.get_json(silent=True) or {}
    profile = {
        **session["profile"],
        "target_calories": session.get("target_calories", 2000),
    }
    day_type = data.get("day_type", "workout")
    plan = fitness_agent.get_daily_plan(profile, day_type)
    return jsonify({"plan": plan})


@app.route("/api/motivation", methods=["GET"])
def api_motivation():
    """Return a personalised motivational message."""
    _init_session()
    streak = session.get("streak", 0)
    goal   = session["profile"].get("goal", "fitness")
    message = fitness_agent.get_motivation(streak, goal)
    return jsonify({"message": message, "streak": streak})


@app.route("/api/tip", methods=["GET"])
def api_tip():
    """Return a daily fitness tip (cached per day per session)."""
    _init_session()
    today = str(date.today())

    if session.get("daily_tip_shown") != today:
        tip = fitness_agent.get_fitness_tip()
        session["daily_tip_shown"] = today
        session["daily_tip"] = tip
    else:
        tip = session.get("daily_tip", "Stay consistent — progress takes time! 💪")

    return jsonify({"tip": tip, "date": today})


# ════════════════════════════════════════════════════════════════════════════════
#  Routes — Progress Dashboard
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/api/progress", methods=["GET"])
def api_progress():
    """Return summary stats for the progress dashboard."""
    _init_session()
    logs = session.get("workout_log", [])

    # Weekly stats (last 7 days)
    from datetime import timedelta
    week_ago = str(date.today() - timedelta(days=7))
    weekly   = [l for l in logs if l["date"] >= week_ago]

    return jsonify({
        "streak":              session.get("streak", 0),
        "total_workouts":      session.get("total_workouts", 0),
        "achievements":        session.get("achievements", []),
        "weekly_workouts":     len(weekly),
        "weekly_calories_burned": sum(l.get("calories_burned", 0) for l in weekly),
        "recent_logs":         logs[-7:],
        "target_calories":     session.get("target_calories", 2000),
    })


# ════════════════════════════════════════════════════════════════════════════════
#  Routes — Static Data
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/api/activity-levels", methods=["GET"])
def api_activity_levels():
    """Return activity level options for the frontend."""
    return jsonify({k: v["label"] for k, v in ACTIVITY_LEVELS.items()})


@app.route("/api/warmup", methods=["GET"])
def api_warmup():
    """Return warmup exercises."""
    return jsonify(get_warmup())


@app.route("/api/cooldown", methods=["GET"])
def api_cooldown():
    """Return cool-down exercises."""
    return jsonify(get_cooldown())


# ════════════════════════════════════════════════════════════════════════════════
#  Error Handlers
# ════════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found."}), 404


@app.errorhandler(500)
def server_error(e):
    logger.exception("Internal server error: %s", e)
    return jsonify({"error": "Internal server error. Please try again."}), 500


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed."}), 405


# ════════════════════════════════════════════════════════════════════════════════
#  Entry Point
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    port  = int(os.getenv("PORT", 5000))
    logger.info("Starting Fitness Buddy on port %d (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
