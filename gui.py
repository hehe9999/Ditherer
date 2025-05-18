# Standard library imports
import os

# Third-party imports
import cv2
from PIL import Image, ImageTk

# Local imports
from dither import apply_bayer_dithering, apply_grayscale, fs_dither
from media.image_utils import load_image, resize_to_fit
from media.state import MediaState
from exporter import export_image, export_video

# Tkinter imports
import tkinter as tk
from tkinter import filedialog, ttk, messagebox


# Create window
window = tk.Tk()
window.title("Ditherer")
window.geometry("600x900")
window.minsize(600, 900)
style = ttk.Style()


## Frames and labels

# Load image button frame
load_button_frame = ttk.Frame(window)
load_button_frame.place(relx=0.5, rely=0.05, anchor="center")

# Grayscale checkbox frame
grayscale_frame = ttk.Frame(window)
grayscale_frame.place(relx=0.5, rely=0.9, relwidth=0.4, relheight=0.1, anchor="center")

# Algo dropdown frame
dropdown_frame = ttk.Frame(window)
dropdown_frame.place(relx=0.5, rely=0.56, relwidth=0.4, relheight=0.05, anchor="center")

# Algo submenu frame
floyd_steinberg_submenu = ttk.Frame(window)

submenu_dropdown_frame = ttk.Frame(window)


# Export buttons frame
export_frame = ttk.Frame(window)
export_frame.place(relx=0.5, rely=0.92, relwidth=0.6, anchor="center")

# Image frame
image_frame = ttk.Frame(window)
image_frame.place(relx=0.5, rely=0.3, relwidth=0.8, relheight=0.4, anchor="center")
image_frame.pack_propagate(False)

# Slider frame
downscale_factor = tk.IntVar(value=2)
slider_frame = ttk.Frame(window)
slider_frame.place(relx=0.5, rely=0.80, relwidth=0.7, relheight=0.1, anchor="center")

# Label to display image
image_label = tk.Label(image_frame, bg="#d0d0d0")
image_label.pack(fill=tk.BOTH, expand=True)

# Label to display Slider
slider_label = ttk.Label(
    slider_frame, text="Downscale Factor:", anchor="w", justify="left"
)
slider_label.pack(anchor="w")

# Algorithm dropdown label frame
algo_label_frame = ttk.Frame(window)
algo_label_frame.place(
    relx=0.5, rely=0.515, relwidth=0.3, relheight=0.03, anchor="center"
)

# Algorithm dropdown label
algo_label = ttk.Label(algo_label_frame, text="Dithering Algorithm", anchor="w")
algo_label.pack()

# Algorithm submenu label frame
algo_submenulabel_frame = ttk.Frame(window)
algo_submenulabel_frame.place(
    relx=0.5, rely=0.59, relwidth=0.3, relheight=0.03, anchor="center"
)

# Global variables and media dataclass
loaded_image = None
image_tk = None
resize_after_id = None
prev_size = None
media_state = MediaState()

# When 'Load Media' is clicked
def load_media():
    global loaded_image, image_tk, cap
    path = filedialog.askopenfilename(
        filetypes=[("Media Files", "*.png; *.jpg; *.jpeg; *.mp4; *.mkv, *.webm")]
    )
    image_extensions = [".png", ".jpg", ".jpeg"]
    video_extensions = [".mkv", ".mp4", ".webm"]
    if path:
        ext = os.path.splitext(path)[1]
        if ext in image_extensions:
            media_state.is_video = False
            loaded_image = load_image(path)
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

        resized_image = resize_to_fit(loaded_image, frame_width, frame_height)

        image_tk = ImageTk.PhotoImage(resized_image)
        image_label.config(image=image_tk)
        image_label.image = image_tk


# Debounce resize event
def on_resize(event):
    global resize_after_id

    if not loaded_image:
        return

    if resize_after_id:
        window.after_cancel(resize_after_id)
    resize_after_id = window.after(100, update_image)


# Bind the resize of window to image update
window.bind("<Configure>", on_resize)

###########
# Widgets #
###########
# Load button
load_media_button = ttk.Button(load_button_frame, text="Load Media", command=load_media)
load_media_button.pack(pady=10)

# Grayscale checkbox
grayscale_var = tk.BooleanVar()
grayscale_checkbox = ttk.Checkbutton(
    grayscale_frame, text="Convert to grayscale?", variable=grayscale_var
)
grayscale_checkbox.pack()

