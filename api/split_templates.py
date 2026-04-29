from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from api.models import (
    NormalizedPlanRequest,
    SplitTemplate,
    SplitTemplateMatch,
)

DATA_PATH = Path(__file__).resolve().parent / "data" / "split_templates.json"


@lru_cache(maxsize=1)
def load_split_templates() -> list[SplitTemplate]:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        raw_templates = json.load(handle)
    return [SplitTemplate.model_validate(item) for item in raw_templates]


def _score_template(template: SplitTemplate, normalized: NormalizedPlanRequest) -> SplitTemplateMatch:
    constraints = normalized.constraints

    score = 0.0
    rationale: list[str] = []

    if not template.equipment_tags:
        score += 0.5
    else:
        matched_equipment = [
            item for item in template.equipment_tags if item in constraints.equipment
        ]
        if matched_equipment:
            score += min(2.0, 0.7 * len(matched_equipment))
            rationale.append(
                "uses available equipment well"
            )
        else:
            rationale.append(
                "not strongly tied to the current equipment list"
            )

    return SplitTemplateMatch(
        template_id=template.id,
        label=template.label,
        score=round(score, 2),
        summary=template.summary,
        rationale=rationale[:5],
        day_blueprints=template.day_blueprints,
    )


def shortlist_split_templates(
    normalized: NormalizedPlanRequest,
    *,
    top_k: int = 4,
) -> list[SplitTemplateMatch]:
    templates = [
        template
        for template in load_split_templates()
        if template.days_per_week == normalized.constraints.days_per_week
    ]

    matches = [_score_template(template, normalized) for template in templates]
    matches.sort(key=lambda item: (-item.score, item.label))
    return matches[:top_k]
