# Standard library imports
from dataclasses import dataclass
import typing

# Third-party imports
import cv2


# Dataclass for holding video information
@dataclass
class MediaState:
    frame_rate: float = 0.0
    total_frames: int = 0
    cap: cv2.VideoCapture = None
    path: str = ""

    _is_video: bool = False

    on_video_state_change: typing.Callable[[], None] = None

    @property
    def is_video(self) -> bool:
        return self._is_video

    @is_video.setter
    def is_video(self, value: bool):
        if self._is_video != value:
            self._is_video = value
            if self.on_video_state_change:
                self.on_video_state_change()


media_state = MediaState()
