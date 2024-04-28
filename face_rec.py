
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import imutils
import pickle
import time
import cv2
from tkinter import Tk, Button, Label, Entry, Frame, messagebox, simpledialog
import serial
import adafruit_fingerprint
import smtplib
import random
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Initialize 'currentname' to trigger only when a new person is identified.
currentname = "unknown"
# Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"
# Use this xml file
# https://github.com/opencv/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml
cascade = "haarcascade_frontalface_default.xml"

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())
detector = cv2.CascadeClassifier(cascade)

# SMTP server configuration for sending emails via Gmail
EMAIL_ADDRESS = 'akhilunair2002@gmail.com'
EMAIL_PASSWORD = 'gxfx rmzt kstm rmcg'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
OTP_LENGTH = 6  # Length of the OTP to be generated

uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Initialize video stream with lower resolution
vs = VideoStream(src=0, resolution=(640, 480)).start()  # You can adjust the resolution here
time.sleep(2.0)

# Start the FPS counter
fps = FPS().start()

# Initialize global variable
root = None

# Function to generate a random OTP
def generate_otp():
    otp = ''.join(random.choices('0123456789', k=OTP_LENGTH))
    return otp

# Function to send OTP to the provided email address
def send_otp(email, otp):
    subject = 'Your One-Time Password (OTP)'
    body = f'Your OTP is: {otp}'

    try:
        # Connect to SMTP server (Gmail)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

            # Create email message
            msg = f'Subject: {subject}\n\n{body}'

            # Send email
            smtp.sendmail(EMAIL_ADDRESS, email, msg)
            print("OTP sent successfully.")
    except Exception as e:
        print(f"Error sending OTP: {e}")

# Function to send email notification
def send_email_notification(email, subject, message):
    try:
        # Connect to SMTP server (Gmail)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

            # Create a multipart message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = email
            msg['Subject'] = subject

            # Add body to email
            msg.attach(MIMEText(message, 'plain'))

            # Send email
            server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
            print(f"Email notification sent successfully: {subject}")
    except Exception as e:
        print(f"Error sending email notification: {e}")

# Function to get a finger print image, template it, and see if it matches
def get_fingerprint():
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

