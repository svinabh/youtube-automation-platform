import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.app.services.ai.llm import MockTextGenerationProvider, OpenAITextGenerationProvider
import httpx

@pytest.mark.asyncio
async def test_mock_llm_valid_prompt():
    provider = MockTextGenerationProvider()
    response = await provider.generate_text("Hello")
    assert response == "Mock response for: Hello"

@pytest.mark.asyncio
async def test_mock_llm_empty_prompt():
    provider = MockTextGenerationProvider()
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        await provider.generate_text("")

def test_openai_missing_key():
    # Attempting to init real provider without config should raise RuntimeError
    # (Since our tests run with 'settings = None' due to missing .env, it should raise)
    with patch("backend.app.services.ai.llm.settings", None):
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY is missing or invalid"):
            OpenAITextGenerationProvider()

@pytest.mark.asyncio
async def test_openai_retries_on_http_error():
    # Test that the tenacity retry logic kicks in
    mock_settings = MagicMock()
    mock_settings.OPENAI_API_KEY.get_secret_value.return_value = "fake-key"
    mock_settings.API_REQUEST_TIMEOUT = 1

    with patch("backend.app.services.ai.llm.settings", mock_settings):
        provider = OpenAITextGenerationProvider()

        # We patch the retry decorator to not actually wait during tests
        provider.generate_text.retry.sleep = AsyncMock()

        # Mock the httpx client to always raise HTTPStatusError
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=MagicMock(status_code=500)
            )

            with pytest.raises(httpx.HTTPStatusError):
                await provider.generate_text("Test prompt")

            # It should have tried 3 times based on our retry config
            assert mock_post.call_count == 3
