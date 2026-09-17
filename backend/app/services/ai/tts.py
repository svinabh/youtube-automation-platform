from abc import ABC, abstractmethod
import httpx
import uuid
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.app.core.config import settings

class TTSProvider(ABC):
    @abstractmethod
    async def generate_audio(self, text: str, output_filename: str = None) -> Path:
        """Generate audio from text and return the path to the stored artifact."""
        pass

class MockTTSProvider(TTSProvider):
    def __init__(self):
        # Allow testing without actual config in non-prod
        if settings is not None:
            self.media_dir = settings.get_media_dir()
        else:
            self.media_dir = Path("/tmp/media")
            self.media_dir.mkdir(parents=True, exist_ok=True)

    async def generate_audio(self, text: str, output_filename: str = None) -> Path:
        if not text:
            raise ValueError("Text cannot be empty")

        filename = output_filename or f"mock_tts_{uuid.uuid4().hex}.mp3"
        output_path = self.media_dir / filename

        # Write dummy data to simulate an audio artifact
        output_path.write_bytes(b"mock_audio_data")
        return output_path

class ElevenLabsTTSProvider(TTSProvider):
    def __init__(self):
        if settings is None or settings.ELEVENLABS_API_KEY is None:
            raise RuntimeError("ELEVENLABS_API_KEY is missing or invalid. Cannot initialize ElevenLabsTTSProvider.")
        self.api_key = settings.ELEVENLABS_API_KEY.get_secret_value()
        self.timeout = settings.API_REQUEST_TIMEOUT
        self.media_dir = settings.get_media_dir()
        # Default voice ID, could be configurable
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def generate_audio(self, text: str, output_filename: str = None) -> Path:
        if not text:
            raise ValueError("Text cannot be empty")

        filename = output_filename or f"tts_{uuid.uuid4().hex}.mp3"
        output_path = self.media_dir / filename

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)

        return output_path
