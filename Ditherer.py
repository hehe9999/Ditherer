from PIL import Image
import numpy as np
import numba
from functools import lru_cache


# Define grayscale conversion
def apply_grayscale(image):
    return image.convert('L')

# Predefined Bayer matrices
bayer_matrices = {
    2: np.array([[0, 2],
                [3, 1]]) / 4,
    4: np.array([[0, 8, 2, 10],
                [12, 4, 14, 6],
                [ 3, 11, 1, 9],
                [15, 7, 13, 5]]) / 16,
    8: np.array([[0, 48, 12, 60, 3, 51, 15, 63],
                [32, 16, 44, 28, 35, 19, 47, 31],
                [8, 56, 4, 52, 11, 59, 7, 55],
                [40, 24, 36, 20, 43, 27, 39, 23],
                [2, 50, 14, 62, 1, 49, 13, 61],
                [34, 18, 46, 30, 33, 17, 45, 29],
                [10, 58, 6, 54, 9, 57, 5, 53],
                [42, 26, 38, 22, 41, 25, 37, 21]]) / 64,
    16: np.array([[0, 128, 32, 160, 8, 136, 40, 168, 2, 130, 34, 162, 10, 138, 42, 170],
                [192, 64, 224, 96, 200, 72, 232, 104, 194, 66, 226, 98, 202, 74, 234, 106],
                [48, 176, 16, 144, 56, 184, 24, 152, 50, 178, 18, 146, 58, 186, 26, 154],
                [240, 112, 208, 80, 248, 120, 216, 88, 242, 114, 210, 82, 250, 122, 218, 90],
                [12, 140, 44, 172, 4, 132, 36, 164, 14, 142, 46, 174, 6, 134, 38, 166],
                [204, 76, 236, 108, 196, 68, 228, 100, 206, 78, 238, 110, 198, 70, 230, 102],
                [60, 188, 28, 156, 52, 180, 20, 148, 62, 190, 30, 158, 54, 182, 22, 150],
                [252, 124, 220, 92, 244, 116, 212, 84, 254, 126, 222, 94, 246, 118, 214, 86],
                [3, 131, 35, 163, 11, 139, 43, 171, 1, 129, 33, 161, 9, 137, 41, 169],
                [195, 67, 227, 99, 203, 75, 235, 107, 193, 65, 225, 97, 201, 73, 233, 105],
                [51, 179, 19, 147, 59, 187, 27, 155, 49, 177, 17, 145, 57, 185, 25, 153],
                [243, 115, 211, 83, 251, 123, 219, 91, 241, 113, 209, 81, 249, 121, 217, 89],
                [15, 143, 47, 175, 7, 135, 39, 167, 13, 141, 45, 173, 5, 133, 37, 165],
                [207, 79, 239, 111, 199, 71, 231, 103, 205, 77, 237, 109, 197, 69, 229, 101],
                [63, 191, 31, 159, 55, 183, 23, 151, 61, 189, 29, 157, 53, 181, 21, 149],
                [255, 127, 223, 95, 247, 119, 215, 87, 253, 125, 221, 93, 245, 117, 213, 85]]) / 256
}
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


def apply_bayer_dithering(image: Image.Image, scale_factor: int, matrix_size: int) -> Image.Image:
    width, height = image.size
    downscaled = np.array(
        image.resize((width // scale_factor, height // scale_factor), resample=Image.NEAREST)
    ).astype(np.float32) / 255.0

    h, w = downscaled.shape[:2]
    threshold_map = get_tiled_bayer_matrix(matrix_size, h, w)

    if downscaled.ndim == 2:  # Grayscale
        dithered = bayer_dither(downscaled, threshold_map)
    else:  # RGB
        dithered = np.empty_like(downscaled)
        for i in range(3):
            dithered[..., i] = bayer_dither(downscaled[..., i], threshold_map)

    upscaled = Image.fromarray((dithered * 1).astype(np.uint8)).resize((width, height), resample=Image.NEAREST)
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

    if image.mode == 'L':
        dithered = np.array(image.resize(small_size, resample=Image.NEAREST)).astype(np.float32)
        dithered = fs_dither_grayscale(dithered, dithered.shape[0], dithered.shape[1], r, dl, d, dr)
        result = Image.fromarray(np.uint8(np.clip(dithered, 0, 255)))
    elif image.mode == 'RGB':
        dithered = np.array(image.resize(small_size, resample=Image.NEAREST)).astype(np.float32)
        dithered = fs_dither_rgb(dithered, dithered.shape[0], dithered.shape[1], dithered.shape[2], r, dl, d, dr)
        result = Image.fromarray(np.uint8(np.clip(dithered, 0, 255)))
    else:
        raise ValueError("Image mode must be 'L' or 'RGB'.")

    return result.resize((normalized_width, normalized_height), Image.NEAREST)