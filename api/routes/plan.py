from fastapi import APIRouter, HTTPException

from api.llm_service import generate_edited_plan_response, generate_plan_response
from api.models import PlanEditRequest, PlanRequest, PlanResponse

router = APIRouter()


@router.post("/plan", response_model=PlanResponse)
def create_plan(payload: PlanRequest) -> PlanResponse:
    try:
        return generate_plan_response(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/plan/edit", response_model=PlanResponse)
def edit_plan(payload: PlanEditRequest) -> PlanResponse:
    try:
        return generate_edited_plan_response(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
