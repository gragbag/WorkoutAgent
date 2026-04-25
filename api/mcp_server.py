from __future__ import annotations

from api.exercise_library import get_candidate_exercises
from api.intake import normalize_plan_request
from api.models import PlanRequest
from api.planning_knowledge import get_split_template, get_staple_exercise_hints
from api.rag import retrieve_relevant_context

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None


if FastMCP is not None:
    mcp = FastMCP("WorkoutAgent MCP")

    @mcp.tool()
    def search_exercises(plan_request: dict, limit: int = 12) -> list[dict]:
        """Return curated exercise candidates for a workout intake."""
        payload = PlanRequest.model_validate(plan_request)
        normalized = normalize_plan_request(payload)
        exercises = get_candidate_exercises(normalized, limit=limit)
        return [exercise.model_dump() for exercise in exercises]

    @mcp.tool()
    def recommend_split(plan_request: dict) -> list[str]:
        """Return a simple, traditional split recommendation for the current schedule."""
        payload = PlanRequest.model_validate(plan_request)
        normalized = normalize_plan_request(payload)
        return get_split_template(normalized)

    @mcp.tool()
    def staple_exercise_hints(plan_request: dict) -> list[str]:
        """Return staple exercise names to bias the planner toward."""
        payload = PlanRequest.model_validate(plan_request)
        normalized = normalize_plan_request(payload)
        return get_staple_exercise_hints(normalized)

    @mcp.tool()
    def retrieve_context(plan_request: dict, limit: int = 8) -> list[dict]:
        """Return top retrieved exercise context chunks for the current intake."""
        payload = PlanRequest.model_validate(plan_request)
        normalized = normalize_plan_request(payload)
        exercises = get_candidate_exercises(normalized, limit=max(limit, 12))
        retrieved, _ = retrieve_relevant_context(normalized, exercises, top_k=limit)
        return [chunk.model_dump() for chunk in retrieved]


def main() -> None:
    if FastMCP is None:
        raise RuntimeError(
            "The MCP Python SDK is not installed. Add 'mcp' to your environment first."
        )

    mcp.run()


if __name__ == "__main__":
    main()
