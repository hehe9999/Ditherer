# Third-party imports
import cv2

# Local imports
from media.state import media_state


# Function for loading video files and updating the media_state
def load_video(path):
    # Release any previously open capture (e.g. loading a new video) so we
    # don't leak VideoCapture handles.
    media_state.reset()
    media_state.path = path
    media_state.cap = cv2.VideoCapture(path)
    if not media_state.cap or not media_state.cap.isOpened():
        raise ValueError("Unable to open video file")
    media_state.is_video = True
    media_state.frame_rate = media_state.cap.get(cv2.CAP_PROP_FPS)
    media_state.total_frames = int(media_state.cap.get(cv2.CAP_PROP_FRAME_COUNT))
