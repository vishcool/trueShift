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
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.workout import WorkoutPlan
from app.models.user_state import UserState, RecoveryStatus
from app.ai.llm_service import gemini_service

router = APIRouter()

# ============================================================================
# Schemas
# ============================================================================

class WorkoutGenerationRequest(BaseModel):
    """Request to generate a workout."""
    target_muscle_group: Optional[str] = "Full Body" # e.g. "Chest", "Legs"
    duration_minutes: Optional[int] = 45
    equipment: Optional[List[str]] = [] # e.g. ["Dumbbells", "Bench"]
    fitness_level: Optional[str] = "Intermediate" # Beginner, Intermediate, Advanced
    goals: Optional[str] = None # e.g. "Strength", "Hypertrophy"

class WorkoutLogRequest(BaseModel):
    """Request to log a completed workout."""
    plan_id: str
    completion_data: Dict[str, Any] # Actual sets/reps performed
    feedback: Optional[str] = None

class WorkoutPlanResponse(BaseModel):
    """Response model for workout plans."""
    id: str
    created_at: datetime
    scheduled_date: Optional[datetime]
    status: str
    plan_data: Dict[str, Any]
    completion_data: Optional[Dict[str, Any]]
    feedback_notes: Optional[str]

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
    """
    # Verify user
    result = await db.execute(select(User).where(User.firebase_uid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch Recent History (Last 5 workouts) to enable Progressive Overload
    history_result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user.id)
        .where(WorkoutPlan.status == "completed")
        .order_by(desc(WorkoutPlan.created_at))
        .limit(5)
    )
    last_workouts = history_result.scalars().all()
    
    history_context = "No previous workout history available. Start with standard baseline volume."
    if last_workouts:
        formatted_history = []
        for w in last_workouts:
             # Extract exercises performed
             exercises = w.completion_data.get("exercises", []) if w.completion_data else w.plan_data.get("exercises", [])
             ex_summary = ", ".join([f"{ex.get('name')} ({ex.get('sets')}x{ex.get('reps')})" for ex in exercises])
             formatted_history.append(f"- {w.created_at.strftime('%Y-%m-%d')}: {ex_summary}")
        history_context = "\n".join(formatted_history)

    # Construct Prompt
    prompt = f"""
    Act as a strict, elite strength and conditioning coach focused on PROGRESSIVE OVERLOAD.
    Design a PRECISE workout plan that micro-increases volume/intensity based on previous history.
    
    User Profile:
    - Target: {request.target_muscle_group}
    - Duration: {request.duration_minutes} minutes
    - Level: {request.fitness_level}
    - Equipment: {", ".join(request.equipment) if request.equipment else "Bodyweight only"}
    - Specific Goals: {request.goals or "General Fitness"}
    
    PREVIOUS TRAINING HISTORY (Most Recent First):
    {history_context}
    
    Directives:
    1. ANALYZE HISTORY: Look at the reps/sets used in previous sessions for similar exercises.
       - IF MATCH FOUND: Apply PROGESSIVE OVERLOAD. Increase reps by 1-2 OR add 1 set. Small, micro-increases.
       - IF NO MATCH: Use standard baseline volume (3 sets, 8-12 reps).
    
    2. BE PRECISE: Give EXACT numbers (e.g., "11 reps" if they did "10" last time). Do NOT give ranges.
    3. BE AUTHORITATIVE: Tell the user exactly what to do.
    4. MAXIMIZE EFFICIENCY: Fill the {request.duration_minutes} minutes.
    
    Return the response strictly as a JSON object with the following structure:
    {{
      "overview": "Direct command describing the progression (e.g. 'Increased reps on Squats. Push for 11 today.')",
      "exercises": [
        {{
          "name": "Exercise Name",
          "sets": 3,
          "reps": "11",
          "rest_seconds": 60,
          "notes": "Progression note or form cue (e.g. 'Beat last week's 10 reps.')"
        }}
      ]
    }}
    Do not include markdown formatting like ```json or ```. Just the raw JSON.
    """

    # Call LLM
    llm_response = await gemini_service.generate_content(
        prompt=prompt, 
        response_schema={"type": "object"} # Hinting we want object
    )
    
    if "error" in llm_response:
         raise HTTPException(status_code=500, detail=f"AI Generation failed: {llm_response['error']}")

    # Create WorkoutPlan
    plan = WorkoutPlan(
        user_id=user.id,
        status="generated",
        plan_data=llm_response,
        scheduled_date=datetime.utcnow()
    )
    db.add(plan)
    await db.flush() # Get ID

    return WorkoutPlanResponse(
        id=plan.id,
        created_at=plan.created_at,
        scheduled_date=plan.scheduled_date,
        status=plan.status,
        plan_data=plan.plan_data,
        completion_data=plan.completion_data,
        feedback_notes=plan.feedback_notes
    )

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
    result = await db.execute(select(User).where(User.firebase_uid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Read image
    content = await file.read()

    # 1. Fetch User State (Recovery)
    state_result = await db.execute(select(UserState).where(UserState.user_id == user.id))
    user_state = state_result.scalar_one_or_none()
    
    recovery_score = 50 # Default
    if user_state:
        # Simple mapping: fully_recovered=90, well_rested=75, moderate=50, fatigued=30, exhausted=10
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
             # Basic summary: "Legs (Completed)" or "Full Body (Generated)"
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
    from app.services.ai_coach_service import ai_coach_service # Lazy import to avoid circular dep if any
    
    llm_response = await ai_coach_service.generate_workout_from_image(
        image_bytes=content,
        user_context=user_context
    )

    if "error" in llm_response:
         raise HTTPException(status_code=500, detail=f"AI Generation failed: {llm_response['error']}")

    # Return pure analysis (no DB creation for scans)
    # We strip the ID/Date/Status fields since it's just a raw analysis response
    # We can perform a mock simple response or change the return type. 
    # For now, we return a "Draft" structure.
    return WorkoutPlanResponse(
        id="draft-analysis",
        created_at=datetime.utcnow(),
        scheduled_date=None,
        status="draft",
        plan_data=llm_response,
        completion_data=None,
        feedback_notes=None
    )

class WorkoutRecordRequest(BaseModel):
    """Request to record a full ad-hoc workout."""
    exercises: List[Dict[str, Any]]
    duration_minutes: int
    notes: Optional[str] = None
    completed_at: datetime

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
    result = await db.execute(select(User).where(User.firebase_uid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create WorkoutPlan
    plan = WorkoutPlan(
        user_id=user.id,
        status="completed",
        plan_data={"exercises": request.exercises, "overview": "Ad-hoc Session"},
        completion_data={"exercises": request.exercises}, # For now, target=actual
        feedback_notes=request.notes,
        completed_at=request.completed_at
    )
    db.add(plan)
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
    result = await db.execute(select(User).where(User.firebase_uid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
    # Verify user (getting ID)
    result = await db.execute(select(User).where(User.firebase_uid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
