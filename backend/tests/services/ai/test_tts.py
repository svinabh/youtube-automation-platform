import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from backend.app.services.ai.tts import MockTTSProvider, ElevenLabsTTSProvider
import httpx

@pytest.fixture
def temp_media_dir(tmp_path):
    return tmp_path / "media"

@pytest.mark.asyncio
async def test_mock_tts_valid_text(temp_media_dir):
    with patch("backend.app.services.ai.tts.settings", None):
        provider = MockTTSProvider()
        provider.media_dir = temp_media_dir
        provider.media_dir.mkdir(parents=True, exist_ok=True)

        path = await provider.generate_audio("Hello world", "test.mp3")
        assert path == temp_media_dir / "test.mp3"
        assert path.exists()
        assert path.read_bytes() == b"mock_audio_data"

@pytest.mark.asyncio
async def test_mock_tts_empty_text():
    with patch("backend.app.services.ai.tts.settings", None):
        provider = MockTTSProvider()
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await provider.generate_audio("")

def test_elevenlabs_missing_key():
    with patch("backend.app.services.ai.tts.settings", None):
        with pytest.raises(RuntimeError, match="ELEVENLABS_API_KEY is missing"):
            ElevenLabsTTSProvider()

@pytest.mark.asyncio
async def test_elevenlabs_success_writes_file(temp_media_dir):
    mock_settings = MagicMock()
    mock_settings.ELEVENLABS_API_KEY.get_secret_value.return_value = "fake-key"
    mock_settings.API_REQUEST_TIMEOUT = 1
    mock_settings.get_media_dir.return_value = temp_media_dir
    temp_media_dir.mkdir(parents=True, exist_ok=True)

    with patch("backend.app.services.ai.tts.settings", mock_settings):
        provider = ElevenLabsTTSProvider()

        # Mock httpx.AsyncClient.stream
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()

        # Create an async generator for mock stream bytes
        async def mock_aiter_bytes():
            yield b"fake"
            yield b"_audio"

        mock_response.aiter_bytes.return_value = mock_aiter_bytes()
        # Ensure it returns the async generator directly instead of treating it as a coroutine
        mock_response.aiter_bytes = MagicMock(return_value=mock_aiter_bytes())

        # We mock __aenter__ to return our mock_response
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_response

        with patch("httpx.AsyncClient.stream", return_value=mock_context_manager):
            path = await provider.generate_audio("Test text", "eleven_test.mp3")

            assert path.exists()
            assert path.read_bytes() == b"fake_audio"
