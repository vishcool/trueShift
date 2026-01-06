"""
TrueShift - User Preferences Model

Stores static or semi-static user preferences, goals, and baseline constraints.
"""

from typing import Optional
from sqlalchemy import ForeignKey, String, Integer, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class UserPreferences(BaseModel):
    """
    User preferences and baseline configuration.
    """
    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Physical baseline
    fitness_level: Mapped[str] = mapped_column(String(50), default="beginner")
    physical_constraints: Mapped[list] = mapped_column(JSONB, default=list)  # e.g. ["knee_pain", "no_jumping"]
    equipment_available: Mapped[list] = mapped_column(JSONB, default=list)   # e.g. ["dumbbells", "yoga_mat"]

    # Goals
    primary_goal: Mapped[str] = mapped_column(String(100), nullable=True) # e.g. "weight_loss", "muscle_gain"
    weekly_workout_days_goal: Mapped[int] = mapped_column(Integer, default=3)
    
    # Scheduling preferences
    preferred_workout_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # e.g. "morning", "evening" or "08:00"

    # Mental Wellness
    meditation_experience: Mapped[str] = mapped_column(String(50), default="none")
    stress_management_goals: Mapped[list] = mapped_column(JSONB, default=list)

    # Privacy / AI interaction settings
    ai_coaching_style: Mapped[str] = mapped_column(String(50), default="encouraging") # "strict", "analytical", "encouraging"
