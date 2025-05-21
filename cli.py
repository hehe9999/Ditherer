# Standard library imports
import argparse

# Local imports
from dither import apply_bayer_dithering, apply_grayscale, fs_dither
from media.state import MediaState
from exporter import export_image, export_video


def main():
    parser = argparse.ArgumentParser(description="Multimedia Dithering Tool")

    # Required positional arguments
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")

    # General options
    parser.add_argument("--format", default="PNG", choices=["JPEG","PNG"], help="Image format (default: PNG)")
    parser.add_argument("--algorithm", default="bayer", choices=["floyd-steinberg", "bayer"], help="Dithering algorithm (default: bayer)")
    parser.add_argument("--grayscale", action="store_true", help="Convert media to grayscale before dithering")
    parser.add_argument("--downscale", type=int, default=2, help="Downscale factor for downscaling the image (default: 2)")

    # Algorithm-specific options
    parser.add_argument("--matrix_size", type=str, help="Matrix size for Bayer dithering (default 2x2)")

    args = parser.parse_args()

    if args.algorithm == "bayer"
