# Standard library imports
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional

# Third-party imports
import cv2


@dataclass
class MediaState:
    """Shared state for the currently loaded media.

    A single module-level instance (``media_state``) is used by the importer,
    the exporter, and the GUI. ``is_video`` is a managed property: assigning it
    fires ``on_video_state_change`` so the GUI can react to media swaps.
    """

    frame_rate: float = 0.0
    total_frames: int = 0
    cap: Optional["cv2.VideoCapture"] = None
    path: str = ""
    _is_video: bool = False
    on_video_state_change: Callable[[], None] | None = None

    @property
    def is_video(self) -> bool:
        return self._is_video

    @is_video.setter
    def is_video(self, value: bool) -> None:
        if self._is_video != value:
            self._is_video = value
            if self.on_video_state_change is not None:
                self.on_video_state_change()

    def reset(self) -> None:
        """Release any open capture and clear media-specific state.

        Does not touch ``is_video``; callers set it after reset so the change
        callback fires exactly once.
        """
        if self.cap is not None:
            self.cap.release()
        self.cap = None
        self.path = ""
        self.frame_rate = 0.0
        self.total_frames = 0


media_state = MediaState()
