"""
TrueShift - Events Routes

Event ingestion endpoints for mobile app data.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.event import EventSource
from app.services.event_processor import EventPayload, EventProcessor

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class EventRequest(BaseModel):
    """Single event request."""
    event_type: str = Field(..., description="Type of event")
    payload: dict = Field(default_factory=dict, description="Event data")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")
    session_id: Optional[str] = Field(None, description="Mobile session ID")
    device_info: Optional[dict] = Field(None, description="Device information")


class BatchEventRequest(BaseModel):
    """Batch event request for background sync."""
    events: List[EventRequest] = Field(..., description="List of events")


class EventResponse(BaseModel):
    """Event response."""
    event_id: str
    event_type: str
    processed: bool
    timestamp: str


class BatchEventResponse(BaseModel):
    """Batch event response."""
    processed_count: int
    events: List[EventResponse]


# ============================================================================
# Endpoints
# ============================================================================


@router.post("", response_model=EventResponse)
async def ingest_event(
    request: EventRequest,
    firebase_uid: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a single event from mobile app.
    """
    # Get user
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Process event
    processor = EventProcessor(db)
    
    # Check consent requirements
    required_consents = processor.get_required_consents(request.event_type)
    if required_consents and not user.has_required_consents(required_consents):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required consents: {required_consents}",
        )

    try:
        event_payload = EventPayload(
            event_type=request.event_type,
            payload=request.payload,
            timestamp=request.timestamp,
            session_id=request.session_id,
            device_info=request.device_info,
        )
        
        event = await processor.process(
            user_id=user.id,
            event_payload=event_payload,
            source=EventSource.MOBILE,
        )

        return EventResponse(
            event_id=event.id,
            event_type=event.event_type,
            processed=event.processed,
            timestamp=event.event_timestamp.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/batch", response_model=BatchEventResponse)
async def ingest_events_batch(
    request: BatchEventRequest,
    firebase_uid: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a batch of events (for background sync).
    Events are sorted by timestamp and processed in order.
    """
    # Get user
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Convert to EventPayload objects
    event_payloads = [
        EventPayload(
            event_type=e.event_type,
            payload=e.payload,
            timestamp=e.timestamp,
            session_id=e.session_id,
            device_info=e.device_info,
        )
        for e in request.events
    ]

    # Process batch
    processor = EventProcessor(db)
    events = await processor.process_batch(
        user_id=user.id,
        events=event_payloads,
        source=EventSource.MOBILE,
    )

    return BatchEventResponse(
        processed_count=len(events),
        events=[
            EventResponse(
                event_id=event.id,
                event_type=event.event_type,
                processed=event.processed,
                timestamp=event.event_timestamp.isoformat(),
            )
            for event in events
        ],
    )


@router.get("/types")
async def get_event_types():
    """
    Get list of supported event types.
    """
    from app.models.event import EventType
    
    return {
        "event_types": [e.value for e in EventType],
    }
