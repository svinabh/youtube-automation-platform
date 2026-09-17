import pytest

from app.rendering.models import Resolution, MediaElement, MediaType, Scene, Timeline
from app.rendering.validation import validate_timeline, TimelineValidationError

@pytest.fixture
def base_resolution():
    return Resolution(width=1920, height=1080)

def test_validate_empty_scenes(base_resolution):
    tl = Timeline(
        id="tl1",
        resolution=base_resolution,
        scenes=[],
        output_path="/tmp/out.mp4"
    )
    with pytest.raises(TimelineValidationError, match="contain at least one scene"):
        validate_timeline(tl)

def test_validate_element_exceeds_scene(base_resolution):
    elem = MediaElement(
        id="el1",
        media_type=MediaType.VIDEO,
        file_path="/tmp/vid.mp4",
        start_time=5.0,
        duration=10.0
    )
    scene = Scene(id="s1", elements=[elem], duration=12.0)
    tl = Timeline(
        id="tl1",
        resolution=base_resolution,
        scenes=[scene],
        output_path="/tmp/out.mp4"
    )

    with pytest.raises(TimelineValidationError, match="exceeds scene"):
        validate_timeline(tl)

def test_validate_global_track_exceeds_timeline(base_resolution):
    scene = Scene(id="s1", elements=[], duration=10.0)
    track = MediaElement(
        id="tr1",
        media_type=MediaType.AUDIO,
        file_path="/tmp/audio.mp3",
        duration=15.0
    )

    tl = Timeline(
        id="tl1",
        resolution=base_resolution,
        scenes=[scene],
        global_audio_tracks=[track],
        output_path="/tmp/out.mp4"
    )

    with pytest.raises(TimelineValidationError, match="extends beyond total timeline duration"):
        validate_timeline(tl)

def test_validate_valid_timeline(base_resolution):
    elem = MediaElement(
        id="el1",
        media_type=MediaType.VIDEO,
        file_path="/tmp/vid.mp4",
        start_time=0.0,
        duration=10.0
    )
    scene = Scene(id="s1", elements=[elem], duration=10.0)

    tl = Timeline(
        id="tl1",
        resolution=base_resolution,
        scenes=[scene],
        output_path="/tmp/out.mp4"
    )

    # Should not raise
    validate_timeline(tl)
