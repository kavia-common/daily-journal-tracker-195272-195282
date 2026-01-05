from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_db_session
from src.api.schemas import JournalEntryCreate, JournalEntryOut, JournalHistoryOut, StreakOut
from src.api.services import (
    DuplicateEntryError,
    compute_current_streak,
    create_today_entry,
    get_entry_by_date,
    list_history,
)

router = APIRouter(prefix="/api", tags=["Journal"])


@router.post(
    "/entry/today",
    response_model=JournalEntryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit today's journal entry",
    description="Creates a journal entry for the current day. Enforces one entry per day per user.",
    operation_id="submit_today_entry",
)
# PUBLIC_INTERFACE
async def submit_today_entry(payload: JournalEntryCreate, db: AsyncSession = Depends(get_db_session)) -> JournalEntryOut:
    """Submit today's journal entry for a user."""
    try:
        entry = await create_today_entry(db, user_id=payload.user_id, content=payload.content)
    except DuplicateEntryError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    return JournalEntryOut.model_validate(entry)


@router.get(
    "/streak",
    response_model=StreakOut,
    summary="Get current streak",
    description="Returns the current consecutive-day streak ending today (0 if no entry today).",
    operation_id="get_current_streak",
)
# PUBLIC_INTERFACE
async def get_current_streak(
    user_id: str = Query(..., description="User identifier."),
    db: AsyncSession = Depends(get_db_session),
) -> StreakOut:
    """Get user's current streak."""
    streak = await compute_current_streak(db, user_id=user_id)
    return StreakOut(user_id=user_id, current_streak=streak)


@router.get(
    "/history",
    response_model=JournalHistoryOut,
    summary="List journal history",
    description="List journal entries for a user (most recent first).",
    operation_id="list_journal_history",
)
# PUBLIC_INTERFACE
async def get_history(
    user_id: str = Query(..., description="User identifier."),
    limit: int = Query(365, ge=1, le=5000, description="Maximum entries to return."),
    db: AsyncSession = Depends(get_db_session),
) -> JournalHistoryOut:
    """List a user's journal history."""
    entries = await list_history(db, user_id=user_id, limit=limit)
    return JournalHistoryOut(user_id=user_id, entries=[JournalEntryOut.model_validate(e) for e in entries])


@router.get(
    "/entry",
    response_model=Optional[JournalEntryOut],
    summary="Get a journal entry by date",
    description="Fetch a single entry for the given user and date. Returns null if not found.",
    operation_id="get_entry_by_date",
)
# PUBLIC_INTERFACE
async def get_entry(
    user_id: str = Query(..., description="User identifier."),
    entry_date: date = Query(..., description="Entry date (YYYY-MM-DD)."),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[JournalEntryOut]:
    """Get a user's journal entry for a specific date."""
    entry = await get_entry_by_date(db, user_id=user_id, entry_date=entry_date)
    if entry is None:
        return None
    return JournalEntryOut.model_validate(entry)
