from __future__ import annotations

from typing import Iterable

CANONICAL_EQUIPMENT_CATEGORIES = (
    "Bodyweight",
    "Dumbbells",
    "Resistance bands",
    "Bench",
    "Barbell / rack",
    "Machines / cables",
    "Cardio equipment",
    "Kettlebells",
    "Pull-up bar",
    "Mat / floor space",
)


def _tokenize_equipment_text(value: str) -> set[str]:
    lowered = value.strip().lower()
    if not lowered:
        return set()

    cleaned = "".join(character if character.isalnum() else " " for character in lowered)
    raw_tokens = [token for token in cleaned.split() if token]
    tokens: set[str] = set()

    for token in raw_tokens:
        tokens.add(token)
        if token.endswith("s") and len(token) > 3:
            tokens.add(token[:-1])
        if token.endswith("es") and len(token) > 4:
            tokens.add(token[:-2])

    return tokens


def infer_equipment_categories(value: str) -> set[str]:
    tokens = _tokenize_equipment_text(value)
    categories: set[str] = set()

    if not tokens:
        return categories

    if {"bodyweight", "body", "none"} & tokens:
        categories.add("Bodyweight")
    if {"dumbbell", "db"} & tokens:
        categories.add("Dumbbells")
    if {"band", "resistance", "mini"} & tokens:
        categories.add("Resistance bands")
    if {"bench"} & tokens:
        categories.add("Bench")
    if {"barbell", "rack", "smith", "ez", "curl"} & tokens:
        categories.add("Barbell / rack")
    if {"machine", "cable", "pulley"} & tokens:
        categories.add("Machines / cables")
    if {
        "cardio",
        "treadmill",
        "bike",
        "bicycle",
        "cycle",
        "rower",
        "rowing",
        "elliptical",
        "stair",
        "stepmill",
        "stepper",
    } & tokens:
        categories.add("Cardio equipment")
    if {"kettlebell", "kb"} & tokens:
        categories.add("Kettlebells")
    if {"pullup", "chinup"} & tokens or {"pull", "up", "bar"} <= tokens:
        categories.add("Pull-up bar")
    if {"mat", "floor", "yoga", "ball"} & tokens:
        categories.add("Mat / floor space")

    return categories


def canonicalize_equipment_label(value: str) -> str:
    categories = infer_equipment_categories(value)
    if len(categories) == 1:
        return next(iter(categories))
    return value.strip().lower()


def categories_overlap(left: str | Iterable[str], right: str | Iterable[str]) -> bool:
    left_categories = (
        set(left)
        if not isinstance(left, str)
        else infer_equipment_categories(left)
    )
    right_categories = (
        set(right)
        if not isinstance(right, str)
        else infer_equipment_categories(right)
    )

    if not left_categories or not right_categories:
        return False

    return bool(left_categories & right_categories)
