from tkinter import *
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
from Ditherer import *
from dataclasses import dataclass
import os
import cv2
import subprocess
import tempfile
import shutil
import time
import threading
import math

# Create window
window = Tk()
window.title("Ditherer")
window.geometry("400x600")
window.minsize(400, 600)


# Frames and labels

# Load image button frame
load_button_frame = Frame(window)
load_button_frame.place(relx=0.5, rely=0.05, anchor="center")

# Grayscale checkbox frame
grayscale_frame = Frame(window)
grayscale_frame.place(relx=0.5, rely=0.9, relwidth=0.4, relheight=0.1, anchor="center")

# Algo dropdown frame
dropdown_frame = Frame(window)
dropdown_frame.place(relx=0.5, rely=0.56, relwidth=0.4, relheight=0.05, anchor="center")

# Algo submenu frame
floyd_steinberg_submenu = Frame(window)

submenu_dropdown_frame = Frame(window)


# Export buttons frame
export_frame = Frame(window)
export_frame.place(relx=0.5, rely=0.92, relwidth=0.6, anchor="center")

# Image frame
image_frame = Frame(window)
image_frame.place(relx=0.5, rely=0.3, relwidth=0.8, relheight=0.4, anchor="center")
image_frame.pack_propagate(False)

# Slider frame
downscale_factor = IntVar(value=2)
slider_frame = Frame(window)
slider_frame.place(relx=0.5, rely=0.80, relwidth=0.7, relheight=0.1, anchor='center')

# Label to display image
image_label = Label(image_frame, bg="gray")
image_label.pack(fill=BOTH, expand=True)

# Label to display Slider
slider_label = Label(slider_frame, text= "Downscale Factor:", anchor="w", justify="left")
slider_label.pack(anchor="w")

# Algorithm dropdown label frame
algo_label_frame = Frame(window)
algo_label_frame.place(relx=0.5, rely=0.515, relwidth=0.3, relheight=0.03, anchor="center")

# Algorithm dropdown label
algo_label = Label(algo_label_frame, text= 'Dithering Algorithm', anchor="w")
algo_label.pack()

# Algorithm submenu label frame
algo_submenulabel_frame = Frame(window)
algo_submenulabel_frame.place(relx=0.5, rely=0.59, relwidth=0.3, relheight=0.03, anchor="center")

# Global variables and media dataclass
loaded_image = None
image_tk = None
resize_after_id = None
prev_size = None
@dataclass
class MediaState:
    extension: str = ""
    frame_rate: float = 0.0
    is_video: bool = False
    total_frames: int = 0
    cap: cv2.VideoCapture = None
    path: str = ""

media_state = MediaState()

# When 'Load Media' is clicked
def load_media():
    global loaded_image, image_tk, cap
    path = filedialog.askopenfilename(filetypes=[("Media Files","*.png; *.jpg; *.jpeg; *.mp4; *.mkv, *.webm")])
    image_extensions = ['.png', '.jpg', '.jpeg']
    video_extensions = ['.mkv', '.mp4', '.webm']
    if path:
        ext = os.path.splitext(path)[1]
        if ext in image_extensions:
            loaded_image = Image.open(path)
            update_image()
            export_buttons()
        elif ext in video_extensions:
            media_state.is_video = True
            media_state.path = path
            cap = cv2.VideoCapture(path)
            media_state.cap = cap
            fps = cap.get(cv2.CAP_PROP_FPS)
            media_state.frame_rate = fps
            media_state.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            media_state.extension = ext
            ret, frame = cap.read()
            loaded_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            update_image()
            export_buttons()
        else:
            messagebox.showerror("Unsupported File Type")

# Scale Image with window size
def update_image():
    global loaded_image, image_label

    if loaded_image:
        frame_width = image_frame.winfo_width()
        frame_height = image_frame.winfo_height()
        frame_aspect = frame_width / frame_height

        # Original image size and aspect ratio
        image_width, image_height = loaded_image.size
        image_aspect = image_width / image_height

        # Fit image into window with maintained aspect ratio
        if image_aspect > frame_aspect:
            new_width = frame_width
            new_height = int(frame_width / image_aspect)
        else:
            new_height = frame_height
            new_width = int(frame_height * image_aspect)

        resized_image = loaded_image.resize((new_width, new_height), Image.Resampling.BILINEAR)

        # Convert to use with Tkinter
        image_tk = ImageTk.PhotoImage(resized_image)
        image_label.config(image = image_tk)
        image_label.image = image_tk

