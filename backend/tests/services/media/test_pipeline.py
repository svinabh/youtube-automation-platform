import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from backend.app.services.media.pipeline import MockMediaPipeline, FFmpegMediaPipeline
import asyncio

@pytest.fixture
def temp_media_dir(tmp_path):
    return tmp_path / "media"

@pytest.fixture
def dummy_audio_file(temp_media_dir):
    temp_media_dir.mkdir(parents=True, exist_ok=True)
    audio = temp_media_dir / "test_audio.mp3"
    audio.write_bytes(b"dummy")
    return audio

@pytest.mark.asyncio
async def test_mock_media_pipeline(temp_media_dir, dummy_audio_file):
    with patch("backend.app.services.media.pipeline.settings", None):
        pipeline = MockMediaPipeline()
        pipeline.media_dir = temp_media_dir

        path = await pipeline.generate_video(dummy_audio_file, output_filename="test_vid.mp4")
        assert path.exists()
        assert path.read_bytes() == b"mock_video_data"

@pytest.mark.asyncio
async def test_mock_media_missing_audio(temp_media_dir):
    with patch("backend.app.services.media.pipeline.settings", None):
        pipeline = MockMediaPipeline()
        pipeline.media_dir = temp_media_dir

        missing_audio = temp_media_dir / "does_not_exist.mp3"
        with pytest.raises(FileNotFoundError):
            await pipeline.generate_video(missing_audio)

@pytest.mark.asyncio
async def test_ffmpeg_pipeline_success(temp_media_dir, dummy_audio_file):
    with patch("backend.app.services.media.pipeline.settings", None):
        pipeline = FFmpegMediaPipeline()
        pipeline.media_dir = temp_media_dir

        # We need to mock asyncio.create_subprocess_exec to avoid actually calling ffmpeg in tests
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=(b"stdout", b"stderr"))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            path = await pipeline.generate_video(dummy_audio_file, output_filename="ffmpeg_test.mp4")

            assert path == temp_media_dir / "ffmpeg_test.mp4"
            mock_exec.assert_called_once()

@pytest.mark.asyncio
async def test_ffmpeg_pipeline_failure(temp_media_dir, dummy_audio_file):
    with patch("backend.app.services.media.pipeline.settings", None):
        pipeline = FFmpegMediaPipeline()
        pipeline.media_dir = temp_media_dir

        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=(b"stdout", b"ffmpeg error output"))
        mock_process.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with pytest.raises(RuntimeError, match="FFmpeg failed with return code 1"):
                await pipeline.generate_video(dummy_audio_file)
