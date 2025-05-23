# Third-party imports
import cv2

# Local imports
from media.state import MediaState



def load_video(path):
    MediaState.is_video = True
    MediaState.path = path
    MediaState.cap = cv2.VideoCapture(path)
    if not MediaState.cap or not MediaState.cap.isOpened():
        raise ValueError("Unable to open video file")
    MediaState.frame_rate = MediaState.cap.get(cv2.CAP_PROP_FPS)
    MediaState.total_frames = int(MediaState.cap.get(cv2.CAP_PROP_FRAME_COUNT))
