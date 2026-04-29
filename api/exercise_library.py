from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from api.equipment import categories_overlap
from api.injury_rules import (
    KNEE_STRESS_MARKERS,
    LOW_BACK_STRESS_MARKERS,
    SHOULDER_RELATED_PRIMARYS,
    SHOULDER_STRESS_MARKERS,
    SHOULDER_STRESS_PATTERNS,
    contraindications_conflict,
    infer_injury_flags,
)
from api.models import ExerciseCandidate, NormalizedPlanRequest
from api.rag import build_knowledge_base_entry, build_retrieval_query, score_text_similarity

DATA_PATH = Path(__file__).resolve().parent / "data" / "exercises.json"
NON_MAIN_MOVEMENT_PATTERNS = {"carry"}
CORE_PATTERN = "core stability"


@lru_cache(maxsize=1)
def load_exercise_catalog() -> list[ExerciseCandidate]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        raw_items = json.load(file)

    return [ExerciseCandidate.model_validate(item) for item in raw_items]


def _is_main_work_exercise(exercise: ExerciseCandidate) -> bool:
    if exercise.movement_pattern in NON_MAIN_MOVEMENT_PATTERNS:
        return False

    return True

def _has_injury_conflict(exercise: ExerciseCandidate, injury_flags: set[str]) -> bool:
    if not injury_flags:
        return False

    if contraindications_conflict(exercise.contraindications, injury_flags):
        return True

    lowered_name = exercise.name.lower()
    lowered_pattern = exercise.movement_pattern.lower()
    primary = exercise.primary_muscle_group.lower()

    if "acute knee pain" in injury_flags:
        if any(marker in lowered_name for marker in KNEE_STRESS_MARKERS):
            return True
        if primary in {"legs", "hamstrings", "glutes", "calves"} and lowered_pattern in {
            "squat",
            "single-leg squat",
        }:
            return True

    if "acute low-back pain" in injury_flags:
        if any(marker in lowered_name for marker in LOW_BACK_STRESS_MARKERS):
            return True
        if lowered_pattern == "hip hinge" or primary == "lower back":
            return True

    if "acute shoulder pain" in injury_flags:
        if any(marker in lowered_name for marker in SHOULDER_STRESS_MARKERS):
            return True
        if lowered_pattern in SHOULDER_STRESS_PATTERNS:
            return True
        if primary in SHOULDER_RELATED_PRIMARYS:
            return True

    return False


def get_candidate_exercises(
    normalized: NormalizedPlanRequest, limit: int = 12
) -> list[ExerciseCandidate]:
    catalog = load_exercise_catalog()
    selected_equipment = set(normalized.constraints.equipment)
    injury_flags = infer_injury_flags(normalized.constraints.injuries)
    scored_exercises: list[tuple[float, ExerciseCandidate]] = []
    query = build_retrieval_query(normalized)

    for exercise in catalog:
        if not _is_main_work_exercise(exercise):
            continue

        if not categories_overlap(exercise.equipment_used, selected_equipment):
            continue

        if _has_injury_conflict(exercise, injury_flags):
            continue

        score = score_text_similarity(query, build_knowledge_base_entry(exercise))
        if exercise.movement_pattern == CORE_PATTERN and "core" not in normalized.preferences.notes.lower():
            score -= 0.12
        scored_exercises.append((score, exercise))

    scored_exercises.sort(key=lambda item: (-item[0], item[1].name))
    return [exercise for _, exercise in scored_exercises[:limit]]
