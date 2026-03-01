import json
import logging
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from app.ai.llm_service import gemini_service
from app.schemas.diet import DietPlanRequest

logger = logging.getLogger(__name__)


class DietService:
    @staticmethod
    def _fallback_plan(request: DietPlanRequest) -> Dict[str, Any]:
        calories = request.daily_calories or 2200
        protein = request.protein_g or int(calories * 0.3 / 4)
        carbs = request.carbs_g or int(calories * 0.4 / 4)
        fats = request.fats_g or int(calories * 0.3 / 9)

        base_meals = [
            "Protein source + complex carb + vegetables",
            "Greek yogurt / curd + fruit + nuts",
            "Lean protein bowl with rice/millet and salad",
            "Egg/paneer/tofu wrap with greens",
            "Post-workout whey or high-protein smoothie",
        ]

        meal_templates = []
        for i in range(request.meals_per_day):
            meal_templates.append(
                {
                    "meal_name": f"Meal {i + 1}",
                    "timing": ["Pre-workout", "Post-workout", "Midday", "Dinner", "Snack"][i % 5],
                    "options": [
                        base_meals[i % len(base_meals)],
                        "Adjust portions to match macro targets",
                    ],
                    "notes": "Keep protein in every meal.",
                }
            )

        return {
            "id": str(uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "goal": request.goal,
            "macro_targets": {
                "calories": calories,
                "protein_g": protein,
                "carbs_g": carbs,
                "fats_g": fats,
            },
            "hydration_target_liters": 3.0,
            "meal_templates": meal_templates,
            "shopping_focus": [
                "Lean protein sources",
                "High-fiber carbs",
                "Seasonal vegetables",
                "Hydration/electrolyte support",
            ],
            "adherence_tips": [
                "Pre-log meals in the morning.",
                "Batch-cook protein 2 times per week.",
                "Keep one emergency high-protein snack ready.",
            ],
        }

    async def generate_plan(self, payload: DietPlanRequest, user_context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
You are an elite sports nutrition coach. Build a practical diet plan for gym performance and body composition.

User request:
{payload.model_dump_json(indent=2)}

User context:
{json.dumps(user_context, indent=2)}

Return strict JSON with this shape:
{{
  "id": "uuid-string",
  "created_at": "iso-datetime",
  "goal": "string",
  "macro_targets": {{
    "calories": 2200,
    "protein_g": 160,
    "carbs_g": 230,
    "fats_g": 70
  }},
  "hydration_target_liters": 3.0,
  "meal_templates": [
    {{
      "meal_name": "Meal 1",
      "timing": "Pre-workout",
      "options": ["option 1", "option 2"],
      "notes": "short note"
    }}
  ],
  "shopping_focus": ["item 1", "item 2"],
  "adherence_tips": ["tip 1", "tip 2"]
}}

Rules:
- Keep meal options locally practical for India.
- Respect dietary preferences and restrictions.
- Keep calories/macros realistic.
"""

        generated = await gemini_service.generate_content(prompt=prompt, response_schema={"type": "object"})
        if isinstance(generated, dict) and generated.get("error"):
            logger.warning("Diet generation fallback due to Gemini error: %s", generated.get("error"))
            return self._fallback_plan(payload)

        if not isinstance(generated, dict):
            return self._fallback_plan(payload)

        generated.setdefault("id", str(uuid4()))
        generated.setdefault("created_at", datetime.utcnow().isoformat())
        generated.setdefault("goal", payload.goal)
        generated.setdefault("macro_targets", self._fallback_plan(payload)["macro_targets"])
        generated.setdefault("meal_templates", self._fallback_plan(payload)["meal_templates"])
        generated.setdefault("hydration_target_liters", 3.0)
        generated.setdefault("shopping_focus", ["Lean protein", "Complex carbs", "Vegetables"])
        generated.setdefault("adherence_tips", ["Plan meals ahead", "Hit protein target daily"])

        return generated


diet_service = DietService()
