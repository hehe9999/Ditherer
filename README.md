# Ditherer
![Python](https://img.shields.io/badge/python-3.12+-blue?logo=python) [![License](https://img.shields.io/github/license/hehe9999/Ditherer)](LICENSE) ![SLSA Level 3](https://img.shields.io/badge/SLSA-3-blueviolet?logo=github&logoColor=white) ![Windows Release](https://github.com/hehe9999/Ditherer/actions/workflows/release.yml/badge.svg) ![GPG Signed](https://img.shields.io/badge/Releases-Signed%20with%20GPG-4e8ccf?logo=gnupg&logoColor=white) ![Checksummed](https://img.shields.io/badge/Releases-Checksummed%20(SHA256)-green?logo=files&logoColor=white)

**A fork of [MOPHEADART's Python-based ditherer](https://github.com/MOPHEADART/Ditherer)**

## Table of Contents
- [What is dithering, and why is it useful?](#what-is-dithering-and-why-is-it-useful)
- [What is this project?](#what-is-this-project)
- [Features](#features)
- [Installation and Usage](#usage)
    - [As a standalone .exe](#as-a-standalone-exe)
    - [Using the CLI](#using-the-cli)
    - [Compiling from source](#compiling-from-source)
- [Supported Formats](#the-current-supported-formats-are)
- [SLSA 3](#verified-builds-with-slsa)
- [Verifying the Binary](#verifying-the-binary)
- [License](#license)

## What is dithering, and why is it useful?
[Dithering](https://en.wikipedia.org/wiki/Dither) (in the context of digital images) is the process of intentionally applying noise to randomize [quantization error](https://en.wikipedia.org/wiki/Quantization_(signal_processing)) and is useful in preventing [color banding](https://en.wikipedia.org/wiki/Colour_banding) in an image. This effect is commonly used in systems with a limited [color palette](https://en.wikipedia.org/wiki/Palette_(computing)), and can create the illusion of [color depth](https://en.wikipedia.org/wiki/Color_depth) due to the way the human eye perceives color.

## What is this project?
This project is a Python-based dithering tool that can be used on a variety of media formats, including images and videos. It is designed to be easy to use and fun to play around with, and it is also a great way to learn about dithering, its uses, and how it works. My main goals with this project are to make something that is user-friendly, fun, and educational. This is also a tool for me to learn about Python, image and video manipulation, and to spend my free time in a fun and rewarding way. If you have any suggestions or feedback, please feel free to reach out!

## Features
* Multiple dithering algorithms — **Bayer** (ordered, with selectable matrix sizes), **Floyd-Steinberg** (error diffusion, with adjustable weights), and **Drunk** (error diffusion with extra randomization controls)
* Optional downscaling before dithering
* Grayscale output toggle
* Video encoding with a choice of **H.264 (MP4)** or **VP9 (WebM)** and a target **size constraint**
* CLI and GUI usage

## Usage
### As a standalone .exe:
1. Download the latest release from the [releases page](https://github.com/hehe9999/Ditherer/releases). (Optional: verify the binary using the guide at [docs/verify.md](docs/verify.md))
2. Open the `.exe`.
3. Import your media using the button at the top of the app.
4. Choose a dithering algorithm from the dropdown.
5. Adjust the settings for your selected algorithm
6. Export your dithered file using the button(s) at the bottom.

### Using the CLI:
**To do this, you will need [Python](https://www.python.org/downloads/) 3.12 or higher installed to PATH.**
1. Clone this repo: `git clone https://github.com/hehe9999/Ditherer.git`
2. Open **Command Prompt** in the directory, or navigate to it.
3. Install the `requirements.txt` using `pip`. `pip install -r requirements.txt`
4. Interact with the program by running `py cli.py`, for a list of available commands you can run `py cli.py --help`.

Example usage: `py cli.py testvideo.mp4 testvideo1.mp4 --algorithm "Floyd-Steinberg" --weights -24 5 3 1 --grayscale --downscale 5`
This will process `testvideo.mp4` using the Floyd-Steinberg dithering algorithm at a downscale factor of 5, in grayscale, using the weights -24, 5, 3, 1.

### Compiling from source:
**This is one of many methods that are possible.**
1. Clone this repo: `git clone https://github.com/hehe9999/Ditherer.git`
2. Open **Command Prompt** in the directory, or navigate to it.
3. (Recommended) Create and activate a virtual environment, then install dependencies: `pip install -r requirements.txt`
4. Build the GUI with [PyInstaller](https://pyinstaller.org/): `pyinstaller --onefile --noconsole --name dither gui_qt.py`
   - The GUI loads its Qt layout (`ui.ui`) and Bayer matrices at runtime, so bundle them for a portable build: `--add-data "ui.ui;." --add-data "matrices;matrices"`
5. Run the `dither.exe` located in `\\dist`.

> **The GUI is built with [PySide6](https://doc.qt.io/qtforpython/) (a PyQt-compatible binding).** The old `customtkinter`-based `gui.py` has been retired.



## The current supported formats are:
| Media Type | Supported Formats     |
|------------|------------------------|
| Video*      | `.mkv`, `.mp4`, `.webm` |
| Image      | `.png`, `.jpeg`, `.jpg` |

> **For video files, you will need to install [FFmpeg](https://www.ffmpeg.org/), I recommend using [chocolatey](https://chocolatey.org/) to do this. You can do this by running `choco install ffmpeg` in your command prompt after chocolatey is installed.**

> **Video encoders:** the GUI lets you choose between **H.264 (MP4)** and **VP9 (WebM)**. The **size constraint** field caps the output to a target file size (great for Discord/embed limits) — the encoder adapts its bitrate to fit. The CLI currently always outputs **VP9/WebM**.

> **Dithering detail:** Floyd-Steinberg and Drunk are error-diffusion (high-frequency) algorithms; the exporter uses constant-quality encoding by default and 2-pass rate control when a size constraint is set, so busy frames keep the bitrate they need. Bayer stays crisp at lower bitrates if you want the smallest files.



## Verified Builds with SLSA
This project uses [SLSA 3 Provenance](https://slsa.dev) for secure builds. Each release is automatically built by GitHub Actions and includes a provenance file to verify the binary came from this source code and was not tampered with.

You can verify the `.exe` binary using tools like `slsa-verifier` or the [Sigstore tooling](https://docs.sigstore.dev/).

## Verifying the Binary
For detailed steps on verifying the binary checksum and gpg, please refer to [verify.md](/verify.md).

## License
This project is licensed under the [MIT License](/LICENSE).

---

**To see the newest additions to the program, check out the [changelog](docs/changelog.md).**

**To see what I'm currently working on, and what I have planned for the future of this project, check the [todo list](docs/todo.md).**

### Please check out the [original repository](https://github.com/MOPHEADART/Ditherer)!

# Made with ♡ by hehe
