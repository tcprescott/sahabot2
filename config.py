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
    DISCORD_BOT_ENABLED: bool = True  # Set to False to disable Discord bot

    # Racetime.gg Configuration
    # Format: category1:client_id:client_secret,category2:client_id:client_secret
    RACETIME_BOTS: str = ""  # Comma-separated list of category:client_id:client_secret
    RACETIME_BOTS_ENABLED: bool = True  # Set to False to disable Racetime bots

    # Racetime.gg OAuth2 Configuration (for user account linking)
    RACETIME_CLIENT_ID: str = ""
    RACETIME_CLIENT_SECRET: str = ""
    RACETIME_OAUTH_REDIRECT_URI: Optional[str] = None  # Will default to {BASE_URL}/racetime/link/callback
    RACETIME_URL: str = "https://racetime.gg"

    # Application Configuration
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    BASE_URL: str = "http://localhost:8080"  # Base URL for the application

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # API Rate Limiting
    API_RATE_LIMIT_WINDOW_SECONDS: int = 60
    API_DEFAULT_RATE_LIMIT_PER_MINUTE: int = 60

    # Randomizer Configuration
    ALTTPR_BASEURL: str = "https://alttpr.com"
    OOTR_API_KEY: Optional[str] = None

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

    @property
    def racetime_bot_configs(self) -> list[tuple[str, str, str]]:
        """
        Parse racetime bot configurations.

        Returns:
            List of tuples: (category, client_id, client_secret)
        """
        if not self.RACETIME_BOTS:
            return []

        configs = []
        for bot_config in self.RACETIME_BOTS.split(','):
            bot_config = bot_config.strip()
            if not bot_config:
                continue

            parts = bot_config.split(':')
            if len(parts) == 3:
                category, client_id, client_secret = parts
                configs.append((category.strip(), client_id.strip(), client_secret.strip()))

        return configs

    def get_racetime_oauth_redirect_uri(self) -> str:
        """
        Get the RaceTime OAuth redirect URI.

        If RACETIME_OAUTH_REDIRECT_URI is set in the environment, use that.
        Otherwise, construct it from BASE_URL.

        Returns:
            str: The OAuth redirect URI for RaceTime
        """
        if self.RACETIME_OAUTH_REDIRECT_URI:
            return self.RACETIME_OAUTH_REDIRECT_URI
        return f"{self.BASE_URL.rstrip('/')}/racetime/link/callback"


# Global settings instance
settings = Settings()

# Alias for backward compatibility with external imports
# Use 'settings' instance directly instead for new code
Config = Settings
