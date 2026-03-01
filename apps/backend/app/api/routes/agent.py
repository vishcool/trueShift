"""
TrueShift - Agent API Routes

Endpoints for AI agent chat and memory management.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.agent_chat_service import agent_chat_service
from app.services.agent_memory_service import agent_memory_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = Field(default=None)
    session_id: Optional[str] = Field(default=None)


class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class FitnessProfileUpdate(BaseModel):
    level: Optional[str] = None
    goals: Optional[list[str]] = None
    equipment: Optional[list[str]] = None
    preferred_duration: Optional[int] = None
    preferred_exercises: Optional[list[str]] = None
    avoid_exercises: Optional[list[str]] = None


class ConditionUpdate(BaseModel):
    recovery_status: Optional[str] = None
    energy_level: Optional[str] = None
    soreness: Optional[list[str]] = None
    sleep_quality: Optional[str] = None
    stress_level: Optional[str] = None


# Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with AI workout coach.
    
    The agent has memory of:
    - User's fitness profile (level, goals, equipment)
    - Current condition (recovery, energy, soreness)
    - Recent conversation history
    - Recent workouts
    
    Context can include:
    - current_plan: Current workout plan being discussed
    - current_plan_id: ID of current workout plan
    - equipment: Override equipment list
    - time: Override time preference
    """
    try:
        # Merge session_id into context
        context = request.context or {}
        if request.session_id:
            context["session_id"] = request.session_id
        
        result = await agent_chat_service.chat(
            db=db,
            user_id=str(current_user.id),
            message=request.message,
            context=context
        )
        
        return ChatResponse(
            response=result.get("response", ""),
            conversation_id=result.get("conversation_id"),
            action=result.get("action"),
            data=result.get("data"),
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


@router.get("/memory")
async def get_user_memory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's complete memory (fitness profile, condition, conversation history).
    """
    try:
        memory = await agent_memory_service.get_user_memory(
            db=db,
            user_id=str(current_user.id)
        )
        return memory
        
    except Exception as e:
        logger.error(f"Get memory error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user memory"
        )


@router.put("/profile")
async def update_fitness_profile(
    profile: FitnessProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's fitness profile.
    """
    try:
        # Convert to dict, excluding None values
        updates = profile.model_dump(exclude_none=True)
        
        memory = await agent_memory_service.update_fitness_profile(
            db=db,
            user_id=str(current_user.id),
            profile_updates=updates
        )
        
        return {
            "message": "Fitness profile updated",
            "profile": memory.fitness_profile
        }
        
    except Exception as e:
        logger.error(f"Update profile error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update fitness profile"
        )


@router.put("/condition")
async def update_current_condition(
    condition: ConditionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's current physical condition.
    """
    try:
        # Convert to dict, excluding None values
        updates = condition.model_dump(exclude_none=True)
        
        memory = await agent_memory_service.update_condition(
            db=db,
            user_id=str(current_user.id),
            condition_updates=updates
        )
        
        return {
            "message": "Condition updated",
            "condition": memory.current_condition
        }
        
    except Exception as e:
        logger.error(f"Update condition error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update condition"
        )


@router.get("/conversation/history")
async def get_conversation_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation history.
    """
    try:
        history = await agent_memory_service.get_conversation_history(
            db=db,
            user_id=str(current_user.id),
            limit=limit
        )
        
        return {"history": history}
        
    except Exception as e:
        logger.error(f"Get history error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )
