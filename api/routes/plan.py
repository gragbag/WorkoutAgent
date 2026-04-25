from fastapi import APIRouter

from api.models import PlanRequest, PlanResponse
from api.llm_service import generate_plan_response

router = APIRouter()


@router.post("/plan", response_model=PlanResponse)
def create_plan(payload: PlanRequest) -> PlanResponse:
    return generate_plan_response(payload)
