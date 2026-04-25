from __future__ import annotations

import argparse
import json
import os
from statistics import mean

from api.eval_cases import EVAL_CASES
from api.llm_service import generate_plan_response


def _score_case(case_name: str, plan) -> dict[str, object]:
    metadata = plan.metadata
    requested_days = len(plan.days)
    exercise_names = [exercise.name for day in plan.days for exercise in day.exercises]
    unique_exercises = len(set(exercise_names))
    duplicate_count = len(exercise_names) - unique_exercises

    structure_pass = bool(plan.summary and plan.days and metadata)
    fallback_penalty = 1 if metadata.fallback_used else 0
    duplicate_penalty = 1 if duplicate_count > max(2, len(plan.days)) else 0
    candidate_bonus = 1 if metadata.candidate_exercise_count >= len(plan.days) * 2 else 0

    quality_score = max(1, 5 - fallback_penalty - duplicate_penalty + candidate_bonus)
    coherence_score = 5 if requested_days == len(plan.days) else 3

    return {
      "case": case_name,
      "structure_pass": structure_pass,
      "quality_score": min(5, quality_score),
      "coherence_score": coherence_score,
      "provider_used": metadata.provider_used,
      "model_used": metadata.model_used,
      "fallback_used": metadata.fallback_used,
      "candidate_exercise_count": metadata.candidate_exercise_count,
      "exercise_count": len(exercise_names),
      "duplicate_exercise_count": duplicate_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate WorkoutAgent plan generation across canned backend test cases."
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "configured"],
        default="mock",
        help="Use mock mode or the provider configured in .env/environment.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Maximum number of evaluation cases to run. Keep this low for paid providers.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full evaluation results as JSON.",
    )
    args = parser.parse_args()

    if args.provider == "mock":
        os.environ["WORKOUTAGENT_LLM_PROVIDER"] = "mock"

    limited_cases = EVAL_CASES[: max(1, min(args.limit, len(EVAL_CASES)))]
    results = []

    for case_name, payload in limited_cases:
        plan = generate_plan_response(payload)
        results.append(_score_case(case_name, plan))

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"Evaluated {len(results)} case(s)")
    for result in results:
        print(
            f"- {result['case']}: "
            f"provider={result['provider_used']}, "
            f"fallback={result['fallback_used']}, "
            f"quality={result['quality_score']}/5, "
            f"coherence={result['coherence_score']}/5, "
            f"duplicates={result['duplicate_exercise_count']}"
        )

    avg_quality = mean(result["quality_score"] for result in results)
    avg_coherence = mean(result["coherence_score"] for result in results)
    structure_pass_rate = sum(1 for result in results if result["structure_pass"]) / len(results)

    print("")
    print(f"Average quality: {avg_quality:.2f}/5")
    print(f"Average coherence: {avg_coherence:.2f}/5")
    print(f"Structure pass rate: {structure_pass_rate:.0%}")
    print("")
    print(
        "Tip: start with `python3 -m api.evaluate_plans --provider mock --limit 3`, "
        "then try `--provider configured --limit 1` once you want a cheap real-model sanity check."
    )


if __name__ == "__main__":
    main()
