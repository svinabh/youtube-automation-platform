from abc import ABC, abstractmethod
from typing import Dict, Any

from .models import Timeline

class VideoRenderer(ABC):
    """
    Abstract base class for video rendering implementations.
    Ensures that the rendering mechanism is abstracted away from the core logic.
    """

    @abstractmethod
    async def render(self, timeline: Timeline) -> Dict[str, Any]:
        """
        Renders the given timeline into a video file.

        Args:
            timeline: The timeline definition to render.

        Returns:
            A dictionary containing metadata about the rendering process
            (e.g., status, output_path, execution_time).

        Raises:
            Exception: If rendering fails.
        """
        pass
