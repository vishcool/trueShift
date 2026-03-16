"""
TrueShift - Voice Agent Service

Handles the full voice pipeline:
- STT Streaming (Sarvam saaras:v3)
- Intent Classification (Gemini classifying into agent domains)
- Agent Dispatching (WorkoutAgent, RecoveryAgent, MentalWellnessAgent, CoachingAgent)
- TTS Generation (Sarvam REST text-to-speech)
"""

import logging
import json
import re
from typing import Dict, Any, Optional

import aiohttp
from sarvamai import AsyncSarvamAI
from google import genai

from app.core.config import settings
from app.ai.orchestrator import ai_orchestrator
from app.ai.agents.base_agent import AgentContext
from app.models.user_state import UserState

logger = logging.getLogger(__name__)


class VoiceAgentService:
    """Service to handle real-time voice interactions."""

    def __init__(self):
        self.sarvam_client = AsyncSarvamAI(api_subscription_key=settings.sarvam_api_key)
        self.gemini_client = genai.Client(api_key=settings.google_api_key) if settings.google_api_key else None
        
        # Sarvam REST endpoints
        self.sarvam_tts_url = "https://api.sarvam.ai/text-to-speech"
        
    async def route_intent(self, transcript: str) -> str:
        """
        Classifies the transcript to route to the correct agent.
        Returns one of: workout, recovery, mental, general
        """
        if not self.gemini_client or not transcript.strip():
            return "general"
            
        system_prompt = """
        You are an intent router for a personal training AI.
        Classify the user's transcript into EXACTLY ONE of the following precise categories:
        
        - "workout" -> explicitly asking for a workout plan, asking about exercises, reps, sets, training.
        - "recovery" -> expressing physical pain, soreness, asking about rest, sleep, or recovery.
        - "mental" -> expressing stress, anxiety, lack of motivation, or need for mental encouragement.
        - "general" -> anything else, general fitness questions, greetings, or unclear statements.
        
        Respond ONLY with the exact single word lowercase category name. Nothing else.
        """
        
        try:
            response = await self.gemini_client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=f"User transcript: '{transcript}'",
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0,
                    max_output_tokens=10,
                )
            )
            intent = response.text.strip().lower()
            if intent in ["workout", "recovery", "mental", "general"]:
                return intent
            return "general"
        except Exception as e:
            logger.error(f"Intent routing failed: {e}")
            return "general"

    async def get_agent_response(
        self,
        user_id: str,
        transcript: str,
        user_state: UserState,
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Routes the transcript to the correct specialized agent and extracts a conversational response.
        """
        intent = await self.route_intent(transcript)
        logger.info(f"Voice Intent Router classified transcript as: {intent}")
        
        # Build core context (similar to orchestrator)
        context = AgentContext(
            user_id=user_id,
            user_state=user_state.get_context_summary() if hasattr(user_state, 'get_context_summary') else user_state,
            additional_context={
                "user_input": transcript,
                "mode": (session_context or {}).get("mode", "general"),
            },
        )

        planner_res = await ai_orchestrator.planner_agent.process(context)
        if planner_res.success and isinstance(planner_res.content, dict):
            planned_domain = planner_res.content.get("primary_domain")
            if planned_domain in {"workout", "recovery", "mental", "coaching"}:
                intent = planned_domain

        workout_update = self._extract_workout_update(transcript, session_context or {})

        # Dispatch to specific agent based on intent
        if intent == "workout":
            # For workout requests, we ideally want conversational text wrapping the plan, but we'll use CoachingAgent 
            # as the front-end to wrap WorkoutAgent if needed, or ask WorkoutAgent directly.
            # Using WorkoutAgent directly returning a dict plan. We need conversational text.
            workout_res = await ai_orchestrator.workout_agent.process(context)
            if workout_res.success and isinstance(workout_res.content, dict):
                workout_name = workout_res.content.get("name", "workout")
                text = f"I've got a plan for you. Let's do a {workout_name}. {workout_res.reasoning}"
                if workout_update:
                    text = self._blend_workout_update(text, workout_update)
                return {"text": text, "workout_update": workout_update}
                
        elif intent == "recovery":
            recovery_res = await ai_orchestrator.recovery_agent.process(context)
            if recovery_res.success and isinstance(recovery_res.content, str):
                text = recovery_res.content
                if workout_update:
                    text = self._blend_workout_update(text, workout_update)
                return {"text": text, "workout_update": workout_update}
            elif recovery_res.success and isinstance(recovery_res.content, dict):
                 text = recovery_res.content.get("summary", "Make sure you rest.")
                 if workout_update:
                     text = self._blend_workout_update(text, workout_update)
                 return {"text": text, "workout_update": workout_update}
                 
        elif intent == "mental":
            mental_res = await ai_orchestrator.mental_agent.process(context)
            if mental_res.success and isinstance(mental_res.content, str):
                text = mental_res.content
                if workout_update:
                    text = self._blend_workout_update(text, workout_update)
                return {"text": text, "workout_update": workout_update}
            elif mental_res.success and isinstance(mental_res.content, dict):
                 text = mental_res.content.get("summary", "Take a deep breath. You're doing great.")
                 if workout_update:
                     text = self._blend_workout_update(text, workout_update)
                 return {"text": text, "workout_update": workout_update}
                 
        # Default / General (Coaching Agent acts as generic chat wrapper)
        # Using Coaching agent with the transcript injected
        mode = (session_context or {}).get("mode", "general")
        mode_instruction = ""
        if mode == "diet":
            mode_instruction = (
                "Prioritize practical nutrition coaching first (meals, macros, hydration), "
                "then tie back to workout outcomes."
            )
        elif mode == "workout":
            mode_instruction = "Prioritize exercise programming, form cues, and progression details."
        elif mode == "recovery":
            mode_instruction = "Prioritize recovery, sleep, soreness, and stress-management guidance."

        context_str = (
            f"User said: {transcript}\n"
            f"Conversation mode: {mode}\n"
            f"{mode_instruction}\n"
            "Respond conversationally as a personal trainer in 1-2 short sentences."
        )
        context.additional_context["user_voice_input"] = context_str
        
        general_res = await ai_orchestrator.coaching_agent.process(context)
        
        if general_res.success:
            if isinstance(general_res.content, str):
                text = general_res.content
                if workout_update:
                    text = self._blend_workout_update(text, workout_update)
                return {"text": text, "workout_update": workout_update}
            elif isinstance(general_res.content, dict) and "message" in general_res.content:
                text = general_res.content["message"]
                if workout_update:
                    text = self._blend_workout_update(text, workout_update)
                return {"text": text, "workout_update": workout_update}
            elif isinstance(general_res.content, dict) and "summary" in general_res.content:
                text = general_res.content["summary"]
                if workout_update:
                    text = self._blend_workout_update(text, workout_update)
                return {"text": text, "workout_update": workout_update}
                
        fallback = "I heard you, let's keep working."
        if workout_update:
            fallback = self._blend_workout_update(fallback, workout_update)
        return {"text": fallback, "workout_update": workout_update}

    def _blend_workout_update(self, text: str, workout_update: Dict[str, Any]) -> str:
        update_type = workout_update.get("type")
        if update_type == "log_set":
            return (
                f"{text} I logged set {workout_update.get('set_number')} "
                f"for {workout_update.get('reps')} reps at {workout_update.get('weight')}."
            )
        if update_type == "advance_exercise":
            return f"{text} Moving you to the next exercise."
        if update_type == "recovery_flag":
            return f"{text} I marked this as a recovery warning for the current workout."
        return text

    def _extract_workout_update(
        self,
        transcript: str,
        session_context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        workout_context = session_context.get("workout_context") or {}
        exercises = workout_context.get("exercises") or []
        if not exercises:
            return None

        current_exercise_index = int(workout_context.get("current_exercise_index") or 0)
        lower = transcript.lower()

        if any(token in lower for token in ["next exercise", "move on", "skip exercise"]):
            return {
                "type": "advance_exercise",
                "exercise_index": min(current_exercise_index + 1, max(len(exercises) - 1, 0)),
                "current_exercise_index": min(current_exercise_index + 1, max(len(exercises) - 1, 0)),
                "completed_at": self._now_iso(),
            }

        if any(token in lower for token in ["pain", "sharp pain", "dizzy", "too sore"]):
            return {
                "type": "recovery_flag",
                "exercise_index": current_exercise_index,
                "current_exercise_index": current_exercise_index,
                "note": transcript,
                "completed_at": self._now_iso(),
            }

        reps_match = re.search(r"(\d+)\s*reps?", lower)
        weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilograms|lb|lbs|pounds)", lower)
        set_match = re.search(r"set\s*(\d+)", lower)

        if reps_match or weight_match:
            existing_sets = exercises[current_exercise_index].get("performed_sets", [])
            set_number = int(set_match.group(1)) if set_match else len(existing_sets) + 1
            return {
                "type": "log_set",
                "exercise_index": current_exercise_index,
                "current_exercise_index": current_exercise_index,
                "set_number": set_number,
                "reps": reps_match.group(1) if reps_match else "",
                "weight": weight_match.group(1) if weight_match else "",
                "completed_at": self._now_iso(),
                "source": "voice",
            }

        return None

    def _now_iso(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    async def generate_tts(
        self,
        text: str,
        language_code: str = "en-IN",
        speaker: str = "meera"
    ) -> Optional[str]:
        """
        Calls Sarvam TTS endpoint and returns base64-encoded WAV string.
        """
        # Clean text for TTS (remove bold markdown, etc.)
        clean_text = text.replace("**", "").replace("*", "")
        
        payload = {
            "inputs": [clean_text],
            "target_language_code": language_code,
            "speaker": speaker,
            "pitch": 0,
            "pace": 1.05,
            "loudness": 1.5,
            "speech_sample_rate": 24000,
            "enable_preprocessing": True,
            "model": "aura-v1-beta" # or latest
        }
        
        headers = {
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.sarvam_tts_url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        audios = data.get("audios", [])
                        if audios:
                            return audios[0] # base64 string
                    else:
                        err = await resp.text()
                        logger.error(f"Sarvam TTS Error ({resp.status}): {err}")
        except Exception as e:
            logger.error(f"TTS generation exception: {e}")
            
        return None


# Global singleton
voice_agent_service = VoiceAgentService()
