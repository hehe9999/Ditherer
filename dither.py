# Standard library imports
from functools import lru_cache

import numba
import numpy as np

# Third-party imports
from PIL import Image

# Local imports
from resources import resource_path


# Grayscale conversion function
def apply_grayscale(image):
    return image.convert("L")


# Helper function for Bayer matrix selection from list of predetermined arrays
bayer_matrices = {}
for size in (2, 4, 8, 16):
    bayer_matrices[size] = np.load(resource_path(f"matrices/bayer{size}x{size}.npy"))


# Function for getting a tiled Bayer matrix with caching
@lru_cache(maxsize=4)
def get_tiled_bayer_matrix(matrix_size: int, h: int, w: int) -> np.ndarray:
    bayer = bayer_matrices.get(matrix_size, bayer_matrices[2])
    tiled = np.tile(bayer, (-(-h // matrix_size), -(-w // matrix_size)))
    return tiled[:h, :w]


# Numba JIT compiled Bayer Dithering function
@numba.njit
def bayer_dither(image: np.ndarray, threshold_map: np.ndarray) -> np.ndarray:
    h, w = image.shape
    out = np.empty((h, w), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            out[y, x] = 255 if image[y, x] >= threshold_map[y, x] else 0
    return out


# Function for applying Bayer dithering to an image/frame
def apply_bayer_dithering(image: Image.Image, scale_factor: int, matrix_size: int) -> Image.Image:
    width, height = image.size
    downscaled = (
        np.array(
            image.resize((width // scale_factor, height // scale_factor), resample=Image.NEAREST)
        ).astype(np.float32)
        / 255.0
    )

    h, w = downscaled.shape[:2]
    threshold_map = get_tiled_bayer_matrix(matrix_size, h, w)

    if downscaled.ndim == 2:  # Grayscale
        dithered = bayer_dither(downscaled, threshold_map)
    else:  # RGB
        dithered = np.empty_like(downscaled)
        for i in range(3):
            dithered[..., i] = bayer_dither(downscaled[..., i], threshold_map)

    upscaled = Image.fromarray((dithered * 1).astype(np.uint8)).resize(
        (width, height), resample=Image.NEAREST
    )
    return upscaled


# Grayscale Floyd-Steinberg dithering function
@numba.njit(fastmath=True)
def fs_dither_grayscale(dithered, width, height, r, dl, d, dr):
    r_16 = r * 0.0625
    dl_16 = dl * 0.0625
    d_16 = d * 0.0625
    dr_16 = dr * 0.0625

    for y in range(height):
        for x in range(width):
            old_pixel = dithered[y, x]

            new_pixel = np.round(old_pixel * 0.00390625) * 255.0
            error = old_pixel - new_pixel
            dithered[y, x] = new_pixel

            if x < width - 1:
                dithered[y, x + 1] += error * d_16
            if y < height - 1:
                if x > 0:
                    dithered[y + 1, x - 1] += error * dl_16
                dithered[y + 1, x] += error * r_16
                if x < width - 1:
                    dithered[y + 1, x + 1] += error * dr_16

    return dithered


# RGB version of the Floyd-Steinberg dithering function
@numba.njit(fastmath=True)
def fs_dither_rgb(dithered, width, height, channels, r, dl, d, dr):
    r_16 = r * 0.0625
    dl_16 = dl * 0.0625
    d_16 = d * 0.0625
    dr_16 = dr * 0.0625

    for y in range(height):
        for x in range(width):
            for c in range(channels):
                old_pixel = dithered[y, x, c]
                new_pixel = np.round(old_pixel * 0.00390625) * 255.0
                error = old_pixel - new_pixel
                dithered[y, x, c] = new_pixel

                if x < width - 1:
                    dithered[y, x + 1, c] += error * d_16
                if y < height - 1:
                    if x > 0:
                        dithered[y + 1, x - 1, c] += error * dl_16
                    dithered[y + 1, x, c] += error * r_16
                    if x < width - 1:
                        dithered[y + 1, x + 1, c] += error * dr_16

    return dithered


# Floyd-Steinberg dithering applicator function
def fs_dither(image: Image.Image, scale_factor, r, dl, d, dr) -> Image.Image:
    normalized_width, normalized_height = image.size
    small_size = (normalized_width // scale_factor, normalized_height // scale_factor)

    if image.mode == "L":
        dithered = np.array(image.resize(small_size, resample=Image.NEAREST)).astype(np.float32)

        dithered = fs_dither_grayscale(dithered, dithered.shape[1], dithered.shape[0], r, dl, d, dr)
        result = Image.fromarray(np.uint8(np.clip(dithered, 0, 255)))

    elif image.mode == "RGB":
        dithered = np.array(image.resize(small_size, resample=Image.NEAREST)).astype(np.float32)
        dithered = fs_dither_rgb(
            dithered,
            dithered.shape[1],  # width
            dithered.shape[0],  # height
            dithered.shape[2],  # channels
            r,
            dl,
            d,
            dr,
        )
        result = Image.fromarray(np.uint8(np.clip(dithered, 0, 255)))
    else:
        raise ValueError("Image mode must be 'L' or 'RGB'.")

    return result


# Drunk dithering function
def drunk(
    image: Image.Image,
    scale_factor,
    r,
    dl,
    d,
    dr,
    drunkenness_level,
    frames_per_shift=1,
    randomness_enabled=False,
    randomness=1,
    constant_variability=False,
    per_weight=False,
    integer_wrapping=False,
) -> Image.Image:
    # Placeholder for the Drunk dithering algorithm
    # Implement the actual algorithm here
    return image  # Return the original image for now
