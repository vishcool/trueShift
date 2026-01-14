"""
TrueShift - Authentication Routes

User authentication and consent management endpoints.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    get_current_user_id,
    verify_firebase_token,
    ConsentManager,
)
from app.models.user import User
from app.models.user_state import UserState

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class UserRegisterRequest(BaseModel):
    """Request body for user registration."""
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None


class ConsentUpdateRequest(BaseModel):
    """Request body for updating consent."""
    location_tracking: Optional[bool] = None
    health_data: Optional[bool] = None
    camera_access: Optional[bool] = None
    digital_wellbeing: Optional[bool] = None
    ai_coaching: Optional[bool] = None
    data_analytics: Optional[bool] = None


class UserProfileUpdateRequest(BaseModel):
    """Request body for updating user profile."""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    # Fitness Profile Data
    fitness_goals: Optional[list[str]] = None
    equipment: Optional[list[str]] = None
    fitness_level: Optional[str] = None



class UserResponse(BaseModel):
    """User response model."""
    id: str
    firebase_uid: str
    email: Optional[str]
    display_name: Optional[str]
    is_active: bool
    is_premium: bool
    onboarding_completed: bool
    consent_status: dict


class ConsentResponse(BaseModel):
    """Consent status response."""
    consents: dict
    updated_at: Optional[str]


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/register", response_model=UserResponse)
async def register_user(
    request: UserRegisterRequest,
    token_data: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user or return existing user.
    Called after Firebase authentication.
    """
    firebase_uid = token_data.get("uid")
    email = token_data.get("email") or request.email

    # Check if user exists
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()

    if user:
        return UserResponse(
            id=user.id,
            firebase_uid=user.firebase_uid,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
            is_premium=user.is_premium,
            onboarding_completed=user.onboarding_completed,
            consent_status=user.get_consent_status(),
        )

    # Create new user
    user = User(
        firebase_uid=firebase_uid,
        email=email,
        display_name=request.display_name,
    )
    db.add(user)
    await db.flush()

    # Create initial user state
    user_state = UserState(user_id=user.id)
    db.add(user_state)

    return UserResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_premium=user.is_premium,
        onboarding_completed=user.onboarding_completed,
        consent_status=user.get_consent_status(),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user profile.
    """
    result = await db.execute(
        select(User).where(User.firebase_uid == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_premium=user.is_premium,
        onboarding_completed=user.onboarding_completed,
        consent_status=user.get_consent_status(),
    )


@router.get("/consent", response_model=ConsentResponse)
async def get_consent_status(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current consent status.
    """
    result = await db.execute(
        select(User).where(User.firebase_uid == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return ConsentResponse(
        consents=user.get_consent_status(),
        updated_at=user.consent_updated_at.isoformat() if user.consent_updated_at else None,
    )


@router.put("/consent", response_model=ConsentResponse)
async def update_consent(
    request: ConsentUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user consent preferences.
    """
    result = await db.execute(
        select(User).where(User.firebase_uid == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update consent flags
    if request.location_tracking is not None:
        user.consent_location = request.location_tracking
    if request.health_data is not None:
        user.consent_health_data = request.health_data
    if request.camera_access is not None:
        user.consent_camera = request.camera_access
    if request.digital_wellbeing is not None:
        user.consent_digital_wellbeing = request.digital_wellbeing
    if request.ai_coaching is not None:
        user.consent_ai_coaching = request.ai_coaching
    if request.data_analytics is not None:
        user.consent_analytics = request.data_analytics

    user.consent_updated_at = datetime.now(timezone.utc)

    return ConsentResponse(
        consents=user.get_consent_status(),
        updated_at=user.consent_updated_at.isoformat(),
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UserProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user profile and fitness preferences.
    """
    result = await db.execute(
        select(User).where(User.firebase_uid == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update basic profile
    if request.display_name is not None:
        user.display_name = request.display_name
    if request.avatar_url is not None:
        user.avatar_url = request.avatar_url

    # Update fitness profile in preferences
    # We load existing prefs, update, and save back
    prefs = dict(user.preferences) if user.preferences else {}
    fitness_profile = prefs.get("fitness_profile", {})
    
    if request.fitness_goals is not None:
        fitness_profile["goals"] = request.fitness_goals
    if request.equipment is not None:
        fitness_profile["equipment"] = request.equipment
    if request.fitness_level is not None:
        fitness_profile["level"] = request.fitness_level
        
    prefs["fitness_profile"] = fitness_profile
    user.preferences = prefs

    # If this is the first time setting goals, we mark onboarding as done
    if request.fitness_goals and not user.onboarding_completed:
        user.onboarding_completed = True

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_premium=user.is_premium,
        onboarding_completed=user.onboarding_completed,
        consent_status=user.get_consent_status(),
    )

