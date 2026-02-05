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
            
            # Extract Context
            recovery_score = user_context.get('recovery_score', 50) # Default 50 (neutral)
            history = user_context.get('history', "No recent history")
            fitness_level = user_context.get('fitness_level', 'Intermediate')

            prompt = f"""
            Act as a strict, elite strength and conditioning coach.
            Analyze this image to identify the available gym equipment and PRESCRBE a precise workout.
            
            User Context:
            - Fitness Level: {fitness_level}
            - Recent History: {history}
            - Recovery Score: {recovery_score}/100 (<40=Poor, 40-70=Normal, >70=Prime)
            
            Directives:
            1. Identify the PRIMARY equipment available.
            2. PRESCRIBE exactly 3-5 high-value exercises. Do not suggest "options". Tell the user exactly what to do.
            3. DEFINE Volume based strictly on Recovery:
               - LOW Recovery (<40): PRESCRIBE Restoration. 2 sets max. High reps (15-20). Focus on blood flow.
               - NORMAL Recovery (40-70): PRESCRIBE Hypertrophy. 3 sets. 8-12 reps. Moderate intensity.
               - PRIME Recovery (>70): PRESCRIBE Strength/Power. 4-5 sets. 5-8 reps. Heavy intensity.
            
            4. BE PRECISE. "3 sets" is better than "3-4 sets". "10 reps" is better than "8-12 reps" unless failure is the goal.
            
            Structure the response as a valid JSON object with:
            {{
              "detected_equipment": "Main equipment identified",
              "analysis": "Direct command based on recovery (e.g., 'You are fresh. We go heavy today.')",
              "suggested_exercises": [
                {{
                  "name": "Exercise Name",
                  "sets": 3,
                  "reps": "10",
                  "rest_seconds": 90,
                  "notes": "Specific cue (e.g., 'Explode up, control down. No cheating.')"
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
