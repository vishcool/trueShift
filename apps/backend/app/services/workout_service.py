import logging
import json
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workout import WorkoutPlan
from app.schemas.workout import WorkoutGenerationRequest
from app.ai.llm_service import gemini_service

logger = logging.getLogger(__name__)

class WorkoutService:
    """
    Service for generating and managing workouts.
    Encapsulates AI generation logic.
    """

    async def generate_workout(
        self,
        db: AsyncSession,
        user: User,
        request: WorkoutGenerationRequest
    ) -> WorkoutPlan:
        """
        Generate a personalized workout plan using AI.
        """
        
        # Fetch Recent History (Last 5 workouts)
        history_result = await db.execute(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user.id)
            .where(WorkoutPlan.status == "completed")
            .order_by(desc(WorkoutPlan.created_at))
            .limit(5)
        )
        last_workouts = history_result.scalars().all()
        
        history_context = "No previous workout history available. Start with standard baseline volume."
        if last_workouts:
            formatted_history = []
            for w in last_workouts:
                 # Extract exercises performed
                 exercises = w.completion_data.get("exercises", []) if w.completion_data else w.plan_data.get("exercises", [])
                 ex_summary = ", ".join([f"{ex.get('name')} ({ex.get('sets')}x{ex.get('reps')})" for ex in exercises])
                 formatted_history.append(f"- {w.created_at.strftime('%Y-%m-%d')}: {ex_summary}")
            history_context = "\n".join(formatted_history)

        # Construct Prompt
        prompt = f"""
        Act as a strict, elite strength and conditioning coach focused on PROGRESSIVE OVERLOAD.
        Design a PRECISE workout plan that micro-increases volume/intensity based on previous history.
        
        User Profile:
        - Target: {request.target_muscle_group}
        - Duration: {request.duration_minutes} minutes
        - Level: {request.fitness_level}
        - Equipment: {", ".join(request.equipment) if request.equipment else "Bodyweight only"}
        - Specific Goals: {request.goals or "General Fitness"}
        
        PREVIOUS TRAINING HISTORY (Most Recent First):
        {history_context}
        
        Directives:
        1. ANALYZE HISTORY: Look at the reps/sets used in previous sessions for similar exercises.
           - IF MATCH FOUND: Apply PROGESSIVE OVERLOAD. Increase reps by 1-2 OR add 1 set. Small, micro-increases.
           - IF NO MATCH: Use standard baseline volume (3 sets, 8-12 reps).
        
        2. BE PRECISE: Give EXACT numbers (e.g., "11 reps" if they did "10" last time). Do NOT give ranges.
        3. BE AUTHORITATIVE: Tell the user exactly what to do.
        4. MAXIMIZE EFFICIENCY: Fill the {request.duration_minutes} minutes.
        
        Return the response strictly as a JSON object with the following structure:
        {{
          "overview": "Direct command describing the progression (e.g. 'Increased reps on Squats. Push for 11 today.')",
          "exercises": [
            {{
              "name": "Exercise Name",
              "sets": 3,
              "reps": "11",
              "rest_seconds": 60,
              "notes": "Progression note or form cue (e.g. 'Beat last week's 10 reps.')"
            }}
          ]
        }}
        Do not include markdown formatting like ```json or ```. Just the raw JSON.
        """

        # Call LLM
        llm_response = await gemini_service.generate_content(
            prompt=prompt, 
            response_schema={"type": "object"}
        )
        
        if "error" in llm_response:
             raise Exception(f"AI Generation failed: {llm_response['error']}")

        # Create WorkoutPlan
        plan = WorkoutPlan(
            user_id=user.id,
            status="generated",
            plan_data=llm_response,
            scheduled_date=datetime.utcnow()
        )
        db.add(plan)
        await db.flush() # Get ID
        
        return plan

# Global instance
workout_service = WorkoutService()
