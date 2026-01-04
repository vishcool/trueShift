"""
TrueShift - Health Check Routes

Health check and status endpoints for monitoring.
"""

from fastapi import APIRouter
import redis.asyncio as redis

from app.core.database import engine, redis_client

router = APIRouter()


@router.get("")
async def health_check():
    """
    Basic health check endpoint.
    """
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.
    """
    checks = {
        "database": False,
        "redis": False,
    }

    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
            checks["database"] = True
    except Exception:
        pass

    # Check Redis
    try:
        if redis_client:
            await redis_client.ping()
            checks["redis"] = True
    except Exception:
        pass

    all_healthy = all(checks.values())
    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness check - indicates if the service is running.
    """
    return {"status": "alive"}
