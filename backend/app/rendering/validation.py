import os
from .models import Timeline

class TimelineValidationError(Exception):
    """Base exception for timeline validation errors."""
    pass

def validate_timeline(timeline: Timeline) -> None:
    """
    Validates the structure and properties of a Timeline object.

    Checks:
    - Scenes exist
    - Element durations do not exceed scene duration
    - Basic checks on output path
    """
    if not timeline.scenes:
        raise TimelineValidationError("Timeline must contain at least one scene.")

    if not timeline.output_path:
        raise TimelineValidationError("Timeline must specify an output path.")

    # In a real environment, we'd probably check if files exist, but for pure structure:
    for scene in timeline.scenes:
        for element in scene.elements:
            if element.start_time + element.duration > scene.duration:
                raise TimelineValidationError(
                    f"Element '{element.id}' duration plus start time exceeds scene '{scene.id}' duration."
                )

    for track in timeline.global_audio_tracks:
        if track.start_time + track.duration > timeline.total_duration:
            raise TimelineValidationError(
                f"Global audio track '{track.id}' extends beyond total timeline duration."
            )
