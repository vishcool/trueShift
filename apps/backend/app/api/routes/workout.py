"""
TrueShift - Workout Routes

Endpoints for generating and tracking workouts.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.event import EventSource, EventType
from app.models.workout import WorkoutPlan
from app.models.user_state import UserState, RecoveryStatus
from app.services.event_processor import EventPayload, EventProcessor
from app.services.user_service import user_service
from app.services.workout_service import workout_service

# Import Shared Schemas
from app.schemas.workout import (
    WorkoutGenerationRequest, 
    WorkoutLogRequest, 
    WorkoutPlanResponse
)

router = APIRouter()

# Note: Schemas are imported from app.schemas.workout

class WorkoutRecordRequest(BaseModel):
    """Request to record a full ad-hoc workout."""
    exercises: List[Dict[str, Any]]
    duration_minutes: int
    notes: Optional[str] = None
    completed_at: datetime
    session_id: Optional[str] = None

# ============================================================================
# Endpoints
# ============================================================================

@router.post("/generate", response_model=WorkoutPlanResponse)
async def generate_workout(
    request: WorkoutGenerationRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a personalized workout using Gemini.
    Delegates to WorkoutService.
    """
    # Verify user
    user = await user_service.require_user_by_firebase_uid(db, user_id)

    try:
        plan = await workout_service.generate_workout(db, user, request)
        
        return WorkoutPlanResponse(
            id=plan.id,
            created_at=plan.created_at,
            scheduled_date=plan.scheduled_date,
            status=plan.status,
            plan_data=plan.plan_data,
            completion_data=plan.completion_data,
            feedback_notes=plan.feedback_notes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-with-vision", response_model=WorkoutPlanResponse)
async def generate_workout_with_vision(
    file: UploadFile = File(...),
    duration_minutes: int = Form(45),
    fitness_level: str = Form("Intermediate"),
    goals: str = Form("General Fitness"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a personalized workout by analyzing equipment from an image.
    """
    # Verify user
    user = await user_service.require_user_by_firebase_uid(db, user_id)

    # Read image
    content = await file.read()

    # 1. Fetch User State (Recovery)
    state_result = await db.execute(select(UserState).where(UserState.user_id == user.id))
    user_state = state_result.scalar_one_or_none()
    
    recovery_score = 50 # Default
    if user_state:
        # Simple mapping
        status_map = {
            RecoveryStatus.FULLY_RECOVERED: 90,
            RecoveryStatus.WELL_RESTED: 75,
            RecoveryStatus.MODERATE: 50,
            RecoveryStatus.FATIGUED: 30,
            RecoveryStatus.EXHAUSTED: 10
        }
        recovery_score = status_map.get(user_state.recovery_status, 50)

    # 2. Fetch Recent History (Last 3 workouts)
    history_result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user.id)
        .order_by(desc(WorkoutPlan.created_at))
        .limit(3)
    )
    last_workouts = history_result.scalars().all()
    history_summary = "No recent workouts."
    if last_workouts:
        formatted_history = []
        for w in last_workouts:
             # Basic summary
             formatted_history.append(f"{w.created_at.strftime('%Y-%m-%d')}: {w.status}")
        history_summary = "; ".join(formatted_history)

    # Context for AI
    user_context = {
        "duration_minutes": duration_minutes,
        "fitness_level": fitness_level,
        "goals": goals,
        "recovery_score": recovery_score,
        "history": history_summary
    }

    # Call AI Service
    from app.services.ai_coach_service import ai_coach_service 
    
    llm_response = await ai_coach_service.generate_workout_from_image(
        image_bytes=content,
        user_context=user_context
    )

    if "error" in llm_response:
         raise HTTPException(status_code=500, detail=f"AI Generation failed: {llm_response['error']}")

    return WorkoutPlanResponse(
        id="draft-analysis",
        created_at=datetime.utcnow(),
        scheduled_date=None,
        status="draft",
        plan_data=llm_response,
        completion_data=None,
        feedback_notes=None
    )

@router.post("/record", response_model=WorkoutPlanResponse)
async def record_workout(
    request: WorkoutRecordRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Record a fully completed ad-hoc workout.
    """
    # Verify user
    user = await user_service.require_user_by_firebase_uid(db, user_id)

    # Create WorkoutPlan
    plan = WorkoutPlan(
        user_id=user.id,
        status="completed",
        plan_data={"exercises": request.exercises, "overview": "Ad-hoc Session"},
        completion_data={
            "exercises": request.exercises,
            "duration_minutes": request.duration_minutes,
            "session_id": request.session_id,
            "summary": {
                "exercise_count": len(request.exercises),
                "set_count": sum(len(exercise.get("performed_sets", [])) for exercise in request.exercises),
            },
        },
        feedback_notes=request.notes,
        completed_at=request.completed_at
    )
    db.add(plan)
    await db.flush()

    processor = EventProcessor(db)
    session_id = request.session_id or f"workout-{plan.id}"
    await processor.process(
        user_id=user.id,
        event_payload=EventPayload(
            event_type=EventType.WORKOUT_COMPLETED.value,
            payload={
                "workout_type": "ad_hoc",
                "duration_minutes": request.duration_minutes,
                "exercise_count": len(request.exercises),
            },
            timestamp=request.completed_at,
            session_id=session_id,
            correlation_id=f"workout-record:{user.id}:{request.completed_at.isoformat()}",
        ),
        source=EventSource.MOBILE,
    )

    for index, exercise in enumerate(request.exercises):
        await processor.process(
            user_id=user.id,
            event_payload=EventPayload(
                event_type=EventType.WORKOUT_EXERCISE_LOGGED.value,
                payload={
                    "index": index,
                    "name": exercise.get("name"),
                    "performed_sets": exercise.get("performed_sets", []),
                },
                timestamp=request.completed_at,
                session_id=session_id,
                correlation_id=f"workout-exercise:{user.id}:{request.completed_at.isoformat()}:{index}",
            ),
            source=EventSource.MOBILE,
        )

    await db.commit()
    await db.refresh(plan)

    return WorkoutPlanResponse(
        id=plan.id,
        created_at=plan.created_at,
        scheduled_date=plan.scheduled_date,
        status=plan.status,
        plan_data=plan.plan_data,
        completion_data=plan.completion_data,
        feedback_notes=plan.feedback_notes
    )

@router.post("/log", response_model=WorkoutPlanResponse)
async def log_workout(
    request: WorkoutLogRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Log a completed workout.
    """
    # Verify user
    user = await user_service.require_user_by_firebase_uid(db, user_id)

    # Get Plan
    result = await db.execute(select(WorkoutPlan).where(WorkoutPlan.id == request.plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Workout Plan not found")
        
    if plan.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to log for this plan")

    # Update Plan
    plan.status = "completed"
    plan.completion_data = request.completion_data
    plan.feedback_notes = request.feedback
    plan.completed_at = datetime.utcnow()

    processor = EventProcessor(db)
    await processor.process(
        user_id=user.id,
        event_payload=EventPayload(
            event_type=EventType.WORKOUT_COMPLETED.value,
            payload={
                "workout_type": plan.plan_data.get("overview", "planned_session"),
                "duration_minutes": request.completion_data.get("duration_minutes"),
                "exercise_count": len(request.completion_data.get("exercises", [])),
            },
            timestamp=plan.completed_at,
            session_id=request.completion_data.get("session_id"),
            correlation_id=f"workout-log:{user.id}:{plan.id}:{plan.completed_at.isoformat()}",
        ),
        source=EventSource.MOBILE,
    )
    
    await db.commit()
    await db.refresh(plan)

    return WorkoutPlanResponse(
        id=plan.id,
        created_at=plan.created_at,
        scheduled_date=plan.scheduled_date,
        status=plan.status,
        plan_data=plan.plan_data,
        completion_data=plan.completion_data,
        feedback_notes=plan.feedback_notes
    )

@router.get("/history", response_model=List[WorkoutPlanResponse])
async def get_workout_history(
    limit: int = 10,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get past workouts.
    """
    # Verify user
    user = await user_service.require_user_by_firebase_uid(db, user_id)

    # Get Plans
    result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user.id)
        .order_by(desc(WorkoutPlan.created_at))
        .limit(limit)
    )
    plans = result.scalars().all()

    return [
        WorkoutPlanResponse(
            id=p.id,
            created_at=p.created_at,
            scheduled_date=p.scheduled_date,
            status=p.status,
            plan_data=p.plan_data,
            completion_data=p.completion_data,
            feedback_notes=p.feedback_notes
        ) for p in plans
    ]
