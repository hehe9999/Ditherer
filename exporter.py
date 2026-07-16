# Standard library imports
import os
import subprocess
import tempfile
import time
from threading import Event

# Third-party imports
import cv2
from PIL import Image

# Local imports
from dither import apply_bayer_dithering, apply_grayscale, drunk, fs_dither


# Helper function for grabbing Bayer matrices
def get_matrix_size(selection: str):
    matrix_sizes = {"2x2": 2, "4x4": 4, "8x8": 8, "16x16": 16}
    return matrix_sizes.get(selection)


# Cancel flag to stop export process
cancel_flag = Event()


# Cancel functions
def cancel_export():
    cancel_flag.set()


def reset_cancel_flag():
    cancel_flag.clear()


def check_cancel():
    if cancel_flag.is_set():
        reset_cancel_flag()
        raise RuntimeError("Export cancelled.")


# Main export function for images
def export_image(
    algorithm,  # user algorithm selection
    matrix_selection,  # Bayer matrix size
    loaded_image,  # input image
    grayscale_enabled,  # grayscale toggle
    downscale,  # downscale factor
    format,  # output format
    fs_weights,  # Floyd-Steinberg weights
    progress_callback,  # progress callback
    image_output_path,  # output path for image
    update_callback=None,  # update callback function (if GUI is used)
):
    if loaded_image is None:  # check if image is loaded
        print("No image loaded")
        return

    progress_callback(10 / 100)

    if grayscale_enabled:  # convert to grayscale before checking dithering algorithm
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

    if image_output_path:  # check that output path actually exists
        dithered.save(image_output_path, format=format)
    else:
        print("No output path provided. Image was not saved.")

    progress_callback(100 / 100)
    print(f"Finished! Output: {image_output_path}")

    # Update the GUI (if function was called from GUI)
    if callable(update_callback):
        update_callback()


