from __future__ import annotations

from api.exercise_library import get_candidate_exercises
from api.intake import normalize_plan_request
from api.models import PlanRequest
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

    mcp.settings.host = "127.0.0.1"
    mcp.settings.port = 8001
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
