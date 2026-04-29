from __future__ import annotations

import csv
import json
import re
from pathlib import Path


SOURCE_PATH = Path(__file__).resolve().parent / "data" / "Workout.csv"
TARGET_PATH = Path(__file__).resolve().parent / "data" / "exercises.json"

TITLE_CLEANUP_RE = re.compile(r"[^a-z0-9]+")
WORD_RE = re.compile(r"[a-z0-9]+")

BODY_PART_MAP = {
    "Chest": "chest",
    "Back": "back",
    "Arms": "arms",
    "Legs": "legs",
    "Shoulders": "shoulders",
    "Abs": "core",
    "Forearms": "forearms",
}

MOVEMENT_SECONDARY_DEFAULTS = {
    "horizontal push": ["triceps", "shoulders"],
    "vertical push": ["triceps", "upper back"],
    "horizontal pull": ["biceps", "rear delts"],
    "vertical pull": ["biceps", "upper back"],
    "squat": ["glutes", "core"],
    "single-leg squat": ["glutes", "core"],
    "hip hinge": ["glutes", "core"],
    "core stability": ["obliques"],
    "arm isolation": ["forearms"],
    "calf raise": [],
    "accessory": [],
}

MOVEMENT_CUE_DEFAULTS = {
    "horizontal push": "Keep your shoulder blades set and press through a steady path.",
    "vertical push": "Brace your torso and press without flaring the ribs.",
    "horizontal pull": "Initiate by pulling the elbows back and squeezing the upper back.",
    "vertical pull": "Drive the elbows down and keep the torso controlled.",
    "squat": "Control the lowering phase and keep pressure through the whole foot.",
    "single-leg squat": "Stay balanced and control knee tracking throughout each rep.",
    "hip hinge": "Keep a neutral spine and hinge through the hips, not the low back.",
    "core stability": "Brace the trunk and avoid using momentum to finish the reps.",
    "arm isolation": "Keep the upper arm stable and move only through the target joint.",
    "calf raise": "Use a full range of motion and pause briefly at the top.",
    "accessory": "Move with control and stop shy of technical breakdown.",
}


def _title_case(name: str) -> str:
    cleaned = " ".join(name.strip().split())
    return cleaned[:1].upper() + cleaned[1:] if cleaned else cleaned


def _dedupe_key(title: str) -> str:
    tokens = WORD_RE.findall(title.lower())
    if tokens and tokens[-1].endswith("s") and len(tokens[-1]) > 3:
        tokens[-1] = tokens[-1][:-1]
    return " ".join(tokens)


def _infer_primary_muscle_group(body_part: str, type_of_muscle: str) -> str:
    if body_part == "Chest":
        return "chest"
    if body_part == "Back":
        return "lower back" if type_of_muscle == "Lower" else "back"
    if body_part == "Arms":
        return "biceps" if type_of_muscle == "Biceps" else "triceps"
    if body_part == "Legs":
        leg_map = {
            "Quadriceps": "legs",
            "Hamstrings": "hamstrings",
            "Glutes": "glutes",
            "Calves": "calves",
        }
        return leg_map.get(type_of_muscle, "legs")
    if body_part == "Shoulders":
        return "shoulders"
    if body_part == "Abs":
        return "core"
    if body_part == "Forearms":
        return "forearms"
    return BODY_PART_MAP.get(body_part, body_part.lower())


