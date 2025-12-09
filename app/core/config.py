"""Application settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import URL, make_url


class Settings(BaseSettings):
    """Centralized application settings loaded from environment."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="copilot-api", alias="APP_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    database_url: str = Field(..., alias="DATABASE_URL", min_length=1)
    # Use lowercase to avoid case-sensitive schema issues.
    db_schema: str = Field(default="copilot", alias="DB_SCHEMA")
    sql_echo: bool = Field(default=False, alias="SQL_ECHO")

    def sanitized_database_url(self) -> str:
        """Return DB URL without unsupported sslmode query parameter."""
        url: URL = make_url(self.database_url)
        if "sslmode" in url.query:
            query = {k: v for k, v in url.query.items() if k != "sslmode"}
            url = url.set(query=query)
        return url.render_as_string(hide_password=False)


settings = Settings()
