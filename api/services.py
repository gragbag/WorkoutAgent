from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from api.exercise_library import get_candidate_exercises
from api.intake import normalize_plan_request
from api.models import PlanMetadata, PlanRequest, PromptBundle
from api.rag import retrieve_relevant_context


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
    compatible_exercises = get_candidate_exercises(normalized, limit=120)
    retrieved_context, retrieval_truncated = retrieve_relevant_context(
        normalized, compatible_exercises
    )
    retrieved_titles = {chunk.title for chunk in retrieved_context}

    candidate_exercises = [
        exercise for exercise in compatible_exercises if exercise.name in retrieved_titles
    ]

    if len(candidate_exercises) < 16:
        for exercise in compatible_exercises:
            if exercise in candidate_exercises:
                continue
            candidate_exercises.append(exercise)
            if len(candidate_exercises) >= 16:
                break

    return PromptBundle(
        normalized_input=normalized,
        candidate_exercises=candidate_exercises,
        retrieved_context=retrieved_context,
        retrieval_truncated=retrieval_truncated,
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
