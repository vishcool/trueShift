"""
TrueShift - Event Processor

Validates, routes, and processes incoming events.
Entry point for all event ingestion.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventSource, EventType
from app.services.user_state_engine import UserStateEngine


class EventPayload(BaseModel):
    """
    Incoming event payload from mobile or external sources.
    """
    event_type: str = Field(..., description="Type of event")
    payload: dict = Field(default_factory=dict, description="Event data")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")
    session_id: Optional[str] = Field(None, description="Session ID")
    device_info: Optional[dict] = Field(None, description="Device information")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")


class EventProcessor:
    """
    Processes incoming events.
    Validates, persists, and triggers state updates.
    """

    # Event types that require specific consents
    CONSENT_REQUIREMENTS = {
        EventType.LOCATION_UPDATED.value: ["location_tracking"],
        EventType.LOCATION_CONTEXT_CHANGED.value: ["location_tracking"],
        EventType.HEALTH_SYNC.value: ["health_data"],
        EventType.HEALTH_METRICS_RECEIVED.value: ["health_data"],
        EventType.IMAGE_CAPTURED.value: ["camera_access"],
        EventType.VIDEO_CAPTURED.value: ["camera_access"],
        EventType.SCREEN_TIME_LOGGED.value: ["digital_wellbeing"],
        EventType.APP_USAGE_SYNCED.value: ["digital_wellbeing"],
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_engine = UserStateEngine(db)

    async def process(
        self,
        user_id: str,
        event_payload: EventPayload,
        source: EventSource = EventSource.MOBILE,
    ) -> Event:
        """
        Process an incoming event.

        1. Validate event type
        2. Create event record
        3. Trigger state update
        4. Return created event
        """
        # Validate event type is known
        self._validate_event_type(event_payload.event_type)

        # Create event record
        event = Event.create(
            user_id=user_id,
            event_type=event_payload.event_type,
            payload=event_payload.payload,
            source=source,
            event_timestamp=event_payload.timestamp or datetime.now(timezone.utc),
            session_id=event_payload.session_id,
            device_info=event_payload.device_info,
            correlation_id=event_payload.correlation_id or str(uuid4()),
        )

        # Persist event
        self.db.add(event)
        await self.db.flush()

        # Update user state
        await self.state_engine.process_event(event)

        return event

    async def process_batch(
        self,
        user_id: str,
        events: list[EventPayload],
        source: EventSource = EventSource.MOBILE,
    ) -> list[Event]:
        """
        Process a batch of events (for background sync).
        Events are sorted by timestamp and processed in order.
        """
        # Sort by timestamp
        sorted_events = sorted(
            events,
            key=lambda e: e.timestamp or datetime.now(timezone.utc),
        )

        processed = []
        for event_payload in sorted_events:
            try:
                event = await self.process(user_id, event_payload, source)
                processed.append(event)
            except ValueError as e:
                # Log invalid events but continue processing
                print(f"Skipping invalid event: {e}")
                continue

        return processed

    def _validate_event_type(self, event_type: str) -> None:
        """
        Validate that the event type is known.
        """
        valid_types = {e.value for e in EventType}
        if event_type not in valid_types:
            raise ValueError(f"Unknown event type: {event_type}")

    def get_required_consents(self, event_type: str) -> list[str]:
        """
        Get required consents for an event type.
        """
        return self.CONSENT_REQUIREMENTS.get(event_type, [])
