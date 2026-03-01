"""
TrueShift - Diet Routes

Diet planner endpoints for macro targets and meal templates.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.user_state import UserState
from app.schemas.diet import DietPlanRequest, DietPlanResponse
from app.services.diet_service import diet_service

router = APIRouter()


@router.post("/generate", response_model=DietPlanResponse)
async def generate_diet_plan(
    request: DietPlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.firebase_uid == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    state_result = await db.execute(select(UserState).where(UserState.user_id == user.id))
    state = state_result.scalar_one_or_none()

    fitness_profile = (user.preferences or {}).get("fitness_profile", {})
    voice_preferences = (user.preferences or {}).get("voice_preferences", {})

    user_context = {
        "fitness_profile": fitness_profile,
        "voice_preferences": voice_preferences,
        "recovery_status": state.recovery_status if state else "unknown",
        "workouts_this_week": state.workouts_this_week if state else 0,
        "activity_level": state.current_activity_level if state else "unknown",
    }

    try:
        generated = await diet_service.generate_plan(request, user_context)
        return DietPlanResponse(**generated)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate diet plan: {exc}")
