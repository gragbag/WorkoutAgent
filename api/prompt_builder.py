from api.models import (
    ExerciseCandidate,
    NormalizedPlanRequest,
    PromptBundle,
    RetrievedContextChunk,
)
from api.planning_knowledge import get_split_template, get_staple_exercise_hints

OUTPUT_SCHEMA_DESCRIPTION = """
Return valid JSON only with this shape:
{
  "summary": string,
  "athlete_snapshot": [string, string, string],
  "coaching_notes": [string, string, string],
  "days": [
    {
      "day": "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday",
      "focus": string,
      "duration_minutes": integer,
      "warmup": [string, string],
      "exercises": [
        {
          "name": string,
          "sets": integer,
          "reps": string,
          "rest_seconds": integer,
          "intensity_note": string
        }
      ],
      "cooldown": [string],
      "coach_notes": [string]
    }
  ],
  "optional_days": [
    {
      "day": "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday",
      "focus": string,
      "duration_minutes": integer,
      "warmup": [string, string],
      "exercises": [
        {
          "name": string,
          "sets": integer,
          "reps": string,
          "rest_seconds": integer,
          "intensity_note": string
        }
      ],
      "cooldown": [string],
      "coach_notes": [string]
    }
  ]
}
""".strip()


def _render_candidate_exercises(candidate_exercises: list[ExerciseCandidate]) -> str:
    if not candidate_exercises:
        return "- No candidate exercises were retrieved."

    rendered = []
    for exercise in candidate_exercises:
        rendered.append(
            "- "
            f"{exercise.name} | muscle: {exercise.primary_muscle_group} | "
            f"equipment: {exercise.equipment_used} | difficulty: {exercise.difficulty} | "
            f"pattern: {exercise.movement_pattern} | "
            f"contraindications: {', '.join(exercise.contraindications) or 'none'}"
        )

    return "\n".join(rendered)


def _render_retrieved_context(retrieved_context: list[RetrievedContextChunk]) -> str:
    if not retrieved_context:
        return "- No retrieved knowledge base context was available."

    return "\n".join(
        [
            f"- score={chunk.score} | {chunk.title} | {chunk.content}"
            for chunk in retrieved_context
        ]
    )


def build_plan_prompt(
    normalized: NormalizedPlanRequest,
    candidate_exercises: list[ExerciseCandidate],
    retrieved_context: list[RetrievedContextChunk],
    retrieval_truncated: bool = False,
) -> PromptBundle:
    athlete = normalized.athlete_profile
    constraints = normalized.constraints
    preferences = normalized.preferences
    height_text = f"{athlete.height_feet} ft {athlete.height_inches} in"
    weight_text = f"{athlete.weight_lbs} lb"
    split_template = get_split_template(normalized)
    staple_hints = get_staple_exercise_hints(normalized)

    system_prompt = (
        "You are WorkoutAgent, a careful strength and fitness programming assistant. "
        "Write practical weekly plans that match the athlete's schedule, experience, "
        "equipment, and recovery context. Avoid risky or unrealistic recommendations. "
        "Respect injuries and only return valid JSON matching the required schema."
    )

    user_prompt = f"""
Create a weekly workout plan from this normalized intake.

Athlete profile:
- Experience: {athlete.experience}
- Age range: {athlete.age_range}
- Height: {height_text}
- Weight: {weight_text}
- Current activity level: {athlete.current_activity_level}

Constraints:
- Available equipment categories: {", ".join(constraints.equipment)}
- Workout location: {constraints.workout_location}
- Equipment details: {constraints.equipment_details}
- Training days per week: {constraints.days_per_week}
- Session length: {constraints.session_length} minutes
- Available training days: {", ".join(constraints.available_training_days)}
- Flexible training days: {", ".join(constraints.flexible_training_days) if constraints.flexible_training_days else "None"}
- Injuries or pain points: {constraints.injuries}

Preferences and notes:
- Cardio preference: {preferences.cardio_preference}
- Intensity preference: {preferences.intensity_preference}
- Variety preference: {preferences.variety_preference}
- Additional notes: {preferences.notes}

Recommended split framework:
- {" | ".join(split_template)}

Staple exercise hints to favor when available:
- {", ".join(staple_hints) if staple_hints else "Use simple, recognizable compound lifts where possible."}

Retrieved candidate exercises:
{_render_candidate_exercises(candidate_exercises)}

Retrieved knowledge base context (ordered by relevance):
{_render_retrieved_context(retrieved_context)}

Planning requirements:
- Use exactly {constraints.days_per_week} workout days.
- Only schedule workouts on these days: {", ".join(constraints.available_training_days)}.
- Optional bonus sessions may be placed only on these flexible days: {", ".join(constraints.flexible_training_days) if constraints.flexible_training_days else "none"}.
- Each day must include a warmup, main exercises, cooldown, and coach notes.
- Keep exercise choices realistic for the listed equipment.
- Treat the available equipment categories as a combined pool, not a single gym type.
- If injuries are present, bias toward joint-friendly exercise choices and conservative coaching notes.
- Prefer using exercises from the retrieved candidate list unless there is a strong reason not to.
- Avoid prescribing exercises whose contraindications conflict with the athlete's injuries.
- Favor simple, recognizable exercise names over niche branded variations when both are available.
- Make the weekly structure feel traditional and easy to follow, such as upper/lower or push/pull/legs when appropriate for the schedule.
- If no flexible days are provided, return an empty optional_days array.

{OUTPUT_SCHEMA_DESCRIPTION}
""".strip()

    return PromptBundle(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        normalized_input=normalized,
        candidate_exercises=candidate_exercises,
        retrieved_context=retrieved_context,
        retrieval_truncated=retrieval_truncated,
    )
