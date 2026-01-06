"""
TrueShift - Vision & Movement Analysis Log

Stores results from client-side MoveNet/computer vision analysis.
Used by WorkoutAgent to adjust form correctness and difficulty.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class MovementAnalysis(BaseModel):
    """
    Log of a single exercise set analyzed by computer vision.
    """
    __tablename__ = "vision_logs"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    exercise_name: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "squat", "pushup"
    
    # Analysis Summary
    rep_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_confidence_score: Mapped[float] = mapped_column(Float, nullable=True) # 0.0 - 1.0 confidence in pose detection
    
    # Form Quality
    form_score: Mapped[float] = mapped_column(Float, nullable=True) # 0-100 score
    error_flags: Mapped[list] = mapped_column(JSONB, default=list) # e.g. ["knee_valgus", "back_rounded"]
    
    # Raw Data (optional, might be too big for DB, store link to blob if needed later)
    # For phase 1, we just store the summary JSON report
    analysis_report: Mapped[dict] = mapped_column(JSONB, default=dict) # Full JSON report from client
