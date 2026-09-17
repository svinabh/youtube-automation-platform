from abc import ABC, abstractmethod
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.app.core.config import settings

class TextGenerationProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """Generate text based on a prompt."""
        pass

class MockTextGenerationProvider(TextGenerationProvider):
    async def generate_text(self, prompt: str) -> str:
        # Deterministic mock response for testing
        if not prompt:
            raise ValueError("Prompt cannot be empty")
        return f"Mock response for: {prompt}"

class OpenAITextGenerationProvider(TextGenerationProvider):
    def __init__(self):
        if settings is None or settings.OPENAI_API_KEY is None:
            raise RuntimeError("OPENAI_API_KEY is missing or invalid. Cannot initialize OpenAITextGenerationProvider.")
        self.api_key = settings.OPENAI_API_KEY.get_secret_value()
        self.timeout = settings.API_REQUEST_TIMEOUT

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def generate_text(self, prompt: str) -> str:
        if not prompt:
            raise ValueError("Prompt cannot be empty")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}]
            }
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
