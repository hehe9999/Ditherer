from tkinter import *
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
from Ditherer import apply_bayer_dithering

# Create window
window = Tk()
window.title("Ditherer")
window.geometry("400x600")

###############
#Layout Frames#
###############
# Load image button frame
load_button_frame = Frame(window, height=50)
load_button_frame.place(relx=0.5, rely=0.1, anchor="center")

# Export buttons frame
export_frame = Frame(window)
export_frame.place(relx=0.5, rely=0.85, relwidth=0.6, anchor="center")

# Image frame
image_frame = Frame(window)
image_frame.place(relx=0.5, rely=0.35, relwidth=0.8, relheight=0.4, anchor="center")
image_frame.pack_propagate(False)

# Slider frame
downscale_factor = IntVar(value=2)
slider_frame = Frame(window)
slider_frame.place(relx=0.5, rely=0.65, relwidth=0.7, relheight=0.1, anchor='center')

###############

# Label to display image
image_label = Label(image_frame, bg="gray")
image_label.pack(fill=BOTH, expand=True)

# Label to display Slider
slider_label = Label(slider_frame, text= "Downscale Factor:", anchor="w", justify="left")
slider_label.pack(anchor="w")

# Store image to use globally
loaded_image = None
image_tk = None
resize_after_id = None
prev_size = None

# When 'Load Image' is clicked
def load_image():
    global loaded_image, image_tk
    path = filedialog.askopenfilename(filetypes=[("Image Files","*.png; *.jpg; *.jpeg")])
    
    # If image is selected
    if path:
        loaded_image = Image.open(path)
        update_image()

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
load_image_button = Button(load_button_frame, text="Load Image", command=load_image)
load_image_button.pack(pady=10)

# Export buttons
export_png_button = Button(export_frame, text="Export PNG", command=lambda: export_image("PNG"))
export_png_button.pack(side=RIGHT, expand=True)

export_jpg_button = Button(export_frame, text="Export JPG", command=lambda: export_image("JPEG"))
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
progress_bar.place(relx=0.5, rely=0.95, relwidth=0.9, anchor="center")
###########

# Exporter
def export_image(format):
    if loaded_image is None:
        return
    
    progress_var.set(10)
    
    downscale = downscale_factor.get()
    dithered = apply_bayer_dithering(loaded_image, downscale)

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