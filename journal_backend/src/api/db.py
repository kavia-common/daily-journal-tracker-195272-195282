import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            f"Set it in the container environment (see .env.example)."
        )
    return value


# SQLAlchemy async engine/session factory. Uses POSTGRES_URL provided by the database container.
DATABASE_URL = _require_env("POSTGRES_URL")

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# PUBLIC_INTERFACE
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an Async SQLAlchemy session."""
    async with AsyncSessionLocal() as session:
        yield session
