from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class WorkoutGenerationRequest(BaseModel):
    """Request to generate a workout."""
    target_muscle_group: Optional[str] = "Full Body"
    duration_minutes: Optional[int] = 45
    equipment: Optional[List[str]] = []
    fitness_level: Optional[str] = "Intermediate"
    goals: Optional[str] = "General Fitness"

class WorkoutLogRequest(BaseModel):
    """Request to log a completed workout."""
    plan_id: str
    completion_data: Dict[str, Any]
    feedback: Optional[str] = None

class WorkoutPlanResponse(BaseModel):
    """Response model for workout plans."""
    id: str
    created_at: datetime
    scheduled_date: Optional[datetime]
    status: str
    plan_data: Dict[str, Any]
    completion_data: Optional[Dict[str, Any]]
    feedback_notes: Optional[str]
