from __future__ import annotations

from datetime import date, datetime
from typing import List

from pydantic import BaseModel, Field


class JournalEntryCreate(BaseModel):
    user_id: str = Field(..., description="User identifier (string).")
    content: str = Field(..., min_length=1, description="Journal entry content for today.")


class JournalEntryOut(BaseModel):
    id: int = Field(..., description="Entry id.")
    user_id: str = Field(..., description="User identifier.")
    entry_date: date = Field(..., description="The date of the entry (YYYY-MM-DD).")
    content: str = Field(..., description="Journal entry content.")
    created_at: datetime = Field(..., description="UTC timestamp when the entry was created.")
    updated_at: datetime = Field(..., description="UTC timestamp when the entry was last updated.")

    class Config:
        from_attributes = True


class StreakOut(BaseModel):
    user_id: str = Field(..., description="User identifier.")
    current_streak: int = Field(..., ge=0, description="Current consecutive-day streak ending today (if present).")


class JournalHistoryOut(BaseModel):
    user_id: str = Field(..., description="User identifier.")
    entries: List[JournalEntryOut] = Field(..., description="Journal entries (most recent first).")
