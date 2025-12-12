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
    gateway_base_url: str = Field(default="https://criteria-sdp-api-gw-op.onrender.com", alias="SDP_GATEWAY_URL")
    gateway_client: str = Field(default="Minera Chinalco", alias="SDP_GATEWAY_CLIENT")
    gateway_api_key: str = Field(default="", alias="SDP_GATEWAY_API_KEY")
    comm_sla_default_hours: float = Field(default=48.0, alias="COMM_SLA_DEFAULT_HOURS")
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(default="", alias="AZURE_OPENAI_API_VERSION")
    azure_openai_deployment_gpt: str = Field(default="", alias="AZURE_OPENAI_DEPLOYMENT_GPT")

    def sanitized_database_url(self) -> str:
        """Return DB URL without unsupported sslmode query parameter."""
        url: URL = make_url(self.database_url)
        if "sslmode" in url.query:
            query = {k: v for k, v in url.query.items() if k != "sslmode"}
            url = url.set(query=query)
        return url.render_as_string(hide_password=False)


settings = Settings()
