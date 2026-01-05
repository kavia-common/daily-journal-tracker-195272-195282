import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.db import engine
from src.api.journal_router import router as journal_router
from src.api.models import Base

openapi_tags = [
    {
        "name": "Health",
        "description": "Service health checks.",
    },
    {
        "name": "Journal",
        "description": "Daily journal entry APIs: submit, streak, history, and fetch by date.",
    },
]

app = FastAPI(
    title="Daily Journal Tracker API",
    description=(
        "Backend for a daily journal tracker with one-entry-per-day enforcement and streak calculation.\n\n"
        "Notes:\n"
        "- This template uses a simple `user_id` string passed by the client (no auth yet).\n"
        "- Streak is defined as consecutive days ending today; if there is no entry today, streak is 0."
    ),
    version="0.1.0",
    openapi_tags=openapi_tags,
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    """Create database tables on startup (simple migration-less setup for MVP)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/", tags=["Health"], summary="Health check", operation_id="health_check")
# PUBLIC_INTERFACE
def health_check():
    """Health check endpoint used for uptime monitoring."""
    return {"message": "Healthy"}


app.include_router(journal_router)
