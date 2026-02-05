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
1. TAKE COMMAND: Do not be passive. Do not ask open-ended questions like "What do you want to do?". Instead, analyze the user's state and GIVE INSTRUCTIONS.
2. VERIFY READINESS: If the user has already worked out recently (check 'last_workout'), immediately ASK about their physical state (soreness, energy) BEFORE prescribing anything.
3. BE PRECISE: Give exact numbers, sets, and reps. Do not be vague.
4. DRIVE BEST EFFORT: Your goal is to maximize the user's results. Push them to their best effort while respecting safety.
5. NO DECISION PARALYSIS: Do not offer too many choices. Make the BEST decision for the user and tell them to do it.

INTERACTION PROTOCOL:
- If User says "I want to workout":
  CHECK: Did they workout today/yesterday?
  IF YES: Command: "Assess your recovery. On a scale of 1-10, how sore are you?"
  IF NO: Command: "We are training [Target Muscle] today. Are you ready?"

- If User reports being tired/sore:
  ACTION: Adjust plan immediately. Command: "Understood. We are switching to a recovery session. Stretch and light mobility only."

TONE:
- Authoritative but supportive.
- Concise.
- Action-oriented.
- "Coach" persona - firm but fair.

Respond directly and efficiently."""

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

Coach:"""
        
        return prompt

    @staticmethod
    async def chat(
        db: AsyncSession,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main chat function with user memory.
        
        Args:
            db: Database session
            user_id: User ID
            message: User's message
            context: Additional context (current_plan, equipment, etc.)
        
        Returns:
            {
                "response": str,
                "updated_context": dict (optional)
            }
        """
        try:
            # Get user memory
            user_memory = await agent_memory_service.get_user_memory(db, user_id)
            
            # Build system prompt
            system_prompt = AgentChatService.build_system_prompt(user_memory)
            
            # Build conversation prompt
            conversation_prompt = AgentChatService.build_conversation_context(
                user_memory, message, context
            )
            
            # Save user message
            await agent_memory_service.save_conversation(
                db=db,
                user_id=user_id,
                role="user",
                content=message,
                session_id=context.get("session_id") if context else None
            )
            
            # Call Gemini
            logger.info(f"Calling Gemini for user {user_id}")
            gemini_response = await gemini_service.generate_content(
                prompt=conversation_prompt,
                system_instruction=system_prompt,
                temperature=0.7
            )
            
            # Extract response
            if "error" in gemini_response:
                logger.error(f"Gemini error: {gemini_response}")
                response_text = "I'm having trouble right now. Please try again in a moment."
            else:
                response_text = gemini_response.get("content", "I'm not sure how to respond to that.")
            
            # Save agent response
            await agent_memory_service.save_conversation(
                db=db,
                user_id=user_id,
                role="model",
                content=response_text,
                agent_name="WorkoutAgent",
                session_id=context.get("session_id") if context else None
            )
            
            # Update conversation context
            if context:
                await agent_memory_service.update_conversation_context(
                    db=db,
                    user_id=user_id,
                    context_updates={
                        "current_plan_id": context.get("current_plan_id"),
                        "session_id": context.get("session_id"),
                    }
                )
            
            return {
                "response": response_text,
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
