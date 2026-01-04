"""
TrueShift - Recommendation Engine

Generates context-aware recommendations based on user state and AI outputs.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.models.user_state import UserState, LocationContext, RecoveryStatus


class RecommendationType(str, Enum):
    """Types of recommendations the system can generate."""
    WORKOUT = "workout"
    RECOVERY = "recovery"
    MOVEMENT = "movement"
    DIGITAL_DETOX = "digital_detox"
    SLEEP = "sleep"
    HYDRATION = "hydration"
    MINDFULNESS = "mindfulness"


class Recommendation(BaseModel):
    """A single recommendation."""
    id: str
    type: RecommendationType
    title: str
    description: str
    priority: int  # 1-5, 5 being highest
    context: dict  # Why this recommendation
    actions: list[dict]  # What to do
    confidence: float  # 0-1 confidence score
    expires_at: Optional[datetime] = None


class RecommendationEngine:
    """
    Generates personalized recommendations based on user state.
    Combines rule-based logic with AI insights.
    """

    def __init__(self, ai_orchestrator=None):
        self.ai_orchestrator = ai_orchestrator

    async def generate_recommendations(
        self,
        user_state: UserState,
        limit: int = 3,
    ) -> list[Recommendation]:
        """
        Generate recommendations based on current user state.
        """
        recommendations = []

        # Location-based recommendations
        location_rec = await self._get_location_recommendation(user_state)
        if location_rec:
            recommendations.append(location_rec)

        # Recovery-based recommendations
        recovery_rec = await self._get_recovery_recommendation(user_state)
        if recovery_rec:
            recommendations.append(recovery_rec)

        # Activity recommendations
        activity_rec = await self._get_activity_recommendation(user_state)
        if activity_rec:
            recommendations.append(activity_rec)

        # Digital wellbeing recommendations
        digital_rec = await self._get_digital_recommendation(user_state)
        if digital_rec:
            recommendations.append(digital_rec)

        # Sort by priority and limit
        recommendations.sort(key=lambda r: r.priority, reverse=True)
        return recommendations[:limit]

    async def _get_location_recommendation(
        self,
        state: UserState,
    ) -> Optional[Recommendation]:
        """
        Generate recommendation based on location context.
        """
        context = state.current_location_context

        if context == LocationContext.GYM.value:
            return Recommendation(
                id=f"loc-{state.user_id}-gym",
                type=RecommendationType.WORKOUT,
                title="You're at the gym! 💪",
                description="Perfect time for your strength training session.",
                priority=5,
                context={
                    "location": "gym",
                    "recovery_status": state.recovery_status,
                },
                actions=[
                    {"type": "start_workout", "workout_type": "strength"},
                    {"type": "view_routine", "routine_id": "default_strength"},
                ],
                confidence=0.9,
                expires_at=None,
            )
        elif context == LocationContext.PARK.value:
            return Recommendation(
                id=f"loc-{state.user_id}-park",
                type=RecommendationType.WORKOUT,
                title="Outdoor workout opportunity! 🌳",
                description="Great weather for a cardio session in the park.",
                priority=4,
                context={"location": "park"},
                actions=[
                    {"type": "start_workout", "workout_type": "cardio"},
                    {"type": "start_run"},
                ],
                confidence=0.85,
            )
        elif context == LocationContext.HOME.value:
            return Recommendation(
                id=f"loc-{state.user_id}-home",
                type=RecommendationType.WORKOUT,
                title="Home workout ready 🏠",
                description="Try a bodyweight routine - no equipment needed.",
                priority=3,
                context={"location": "home"},
                actions=[
                    {"type": "start_workout", "workout_type": "bodyweight"},
                ],
                confidence=0.8,
            )

        return None

    async def _get_recovery_recommendation(
        self,
        state: UserState,
    ) -> Optional[Recommendation]:
        """
        Generate recovery-based recommendations.
        """
        recovery = state.recovery_status

        if recovery in [RecoveryStatus.EXHAUSTED.value, RecoveryStatus.FATIGUED.value]:
            return Recommendation(
                id=f"rec-{state.user_id}-recovery",
                type=RecommendationType.RECOVERY,
                title="Recovery day recommended 😴",
                description="Your body needs rest. Focus on light stretching or mobility work.",
                priority=5,
                context={
                    "recovery_status": recovery,
                    "sleep_hours": state.sleep_hours_last_night,
                    "workouts_this_week": state.workouts_this_week,
                },
                actions=[
                    {"type": "start_workout", "workout_type": "stretching"},
                    {"type": "log_rest_day"},
                ],
                confidence=0.95,
            )

        if state.sleep_hours_last_night and state.sleep_hours_last_night < 6:
            return Recommendation(
                id=f"rec-{state.user_id}-sleep",
                type=RecommendationType.SLEEP,
                title="Sleep deficit detected 💤",
                description=f"You only got {state.sleep_hours_last_night:.1f}h of sleep. Consider an earlier bedtime tonight.",
                priority=4,
                context={
                    "sleep_hours": state.sleep_hours_last_night,
                },
                actions=[
                    {"type": "set_reminder", "reminder_type": "bedtime"},
                ],
                confidence=0.9,
            )

        return None

    async def _get_activity_recommendation(
        self,
        state: UserState,
    ) -> Optional[Recommendation]:
        """
        Generate recommendations based on activity levels.
        """
        # Sedentary for too long
        if (
            state.current_activity_level == "sedentary"
            and state.steps_today < 2000
            and state.active_minutes_today < 15
        ):
            return Recommendation(
                id=f"act-{state.user_id}-move",
                type=RecommendationType.MOVEMENT,
                title="Time to move! 🚶",
                description="You've been sedentary for a while. A short walk can boost energy.",
                priority=3,
                context={
                    "steps_today": state.steps_today,
                    "active_minutes": state.active_minutes_today,
                },
                actions=[
                    {"type": "start_walk", "duration": 10},
                    {"type": "stretching_break"},
                ],
                confidence=0.85,
            )

        return None

    async def _get_digital_recommendation(
        self,
        state: UserState,
    ) -> Optional[Recommendation]:
        """
        Generate digital wellbeing recommendations.
        """
        if state.screen_time_today_minutes > 300:  # 5+ hours
            productive_ratio = (
                state.productive_time_today_minutes / state.screen_time_today_minutes
                if state.screen_time_today_minutes > 0
                else 0
            )

            if productive_ratio < 0.3:
                return Recommendation(
                    id=f"dig-{state.user_id}-detox",
                    type=RecommendationType.DIGITAL_DETOX,
                    title="Screen break suggested 📱",
                    description=f"You've had {state.screen_time_today_minutes // 60}h of screen time. Consider a digital break.",
                    priority=3,
                    context={
                        "screen_time_minutes": state.screen_time_today_minutes,
                        "productive_minutes": state.productive_time_today_minutes,
                    },
                    actions=[
                        {"type": "enable_focus_mode"},
                        {"type": "start_activity", "activity": "outdoor_walk"},
                    ],
                    confidence=0.8,
                )

        return None
