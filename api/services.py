from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import re
from uuid import uuid4

from api.exercise_library import get_candidate_exercises
from api.intake import normalize_plan_request
from api.models import PlanDay, PlanExercise, PlanMetadata, PlanRequest, PlanResponse, PromptBundle
from api.rag import retrieve_relevant_context
from api.split_templates import shortlist_split_templates


@dataclass
class Session:
    session_id: str
    created_at: str
    messages: list[dict[str, str]] = field(default_factory=list)


sessions: dict[str, Session] = {}
REP_TOKEN_RE = re.compile(r"\d+")
SECONDS_TOKEN_RE = re.compile(r"(\d+)\s*(?:sec|secs|second|seconds)\b")
MINUTES_TOKEN_RE = re.compile(r"(\d+)\s*(?:min|mins|minute|minutes)\b")
WARMUP_SECONDS_PER_ITEM = 150
COOLDOWN_SECONDS_PER_ITEM = 90
EXERCISE_TRANSITION_SECONDS = 75
SETUP_BUFFER_SECONDS = 60
DEFAULT_SET_WORK_SECONDS = 45


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
    split_template_matches = shortlist_split_templates(normalized)
    compatible_exercises = get_candidate_exercises(normalized, limit=40)
    retrieved_context, retrieval_truncated = retrieve_relevant_context(
        normalized, compatible_exercises
    )
    retrieved_titles = {chunk.title for chunk in retrieved_context}

    candidate_exercises = [
        exercise for exercise in compatible_exercises if exercise.name in retrieved_titles
    ]

    if len(candidate_exercises) < 10:
        for exercise in compatible_exercises:
            if exercise in candidate_exercises:
                continue
            candidate_exercises.append(exercise)
            if len(candidate_exercises) >= 10:
                break

    return PromptBundle(
        normalized_input=normalized,
        candidate_exercises=candidate_exercises,
        retrieved_context=retrieved_context,
        retrieval_truncated=retrieval_truncated,
        split_template_matches=split_template_matches,
    )


def build_plan_metadata(
    prompt_bundle: PromptBundle,
    *,
    provider_requested: str,
    provider_used: str,
    model_used: str,
) -> PlanMetadata:
    return PlanMetadata(
        provider_requested=provider_requested,
        provider_used=provider_used,
        model_used=model_used,
        candidate_exercise_count=len(prompt_bundle.candidate_exercises),
        retrieved_chunk_count=len(prompt_bundle.retrieved_context),
        retrieval_strategy="local_sparse_embedding_rag",
        retrieval_truncated=prompt_bundle.retrieval_truncated,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _estimate_set_work_seconds(exercise: PlanExercise) -> int:
    reps_text = exercise.reps.lower()

    minute_match = MINUTES_TOKEN_RE.search(reps_text)
    if minute_match:
        return min(180, max(45, int(minute_match.group(1)) * 60))

    seconds_match = SECONDS_TOKEN_RE.search(reps_text)
    if seconds_match:
        return min(180, max(30, int(seconds_match.group(1))))

    rep_values = [int(token) for token in REP_TOKEN_RE.findall(reps_text)]
    if rep_values:
        average_reps = sum(rep_values) / len(rep_values)
        estimated = int(round(average_reps * 4.5 + 10))
        return min(75, max(25, estimated))

    return DEFAULT_SET_WORK_SECONDS


def estimate_day_duration_minutes(day: PlanDay) -> int:
    warmup_seconds = len(day.warmup) * WARMUP_SECONDS_PER_ITEM
    cooldown_seconds = len(day.cooldown) * COOLDOWN_SECONDS_PER_ITEM
    work_seconds = 0

    for exercise in day.exercises:
        set_work_seconds = _estimate_set_work_seconds(exercise)
        work_seconds += exercise.sets * set_work_seconds
        work_seconds += max(0, exercise.sets - 1) * exercise.rest_seconds
        work_seconds += EXERCISE_TRANSITION_SECONDS

    total_seconds = warmup_seconds + cooldown_seconds + work_seconds + SETUP_BUFFER_SECONDS
    return max(1, math.ceil(total_seconds / 60))


def apply_estimated_durations(plan: PlanResponse) -> PlanResponse:
    for day in plan.days:
        day.duration_minutes = estimate_day_duration_minutes(day)
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
