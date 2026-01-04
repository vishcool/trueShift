"""
TrueShift - User Model

User profile, preferences, and consent management.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    """
    User model storing profile and consent information.
    """

    __tablename__ = "users"

    # Firebase UID (external auth reference)
    firebase_uid: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=False,
    )

    # Profile Information
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # User Preferences
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Consent Flags - GDPR Compliance
    consent_location: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    consent_health_data: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    consent_camera: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    consent_digital_wellbeing: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    consent_ai_coaching: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    consent_analytics: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    consent_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Account Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Onboarding
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    onboarding_data: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    def get_consent_status(self) -> dict[str, bool]:
        """
        Get all consent flags as a dictionary.
        """
        return {
            "location_tracking": self.consent_location,
            "health_data": self.consent_health_data,
            "camera_access": self.consent_camera,
            "digital_wellbeing": self.consent_digital_wellbeing,
            "ai_coaching": self.consent_ai_coaching,
            "data_analytics": self.consent_analytics,
        }

    def has_required_consents(self, required: list[str]) -> bool:
        """
        Check if user has granted all required consents.
        """
        consent_map = self.get_consent_status()
        return all(consent_map.get(r, False) for r in required)
