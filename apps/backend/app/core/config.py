"""
TrueShift - Application Configuration

Centralized configuration management using Pydantic Settings.
All configuration is loaded from environment variables.
"""

import json
from functools import lru_cache
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic-settings for validation and type coercion.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    api_v1_prefix: str = "/api/v1"

    # Database (local services default)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/trueshift"
    redis_url: str = "redis://localhost:6379/0"

    # Firebase Auth
    firebase_project_id: str = ""
    firebase_credentials_path: str = "./firebase-credentials.json"

    # Google AI / Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # Feature Flags
    feature_ai_coaching: bool = True
    feature_vision_analysis: bool = False
    feature_background_sync: bool = True
    bypass_auth: bool = False  # Set to True to bypass authentication in development


    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
