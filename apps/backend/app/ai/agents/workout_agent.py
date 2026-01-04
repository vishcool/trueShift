"""
TrueShift - Workout Agent

Recommends workouts based on user context and goals.
"""

from typing import Optional

from app.ai.agents.base_agent import (
    AgentContext,
    AgentResponse,
    BaseAgent,
)


class WorkoutRecommendation:
    """Represents a workout recommendation."""

    def __init__(
        self,
        workout_type: str,
        name: str,
        duration_minutes: int,
        intensity: str,
        exercises: list[dict],
        reasoning: str,
    ):
        self.workout_type = workout_type
        self.name = name
        self.duration_minutes = duration_minutes
        self.intensity = intensity
        self.exercises = exercises
        self.reasoning = reasoning

    def to_dict(self) -> dict:
        return {
            "workout_type": self.workout_type,
            "name": self.name,
            "duration_minutes": self.duration_minutes,
            "intensity": self.intensity,
            "exercises": self.exercises,
            "reasoning": self.reasoning,
        }


class WorkoutAgent(BaseAgent):
    """
    Workout Agent - Recommends appropriate workouts.
    
    Purpose: Analyze user context and recommend appropriate
    workout types, intensity, and specific exercises.
    """

    name = "workout_agent"
    description = "Recommends personalized workouts based on context"
    version = "1.0.0"

    # Exercise library (simplified)
    EXERCISE_LIBRARY = {
        "strength": {
            "upper": [
                {"name": "Push-ups", "sets": 3, "reps": 12},
                {"name": "Dumbbell Rows", "sets": 3, "reps": 10},
                {"name": "Shoulder Press", "sets": 3, "reps": 10},
                {"name": "Tricep Dips", "sets": 3, "reps": 12},
            ],
            "lower": [
                {"name": "Squats", "sets": 4, "reps": 12},
                {"name": "Lunges", "sets": 3, "reps": 10},
                {"name": "Romanian Deadlifts", "sets": 3, "reps": 10},
                {"name": "Calf Raises", "sets": 3, "reps": 15},
            ],
            "full_body": [
                {"name": "Squats", "sets": 3, "reps": 12},
                {"name": "Push-ups", "sets": 3, "reps": 12},
                {"name": "Dumbbell Rows", "sets": 3, "reps": 10},
                {"name": "Lunges", "sets": 3, "reps": 10},
            ],
        },
        "cardio": {
            "running": [
                {"name": "Warm-up Walk", "duration": "5 min"},
                {"name": "Jogging", "duration": "20 min"},
                {"name": "Cool-down Walk", "duration": "5 min"},
            ],
            "hiit": [
                {"name": "Jumping Jacks", "duration": "30 sec", "rest": "15 sec"},
                {"name": "Burpees", "duration": "30 sec", "rest": "15 sec"},
                {"name": "High Knees", "duration": "30 sec", "rest": "15 sec"},
                {"name": "Mountain Climbers", "duration": "30 sec", "rest": "15 sec"},
            ],
        },
        "bodyweight": {
            "basic": [
                {"name": "Bodyweight Squats", "sets": 3, "reps": 15},
                {"name": "Push-ups", "sets": 3, "reps": 10},
                {"name": "Plank", "sets": 3, "duration": "30 sec"},
                {"name": "Glute Bridges", "sets": 3, "reps": 12},
            ],
        },
        "stretching": {
            "full_body": [
                {"name": "Neck Rolls", "duration": "1 min"},
                {"name": "Shoulder Stretches", "duration": "2 min"},
                {"name": "Forward Fold", "duration": "1 min"},
                {"name": "Hip Flexor Stretch", "duration": "2 min"},
                {"name": "Child's Pose", "duration": "2 min"},
            ],
        },
    }

    def get_agent_prompt(self) -> str:
        return """
        You are a workout programming expert.
        
        Your responsibility:
        1. Analyze user's recovery status and recent activity
        2. Consider their location and available equipment
        3. Recommend appropriate workout type and intensity
        4. Provide specific exercise recommendations
        
        Always prioritize:
        - Safety first - never push through fatigue/injury
        - Progressive overload principles
        - Balanced training (avoid overtraining muscle groups)
        - User preferences and goals
        """

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Generate workout recommendation based on context.
        """
        if not self.validate_context(context):
            return AgentResponse(
                agent_name=self.name,
                success=False,
                content="Invalid context provided",
                confidence=0.0,
            )

        state = context.user_state

        # Determine workout parameters
        workout_type = self._determine_workout_type(state)
        intensity = self._determine_intensity(state)
        duration = self._determine_duration(state)

        # Get exercises
        exercises = self._get_exercises(workout_type, state)

        recommendation = WorkoutRecommendation(
            workout_type=workout_type,
            name=self._get_workout_name(workout_type, intensity),
            duration_minutes=duration,
            intensity=intensity,
            exercises=exercises,
            reasoning=self._get_reasoning(state, workout_type),
        )

        return AgentResponse(
            agent_name=self.name,
            success=True,
            content=recommendation.to_dict(),
            reasoning=recommendation.reasoning,
            confidence=0.85,
            suggestions=[
                f"Start with {recommendation.name}",
                f"Duration: {duration} minutes",
            ],
        )

    def _determine_workout_type(self, state: dict) -> str:
        """
        Determine workout type based on location and recovery.
        """
        physical = state.get("physical", {})
        location = state.get("location", {})

        recovery = physical.get("recovery_status", "moderate")
        loc_context = location.get("context", "unknown")

        # Recovery takes priority
        if recovery in ["exhausted", "fatigued"]:
            return "stretching"

        # Location-based suggestions
        if loc_context == "gym":
            return "strength"
        elif loc_context == "park":
            return "cardio"
        elif loc_context == "home":
            return "bodyweight"

        # Default to bodyweight
        return "bodyweight"

    def _determine_intensity(self, state: dict) -> str:
        """
        Determine appropriate intensity level.
        """
        physical = state.get("physical", {})
        recovery = physical.get("recovery_status", "moderate")

        intensity_map = {
            "fully_recovered": "moderate-high",
            "well_rested": "moderate",
            "moderate": "low-moderate",
            "fatigued": "low",
            "exhausted": "very_low",
        }
        return intensity_map.get(recovery, "moderate")

    def _determine_duration(self, state: dict) -> int:
        """
        Determine workout duration in minutes.
        """
        physical = state.get("physical", {})
        recovery = physical.get("recovery_status", "moderate")

        duration_map = {
            "fully_recovered": 45,
            "well_rested": 40,
            "moderate": 30,
            "fatigued": 20,
            "exhausted": 15,
        }
        return duration_map.get(recovery, 30)

    def _get_exercises(self, workout_type: str, state: dict) -> list[dict]:
        """
        Get exercises for the workout type.
        """
        if workout_type == "strength":
            # Alternate muscle groups based on last workout
            last_workout = state.get("physical", {}).get("last_workout_type")
            if last_workout and "upper" in last_workout.lower():
                return self.EXERCISE_LIBRARY["strength"]["lower"]
            elif last_workout and "lower" in last_workout.lower():
                return self.EXERCISE_LIBRARY["strength"]["upper"]
            return self.EXERCISE_LIBRARY["strength"]["full_body"]

        elif workout_type == "cardio":
            return self.EXERCISE_LIBRARY["cardio"]["running"]

        elif workout_type == "bodyweight":
            return self.EXERCISE_LIBRARY["bodyweight"]["basic"]

        elif workout_type == "stretching":
            return self.EXERCISE_LIBRARY["stretching"]["full_body"]

        return self.EXERCISE_LIBRARY["bodyweight"]["basic"]

    def _get_workout_name(self, workout_type: str, intensity: str) -> str:
        """
        Generate a descriptive workout name.
        """
        names = {
            "strength": f"{intensity.title()} Intensity Strength Training",
            "cardio": "Cardio Session",
            "bodyweight": "Home Bodyweight Circuit",
            "stretching": "Recovery Stretching Routine",
        }
        return names.get(workout_type, "Custom Workout")

    def _get_reasoning(self, state: dict, workout_type: str) -> str:
        """
        Generate reasoning for the recommendation.
        """
        physical = state.get("physical", {})
        location = state.get("location", {})

        parts = []

        recovery = physical.get("recovery_status", "moderate")
        parts.append(f"Based on {recovery} recovery status")

        loc_context = location.get("context")
        if loc_context:
            parts.append(f"and current location ({loc_context})")

        parts.append(f"recommending {workout_type} workout")

        return ", ".join(parts) + "."
