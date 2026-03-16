"""
TrueShift - Progress Dashboard Service

Builds derived workout and recovery insights for the mobile dashboard.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_state import UserState
from app.models.workout import WorkoutPlan


def _to_float(value: Any) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class ProgressDashboardService:
    async def build_dashboard(
        self,
        db: AsyncSession,
        user_id: str,
        user_state: UserState,
    ) -> dict[str, Any]:
        result = await db.execute(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id)
            .order_by(desc(WorkoutPlan.created_at))
            .limit(20)
        )
        workouts = result.scalars().all()
        completed_workouts = [workout for workout in workouts if workout.status == "completed"]

        recent_sessions = []
        total_sets = 0
        total_reps = 0.0
        total_volume = 0.0
        weekly_minutes = 0
        weekly_workouts = 0
        muscle_groups: Counter[str] = Counter()

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        for workout in completed_workouts:
            completion = workout.completion_data or {}
            exercises = completion.get("exercises") or workout.plan_data.get("exercises", [])
            session_minutes = int(_to_float(completion.get("duration_minutes") or 0))
            session_sets = 0
            session_volume = 0.0

            for exercise in exercises:
                exercise_name = str(exercise.get("name", "Exercise"))
                muscle_groups[exercise_name] += 1
                for performed_set in exercise.get("performed_sets", []):
                    reps = _to_float(performed_set.get("reps"))
                    weight = _to_float(performed_set.get("weight"))
                    total_reps += reps
                    total_volume += reps * weight
                    total_sets += 1
                    session_sets += 1
                    session_volume += reps * weight

            if workout.completed_at and workout.completed_at >= week_ago:
                weekly_workouts += 1
                weekly_minutes += session_minutes

            recent_sessions.append(
                {
                    "id": str(workout.id),
                    "created_at": workout.created_at.isoformat(),
                    "status": workout.status,
                    "overview": workout.plan_data.get("overview", "Workout session"),
                    "exercise_count": len(exercises),
                    "set_count": session_sets,
                    "duration_minutes": session_minutes,
                    "volume_kg": round(session_volume, 1),
                }
            )

        avg_reps = round(total_reps / total_sets, 1) if total_sets else 0.0
        readiness_label = self._readiness_label(user_state)
        focus_area = self._focus_area(user_state, muscle_groups)

        return {
            "overview": {
                "workouts_completed": len(completed_workouts),
                "workouts_this_week": weekly_workouts,
                "minutes_this_week": weekly_minutes,
                "sets_logged": total_sets,
                "avg_reps_per_set": avg_reps,
                "total_volume_kg": round(total_volume, 1),
                "recovery_status": user_state.recovery_status,
                "readiness_label": readiness_label,
            },
            "recovery": {
                "status": user_state.recovery_status,
                "sleep_hours": user_state.sleep_hours_last_night,
                "hrv_score": user_state.hrv_score,
                "resting_heart_rate": user_state.resting_heart_rate,
                "active_minutes_today": user_state.active_minutes_today,
            },
            "focus": {
                "primary_training_focus": focus_area,
                "top_logged_exercises": [name for name, _ in muscle_groups.most_common(3)],
            },
            "insights": self._build_insights(
                user_state=user_state,
                weekly_workouts=weekly_workouts,
                weekly_minutes=weekly_minutes,
                total_sets=total_sets,
                avg_reps=avg_reps,
                focus_area=focus_area,
            ),
            "suggestions": self._build_suggestions(user_state, weekly_workouts, total_sets, focus_area),
            "recent_sessions": recent_sessions[:6],
        }

    def _readiness_label(self, user_state: UserState) -> str:
        recovery = user_state.recovery_status
        if recovery in {"fully_recovered", "well_rested"}:
            return "ready_to_push"
        if recovery == "moderate":
            return "train_with_control"
        return "prioritize_recovery"

    def _focus_area(self, user_state: UserState, muscle_groups: Counter[str]) -> str:
        if user_state.recovery_status in {"fatigued", "exhausted"}:
            return "recovery"
        if user_state.workouts_this_week < 3:
            return "consistency"
        if muscle_groups:
            return muscle_groups.most_common(1)[0][0]
        return "general_fitness"

    def _build_insights(
        self,
        user_state: UserState,
        weekly_workouts: int,
        weekly_minutes: int,
        total_sets: int,
        avg_reps: float,
        focus_area: str,
    ) -> list[dict[str, Any]]:
        insights = [
            {
                "type": "training_load",
                "title": "Weekly training load",
                "detail": f"{weekly_workouts} workouts and {weekly_minutes} active minutes logged in the last 7 days.",
                "priority": "high" if weekly_workouts < 3 else "medium",
            },
            {
                "type": "volume",
                "title": "Workout logging quality",
                "detail": f"{total_sets} sets logged with an average of {avg_reps} reps per set.",
                "priority": "medium",
            },
            {
                "type": "focus",
                "title": "Current coaching focus",
                "detail": f"Primary focus is {focus_area.replace('_', ' ')} based on recent training and recovery.",
                "priority": "medium",
            },
        ]

        if user_state.sleep_hours_last_night and user_state.sleep_hours_last_night < 6:
            insights.append(
                {
                    "type": "sleep",
                    "title": "Recovery is being capped by sleep",
                    "detail": f"Last sleep record is {user_state.sleep_hours_last_night:.1f} hours. Diet and training should stay conservative today.",
                    "priority": "high",
                }
            )

        return insights

    def _build_suggestions(
        self,
        user_state: UserState,
        weekly_workouts: int,
        total_sets: int,
        focus_area: str,
    ) -> list[str]:
        suggestions = []

        if weekly_workouts < 3:
            suggestions.append("Add one more structured workout this week to improve consistency.")
        if total_sets < 20:
            suggestions.append("Log every working set so progression and form insights become more accurate.")
        if user_state.recovery_status in {"fatigued", "exhausted"}:
            suggestions.append("Prioritize hydration, sleep, and lower-intensity training until recovery improves.")
        if focus_area not in {"recovery", "consistency", "general_fitness"}:
            suggestions.append(f"Use the next session to progress {focus_area} with small rep or load increases.")
        if not suggestions:
            suggestions.append("Keep training volume steady and use recovery data to decide when to push harder.")

        return suggestions[:4]


progress_dashboard_service = ProgressDashboardService()
