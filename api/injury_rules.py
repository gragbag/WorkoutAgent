from __future__ import annotations

INJURY_KEYWORDS = {
    "acute knee pain": {"knee", "knees", "patella", "acl", "mcl", "meniscus"},
    "acute low-back pain": {"low back", "lower back", "back", "spine", "disc"},
    "acute shoulder pain": {"shoulder", "shoulders", "rotator cuff", "labrum"},
    "acute elbow pain": {"elbow", "tendonitis", "tendinitis"},
}

KNEE_STRESS_MARKERS = {
    "jump",
    "hop",
    "lunge",
    "split squat",
    "step-up",
    "step up",
    "step-out",
    "step out",
    "knee up-down",
    "single-leg deadlift",
    "single leg deadlift",
    "single-leg",
    "single leg",
    "sissy squat",
    "bulgarian",
    "pistol squat",
}

LOW_BACK_STRESS_MARKERS = {
    "deadlift",
    "good morning",
    "hinge",
    "bent-over",
    "bent over",
}

SHOULDER_STRESS_MARKERS = {
    "overhead press",
    "behind-the-neck",
    "upright row",
    "lateral raise",
    "front raise",
    "rear delt",
    "rear-delt",
    "arnold press",
    "dip",
    "push-up",
    "push up",
}

SHOULDER_STRESS_PATTERNS = {
    "vertical push",
    "lateral raise",
    "rear delt",
    "shoulder isolation",
}

SHOULDER_RELATED_PRIMARYS = {"shoulder", "shoulders"}


def infer_injury_flags(injuries_text: str) -> set[str]:
    lowered = injuries_text.lower()
    flags: set[str] = set()

    for flag, keywords in INJURY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            flags.add(flag)

    return flags


def contraindications_conflict(
    contraindications: list[str], injury_flags: set[str]
) -> bool:
    normalized = {item.lower().strip() for item in contraindications if item}
    if normalized & injury_flags:
        return True

    if "acute shoulder pain" in injury_flags and any(
        "shoulder" in item or "rotator cuff" in item or "labrum" in item
        for item in normalized
    ):
        return True

    if "acute knee pain" in injury_flags and any(
        "knee" in item or "patella" in item or "meniscus" in item for item in normalized
    ):
        return True

    if "acute low-back pain" in injury_flags and any(
        "back" in item or "spine" in item or "disc" in item for item in normalized
    ):
        return True

    if "acute elbow pain" in injury_flags and any("elbow" in item for item in normalized):
        return True

    return False


def render_injury_guidance(injury_flags: set[str]) -> list[str]:
    guidance: list[str] = []

    if "acute shoulder pain" in injury_flags:
        guidance.append(
            "Treat shoulder injury as a hard constraint: avoid direct shoulder exercises and common shoulder-aggravating presses, raises, upright rows, and dips unless the user explicitly asks for rehab work."
        )
    if "acute knee pain" in injury_flags:
        guidance.append(
            "Treat knee pain as a hard constraint: avoid high-impact jumps, lunges, split squats, and other knee-aggravating squat patterns unless the user explicitly asks for rehab work."
        )
    if "acute low-back pain" in injury_flags:
        guidance.append(
            "Treat low-back pain as a hard constraint: avoid heavy hip hinges, good mornings, and lower-back-dominant loading unless the user explicitly asks for rehab work."
        )
    if "acute elbow pain" in injury_flags:
        guidance.append(
            "Treat elbow pain as a hard constraint: avoid elbow-aggravating isolation or repetitive pressing patterns unless the user explicitly asks for rehab work."
        )

    return guidance
