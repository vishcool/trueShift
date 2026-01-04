"""
TrueShift - Security & Authentication

Firebase Auth verification and consent management.
"""

from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import firebase_admin
from firebase_admin import auth, credentials

from app.core.config import settings


# Initialize Firebase Admin SDK
_firebase_app: Optional[firebase_admin.App] = None
security = HTTPBearer()


def init_firebase() -> None:
    """
    Initialize Firebase Admin SDK.
    Called on application startup if credentials are available.
    """
    global _firebase_app

    if _firebase_app is not None:
        return

    try:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        _firebase_app = firebase_admin.initialize_app(cred)
    except Exception as e:
        if settings.is_development:
            print(f"Warning: Firebase initialization failed: {e}")
            print("Running without Firebase authentication in development mode.")
        else:
            raise


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Verify Firebase ID token from Authorization header.
    Returns decoded token data on success.
    """
    token = credentials.credentials

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
        )
    except Exception as e:
        if settings.is_development:
            # Allow development without Firebase
            return {
                "uid": "dev-user-001",
                "email": "dev@trueshift.local",
                "dev_mode": True,
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


async def get_current_user_id(
    token_data: dict = Depends(verify_firebase_token),
) -> str:
    """
    Extract user ID from verified token.
    """
    return token_data.get("uid", "")


class ConsentManager:
    """
    Manages user consent for data collection and processing.
    Ensures GDPR/privacy compliance.
    """

    CONSENT_TYPES = [
        "location_tracking",
        "health_data",
        "camera_access",
        "digital_wellbeing",
        "ai_coaching",
        "data_analytics",
    ]

    @staticmethod
    def validate_consent(consent_data: dict, required_consents: list[str]) -> bool:
        """
        Validate that user has given required consents.
        """
        for consent_type in required_consents:
            if not consent_data.get(consent_type, False):
                return False
        return True

    @staticmethod
    def create_consent_record(
        user_id: str,
        consent_type: str,
        granted: bool,
    ) -> dict:
        """
        Create a consent record for audit trail.
        """
        return {
            "user_id": user_id,
            "consent_type": consent_type,
            "granted": granted,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
        }