# Algorithm dropdown
options_list = ("Bayer", "Floyd-Steinberg")
selected_option = tk.StringVar(value=options_list[0])
dropdown = ttk.Combobox(dropdown_frame, textvariable=selected_option)
dropdown["values"] = options_list
dropdown["state"] = "readonly"
dropdown.pack()

dropdown_submenulabel = ttk.Label(algo_submenulabel_frame, anchor="w")

# Algo submenus
# Bayer submenu
submenu_options_list = ("2x2", "4x4", "8x8", "16x16")
submenu_selected_option = tk.StringVar(value=submenu_options_list[0])
dropdown_submenu = ttk.Combobox(
    submenu_dropdown_frame, textvariable=submenu_selected_option
)
dropdown_submenu["values"] = submenu_options_list
dropdown_submenu["state"] = "readonly"
# Floyd-Steinberg submenu
sliders = []
for i in range(4):
    initial_value = [7, 3, 5, 1]
    slide = tk.Scale(floyd_steinberg_submenu, orient="horizontal", from_=-24, to=24)
    slide.set(initial_value[i])
    sliders.append(slide)
sliders[0].grid(row=0, column=0)  # Top left
sliders[1].grid(row=0, column=1)  # Top right
sliders[2].grid(row=1, column=0)  # Bottom left
sliders[3].grid(row=1, column=1)  # Bottom right


def show_submenu(*args):
    if dropdown.get() == "Bayer":
        floyd_steinberg_submenu.place_forget()
        submenu_dropdown_frame.place(
            relx=0.5, rely=0.63, relwidth=0.95, relheight=0.05, anchor="center"
        )
        dropdown_submenulabel.configure(text="Matrix Size")
        dropdown_submenu.pack()
        dropdown_submenulabel.pack()

    elif dropdown.get() == "Floyd-Steinberg":
        submenu_dropdown_frame.place_forget()
        floyd_steinberg_submenu.place(
            relx=0.5, rely=0.68, relwidth=0.523, relheight=0.15, anchor="center"
        )
        dropdown_submenulabel.configure(text="Weights")


dropdown.bind("<<ComboboxSelected>>", show_submenu)
show_submenu()

# Downscale Slider
downscale_slider = tk.Scale(
    slider_frame, from_=1, to=12, orient=tk.HORIZONTAL, variable=downscale_factor
)
downscale_slider.pack(fill=tk.X, expand=True)

# Progress bar
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(window, variable=progress_var, maximum=100)
progress_bar.place(relx=0.5, rely=0.97, relwidth=0.9, anchor="center")

# Export buttons
export_png_button = ttk.Button(
    export_frame, text="Export PNG", command=lambda: export_image(
        window,
        dropdown,
        dropdown_submenu,
        loaded_image,
        grayscale_enabled=grayscale_var.get(),
        downscale=downscale_factor.get(),
        format="png",
        sliders=sliders,
        apply_grayscale=apply_grayscale,
        apply_bayer_dithering=apply_bayer_dithering,
        fs_dither=fs_dither,
        progress_callback=progress_var.set
))
export_jpg_button = ttk.Button(
    export_frame, text="Export JPG", command=lambda: export_image(
        dropdown,
        dropdown_submenu,
        loaded_image,
        grayscale_enabled=grayscale_var.get(),
        downscale=downscale_factor.get(),
        format="jpeg",
        sliders=sliders,
        apply_grayscale=apply_grayscale,
        apply_bayer_dithering=apply_bayer_dithering,
        fs_dither=fs_dither,
        progress_callback=progress_var.set,
        window=window
))
export_video_button = ttk.Button(
    export_frame, text="Export Video", command=lambda: export_video(
        window,
        dropdown,
        dropdown_submenu,
        media_state,
        grayscale_var,
        apply_grayscale=apply_grayscale,
        apply_bayer_dithering=apply_bayer_dithering,
        fs_dither=fs_dither,
        downscale=downscale_factor.get(),
        sliders=sliders,
        progress_callback=progress_var.set,


    )
)


def export_buttons(*args):
    if media_state.is_video:
        export_jpg_button.pack_forget()
        export_png_button.pack_forget()
        export_video_button.pack(side=tk.TOP, expand=True)
    else:
        export_video_button.pack_forget()
        export_png_button.pack(side=tk.RIGHT, expand=True)
        export_jpg_button.pack(side=tk.LEFT, expand=True)


# Tinker Event loop
window.mainloop()
