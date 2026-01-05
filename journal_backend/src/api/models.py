from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""


class JournalEntry(Base):
    """Journal entry: exactly one per day per user_id."""

    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # In lieu of full auth, the frontend can supply any stable user_id string.
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# Enforce one entry per day per user (also used for fast lookup)
Index(
    "ux_journal_entries_user_date",
    JournalEntry.user_id,
    JournalEntry.entry_date,
    unique=True,
)