# Function to fetch user details from the database based on fingerprint ID
def fetch_user_details(fingerprint_id):
    try:
        with sqlite3.connect('fingerprint_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE fingerprint_template_id=?", (fingerprint_id,))
            user_details = cursor.fetchone()
        return user_details
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

# Function to create GUI for withdrawal options
def gui_withdraw(user_details):
    def exit_and_return():
        withdraw_window.destroy()  # Close the withdrawal window
        verify_and_continue()  # Return to face recognition

    def withdraw_amount_from_gui():
        amount = float(withdrawal_entry.get())
        withdraw_amount(user_details[0], amount)

    def add_to_amount(digit):
        current_amount = withdrawal_entry.get()
        new_amount = current_amount + digit
        withdrawal_entry.delete(0, 'end')
        withdrawal_entry.insert('end', new_amount)

    def send_transaction_history_to_email():
        try:
            with sqlite3.connect('fingerprint_database.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT amount, transaction_time FROM transactions WHERE user_id=? ORDER BY transaction_time DESC LIMIT 20", (user_details[0],))
                transactions = cursor.fetchall()
            
            if transactions:
                transaction_history = "\n".join([f"Amount: ₹{transaction[0]}, Time: {transaction[1]}" for transaction in transactions])
                send_email_notification(user_details[3], "Transaction History", f"Last 20 Transactions:\n{transaction_history}")
                messagebox.showinfo("Email Sent", "Transaction history sent to your email.")
            else:
                messagebox.showinfo("No Transactions", "No transaction history found.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    # Create a new window for withdrawal
    withdraw_window = Tk()
    withdraw_window.title("ATM - Withdrawal")

    # Stretch the window to full screen
    withdraw_window.attributes('-fullscreen', True)

    # Set background color for the window
    withdraw_window.configure(bg='#D9F1F1')  # Light blue background

    label_font = ('Helvetica', 24)
    button_font = ('Helvetica', 18)

    # Populate user details
    user_label = Label(withdraw_window, text=f"Name: {user_details[1]}\nBalance: ₹{user_details[2]}", font=label_font, bg='#D9F1F1')
    user_label.pack()

    # Withdrawal entry
    withdrawal_entry = Entry(withdraw_window, font=button_font)
    withdrawal_entry.pack()

    # Virtual keypad
    keypad_frame = Frame(withdraw_window, bg='#D9F1F1')
    keypad_frame.pack()

    for i in range(1, 10):
        Button(keypad_frame, text=str(i), font=button_font, command=lambda digit=i: add_to_amount(str(digit))).grid(row=(i-1)//3, column=(i-1)%3)

    Button(keypad_frame, text="0", font=button_font, command=lambda: add_to_amount("0")).grid(row=3, column=1)
    Button(keypad_frame, text=".", font=button_font, command=lambda: add_to_amount(".")).grid(row=3, column=2)

    # Withdraw button
    withdraw_button = Button(withdraw_window, text="Withdraw", font=button_font, command=withdraw_amount_from_gui, bg='#B3FFCD')  # Light green button
    withdraw_button.pack()

    # Send transaction history button
    send_transaction_history_button = Button(withdraw_window, text="Send Transaction History", font=button_font, command=send_transaction_history_to_email, bg='#B3FFCD')
    send_transaction_history_button.pack()

    # Exit button
    exit_button = Button(withdraw_window, text="Exit", font=button_font, command=exit_and_return, bg='#B3FFCD')  # Light green button
    exit_button.pack()

    withdraw_window.mainloop()

# Function to withdraw amount from user's balance
def withdraw_amount(user_id, amount):
    if amount <= 0:
        messagebox.showerror("Error", "Invalid withdrawal amount")
        return

    try:
        with sqlite3.connect('fingerprint_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance, email FROM users WHERE id=?", (user_id,))
            result = cursor.fetchone()
            current_balance, email = result[0], result[1]

            if current_balance < amount:
                messagebox.showerror("Insufficient Balance", "You have insufficient balance.")
                return

            new_balance = current_balance - amount
            cursor.execute("UPDATE users SET balance=? WHERE id=?", (new_balance, user_id))
            cursor.execute("INSERT INTO transactions (user_id, amount) VALUES (?, ?)", (user_id, amount))
            conn.commit()
            messagebox.showinfo("Success", f"Withdrawal successful. New balance: ₹{new_balance}")

            # Send email notification for successful transaction
            subject = "Successful Withdrawal"
            message = f"Your withdrawal of ₹{amount} was successful. Your new balance is ₹{new_balance}."
            send_email_notification(email, subject, message)
    except sqlite3.Error as e:
        print(f"Database error: {e}")

# Function to verify identity and continue with ATM functionalities
def verify():
    fingerprint_not_found = False
    if get_fingerprint():
        fingerprint_id = finger.finger_id
        user_details = fetch_user_details(fingerprint_id)
        if user_details:
            vs.stop()
            gui_withdraw(user_details)
        else:
            messagebox.showerror("Fingerprint Not Found", "User details not found for the fingerprint.")
    else:
        fingerprint_not_found = True

    # If fingerprint not found, prompt for email
    if fingerprint_not_found:
        email = simpledialog.askstring("Enter Email", "Enter your email address:")
        if email:
            verify_with_otp(email)

# Function to verify identity with OTP and continue with ATM functionalities
def verify_with_otp(email):
    try:
        with sqlite3.connect('fingerprint_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email=?", (email,))
            user_details = cursor.fetchone()

            if user_details:
                otp = generate_otp()
                send_otp(email, otp)
                user_input = simpledialog.askstring("Enter OTP", "Enter the OTP sent to your email:")
                if user_input == otp:
                    messagebox.showinfo("OTP Verified", "OTP verification successful!")
                    gui_withdraw(user_details)  # Move to withdraw page with user details
                else:
                    messagebox.showerror("OTP Verification Failed", "Incorrect OTP!")
            else:
                messagebox.showerror("Email Not Found", "Entered email address is not registered.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")

# Function to verify identity and continue with ATM functionalities
def verify_and_continue():
    messagebox.showinfo("Verification", "Identity verified. Proceed with ATM functionalities.")

    # Send email notification for successful login
    if currentname != "unknown":
        try:
            with sqlite3.connect('fingerprint_database.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM users WHERE name=?", (currentname,))
                email = cursor.fetchone()[0]

            subject = "Successful Login"
            message = "You have successfully logged in to the ATM system."
            send_email_notification(email, subject, message)
        except sqlite3.Error as e:
            print(f"Error retrieving user email: {e}")

    cv2.destroyAllWindows()

    # Open a new window or frame for further verification
    global root
    if root:
        root.destroy()  # Close the current window

    # Create a new window for additional verification
    root = Tk()
    root.title("ATM")

    # Set background color for the window
    root.configure(bg='#D9F1F1')  # Light blue background

    # Stretch the window to full screen
    root.attributes('-fullscreen', True)

    button_font = ('Helvetica', 18)

    # Button to verify fingerprint and continue
    verify_fingerprint_button = Button(root, text="Verify Fingerprint", font=button_font, command=verify, bg='#B3FFCD')  # Light green button
    verify_fingerprint_button.pack(fill='x', padx=10, pady=10)

    # Button to exit program
    exit_button = Button(root, text="Exit", font=button_font, command=exit_program, bg='#B3FFCD')  # Light green button
    exit_button.pack(fill='x', padx=10, pady=10)

    root.mainloop()

# Function to exit the program
def exit_program():
    vs.stop()
    if root:
        root.destroy()

# Main loop for facial recognition
while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=640)  # Resize the frame to match the resolution
    frame = cv2.flip(frame, 1)  # Flip the frame horizontally if needed

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    rects = detector.detectMultiScale(gray, scaleFactor=1.1,
                                      minNeighbors=5, minSize=(30, 30),
                                      flags=cv2.CASCADE_SCALE_IMAGE)

    boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]

    encodings = face_recognition.face_encodings(rgb, boxes)
    names = []

    for encoding in encodings:
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        name = "Unknown"

        if True in matches:
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}

            for i in matchedIdxs:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1

            name = max(counts, key=counts.get)

            if currentname != name:
                currentname = name
                print(currentname)
                verify_and_continue()
                vs.stop()
                break

        names.append(name)

    for ((top, right, bottom, left), name) in zip(boxes, names):
        cv2.rectangle(frame, (left, top), (right, bottom),
                      (0, 255, 0), 2)

    # Display the frame
    cv2.imshow("Facial Recognition", frame)

    # Check for key press to exit the program
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# Cleanup
cv2.destroyAllWindows()
vs.stop()