# Debounce resize event
def on_resize(event):
    global resize_after_id

    if not loaded_image:
        return
    current_size = (image_frame.winfo_width(), image_frame.winfo_height())

    if resize_after_id:
        window.after_cancel(resize_after_id)
    resize_after_id = window.after(100, update_image)

# Bind the resize of window to image update
window.bind("<Configure>", on_resize)

###########
# Widgets #
###########
# Load button
load_media_button = Button(load_button_frame, text="Load Media", command=load_media)
load_media_button.pack(pady=10)

# Grayscale checkbox
grayscale_var = BooleanVar()
grayscale_checkbox = Checkbutton(grayscale_frame, text="Convert to grayscale?", variable=grayscale_var)
grayscale_checkbox.pack()

# Algorithm dropdown
options_list = ("Bayer", "Floyd-Steinberg")
selected_option = StringVar(value=options_list[0]) 
dropdown = ttk.Combobox(dropdown_frame, textvariable=selected_option)
dropdown['values'] = options_list
dropdown['state'] = 'readonly'
dropdown.pack()

dropdown_submenulabel = Label(algo_submenulabel_frame, anchor="w")

# Algo submenus
    # Bayer submenu
submenu_options_list = ("2x2", "4x4", "8x8", "16x16")
submenu_selected_option = StringVar(value=submenu_options_list[0])
dropdown_submenu = ttk.Combobox(submenu_dropdown_frame, textvariable=submenu_selected_option)
dropdown_submenu['values'] = submenu_options_list
dropdown_submenu['state'] = 'readonly'
    # Floyd-Steinberg submenu
sliders = []
for i in range(4):
    initial_value = [7, 3, 5, 1]
    slide = Scale(floyd_steinberg_submenu, orient='horizontal', from_=-24, to=24)
    slide.set(initial_value[i])
    sliders.append(slide)
sliders[0].grid(row=0, column=0) # Top left
sliders[1].grid(row=0, column=1) # Top right
sliders[2].grid(row=1, column=0) # Bottom left
sliders[3].grid(row=1, column=1) # Bottom right

def show_submenu(*args):
    if dropdown.get() == 'Bayer':
        floyd_steinberg_submenu.place_forget()
        submenu_dropdown_frame.place(relx=0.5, rely=0.63, relwidth=.95, relheight=0.05, anchor="center")
        dropdown_submenulabel.configure(text="Matrix Size")
        dropdown_submenu.pack()
        dropdown_submenulabel.pack()
        
    elif dropdown.get() == 'Floyd-Steinberg':
        submenu_dropdown_frame.place_forget()
        floyd_steinberg_submenu.place(relx=0.5, rely=0.68, relwidth=.523, relheight=0.15, anchor="center")
        dropdown_submenulabel.configure(text="Weights")
        
    
dropdown.bind('<<ComboboxSelected>>', show_submenu)
show_submenu()
# Export buttons
export_png_button = Button(export_frame, text="Export PNG", command=lambda: export_media("PNG"))
export_jpg_button = Button(export_frame, text="Export JPG", command=lambda: export_media("JPEG"))
export_video_button = Button(export_frame, text = "Export Video", command=lambda: export_media("none"))
def export_buttons(*args):
    if media_state.is_video == True:
        export_jpg_button.pack_forget()
        export_png_button.pack_forget()
        export_video_button.pack(side=TOP, expand=True)
    else:
        export_video_button.pack_forget()
        export_png_button.pack(side=RIGHT, expand=True)
        export_jpg_button.pack(side=LEFT, expand=True)

# Downscale Slider
downscale_slider = Scale(
    slider_frame, from_=1, to=12, orient=HORIZONTAL,
    variable=downscale_factor
)
downscale_slider.pack (fill=X, expand=True)

# Progress bar
progress_var = DoubleVar()
progress_bar = ttk.Progressbar(window, variable=progress_var, maximum=100)
progress_bar.place(relx=0.5, rely=0.97, relwidth=0.9, anchor="center")

