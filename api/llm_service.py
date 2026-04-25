from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from api.models import PlanRequest, PlanResponse
from api.services import build_mock_plan_response, build_plan_metadata, prepare_plan_generation
from api.validators import validate_plan_response


@dataclass
class LLMConfig:
    provider: str
    api_url: str
    api_key: str
    model: str
    timeout_seconds: int


def _load_config() -> LLMConfig:
    return LLMConfig(
        provider=os.getenv("WORKOUTAGENT_LLM_PROVIDER", "mock"),
        api_url=os.getenv(
            "WORKOUTAGENT_LLM_API_URL",
            "https://api.openai.com/v1/chat/completions",
        ),
        api_key=os.getenv("WORKOUTAGENT_LLM_API_KEY", ""),
        model=os.getenv("WORKOUTAGENT_LLM_MODEL", ""),
        timeout_seconds=int(os.getenv("WORKOUTAGENT_LLM_TIMEOUT", "45")),
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
        if config.provider != "openai_compat":
            raise ValueError(
                "Unsupported WORKOUTAGENT_LLM_PROVIDER. Use 'mock' or 'openai_compat'."
            )

        raw_response = _call_openai_compatible_api(
            config,
            system_prompt=prompt_bundle.system_prompt,
            user_prompt=prompt_bundle.user_prompt,
        )
        plan = _parse_plan_response(raw_response)
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
    return {
        "system_prompt": prompt_bundle.system_prompt,
        "user_prompt": prompt_bundle.user_prompt,
        "normalized_input": prompt_bundle.normalized_input.model_dump(),
    }
