import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import time
import serial
import adafruit_fingerprint
import random
import smtplib
from email.mime.text import MIMEText

uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)a

class Admin_GUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Admin Panel")
        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()
        self.master.geometry(f"{int(self.screen_width*0.4)}x{int(self.screen_height*0.4)}")
        self.master.configure(bg='#009688')

        self.create_widgets()
        self.load_users()

    def create_widgets(self):
        self.header_label = tk.Label(self.master, text="Admin Panel - Add User", bg='#009688', fg='white', font=('Helvetica', 24, 'bold'))
        self.header_label.pack(pady=20)

        self.name_label = tk.Label(self.master, text="Enter Name:", bg='#009688', fg='white', font=('Helvetica', 14))
        self.name_label.pack()

        self.name_entry = tk.Entry(self.master, font=('Helvetica', 14))
        self.name_entry.pack()

        self.balance_label = tk.Label(self.master, text="Enter Balance:", bg='#009688', fg='white', font=('Helvetica', 14))
        self.balance_label.pack()

        self.balance_entry = tk.Entry(self.master, font=('Helvetica', 14))
        self.balance_entry.pack()

        self.email_label = tk.Label(self.master, text="Enter Email:", bg='#009688', fg='white', font=('Helvetica', 14))
        self.email_label.pack()

        self.email_entry = tk.Entry(self.master, font=('Helvetica', 14))
        self.email_entry.pack()

        self.enroll_button = tk.Button(self.master, text="Enroll Fingerprint", command=self.enroll_fingerprint, bg='#FF5722', fg='white', font=('Helvetica', 14))
        self.enroll_button.pack(pady=10)

        self.add_button = tk.Button(self.master, text="Add User", command=self.add_user, bg='#FF5722', fg='white', font=('Helvetica', 14))
        self.add_button.pack(pady=10)

        self.exit_button = tk.Button(self.master, text="Exit", command=self.master.destroy, bg='#FF5722', fg='white', font=('Helvetica', 14))
        self.exit_button.pack(pady=10)

        self.users_header_label = tk.Label(self.master, text="Select user to edit and update changes", bg='#009688', fg='white', font=('Helvetica', 14))
        self.users_header_label.pack()

        self.users_listbox = tk.Listbox(self.master, font=('Helvetica', 14), width=40, height=10)
        self.users_listbox.pack(pady=20)

        self.edit_button = tk.Button(self.master, text="Edit", command=self.edit_user, bg='#FF5722', fg='white', font=('Helvetica', 14))
        self.edit_button.pack()

        self.update_button = tk.Button(self.master, text="Update", command=self.update_user, bg='#FF5722', fg='white', font=('Helvetica', 14))
        self.update_button.pack()

    def load_users(self):
        try:
            conn = sqlite3.connect('fingerprint_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, balance, email FROM users")
            self.users = cursor.fetchall()
            conn.close()
            for user in self.users:
                self.users_listbox.insert(tk.END, f"Name: {user[0]}, Balance: {user[1]}, Email: {user[2]}")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error: {e}")

    def enroll_fingerprint(self):
        try:
            conn = sqlite3.connect('fingerprint_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE name=?", (self.name_entry.get(),))
            user_count = cursor.fetchone()[0]
            conn.close()

            if user_count > 0:
                update_fingerprint = tk.messagebox.askyesno("Update Fingerprint", "User already exists. Do you want to update the fingerprint?")
                if not update_fingerprint:
                    return

            location = simpledialog.askinteger("Enroll", "Enter location to enroll (0-{}):".format(finger.library_size - 1))
            if location is not None:
                template_id = self.enroll_finger(location)
                if template_id is not None:
                    tk.messagebox.showinfo("Fingerprint Enrolled", "Fingerprint enrolled successfully.")
                    self.store_fingerprint(location, template_id)
                else:
                    tk.messagebox.showerror("Fingerprint Enrollment Error", "Failed to enroll fingerprint.")
        except Exception as e:
            tk.messagebox.showerror("Fingerprint Enrollment Error", f"Error: {e}")

    def enroll_finger(self, location):
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
                    return None
                else:
                    print("Other error")
                    return None

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
                return None

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
            return None

        print("Storing model #%d..." % location, end="")
        i = finger.store_model(location)
        if i == adafruit_fingerprint.OK:
            print("Stored")
            return location
        else:
            if i == adafruit_fingerprint.BADLOCATION:
                print("Bad storage location")
            elif i == adafruit_fingerprint.FLASHERR:
                print("Flash storage error")
            else:
                print("Other error")
            return None

    def store_fingerprint(self, location, template_id):
        try:
            # Generate a random PIN number
            pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            conn = sqlite3.connect('fingerprint_database.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, balance, email, fingerprint_template_id, pin) VALUES (?, ?, ?, ?, ?)", (self.name_entry.get(), self.balance_entry.get(), self.email_entry.get(), template_id, pin))
            conn.commit()
            conn.close()

            # Send PIN to user's email
            self.send_email(self.email_entry.get(), pin)

            messagebox.showinfo("Fingerprint Stored", "Fingerprint data stored successfully and PIN sent to the user's email.")
            self.clear_entries()
            self.users_listbox.delete(0, tk.END)
            self.load_users()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")

    def send_email(self, recipient_email, pin):
        try:
            sender_email = "akhilunair2002@gmail.com"  # Change to your email address
            password = "snce tguo ocnf sfah"  # Change to your email password

            message = MIMEText(f"Your PIN number is: {pin}")
            message['From'] = sender_email
            message['To'] = recipient_email
            message['Subject'] = "Your PIN Number"

            server = smtplib.SMTP('smtp.gmail.com', 587)  # Change to your SMTP server
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, message.as_string())
            server.quit()
        except Exception as e:
            messagebox.showerror("Email Error", f"Error sending email: {e}")

    def add_user(self):
        name = self.name_entry.get()
        balance = self.balance_entry.get()
        email = self.email_entry.get()

        if name.strip() and balance.isdigit() and email.strip():
            try:
                conn = sqlite3.connect('fingerprint_database.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (name, balance, email) VALUES (?, ?, ?)", (name, balance, email))
                conn.commit()
                conn.close()
                messagebox.showinfo("User Added", "User details added successfully.")
                self.clear_entries()
                self.users_listbox.delete(0, tk.END)
                self.load_users()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error: {e}")
        else:
            messagebox.showerror("Invalid Input", "Please enter valid name, balance, and email.")

    def clear_entries(self):
        self.name_entry.delete(0, tk.END)
        self.balance_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)

    def edit_user(self):
        selected_index = self.users_listbox.curselection()
        if selected_index:
            selected_user = self.users_listbox.get(selected_index)
            name = selected_user.split(', ')[0].split(': ')[1]

            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, name)

    def update_user(self):
        selected_index = self.users_listbox.curselection()
        if selected_index:
            selected_user = self.users_listbox.get(selected_index)
            name = selected_user.split(', ')[0].split(': ')[1]

            updated_name = self.name_entry.get()
            updated_balance = self.balance_entry.get()
            updated_email = self.email_entry.get()

            if updated_name.strip() and updated_balance.isdigit() and updated_email.strip():
                try:
                    conn = sqlite3.connect('fingerprint_database.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET name=?, balance=?, email=? WHERE name=?", (updated_name, updated_balance, updated_email, name))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("User Updated", "User details updated successfully.")
                    self.clear_entries()
                    self.users_listbox.delete(0, tk.END)
                    self.load_users()
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Error: {e}")
            else:
                messagebox.showerror("Invalid Input", "Please enter valid name, balance, and email.")

def create_users_table():
    try:
        conn = sqlite3.connect('fingerprint_database.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        balance INTEGER NOT NULL,
                        email TEXT NOT NULL,
                        fingerprint_template_id INTEGER,
                        pin TEXT)''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Error: {e}")

def main():
    create_users_table()
    root = tk.Tk()
    admin = Admin_GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

