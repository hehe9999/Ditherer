import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# Create window
window = tk.Tk()
window.title("Ditherer")
window.geometry("400x600")

###############
#Layout Frames#
###############
# Load image button frame
load_button_frame = tk.Frame(window, height=50)
load_button_frame.place(relx=0.5, rely=0.1, anchor="center")

# Image frame
image_frame = tk.Frame(window)
image_frame.place(relx=0.5, rely=0.35, relwidth=0.8, relheight=0.4, anchor="center")
##############

# Label to display image
image_label = tk.Label(image_frame, bg="gray")
image_label.pack(fill=tk.BOTH, expand=True)

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

# Widgets
load_image_button = tk.Button(load_button_frame, text="Load Image", command=load_image)
load_image_button.pack(pady=10)

# Tinker Event loop
window.mainloop()