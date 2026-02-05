"""
TrueShift - Agent Chat Service

Conversational AI service for workout coaching with user memory.
Uses Gemini API with personalized context.
"""

import logging
import json
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_service import gemini_service
from app.services.agent_memory_service import agent_memory_service

logger = logging.getLogger(__name__)


from app.services.workout_service import workout_service
from app.schemas.workout import WorkoutGenerationRequest

class AgentChatService:
    """
    Service for conversational AI coaching with user memory.
    """

    @staticmethod
    def build_system_prompt(user_memory: Dict[str, Any]) -> str:
        """
        Build personalized system prompt from user memory.
        """
        fitness_profile = user_memory.get("fitness_profile", {})
        current_condition = user_memory.get("current_condition", {})
        recent_workouts = user_memory.get("recent_workouts", [])
        
        # Format equipment list
        equipment = fitness_profile.get("equipment", [])
        equipment_str = ", ".join(equipment) if equipment else "None specified"
        
        # Format goals
        goals = fitness_profile.get("goals", [])
        goals_str = ", ".join(goals) if goals else "General fitness"
        
        # Format soreness
        soreness = current_condition.get("soreness", [])
        soreness_str = ", ".join(soreness) if soreness else "None"
        
        # Recent workout summary
        workout_summary = ""
        if recent_workouts:
            last_workout = recent_workouts[0]
            workout_summary = f"\nLast Workout: {last_workout.get('created_at', 'Unknown')} - {last_workout.get('overview', 'N/A')}"
        
        system_prompt = f"""You are TrueShift AI Coach, a highly precise, directive, and authoritative personal fitness assistant. 

USER PROFILE:
- Fitness Level: {fitness_profile.get('level', 'intermediate')}
- Goals: {goals_str}
- Available Equipment: {equipment_str}
- Preferred Duration: {fitness_profile.get('preferred_duration', 30)} minutes
- Preferred Exercises: {', '.join(fitness_profile.get('preferred_exercises', [])) or 'None specified'}
- Avoid: {', '.join(fitness_profile.get('avoid_exercises', [])) or 'None'}

CURRENT CONDITION:
- Recovery Status: {current_condition.get('recovery_status', 'unknown')}
- Energy Level: {current_condition.get('energy_level', 'medium')}
- Soreness: {soreness_str}
- Sleep Quality: {current_condition.get('sleep_quality', 'unknown')}
- Stress Level: {current_condition.get('stress_level', 'medium')}
- Workouts This Week: {current_condition.get('workouts_this_week', 0)}
{workout_summary}

YOUR CORE DIRECTIVES:
1. TAKE COMMAND: Analyze the user's state and GIVE INSTRUCTIONS.
2. DETECT WORKOUT INTENT: If the user indicates they want to workout (e.g., "Give me a plan", "I want to train legs"), you MUST trigger the 'generate_workout' action.
3. EXTRACT PARAMETERS: If generating a workout, infer target muscle, duration, etc., from context or defaults.

RESPONSE FORMAT:
You MUST respond in strict JSON format:
{{
  "response": "Your conversational response to the user (e.g., 'Understood. Generating a high-intensity leg session for you now.')",
  "action": "none" | "generate_workout",
  "workout_params": {{
      "target_muscle_group": "Full Body" | "Upper Body" | "Lower Body" | "Push" | "Pull" | "Legs" | "Chest" | "Back" | "Arms" | "Shoulders",
      "duration_minutes": 45,
      "fitness_level": "Intermediate", 
      "goals": "Strength" | "Hypertrophy" | "Endurance"
  }} (Include ONLY if action is 'generate_workout')
}}

TONE:
- Authoritative but supportive.
- Concise.
- Action-oriented.

Respond directly in JSON."""

        return system_prompt

    @staticmethod
    def build_conversation_context(
        user_memory: Dict[str, Any],
        current_message: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build conversation context including history and current message.
        """
        conversation_history = user_memory.get("conversation_history", [])
        
        # Format recent conversation
        history_text = ""
        if conversation_history:
            history_text = "\n\nRECENT CONVERSATION:\n"
            for msg in conversation_history[-6:]:  # Last 6 messages
                role = "User" if msg["role"] == "user" else "Coach"
                history_text += f"{role}: {msg['content']}\n"
        
        # Add current plan context if provided
        plan_context = ""
        if additional_context and "current_plan" in additional_context:
            plan = additional_context["current_plan"]
            if plan:
                exercises = plan.get("plan_data", {}).get("exercises", [])
                exercise_names = [ex.get("name", "") for ex in exercises]
                plan_context = f"\n\nCURRENT WORKOUT PLAN:\n{plan.get('plan_data', {}).get('overview', '')}\nExercises: {', '.join(exercise_names)}\n"
        
        # Build full prompt
        prompt = f"""{history_text}{plan_context}
        
        User: {current_message}
        
        Coach (JSON):"""
        
        return prompt

    @staticmethod
    async def chat(
        db: AsyncSession,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main chat function with user memory and action handling.
        """
        try:
            # Get user user object (needed for workout service)
            from sqlalchemy import select
            from app.models.user import User
            user_result = await db.execute(select(User).where(User.firebase_uid == user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                 raise Exception("User not found")

            # Get user memory
            user_memory = await agent_memory_service.get_user_memory(db, user_id)
            
            # Build prompts
            system_prompt = AgentChatService.build_system_prompt(user_memory)
            conversation_prompt = AgentChatService.build_conversation_context(
                user_memory, message, context
            )
            
            # Save user message
            await agent_memory_service.save_conversation(
                db=db, user_id=user_id, role="user", content=message,
                session_id=context.get("session_id") if context else None
            )
            
            # Call Gemini
            logger.info(f"Calling Gemini for user {user_id}")
            gemini_response = await gemini_service.generate_content(
                prompt=conversation_prompt,
                system_instruction=system_prompt,
                temperature=0.7,
                response_schema={"type": "object"} # Enforce JSON
            )
            
            response_content = gemini_response.get("content", "{}")
            action_data = {}
            response_text = "I'm having trouble processing that."
            
            try:
                # Parse JSON response
                if isinstance(response_content, str):
                    parsed_response = json.loads(response_content)
                else:
                    parsed_response = response_content # Already dict if using smart parser
                
                response_text = parsed_response.get("response", response_text)
                action = parsed_response.get("action", "none")
                
                # Handle Action
                if action == "generate_workout":
                    params = parsed_response.get("workout_params", {})
                    # Add defaults from user profile if missing
                    fitness_profile = user_memory.get("fitness_profile", {})
                    request = WorkoutGenerationRequest(
                        target_muscle_group=params.get("target_muscle_group", "Full Body"),
                        duration_minutes=params.get("duration_minutes", fitness_profile.get("preferred_duration", 45)),
                        fitness_level=params.get("fitness_level", fitness_profile.get("level", "Intermediate")),
                        goals=params.get("goals", "General Fitness"),
                        equipment=fitness_profile.get("equipment", [])
                    )
                    
                    # Generate Workout
                    plan = await workout_service.generate_workout(db, user, request)
                    
                    action_data = {
                        "action": "view_workout",
                        "data": {
                            "id": plan.id,
                            "overview": plan.plan_data.get("overview", "Generated Workout"),
                            "exercises": plan.plan_data.get("exercises", [])
                        }
                    }
                    
                    # Update response text if needed (optional)
                    # response_text += f" I've created a {request.target_muscle_group} plan for you."

            except json.JSONDecodeError:
                logger.error("Failed to parse agent JSON response")
                response_text = str(response_content) # Fallback to raw text
            except Exception as e:
                logger.error(f"Action processing error: {e}")
                response_text += " (I tried to generate a workout but encountered an error.)"

            # Save agent response (Clean text only)
            await agent_memory_service.save_conversation(
                db=db, user_id=user_id, role="model", content=response_text,
                agent_name="WorkoutAgent",
                session_id=context.get("session_id") if context else None
            )
            
            return {
                "response": response_text,
                "action": action_data.get("action"), # To frontend
                "data": action_data.get("data"),     # To frontend
                "conversation_id": user_memory.get("conversation_context", {}).get("session_id")
            }
            
        except Exception as e:
            logger.error(f"Agent chat error: {e}", exc_info=True)
            return {
                "response": "I encountered an error. Please try again.",
                "error": str(e)
            }


# Global instance
agent_chat_service = AgentChatService()
