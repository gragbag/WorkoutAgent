from api.models import (
    NormalizedAthleteProfile,
    NormalizedConstraints,
    NormalizedPlanRequest,
    NormalizedPreferences,
    PlanRequest,
)


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_free_text(value: str, *, default: str, max_length: int) -> str:
    cleaned = _clean_text(value)
    if not cleaned:
        return default
    return cleaned[:max_length]


def _dedupe_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered_values: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            ordered_values.append(value)

    return ordered_values


def _dedupe_days(days: list[str]) -> list[str]:
    return _dedupe_values(days)


def normalize_plan_request(payload: PlanRequest) -> NormalizedPlanRequest:
    ordered_days = _dedupe_days(payload.available_training_days)
    if len(ordered_days) < payload.days_per_week:
        raise ValueError(
            "available_training_days must include at least days_per_week unique days."
        )

    normalized_days = ordered_days[: payload.days_per_week]
    injuries = _normalize_free_text(
        payload.injuries,
        default="None reported",
        max_length=400,
    )
    notes = _normalize_free_text(
        payload.notes,
        default="No extra athlete notes provided",
        max_length=600,
    )
    normalized_equipment = _dedupe_values(payload.equipment)
    session_length_min = min(payload.session_length_min, payload.session_length_max)
    session_length_max = max(payload.session_length_min, payload.session_length_max)

    return NormalizedPlanRequest(
        athlete_profile=NormalizedAthleteProfile(
            experience=payload.experience,
            age_range=payload.age_range,
            current_activity_level=payload.current_activity_level,
        ),
        constraints=NormalizedConstraints(
            equipment=normalized_equipment,
            days_per_week=payload.days_per_week,
            session_length_min=session_length_min,
            session_length_max=session_length_max,
            available_training_days=normalized_days,
            injuries=injuries,
        ),
        preferences=NormalizedPreferences(
            intensity_preference=payload.intensity_preference,
            notes=notes,
        ),
    )
