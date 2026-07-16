# Standard library imports
import argparse
import os
import sys
import time

# Local imports
from exporter import export_image, export_video, cancel_export
from media.image_utils import load_image
from media.video_utils import load_video
from media.state import MediaState


# Helper function for cancelling processing
def listen_for_cancel():
    print("Press 'c' then Enter to cancel...")
    while True:
        key = input()
        if key.strip().lower() == "c":
            cancel_export()
            break


# Timer for video ETA
def format_eta(seconds):
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"


def main():
    parser = argparse.ArgumentParser(description="Multimedia Dithering Tool")

    # Required positional arguments
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")

    # General options
    parser.add_argument(
        "--format",
        default="PNG",
        choices=["JPEG", "PNG"],
        help="Image format (default: PNG)",
    )
    parser.add_argument(
        "--algorithm",
        default="Bayer",
        choices=["Floyd-Steinberg", "Bayer"],
        help="Dithering algorithm (default: Bayer)",
    )
    parser.add_argument(
        "--grayscale",
        action="store_true",
        help="Convert media to grayscale before dithering",
    )
    parser.add_argument(
        "--downscale",
        type=int,
        default=2,
        help="Downscale factor for downscaling the image (1-12, default: 2)",
    )
    parser.add_argument(
        "--enable_printing",
        action="store_true",
        help="Enable debug printing (very spammy)",
    )

    # Algorithm-specific options
    parser.add_argument(
        "--matrix_size",
        type=str,
        default="2x2",
        choices=["2x2", "4x4", "8x8", "16x16"],
        help="Matrix size for Bayer dithering (default: 2x2)",
    )
    parser.add_argument(
        "--weights",
        nargs=4,
        type=float,
        default=[7, 5, 3, 1],
        help="Weights for Floyd-Steinberg dithering (default: 7, 5, 3, 1)",
    )

    args = parser.parse_args()

    if args.algorithm.lower() != "bayer" and "--matrix_size" in sys.argv:
        parser.error(
            "The --matrix_size option is only supported with the Bayer algorithm"
        )

    if args.algorithm.lower() != "floyd-steinberg" and "--weights" in sys.argv:
        parser.error(
            "The --weights option is only supported with the Floyd-Steinberg algorithm"
        )

    if args.downscale < 1 or args.downscale > 12:
        parser.error("Downscale factor must be between 1 and 12")

    image_extensions = [".png", ".jpg", ".jpeg"]
    video_extensions = [".mkv", ".mp4", ".webm"]

    if args.input:
        ext = os.path.splitext(args.input)[1]
        if ext in image_extensions:
            loaded_image = load_image(args.input)
            export_image(
                algorithm=args.algorithm,
                matrix_selection=args.matrix_size,
                loaded_image=loaded_image,
                grayscale_enabled=args.grayscale,
                downscale=args.downscale,
                format=args.format,
                fs_weights=args.weights,
                progress_callback=lambda p: print(f"{int(p * 100)}% complete"),
                image_output_path=args.output,
                update_callback=None,
            )
        if ext in video_extensions:
            load_video(args.input)

            # Force output extension to .webm
            original_output = os.path.splitext(args.output)[0]
            output_path = original_output + ".webm"

            # Warn if user tried using a different extension
            if not args.output.lower().endswith(".webm"):
                print(
                    f"Warning: Output file extension changed to '.webm' (was '{os.path.splitext(args.output)[1]}')"
                )

            start_time = time.time()
            export_video(
                algorithm=args.algorithm,
                media_state=MediaState,
                grayscale_enabled=args.grayscale,
                matrix_selection=args.matrix_size,
                downscale=args.downscale,
                fs_weights=args.weights,
                progress_callback=lambda p: print(
                    f"\rProcessing frames: {int(p * 100):3d}% complete | ETA: {format_eta((time.time() - start_time) * (1 - p) / p) if p > 0 else '--:--'}",
                    end="\n" if p >= 1.0 else "",
                    flush=True,
                ),
                video_output_path=output_path,
                update_callback=None,
                enable_printing=args.enable_printing,
            )


if __name__ == "__main__":
    main()
