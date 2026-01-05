import os
from typing import AsyncGenerator, Optional

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def _maybe_get_env(name: str) -> Optional[str]:
    """Return env var value or None if missing/empty."""
    value = os.getenv(name)
    if value and value.strip():
        return value.strip()
    return None


def _normalize_async_database_url(raw_url: str) -> str:
    """
    Normalize a postgres URL to one compatible with SQLAlchemy async engine.

    The DB container typically provides a URL like:
      postgresql://user:pass@host:port/db

    Async SQLAlchemy requires the async driver:
      postgresql+asyncpg://user:pass@host:port/db
    """
    url = make_url(raw_url)

    # If drivername is already async, keep it.
    if "+asyncpg" in url.drivername:
        return str(url)

    # Convert plain postgres urls to asyncpg dialect.
    if url.drivername in {"postgresql", "postgres"}:
        return str(url.set(drivername="postgresql+asyncpg"))

    # Otherwise, return unchanged (might be already a fully-qualified dialect URL).
    return str(url)


_engine: Optional[AsyncEngine] = None
_SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


# PUBLIC_INTERFACE
def get_engine() -> AsyncEngine:
    """Return a singleton AsyncEngine configured from POSTGRES_URL."""
    global _engine, _SessionLocal

    if _engine is not None:
        return _engine

    raw_url = _maybe_get_env("POSTGRES_URL")
    if not raw_url:
        raise RuntimeError(
            "Missing required environment variable POSTGRES_URL. "
            "Set it in the container environment (see .env.example)."
        )

    database_url = _normalize_async_database_url(raw_url)

    _engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
    )
    _SessionLocal = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _engine


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Internal helper to lazily initialize sessionmaker."""
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


# PUBLIC_INTERFACE
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an Async SQLAlchemy session."""
    session_maker = _get_sessionmaker()
    async with session_maker() as session:
        yield session
