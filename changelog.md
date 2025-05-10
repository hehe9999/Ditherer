# Changelog

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



