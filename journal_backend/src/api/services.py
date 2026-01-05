from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models import JournalEntry


class DuplicateEntryError(Exception):
    """Raised when trying to create more than one entry for the same user and date."""


async def create_today_entry(
    session: AsyncSession, *, user_id: str, content: str, today: Optional[date] = None
) -> JournalEntry:
    """Create today's journal entry for a user, enforcing one-entry-per-day."""
    if today is None:
        today = date.today()

    entry = JournalEntry(user_id=user_id, entry_date=today, content=content)
    session.add(entry)

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        # Unique constraint violation: (user_id, entry_date)
        raise DuplicateEntryError("Journal entry for today already exists.") from e

    await session.refresh(entry)
    return entry


async def get_entry_by_date(session: AsyncSession, *, user_id: str, entry_date: date) -> Optional[JournalEntry]:
    """Fetch a user's journal entry by date."""
    stmt = select(JournalEntry).where(JournalEntry.user_id == user_id, JournalEntry.entry_date == entry_date)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def list_history(session: AsyncSession, *, user_id: str, limit: int = 365) -> List[JournalEntry]:
    """List a user's journal history (most recent first)."""
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.user_id == user_id)
        .order_by(desc(JournalEntry.entry_date))
        .limit(limit)
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def compute_current_streak(session: AsyncSession, *, user_id: str, today: Optional[date] = None) -> int:
    """
    Compute the current streak of consecutive days ending today.

    Definition:
    - Streak counts consecutive calendar days with an entry.
    - Streak is 0 if there is no entry for today.
    """
    if today is None:
        today = date.today()

    # Fetch all dates up to today (descending), then walk until a gap is found.
    stmt = (
        select(JournalEntry.entry_date)
        .where(JournalEntry.user_id == user_id, JournalEntry.entry_date <= today)
        .order_by(desc(JournalEntry.entry_date))
    )
    res = await session.execute(stmt)
    dates = list(res.scalars().all())

    if not dates or dates[0] != today:
        return 0

    streak = 1
    expected = today - timedelta(days=1)

    for d in dates[1:]:
        if d == expected:
            streak += 1
            expected = expected - timedelta(days=1)
            continue
        if d < expected:
            # Gap found (or older data) -> stop.
            break

    return streak
