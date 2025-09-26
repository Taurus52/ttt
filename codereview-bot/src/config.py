"""Application configuration module."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Bot Configuration
    bot_token: str = Field(..., env="BOT_TOKEN")
    admin_tg_id: int = Field(..., env="ADMIN_TG_ID")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    db_host: str = Field("localhost", env="DB_HOST")
    db_port: int = Field(5432, env="DB_PORT")
    db_name: str = Field("codereview_bot", env="DB_NAME")
    db_user: str = Field("postgres", env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")
    
    # Application Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    environment: str = Field("development", env="ENVIRONMENT")
    
    # Optional: Sentry
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    
    @validator("admin_tg_id", pre=True)
    def validate_admin_id(cls, v):
        """Validate admin telegram ID."""
        if isinstance(v, str):
            return int(v)
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()