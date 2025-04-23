from PIL import Image
import os
import numpy as np

# Define Bayer 2x2 Matrix Dithering
def bayer_dither(data: np.ndarray) -> np.ndarray:
    normalized_height, normalized_width = data.shape[:2]
    bayer_matrix = np.array([[0.0, 0.5], [0.75, 0.25]])

    dithered = np.zeros((normalized_height, normalized_width), dtype=np.uint8)
    for y in range(normalized_height):
        for x in range(normalized_width):
            threshold = bayer_matrix[y % 2, x % 2]
            value = data[y, x]
            dithered[y, x] = 255 if value >= threshold else 0
    return dithered

    # Downscale image and normalize values
def apply_bayer_dithering(image: Image.Image, scale_factor: int=2) -> Image.Image:
    width, height = image.size
    downscaled = np.array(image.convert("L").resize((width // scale_factor, height // scale_factor), resample=Image.BILINEAR)).astype(np.float32) / 255.0
    dithered = bayer_dither(downscaled)
    return Image.fromarray(dithered, mode="L").resize((width, height), resample=Image.NEAREST)

    # Downscale image and normalize values
def apply_rgbbayer_dithering(image: Image.Image, scale_factor: int=2) -> Image.Image:
    width, height = image.size
    downscaled = [np.array(channel).astype(np.float32)/255.0 for channel in image.resize((width // scale_factor, height // scale_factor), resample=Image.BILINEAR).split()]

    # Dither color channels
    r_dithered = bayer_dither(downscaled[0])
    g_dithered = bayer_dither(downscaled[1])
    b_dithered = bayer_dither(downscaled[2])

     # Merge dithered channels and upscale image
    merged_channels = Image.merge("RGB", (Image.fromarray(r_dithered), Image.fromarray(g_dithered), Image.fromarray(b_dithered)))
    return merged_channels.resize((width, height), resample=Image.NEAREST)