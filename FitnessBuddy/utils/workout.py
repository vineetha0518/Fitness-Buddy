"""
FitnessBuddy — Workout Recommendation Utility
==============================================
Loads workout data from JSON and returns level/goal-appropriate
exercise plans with estimated calorie burn.
"""
import json
import os

# ── Load workout dataset once at module import ────────────────────────────────
_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "workouts.json")

with open(_DATA_PATH, "r", encoding="utf-8") as _f:
    WORKOUT_DB: dict = json.load(_f)


def get_workout_plan(
    level: str = "beginner",
    goal: str = "weight_loss",
    available_time_min: int = 30,
) -> dict:
    """
    Return a structured workout plan.

    Args:
        level:              'beginner' | 'intermediate' | 'advanced'
        goal:               'weight_loss' | 'muscle_gain' | 'endurance' | 'flexibility'
        available_time_min: workout duration the user has available

    Returns:
        dict with warmup, exercises, cooldown, weekly schedule, and estimated calories
    """
    level = level.lower() if level.lower() in WORKOUT_DB else "beginner"

    exercises: list = WORKOUT_DB[level].get("full_body", [])

    # Trim exercises to fit available time (rough: ~5 min per exercise)
    max_exercises = max(2, available_time_min // 5)
    exercises = exercises[:max_exercises]

    # Adjust intensity for goal
    exercises = _tune_for_goal(exercises, goal)

    total_calories = sum(
        ex.get("calories_burned", 0) * ex.get("sets", 3)
        for ex in exercises
    )

    return {
        "level": level.title(),
        "goal": goal.replace("_", " ").title(),
        "duration_min": available_time_min,
        "warmup": WORKOUT_DB.get("warmup", []),
        "exercises": exercises,
        "cooldown": WORKOUT_DB.get("cooldown", []),
        "weekly_schedule": WORKOUT_DB["weekly_plan"].get(level, {}),
        "estimated_calories_burned": total_calories,
    }


def get_warmup() -> list:
    """Return warmup exercise list."""
    return WORKOUT_DB.get("warmup", [])


def get_cooldown() -> list:
    """Return cool-down exercise list."""
    return WORKOUT_DB.get("cooldown", [])


def _tune_for_goal(exercises: list, goal: str) -> list:
    """Modify sets/reps based on fitness goal."""
    tuned = []
    for ex in exercises:
        ex = dict(ex)   # shallow copy to avoid mutating source data
        if goal == "muscle_gain":
            ex["sets"] = min(5, ex.get("sets", 3) + 1)
            ex["note"] = "Focus on slow, controlled reps with heavier weight."
        elif goal == "weight_loss":
            ex["rest"] = "30 seconds"   # shorter rest → higher caloric burn
            ex["note"] = "Keep rest minimal to maintain elevated heart rate."
        elif goal == "endurance":
            ex["reps"] = "20" if ex.get("reps", "").isdigit() else ex.get("reps")
            ex["rest"] = "30 seconds"
            ex["note"] = "Aim for higher rep ranges with lighter resistance."
        elif goal == "flexibility":
            ex["note"] = "Prioritise full range of motion on every rep."
        tuned.append(ex)
    return tuned
