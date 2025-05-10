# A fork of [MOPHEADART's Python-based ditherer](https://github.com/MOPHEADART/Ditherer)

## What is dithering, and why is it useful?
[Dithering](https://en.wikipedia.org/wiki/Dither) (in the context of digital images) is the process of intentionally applying noise to randomize [quantization error](https://en.wikipedia.org/wiki/Quantization_(signal_processing)) and is useful in preventing [color banding](https://en.wikipedia.org/wiki/Colour_banding) in an image. This effect is commonly used in systems with a limited [color palette](https://en.wikipedia.org/wiki/Palette_(computing)), and can create the illusion of [color depth](https://en.wikipedia.org/wiki/Color_depth) due to the way the human eye perceives color.

## What is this project?
This project is a Python-based dithering tool that can be used on a variety of media formats, including images and videos. It is designed to be easy to use and fun to play around with, and it is also a great way to learn about dithering, its uses, and how it works. My main goals with this project are to make something that is user-friendly, fun, and educational. This is also a tool for me to learn about Python, image and video manipulation, and to spend my free time in a fun and rewarding way. If you have any suggestions or feedback, please feel free to reach out!

## Usage
To get started, download the latest release from the [releases page](https://github.com/hehe9999/Ditherer/releases). Once you have downloaded the latest release, extract it to a folder of your choice, then open the 'Ditherer.exe' file. Once inside the program, you can import media files at the top, then select a dithering algorithm from the drop-down menu. From here, you can play around with the options for your selected algorithm and then click the export button at the bottom to save your file. 

---

The current supported formats are:
| Media Type | Supported Formats     |
|------------|------------------------|
| Video*      | `.mkv`, `.mp4`, `.webm` |
| Image      | `.png`, `.jpeg`, `.jpg` |

* For video files, you will need to install [FFmpeg](https://www.ffmpeg.org/), I recommend using [chocolatey](https://chocolatey.org/) to do this. You can do this by running `choco install ffmpeg` in your command prompt after chocolatey is installed.


---

**To see the newest additions to the program, check out the [changelog](/changelog.md).**

**To see what I'm currently working on, check the [todo list](/todo.md).**

### Please check out the [original repository](https://github.com/MOPHEADART/Ditherer)!

# Made with ♡ by hehe
