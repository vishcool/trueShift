"""
TrueShift - User State Engine

Core engine that maintains and updates user state based on incoming events.
This is the heart of the behavior intelligence system.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventType
from app.models.user_state import (
    ActivityLevel,
    LocationContext,
    RecoveryStatus,
    UserState,
)


class UserStateEngine:
    """
    Maintains continuously updated user state.
    Processes events and updates state accordingly.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_state(self, user_id: str) -> Optional[UserState]:
        """
        Get current user state.
        """
        result = await self.db.execute(
            select(UserState).where(UserState.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_state(self, user_id: str) -> UserState:
        """
        Get existing state or create a new one.
        """
        state = await self.get_state(user_id)
        if state is None:
            state = UserState(user_id=user_id)
            self.db.add(state)
            await self.db.flush()
        return state

    async def process_event(self, event: Event) -> UserState:
        """
        Process an event and update user state accordingly.
        """
        state = await self.get_or_create_state(event.user_id)
        state.last_activity_at = datetime.now(timezone.utc)

        # Route to appropriate handler based on event type
        handler = self._get_handler(event.event_type)
        if handler:
            await handler(state, event)

        # Mark event as processed
        event.processed = True
        event.processed_at = datetime.now(timezone.utc)

        await self.db.flush()
        return state

    def _get_handler(self, event_type: str):
        """
        Get the appropriate handler for an event type.
        """
        handlers = {
            # Location events
            EventType.LOCATION_UPDATED.value: self._handle_location_update,
            EventType.LOCATION_CONTEXT_CHANGED.value: self._handle_location_context,

            # Workout events
            EventType.WORKOUT_STARTED.value: self._handle_workout_started,
            EventType.WORKOUT_COMPLETED.value: self._handle_workout_completed,
            EventType.WORKOUT_EXERCISE_LOGGED.value: self._handle_exercise_logged,

            # Health events
            EventType.HEALTH_SYNC.value: self._handle_health_sync,
            EventType.HEALTH_METRICS_RECEIVED.value: self._handle_health_metrics,

            # Digital wellbeing
            EventType.SCREEN_TIME_LOGGED.value: self._handle_screen_time,
            EventType.APP_USAGE_SYNCED.value: self._handle_app_usage,

            # AI events
            EventType.AI_RECOMMENDATION_GENERATED.value: self._handle_recommendation,
            EventType.AI_FEEDBACK_RECEIVED.value: self._handle_feedback,
        }
        return handlers.get(event_type)

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================

    async def _handle_location_update(self, state: UserState, event: Event) -> None:
        """Handle location update events."""
        payload = event.payload
        state.current_latitude = payload.get("latitude")
        state.current_longitude = payload.get("longitude")
        state.location_updated_at = event.event_timestamp

    async def _handle_location_context(self, state: UserState, event: Event) -> None:
        """Handle location context change events."""
        payload = event.payload
        context = payload.get("context", LocationContext.UNKNOWN.value)
        state.current_location_context = context

        # Update known places if provided
        if place_id := payload.get("place_id"):
            state.known_places[place_id] = {
                "context": context,
                "last_visited": event.event_timestamp.isoformat(),
                "name": payload.get("place_name"),
            }

    async def _handle_workout_started(self, state: UserState, event: Event) -> None:
        """Handle workout start events."""
        state.current_activity_level = ActivityLevel.ACTIVE.value

    async def _handle_workout_completed(self, state: UserState, event: Event) -> None:
        """Handle workout completion events."""
        payload = event.payload
        state.last_workout_at = event.event_timestamp
        state.last_workout_type = payload.get("workout_type")
        state.workouts_this_week += 1
        state.current_activity_level = ActivityLevel.LIGHT.value

        # Update calories if provided
        if calories := payload.get("calories_burned"):
            state.calories_burned_today += calories

        # Update active minutes
        if duration := payload.get("duration_minutes"):
            state.active_minutes_today += duration

    async def _handle_exercise_logged(self, state: UserState, event: Event) -> None:
        """Handle individual exercise logging."""
        payload = event.payload
        if calories := payload.get("calories"):
            state.calories_burned_today += calories

    async def _handle_health_sync(self, state: UserState, event: Event) -> None:
        """Handle health data sync from Google Fit / HealthKit."""
        payload = event.payload

        # Update step count
        if steps := payload.get("steps"):
            state.steps_today = steps

        # Update sleep data
        if sleep_hours := payload.get("sleep_hours"):
            state.sleep_hours_last_night = sleep_hours
        if sleep_quality := payload.get("sleep_quality"):
            state.sleep_quality_score = sleep_quality

        # Update heart metrics
        if rhr := payload.get("resting_heart_rate"):
            state.resting_heart_rate = rhr
        if hrv := payload.get("hrv"):
            state.hrv_score = hrv

        # Derive recovery status
        await self._update_recovery_status(state)

    async def _handle_health_metrics(self, state: UserState, event: Event) -> None:
        """Handle real-time health metrics."""
        payload = event.payload

        # Update activity level based on current heart rate
        if current_hr := payload.get("heart_rate"):
            if current_hr > 140:
                state.current_activity_level = ActivityLevel.INTENSE.value
            elif current_hr > 100:
                state.current_activity_level = ActivityLevel.ACTIVE.value
            elif current_hr > 70:
                state.current_activity_level = ActivityLevel.LIGHT.value
            else:
                state.current_activity_level = ActivityLevel.SEDENTARY.value

    async def _handle_screen_time(self, state: UserState, event: Event) -> None:
        """Handle screen time logging."""
        payload = event.payload
        if minutes := payload.get("total_minutes"):
            state.screen_time_today_minutes = minutes
        if productive := payload.get("productive_minutes"):
            state.productive_time_today_minutes = productive

    async def _handle_app_usage(self, state: UserState, event: Event) -> None:
        """Handle app usage sync."""
        payload = event.payload
        if usage_data := payload.get("app_usage"):
            state.app_usage_today = usage_data

    async def _handle_recommendation(self, state: UserState, event: Event) -> None:
        """Handle AI recommendation generated."""
        state.last_recommendation_at = event.event_timestamp
        state.last_recommendation = event.payload.get("recommendation")

    async def _handle_feedback(self, state: UserState, event: Event) -> None:
        """Handle user feedback on recommendations."""
        payload = event.payload
        if payload.get("followed"):
            state.recommendations_followed_count += 1
        elif payload.get("dismissed"):
            state.recommendations_dismissed_count += 1

    # =========================================================================
    # DERIVED STATE
    # =========================================================================

    async def _update_recovery_status(self, state: UserState) -> None:
        """
        Update recovery status based on available metrics.
        Uses sleep, HRV, and activity data.
        """
        score = 100  # Start with perfect recovery

        # Penalize for poor sleep
        if state.sleep_hours_last_night:
            if state.sleep_hours_last_night < 6:
                score -= 30
            elif state.sleep_hours_last_night < 7:
                score -= 15

        # Consider HRV if available
        if state.hrv_score:
            # Simplified HRV assessment (would be personalized in production)
            if state.hrv_score < 30:
                score -= 25
            elif state.hrv_score < 50:
                score -= 10

        # Consider recent workout load
        if state.workouts_this_week > 5:
            score -= 15

        # Map score to status
        if score >= 90:
            state.recovery_status = RecoveryStatus.FULLY_RECOVERED.value
        elif score >= 70:
            state.recovery_status = RecoveryStatus.WELL_RESTED.value
        elif score >= 50:
            state.recovery_status = RecoveryStatus.MODERATE.value
        elif score >= 30:
            state.recovery_status = RecoveryStatus.FATIGUED.value
        else:
            state.recovery_status = RecoveryStatus.EXHAUSTED.value