def _infer_equipment_used(name: str, body_part: str, type_of_muscle: str) -> str:
    lowered = name.lower()

    if "dumbbell" in lowered:
        if "press" in lowered or "fly" in lowered or "row" in lowered:
            return "Dumbbells / Bench"
        return "Dumbbells"
    if "barbell" in lowered:
        return "Barbell / rack"
    if "bench press" in lowered:
        return "Barbell / rack / Bench"
    if "romanian deadlift" in lowered:
        return "Barbell / rack"
    if "cable" in lowered or "pushdown" in lowered:
        return "Machines / cables"
    if "leg press" in lowered or "leg extension" in lowered or "leg curl" in lowered:
        return "Machines / cables"
    if "preacher curl" in lowered:
        return "Machines / cables"
    if "row" in lowered:
        return "Barbell / rack"
    if "pull-up" in lowered or "pull up" in lowered or "hanging leg raise" in lowered:
        return "Pull-up bar"
    if "plate pinch" in lowered:
        return "Barbell / rack"
    if "towel pull-up" in lowered or "towel pull up" in lowered:
        return "Pull-up bar"
    if "hyperextension" in lowered:
        return "Bench"
    if "military press" in lowered:
        return "Dumbbells"
    if "curl" in lowered or "skull crusher" in lowered or "overhead triceps extension" in lowered:
        return "Dumbbells"
    if "face pull" in lowered:
        return "Machines / cables"
    if "fly" in lowered:
        return "Dumbbells / Bench"
    if (
        "bird dog" in lowered
        or "crunch" in lowered
        or "plank" in lowered
        or "russian twist" in lowered
        or "donkey kick" in lowered
        or "leg raise" in lowered
    ):
        return "Mat / floor space"
    if "dip" in lowered:
        return "Bench"
    if body_part == "Abs":
        return "Mat / floor space"
    return "Bodyweight"


def _infer_movement_pattern(name: str, body_part: str, type_of_muscle: str) -> str:
    lowered = name.lower()

    if "pull-up" in lowered or "pull up" in lowered or "hanging leg raise" in lowered:
        return "vertical pull" if "leg raise" not in lowered else "core stability"
    if "row" in lowered or "face pull" in lowered:
        return "horizontal pull"
    if "military press" in lowered or "overhead triceps extension" in lowered:
        return "vertical push" if "triceps" not in lowered else "arm isolation"
    if "press" in lowered or "push-up" in lowered or "dip" in lowered:
        return "horizontal push"
    if "squat" in lowered or "leg press" in lowered:
        return "squat"
    if "deadlift" in lowered or "hip thrust" in lowered or "hyperextension" in lowered:
        return "hip hinge"
    if "raise" in lowered and body_part == "Shoulders":
        return "accessory"
    if "curl" in lowered or "extension" in lowered or "pushdown" in lowered or "skull crusher" in lowered:
        return "arm isolation"
    if (
        "plank" in lowered
        or "crunch" in lowered
        or "twist" in lowered
        or "bird dog" in lowered
        or "leg raise" in lowered
    ):
        return "core stability"
    if "leg extension" in lowered or "leg curl" in lowered or "fly" in lowered or "crossover" in lowered:
        return "accessory"
    if "calf raise" in lowered:
        return "calf raise"
    return "accessory"


def _infer_secondary_muscles(primary: str, movement_pattern: str, name: str) -> list[str]:
    secondary = MOVEMENT_SECONDARY_DEFAULTS.get(movement_pattern, []).copy()
    lowered = name.lower()

    if primary == "chest":
        if "shoulders" not in secondary:
            secondary.append("shoulders")
        if "triceps" not in secondary and movement_pattern in {"horizontal push", "vertical push"}:
            secondary.append("triceps")
    if primary == "back" and "upper back" not in secondary:
        secondary.append("upper back")
    if primary == "lower back" and "glutes" not in secondary:
        secondary.append("glutes")
    if primary == "legs" and "glutes" not in secondary:
        secondary.append("glutes")
    if primary == "hamstrings" and "glutes" not in secondary:
        secondary.append("glutes")
    if primary == "glutes" and "hamstrings" not in secondary:
        secondary.append("hamstrings")
    if primary == "shoulders" and movement_pattern == "accessory":
        if "upper back" not in secondary and "face pull" in lowered:
            secondary.append("upper back")
        if "triceps" not in secondary and "press" in lowered:
            secondary.append("triceps")
    if primary == "core" and "obliques" not in secondary and "twist" in lowered:
        secondary.append("obliques")

    deduped: list[str] = []
    for muscle in secondary:
        if muscle and muscle != primary and muscle not in deduped:
            deduped.append(muscle)
    return deduped[:4]


