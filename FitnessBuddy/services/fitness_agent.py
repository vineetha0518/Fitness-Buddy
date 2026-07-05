"""
FitnessBuddy — Fitness Agent (Prompt Engineering Layer)
========================================================
Builds structured prompts for the IBM Granite model and
interprets responses into structured fitness guidance.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AGENT_INSTRUCTIONS  ←  Customise personality here
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modify the sections below to change the AI's behaviour
without touching any other code in the application.
"""

# ══════════════════════════════════════════════════════════════════════════════
#  AGENT_INSTRUCTIONS
#  All customisation lives here. No other file needs to be touched.
# ══════════════════════════════════════════════════════════════════════════════

AGENT_INSTRUCTIONS = {

    # ── Personality & Communication Style ────────────────────────────────────
    "name": "FitBot",
    "personality": (
        "You are FitBot — a warm, enthusiastic, and knowledgeable AI fitness coach. "
        "You speak like a supportive best friend who happens to be a certified personal "
        "trainer and nutrition expert. You are encouraging, positive, and non-judgmental. "
        "You celebrate every small win and never shame users about their current fitness level."
    ),

    # ── Motivational Style ────────────────────────────────────────────────────
    "motivation_style": (
        "Use uplifting, energetic language. Reference Indian fitness icons and cultural "
        "context where appropriate. Include short motivational phrases like "
        "'Ek aur rep!' (One more rep!) or 'Aap kar sakte ho!' (You can do it!) "
        "occasionally to add cultural warmth. Keep motivation genuine, not hollow."
    ),

    # ── Fitness Specialisation ────────────────────────────────────────────────
    "specialization": (
        "Specialise in home-based workouts requiring minimal or no equipment. "
        "Provide science-backed recommendations. Cover all fitness goals: "
        "weight loss, muscle gain, endurance, flexibility, and general wellness. "
        "Always tailor advice to the user's stated fitness level (beginner/intermediate/advanced)."
    ),

    # ── Indian Food & Nutrition Focus ─────────────────────────────────────────
    "nutrition_focus": (
        "Prioritise traditional Indian foods: dals, sabzis, roti, rice, curd, "
        "paneer, sprouts, makhana, eggs, and regional dishes. Provide calorie "
        "estimates, macros (protein/carbs/fat/fiber), and practical meal timing. "
        "Respect vegetarian, vegan, and non-vegetarian dietary preferences. "
        "Suggest local seasonal produce and budget-friendly meal options."
    ),

    # ── Workout Intensity Guidance ────────────────────────────────────────────
    "intensity_guidance": (
        "Always start new users with a proper warm-up and end with a cool-down. "
        "Recommend progressive overload — increase intensity gradually over weeks. "
        "For beginners: 2–3 sessions/week. Intermediate: 4–5. Advanced: 5–6. "
        "Include rest days and active recovery in every plan."
    ),

    # ── Language Tone ─────────────────────────────────────────────────────────
    "language_tone": (
        "Respond in clear, simple English. Avoid overly technical jargon unless "
        "the user asks for it. Use bullet points and short paragraphs for readability. "
        "For Indian users, you may occasionally use Hindi fitness terms with English "
        "translations in brackets. Keep responses concise but complete."
    ),

    # ── Response Format ───────────────────────────────────────────────────────
    "response_format": (
        "Structure responses with clear headings using emoji icons (🏋️, 🥗, 💧, etc.). "
        "Use bullet points for exercise lists and numbered steps for instructions. "
        "Always end workout recommendations with a 'Pro Tip' section. "
        "Include estimated calories burned for workout suggestions. "
        "Provide time estimates for all workout plans."
    ),

    # ── Safety Guidelines ─────────────────────────────────────────────────────
    "safety_guidelines": (
        "ALWAYS include this medical disclaimer for medical/health advice: "
        "'⚠️ Disclaimer: This is for informational purposes only and is not a substitute "
        "for professional medical advice. Consult a healthcare professional before starting "
        "any new exercise or diet program, especially if you have any medical conditions.' "
        "Advise stopping exercise if the user experiences pain, dizziness, or chest discomfort. "
        "Never recommend extreme calorie restriction (below 1200 kcal for women, 1500 for men). "
        "Always recommend consulting a doctor for users over 60, pregnant users, or those with "
        "chronic conditions like diabetes, hypertension, or heart disease."
    ),

    # ── Language & Regional Awareness ────────────────────────────────────────
    "regional_awareness": (
        "Be aware of Indian regional preferences. When suggesting meals, mention "
        "north Indian, south Indian, east Indian, and west Indian options where relevant. "
        "Acknowledge festival seasons (Navratri, Ramadan, etc.) when users mention dietary "
        "restrictions. Suggest locally available, affordable ingredients."
    ),

    # ── Scope Restrictions ────────────────────────────────────────────────────
    "scope": (
        "You are a fitness and nutrition assistant ONLY. If asked about unrelated topics "
        "(politics, programming, etc.), politely redirect: "
        "'I'm best at fitness and nutrition topics! Let me help you with your health goals instead.' "
        "Never diagnose medical conditions or prescribe medication."
    ),
}

