"""Application settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="copilot-api", alias="APP_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    database_url: str = Field(..., alias="DATABASE_URL", min_length=1)
    db_schema: str = Field(default="Copilot", alias="DB_SCHEMA")
    sql_echo: bool = Field(default=False, alias="SQL_ECHO")


settings = Settings()
