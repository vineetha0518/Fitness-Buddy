"""
FitnessBuddy — Calorie & TDEE Calculator Utility
=================================================
Computes BMR (Basal Metabolic Rate) and TDEE (Total Daily Energy Expenditure)
using Mifflin-St Jeor equation, and provides macronutrient targets.
"""

# ── Activity Multipliers (PAL — Physical Activity Level) ──────────────────────
ACTIVITY_LEVELS = {
    "sedentary":        {"label": "Sedentary (desk job, little/no exercise)",  "multiplier": 1.2},
    "light":            {"label": "Lightly Active (1–3 workouts/week)",         "multiplier": 1.375},
    "moderate":         {"label": "Moderately Active (3–5 workouts/week)",      "multiplier": 1.55},
    "very_active":      {"label": "Very Active (6–7 workouts/week)",            "multiplier": 1.725},
    "extra_active":     {"label": "Extra Active (physical job + workouts)",     "multiplier": 1.9},
}

# ── Goal Adjustments (daily kcal delta) ───────────────────────────────────────
GOAL_ADJUSTMENTS = {
    "weight_loss":      -500,   # ~0.5 kg/week loss
    "aggressive_loss":  -750,   # ~0.75 kg/week loss
    "maintenance":        0,
    "muscle_gain":      +300,   # lean bulk
    "aggressive_gain":  +500,   # bulk
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """
    Mifflin-St Jeor BMR equation.

    Args:
        weight_kg: body weight in kg
        height_cm: height in cm
        age:       age in years
        gender:    'male' or 'female'

    Returns:
        BMR in kcal/day (float)
    """
    if gender.lower() in ("male", "m"):
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161


def calculate_tdee(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str = "moderate",
    goal: str = "maintenance",
) -> dict:
    """
    Calculate TDEE and goal-adjusted calorie targets.

    Args:
        weight_kg:      body weight in kg
        height_cm:      height in cm
        age:            age in years
        gender:         'male' or 'female'
        activity_level: key from ACTIVITY_LEVELS
        goal:           key from GOAL_ADJUSTMENTS

    Returns:
        dict with bmr, tdee, target_calories, macros, and water intake
    """
    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        raise ValueError("Weight, height, and age must be positive values.")

    level = ACTIVITY_LEVELS.get(activity_level, ACTIVITY_LEVELS["moderate"])
    adj   = GOAL_ADJUSTMENTS.get(goal, 0)

    bmr  = round(calculate_bmr(weight_kg, height_cm, age, gender), 0)
    tdee = round(bmr * level["multiplier"], 0)
    target = max(1200, round(tdee + adj, 0))   # Never below 1200 kcal

    macros = _calculate_macros(target, goal)
    water  = _water_intake(weight_kg, activity_level)

    return {
        "bmr":              int(bmr),
        "tdee":             int(tdee),
        "target_calories":  int(target),
        "activity_label":   level["label"],
        "goal":             goal.replace("_", " ").title(),
        "calorie_adjustment": adj,
        "macros":           macros,
        "water_litres":     water,
        "meal_split":       _meal_distribution(target),
    }


def _calculate_macros(calories: float, goal: str) -> dict:
    """Return macro targets in grams based on goal."""
    # Protein: 1.6–2.2 g/kg is standard for active individuals
    # Here we use calorie-based percentages for simplicity
    if goal in ("muscle_gain", "aggressive_gain"):
        protein_pct, fat_pct, carb_pct = 0.30, 0.25, 0.45
    elif goal in ("weight_loss", "aggressive_loss"):
        protein_pct, fat_pct, carb_pct = 0.35, 0.30, 0.35
    else:   # maintenance
        protein_pct, fat_pct, carb_pct = 0.25, 0.30, 0.45

    return {
        "protein_g":      round((calories * protein_pct) / 4),   # 4 kcal/g
        "carbohydrate_g": round((calories * carb_pct)   / 4),
        "fat_g":          round((calories * fat_pct)    / 9),    # 9 kcal/g
        "fiber_g":        25 if calories < 2000 else 35,
    }


def _water_intake(weight_kg: float, activity_level: str) -> float:
    """Recommend daily water intake in litres."""
    base = weight_kg * 0.033          # 33 ml per kg body weight
    if activity_level in ("very_active", "extra_active"):
        base += 1.0                   # Extra litre for intense activity
    elif activity_level == "moderate":
        base += 0.5
    return round(base, 1)


def _meal_distribution(calories: int) -> dict:
    """Suggest calorie split across meals."""
    return {
        "breakfast": round(calories * 0.25),
        "mid_morning_snack": round(calories * 0.10),
        "lunch": round(calories * 0.30),
        "evening_snack": round(calories * 0.10),
        "dinner": round(calories * 0.25),
    }
