"""
TrueShift - Workout Management Models

Stores generated workout plans and their execution status.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class WorkoutPlan(BaseModel):
    """
    A generated workout plan for a user.
    """
    __tablename__ = "workout_plans"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status: "generated", "in_progress", "completed", "skipped"
    status: Mapped[str] = mapped_column(String(50), default="generated", index=True)
    
    # The generated plan details (JSON)
    # Structure example:
    # {
    #   "overview": "Full Body Strength",
    #   "exercises": [
    #     {"name": "Squat", "sets": 3, "reps": 10, "rest": 60, "notes": "Keep back straight"},
    #     ...
    #   ]
    # }
    plan_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Execution data (optional link to logs or summary of what was actually done)
    completion_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    feedback_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
