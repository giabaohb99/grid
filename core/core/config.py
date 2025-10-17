from typing import Dict, Any, Optional
import os
from urllib.parse import quote_plus
from enum import IntEnum
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App settings
    APP_NAME: str
    DEBUG: bool
    ENABLE_SSL: bool
    ENV: str = "development"
    PROJECT_NAME: str = "FastAPI Monolithic"
    API_V1_STR: str = "/v1"

    # CORS settings
    CORS: dict = {
        "ALLOW_ORIGINS": ["*"],
        "ALLOW_CREDENTIALS": True,
        "ALLOW_METHODS": ["*"],
        "ALLOW_HEADERS": ["*"],
    }

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 7 days

    # Database settings
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # AWS S3 Settings
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION_NAME: str
    AWS_S3_BUCKET_NAME: Optional[str] = None

    # Email settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "demopodnoreply@gmail.com"
    SMTP_PASSWORD: str = "lyvinsoqqzrqkmwf"
    ADMIN_EMAIL: str = "demopodnoreply@gmail.com"
    ADMIN_SUPPORT_EMAIL: str = "kirito993255@gmail.com"
    FROM_EMAIL: str = "demopodnoreply@gmail.com"

    COMPANY_NAME: str = "POD Software"
    ADMIN_DASHBOARD_URL: str = "http://localhost:8000/admin/support"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore' # Ignores extra fields instead of raising an error
    )

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()