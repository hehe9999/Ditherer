# Standard library imports
import os
import math
import time
import tempfile
import shutil
import subprocess
from tkinter import filedialog

# Third-party imports
import cv2
from PIL import Image

def get_matrix_size(dropdown, dropdown_submenu):
    if dropdown.get() == "Bayer":
        matrix_sizes = {
            "2x2": 2,
            "4x4": 4,
            "8x8": 8,
            "16x16": 16
        }
        matrix_size = matrix_sizes.get(dropdown_submenu.get())
    return matrix_size


def export_image(
    window,
    dropdown,
    dropdown_submenu,
    loaded_image,
    grayscale_enabled,
    downscale,
    format,
    sliders,
    apply_grayscale,
    apply_bayer_dithering,
    fs_dither,
    progress_callback=None
):
    if loaded_image is None:
        print("No image loaded")
        return
    progress_callback(10)

    if dropdown.get() == "Bayer":
        matrix_size = get_matrix_size(dropdown, dropdown_submenu)
        if grayscale_enabled:
            loaded_image = apply_grayscale(loaded_image)
        dithered = apply_bayer_dithering(loaded_image, downscale, matrix_size)

    elif dropdown.get() == "Floyd-Steinberg":
        if grayscale_enabled:
            grayscale = apply_grayscale(loaded_image)
            source_image = grayscale
        else:
            source_image = loaded_image
        progress_callback(30)
        slider_values = [s.get() for s in sliders]
        dithered = fs_dither(
            source_image,
            downscale,
            slider_values[0],
            slider_values[1],
            slider_values[2],
            slider_values[3],
        )

    else:
        raise ValueError(f"Unsupported algorithm: {dropdown.get()}")

    if progress_callback:
        progress_callback(50)

    ext = format.lower()
    file_path = filedialog.asksaveasfilename(
        defaultextension=f".{ext}",
        filetypes=[(f"{format} files", f"*.{ext}")]
    )

    if file_path:
        dithered.save(file_path, format=format)

    progress_callback(100)
    window.update_idletasks

    window.after(500, lambda: progress_callback(0))

def export_video(
    window,
    dropdown,
    dropdown_submenu,
    media_state,
    grayscale_var,
    apply_grayscale,
    apply_bayer_dithering,
    fs_dither,
    downscale,
    sliders,
    progress_callback,

):
    video_output_path = filedialog.asksaveasfilename(
        defaultextension=".webm", filetypes=[("(.webm) files", "*.webm")]
    )

    if video_output_path:
        fps = media_state.frame_rate
        # Create temporary directory for compressed frames
        temp_dir = tempfile.mkdtemp()
        print(temp_dir)
        frame_count = 0

        # Reset video capture position
        media_state.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = media_state.cap.read()

        # Start measuring time
        total_start_time = time.time()

        while ret:
            # Start timing frame processing
            frame_start_time = time.time()

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(rgb_frame)

            # Apply dithering
            if dropdown.get() == "Bayer":
                matrix_size = get_matrix_size(dropdown, dropdown_submenu)
                if grayscale_var.get():
                    grayscale = apply_grayscale(img_pil)
                    dithered = apply_bayer_dithering(
                        grayscale, downscale, matrix_size
                    )
                    dithered = dithered.convert("RGB")
                else:
                    dithered = apply_bayer_dithering(
                        img_pil, downscale, matrix_size
                    )

            elif dropdown.get() == "Floyd-Steinberg":
                slider_values = [slide.get() for slide in sliders]
                if grayscale_var.get():
                    grayscale = apply_grayscale(img_pil)
                    dithered = fs_dither(grayscale, downscale, *slider_values)
                    dithered = dithered.convert("RGB")
                else:
                    dithered = fs_dither(img_pil, downscale, *slider_values)

            # Save frame as compressed PNG
            frame_path = os.path.join(temp_dir, f"frame_{frame_count:04d}.png")
            dithered.save(frame_path, format="PNG", optimize=True)

            frame_count += 1
            progress_callback(int((frame_count / media_state.total_frames) * 100))

            # Calculate and print time for this frame
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
            200, int(avg_entropy * 400)
        )  # tuneable bitrate scale based on calculated entropy
        bitrate = f"{bitrate_kbps}k"
        print(f"Average entropy: {avg_entropy}")
        print(f"Estimated bitrate: {bitrate}")

        # Two-pass VP9 encoding with passlogfile
        passlogfile = os.path.join(temp_dir, "ffmpeg2pass")
        null_output = os.path.join(temp_dir, "null.webm")  # dummy first pass output
        # fmt: off
        first_pass = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", os.path.join(temp_dir, "frame_%04d.png"),

            # Video codec settings
            "-c:v", "libvpx-vp9",
            "-b:v", bitrate,
            "-pass", "1",
            "-passlogfile", passlogfile,

            # Output format
            "-an", "-f", "webm", null_output,
        ]

        second_pass = [
            "ffmpeg", "-y",
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

            # Audio settings
            "-c:a", "libopus",
            "-b:a", "100k",

            # Output options
            "-movflags", "faststart",
            video_output_path,
        ]
        # fmt: on

        # Run passes
        print(f"Running first pass with bitrate {bitrate}...")
        subprocess.run(first_pass, check=True)

        print("Running second pass...")
        subprocess.run(second_pass, check=True)

        # Cleanup
        for ext in ["log", "log.mbtree"]:
            try:
                os.remove(f"{passlogfile}.{ext}")
            except FileNotFoundError:
                pass
        shutil.rmtree(temp_dir)
        window.update_idletasks

        window.after(500, lambda: progress_callback(0))