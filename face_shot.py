
import picamera
import time
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk  # Import ImageTk for displaying images
import os

name = 'Akhil'  # replace with your name
num_images = 12  # Number of images to capture

# Initialize the PiCamera
camera = picamera.PiCamera()

# Set the resolution (adjust as needed for quality)
camera.resolution = (640, 480)  # Example resolution

# Warm up the camera
time.sleep(2)

# Create Tkinter window
root = tk.Tk()
root.title("PiCamera Capture")

# Set background and foreground colors
bg_color = '#8A2BE2'  # Violet
fg_color = '#000000'  # Black
label_bg_color = '#2F4F4F'  # Dark Slate Gray

# Set window size
window_width = 800
window_height = 600
root.geometry(f"{window_width}x{window_height}")

# Set window background color
root.configure(bg=bg_color)

# Function to capture image
def capture_image():
    # Open file dialog to choose directory
    save_dir = filedialog.askdirectory()
    if save_dir:
        # Check if the directory exists, if not, ask user to create it
        if not os.path.exists(save_dir):
            create_folder = messagebox.askyesno("Folder not found", "The specified directory doesn't exist. Do you want to create it?")
            if create_folder:
                os.makedirs(save_dir)
            else:
                messagebox.showinfo("Information", "Please choose a valid directory.")
                return
        img_name = f"{save_dir}/{name}_{time.time()}.jpg"
        camera.capture(img_name)
        print(f"{img_name} written!")
        img = cv2.imread(img_name)
        # Convert image to RGB format for displaying in Tkinter
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Resize image to fit the window
        img_rgb = cv2.resize(img_rgb, (640, 480))
        # Convert image to PIL format
        img_pil = Image.fromarray(img_rgb)
        # Convert PIL image to Tkinter format
        img_tk = ImageTk.PhotoImage(img_pil)
        # Display image on label
        label_img.imgtk = img_tk
        label_img.config(image=img_tk)

# Create a label to display the captured image
label_img = tk.Label(root, bg=label_bg_color)
label_img.pack()

# Create a button to capture an image
btn_capture = tk.Button(root, text="Capture Image", command=capture_image, bg=fg_color, fg=bg_color)
btn_capture.pack()

# Run the Tkinter event loop
root.mainloop()

# Release the camera
camera.close()

