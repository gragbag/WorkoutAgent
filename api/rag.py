from __future__ import annotations

import math
import re
from collections import Counter

from api.models import ExerciseCandidate, NormalizedPlanRequest, RetrievedContextChunk

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "into",
    "from",
    "your",
    "their",
    "using",
    "use",
    "only",
    "per",
    "day",
}
MAX_RETRIEVED_CHARS = 2200
MAX_RETRIEVED_ITEMS = 8


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]


def embed_text(text: str) -> Counter[str]:
    return Counter(_tokenize(text))


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0

    dot = sum(left[token] * right[token] for token in left.keys() & right.keys())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))

    if not left_norm or not right_norm:
        return 0.0

    return dot / (left_norm * right_norm)


def score_text_similarity(query: str, candidate_text: str) -> float:
    return _cosine_similarity(embed_text(query), embed_text(candidate_text))


def build_knowledge_base_entry(exercise: ExerciseCandidate) -> str:
    return (
        f"Exercise: {exercise.name}. "
        f"Primary muscle: {exercise.primary_muscle_group}. "
        f"Secondary muscles: {', '.join(exercise.secondary_muscles) or 'none'}. "
        f"Equipment: {exercise.equipment_used}. "
        f"Difficulty: {exercise.difficulty}. "
        f"Movement pattern: {exercise.movement_pattern}. "
        f"Suitable goals: {', '.join(exercise.suitable_goals) or 'general fitness'}. "
        f"Coaching cues: {', '.join(exercise.coaching_cues) or 'move with control'}. "
        f"Contraindications: {', '.join(exercise.contraindications) or 'none'}."
    )


def build_retrieval_query(normalized: NormalizedPlanRequest) -> str:
    athlete = normalized.athlete_profile
    constraints = normalized.constraints
    preferences = normalized.preferences

    return " ".join(
        [
            athlete.experience,
            athlete.current_activity_level,
            " ".join(constraints.equipment),
            constraints.workout_location,
            constraints.equipment_details,
            preferences.cardio_preference,
            preferences.intensity_preference,
            preferences.variety_preference,
            constraints.injuries,
            " ".join(constraints.available_training_days),
            preferences.notes,
        ]
    )


def retrieve_relevant_context(
    normalized: NormalizedPlanRequest,
    candidate_exercises: list[ExerciseCandidate],
    *,
    top_k: int = MAX_RETRIEVED_ITEMS,
    char_budget: int = MAX_RETRIEVED_CHARS,
) -> tuple[list[RetrievedContextChunk], bool]:
    query_embedding = embed_text(build_retrieval_query(normalized))

    scored_chunks: list[RetrievedContextChunk] = []
    for exercise in candidate_exercises:
        content = build_knowledge_base_entry(exercise)
        score = _cosine_similarity(query_embedding, embed_text(content))
        scored_chunks.append(
            RetrievedContextChunk(
                source_id=exercise.name.lower().replace(" ", "-"),
                title=exercise.name,
                score=round(score, 4),
                content=content,
                movement_pattern=exercise.movement_pattern,
                equipment_used=exercise.equipment_used,
            )
        )

    scored_chunks.sort(key=lambda chunk: (-chunk.score, chunk.title))

    truncated = False
    selected: list[RetrievedContextChunk] = []
    used_chars = 0
    for chunk in scored_chunks[:top_k]:
        projected = used_chars + len(chunk.content)
        if selected and projected > char_budget:
            truncated = True
            break
        selected.append(chunk)
        used_chars = projected

    if len(scored_chunks) > len(selected):
        truncated = True

    return selected, truncated
