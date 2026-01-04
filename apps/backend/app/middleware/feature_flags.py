"""
TrueShift - Feature Flags Middleware

Feature flag checking for gradual rollout and A/B testing.
"""

from typing import Callable, Dict, Optional, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class FeatureFlagMiddleware(BaseHTTPMiddleware):
    """
    Feature flag middleware for controlling feature access.
    Supports:
    - Global feature flags
    - User-specific overrides
    - Percentage-based rollout (future)
    """

    # Endpoint to feature flag mapping
    PROTECTED_ENDPOINTS: Dict[str, str] = {
        "/api/v1/state/ai/coaching": "feature_ai_coaching",
        "/api/v1/vision": "feature_vision_analysis",
    }

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Check feature flags before processing request.
        """
        path = request.url.path

        # Check if endpoint is protected by a feature flag
        for endpoint_prefix, flag_name in self.PROTECTED_ENDPOINTS.items():
            if path.startswith(endpoint_prefix):
                if not self._check_flag(flag_name, request):
                    from starlette.responses import JSONResponse
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": "Feature not available",
                            "feature": flag_name,
                        },
                    )

        # Add feature flags to request state for downstream use
        request.state.feature_flags = self._get_active_flags()

        return await call_next(request)

    def _check_flag(self, flag_name: str, request: Request) -> bool:
        """
        Check if a feature flag is enabled.
        """
        return getattr(settings, flag_name, False)

    def _get_active_flags(self) -> Dict[str, bool]:
        """
        Get all active feature flags.
        """
        return {
            "ai_coaching": settings.feature_ai_coaching,
            "vision_analysis": settings.feature_vision_analysis,
            "background_sync": settings.feature_background_sync,
        }


class FeatureFlags:
    """
    Utility class for checking feature flags in code.
    """

    @staticmethod
    def is_enabled(flag_name: str, user_id: Optional[str] = None) -> bool:
        """
        Check if a feature is enabled.
        """
        flag_attr = f"feature_{flag_name}"
        return getattr(settings, flag_attr, False)

    @staticmethod
    def get_all() -> Dict[str, bool]:
        """
        Get all feature flags.
        """
        return {
            "ai_coaching": settings.feature_ai_coaching,
            "vision_analysis": settings.feature_vision_analysis,
            "background_sync": settings.feature_background_sync,
        }
