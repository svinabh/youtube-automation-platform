import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock, call

from app.rendering.models import Resolution, MediaElement, MediaType, Scene, Timeline
from app.rendering.ffmpeg_renderer import FFmpegRenderer, FFmpegRendererError

@pytest.fixture
def complex_timeline():
    # Video with delay
    elem1 = MediaElement(
        id="el1",
        media_type=MediaType.VIDEO,
        file_path="/tmp/vid1.mp4",
        start_time=2.0,
        duration=3.0
    )
    scene1 = Scene(id="s1", elements=[elem1], duration=5.0)

    # Audio-only and Image in same scene
    elem_audio = MediaElement(
        id="el_aud",
        media_type=MediaType.AUDIO,
        file_path="/tmp/effect.wav",
        start_time=0.0,
        duration=2.0
    )
    elem_img = MediaElement(
        id="el_img",
        media_type=MediaType.IMAGE,
        file_path="/tmp/img1.png",
        start_time=0.0,
        duration=5.0
    )
    scene2 = Scene(id="s2", elements=[elem_audio, elem_img], duration=5.0)

    # Global audio track
    track = MediaElement(
        id="tr1",
        media_type=MediaType.AUDIO,
        file_path="/tmp/bgm.mp3",
        duration=10.0
    )

    return Timeline(
        id="tl1",
        resolution=Resolution(width=1920, height=1080),
        scenes=[scene1, scene2],
        global_audio_tracks=[track],
        output_path="/tmp/output.mp4"
    )

@pytest.mark.asyncio
@patch('os.makedirs')
@patch('os.path.exists', return_value=True)
async def test_ffmpeg_renderer_filtergraph(mock_exists, mock_makedirs, complex_timeline, mocker):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"stdout", b"stderr"))
    mocker.patch("asyncio.create_subprocess_exec", return_value=mock_process)

    renderer = FFmpegRenderer()
    result = await renderer.render(complex_timeline)

    assert result["status"] == "success"
    cmd = result["command"]
    filter_string = cmd[cmd.index("-filter_complex") + 1]

    # 1. Test Input index alignment and tpad/adelay semantics
    # Scene 1: element 0 (video) with start_time=2.0
    assert "tpad=start_duration=2.0" in filter_string
    assert "adelay=2000|2000" in filter_string

    # 2. Test proper output naming for scenes
    assert "[s0v_out]" in filter_string
    assert "[s0a_out]" in filter_string
    assert "[s1v_out]" in filter_string
    assert "[s1a_out]" in filter_string

    # 3. Test Interleaving concat syntax
    # The concat filter should receive [s0v_out][s0a_out][s1v_out][s1a_out] exactly in that order
    assert "[s0v_out][s0a_out][s1v_out][s1a_out]concat=n=2:v=1:a=1" in filter_string

    # 4. Global audio mixing
    assert "amix" in filter_string

@pytest.mark.asyncio
@patch('os.makedirs')
@patch('os.remove')
@patch('os.path.exists')
async def test_ffmpeg_renderer_failure_cleanup(mock_exists, mock_remove, mock_makedirs, complex_timeline, mocker):

    # Track the call counts to mock_exists separately
    exists_calls = 0

    def exists_side_effect(path):
        nonlocal exists_calls
        exists_calls += 1

        if path == complex_timeline.output_path:
            # We want it to be False on the first check (output_existed = os.path.exists)
            # Then True on the second check (inside the failure block to trigger cleanup)
            # Then False on the third check (inside the Exception block, which shouldn't run anyway if we catch FFmpegRendererError, but just in case)
            if exists_calls <= 5: # Assuming dirs, inputs, etc. taking up first 4 calls
                 return False
            elif exists_calls == 6:
                 return True
            return False
        return True

    mock_exists.side_effect = exists_side_effect

    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"Error message from ffmpeg"))

    mocker.patch("asyncio.create_subprocess_exec", return_value=mock_process)
    renderer = FFmpegRenderer()

    with pytest.raises(FFmpegRendererError, match="FFmpeg process failed with code 1"):
        await renderer.render(complex_timeline)

    mock_remove.assert_called_once_with(complex_timeline.output_path)
