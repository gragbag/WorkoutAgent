from __future__ import annotations

from api.equipment import categories_overlap
from api.models import PlanResponse, PromptBundle


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


def validate_plan_response(plan: PlanResponse, prompt_bundle: PromptBundle) -> None:
    constraints = prompt_bundle.normalized_input.constraints
    allowed_days = set(constraints.available_training_days)
    flexible_days = set(constraints.flexible_training_days)
    candidate_by_name = {
        exercise.name: exercise for exercise in prompt_bundle.candidate_exercises
    }
    selected_equipment = set(constraints.equipment)

    if len(plan.days) != constraints.days_per_week:
        raise ValueError("Plan returned the wrong number of required sessions.")

    required_day_names = [day.day for day in plan.days]
    if len(required_day_names) != len(set(required_day_names)):
        raise ValueError("Plan used duplicate required training days.")

    optional_day_names = [day.day for day in plan.optional_days]
    if len(optional_day_names) != len(set(optional_day_names)):
        raise ValueError("Plan used duplicate optional training days.")

    if set(required_day_names) != allowed_days:
        raise ValueError("Plan days must match the selected required training days exactly.")

    if set(optional_day_names) - flexible_days:
        raise ValueError("Plan used optional training days outside the flexible day set.")

    for day in plan.days:
        if not constraints.session_length_min <= day.duration_minutes <= constraints.session_length_max:
            raise ValueError(f"Plan used an out-of-range session duration on {day.day}.")

        for exercise in day.exercises:
            candidate_equipment = candidate_by_name.get(exercise.name)
            if not _is_equipment_compatible(
                exercise.equipment_used,
                selected_equipment,
                candidate_equipment.equipment_used if candidate_equipment else None,
            ):
                raise ValueError(
                    f"Plan used incompatible equipment for selected setup: {exercise.name}"
                )

    for day in plan.optional_days:
        if not constraints.session_length_min <= day.duration_minutes <= constraints.session_length_max:
            raise ValueError(f"Optional session used an out-of-range duration on {day.day}.")

        for exercise in day.exercises:
            candidate_equipment = candidate_by_name.get(exercise.name)
            if not _is_equipment_compatible(
                exercise.equipment_used,
                selected_equipment,
                candidate_equipment.equipment_used if candidate_equipment else None,
            ):
                raise ValueError(
                    f"Optional session used incompatible equipment for selected setup: {exercise.name}"
                )
