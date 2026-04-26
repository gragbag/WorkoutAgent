from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from api.models import (
    PlanRequest,
    PlanResponse,
    PlanReview,
    PromptBundle,
    SplitPlan,
)
from api.services import build_mock_plan_response, build_plan_metadata, prepare_plan_generation
from api.validators import validate_plan_response


@dataclass
class LLMConfig:
    provider: str
    api_url: str
    api_key: str
    model: str
    timeout_seconds: int
    mcp_server_url: str


def _load_config() -> LLMConfig:
    provider = os.getenv("WORKOUTAGENT_LLM_PROVIDER", "mock")
    return LLMConfig(
        provider=provider,
        api_url=os.getenv(
            "WORKOUTAGENT_LLM_API_URL",
            "https://api.openai.com/v1/responses"
            if provider == "openai_mcp"
            else "https://api.openai.com/v1/chat/completions",
        ),
        api_key=os.getenv("WORKOUTAGENT_LLM_API_KEY", ""),
        model=os.getenv("WORKOUTAGENT_LLM_MODEL", ""),
        timeout_seconds=int(os.getenv("WORKOUTAGENT_LLM_TIMEOUT", "45")),
        mcp_server_url=os.getenv("WORKOUTAGENT_MCP_SERVER_URL", ""),
    )


def _extract_json_blob(raw_text: str) -> str:
    stripped = raw_text.strip()

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model response did not contain a JSON object.")

    return stripped[start : end + 1]


def _call_openai_compatible_api(config: LLMConfig, system_prompt: str, user_prompt: str) -> str:
    if not config.api_key:
        raise ValueError("Missing WORKOUTAGENT_LLM_API_KEY.")

    if not config.model:
        raise ValueError("Missing WORKOUTAGENT_LLM_MODEL.")

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    req = request.Request(
        config.api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LLM HTTP error {exc.code}: {error_body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"LLM network error: {exc.reason}") from exc

    choices = data.get("choices", [])
    if not choices:
        raise ValueError("LLM response did not include any choices.")

    message = choices[0].get("message", {})
    content = message.get("content")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") in {"text", "output_text"}
        ]
        combined = "".join(text_parts).strip()
        if combined:
            return combined

    raise ValueError("LLM response did not contain text content.")


