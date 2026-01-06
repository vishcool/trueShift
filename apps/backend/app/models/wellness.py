"""
TrueShift - Wellness Data Models

Models for tracking subjective and objective wellness data:
- SleepLog (Objective/Subjective)
- MoodLog (Subjective)
- PainLog (Subjective)
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class SleepLog(BaseModel):
    """
    Daily sleep record.
    """
    __tablename__ = "sleep_logs"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False) # The "night of" date
    
    # Metrics
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False)
    quality_score: Mapped[int] = mapped_column(Integer, nullable=True) # 1-100 or 1-10
    
    # Stages (optional, from wearables)
    deep_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rem_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    awake_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    source: Mapped[str] = mapped_column(String(50), default="manual") # manual, apple_health, oura, etc.


class MoodLog(BaseModel):
    """
    Point-in-time mood check-in.
    """
    __tablename__ = "mood_logs"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    energy_level: Mapped[int] = mapped_column(Integer, nullable=False) # 1-10
    stress_level: Mapped[int] = mapped_column(Integer, nullable=False) # 1-10
    mood_tags: Mapped[list] = mapped_column(JSONB, default=list) # ["anxious", "excited", "tired"]
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PainLog(BaseModel):
    """
    Pain or Injury tracking log.
    """
    __tablename__ = "pain_logs"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    body_part: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False) # 1-10
    pain_type: Mapped[str] = mapped_column(String(50), nullable=True) # "sharp", "dull", "soreness"
    
    is_injury: Mapped[bool] = mapped_column(default=False) # True if diagnosed injury, False if just soreness
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
