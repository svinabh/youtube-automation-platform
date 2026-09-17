import pytest
from pydantic import ValidationError

from app.rendering.models import Resolution, MediaElement, MediaType, Scene, Timeline

def test_resolution_creation():
    res = Resolution(width=1920, height=1080)
    assert res.width == 1920
    assert res.height == 1080

def test_resolution_invalid():
    with pytest.raises(ValidationError):
        Resolution(width=0, height=1080)

def test_media_element_creation():
    elem = MediaElement(
        id="el1",
        media_type=MediaType.VIDEO,
        file_path="/tmp/vid.mp4",
        duration=10.5
    )
    assert elem.id == "el1"
    assert elem.media_type == MediaType.VIDEO
    assert elem.duration == 10.5
    assert elem.start_time == 0.0

def test_scene_creation():
    elem = MediaElement(
        id="el1",
        media_type=MediaType.VIDEO,
        file_path="/tmp/vid.mp4",
        duration=10.0
    )
    scene = Scene(id="s1", elements=[elem], duration=15.0)
    assert scene.id == "s1"
    assert len(scene.elements) == 1
    assert scene.duration == 15.0

def test_timeline_total_duration():
    s1 = Scene(id="s1", elements=[], duration=10.0)
    s2 = Scene(id="s2", elements=[], duration=20.0)

    tl = Timeline(
        id="tl1",
        resolution=Resolution(width=1920, height=1080),
        scenes=[s1, s2],
        output_path="/tmp/out.mp4"
    )

    assert tl.total_duration == 30.0