def _extract_responses_api_text(data: dict[str, Any]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output_items = data.get("output", [])
    text_parts: list[str] = []

    for item in output_items:
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    text_parts.append(content["text"])

    combined = "\n".join(text_parts).strip()
    if combined:
        return combined

    raise ValueError("Responses API output did not contain any text.")


def _call_openai_responses_api_with_mcp(
    config: LLMConfig, system_prompt: str, user_prompt: str
) -> str:
    if not config.api_key:
        raise ValueError("Missing WORKOUTAGENT_LLM_API_KEY.")

    if not config.model:
        raise ValueError("Missing WORKOUTAGENT_LLM_MODEL.")

    if not config.mcp_server_url:
        raise ValueError("Missing WORKOUTAGENT_MCP_SERVER_URL.")

    payload = {
        "model": config.model,
        "instructions": system_prompt,
        "input": user_prompt,
        "tools": [
            {
                "type": "mcp",
                "server_label": "workoutagent_mcp",
                "server_description": "Workout planning tools for exercise search, split recommendations, and retrieval.",
                "server_url": config.mcp_server_url,
                "require_approval": "never",
                "allowed_tools": [
                    "search_exercises",
                    "retrieve_context",
                ],
            }
        ],
    }

    req = request.Request(
        config.api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LLM HTTP error {exc.code}: {error_body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"LLM network error: {exc.reason}") from exc

    return _extract_responses_api_text(data)


def _parse_plan_response(raw_text: str) -> PlanResponse:
    json_blob = _extract_json_blob(raw_text)
    parsed = json.loads(json_blob)
    parsed.setdefault(
        "metadata",
        {
            "provider_requested": "pending",
            "provider_used": "pending",
            "model_used": "pending",
            "fallback_used": False,
            "fallback_reason": "",
            "candidate_exercise_count": 0,
            "generated_at": "pending",
        },
    )
    return PlanResponse.model_validate(parsed)


def _parse_split_plan(raw_text: str) -> SplitPlan:
    json_blob = _extract_json_blob(raw_text)
    return SplitPlan.model_validate(json.loads(json_blob))


def _parse_plan_review(raw_text: str) -> PlanReview:
    json_blob = _extract_json_blob(raw_text)
    return PlanReview.model_validate(json.loads(json_blob))


def _render_candidate_summary(prompt_bundle: PromptBundle) -> str:
    if not prompt_bundle.candidate_exercises:
        return "- No candidate exercises were retrieved."

    lines = []
    for exercise in prompt_bundle.candidate_exercises[:16]:
        lines.append(
            "- "
            f"{exercise.name} | muscle: {exercise.primary_muscle_group} | "
            f"equipment: {exercise.equipment_used} | pattern: {exercise.movement_pattern} | "
            f"difficulty: {exercise.difficulty}"
        )
    return "\n".join(lines)


def _render_retrieved_context(prompt_bundle: PromptBundle) -> str:
    if not prompt_bundle.retrieved_context:
        return "- No retrieved context."

    return "\n".join(
        f"- {chunk.title} | score={chunk.score} | {chunk.content}"
        for chunk in prompt_bundle.retrieved_context
    )


def _render_intake_context(prompt_bundle: PromptBundle) -> str:
    athlete = prompt_bundle.normalized_input.athlete_profile
    constraints = prompt_bundle.normalized_input.constraints
    preferences = prompt_bundle.normalized_input.preferences

    return f"""
Athlete profile:
- Experience: {athlete.experience}
- Age range: {athlete.age_range}
- Height: {athlete.height_feet} ft {athlete.height_inches} in
- Weight: {athlete.weight_lbs} lb
- Current activity level: {athlete.current_activity_level}

Constraints:
- Equipment categories: {", ".join(constraints.equipment)}
- Workout location: {constraints.workout_location}
- Equipment details: {constraints.equipment_details}
- Required training days: {", ".join(constraints.available_training_days)}
- Flexible training days: {", ".join(constraints.flexible_training_days) if constraints.flexible_training_days else "None"}
- Session length: {constraints.session_length} minutes
- Injuries or pain points: {constraints.injuries}

Preferences:
- Cardio preference: {preferences.cardio_preference}
- Intensity preference: {preferences.intensity_preference}
- Variety preference: {preferences.variety_preference}
- Notes: {preferences.notes}
""".strip()


def _build_split_agent_prompts(prompt_bundle: PromptBundle) -> tuple[str, str]:
    system_prompt = (
        "You are the Split Planner agent for WorkoutAgent. "
        "Your job is only to design a practical weekly structure. "
        "Prefer traditional, easy-to-follow splits such as full body, upper/lower, or push/pull/legs when they fit the schedule. "
        "Do not choose exercises yet. Return valid JSON only."
    )
    user_prompt = f"""
Plan the weekly split for this athlete.

{_render_intake_context(prompt_bundle)}

Requirements:
- Use exactly {prompt_bundle.normalized_input.constraints.days_per_week} required training days.
- Required days must be only: {", ".join(prompt_bundle.normalized_input.constraints.available_training_days)}.
- Optional days must be only: {", ".join(prompt_bundle.normalized_input.constraints.flexible_training_days) if prompt_bundle.normalized_input.constraints.flexible_training_days else "none"}.
- Make the structure feel traditional and realistic for a normal gym trainee.
- If the athlete is a beginner or schedule-constrained, prefer simpler structures over fancy ones.

Return JSON in this shape:
{{
  "summary": string,
  "rationale": [string, string],
  "days": [
    {{
      "day": "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday",
      "focus": string,
      "objective": string,
      "key_patterns": [string]
    }}
  ],
  "optional_days": [
    {{
      "day": "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday",
      "focus": string,
      "objective": string,
      "key_patterns": [string]
    }}
  ]
}}
""".strip()
    return system_prompt, user_prompt


def _build_exercise_agent_prompts(
    prompt_bundle: PromptBundle, split_plan: SplitPlan, revision_notes: list[str] | None = None
) -> tuple[str, str]:
    system_prompt = (
        "You are the Exercise Planner agent for WorkoutAgent. "
        "Your job is to turn a split into a full workout plan with normal, recognizable exercise choices. "
        "Prefer staple exercises and avoid weird branded variations unless nothing better is available. "
        "Return valid JSON only."
    )
    revision_block = ""
    if revision_notes:
        revision_block = "\nVerifier revision notes:\n- " + "\n- ".join(revision_notes)

    user_prompt = f"""
Build the final workout plan from this split.

{_render_intake_context(prompt_bundle)}

Chosen split:
{json.dumps(split_plan.model_dump(), indent=2)}

Candidate exercises to favor:
{_render_candidate_summary(prompt_bundle)}

Retrieved exercise context:
{_render_retrieved_context(prompt_bundle)}
{revision_block}

Requirements:
- Required sessions must stay on the split's required days.
- Optional sessions must stay on the split's optional days.
- Use exercises from the candidate list whenever possible.
- Choose normal, traditional exercise names such as bench press, rows, squats, leg press, pulldowns, curls, and triceps work when available.
- Match equipment, injuries, and session length.
- Keep plans traditional and believable, not novelty-heavy.
- Include concise, useful coach notes.

Return JSON in this shape:
{{
  "summary": string,
  "athlete_snapshot": [string, string, string],
  "coaching_notes": [string, string, string],
  "days": [
    {{
      "day": "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday",
      "focus": string,
      "duration_minutes": integer,
      "warmup": [string, string],
      "exercises": [
        {{
          "name": string,
          "sets": integer,
          "reps": string,
          "rest_seconds": integer,
          "intensity_note": string,
          "primary_muscle_group": string,
          "equipment_used": string,
          "substitution_note": string
        }}
      ],
      "cooldown": [string],
      "coach_notes": [string]
    }}
  ],
  "optional_days": [
    {{
      "day": "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday",
      "focus": string,
      "duration_minutes": integer,
      "warmup": [string, string],
      "exercises": [
        {{
          "name": string,
          "sets": integer,
          "reps": string,
          "rest_seconds": integer,
          "intensity_note": string,
          "primary_muscle_group": string,
          "equipment_used": string,
          "substitution_note": string
        }}
      ],
      "cooldown": [string],
      "coach_notes": [string]
    }}
  ]
}}
""".strip()
    return system_prompt, user_prompt


def _build_verifier_prompts(prompt_bundle: PromptBundle, plan: PlanResponse) -> tuple[str, str]:
    system_prompt = (
        "You are the Verifier agent for WorkoutAgent. "
        "Your job is to critique a workout plan for realism, normal exercise selection, split coherence, and constraint adherence. "
        "Return valid JSON only."
    )
    user_prompt = f"""
Review this workout plan.

{_render_intake_context(prompt_bundle)}

Candidate exercises:
{_render_candidate_summary(prompt_bundle)}

Plan to review:
{json.dumps(plan.model_dump(exclude={"metadata"}), indent=2)}

Checklist:
- Does the split feel traditional and easy to follow?
- Are the exercise names normal and recognizable?
- Does the plan respect days, flexible days, equipment, injuries, and session length?
- Would a normal user trust this plan?

Return JSON in this shape:
{{
  "approved": boolean,
  "issues": [string],
  "revision_notes": [string]
}}
""".strip()
    return system_prompt, user_prompt


def _call_model(config: LLMConfig, system_prompt: str, user_prompt: str) -> str:
    if config.provider == "openai_compat":
        return _call_openai_compatible_api(config, system_prompt, user_prompt)
    if config.provider == "openai_mcp":
        return _call_openai_responses_api_with_mcp(config, system_prompt, user_prompt)
    raise ValueError(
        "Unsupported WORKOUTAGENT_LLM_PROVIDER. Use 'mock', 'openai_compat', or 'openai_mcp'."
    )


def _validate_split_plan(split_plan: SplitPlan, prompt_bundle: PromptBundle) -> None:
    required_days = set(prompt_bundle.normalized_input.constraints.available_training_days)
    flexible_days = set(prompt_bundle.normalized_input.constraints.flexible_training_days)
    expected_required_count = prompt_bundle.normalized_input.constraints.days_per_week

    if len(split_plan.days) != expected_required_count:
        raise ValueError("Split planner returned the wrong number of required days.")

    for day in split_plan.days:
        if day.day not in required_days:
            raise ValueError(f"Split planner used an unavailable required day: {day.day}")

    for day in split_plan.optional_days:
        if day.day not in flexible_days:
            raise ValueError(f"Split planner used a non-flexible optional day: {day.day}")


def generate_plan_response(payload: PlanRequest) -> PlanResponse:
    prompt_bundle = prepare_plan_generation(payload)
    config = _load_config()
    model_used = config.model or "unconfigured"

    if config.provider == "mock":
        return build_mock_plan_response(
            payload,
            prompt_bundle=prompt_bundle,
            provider_requested=config.provider,
            provider_used="mock",
            model_used="mock-template",
            fallback_used=False,
        )

    try:
        split_system_prompt, split_user_prompt = _build_split_agent_prompts(prompt_bundle)
        split_response = _call_model(config, split_system_prompt, split_user_prompt)
        split_plan = _parse_split_plan(split_response)
        _validate_split_plan(split_plan, prompt_bundle)

        exercise_system_prompt, exercise_user_prompt = _build_exercise_agent_prompts(
            prompt_bundle, split_plan
        )
        plan_response = _call_model(config, exercise_system_prompt, exercise_user_prompt)
        plan = _parse_plan_response(plan_response)

        verifier_system_prompt, verifier_user_prompt = _build_verifier_prompts(
            prompt_bundle, plan
        )
        review_response = _call_model(config, verifier_system_prompt, verifier_user_prompt)
        review = _parse_plan_review(review_response)

        if not review.approved and review.revision_notes:
            revised_system_prompt, revised_user_prompt = _build_exercise_agent_prompts(
                prompt_bundle,
                split_plan,
                revision_notes=review.revision_notes,
            )
            revised_response = _call_model(
                config, revised_system_prompt, revised_user_prompt
            )
            plan = _parse_plan_response(revised_response)

        validate_plan_response(plan, prompt_bundle)
        plan.metadata = build_plan_metadata(
            prompt_bundle,
            provider_requested=config.provider,
            provider_used=config.provider,
            model_used=model_used,
            fallback_used=False,
        )
        return plan
    except Exception as exc:
        print(f"Plan generation fell back to mock response: {exc!r}")
        return build_mock_plan_response(
            payload,
            prompt_bundle=prompt_bundle,
            provider_requested=config.provider,
            provider_used="mock",
            model_used="mock-template",
            fallback_used=True,
            fallback_reason=str(exc),
        )


def preview_prompt_payload(payload: PlanRequest) -> dict[str, Any]:
    prompt_bundle = prepare_plan_generation(payload)
    split_system_prompt, split_user_prompt = _build_split_agent_prompts(prompt_bundle)
    return {
        "split_agent": {
            "system_prompt": split_system_prompt,
            "user_prompt": split_user_prompt,
        },
        "normalized_input": prompt_bundle.normalized_input.model_dump(),
        "candidate_exercises": [exercise.model_dump() for exercise in prompt_bundle.candidate_exercises[:8]],
    }
