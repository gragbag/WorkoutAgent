from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from api.equipment import categories_overlap
from api.models import ExerciseCandidate, NormalizedPlanRequest
from api.rag import build_knowledge_base_entry, build_retrieval_query, score_text_similarity

DATA_PATH = Path(__file__).resolve().parent / "data" / "exercises.json"


@lru_cache(maxsize=1)
def load_exercise_catalog() -> list[ExerciseCandidate]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        raw_items = json.load(file)

    return [ExerciseCandidate.model_validate(item) for item in raw_items]


def get_candidate_exercises(
    normalized: NormalizedPlanRequest, limit: int = 12
) -> list[ExerciseCandidate]:
    catalog = load_exercise_catalog()
    selected_equipment = set(normalized.constraints.equipment)
    scored_exercises: list[tuple[float, ExerciseCandidate]] = []
    query = build_retrieval_query(normalized)

    for exercise in catalog:
        if not categories_overlap(exercise.equipment_used, selected_equipment):
            continue

        score = score_text_similarity(query, build_knowledge_base_entry(exercise))
        scored_exercises.append((score, exercise))

    scored_exercises.sort(key=lambda item: (-item[0], item[1].name))
    return [exercise for _, exercise in scored_exercises[:limit]]
