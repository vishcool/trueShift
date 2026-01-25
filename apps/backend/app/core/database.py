"""
TrueShift - Database Configuration

Async PostgreSQL connection using SQLAlchemy 2.0.
Redis client for caching and real-time features.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
import redis.asyncio as redis

from app.core.config import settings


# SQLAlchemy Async Engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session Factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Redis Client (initialized on startup)
redis_client: redis.Redis | None = None


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base class.
    All models inherit from this.
    """
    pass


async def init_db() -> None:
    """
    Initialize database connections.
    Called on application startup.
    """
    global redis_client

    # Initialize Redis (best-effort)
    try:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    except Exception as e:
        # Do not fail startup due to Redis connection issues; log and continue.
        import logging

        logging.getLogger(__name__).warning("Failed to initialize Redis client: %s", e)

    # Create tables (for development - use Alembic in production)
    if settings.is_development:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            # Log DB initialization failures but allow application to start.
            import logging

            logging.getLogger(__name__).error("Database initialization failed: %s", e)


async def close_db() -> None:
    """
    Close database connections.
    Called on application shutdown.
    """
    global redis_client

    if redis_client:
        await redis_client.close()

    await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions.
    Yields a session and ensures cleanup.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> redis.Redis:
    """
    Dependency injection for Redis client.
    """
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client
