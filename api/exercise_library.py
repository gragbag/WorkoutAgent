from __future__ import annotations

import json
from pathlib import Path

from api.models import ExerciseCandidate, NormalizedPlanRequest
from api.planning_knowledge import score_exercise_name

DATA_PATH = Path(__file__).resolve().parent / "data" / "exercises.json"

EQUIPMENT_ALIASES = {
    "Bodyweight": {"bodyweight"},
    "Dumbbells": {"dumbbell"},
    "Resistance bands": {"resistance band", "bands"},
    "Bench": {"bench"},
    "Barbell / rack": {"barbell", "ez curl bar"},
    "Machines / cables": {"machine", "cable machine"},
    "Cardio equipment": {"other"},
    "Kettlebells": {"kettlebell"},
    "Pull-up bar": {"bodyweight"},
    "Mat / floor space": {"mat", "exercise ball", "bodyweight"},
}

INJURY_KEYWORDS = {
    "shoulder": {"shoulder pain", "acute shoulder pain"},
    "knee": {"acute knee pain"},
    "back": {"acute low-back pain"},
    "low back": {"acute low-back pain"},
    "wrist": {"wrist pain"},
}


def load_exercise_catalog() -> list[ExerciseCandidate]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        raw_items = json.load(file)

    return [ExerciseCandidate.model_validate(item) for item in raw_items]


def _injury_tokens(injuries: str) -> set[str]:
    lowered = injuries.lower()
    return {
        contraindication
        for keyword, contraindications in INJURY_KEYWORDS.items()
        if keyword in lowered
        for contraindication in contraindications
    }


def get_candidate_exercises(
    normalized: NormalizedPlanRequest, limit: int = 12
) -> list[ExerciseCandidate]:
    catalog = load_exercise_catalog()
    allowed_equipment = {
        alias
        for equipment_group in normalized.constraints.equipment
        for alias in EQUIPMENT_ALIASES.get(equipment_group, {equipment_group.lower()})
    }
    experience = normalized.athlete_profile.experience.lower()
    injury_flags = _injury_tokens(normalized.constraints.injuries)
    preferred_patterns: set[str] = set()
    intensity_preference = normalized.preferences.intensity_preference
    cardio_preference = normalized.preferences.cardio_preference
    variety_preference = normalized.preferences.variety_preference

    if intensity_preference == "Challenging":
        preferred_patterns.update(
            {"squat", "horizontal push", "horizontal pull", "hip hinge", "vertical pull"}
        )
    elif intensity_preference == "Light":
        preferred_patterns.update({"core stability", "carry", "anti-rotation", "single-leg squat"})
    else:
        preferred_patterns.update({"horizontal push", "horizontal pull", "hip hinge", "core stability"})

    if cardio_preference == "Enjoys cardio":
        preferred_patterns.update({"carry", "single-leg squat", "anti-rotation"})
    elif cardio_preference == "Low-impact only":
        preferred_patterns.update({"core stability", "horizontal pull", "hip hinge"})

    scored: list[tuple[int, ExerciseCandidate]] = []

    for exercise in catalog:
        if exercise.equipment_used not in allowed_equipment:
            continue

        if injury_flags.intersection(set(exercise.contraindications)):
            continue

        score = 0

        if exercise.movement_pattern in preferred_patterns:
            score += 3

        if exercise.difficulty == experience:
            score += 3
        elif experience == "advanced":
            score += 2
        elif experience == "intermediate" and exercise.difficulty in {"beginner", "intermediate"}:
            score += 2
        elif experience == "beginner" and exercise.difficulty == "beginner":
            score += 2

        if normalized.constraints.equipment_details:
            details_lower = normalized.constraints.equipment_details.lower()
            if exercise.equipment_used in details_lower:
                score += 1

        if cardio_preference == "Prefer minimal cardio" and exercise.movement_pattern in {
            "carry",
            "single-leg squat",
        }:
            score -= 1

        if variety_preference == "Keep it simple" and exercise.difficulty == "beginner":
            score += 1
        elif variety_preference == "Mix it up" and len(exercise.secondary_muscles) >= 2:
            score += 1

        score += score_exercise_name(exercise.name)

        scored.append((score, exercise))

    scored.sort(key=lambda item: (-item[0], item[1].name))
    return [exercise for _, exercise in scored[:limit]]
