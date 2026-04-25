from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from api.exercise_library import get_candidate_exercises
from api.intake import normalize_plan_request
from api.models import (
    ExerciseCandidate,
    NormalizedPlanRequest,
    PlanDay,
    PlanExercise,
    PlanMetadata,
    PlanRequest,
    PlanResponse,
    PromptBundle,
)
from api.planning_knowledge import get_split_template
from api.prompt_builder import build_plan_prompt
from api.rag import retrieve_relevant_context
from api.validators import validate_plan_response

WARMUP_LIBRARY = {
    "default": ["5-minute easy cardio", "Dynamic mobility flow"],
    "shoulder_sensitive": ["Band pull-aparts", "Scapular wall slides"],
}

COOLDOWN_LIBRARY = {
    "default": ["Easy walking cooldown", "Two minutes of relaxed breathing"],
    "lower_body": ["Hamstring stretch", "Hip flexor stretch"],
}


@dataclass
class Session:
    session_id: str
    created_at: str
    messages: list[dict[str, str]] = field(default_factory=list)


sessions: dict[str, Session] = {}


def create_session() -> Session:
    session = Session(
        session_id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    sessions[session.session_id] = session
    return session


def get_session(session_id: str) -> Session | None:
    return sessions.get(session_id)


def append_message(session_id: str, role: str, content: str) -> Session | None:
    session = get_session(session_id)
    if not session:
        return None

    session.messages.append(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    return session


def prepare_plan_generation(payload: PlanRequest) -> PromptBundle:
    normalized = normalize_plan_request(payload)
    candidate_exercises = get_candidate_exercises(normalized)
    retrieved_context, retrieval_truncated = retrieve_relevant_context(
        normalized, candidate_exercises
    )
    return build_plan_prompt(
        normalized,
        candidate_exercises,
        retrieved_context,
        retrieval_truncated=retrieval_truncated,
    )


def build_plan_metadata(
    prompt_bundle: PromptBundle,
    *,
    provider_requested: str,
    provider_used: str,
    model_used: str,
    fallback_used: bool,
    fallback_reason: str = "",
) -> PlanMetadata:
    return PlanMetadata(
        provider_requested=provider_requested,
        provider_used=provider_used,
        model_used=model_used,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        candidate_exercise_count=len(prompt_bundle.candidate_exercises),
        retrieved_chunk_count=len(prompt_bundle.retrieved_context),
        retrieval_strategy="local_sparse_embedding_rag",
        retrieval_truncated=prompt_bundle.retrieval_truncated,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _focus_templates(normalized: NormalizedPlanRequest) -> list[str]:
    return get_split_template(normalized)


def _candidate_slice(
    candidate_exercises: list[ExerciseCandidate], day_index: int, count: int = 4
) -> list[ExerciseCandidate]:
    if not candidate_exercises:
        return []

    start_index = (day_index * 2) % len(candidate_exercises)
    rotated = candidate_exercises[start_index:] + candidate_exercises[:start_index]
    return rotated[:count]


def _build_exercises(
    normalized: NormalizedPlanRequest,
    candidate_exercises: list[ExerciseCandidate],
    day_index: int,
) -> list[PlanExercise]:
    experience = normalized.athlete_profile.experience
    injuries = normalized.constraints.injuries.lower()
    selected = _candidate_slice(candidate_exercises, day_index)

    if len(selected) < 3:
        raise ValueError("Not enough exercise candidates were retrieved to build a plan.")

    base_sets = 3 if experience == "Beginner" else 4
    default_rest = 90 if normalized.preferences.intensity_preference == "Challenging" else 60

    return [
        PlanExercise(
            name=exercise.name,
            sets=base_sets,
            reps="10-12" if exercise_index >= 2 else "6-10",
            rest_seconds=default_rest,
            intensity_note=(
                "Use a pain-free range and stop with 2 reps in reserve."
                if "shoulder" in injuries or "pain" in injuries
                else "Finish each set with 1-2 reps left in reserve."
            ),
            primary_muscle_group=exercise.primary_muscle_group,
            equipment_used=exercise.equipment_used,
            substitution_note=(
                "Swap for a similar pain-free pattern if symptoms flare."
                if exercise.contraindications
                else "Swap for a similar pattern if equipment access changes."
            ),
        )
        for exercise_index, exercise in enumerate(selected)
    ]


def _build_warmup(normalized: NormalizedPlanRequest, focus: str) -> list[str]:
    injuries = normalized.constraints.injuries.lower()
    if "shoulder" in injuries:
        return WARMUP_LIBRARY["shoulder_sensitive"]
    if "lower" in focus.lower():
        return ["5-minute easy bike", "Leg swings and glute activation"]
    return WARMUP_LIBRARY["default"]


def _build_cooldown(focus: str) -> list[str]:
    if "lower" in focus.lower():
        return COOLDOWN_LIBRARY["lower_body"]
    return COOLDOWN_LIBRARY["default"]


def _build_day_notes(normalized: NormalizedPlanRequest, is_last_day: bool) -> list[str]:
    notes = []
    intensity = normalized.preferences.intensity_preference

    if normalized.constraints.injuries != "None reported":
        notes.append("Prioritize clean technique and avoid any painful movement pattern.")
    else:
        notes.append("Keep the session challenging but technically crisp.")

    if intensity == "Light":
        notes.append("Keep effort smooth and sustainable instead of pushing hard sets.")
    elif intensity == "Challenging":
        notes.append("Push the working sets with intent while keeping one solid rep in reserve.")
    else:
        notes.append("Use a steady training pace that feels repeatable across the full week.")

    if is_last_day:
        notes.append("Use this session to finish the week feeling accomplished, not wrecked.")

    return notes[:3]


def _build_optional_day_notes(normalized: NormalizedPlanRequest) -> list[str]:
    notes = ["Treat this session as a bonus option, not a must-hit workout."]

    if normalized.preferences.intensity_preference == "Light":
        notes.append("Keep this one easy and restorative if energy is limited.")
    else:
        notes.append("Use this slot for extra practice, light conditioning, or accessory work.")

    notes.append("Skip it without guilt if schedule or recovery is tight.")
    return notes[:3]


def build_mock_plan_response(
    payload: PlanRequest,
    *,
    prompt_bundle: PromptBundle | None = None,
    provider_requested: str = "mock",
    provider_used: str = "mock",
    model_used: str = "mock-template",
    fallback_used: bool = False,
    fallback_reason: str = "",
) -> PlanResponse:
    prompt_bundle = prompt_bundle or prepare_plan_generation(payload)
    normalized = prompt_bundle.normalized_input
    focuses = _focus_templates(normalized)
    days: list[PlanDay] = []
    optional_days: list[PlanDay] = []

    for index, day_name in enumerate(normalized.constraints.available_training_days):
        focus = focuses[index % len(focuses)]
        days.append(
            PlanDay(
                day=day_name,
                focus=focus,
                duration_minutes=normalized.constraints.session_length,
                warmup=_build_warmup(normalized, focus),
                exercises=_build_exercises(
                    normalized,
                    prompt_bundle.candidate_exercises,
                    index,
                ),
                cooldown=_build_cooldown(focus),
                coach_notes=_build_day_notes(
                    normalized,
                    is_last_day=index == normalized.constraints.days_per_week - 1,
                ),
            )
        )

    for flex_index, day_name in enumerate(normalized.constraints.flexible_training_days):
        focus = focuses[(len(days) + flex_index) % len(focuses)]
        optional_days.append(
            PlanDay(
                day=day_name,
                focus=f"{focus} (optional)",
                duration_minutes=max(20, normalized.constraints.session_length - 15),
                warmup=_build_warmup(normalized, focus),
                exercises=_build_exercises(
                    normalized,
                    prompt_bundle.candidate_exercises,
                    len(days) + flex_index,
                )[:3],
                cooldown=_build_cooldown(focus),
                coach_notes=_build_optional_day_notes(normalized),
            )
        )

    athlete = normalized.athlete_profile
    constraints = normalized.constraints
    height_text = f"{athlete.height_feet} ft {athlete.height_inches} in"
    weight_text = f"{athlete.weight_lbs} lb"

    plan = PlanResponse(
        summary=(
            f"{constraints.days_per_week}-day plan for a "
            f"{athlete.experience.lower()} athlete, scheduled on "
            f"{', '.join(constraints.available_training_days)}."
        ),
        athlete_snapshot=[
            f"Age range: {athlete.age_range}",
            f"Body metrics: {height_text}, {weight_text}",
            f"Activity level: {athlete.current_activity_level}",
            f"Training setup: {constraints.workout_location} with {', '.join(constraints.equipment)}",
        ],
        coaching_notes=[
            f"Equipment setup: {constraints.workout_location} using {constraints.equipment_details}.",
            f"Cardio preference: {normalized.preferences.cardio_preference}.",
            f"Intensity target: {normalized.preferences.intensity_preference}; variety: {normalized.preferences.variety_preference}.",
            f"Flexible days: {', '.join(constraints.flexible_training_days) if constraints.flexible_training_days else 'None added'}.",
            f"Injury guidance: {constraints.injuries}.",
            f"Additional note: {normalized.preferences.notes}.",
        ],
        days=days,
        optional_days=optional_days,
        metadata=build_plan_metadata(
            prompt_bundle,
            provider_requested=provider_requested,
            provider_used=provider_used,
            model_used=model_used,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        ),
    )

    validate_plan_response(plan, prompt_bundle)
    return plan


def generate_chat_reply(session: Session, message: str) -> str:
    lower_message = message.lower()
    prior_turns = sum(1 for entry in session.messages if entry["role"] == "user")

    if "shoulder" in lower_message:
        return (
            "We should keep pressing volume moderate, favor pain-free ranges of "
            "motion, and add extra upper-back warm-up work."
        )

    if "equipment" in lower_message:
        return (
            "We can tailor the plan around whatever you actually have access to, "
            "even if that means bodyweight and one pair of dumbbells."
        )

    return (
        f"Coach note {prior_turns + 1}: I’d use your latest preferences to tighten "
        "the weekly split, choose simpler exercises first, and keep the plan "
        "realistic enough to follow."
    )
