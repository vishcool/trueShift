"""
TrueShift - State Routes

User state and AI recommendation endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.user_state_engine import UserStateEngine
from app.services.recommendation_engine import RecommendationEngine
from app.services.progress_dashboard_service import progress_dashboard_service
from app.services.user_service import user_service
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
    planner: dict | None = None
    coaching: dict | None
    workout: dict | None
    errors: list[str]


class DashboardOverview(BaseModel):
    workouts_completed: int
    workouts_this_week: int
    minutes_this_week: int
    sets_logged: int
    avg_reps_per_set: float
    total_volume_kg: float
    recovery_status: str
    readiness_label: str


class DashboardRecovery(BaseModel):
    status: str
    sleep_hours: float | None
    hrv_score: float | None
    resting_heart_rate: int | None
    active_minutes_today: int


class DashboardFocus(BaseModel):
    primary_training_focus: str
    top_logged_exercises: list[str]


class DashboardInsight(BaseModel):
    type: str
    title: str
    detail: str
    priority: str


class DashboardSession(BaseModel):
    id: str
    created_at: str
    status: str
    overview: str
    exercise_count: int
    set_count: int
    duration_minutes: int
    volume_kg: float


class ProgressDashboardResponse(BaseModel):
    overview: DashboardOverview
    recovery: DashboardRecovery
    focus: DashboardFocus
    insights: list[DashboardInsight]
    suggestions: list[str]
    recent_sessions: list[DashboardSession]


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
    user = await user_service.require_user_by_firebase_uid(db, firebase_uid)

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
    user = await user_service.require_user_by_firebase_uid(db, firebase_uid)

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


@router.get("/dashboard", response_model=ProgressDashboardResponse)
async def get_progress_dashboard(
    firebase_uid: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.require_user_by_firebase_uid(db, firebase_uid)
    state_engine = UserStateEngine(db)
    state = await state_engine.get_or_create_state(user.id)
    dashboard = await progress_dashboard_service.build_dashboard(db, user.id, state)
    return ProgressDashboardResponse(**dashboard)


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
    user = await user_service.require_user_by_firebase_uid(db, firebase_uid)

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
        planner=result.planner,
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
    user = await user_service.require_user_by_firebase_uid(db, firebase_uid)

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
