"""
TrueShift - Agent Memory Service

Manages user memory for AI agent personalization.
Retrieves and updates fitness profile, current condition, and conversation history.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.user_memory import UserMemory
from app.models.conversation import ConversationLog
from app.models.user_state import UserState
from app.models.workout import WorkoutPlan

logger = logging.getLogger(__name__)


class AgentMemoryService:
    """
    Service for managing user memory and context for AI agents.
    """

    @staticmethod
    async def get_or_create_memory(db: AsyncSession, user_id: str) -> UserMemory:
        """
        Get existing user memory or create new one with defaults.
        """
        result = await db.execute(
            select(UserMemory).where(UserMemory.user_id == user_id)
        )
        memory = result.scalar_one_or_none()

        if not memory:
            memory = UserMemory(
                user_id=user_id,
                fitness_profile={
                    "level": "intermediate",
                    "goals": [],
                    "equipment": [],
                    "preferred_duration": 30,
                    "preferred_exercises": [],
                    "avoid_exercises": []
                },
                current_condition={
                    "recovery_status": "unknown",
                    "energy_level": "medium",
                    "soreness": [],
                    "last_workout_date": None,
                    "sleep_quality": "unknown",
                    "stress_level": "medium"
                },
                conversation_context={
                    "recent_topics": [],
                    "current_plan_id": None,
                    "session_id": None,
                    "last_interaction": None
                }
            )
            db.add(memory)
            await db.commit()
            await db.refresh(memory)

        return memory

    @staticmethod
    async def get_user_memory(db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """
        Get complete user memory including profile, condition, and recent conversations.
        """
        memory = await AgentMemoryService.get_or_create_memory(db, user_id)

        # Get recent conversation history
        conversation_history = await AgentMemoryService.get_conversation_history(
            db, user_id, limit=10
        )

        # Get user state for current condition
        user_state = await AgentMemoryService.get_current_state(db, user_id)

        # Get recent workouts
        recent_workouts = await AgentMemoryService.get_recent_workouts(db, user_id, limit=5)

        return {
            "fitness_profile": memory.fitness_profile,
            "current_condition": {
                **memory.current_condition,
                **(user_state or {})
            },
            "conversation_context": memory.conversation_context,
            "conversation_history": conversation_history,
            "recent_workouts": recent_workouts,
        }

    @staticmethod
    async def update_fitness_profile(
        db: AsyncSession, 
        user_id: str, 
        profile_updates: Dict[str, Any]
    ) -> UserMemory:
        """
        Update user's fitness profile.
        """
        memory = await AgentMemoryService.get_or_create_memory(db, user_id)
        
        # Merge updates
        memory.fitness_profile = {**memory.fitness_profile, **profile_updates}
        memory.profile_updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(memory)
        
        return memory

    @staticmethod
    async def update_condition(
        db: AsyncSession, 
        user_id: str, 
        condition_updates: Dict[str, Any]
    ) -> UserMemory:
        """
        Update user's current condition.
        """
        memory = await AgentMemoryService.get_or_create_memory(db, user_id)
        
        # Merge updates
        memory.current_condition = {**memory.current_condition, **condition_updates}
        memory.condition_updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(memory)
        
        return memory

    @staticmethod
    async def update_conversation_context(
        db: AsyncSession,
        user_id: str,
        context_updates: Dict[str, Any]
    ) -> UserMemory:
        """
        Update conversation context (session, topics, current plan).
        """
        memory = await AgentMemoryService.get_or_create_memory(db, user_id)
        
        # Merge updates
        memory.conversation_context = {**memory.conversation_context, **context_updates}
        memory.conversation_context["last_interaction"] = datetime.utcnow().isoformat()
        
        await db.commit()
        await db.refresh(memory)
        
        return memory

    @staticmethod
    async def get_conversation_history(
        db: AsyncSession, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation messages.
        """
        result = await db.execute(
            select(ConversationLog)
            .where(ConversationLog.user_id == user_id)
            .order_by(desc(ConversationLog.created_at))
            .limit(limit)
        )
        logs = result.scalars().all()
        
        # Reverse to get chronological order
        return [log.to_dict() for log in reversed(logs)]

    @staticmethod
    async def save_conversation(
        db: AsyncSession,
        user_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = "WorkoutAgent",
        session_id: Optional[str] = None
    ) -> ConversationLog:
        """
        Save a conversation message.
        """
        log = ConversationLog(
            user_id=user_id,
            role=role,
            content=content,
            agent_name=agent_name,
            session_id=session_id
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        
        return log

    @staticmethod
    async def get_current_state(db: AsyncSession, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's current physical state.
        """
        result = await db.execute(
            select(UserState).where(UserState.user_id == user_id)
        )
        state = result.scalar_one_or_none()
        
        if not state:
            return None
        
        return {
            "recovery_status": state.physical.get("recovery_status", "unknown"),
            "steps_today": state.physical.get("steps_today", 0),
            "active_minutes": state.physical.get("active_minutes", 0),
            "workouts_this_week": state.physical.get("workouts_this_week", 0),
        }

    @staticmethod
    async def get_recent_workouts(
        db: AsyncSession, 
        user_id: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent workout plans.
        """
        result = await db.execute(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id)
            .order_by(desc(WorkoutPlan.created_at))
            .limit(limit)
        )
        workouts = result.scalars().all()
        
        return [
            {
                "id": str(workout.id),
                "created_at": workout.created_at.isoformat(),
                "status": workout.status,
                "overview": workout.plan_data.get("overview", ""),
                "exercise_count": len(workout.plan_data.get("exercises", []))
            }
            for workout in workouts
        ]


# Global instance
agent_memory_service = AgentMemoryService()
