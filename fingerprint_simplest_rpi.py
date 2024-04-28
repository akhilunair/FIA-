import time
import serial
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import adafruit_fingerprint
from PIL import Image

uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

def enroll_finger(location):
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="")
        else:
            print("Place same finger again...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Storing model #%d..." % location, end="")
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Stored")
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return False

    return True

def get_num(max_number):
    """Use input() to get a valid number from 0 to the maximum size
    of the library. Retry till success!"""
    i = -1
    while (i > max_number - 1) or (i < 0):
        try:
            i = int(input("Enter ID # from 0-{}: ".format(max_number - 1)))
        except ValueError:
            pass
    return i

def save_fingerprint_image_wrapper():
    filename = simpledialog.askstring("Save Fingerprint Image", "Enter filename to save the fingerprint image:")
    if filename:
        if save_fingerprint_image(filename):
            messagebox.showinfo("Success", "Fingerprint image saved successfully!")
        else:
            messagebox.showinfo("Error", "Failed to save fingerprint image")

def save_fingerprint_image(filename):
    """Scan fingerprint then save image to filename."""
    while finger.get_image():
        pass

    img = Image.new("L", (256, 288), "white")
    pixeldata = img.load()
    mask = 0b00001111
    result = finger.get_fpdata(sensorbuffer="image")

    x = 0
    y = 0
    for i in range(len(result)):
        pixeldata[x, y] = (int(result[i]) >> 4) * 17
        x += 1
        pixeldata[x, y] = (int(result[i]) & mask) * 17
        if x == 255:
            x = 0
            y += 1
        else:
            x += 1

    try:
        img.save(filename)
        return True
    except Exception as e:
        print("Error saving fingerprint image:", e)
        return False

def enroll():
    location = simpledialog.askinteger("Enroll", "Enter location to enroll (0-{}):".format(finger.library_size - 1))
    if location is not None:
        enroll_finger(location)

def find():
    if get_fingerprint():
        messagebox.showinfo("Fingerprint Found", "Detected #{} with confidence {}".format(finger.finger_id, finger.confidence))
    else:
        messagebox.showinfo("Fingerprint Not Found", "Finger not found")

def delete():
    location = simpledialog.askinteger("Delete", "Enter location to delete (0-{}):".format(finger.library_size - 1))
    if location is not None:
        if finger.delete_model(location) == adafruit_fingerprint.OK:
            messagebox.showinfo("Deleted", "Fingerprint at location {} deleted successfully!".format(location))
        else:
            messagebox.showinfo("Failed", "Failed to delete fingerprint")

def reset_library():
    if finger.empty_library() == adafruit_fingerprint.OK:
        messagebox.showinfo("Library Reset", "Library emptied successfully!")
    else:
        messagebox.showinfo("Failed", "Failed to reset library")

def gui_main():
    root = tk.Tk()
    root.title("Fingerprint GUI")

    # Set the GUI to fullscreen
    root.attributes('-fullscreen', True)

    # Define colors and fonts
    background_color = "#f0f0f0"  # Light grey background
    button_color = "#4CAF50"  # Green button color
    button_font = ('Helvetica', 18, 'bold')  # Button font

    # Define a custom style for the buttons
    style = ttk.Style()
    style.configure('TButton', font=button_font, foreground='black', background=button_color)

    # Create frames for organizing widgets
    frame_header = tk.Frame(root, bg=background_color)
    frame_header.pack(fill=tk.BOTH)

    frame_buttons = tk.Frame(root, bg=background_color)
    frame_buttons.pack(fill=tk.BOTH, expand=True)

    frame_footer = tk.Frame(root, bg=background_color)
    frame_footer.pack(fill=tk.BOTH)

    # Add a header label
    header_label = tk.Label(frame_header, text="Fingerprint GUI", font=('Helvetica', 24, 'bold'), bg=background_color)
    header_label.pack(pady=20)

    # Create colorful and beautiful buttons
    button_enroll = ttk.Button(frame_buttons, text="Enroll", command=enroll)
    button_enroll.pack(side=tk.LEFT, padx=20, pady=10)

    button_find = ttk.Button(frame_buttons, text="Find", command=find)
    button_find.pack(side=tk.LEFT, padx=20, pady=10)

    button_delete = ttk.Button(frame_buttons, text="Delete", command=delete)
    button_delete.pack(side=tk.LEFT, padx=20, pady=10)

    button_reset = ttk.Button(frame_buttons, text="Reset Library", command=reset_library)
    button_reset.pack(side=tk.LEFT, padx=20, pady=10)

    button_save = ttk.Button(frame_buttons, text="Save Fingerprint Image", command=save_fingerprint_image_wrapper)
    button_save.pack(side=tk.LEFT, padx=20, pady=10)

    button_quit = ttk.Button(frame_footer, text="Quit", command=root.destroy)
    button_quit.pack(side=tk.RIGHT, padx=20, pady=10)

    root.mainloop()

def main():
    while True:
        print("----------------")
        if finger.read_templates() != adafruit_fingerprint.OK:
            raise RuntimeError("Failed to read templates")
        print("Fingerprint templates: ", finger.templates)
        if finger.count_templates() != adafruit_fingerprint.OK:
            raise RuntimeError("Failed to read templates")
        print("Number of templates found: ", finger.template_count)
        if finger.read_sysparam() != adafruit_fingerprint.OK:
            raise RuntimeError("Failed to get system parameters")
        print("Size of template library: ", finger.library_size)
        print("e) enroll print")
        print("f) find print")
        print("d) delete print")
        print("s) save fingerprint image")
        print("r) reset library")
        print("q) quit")
        print("----------------")
        c = input("> ")

        if c == "e":
            enroll_finger(get_num(finger.library_size))
        if c == "f":
            if get_fingerprint():
                print("Detected #", finger.finger_id, "with confidence", finger.confidence)
            else:
                print("Finger not found")
        if c == "d":
            if finger.delete_model(get_num(finger.library_size)) == adafruit_fingerprint.OK:
                print("Deleted!")
            else:
                print("Failed to delete")
        if c == "s":
            if save_fingerprint_image("fingerprint.png"):
                print("Fingerprint image saved")
            else:
                print("Failed to save fingerprint image")
        if c == "r":
            if finger.empty_library() == adafruit_fingerprint.OK:
                print("Library empty!")
            else:
                print("Failed to empty library")
        if c == "q":
            print("Exiting fingerprint example program")
            raise SystemExit

if __name__ == "__main__":
    gui_main()
