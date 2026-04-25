from fastapi import APIRouter, status

from api.models import SessionResponse
from api.services import create_session

router = APIRouter()


@router.post("/session", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def new_session() -> SessionResponse:
    session = create_session()
    return SessionResponse(session_id=session.session_id, created_at=session.created_at)
