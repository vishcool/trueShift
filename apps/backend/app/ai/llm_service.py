"""
TrueShift - Gemini LLM Service

Handles interactions with Google's Gemini API (v1beta/v1alpha).
"""

import os
import json
import logging
import aiohttp
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Service for interacting with Google Gemini API.
    """
    BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/models")
    MODEL = settings.gemini_model
    def __init__(self):
        # Prefer application Settings (loads .env) but allow explicit env var fallback
        self.api_key = settings.google_api_key
        if not self.api_key:
            logger.warning("Gemini API key not configured (set GOOGLE_API_KEY or GEMINI_API_KEY)")

    async def generate_content(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate content using Gemini.
        Returns the parsed JSON response if schema is provided, or raw text.
        """
        if not self.api_key:
            return {"error": "API Key missing", "content": "Configuration Error: No API Key"}

        url = f"{self.BASE_URL}/{self.MODEL}:generateContent?key={self.api_key}"
        
        # Construct payload
        contents_part = {"parts": [{"text": prompt}]}
        
        payload = {
            "contents": [contents_part],
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if response_schema:
            # Force JSON mode
            payload["generationConfig"]["responseMimeType"] = "application/json"
            # In gemini-2.0-flash / pro, we can pass schema, but for simple JSON enforcement 
            # mimeType is often enough if the prompt is good. 
            # We can explore strict schema if needed.
            
        headers = {
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API Error {response.status}: {error_text}")
                        return {"error": f"API Error {response.status}", "details": error_text}
                    
                    data = await response.json()
                    
                    # Parse response
                    try:
                        candidates = data.get("candidates", [])
                        if not candidates:
                            return {"error": "No candidates returned"}
                        
                        content_part = candidates[0].get("content", {}).get("parts", [])[0]
                        text_response = content_part.get("text", "")
                        
                        if response_schema:
                            # Try to parse JSON
                            # Sometimes markdown blocks need stripping ```json ... ```
                            clean_text = text_response.strip()
                            if clean_text.startswith("```json"):
                                clean_text = clean_text[7:]
                            if clean_text.startswith("```"):
                                clean_text = clean_text[3:]
                            if clean_text.endswith("```"):
                                clean_text = clean_text[:-3]
                                
                            return json.loads(clean_text)
                        
                        return {"content": text_response}

                    except (json.JSONDecodeError, IndexError, AttributeError) as e:
                        logger.error(f"Failed to parse Gemini response: {e}")
                        return {"error": "Parsing Error", "raw": text_response}

        except Exception as e:
            logger.error(f"Gemini Service Exception: {e}")
            return {"error": f"Service Exception: {str(e)}"}

# Global instance
gemini_service = GeminiService()
