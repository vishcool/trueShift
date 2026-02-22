"""
TrueShift - API Router

Central router that aggregates all API endpoints.
"""

from fastapi import APIRouter

from app.api.routes import auth, events, state, health, vision, workout, agent, voice

api_router = APIRouter()

# Health endpoints (no prefix)
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

# Authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

# Event ingestion endpoints
api_router.include_router(
    events.router,
    prefix="/events",
    tags=["Events"],
)

# State & AI endpoints
api_router.include_router(
    state.router,
    prefix="/state",
    tags=["State & AI"],
)

# Vision & AI endpoints
api_router.include_router(
    vision.router,
    prefix="/vision",
    tags=["Vision"],
)

# Workout endpoints
api_router.include_router(
    workout.router,
    prefix="/workout",
    tags=["Workout"],
)

# Agent endpoints
api_router.include_router(
    agent.router,
    prefix="/agent",
    tags=["Agent"],
)

# Voice WebSocket endpoints
api_router.include_router(
    voice.router,
    prefix="/voice",
    tags=["Voice"],
)