# ──────────────────────────────────────────────────────────────────────────────
# Build the system prompt from AGENT_INSTRUCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def _build_system_prompt() -> str:
    """Assemble the full system prompt from AGENT_INSTRUCTIONS."""
    ai = AGENT_INSTRUCTIONS
    return f"""
{ai['personality']}

MOTIVATIONAL APPROACH: {ai['motivation_style']}

FITNESS EXPERTISE: {ai['specialization']}

NUTRITION EXPERTISE: {ai['nutrition_focus']}

INTENSITY & PROGRAMMING: {ai['intensity_guidance']}

COMMUNICATION STYLE: {ai['language_tone']}

RESPONSE FORMATTING: {ai['response_format']}

SAFETY RULES (NON-NEGOTIABLE): {ai['safety_guidelines']}

REGIONAL AWARENESS: {ai['regional_awareness']}

SCOPE: {ai['scope']}
""".strip()


SYSTEM_PROMPT = _build_system_prompt()


# ──────────────────────────────────────────────────────────────────────────────
# Prompt builders — one function per use-case
# ──────────────────────────────────────────────────────────────────────────────

from services.granite_client import generate_text   # noqa: E402


def chat(user_message: str, history: list[dict] | None = None) -> str:
    """
    General conversational chat with optional multi-turn history.

    Args:
        user_message: Current user input
        history:      List of {"role": "user"|"assistant", "content": str}

    Returns:
        AI-generated response string
    """
    history = history or []

    # Build conversation context (last 6 turns for context window efficiency)
    conversation = ""
    for turn in history[-6:]:
        role    = "User"    if turn["role"] == "user" else "FitBot"
        conversation += f"\n{role}: {turn['content']}"

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Conversation so far:{conversation}\n\n"
        f"User: {user_message}\n"
        f"FitBot:"
    )
    return generate_text(prompt)


def get_workout_recommendation(profile: dict) -> str:
    """
    Generate a personalized workout plan.

    Args:
        profile: dict with keys — age, gender, weight_kg, height_cm,
                 fitness_level, goal, available_time_min, equipment
    Returns:
        Formatted workout plan string
    """
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Generate a complete, personalized workout plan for the following user:\n"
        f"- Age: {profile.get('age', 25)} years\n"
        f"- Gender: {profile.get('gender', 'not specified')}\n"
        f"- Weight: {profile.get('weight_kg', 70)} kg\n"
        f"- Height: {profile.get('height_cm', 170)} cm\n"
        f"- Fitness Level: {profile.get('fitness_level', 'beginner')}\n"
        f"- Goal: {profile.get('goal', 'general fitness')}\n"
        f"- Available Time: {profile.get('available_time_min', 30)} minutes\n"
        f"- Equipment Available: {profile.get('equipment', 'none (bodyweight only)')}\n\n"
        f"Include: warm-up, main exercises (with sets, reps, rest), cool-down, "
        f"weekly schedule, estimated calories burned, and a Pro Tip.\n"
        f"FitBot:"
    )
    return generate_text(prompt)


def get_nutrition_advice(profile: dict, query: str = "") -> str:
    """
    Generate Indian-food-based nutrition recommendations.

    Args:
        profile: user profile dict
        query:   specific nutrition question (optional)

    Returns:
        Nutrition guidance string
    """
    specific = f"Specific question: {query}\n\n" if query else ""
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Provide personalised nutrition advice for:\n"
        f"- Goal: {profile.get('goal', 'general health')}\n"
        f"- Dietary preference: {profile.get('diet', 'vegetarian')}\n"
        f"- Daily calorie target: {profile.get('target_calories', 2000)} kcal\n"
        f"- Protein target: {profile.get('protein_g', 100)}g\n"
        f"{specific}"
        f"Suggest a full-day Indian meal plan with breakfast, mid-morning snack, "
        f"lunch, evening snack, and dinner. Include calories and macros for each meal.\n"
        f"FitBot:"
    )
    return generate_text(prompt)


def get_daily_plan(profile: dict, day_type: str = "workout") -> str:
    """
    Generate a complete daily fitness and nutrition plan.

    Args:
        profile:  user profile dict
        day_type: 'workout', 'rest', or 'active_recovery'

    Returns:
        Full daily plan string
    """
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Create a complete daily plan for a {day_type} day:\n"
        f"- User Goal: {profile.get('goal', 'weight loss')}\n"
        f"- Fitness Level: {profile.get('fitness_level', 'beginner')}\n"
        f"- Target Calories: {profile.get('target_calories', 1800)} kcal\n\n"
        f"Include: wake-up routine, breakfast, workout schedule (if applicable), "
        f"meal plan with times, hydration reminders, evening routine, and sleep tips.\n"
        f"FitBot:"
    )
    return generate_text(prompt)


def get_motivation(streak: int = 0, goal: str = "fitness") -> str:
    """Return a motivational message personalised to the user's streak."""
    streak_text = (
        f"They have maintained a {streak}-day streak!" if streak > 0
        else "They are just starting out."
    )
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Give a short (3–4 sentences) powerful motivational message for a user "
        f"working toward {goal}. {streak_text} Make it personal, energetic, and "
        f"include one actionable tip for today.\n"
        f"FitBot:"
    )
    return generate_text(prompt)


def get_fitness_tip() -> str:
    """Return a daily fitness tip."""
    import random
    topics = [
        "the importance of sleep for muscle recovery",
        "how to stay hydrated during workouts",
        "progressive overload in strength training",
        "the benefits of morning exercise",
        "how to avoid workout plateaus",
        "the role of protein in muscle building",
        "managing DOMS (delayed onset muscle soreness)",
        "benefits of stretching post-workout",
        "healthy snacking before and after exercise",
        "mental health benefits of regular exercise",
    ]
    topic = random.choice(topics)
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Give one concise, practical daily fitness tip about: {topic}. "
        f"Keep it to 2–3 sentences, include an actionable step.\n"
        f"FitBot:"
    )
    return generate_text(prompt)
