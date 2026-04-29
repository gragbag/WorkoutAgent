from __future__ import annotations

import re

from api.models import SplitPlan

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
}

FOCUS_ALIASES = {
    "upper": "upper",
    "upper body": "upper",
    "lower": "lower",
    "lower body": "lower",
    "full body": "full_body",
    "full-body": "full_body",
    "push": "push",
    "pull": "pull",
    "legs": "legs",
    "leg": "legs",
    "arms": "arms",
    "core": "core",
}

LOWER_KEY_PATTERNS = {
    "squat",
    "hinge",
    "single-leg",
    "single leg",
    "single-leg squat",
    "compound lower",
    "posterior chain",
    "calves",
}
UPPER_KEY_PATTERNS = {
    "horizontal push",
    "vertical push",
    "horizontal pull",
    "vertical pull",
    "upper back",
    "rear delt",
    "lateral raise",
    "accessory press",
    "arms",
    "biceps",
    "triceps",
    "forearms",
    "incline push",
}


def _all_number_tokens() -> str:
    return "|".join([str(value) for value in range(1, 8)] + list(NUMBER_WORDS.keys()))


COUNT_PATTERN = re.compile(
    rf"\b(?P<count>{_all_number_tokens()})\s+"
    r"(?P<focus>upper body|lower body|full body|full-body|upper|lower|push|pull|legs|leg|arms|core)\b",
    re.IGNORECASE,
)


def _parse_count(token: str) -> int | None:
    lowered = token.lower()
    if lowered.isdigit():
        value = int(lowered)
        return value if 1 <= value <= 7 else None
    return NUMBER_WORDS.get(lowered)


def extract_requested_focus_counts(notes: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in COUNT_PATTERN.finditer(notes):
        count = _parse_count(match.group("count"))
        focus = FOCUS_ALIASES.get(match.group("focus").lower())
        if count is None or not focus:
            continue
        counts[focus] = count
    return counts


def render_requested_focus_counts(notes: str) -> str:
    counts = extract_requested_focus_counts(notes)
    if not counts:
        return ""

    ordered = [f"{focus}={count}" for focus, count in sorted(counts.items())]
    return "\nDetected requested weekly split distribution:\n- " + "\n- ".join(ordered)


def _day_focus_tags(focus: str, key_patterns: list[str]) -> set[str]:
    normalized_focus = focus.lower().replace("-", " ")
    tags: set[str] = set()

    for label, canonical in FOCUS_ALIASES.items():
        if label in normalized_focus:
            tags.add(canonical)

    normalized_patterns = {" ".join(pattern.lower().replace("-", " ").split()) for pattern in key_patterns}
    if normalized_patterns & LOWER_KEY_PATTERNS:
        tags.add("lower")
        tags.add("legs")
    if normalized_patterns & UPPER_KEY_PATTERNS:
        tags.add("upper")

    return tags


def count_split_focuses(split_plan: SplitPlan) -> dict[str, int]:
    counts: dict[str, int] = {}
    for day in split_plan.days:
        tags = _day_focus_tags(day.focus, day.key_patterns)
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def requested_focus_mismatches(notes: str, split_plan: SplitPlan) -> list[str]:
    requested = extract_requested_focus_counts(notes)
    if not requested:
        return []

    actual = count_split_focuses(split_plan)
    mismatches: list[str] = []
    for focus, requested_count in requested.items():
        actual_count = actual.get(focus, 0)
        if actual_count != requested_count:
            mismatches.append(
                f"requested {requested_count} {focus} day(s) but the split has {actual_count}"
            )
    return mismatches
