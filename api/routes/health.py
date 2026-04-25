from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "workoutagent-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
