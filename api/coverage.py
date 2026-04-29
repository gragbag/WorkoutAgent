from __future__ import annotations

from api.models import PlanResponse, SplitPlan

MUSCLE_ALIASES = {
    "arm": "arms",
    "arms": "arms",
    "back": "back",
    "bicep": "biceps",
    "biceps": "biceps",
    "calf": "calves",
    "calves": "calves",
    "chest": "chest",
    "core": "core",
    "forearm": "forearms",
    "forearms": "forearms",
    "glute": "glutes",
    "glutes": "glutes",
    "hamstring": "hamstrings",
    "hamstrings": "hamstrings",
    "lat": "back",
    "lats": "back",
    "leg": "quads",
    "legs": "quads",
    "lower back": "back",
    "middle back": "back",
    "obliques": "core",
    "posterior chain": "hamstrings",
    "quad": "quads",
    "quadriceps": "quads",
    "quads": "quads",
    "rear delts": "shoulders",
    "rear delt": "shoulders",
    "shoulder": "shoulders",
    "shoulders": "shoulders",
    "tricep": "triceps",
    "triceps": "triceps",
    "upper back": "back",
}

KEY_PATTERN_TO_MUSCLES = {
    "accessory press": {"chest", "shoulders", "triceps"},
    "arms": {"biceps", "triceps", "forearms"},
    "biceps": {"biceps"},
    "calves": {"calves"},
    "carry": {"core", "forearms"},
    "compound lower": {"quads", "glutes"},
    "conditioning": set(),
    "core": {"core"},
    "hinge": {"hamstrings", "glutes"},
    "horizontal pull": {"back", "biceps"},
    "horizontal push": {"chest", "shoulders", "triceps"},
    "incline push": {"chest", "shoulders", "triceps"},
    "lateral raise": {"shoulders"},
    "posterior chain": {"hamstrings", "glutes"},
    "pull": {"back", "biceps"},
    "push": {"chest", "shoulders", "triceps"},
    "rear delt": {"shoulders", "back"},
    "single-leg": {"quads", "glutes"},
    "single leg": {"quads", "glutes"},
    "single-leg squat": {"quads", "glutes"},
    "squat": {"quads", "glutes"},
    "triceps": {"triceps"},
    "upper back": {"back"},
    "vertical pull": {"back", "biceps"},
    "vertical push": {"shoulders", "triceps"},
}

FOCUS_HINTS = {
    "arms": {"biceps", "triceps", "forearms"},
    "back": {"back"},
    "biceps": {"biceps"},
    "calf": {"calves"},
    "calves": {"calves"},
    "chest": {"chest"},
    "core": {"core"},
    "glute": {"glutes"},
    "glutes": {"glutes"},
    "hamstring": {"hamstrings"},
    "hamstrings": {"hamstrings"},
    "leg": {"quads", "glutes"},
    "legs": {"quads", "glutes"},
    "quad": {"quads"},
    "quads": {"quads"},
    "shoulder": {"shoulders"},
    "shoulders": {"shoulders"},
    "triceps": {"triceps"},
}


def normalize_muscle_label(label: str) -> str | None:
    normalized = " ".join(label.lower().replace("_", " ").replace("-", " ").split())
    return MUSCLE_ALIASES.get(normalized, normalized or None)


def _muscles_from_key_pattern(pattern: str) -> set[str]:
    normalized = " ".join(pattern.lower().replace("_", " ").replace("-", " ").split())
    if normalized in KEY_PATTERN_TO_MUSCLES:
        return set(KEY_PATTERN_TO_MUSCLES[normalized])

    inferred: set[str] = set()
    for keyword, muscles in KEY_PATTERN_TO_MUSCLES.items():
        if keyword and keyword in normalized:
            inferred.update(muscles)
    return inferred


def _muscles_from_focus(focus: str) -> set[str]:
    normalized = " ".join(focus.lower().replace("_", " ").replace("-", " ").split())
    inferred: set[str] = set()
    for keyword, muscles in FOCUS_HINTS.items():
        if keyword in normalized:
            inferred.update(muscles)
    return inferred


def expected_weekly_coverage(split_plan: SplitPlan | None) -> set[str]:
    if split_plan is None:
        return set()

    expected: set[str] = set()
    for day in split_plan.days:
        expected.update(_muscles_from_focus(day.focus))
        for pattern in day.key_patterns:
            expected.update(_muscles_from_key_pattern(pattern))
    return expected


def actual_weekly_coverage(plan: PlanResponse) -> set[str]:
    covered: set[str] = set()
    for day in plan.days:
        for exercise in day.exercises:
            primary = normalize_muscle_label(exercise.primary_muscle_group)
            if primary:
                covered.add(primary)
            for muscle in exercise.secondary_muscles:
                normalized = normalize_muscle_label(muscle)
                if normalized:
                    covered.add(normalized)
    return covered


def missing_weekly_coverage(
    plan: PlanResponse,
    split_plan: SplitPlan | None,
) -> list[str]:
    expected = expected_weekly_coverage(split_plan)
    if not expected:
        return []

    covered = actual_weekly_coverage(plan)
    missing = sorted(expected - covered)
    return missing
