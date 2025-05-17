# Standard library imports
from dataclasses import dataclass

# Third-party imports
import cv2

@dataclass
class MediaState:
    extension: str = ""
    frame_rate: float = 0.0
    is_video: bool = False
    total_frames: int = 0
    cap: cv2.VideoCapture = None
    path: str = ""