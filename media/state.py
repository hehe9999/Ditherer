# Standard library imports
from dataclasses import dataclass

# Third-party imports
import cv2


# Dataclass for holding video information
@dataclass
class MediaState:
    frame_rate: float = 0.0
    is_video: bool = False
    total_frames: int = 0
    cap: cv2.VideoCapture = None
    path: str = ""
