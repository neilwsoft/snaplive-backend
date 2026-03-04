"""Application configuration using pydantic-settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings and configuration"""

    # Application
    app_name: str = "SnapLive Backend"
    app_version: str = "0.1.0"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000  # Will be overridden by PORT env var on Render

    # MongoDB
    mongodb_url: str
    mongodb_db_name: str = "snaplive"
    mongodb_min_pool_size: int = 10
    mongodb_max_pool_size: int = 50

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    # JWT Authentication
    secret_key: str = "your-secret-key-change-this-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    refresh_token_expire_days_remember: int = 30
    password_reset_token_expire_hours: int = 24

    # Email Configuration
    email_from: str = "noreply@snaplive.com"
    email_from_name: str = "SnapLive"
    # Email service provider settings (for future use)
    # email_api_key: Optional[str] = None  # SendGrid, AWS SES, etc.
    # smtp_host: Optional[str] = None
    # smtp_port: Optional[int] = 587
    # smtp_username: Optional[str] = None
    # smtp_password: Optional[str] = None

    # Environment
    environment: str = "development"

    # LiveKit Configuration
    livekit_url: str = "wss://your-project.livekit.cloud"
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # Object Detection Configuration
    yolo_model_path: str = "../snaplive-ai/yolo12n.pt"
    detection_confidence_threshold: float = 0.25
    detection_image_size: int = 416  # Balanced preset for 40-60 FPS

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )


def get_settings() -> Settings:
    """Get settings instance"""
    return Settings()


settings = Settings()

