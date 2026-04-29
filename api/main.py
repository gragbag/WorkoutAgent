import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, health, plan, session

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="WorkoutAgent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(session.router, prefix="/api", tags=["session"])
app.include_router(plan.router, prefix="/api", tags=["plan"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