def _infer_contraindications(primary: str, movement_pattern: str, name: str) -> list[str]:
    lowered = name.lower()
    flags: set[str] = set()

    if primary in {"legs", "hamstrings", "glutes", "calves"} or movement_pattern in {
        "squat",
        "single-leg squat",
        "calf raise",
    }:
        flags.add("acute knee pain")
    if movement_pattern == "hip hinge" or primary == "lower back":
        flags.add("acute low-back pain")
    if movement_pattern in {"horizontal push", "vertical push"} or primary == "shoulders":
        flags.add("acute shoulder pain")
    if primary in {"biceps", "triceps", "forearms"} or movement_pattern == "arm isolation":
        flags.add("acute elbow pain")
    if "pull-up" in lowered or "pull up" in lowered:
        flags.add("acute elbow pain")
        flags.add("acute shoulder pain")

    return sorted(flags)


def _build_coaching_cues(
    name: str,
    body_part: str,
    type_of_muscle: str,
    movement_pattern: str,
    sets: str,
    reps: str,
) -> list[str]:
    volume_text = f"Use about {sets} sets of {reps} reps."
    if "second" in sets.lower():
        volume_text = f"Use holds of about {sets} for {reps} round(s)."
    elif "second" in reps.lower():
        volume_text = f"Use about {sets} sets of {reps}."

    cues = [
        (
            f"{name} targets the {type_of_muscle.lower()} area of the "
            f"{body_part.lower()}."
        ),
        volume_text,
        MOVEMENT_CUE_DEFAULTS.get(
            movement_pattern, "Move with control and stop shy of technical breakdown."
        ),
    ]

    lowered = name.lower()
    if "incline" in lowered:
        cues.append("Keep the angle fixed and avoid turning the movement into a flat press.")
    elif "decline" in lowered:
        cues.append("Stay controlled at the bottom and keep the pressing path smooth.")
    elif "face pull" in lowered:
        cues.append("Lead with the elbows and finish with the hands near eye level.")
    elif "romanian deadlift" in lowered:
        cues.append("Keep the bar or dumbbells close and stop when the hamstrings are fully loaded.")
    elif "bird dog" in lowered or "plank" in lowered:
        cues.append("Keep the ribs down and avoid shifting side to side.")

    deduped: list[str] = []
    for cue in cues:
        cue = " ".join(cue.split())
        if cue and cue not in deduped:
            deduped.append(cue)
    return deduped[:3]


def convert_row(row: dict[str, str]) -> dict[str, object]:
    body_part = row["Body Part"].strip()
    type_of_muscle = row["Type of Muscle"].strip()
    name = _title_case(row["Workout"])
    sets = row["Sets"].strip()
    reps = row["Reps per Set"].strip()

    primary = _infer_primary_muscle_group(body_part, type_of_muscle)
    movement_pattern = _infer_movement_pattern(name, body_part, type_of_muscle)

    return {
        "name": name,
        "primary_muscle_group": primary,
        "secondary_muscles": _infer_secondary_muscles(primary, movement_pattern, name),
        "equipment_used": _infer_equipment_used(name, body_part, type_of_muscle),
        "movement_pattern": movement_pattern,
        "coaching_cues": _build_coaching_cues(
            name, body_part, type_of_muscle, movement_pattern, sets, reps
        ),
        "contraindications": _infer_contraindications(primary, movement_pattern, name),
    }


def main() -> None:
    with SOURCE_PATH.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        converted: list[dict[str, object]] = []
        seen_names: set[str] = set()
        skipped_for_duplicate = 0

        for row in reader:
            name = _title_case(row["Workout"])
            dedupe_key = _dedupe_key(name)
            if not dedupe_key or dedupe_key in seen_names:
                skipped_for_duplicate += 1
                continue

            seen_names.add(dedupe_key)
            converted.append(convert_row(row))

    converted.sort(key=lambda item: str(item["name"]))

    with TARGET_PATH.open("w", encoding="utf-8") as file:
        json.dump(converted, file, indent=2)
        file.write("\n")

    print(
        f"Wrote {len(converted)} exercises to {TARGET_PATH} "
        f"(skipped {skipped_for_duplicate} duplicates from {SOURCE_PATH.name})"
    )


if __name__ == "__main__":
    main()
