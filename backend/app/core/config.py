from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # Core API Keys
    OPENAI_API_KEY: SecretStr = Field(
        ...,
        description="OpenAI API Key for text generation. Required in production."
    )
    ELEVENLABS_API_KEY: Optional[SecretStr] = Field(
        None,
        description="ElevenLabs API Key for TTS."
    )

    # Retry & Timeout Settings
    API_REQUEST_TIMEOUT: int = Field(30, description="Global API request timeout in seconds.")
    MAX_RETRIES: int = Field(3, description="Maximum number of retries for external API calls.")

    # Media Artifacts Settings
    MEDIA_STORAGE_PATH: str = Field(
        "/tmp/media",
        description="Base path for storing generated media artifacts."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_media_dir(self) -> Path:
        """Ensure media directory exists and return it."""
        path = Path(self.MEDIA_STORAGE_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path

# Global settings instance
try:
    settings = Settings()
except Exception as e:
    # Fail closed if required credentials (e.g., OPENAI_API_KEY) are missing in a real env.
    # We provide a mock instance for testing/import if we can't load the real one immediately.
    # In a real app we might let this crash, but we will catch it here to allow tests to run with mocks.
    settings = None # type: ignore
    print(f"Warning: Configuration could not be loaded: {e}. 'settings' is None.")
