from fastapi import APIRouter, HTTPException

from api.models import ChatRequest, ChatResponse
from api.services import append_message, generate_chat_reply, get_session

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    session = get_session(payload.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    append_message(payload.session_id, "user", payload.message)
    reply = generate_chat_reply(session, payload.message)
    updated_session = append_message(payload.session_id, "assistant", reply)

    return ChatResponse(
        response=reply,
        message_count=len(updated_session.messages) if updated_session else 0,
    )
