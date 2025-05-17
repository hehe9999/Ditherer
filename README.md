# A fork of [MOPHEADART's Python-based ditherer](https://github.com/MOPHEADART/Ditherer)
![Python](https://img.shields.io/badge/python-3.13+-blue?logo=python) ![License](https://img.shields.io/github/license/hehe9999/Ditherer) ![SLSA Level 3](https://img.shields.io/badge/SLSA-3-blueviolet?logo=github&logoColor=white) ![Windows Release](https://github.com/hehe9999/Ditherer/actions/workflows/release.yml/badge.svg) ![GPG Signed](https://img.shields.io/badge/Releases-Signed%20with%20GPG-4e8ccf?logo=gnupg&logoColor=white) ![Checksummed](https://img.shields.io/badge/Releases-Checksummed%20(SHA256)-green?logo=files&logoColor=white)
## What is dithering, and why is it useful?
[Dithering](https://en.wikipedia.org/wiki/Dither) (in the context of digital images) is the process of intentionally applying noise to randomize [quantization error](https://en.wikipedia.org/wiki/Quantization_(signal_processing)) and is useful in preventing [color banding](https://en.wikipedia.org/wiki/Colour_banding) in an image. This effect is commonly used in systems with a limited [color palette](https://en.wikipedia.org/wiki/Palette_(computing)), and can create the illusion of [color depth](https://en.wikipedia.org/wiki/Color_depth) due to the way the human eye perceives color.

## What is this project?
This project is a Python-based dithering tool that can be used on a variety of media formats, including images and videos. It is designed to be easy to use and fun to play around with, and it is also a great way to learn about dithering, its uses, and how it works. My main goals with this project are to make something that is user-friendly, fun, and educational. This is also a tool for me to learn about Python, image and video manipulation, and to spend my free time in a fun and rewarding way. If you have any suggestions or feedback, please feel free to reach out!

## Usage
### As a standalone .exe:
1. Download the latest release from the [releases page](https://github.com/hehe9999/Ditherer/releases). (Optional: verify the binary using the guide at [verify.md](/verify.md))
2. Open the `.exe`.
3. Import your media using the button at the top of the app.
4. Choose a dithering algorithm from the dropdown.
5. Adjust the settings for your selected algorithm
6. Export your dithered file using the button/s at the bottom.

### Using the Command Prompt:

### Compiling from source:


---

#### The current supported formats are:
| Media Type | Supported Formats     |
|------------|------------------------|
| Video*      | `.mkv`, `.mp4`, `.webm` |
| Image      | `.png`, `.jpeg`, `.jpg` |

> **For video files, you will need to install [FFmpeg](https://www.ffmpeg.org/), I recommend using [chocolatey](https://chocolatey.org/) to do this. You can do this by running `choco install ffmpeg` in your command prompt after chocolatey is installed.**

> **When processing videos, Bayer dithering is recommended. Floyd-Steinberg outputs are extremely large and often bitrate-starved.**

 All video outputs are encoded in [VP9](https://en.wikipedia.org/wiki/VP9) and use the [WebM](https://en.wikipedia.org/wiki/WebM) container - this ensures compatibility with Discord embeds and keeps file sizes manageable.

---

### Verified Builds with SLSA
This project uses [SLSA 3 Provenance](https://slsa.dev) for secure builds. Each release is automatically built by GitHub Actions and includes a provenance file to verify the binary came from this source code and was not tampered with.

You can verify the `.exe` binary using tools like `slsa-verifier` or the [Sigstore tooling](https://docs.sigstore.dev/).

### Verifying the binary
For detailed steps on verifying the binary please refer to [verify.md](/verify.md).

---

**To see the newest additions to the program, check out the [changelog](/changelog.md).**

**To see what I'm currently working on, and what I have planned for the future of this project, check the [todo list](/todo.md).**

### Please check out the [original repository](https://github.com/MOPHEADART/Ditherer)!

# Made with ♡ by hehe
