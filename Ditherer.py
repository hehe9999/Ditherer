from PIL import Image
import numpy as np

# Define grayscale conversion
def apply_grayscale(image):
    return image.convert('L')

# Define Bayer Dithering with matrix resizing
def bayer_dither(image: np.ndarray, matrix_size) -> np.ndarray:
    normalized_height, normalized_width = image.shape[:2]
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
    bayer_matrix = bayer_matrices.get(matrix_size, bayer_matrices[2])
    dithered = np.zeros((normalized_height, normalized_width), dtype=np.uint8)
    for y in range(normalized_height):
        for x in range(normalized_width):
            threshold = bayer_matrix[y % matrix_size, x % matrix_size]
            value = image[y, x]
            dithered[y, x] = 255 if value >= threshold else 0
    return dithered

def apply_bayer_dithering(image: Image.Image, scale_factor, matrix_size) -> Image.Image:
    width, height = image.size
    downscaled = np.array(image.resize((width // scale_factor, height // scale_factor), resample=Image.BILINEAR)).astype(np.float32) / 255
    # Grayscale input
    if len(downscaled.shape) == 2:
        dithered = bayer_dither(downscaled, matrix_size)
    # RGB input
    else:
        rgb_dithered = np.empty((*downscaled.shape[:2], 3), dtype=np.uint8)
        for i in range(3):
            rgb_dithered[:, :, i] = bayer_dither(downscaled[:, :, i], matrix_size)
        dithered = rgb_dithered
    return Image.fromarray(dithered).resize((width, height), resample=Image.NEAREST)

def fs_dither(image: Image.Image, scale_factor, r, dl, d, dr) -> Image.Image:
    if image.mode == 'L':
        normalized_width, normalized_height = image.size
        dithered = np.array(image.resize((normalized_width // scale_factor, normalized_height // scale_factor), resample=Image.BILINEAR)).astype('float')
        width, height = dithered.shape
    elif image.mode == 'RGB':
        normalized_width, normalized_height = image.size
        dithered = np.array(image.resize((normalized_width // scale_factor, normalized_height // scale_factor), resample=Image.BILINEAR)).astype('float')
        width, height, channels = dithered.shape

    def adjust(dithered, x, y, channel=None):
        old_pixel = dithered[x][y].copy()
        new_pixel = np.round(old_pixel / 256) * 255
        dithered[x][y] = new_pixel
        error = old_pixel - new_pixel
        if x < width - 1:
            dithered[x + 1][y] += error * d / 16
        if y < height - 1 and x > 0:
            dithered[x - 1][y + 1] += error * dl / 16
        if y < height - 1:
            dithered[x][y + 1] += error * r / 16
        if x < width - 1 and y < height - 1:
            dithered[x + 1][y + 1] += error * dr / 16
        return dithered
    
    if image.mode == 'L':
        for y in range(height):
            for x in range(width):
                image = adjust(dithered, x, y)
    elif image.mode == 'RGB':
        for c in range(channels):
            for y in range(height):
                for x in range(width):
                    image = adjust(dithered, x, y, c)
    return Image.fromarray(np.uint8(np.clip(image, 0, 255))).resize((normalized_width, normalized_height), Image.NEAREST)