from __future__ import annotations

import re

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
from api.models import ExerciseCandidate, PlanResponse, PromptBundle, SplitPlan

NAME_TOKEN_RE = re.compile(r"[a-z0-9]+")
SIMILARITY_STOPWORDS = {
    "alternating",
    "assisted",
    "bar",
    "bodyweight",
    "close",
    "dumbbell",
    "grip",
    "incline",
    "machine",
    "narrow",
    "neutral",
    "pronated",
    "rope",
    "seated",
    "single",
    "single-arm",
    "single-leg",
    "standing",
    "supinated",
    "wide",
    "weighted",
}
def _is_equipment_compatible(
    reported_equipment: str,
    selected_equipment: set[str],
    candidate_equipment: str | None = None,
) -> bool:
    if not selected_equipment:
        return True

    if categories_overlap(reported_equipment, selected_equipment):
        return True

    if candidate_equipment and categories_overlap(candidate_equipment, selected_equipment):
        return True

    return False


def _normalize_exercise_tokens(name: str) -> set[str]:
    tokens = set(NAME_TOKEN_RE.findall(name.lower()))
    normalized: set[str] = set()

    for token in tokens:
        normalized.add(token)
        if token.endswith("s") and len(token) > 3:
            normalized.add(token[:-1])
        if token.endswith("es") and len(token) > 4:
            normalized.add(token[:-2])

    return normalized


def _base_similarity_tokens(name: str) -> set[str]:
    return {
        token
        for token in _normalize_exercise_tokens(name)
        if token not in SIMILARITY_STOPWORDS and len(token) > 1
    }

def _has_injury_conflict(
    exercise_name: str,
    movement_pattern: str,
    primary_muscle_group: str,
    contraindications: list[str],
    injury_flags: set[str],
) -> bool:
    if not injury_flags:
        return False

    if contraindications_conflict(contraindications, injury_flags):
        return True

    lowered_name = exercise_name.lower()
    lowered_pattern = movement_pattern.lower()
    primary = primary_muscle_group.lower()

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


def _find_similar_exercise_pair(exercise_names: list[str]) -> tuple[str, str] | None:
    seen: list[tuple[str, set[str]]] = []

    for name in exercise_names:
        tokens = _base_similarity_tokens(name)
        if not tokens:
            continue

        for other_name, other_tokens in seen:
            if not other_tokens:
                continue

            overlap = tokens & other_tokens
            similarity = len(overlap) / max(len(tokens), len(other_tokens))
            if similarity >= 0.8:
                return other_name, name

        seen.append((name, tokens))

    return None


def _find_candidate_match(
    exercise_name: str,
    candidates: list[ExerciseCandidate],
    selected_equipment: set[str],
    reported_equipment: str,
) -> ExerciseCandidate | None:
    exact_lower = exercise_name.lower()
    for candidate in candidates:
        if candidate.name.lower() == exact_lower:
            return candidate

    target_tokens = _normalize_exercise_tokens(exercise_name)
    if not target_tokens:
        return None

    scored_matches: list[tuple[int, int, ExerciseCandidate]] = []
    for candidate in candidates:
        candidate_tokens = _normalize_exercise_tokens(candidate.name)
        if not target_tokens <= candidate_tokens:
            continue

        equipment_score = 0
        if categories_overlap(candidate.equipment_used, selected_equipment):
            equipment_score += 2
        if reported_equipment and categories_overlap(candidate.equipment_used, reported_equipment):
            equipment_score += 1

        scored_matches.append((equipment_score, len(candidate_tokens), candidate))

    if not scored_matches:
        return None

    scored_matches.sort(key=lambda item: (-item[0], item[1], item[2].name))
    return scored_matches[0][2]


def validate_plan_response(
    plan: PlanResponse,
    prompt_bundle: PromptBundle,
    split_plan: SplitPlan | None = None,
) -> None:
    constraints = prompt_bundle.normalized_input.constraints
    allowed_days = set(constraints.available_training_days)
    candidates = prompt_bundle.candidate_exercises
    selected_equipment = set(constraints.equipment)
    injury_flags = _infer_injury_flags(constraints.injuries)

    if len(plan.days) != constraints.days_per_week:
        raise ValueError("Plan returned the wrong number of required sessions.")

    required_day_names = [day.day for day in plan.days]
    if len(required_day_names) != len(set(required_day_names)):
        raise ValueError("Plan used duplicate required training days.")

    if set(required_day_names) != allowed_days:
        raise ValueError("Plan days must match the selected required training days exactly.")

    for day in plan.days:
        if day.duration_minutes > constraints.session_length_max:
            raise ValueError(
                f"Plan session exceeds the athlete's max session length: {day.day}"
            )

        similar_pair = _find_similar_exercise_pair([exercise.name for exercise in day.exercises])
        if similar_pair:
            raise ValueError(
                f"Plan used near-duplicate exercises in the same session on {day.day}: "
                f"{similar_pair[0]} and {similar_pair[1]}"
            )

        pulling_count = sum(
            1
            for exercise in day.exercises
            if exercise.movement_pattern in {"horizontal pull", "vertical pull"}
        )
        direct_biceps_count = sum(
            1
            for exercise in day.exercises
            if exercise.primary_muscle_group.lower() == "biceps"
        )
        if pulling_count >= 2 and direct_biceps_count == 0:
            raise ValueError(
                f"Plan under-covered biceps on a pull-heavy day: {day.day}"
            )

        for exercise in day.exercises:
            candidate_match = _find_candidate_match(
                exercise.name,
                candidates,
                selected_equipment,
                exercise.equipment_used,
            )
            if not _is_equipment_compatible(
                exercise.equipment_used,
                selected_equipment,
                candidate_match.equipment_used if candidate_match else None,
            ):
                raise ValueError(
                    f"Plan used incompatible equipment for selected setup: {exercise.name}"
                )
            contraindications = candidate_match.contraindications if candidate_match else []
            if _has_injury_conflict(
                exercise.name,
                exercise.movement_pattern,
                exercise.primary_muscle_group,
                contraindications,
                injury_flags,
            ):
                raise ValueError(
                    f"Plan used an exercise that likely conflicts with the athlete's injuries: {exercise.name}"
                )