def export_video(
    algorithm,
    media_state,
    drunkenness_level,
    grayscale_enabled,
    matrix_selection,
    downscale,
    fs_weights,
    progress_callback,
    video_output_path,
    encoder="H.264 (mp4)",  # GUI encoder choice: "VP9 (webm)" or "H.264 (mp4)"
    size_constraint_mb=0,  # GUI size cap in MB (0 = no hard cap)
    drunk_settings=None,  # GUI extra Drunk-mode controls (dict) or None
    update_callback=None,
    enable_printing=None,
):
    if video_output_path:
        fps = media_state.frame_rate
        total_frames = media_state.total_frames
        duration_secs = total_frames / fps

        # Reset video capture position and read the FIRST frame
        media_state.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = media_state.cap.read()

        if not ret:
            print("Error: Could not read the first frame.")
            return

        # Dither one BGR frame into an RGB PIL image. Shared by the first-frame
        # size probe and the encode loop so the two can never disagree.
        def render(bgr_frame):
            img = Image.fromarray(cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB))
            if grayscale_enabled:
                img = apply_grayscale(img).convert("RGB")
            if algorithm == "Bayer":
                out = apply_bayer_dithering(img, downscale, get_matrix_size(matrix_selection))
            elif algorithm == "Floyd-Steinberg":
                out = fs_dither(img, downscale, *fs_weights)
            elif algorithm == "Drunk":
                out = drunk(
                    img,
                    downscale,
                    *fs_weights,
                    drunkenness_level=drunkenness_level,
                    **(drunk_settings or {}),
                )
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            return out if out.mode == "RGB" else out.convert("RGB")

        # Measure the ACTUAL dithered size from the first frame rather than
        # assuming orig/downscale: fs_dither returns the downscaled size while
        # Bayer/Drunk return full size, so a fixed guess corrupts the raw pipe.
        first_frame = render(frame)
        dither_width, dither_height = first_frame.size

        # --- RATE CONTROL -------------------------------------------------
        # Dithered / error-diffused frames carry heavy high-frequency detail
        # that blocks badly when starved. A user size cap uses 2-pass ABR to
        # hit that size; otherwise we use constant quality (CRF) so each frame
        # keeps the bitrate it needs, capped by a sane ceiling.
        audio_kbps = 100
        bitrate_bounded = bool(size_constraint_mb and size_constraint_mb > 0)

        if bitrate_bounded:
            target_size_bytes = size_constraint_mb * 1024 * 1024
            print(
                f"Size Constraint: Targeting under {size_constraint_mb}MB over {duration_secs:.2f}s"
            )
            target_kbps = max(
                100, int((target_size_bytes * 8) / (duration_secs * 1000) - audio_kbps)
            )
        else:
            print("Quality Mode: Constant quality (CRF)")
            target_kbps = 16000  # ceiling for the CRF maxrate

        maxrate_kbps = int(target_kbps * 1.45)
        bufsize_kbps = int(target_kbps * 2.0)

        # Codec, audio codec, CRF and quality tuning per encoder choice.
        # CRF is a fixed high-quality default; use the size cap to trade size.
        if encoder == "VP9 (webm)":
            final_vcodec, final_acodec = "libvpx-vp9", "libopus"
            crf = "28"
            quality_flags = [
                "-row-mt",
                "1",
                "-tile-columns",
                "2",
                "-aq-mode",
                "2",
                "-quality",
                "good",
                "-cpu-used",
                "1",
            ]
        else:  # H.264 (mp4)
            final_vcodec, final_acodec = "libx264", "aac"
            crf = "18"
            # 'grain' tune relaxes deblocking and boosts psychovisual rate-
            # distortion so the dither pattern survives; adaptive quantization
            # pushes bits into the busiest, most block-prone regions.
            quality_flags = ["-tune", "grain", "-aq-mode", "3", "-aq-strength", "1.0"]

        # Define temporary file names (kept out of the project dir so the
        # working directory stays clean and exports work from any CWD).
        temp_dir = tempfile.gettempdir()
        temp_intermediate = os.path.join(temp_dir, "ditherer_intermediate.mp4")
        pass_log_prefix = os.path.join(temp_dir, "ditherer_2pass_log")

        # --- STEP 1: EXPORT HIGH-SPEED, NEAR-LOSSLESS INTERMEDIATE ---
        # Python writes directly to this. 'ultrafast' + crf 0 keeps the dither
        # bit-exact so the quality-focused final pass has pristine source.
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{dither_width}x{dither_height}",
            "-r",
            str(fps),
            "-i",
            "-",
            # Pull original audio directly from source video
            "-i",
            media_state.path,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            # High-speed, mathematically lossless intermediate
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-qp",
            "0",  # lossless: no dither loss before final pass
            "-pix_fmt",
            "yuv444p",  # no chroma subsampling on the dither yet
            "-c:a",
            "copy",  # copy audio raw to avoid double-encoding
            temp_intermediate,
        ]

        # Start the FFmpeg subprocess
        ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        try:
            frame_count = 0
            total_start_time = time.time()

            while ret:
                check_cancel()

                if enable_printing:
                    frame_start_time = time.time()

                # Reuse the already-rendered first frame, then render the rest.
                dithered = first_frame if frame_count == 0 else render(frame)

                # Pipe raw bytes directly to the intermediate FFmpeg process
                ffmpeg_process.stdin.write(dithered.tobytes())

                frame_count += 1
                progress_callback(
                    (frame_count / media_state.total_frames) * 0.70
                )  # 70% of progress is Python processing

                if enable_printing:
                    frame_end_time = time.time()
                    print(
                        f"Frame {frame_count} processed in {frame_end_time - frame_start_time:.4f}s"
                    )

                ret, frame = media_state.cap.read()

        finally:
            # Safely close python stream and wait for intermediate to compile
            if ffmpeg_process.stdin:
                ffmpeg_process.stdin.close()
            ffmpeg_process.wait()

        # --- STEP 2: FINAL ENCODE ---
        null_output = "NUL" if os.name == "nt" else "/dev/null"

        if bitrate_bounded:
            # Size-constrained: 2-pass ABR to precisely hit the target size,
            # with a generous VBV so busy dithered frames can spike instead of
            # blocking. maxrate/bufsize give the encoder headroom.
            print("\nRunning 2-Pass Optimization (bitrate-bounded)...")
            rate_flags = [
                "-b:v",
                f"{target_kbps}k",
                "-maxrate",
                f"{maxrate_kbps}k",
                "-bufsize",
                f"{bufsize_kbps}k",
            ]

            pass1_cmd = [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                temp_intermediate,
                "-c:v",
                final_vcodec,
                "-preset",
                "slow",
                *rate_flags,
                *quality_flags,
                "-pass",
                "1",
                "-passlogfile",
                pass_log_prefix,
                "-an",
                "-f",
                "webm" if final_vcodec == "libvpx-vp9" else "mp4",
                null_output,
            ]
            progress_callback(0.85)
            subprocess.run(pass1_cmd)

            pass2_cmd = [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                temp_intermediate,
                "-c:v",
                final_vcodec,
                "-preset",
                "slow",
                *rate_flags,
                *quality_flags,
                "-pass",
                "2",
                "-passlogfile",
                pass_log_prefix,
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                final_acodec,
                "-b:a",
                "128k",
                "-movflags",
                "faststart",
                video_output_path,
            ]
            subprocess.run(pass2_cmd)
        else:
            # Unbounded: single-pass constant quality. Each frame gets exactly
            # the bitrate its detail needs (best dither preservation). x264 caps
            # runaway frames with maxrate; VP9 constant-quality uses -b:v 0 and
            # rejects maxrate/bufsize, so it runs pure CQ.
            print("\nRunning constant-quality encode...")
            if final_vcodec == "libvpx-vp9":
                rate_flags = ["-b:v", "0", "-crf", crf]
            else:
                rate_flags = [
                    "-crf",
                    crf,
                    "-maxrate",
                    f"{maxrate_kbps}k",
                    "-bufsize",
                    f"{bufsize_kbps}k",
                ]

            encode_cmd = [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                temp_intermediate,
                "-c:v",
                final_vcodec,
                "-preset",
                "slow",
                *rate_flags,
                *quality_flags,
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                final_acodec,
                "-b:a",
                "128k",
                "-movflags",
                "faststart",
                video_output_path,
            ]
            progress_callback(0.85)
            subprocess.run(encode_cmd)

        progress_callback(1.0)  # Finish progress

        # --- STEP 3: CLEAN UP COMPILATION ARTIFACTS ---
        if os.path.exists(temp_intermediate):
            os.remove(temp_intermediate)

        # Clean up 2-pass log files
        for ext in [".log", ".log.mbtree", "-0.log", "-0.log.mbtree"]:
            log_file = f"{pass_log_prefix}{ext}"
            if os.path.exists(log_file):
                os.remove(log_file)

        total_process_time = time.time() - total_start_time
        print(f"Finished! Total pipeline time: {total_process_time:.2f}s")
        print(f"Optimized Video Output: {video_output_path}")

        # Update GUI if callback is registered
        if callable(update_callback):
            update_callback()
