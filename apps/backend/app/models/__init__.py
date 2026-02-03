"""
Models package initialization.
Import all models here to ensure they are registered with SQLAlchemy Base.
"""

# Import all models to register with Base metadata
from app.models.user import User
from app.models.user_state import UserState
from app.models.preferences import UserPreferences
from app.models.wellness import SleepLog, MoodLog, PainLog
from app.models.event import Event
from app.models.user_behavior import BehavioralMarkers, InterventionHistory
from app.models.conversation import ConversationLog
from app.models.vision_log import MovementAnalysis
from app.models.workout import WorkoutPlan
from app.models.user_memory import UserMemory

__all__ = [
    "User",
    "UserState",
    "UserPreferences",
    "SleepLog",
    "MoodLog",
    "PainLog",
    "Event",
    "BehavioralMarkers",
    "InterventionHistory",
    "ConversationLog",
    "MovementAnalysis",
    "WorkoutPlan",
    "UserMemory",
]
