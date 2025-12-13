"""Cliente IA para Azure OpenAI."""

from typing import Any, Dict, List

from openai import AsyncAzureOpenAI, OpenAIError

from app.core.config import settings


class IAClient:
    """Encapsula llamadas al deployment GPT en Azure OpenAI."""

    def __init__(self) -> None:
        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            raise ValueError("azure_openai_not_configured")
        self.client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
        self.deployment = settings.azure_openai_deployment_gpt

    async def generate_reply(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 400,
    ) -> str:
        """Genera un mensaje de respuesta usando chat completions."""
        try:
            resp = await self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except OpenAIError as exc:
            # Propagar para que el endpoint registre en ia_logs y devuelva error claro.
            raise
        content = resp.choices[0].message.content if resp.choices else ""
        return content or ""

    async def interpret_conversation(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 400,
    ) -> str:
        """Interpreta historial/conversación y devuelve sugerencia de enfoque."""
        try:
            resp = await self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except OpenAIError as exc:
            raise
        content = resp.choices[0].message.content if resp.choices else ""
        return content or ""
