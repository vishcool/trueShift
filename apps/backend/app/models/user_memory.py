"""
TrueShift - User Memory Model

Stores structured memory for AI agent personalization.
Includes fitness profile, current condition, and preferences.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class UserMemory(BaseModel):
    """
    Structured memory storage for AI agent personalization.
    Stores user's fitness profile, current condition, and conversation context.
    """
    __tablename__ = "user_memory"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Fitness Profile
    fitness_profile: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="User's fitness level, goals, equipment, preferences"
    )
    # Example structure:
    # {
    #   "level": "intermediate",
    #   "goals": ["build_muscle", "lose_fat"],
    #   "equipment": ["dumbbells", "barbell"],
    #   "preferred_duration": 45,
    #   "preferred_exercises": ["bench_press", "squats"],
    #   "avoid_exercises": ["burpees"]
    # }

    # Current Condition
    current_condition: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="User's current physical state and recovery"
    )
    # Example structure:
    # {
    #   "recovery_status": "well_rested",
    #   "energy_level": "high",
    #   "soreness": ["legs", "chest"],
    #   "last_workout_date": "2024-01-30",
    #   "sleep_quality": "good",
    #   "stress_level": "low"
    # }

    # Conversation Context
    conversation_context: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Recent conversation topics and session info"
    )
    # Example structure:
    # {
    #   "recent_topics": ["chest_workout", "form_tips"],
    #   "current_plan_id": "uuid",
    #   "session_id": "session_123",
    #   "last_interaction": "2024-01-30T10:00:00Z"
    # }

    # Metadata
    profile_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    condition_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "fitness_profile": self.fitness_profile,
            "current_condition": self.current_condition,
            "conversation_context": self.conversation_context,
            "profile_updated_at": self.profile_updated_at.isoformat() if self.profile_updated_at else None,
            "condition_updated_at": self.condition_updated_at.isoformat() if self.condition_updated_at else None,
        }
