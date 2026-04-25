from __future__ import annotations

from api.models import NormalizedPlanRequest

STAPLE_EXERCISE_KEYWORDS = (
    "bench press",
    "chest press",
    "push-up",
    "overhead press",
    "shoulder press",
    "lat pulldown",
    "pull-up",
    "row",
    "seated row",
    "cable row",
    "goblet squat",
    "squat",
    "split squat",
    "lunge",
    "romanian deadlift",
    "deadlift",
    "hip thrust",
    "glute bridge",
    "leg press",
    "leg curl",
    "leg extension",
    "curl",
    "triceps extension",
    "plank",
)

LOW_QUALITY_NAME_TERMS = (
    "gethin",
    "total fitness",
    "variation",
    "reactive",
)


def score_exercise_name(name: str) -> int:
    lowered = name.lower()
    score = 0

    if any(keyword in lowered for keyword in STAPLE_EXERCISE_KEYWORDS):
        score += 3

    if any(keyword in lowered for keyword in LOW_QUALITY_NAME_TERMS):
        score -= 3

    if "(" in lowered and ")" in lowered:
        score -= 1

    return score


def get_split_template(normalized: NormalizedPlanRequest) -> list[str]:
    days = normalized.constraints.days_per_week
    experience = normalized.athlete_profile.experience
    intensity = normalized.preferences.intensity_preference
    cardio = normalized.preferences.cardio_preference

    if days == 2:
        return ["Full body A", "Full body B"]

    if days == 3:
        if experience != "Beginner" and intensity != "Light":
            return ["Push", "Pull", "Legs"]
        return ["Full body", "Upper body", "Lower body"]

    if days == 4:
        if cardio == "Enjoys cardio":
            return ["Upper body", "Lower body", "Upper body", "Conditioning + core"]
        return ["Upper body", "Lower body", "Upper body", "Lower body"]

    if days == 5:
        return ["Push", "Pull", "Legs", "Upper accessory", "Lower accessory"]

    return ["Push", "Pull", "Legs", "Push", "Pull", "Legs"]


def get_staple_exercise_hints(normalized: NormalizedPlanRequest) -> list[str]:
    equipment = set(normalized.constraints.equipment)
    hints: list[str] = []

    if {"Bench", "Dumbbells"} & equipment:
        hints.extend(["dumbbell bench press", "incline dumbbell bench press"])

    if "Barbell / rack" in equipment:
        hints.extend(["barbell squat", "barbell bench press", "romanian deadlift"])

    if "Machines / cables" in equipment:
        hints.extend(["lat pulldown", "seated cable row", "machine chest press", "leg press"])

    if "Resistance bands" in equipment and not hints:
        hints.extend(["band row", "band chest press", "band squat"])

    if "Bodyweight" in equipment:
        hints.extend(["push-up", "split squat", "glute bridge", "plank"])

    if normalized.constraints.injuries != "None reported":
        hints.append("pain-free substitutions are preferred over risky variations")

    seen: set[str] = set()
    ordered_hints: list[str] = []
    for hint in hints:
        if hint not in seen:
            seen.add(hint)
            ordered_hints.append(hint)

    return ordered_hints[:8]
