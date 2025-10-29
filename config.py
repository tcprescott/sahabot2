"""
Application configuration module.

This module loads and validates all configuration settings from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings are loaded from .env file or environment variables.
    """

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "sahabot2"
    DB_PASSWORD: str
    DB_NAME: str = "sahabot2"

    # Discord OAuth2 Configuration
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str
    DISCORD_REDIRECT_URI: str = "http://localhost:8080/auth/callback"
    DISCORD_GUILD_ID: Optional[str] = None
    
    # Discord Bot Configuration
    DISCORD_BOT_TOKEN: str

    # Application Configuration
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    @property
    def database_url(self) -> str:
        """
        Generate database URL for Tortoise ORM.

        Returns:
            str: MySQL connection URL
        """
        return f"mysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def is_production(self) -> bool:
        """
        Check if running in production environment.

        Returns:
            bool: True if production, False otherwise
        """
        return self.ENVIRONMENT.lower() == "production"


# Global settings instance
settings = Settings()
