"""
TrueShift - State Routes

User state and AI recommendation endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.user_state import UserState
from app.services.user_state_engine import UserStateEngine
from app.services.recommendation_engine import RecommendationEngine
from app.ai.orchestrator import ai_orchestrator

router = APIRouter()


# ============================================================================
# Response Schemas
# ============================================================================


class UserStateResponse(BaseModel):
    """User state response."""
    user_id: str
    last_activity_at: str | None
    physical: dict
    location: dict
    digital: dict
    goals: list
    focus_area: str | None


class RecommendationsResponse(BaseModel):
    """Recommendations response."""
    recommendations: list[dict]
    count: int


class AICoachingResponse(BaseModel):
    """AI coaching response."""
    context_summary: dict | None
    coaching: dict | None
    workout: dict | None
    errors: list[str]


# ============================================================================
# Endpoints
# ============================================================================


@router.get("", response_model=UserStateResponse)
async def get_user_state(
    firebase_uid: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user state.
    """
    # Get user
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get state
    state_engine = UserStateEngine(db)
    state = await state_engine.get_or_create_state(user.id)

    context = state.get_context_summary()

    return UserStateResponse(
        user_id=state.user_id,
        last_activity_at=state.last_activity_at.isoformat() if state.last_activity_at else None,
        physical=context.get("physical", {}),
        location=context.get("location", {}),
        digital=context.get("digital", {}),
        goals=context.get("goals", []),
        focus_area=context.get("focus_area"),
    )


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    limit: int = 3,
    firebase_uid: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get personalized recommendations based on current state.
    """
    # Get user
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get state
    state_engine = UserStateEngine(db)
    state = await state_engine.get_or_create_state(user.id)

    # Get recommendations
    rec_engine = RecommendationEngine()
    recommendations = await rec_engine.generate_recommendations(state, limit=limit)

    return RecommendationsResponse(
        recommendations=[r.model_dump() for r in recommendations],
        count=len(recommendations),
    )


@router.get("/ai/coaching", response_model=AICoachingResponse)
async def get_ai_coaching(
    firebase_uid: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full AI coaching output including context, coaching advice, and workout.
    Runs the complete multi-agent pipeline.
    """
    # Get user
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check AI coaching consent
    if not user.consent_ai_coaching:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI coaching consent required",
        )

    # Get state
    state_engine = UserStateEngine(db)
    state = await state_engine.get_or_create_state(user.id)

    # Run AI pipeline
    result = await ai_orchestrator.process_full_pipeline(
        user_id=user.id,
        user_state=state,
    )

    return AICoachingResponse(
        context_summary=result.context_summary,
        coaching=result.coaching,
        workout=result.workout,
        errors=result.errors,
    )


@router.get("/ai/workout")
async def get_workout_recommendation(
    firebase_uid: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get workout recommendation only.
    """
    # Get user
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get state
    state_engine = UserStateEngine(db)
    state = await state_engine.get_or_create_state(user.id)

    # Get workout
    response = await ai_orchestrator.get_workout(user.id, state)

    return {
        "success": response.success,
        "workout": response.content,
        "confidence": response.confidence,
    }
