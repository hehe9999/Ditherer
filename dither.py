# Standard library imports
from functools import lru_cache

# Third-party imports
from PIL import Image
import numpy as np
import numba


# Define grayscale conversion
def apply_grayscale(image):
    return image.convert("L")


# Predefined Bayer matrices
bayer_matrices = {}
for size in (2, 4, 8, 16):
    bayer_matrices[size] = np.load(f"matrices/bayer{size}x{size}.npy")


# Define Bayer Dithering with matrix resizing
@lru_cache(maxsize=4)
def get_tiled_bayer_matrix(matrix_size: int, h: int, w: int) -> np.ndarray:
    bayer = bayer_matrices.get(matrix_size, bayer_matrices[2])
    tiled = np.tile(bayer, (-(-h // matrix_size), -(-w // matrix_size)))
    return tiled[:h, :w]


# Numba JIT compiled Bayer Dithering
@numba.njit
def bayer_dither(image: np.ndarray, threshold_map: np.ndarray) -> np.ndarray:
    h, w = image.shape
    out = np.empty((h, w), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            out[y, x] = 255 if image[y, x] >= threshold_map[y, x] else 0
    return out


def apply_bayer_dithering(
    image: Image.Image, scale_factor: int, matrix_size: int
) -> Image.Image:
    width, height = image.size
    downscaled = (
        np.array(
            image.resize(
                (width // scale_factor, height // scale_factor), resample=Image.NEAREST
            )
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


# Numba JIT compiled Floyd-Steinberg dithering (grayscale)
@numba.njit
def fs_dither_grayscale(dithered, width, height, r, dl, d, dr):
    for y in range(height):
        for x in range(width):
            old_pixel = dithered[x, y]
            new_pixel = np.round(old_pixel / 256) * 255
            error = old_pixel - new_pixel
            dithered[x, y] = new_pixel
            if x < width - 1:
                dithered[x + 1, y] += error * d / 16
            if y < height - 1 and x > 0:
                dithered[x - 1, y + 1] += error * dl / 16
            if y < height - 1:
                dithered[x, y + 1] += error * r / 16
            if x < width - 1 and y < height - 1:
                dithered[x + 1, y + 1] += error * dr / 16
    return dithered


# Numba JIT compiled Floyd-Steinberg dithering (rgb)
@numba.njit
def fs_dither_rgb(dithered, width, height, channels, r, dl, d, dr):
    for c in range(channels):
        for y in range(height):
            for x in range(width):
                old_pixel = dithered[x, y, c]
                new_pixel = np.round(old_pixel / 256) * 255
                error = old_pixel - new_pixel
                dithered[x, y, c] = new_pixel
                if x < width - 1:
                    dithered[x + 1, y, c] += error * d / 16
                if y < height - 1 and x > 0:
                    dithered[x - 1, y + 1, c] += error * dl / 16
                if y < height - 1:
                    dithered[x, y + 1, c] += error * r / 16
                if x < width - 1 and y < height - 1:
                    dithered[x + 1, y + 1, c] += error * dr / 16
    return dithered


def fs_dither(image: Image.Image, scale_factor, r, dl, d, dr) -> Image.Image:
    normalized_width, normalized_height = image.size
    small_size = (normalized_width // scale_factor, normalized_height // scale_factor)

    if image.mode == "L":
        dithered = np.array(image.resize(small_size, resample=Image.NEAREST)).astype(
            np.float32
        )
        dithered = fs_dither_grayscale(
            dithered, dithered.shape[0], dithered.shape[1], r, dl, d, dr
        )
        result = Image.fromarray(np.uint8(np.clip(dithered, 0, 255)))
    elif image.mode == "RGB":
        dithered = np.array(image.resize(small_size, resample=Image.NEAREST)).astype(
            np.float32
        )
        dithered = fs_dither_rgb(
            dithered,
            dithered.shape[0],
            dithered.shape[1],
            dithered.shape[2],
            r,
            dl,
            d,
            dr,
        )
        result = Image.fromarray(np.uint8(np.clip(dithered, 0, 255)))
    else:
        raise ValueError("Image mode must be 'L' or 'RGB'.")

    return result.resize((normalized_width, normalized_height), Image.NEAREST)
