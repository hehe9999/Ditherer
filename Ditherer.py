from PIL import Image
import numpy as np

# Define grayscale conversion
def apply_grayscale(image):
    return image.convert('L')

# Define Bayer Dithering with matrix resizing
def bayer_dither(image: np.ndarray, matrix_size) -> np.ndarray:
    normalized_height, normalized_width = image.shape[:2]
    if matrix_size == 2:
        bayer_matrix = np.array([[0.0, 0.5],
                                [0.75, 0.25]])
    elif matrix_size == 4:
        bayer_matrix = np.array([[0.0, 0.53125, 0.15625, 0.65625],
                                [0.78125, 0.28125, 0.90625, 0.40625],
                                [0.21875, 0.71875, 0.09375, 0.59375],
                                [0.96875, 0.46875, 0.84375, 0.34375]])
    elif matrix_size == 8:
        bayer_matrix = np.array([[0.00000, 0.75000, 0.18750, 0.93750, 0.04688, 0.79688, 0.23438, 0.98438],
                                [0.50000, 0.25000, 0.68750, 0.43750, 0.54688, 0.29688, 0.73438, 0.48438],
                                [0.12500, 0.87500, 0.06250, 0.81250, 0.17188, 0.92188, 0.10938, 0.85938],
                                [0.62500, 0.37500, 0.56250, 0.31250, 0.67188, 0.42188, 0.60938, 0.35938],
                                [0.03125, 0.78125, 0.21875, 0.96875, 0.01562, 0.76562, 0.20312, 0.95312],
                                [0.53125, 0.28125, 0.71875, 0.46875, 0.51562, 0.26562, 0.70312, 0.45312],
                                [0.15625, 0.90625, 0.09375, 0.84375, 0.14062, 0.89062, 0.07812, 0.82812],
                                [0.65625, 0.40625, 0.59375, 0.34375, 0.64062, 0.39062, 0.57812, 0.32812]])
    dithered = np.zeros((normalized_height, normalized_width), dtype=np.uint8)
    for y in range(normalized_height):
        for x in range(normalized_width):
            threshold = bayer_matrix[y % matrix_size, x % matrix_size]
            value = image[y, x]
            dithered[y, x] = 255 if value >= threshold else 0
    return dithered

# Apply bayer dithering, merge RGB channels, and then upscale back to the original size
def apply_bayer_dithering(image: Image.Image, scale_factor, matrix_size) -> Image.Image:
    # Convert image to NumPy array and downscale by scale_factor
    width, height = image.size 
    downscaled = np.array(image.resize((width // scale_factor, height // scale_factor), resample=Image.BILINEAR)).astype(np.float32) / 255.0
    # Grayscale input
    if len(downscaled.shape) == 2:
        dithered = bayer_dither(downscaled, matrix_size)
        # Return final resized image
        return Image.fromarray(dithered).resize((width, height), resample=Image.NEAREST)
    # RGB input
    else:
        r_dithered = bayer_dither(downscaled[:, :, 0], matrix_size)
        g_dithered = bayer_dither(downscaled[:, :, 1], matrix_size)
        b_dithered = bayer_dither(downscaled[:, :, 2], matrix_size)
        # Combine channels back into single image
        dithered = np.stack((r_dithered, g_dithered, b_dithered), axis=-1)
    # Return final resized image
    return Image.fromarray(dithered).resize((width, height), Image.NEAREST) 

def fs_dither(image: Image.Image, scale_factor) -> Image.Image:
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
            dithered[x + 1][y] += error * 7 / 16
        if x > 0 and y < height - 1:
            dithered[x - 1][y + 1] += error * 3 / 16
        if y < height - 1:
            dithered[x][y + 1] += error * 5 / 16
        if x < width - 1 and y < height - 1:
            dithered[x + 1][y + 1] += error / 16
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