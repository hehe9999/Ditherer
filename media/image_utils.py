# Third-party imports
from PIL import Image

def load_image(path):
    return Image.open(path)

def resize_to_fit(image, target_width, target_height):
    image_width, image_height = image.size
    frame_aspect = target_width / target_height
    image_aspect = image_width / image_height

    if image_aspect > frame_aspect:
        new_width = target_width
        new_height = int(target_width / image_aspect)
    else:
        new_height = target_height
        new_width = int(target_height * image_aspect)

    return image.resize((new_width, new_height), Image.Resampling.BILINEAR)