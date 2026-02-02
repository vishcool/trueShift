"""
TrueShift - User Behavior & Coaching History

Models for the "Behavior Coach" to track long-term patterns and intervention effectiveness.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class BehavioralMarkers(BaseModel):
    """
    Aggregated behavioral stats and markers.
    One row per user, continuously updated (Digital Twin aspect).
    """
    __tablename__ = "behavioral_markers"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Habits & Streaks
    current_workout_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_workout_streak: Mapped[int] = mapped_column(Integer, default=0)
    
    # Adherence
    plan_adherence_score: Mapped[float] = mapped_column(Float, default=1.0) # 0.0 - 1.0
    
    # Inferred Preferences (AI learned)
    inferred_preferences: Mapped[dict] = mapped_column(JSONB, default=dict) # e.g. {"preferred_day": "Monday"}


class InterventionHistory(BaseModel):
    """
    Log of AI interventions/suggestions and user response.
    Used to reinforce learning (RLHF).
    """
    __tablename__ = "intervention_history"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False) # "CoachingAgent", "RecoveryAgent"
    intervention_type: Mapped[str] = mapped_column(String(50), nullable=False) # "prompt", "workout_adjustment", "notification"
    
    content: Mapped[dict] = mapped_column(JSONB, nullable=False) # The actual advice given
    
    # User Response
    user_action: Mapped[str] = mapped_column(String(50), nullable=True) # "accepted", "dismissed", "completed", "ignored"
    user_feedback_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 1-5 rating if given
