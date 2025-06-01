# Standard library imports
import os
import math
import time
import tempfile
import shutil
import subprocess
import multiprocessing

# Third-party imports
import cv2
from PIL import Image

# Local imports
from dither import fs_dither, apply_bayer_dithering, apply_grayscale

# Helper function for grabbing Bayer matrices
def get_matrix_size(selection: str):
    matrix_sizes = {"2x2": 2, "4x4": 4, "8x8": 8, "16x16": 16}
    return matrix_sizes.get(selection)


# Main export function for images
def export_image(
    algorithm, # user algorithm selection
    matrix_selection, # Bayer matrix size
    loaded_image, # input image
    grayscale_enabled, # grayscale toggle
    downscale, # downscale factor
    format, # output format
    fs_weights, # Floyd-Steinberg weights
    progress_callback, # progress callback
    image_output_path, # output path for image
    update_callback=None, # update callback function (if GUI is used)
):
    if loaded_image is None: # check if image is loaded
        print("No image loaded")
        return
    
    progress_callback(10 / 100)

    if grayscale_enabled: # convert to grayscale before checking dithering algorithm
        loaded_image = apply_grayscale(loaded_image)

    progress_callback(30 / 100)

    # Apply the selected algorithm
    if algorithm == "Bayer":
        matrix_size = get_matrix_size(matrix_selection)
        dithered = apply_bayer_dithering(loaded_image, downscale, matrix_size)

    elif algorithm == "Floyd-Steinberg":
        dithered = fs_dither(loaded_image, downscale, *fs_weights)
    
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    progress_callback(50 / 100)

    if image_output_path: # check that output path actually exists
        dithered.save(image_output_path, format=format)
    else:
        print("No output path provided. Image was not saved.")

    progress_callback(100 / 100)
    print(f"Finished! Output: {image_output_path}")

    # Update the GUI (if function was called from GUI)
    if callable(update_callback):
        update_callback()


# Main export function for videos
def export_video(
    algorithm, # user algorithm selection
    media_state, # MediaState class
    grayscale_enabled, # grayscale toggle
    matrix_selection, # Bayer matrix size
    downscale, # downscale factor
    fs_weights, # Floyd-Steinberg weights
    progress_callback, # progress callback
    video_output_path, # output path for video
    update_callback=None, # update callback function (if GUI is used)
    enable_printing=None, # toggle to enable extra debug printing
):

    if video_output_path: # check that output path actually exists
        fps = media_state.frame_rate

        # Create temporary directory for compressed frames
        temp_dir = tempfile.mkdtemp()

        if enable_printing:
            print(f"Temporary directory created: {temp_dir}")
        frame_count = 0

        # Reset video capture position
        media_state.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = media_state.cap.read()

        # Start measuring time
        total_start_time = time.time()

        while ret: # loop through frames
            if enable_printing:
                # Start timing frame processing
                frame_start_time = time.time()

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(rgb_frame)

            # Apply grayscale before dithering
            if grayscale_enabled:
                img_pil = apply_grayscale(img_pil)
                img_pil = img_pil.convert("RGB")

            # Apply dithering
            if algorithm == "Bayer":
                matrix_size = get_matrix_size(matrix_selection)
                dithered = apply_bayer_dithering(img_pil, downscale, matrix_size)

            elif algorithm == "Floyd-Steinberg":
                    dithered = fs_dither(img_pil, downscale, *fs_weights)

            # Save frame as compressed PNG
            frame_path = os.path.join(temp_dir, f"frame_{frame_count:04d}.png")
            dithered.save(frame_path, format="PNG", optimize=True)

            # Update frame count and progress callback
            frame_count += 1
            progress_callback(frame_count / media_state.total_frames)

            # Calculate and print time for this frame
            if enable_printing:
                frame_end_time = time.time()
                frame_process_time = frame_end_time - frame_start_time
                print(
                    f"Frame {frame_count} processed in {frame_process_time:.4f} seconds"
                )

            ret, frame = media_state.cap.read()

        # Total time for processing all frames
        total_end_time = time.time()
        total_process_time = total_end_time - total_start_time
        print(
            f"Total time to process {frame_count} frames: {total_process_time:.4f} seconds"
        )

        # Estimate bitrate using entropy
        def calculate_image_entropy(image):
            grayscale = image.convert("L")
            histogram = grayscale.histogram()
            total = sum(histogram)
            entropy = -sum(
                (count / total) * math.log2(count / total)
                for count in histogram
                if count > 0
            )
            return entropy

        entropy_values = []
        for i in range(min(5, frame_count)):
            img = Image.open(os.path.join(temp_dir, f"frame_{i:04d}.png"))
            entropy_values.append(calculate_image_entropy(img))
        avg_entropy = sum(entropy_values) / len(entropy_values)
        bitrate_kbps = max(
            200,
            int(
                avg_entropy * 400
            ),  # tuneable bitrate scale based on calculated entropy
        )
        bitrate = f"{bitrate_kbps}k"
        print(f"Average entropy: {avg_entropy}")
        print(f"Estimated bitrate: {bitrate}bps")
        num_threads = multiprocessing.cpu_count()

        # Two-pass VP9 encoding with passlogfile
        passlogfile = os.path.join(temp_dir, "ffmpeg2pass")
        null_output = os.path.join(temp_dir, "null.webm")  # dummy first pass output
        # fmt: off
        first_pass = [
            "ffmpeg", "-y",
            "-loglevel", "error",
            "-framerate", str(fps),
            "-i", os.path.join(temp_dir, "frame_%04d.png"),

            # Video codec settings
            "-c:v", "libvpx-vp9",
            "-b:v", bitrate,
            "-pass", "1",
            "-passlogfile", passlogfile,
            "-threads", str(num_threads),

            # Output format
            "-an", "-f", "webm", null_output,
        ]

        second_pass = [
            "ffmpeg", "-y",
            "-loglevel", "error",
            "-stats",
            "-framerate", str(fps),
            "-i", os.path.join(temp_dir, "frame_%04d.png"),
            "-i", media_state.path,
            "-shortest",

            # Video codec settings
            "-c:v", "libvpx-vp9",
            "-b:v", bitrate,
            "-pass", "2",
            "-passlogfile", passlogfile,
            "-deadline", "good",
            "-pix_fmt", "yuv420p",
            "-threads", str(num_threads),

            # Audio settings
            "-c:a", "libopus",
            "-b:a", "100k",

            # Output options
            "-movflags", "faststart",
            video_output_path,
        ]
        # fmt: on

        # Run passes
        print("Running dummy first pass...")
        subprocess.run(first_pass, check=True)

        print(f"Running second pass with {bitrate}bps bitrate...")
        subprocess.run(second_pass, check=True)

        # Cleanup
        for ext in ["log", "log.mbtree"]:
            try:
                os.remove(f"{passlogfile}.{ext}")
            except FileNotFoundError:
                pass
        shutil.rmtree(temp_dir)
        print(f"Finished! Output: {video_output_path}")

        # Update the GUI (if function was called from GUI)
        if callable(update_callback):
            update_callback()
