# Changelog

## v2.0.0 ()

### Added or Changed
- Complete refactoring of the codebase, separating exporting into its own python file and making it GUI agnostic for use with the CLI
- CLI integration, users can now interact with the program directly through the command-line
- Minor optimizations
- Automatic builds using GitHub actions
- Lots of security:
    - Verified binaries with SLSA 3 Provenance, ensures the binary was built in a controlled environment in a reproducible way and is cryptographically tied to the source code
    - SHA256 checksums of the binary, to ensure that the exact binary that was distributed is what the user downloaded
    - GPG signing of the checksum, to ensure that each release is tied directly to my name, and was verified by me before distribution
- requirements.txt has been added to make it easier for compiling from source and interacting through CLI
- [verify.md](/verify.md) has been added to give a tutorial on verifying the binaries using the new security features
- The MediaState class has been put inside its [own file](/media/state.py) alongside [image_utils](/media/image_utils.py) and [video_utils](/media/video_utils.py) to near-completely separate the GUI from logic, also allowing the codebase to be more modular, maintainable, and expandable
- A [dev branch](https://github.com/hehe9999/Ditherer/tree/dev) has been created to be more up-to-date with commits, and to preview the latest features or for anyone to continue development easily on their own
- Cleaned up [dither.py](/dither.py) by moving the pre-generated Bayer matrices to their own .npy files
- Clear labels for imports in each .py file
- Auto-detection of CPU core count to use with FFmpeg
- Changed GUI to be based on customtkinter, modernizing the looks
- GUI is now dark theme
- Fixed progress display in the GUI when processing videos
- Integrated Ruff linting and Black formatting
- Changed all video outputs to be encoded in VP9 and contained inside WebM, allowing for Discord embeds while maintaining a smaller file size than h264
- Changed all video outputs audio to be encoded using opus, saving a small amount of space while maintaining broad compatibility
- Updated the [LICENSE](/LICENSE)
- Added much more documentation to the [README](/README.md), and also expanded its contents to include better explanations, a list of features, a Table of Contents, and badges

## v1.1.0 (5/10/2025)

### Added or Changed
- Massive optimizations to both Floyd-Steinberg and Bayer dithering algorithms, more details in the [todo list](/todo.md)
- Added video support
- Added this changelog
- Updated the [README](/README.md)
- Updated the [todo list](/todo.md)

## v1.0.1 (4/27/2025)

### Added or Changed
- Added 16x16 Bayer matrix
- Improved Bayer matrices, and improved handling of matrix size selection
- Bayer dithering rewritten
- Fixed broken Floyd-Steinberg weights
- Added nested sliders to select Floyd-Steinberg weights
- Updated the [todo list](/todo.md)
- Added labels in the GUI for better readability
- Moved around UI elements

## v1.0.0 (4/25/2025)

### Added or Changed
- Initial fork of the project from https://github.com/MOPHEADART/Ditherer
- Added RGB functionality
- Added a toggle for switching between RGB and Grayscale outputs
- Added .gitignore
- Added the [todo list](/todo.md)
- Updated the [README](/README.md)

### Removed
- Removed reliance on .tk prefix for Tkinter (ex: Frame instead of tk.Frame)
- Removed old unused code from [ditherer.py](/ditherer.py)
- Removed pycache from the repository



