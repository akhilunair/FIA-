import picamera
import time
import cv2
import numpy as np

name = 'Akhil'  # replace with your name
num_images = 12  # Number of images to capture

# Initialize the PiCamera
camera = picamera.PiCamera()

# Set the resolution (adjust as needed for quality)
camera.resolution = (640, 480)  # Example resolution

# Warm up the camera
time.sleep(2)

# Function to capture and show image
def capture_and_show():
    img_name = "/home/pi/Desktop/{}_{}.jpg".format(name, time.time())
    camera.capture(img_name)
    print("{} written!".format(img_name))
    img = cv2.imread(img_name)
    cv2.imshow('Preview', img)
    cv2.waitKey(1000)
    cv2.destroyAllWindows()

# Create a window to display the camera feed
cv2.namedWindow('Preview', cv2.WINDOW_NORMAL)

img_counter = 0
while img_counter < num_images:
    # Capture and show image
    capture_and_show()
    img_counter += 1

# Release the camera
camera.close()
