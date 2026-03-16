"""
TrueShift - Event Model

Immutable event storage for event-driven architecture.
All user actions are stored as events for audit trail and state reconstruction.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class EventSource(str, Enum):
    """Source of the event."""
    MOBILE = "mobile"
    BACKEND = "backend"
    AI = "ai"
    SYSTEM = "system"


class EventType(str, Enum):
    """Types of events in the system."""
    # User Activity
    USER_REGISTERED = "user.registered"
    USER_PROFILE_UPDATED = "user.profile_updated"
    USER_CONSENT_UPDATED = "user.consent_updated"

    # Location Events
    LOCATION_UPDATED = "location.updated"
    LOCATION_CONTEXT_CHANGED = "location.context_changed"

    # Workout Events
    WORKOUT_STARTED = "workout.started"
    WORKOUT_COMPLETED = "workout.completed"
    WORKOUT_PAUSED = "workout.paused"
    WORKOUT_SET_LOGGED = "workout.set_logged"
    WORKOUT_EXERCISE_LOGGED = "workout.exercise_logged"

    # Health & Fitness
    HEALTH_SYNC = "health.sync"
    HEALTH_METRICS_RECEIVED = "health.metrics_received"
    STRAVA_ACTIVITY_SYNCED = "strava.activity_synced"

    # Digital Wellbeing
    SCREEN_TIME_LOGGED = "digital.screen_time_logged"
    APP_USAGE_SYNCED = "digital.app_usage_synced"

    # Vision / Camera
    IMAGE_CAPTURED = "vision.image_captured"
    VIDEO_CAPTURED = "vision.video_captured"
    VISION_ANALYSIS_COMPLETED = "vision.analysis_completed"

    # AI Events
    AI_RECOMMENDATION_GENERATED = "ai.recommendation_generated"
    AI_COACHING_DELIVERED = "ai.coaching_delivered"
    AI_FEEDBACK_RECEIVED = "ai.feedback_received"
    VOICE_SESSION_STARTED = "voice.session_started"
    VOICE_TURN_COMPLETED = "voice.turn_completed"

    # System Events
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"
    BACKGROUND_SYNC = "system.background_sync"


class Event(BaseModel):
    """
    Immutable event model.
    Core of the event-driven architecture.
    """

    __tablename__ = "events"

    # Event ownership
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Event identification
    event_type: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        default=EventSource.MOBILE.value,
        nullable=False,
    )

    # Event timing
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )

    # Event data
    payload: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Optional metadata
    session_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    device_info: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    correlation_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    # Processing status
    processed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Composite indexes for efficient querying
    __table_args__ = (
        Index("ix_events_user_type_time", "user_id", "event_type", "event_timestamp"),
        Index("ix_events_user_time", "user_id", "event_timestamp"),
        Index("ix_events_processed", "processed", "created_at"),
    )

    @classmethod
    def create(
        cls,
        user_id: str,
        event_type: EventType | str,
        payload: dict,
        source: EventSource = EventSource.MOBILE,
        event_timestamp: datetime | None = None,
        session_id: str | None = None,
        device_info: dict | None = None,
        correlation_id: str | None = None,
    ) -> "Event":
        """
        Factory method to create a new event.
        """
        from datetime import timezone

        return cls(
            user_id=user_id,
            event_type=event_type.value if isinstance(event_type, EventType) else event_type,
            source=source.value if isinstance(source, EventSource) else source,
            payload=payload,
            event_timestamp=event_timestamp or datetime.now(timezone.utc),
            session_id=session_id,
            device_info=device_info,
            correlation_id=correlation_id,
        )
