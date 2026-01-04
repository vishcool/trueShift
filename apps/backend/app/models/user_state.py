"""
TrueShift - User State Model

Continuously updated user state model.
Represents the current understanding of the user's condition.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LocationContext(str, Enum):
    """Context derived from user's location."""
    HOME = "home"
    GYM = "gym"
    PARK = "park"
    OFFICE = "office"
    OUTDOORS = "outdoors"
    TRANSIT = "transit"
    UNKNOWN = "unknown"


class ActivityLevel(str, Enum):
    """Current activity level."""
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    INTENSE = "intense"


class RecoveryStatus(str, Enum):
    """Recovery status assessment."""
    FULLY_RECOVERED = "fully_recovered"
    WELL_RESTED = "well_rested"
    MODERATE = "moderate"
    FATIGUED = "fatigued"
    EXHAUSTED = "exhausted"


class UserState(BaseModel):
    """
    Current user state - continuously updated based on events.
    Single source of truth for the user's current condition.
    """

    __tablename__ = "user_states"

    # User reference
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Last activity timestamp
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # =========================================================================
    # PHYSICAL STATE
    # =========================================================================
    
    # Activity & Movement
    current_activity_level: Mapped[str] = mapped_column(
        String(50),
        default=ActivityLevel.SEDENTARY.value,
        nullable=False,
    )
    steps_today: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    calories_burned_today: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    active_minutes_today: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Recent workout info
    last_workout_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_workout_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    workouts_this_week: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Recovery metrics
    recovery_status: Mapped[str] = mapped_column(
        String(50),
        default=RecoveryStatus.WELL_RESTED.value,
        nullable=False,
    )
    sleep_hours_last_night: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    sleep_quality_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    resting_heart_rate: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    hrv_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # =========================================================================
    # LOCATION & ENVIRONMENT
    # =========================================================================
    
    current_location_context: Mapped[str] = mapped_column(
        String(50),
        default=LocationContext.UNKNOWN.value,
        nullable=False,
    )
    current_latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    current_longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Favorite/frequent places
    known_places: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # =========================================================================
    # DIGITAL WELLBEING
    # =========================================================================
    
    screen_time_today_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    productive_time_today_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    app_usage_today: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # =========================================================================
    # AI COACHING STATE
    # =========================================================================
    
    # Current goals and focus
    active_goals: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    current_focus_area: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Last AI interaction
    last_recommendation_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_recommendation: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # User engagement
    recommendations_followed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    recommendations_dismissed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =========================================================================
    # EXTENDED STATE (Flexible)
    # =========================================================================
    
    extended_state: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    def get_context_summary(self) -> dict:
        """
        Get a summary of current state for AI context.
        """
        return {
            "physical": {
                "activity_level": self.current_activity_level,
                "steps_today": self.steps_today,
                "active_minutes": self.active_minutes_today,
                "recovery_status": self.recovery_status,
                "sleep_hours": self.sleep_hours_last_night,
                "last_workout": self.last_workout_type,
                "workouts_this_week": self.workouts_this_week,
            },
            "location": {
                "context": self.current_location_context,
            },
            "digital": {
                "screen_time_minutes": self.screen_time_today_minutes,
                "productive_minutes": self.productive_time_today_minutes,
            },
            "goals": self.active_goals,
            "focus_area": self.current_focus_area,
        }
