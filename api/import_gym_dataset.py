from __future__ import annotations

import csv
import json
from pathlib import Path

from api.equipment import canonicalize_equipment_label


SOURCE_PATH = Path(__file__).resolve().parent / "data" / "megaGymDataset.csv"
TARGET_PATH = Path(__file__).resolve().parent / "data" / "exercises.json"

BODY_PART_MAP = {
    "Abdominals": "core",
    "Abductors": "glutes",
    "Adductors": "legs",
    "Biceps": "biceps",
    "Calves": "calves",
    "Chest": "chest",
    "Forearms": "forearms",
    "Glutes": "glutes",
    "Hamstrings": "hamstrings",
    "Lats": "back",
    "Lower Back": "lower back",
    "Middle Back": "back",
    "Neck": "neck",
    "Quadriceps": "legs",
    "Shoulders": "shoulders",
    "Traps": "upper back",
    "Triceps": "triceps",
}

LEVEL_MAP = {
    "Beginner": "beginner",
    "Intermediate": "intermediate",
    "Expert": "advanced",
}

GOAL_RULES = {
    "Strength": ["Build muscle", "Stay consistent"],
    "Powerlifting": ["Build muscle"],
    "Olympic Weightlifting": ["Build muscle", "Improve endurance"],
    "Plyometrics": ["Improve endurance", "Lose fat"],
    "Cardio": ["Lose fat", "Improve endurance"],
    "Stretching": ["Stay consistent", "Improve endurance"],
    "Strongman": ["Build muscle", "Lose fat"],
}

MOVEMENT_RULES = [
    ("squat", "squat"),
    ("lunge", "single-leg squat"),
    ("row", "horizontal pull"),
    ("pulldown", "vertical pull"),
    ("pull-up", "vertical pull"),
    ("chin-up", "vertical pull"),
    ("press", "horizontal push"),
    ("push-up", "horizontal push"),
    ("curl", "arm isolation"),
    ("extension", "arm isolation"),
    ("deadlift", "hip hinge"),
    ("hinge", "hip hinge"),
    ("carry", "carry"),
    ("walk", "carry"),
    ("crunch", "core stability"),
    ("plank", "core stability"),
    ("raise", "accessory"),
]

CONTRAINDICATION_RULES = {
    "shoulders": ["acute shoulder pain"],
    "shoulder": ["acute shoulder pain"],
    "lower back": ["acute low-back pain"],
    "back": ["acute low-back pain"],
    "quadriceps": ["acute knee pain"],
    "hamstrings": ["acute knee pain"],
    "glutes": ["acute knee pain"],
    "chest": ["acute shoulder pain"],
    "triceps": ["acute elbow pain"],
    "biceps": ["acute elbow pain"],
}


def _normalize_title(title: str) -> str:
    title = title.strip()
    if not title:
        return title
    return title[0].upper() + title[1:]


def _infer_movement_pattern(title: str, description: str, body_part: str) -> str:
    haystack = f"{title} {description}".lower()
    for keyword, pattern in MOVEMENT_RULES:
        if keyword in haystack:
            return pattern

    if body_part in {"core", "abdominals"}:
        return "core stability"
    if body_part in {"legs", "quadriceps"}:
        return "squat"
    if body_part in {"back", "lats", "middle back"}:
        return "horizontal pull"
    if body_part == "chest":
        return "horizontal push"
    return "accessory"


def _infer_secondary_muscles(primary: str, movement_pattern: str) -> list[str]:
    defaults = {
        "horizontal push": ["triceps", "shoulders"],
        "vertical pull": ["biceps", "upper back"],
        "horizontal pull": ["biceps", "rear delts"],
        "squat": ["glutes", "core"],
        "single-leg squat": ["glutes", "core"],
        "hip hinge": ["glutes", "core"],
        "carry": ["core", "upper back"],
        "core stability": ["obliques"],
        "arm isolation": ["forearms"],
        "accessory": [],
    }

    secondary = defaults.get(movement_pattern, []).copy()

    if primary == "shoulders" and "triceps" not in secondary:
        secondary.append("triceps")
    if primary == "chest" and "shoulders" not in secondary:
        secondary.append("shoulders")
    if primary == "legs" and "glutes" not in secondary:
        secondary.append("glutes")

    return secondary[:4]


def _infer_contraindications(primary: str, title: str) -> list[str]:
    flags = set(CONTRAINDICATION_RULES.get(primary, []))
    lowered_title = title.lower()

    if "overhead" in lowered_title:
        flags.add("acute shoulder pain")
    if "squat" in lowered_title or "lunge" in lowered_title:
        flags.add("acute knee pain")
    if "deadlift" in lowered_title:
        flags.add("acute low-back pain")

    return sorted(flags)


def _coaching_cues(description: str) -> list[str]:
    cues = []

    summary = " ".join(description.split())
    if summary:
        cues.append(summary[:110].rstrip())

    lowered = description.lower()
    if "control" in lowered:
        cues.append("Keep the movement controlled throughout each rep.")
    elif "pause" in lowered:
        cues.append("Pause briefly in the strongest position.")
    else:
        cues.append("Move with control and stop shy of technical breakdown.")

    deduped = []
    for cue in cues:
        if cue and cue not in deduped:
            deduped.append(cue)

    return deduped[:3]


def convert_row(row: dict[str, str]) -> dict[str, object]:
    title = _normalize_title(row["Title"])
    description = row["Desc"].strip()
    exercise_type = row["Type"].strip()
    body_part_raw = row["BodyPart"].strip()
    body_part = BODY_PART_MAP.get(body_part_raw, body_part_raw.lower())
    equipment_used = canonicalize_equipment_label(row["Equipment"].strip())
    difficulty = LEVEL_MAP.get(row["Level"].strip(), "intermediate")
    movement_pattern = _infer_movement_pattern(title, description, body_part)

    return {
        "name": title,
        "primary_muscle_group": body_part,
        "secondary_muscles": _infer_secondary_muscles(body_part, movement_pattern),
        "equipment_used": equipment_used,
        "difficulty": difficulty,
        "movement_pattern": movement_pattern,
        "suitable_goals": GOAL_RULES.get(exercise_type, ["Stay consistent"]),
        "coaching_cues": _coaching_cues(description),
        "contraindications": _infer_contraindications(body_part, title),
    }


def main() -> None:
    with SOURCE_PATH.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        converted = []
        seen_names = set()

        for row in reader:
            title = _normalize_title(row["Title"])
            if not title or title in seen_names:
                continue

            seen_names.add(title)
            converted.append(convert_row(row))

    converted.sort(key=lambda item: item["name"])

    with TARGET_PATH.open("w", encoding="utf-8") as file:
        json.dump(converted, file, indent=2)
        file.write("\n")

    print(f"Wrote {len(converted)} exercises to {TARGET_PATH}")


if __name__ == "__main__":
    main()
