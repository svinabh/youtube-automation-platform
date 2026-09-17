from abc import ABC, abstractmethod
from pathlib import Path
import uuid
import ffmpeg
import asyncio
from backend.app.core.config import settings

class MediaPipeline(ABC):
    @abstractmethod
    async def generate_video(self, audio_path: Path, image_path: Path = None, text: str = None, output_filename: str = None) -> Path:
        """Combine audio and visual elements into a video artifact."""
        pass

class MockMediaPipeline(MediaPipeline):
    def __init__(self):
        if settings is not None:
            self.media_dir = settings.get_media_dir()
        else:
            self.media_dir = Path("/tmp/media")
            self.media_dir.mkdir(parents=True, exist_ok=True)

    async def generate_video(self, audio_path: Path, image_path: Path = None, text: str = None, output_filename: str = None) -> Path:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        filename = output_filename or f"mock_video_{uuid.uuid4().hex}.mp4"
        output_path = self.media_dir / filename

        # Write dummy data to simulate a video artifact
        output_path.write_bytes(b"mock_video_data")
        return output_path

class FFmpegMediaPipeline(MediaPipeline):
    def __init__(self):
        # Allow testing without actual config in non-prod
        if settings is not None:
            self.media_dir = settings.get_media_dir()
        else:
            self.media_dir = Path("/tmp/media")
            self.media_dir.mkdir(parents=True, exist_ok=True)

    async def generate_video(self, audio_path: Path, image_path: Path = None, text: str = None, output_filename: str = None) -> Path:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        filename = output_filename or f"video_{uuid.uuid4().hex}.mp4"
        output_path = self.media_dir / filename

        # We need either an image or we will generate a black background video
        try:
            audio_input = ffmpeg.input(str(audio_path))

            if image_path and image_path.exists():
                # Image based video looping image over audio duration
                video_input = ffmpeg.input(str(image_path), loop=1, framerate=1)
                stream = ffmpeg.output(
                    video_input,
                    audio_input,
                    str(output_path),
                    vcodec='libx264',
                    acodec='aac',
                    shortest=None,  # Finish encoding when the shortest stream (audio) ends
                    pix_fmt='yuv420p'
                )
            else:
                # Black background video if no image provided (for basic testing/fallback)
                video_input = ffmpeg.input('color=c=black:s=1280x720:r=30', f='lavfi')
                stream = ffmpeg.output(
                    video_input,
                    audio_input,
                    str(output_path),
                    vcodec='libx264',
                    acodec='aac',
                    shortest=None
                )

            # Run ffmpeg asynchronously
            process = await asyncio.create_subprocess_exec(
                *ffmpeg.compile(stream, overwrite_output=True),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg failed with return code {process.returncode}:\n{stderr.decode()}")

        except ffmpeg.Error as e:
            raise RuntimeError(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")

        return output_path
