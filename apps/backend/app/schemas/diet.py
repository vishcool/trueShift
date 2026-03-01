from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MacroTargets(BaseModel):
    calories: int = Field(..., ge=800, le=6000)
    protein_g: int = Field(..., ge=20, le=400)
    carbs_g: int = Field(..., ge=20, le=800)
    fats_g: int = Field(..., ge=10, le=250)


class MealTemplate(BaseModel):
    meal_name: str
    timing: str
    options: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class DietPlanRequest(BaseModel):
    goal: str = Field(default="Body Recomposition")
    daily_calories: Optional[int] = Field(default=None, ge=800, le=6000)
    protein_g: Optional[int] = Field(default=None, ge=20, le=400)
    carbs_g: Optional[int] = Field(default=None, ge=20, le=800)
    fats_g: Optional[int] = Field(default=None, ge=10, le=250)
    meals_per_day: int = Field(default=4, ge=2, le=8)
    dietary_preferences: List[str] = Field(default_factory=list)
    restrictions: List[str] = Field(default_factory=list)
    cuisine_preferences: List[str] = Field(default_factory=list)
    training_days_per_week: int = Field(default=4, ge=1, le=7)


class DietPlanResponse(BaseModel):
    id: str
    created_at: datetime
    goal: str
    macro_targets: MacroTargets
    hydration_target_liters: float
    meal_templates: List[MealTemplate]
    shopping_focus: List[str]
    adherence_tips: List[str]
