from api.models import (
    NormalizedAthleteProfile,
    NormalizedConstraints,
    NormalizedPlanRequest,
    NormalizedPreferences,
    PlanRequest,
)

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def _dedupe_days(days: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered_days: list[str] = []

    for day in days:
        if day not in seen:
            seen.add(day)
            ordered_days.append(day)

    return ordered_days


def normalize_plan_request(payload: PlanRequest) -> NormalizedPlanRequest:
    ordered_days = _dedupe_days(payload.available_training_days)

    for default_day in DAY_ORDER:
        if len(ordered_days) >= payload.days_per_week:
            break
        if default_day not in ordered_days:
            ordered_days.append(default_day)

    normalized_days = ordered_days[: payload.days_per_week]
    flexible_days = [
        day
        for day in _dedupe_days(payload.flexible_training_days)
        if day not in normalized_days
    ][:3]

    injuries = _clean_text(payload.injuries) or "None reported"
    equipment_details = _clean_text(payload.equipment_details) or "No extra equipment details provided"
    notes = _clean_text(payload.notes) or "No extra athlete notes provided"

    return NormalizedPlanRequest(
        athlete_profile=NormalizedAthleteProfile(
            experience=payload.experience,
            age_range=payload.age_range,
            height_feet=payload.height_feet,
            height_inches=payload.height_inches,
            weight_lbs=payload.weight_lbs,
            current_activity_level=payload.current_activity_level,
        ),
        constraints=NormalizedConstraints(
            equipment=payload.equipment,
            workout_location=payload.workout_location,
            equipment_details=equipment_details,
            days_per_week=payload.days_per_week,
            session_length=payload.session_length,
            available_training_days=normalized_days,
            flexible_training_days=flexible_days,
            injuries=injuries,
        ),
        preferences=NormalizedPreferences(
            cardio_preference=payload.cardio_preference,
            intensity_preference=payload.intensity_preference,
            variety_preference=payload.variety_preference,
            notes=notes,
        ),
    )
