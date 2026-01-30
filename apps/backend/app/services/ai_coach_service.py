"""
TrueShift - AI Coach Service

Uses Google Gemini to provide human-friendly feedback on workout form
based on metrics from the V-JEPA vision model.
"""

import logging
from typing import Dict, Any, Optional
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class AICoachService:
    def __init__(self):
        if settings.google_api_key:
            self.client = genai.Client(api_key=settings.google_api_key)
            self.model_name = settings.gemini_model
        else:
            logger.warning("Google API Key not found. AI Coach will be disabled.")
            self.client = None
            self.model_name = None

    async def generate_feedback(self, metrics: Dict[str, Any], user_context: Optional[Dict] = None) -> str:
        """
        Generates human-friendly feedback based on vision metrics.
        
        Args:
            metrics: Dictionary containing form score, rep count, and specific issues.
            user_context: Optional dictionary with user history/goals.
        """
        if not self.client:
            return "AI Coach unavailable (API Key missing)."

        try:
            # unique context construction
            exercise = metrics.get('exercise', 'movement')
            score = metrics.get('form_score', 0)
            issues = metrics.get('issues', [])
            reps = metrics.get('reps', 0)
            
            prompt = f"""
            You are an encouraging and expert fitness coach. 
            A user is performing {exercise}.
            
            Here is the live data from their latest set:
            - Form Score: {score}/100
            - Rep Count: {reps}
            - Detected Issues: {', '.join(issues) if issues else 'None'}
            
            User Context: {user_context if user_context else 'None'}
            
            Give a ONE SENTENCE, concise, and motivating feedback message. 
            - If the score is high (>85), praise them.
            - If there are issues, give a specific tip to correct the most important one.
            - Keep it under 20 words.
            """
            
            # Generate content using new SDK
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate AI feedback: {e}")
            return "Keep going! You're doing great."

    async def generate_workout_from_image(self, image_bytes: bytes, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a workout plan based on an image of available equipment.
        
        Args:
            image_bytes: Raw bytes of the uploaded image.
            user_context: User profile and goals (Dict).
        """
        if not self.client:
            return {"error": "AI Coach unavailable (API Key missing)."}

        try:
            from google.genai import types
            
            prompt = f"""
            Act as an elite personal trainer. 
            Analyze this image to identify the available gym equipment.
            Based ONLY on the detected equipment (or lack thereof, implying bodyweight), generate a structured workout plan for the user.
            
            User Profile:
            - Fitness Level: {user_context.get('fitness_level', 'Intermediate')}
            - Duration: {user_context.get('duration_minutes', 45)} minutes
            - Goal: {user_context.get('goals', 'General Fitness')}
            
            Structure the response as a valid JSON object with:
            {{
              "overview": "Brief description of the workout intent (e.g., 'Full Body Dumbbell HIIT' or 'Bodyweight Cardio')",
              "detected_equipment": ["List", "of", "detected", "items"],
              "exercises": [
                {{
                  "name": "Exercise Name",
                  "sets": 3,
                  "reps": "10-12",
                  "rest_seconds": 60,
                  "notes": "Form cue or tip"
                }}
              ]
            }}
            Do not include markdown formatting. Return raw JSON.
            """

            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            
            import json
            return json.loads(response.text)

        except Exception as e:
            logger.error(f"Failed to generate workout from image: {e}")
            return {"error": f"Failed to generate workout: {str(e)}"}

ai_coach_service = AICoachService()
