# Todo List:
- [ ] Add "Reset Weights" button for Floyd-Steinberg weights
- [ ] Add Atkinson dithering
- [ ] Add "Randomize" button for Floyd-Steinberg weights
- [ ] Add live preview
- [ ] Add processing time display (ex: Image took 5.92s to process!)
- [ ] Add filter effects (ex: blur, sharpen, crt, etc. could be done standalone or with dithering)
- [ ] GIF support
- [ ] Add controls for palette size/bits per color
- [ ] Add cancel button for processing
- [ ] Add example images/videos to README.md to more clearly explain the use of the software
- [ ] Run export function on a separate thread so the UI doesn't freeze
- [ ] Clean up Ditherer_gui.py for better readability
- [ ] Drag and drop functionality
- [ ] Optimize optimize optimize!
- [ ] Discord webhook integration



# Challenges for the future:
- [ ] Add audio dithering options to separated audio or audio files by themself
- [ ] Multiprocessing
- [ ] Live video support (dithering your camera feed?)
- [ ] Link support (ex: link to a youtube video and dither it)
- [ ] Multiple files support (dither multiple files at once?)
- [ ] Presets for options
- [ ] Ability to change FFmpeg command line arguments (unlikely due to file sizes but interesting)
- [ ] Output file size estimation?



# Fun ideas
- [ ] Add a "Drunk mode" that changes dithering algorithms randomly per frame of a video
- [ ] More randomization options than just the weights (ex: randomize palette, randomize dithering algorithms, etc.)
- [ ] Add an "Ascii mode" to convert images/frames into ascii art (dither afterwards? font options?)



# Completed
- [x] Create exporter.py to handle all exporting functions, leaving Ditherer_gui.py to solely handle the gui and allow for CLI and discord bot operations
- [x] Add a changelog
- [x] Improve progress bar display
- [x] Handle input modes that aren't 'L' or 'RGB'
- [x] Add 16x16 Bayer matrix
- [x] Improve handling of Bayer matrix size selection
- [x] Add nested sliders for changing Floyd-Steinberg dithering weights
- [x] Add video handling with audio separation and merging when exporting
- [x] Vectorize Bayer Dithering function (5x-10x speedup)
- [x] Cache tiled Bayer matrix using lru_cache so it can be reused (negligible-huge speedup depending on matrix and image size)
- [x] Perform JIT compilation using numba for Floyd-Steinberg dithering function (50x-100x speedup)
- [x] Perform JIT compilation using numba for Bayer Dithering function (2x-10x speedup for large videos)
- [x] Add dev branch for more updated commits
- [x] Beautify UI