# Exporter, matrix size handler, and algorithm applicator
def export_media(format):
    if loaded_image is None:
        return
    
    progress_var.set(10)
    print(loaded_image.mode)
    if dropdown.get() == 'Bayer':
        if dropdown_submenu.get() == '2x2':
            matrix_size = 2
        elif dropdown_submenu.get() == '4x4':
            matrix_size = 4
        elif dropdown_submenu.get() == '8x8':
            matrix_size = 8
        elif dropdown_submenu.get() == '16x16':
            matrix_size = 16

    downscale = downscale_factor.get()
    if media_state.is_video:
        video_output_path = filedialog.asksaveasfilename(defaultextension=f".webm",
                                                        filetypes=[(f"(.webm) files", f"*.webm")])

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
                if dropdown.get() == 'Bayer':
                    if grayscale_var.get():
                        grayscale = apply_grayscale(img_pil)
                        dithered = apply_bayer_dithering(grayscale, downscale, matrix_size)
                        dithered = dithered.convert("RGB")
                    else:
                        dithered = apply_bayer_dithering(img_pil, downscale, matrix_size)

                elif dropdown.get() == 'Floyd-Steinberg':
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
                progress_var.set(int((frame_count / media_state.total_frames) * 100))

                # Calculate and print time for this frame
                frame_end_time = time.time()
                frame_process_time = frame_end_time - frame_start_time
                print(f"Frame {frame_count} processed in {frame_process_time:.4f} seconds")

                ret, frame = media_state.cap.read()

            # Total time for processing all frames
            total_end_time = time.time()
            total_process_time = total_end_time - total_start_time
            print(f"Total time to process {frame_count} frames: {total_process_time:.4f} seconds")


            # Estimate bitrate using entropy
            def calculate_image_entropy(image):
                grayscale = image.convert("L")
                histogram = grayscale.histogram()
                total = sum(histogram)
                entropy = -sum((count / total) * math.log2(count / total)
                            for count in histogram if count > 0)
                return entropy

            entropy_values = []
            for i in range(min(5, frame_count)):
                img = Image.open(os.path.join(temp_dir, f"frame_{i:04d}.png"))
                entropy_values.append(calculate_image_entropy(img))
            avg_entropy = sum(entropy_values) / len(entropy_values)
            bitrate_kbps = max(200, int(avg_entropy * 400))  # Tune scale as needed
            bitrate = f"{bitrate_kbps}k"
            print(f"Average entropy: {avg_entropy}")
            print(f"Estimated bitrate: {bitrate}")

            # Two-pass VP9 encoding with passlogfile
            passlogfile = os.path.join(temp_dir, "ffmpeg2pass")
            null_output = os.path.join(temp_dir, "null.webm")  # dummy first pass output

            first_pass = [
                'ffmpeg', '-y',
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%04d.png'),
                '-c:v', 'libvpx-vp9',
                '-b:v', bitrate,
                '-pass', '1',
                '-passlogfile', passlogfile,
                '-an',
                '-f', 'webm',
                null_output
            ]

            second_pass = [
                'ffmpeg', '-y',
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%04d.png'),
                '-i', media_state.path,
                '-shortest',
                '-c:v', 'libvpx-vp9',
                '-b:v', bitrate,
                '-pass', '2',
                '-passlogfile', passlogfile,
                '-deadline', 'good',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'libopus',
                '-b:a', '100k',
                '-movflags', 'faststart',
                video_output_path
            ]

            # Run passes
            print(f"Running first pass with bitrate {bitrate}...")
            subprocess.run(first_pass, check=True)

            print("Running second pass...")
            subprocess.run(second_pass, check=True)

            # Cleanup
            for ext in ['log', 'log.mbtree']:
                try:
                    os.remove(f"{passlogfile}.{ext}")
                except FileNotFoundError:
                    pass
            shutil.rmtree(temp_dir)





    else: # If not video
            if grayscale_var.get() and dropdown.get() == 'Bayer':
                grayscale = apply_grayscale(loaded_image)
                dithered = apply_bayer_dithering(grayscale, downscale, matrix_size)
            elif dropdown.get() == 'Bayer':
                dithered = apply_bayer_dithering(loaded_image, downscale, matrix_size)
            elif dropdown.get() =='Floyd-Steinberg' and grayscale_var.get():
                grayscale = apply_grayscale(loaded_image)
                slider_values = [slide.get() for slide in sliders]
                dithered = fs_dither(grayscale, downscale, slider_values[0], slider_values[1], slider_values[2], slider_values[3])
            elif dropdown.get() == 'Floyd-Steinberg':
                slider_values = [slide.get() for slide in sliders]
                dithered = fs_dither(loaded_image, downscale, slider_values[0], slider_values[1], slider_values[2], slider_values[3])
        
            progress_var.set(50)
       

            ext = format.lower()
            file_path = filedialog.asksaveasfilename(defaultextension=f".{ext}", filetypes=[(f"{format} files", f"*.{ext}")])
            if file_path:
                dithered.save(file_path, format=format)

            progress_var.set(100)
    window.update_idletasks

    window.after(500, lambda: progress_var.set(0))

# Tinker Event loop
window.mainloop()