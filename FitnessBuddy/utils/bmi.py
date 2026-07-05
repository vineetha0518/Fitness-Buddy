"""
FitnessBuddy — BMI Calculator Utility
======================================
Calculates Body Mass Index (BMI) and returns health status,
risk levels, and personalized recommendations.
"""

# ── BMI Classification Thresholds (WHO standard) ──────────────────────────────
BMI_CATEGORIES = [
    {"max": 16.0,  "label": "Severely Underweight", "color": "danger",  "risk": "High"},
    {"max": 18.5,  "label": "Underweight",           "color": "warning", "risk": "Moderate"},
    {"max": 25.0,  "label": "Normal Weight",          "color": "success", "risk": "Low"},
    {"max": 30.0,  "label": "Overweight",             "color": "warning", "risk": "Moderate"},
    {"max": 35.0,  "label": "Obese Class I",          "color": "danger",  "risk": "High"},
    {"max": 40.0,  "label": "Obese Class II",         "color": "danger",  "risk": "Very High"},
    {"max": float("inf"), "label": "Obese Class III", "color": "danger",  "risk": "Extremely High"},
]

# ── Ideal Weight Ranges (Devine Formula) ──────────────────────────────────────
def calculate_ideal_weight(height_cm: float, gender: str) -> dict:
    """Return ideal weight range using Devine formula."""
    height_in = height_cm / 2.54
    inches_over_5ft = max(0, height_in - 60)

    if gender.lower() in ("male", "m"):
        base = 50.0
        per_inch = 2.3
    else:
        base = 45.5
        per_inch = 2.3

    ideal = base + per_inch * inches_over_5ft
    return {
        "min_kg": round(ideal * 0.9, 1),
        "ideal_kg": round(ideal, 1),
        "max_kg": round(ideal * 1.1, 1),
    }


def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    """
    Calculate BMI and return full analysis.

    Args:
        weight_kg: body weight in kilograms
        height_cm: height in centimetres

    Returns:
        dict with bmi value, category, color, risk, advice, and ideal weight
    """
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Height and weight must be positive values.")

    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)

    # Determine category
    category_info = BMI_CATEGORIES[-1]
    for cat in BMI_CATEGORIES:
        if bmi < cat["max"]:
            category_info = cat
            break

    # Build tailored advice
    label = category_info["label"]
    advice = _get_bmi_advice(label, bmi)

    return {
        "bmi": bmi,
        "category": label,
        "color": category_info["color"],
        "risk": category_info["risk"],
        "advice": advice,
        "healthy_range": "18.5 – 24.9",
    }


def _get_bmi_advice(label: str, bmi: float) -> str:
    """Return category-specific actionable advice."""
    advices = {
        "Severely Underweight": (
            "Your BMI indicates severe underweight. Please consult a doctor or "
            "registered dietitian immediately. Focus on nutrient-dense calorie-rich "
            "foods and gentle strength training to build lean mass safely."
        ),
        "Underweight": (
            "You are slightly underweight. Aim for a slight calorie surplus "
            "(+300–500 kcal/day) with protein-rich Indian foods like dal, paneer, "
            "eggs, and nuts. Include strength training 3× per week."
        ),
        "Normal Weight": (
            "Excellent! You are at a healthy weight. Maintain it with balanced "
            "nutrition, 150+ minutes of moderate activity per week, and adequate sleep."
        ),
        "Overweight": (
            "You are slightly above the healthy range. Aim for a 300–500 kcal/day "
            "deficit through diet and 30–45 min of cardio + strength training 4–5× "
            "per week. Reduce refined carbs and sugary beverages."
        ),
        "Obese Class I": (
            "Consider consulting a healthcare professional. Combine a moderate calorie "
            "deficit with progressive resistance training and low-impact cardio. "
            "Focus on whole grains, vegetables, and lean protein."
        ),
        "Obese Class II": (
            "Medical supervision is strongly recommended before starting a new "
            "exercise or diet program. Low-impact activities like swimming, cycling, "
            "and walking are safer starting points."
        ),
        "Obese Class III": (
            "Please consult a physician before beginning any exercise program. "
            "A medically supervised weight-management plan is recommended."
        ),
    }
    return advices.get(label, "Maintain a balanced diet and regular physical activity.")
