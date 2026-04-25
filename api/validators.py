from __future__ import annotations

from api.models import PlanResponse, PromptBundle
from api.exercise_library import EQUIPMENT_ALIASES


def validate_plan_response(plan: PlanResponse, prompt_bundle: PromptBundle) -> None:
    allowed_days = set(prompt_bundle.normalized_input.constraints.available_training_days)
    flexible_days = set(prompt_bundle.normalized_input.constraints.flexible_training_days)
    allowed_exercises = {exercise.name for exercise in prompt_bundle.candidate_exercises}
    allowed_equipment_groups = prompt_bundle.normalized_input.constraints.equipment
    allowed_equipment = {
        alias
        for equipment_group in allowed_equipment_groups
        for alias in EQUIPMENT_ALIASES.get(equipment_group, {equipment_group.lower()})
    }

    for day in plan.days:
        if day.day not in allowed_days:
            raise ValueError(f"Plan used an unavailable training day: {day.day}")

        for exercise in day.exercises:
            if allowed_exercises and exercise.name not in allowed_exercises:
                raise ValueError(f"Plan used an exercise outside the retrieved candidate set: {exercise.name}")

            if allowed_equipment and exercise.equipment_used not in allowed_equipment:
                raise ValueError(f"Plan used incompatible equipment for selected setup: {exercise.name}")

    for day in plan.optional_days:
        if day.day not in flexible_days:
            raise ValueError(f"Optional session used a non-flexible day: {day.day}")

        for exercise in day.exercises:
            if allowed_exercises and exercise.name not in allowed_exercises:
                raise ValueError(f"Optional session used an exercise outside the retrieved candidate set: {exercise.name}")

            if allowed_equipment and exercise.equipment_used not in allowed_equipment:
                raise ValueError(f"Optional session used incompatible equipment for selected setup: {exercise.name}")
