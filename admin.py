import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import pickle
import time
from pyfingerprint.pyfingerprint import PyFingerprint

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
            cursor.execute("SELECT name, balance FROM users")
            self.users = cursor.fetchall()
            conn.close()
            for user in self.users:
                self.users_listbox.insert(tk.END, f"Name: {user[0]}, Balance: {user[1]}")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error: {e}")

    def enroll_fingerprint(self):
        try:
            # Check if the user already exists in the database
            conn = sqlite3.connect('fingerprint_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE name=?", (self.name_entry.get(),))
            user_count = cursor.fetchone()[0]
            conn.close()

            if user_count > 0:
                # If user exists, prompt for updating fingerprint
                update_fingerprint = tk.messagebox.askyesno("Update Fingerprint", "User already exists. Do you want to update the fingerprint?")
                if not update_fingerprint:
                    return

            f = PyFingerprint('/dev/ttyAMA0', 57600, 0xFFFFFFFF, 0x00000000)
            if not f.verifyPassword():
                raise ValueError('The fingerprint sensor password is incorrect!')

            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                print('Place your finger on the sensor...')
                while not f.readImage():
                    pass

                f.convertImage(0x01)

                print('Remove your finger...')
                tk.messagebox.showinfo("Fingerprint Enrolled", "Fingerprint enrolled successfully.")
                # Store the fingerprint data in the database
                fingerprint_data = pickle.dumps(f.downloadCharacteristics())
                self.store_fingerprint(fingerprint_data)
                break

            if retry_count == max_retries:
                tk.messagebox.showerror("Fingerprint Enrollment Error", "Maximum retries exceeded. Please try again later.")

        except Exception as e:
            tk.messagebox.showerror("Fingerprint Enrollment Error", f"Error: {e}")

    def store_fingerprint(self, fingerprint_data):
        try:
            conn = sqlite3.connect('fingerprint_database.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, balance, fingerprint) VALUES (?, ?, ?)", (self.name_entry.get(), self.balance_entry.get(), fingerprint_data))
            conn.commit()
            conn.close()
            messagebox.showinfo("Fingerprint Stored", "Fingerprint data stored successfully.")
            self.clear_entries()
            self.users_listbox.delete(0, tk.END)
            self.load_users()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error: {e}")

    def add_user(self):
        name = self.name_entry.get()
        balance = self.balance_entry.get()

        if name.strip() and balance.isdigit():
            try:
                conn = sqlite3.connect('fingerprint_database.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (name, balance) VALUES (?, ?)", (name, balance))
                conn.commit()
                conn.close()
                messagebox.showinfo("User Added", "User details added successfully.")
                self.clear_entries()
                self.users_listbox.delete(0, tk.END)
                self.load_users()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error: {e}")
        else:
            messagebox.showerror("Invalid Input", "Please enter valid name and balance.")

    def clear_entries(self):
        self.name_entry.delete(0, tk.END)
        self.balance_entry.delete(0, tk.END)

    def edit_user(self):
        selected_index = self.users_listbox.curselection()
        if selected_index:
            selected_user = self.users_listbox.get(selected_index)
            name = selected_user.split(', ')[0].split(': ')[1]

            # Populate entry fields with user details
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, name)

    def update_user(self):
        selected_index = self.users_listbox.curselection()
        if selected_index:
            selected_user = self.users_listbox.get(selected_index)
            name = selected_user.split(', ')[0].split(': ')[1]

            # Get updated details from entry fields
            updated_name = self.name_entry.get()
            updated_balance = self.balance_entry.get()

            # Update database with new details
            if updated_name.strip() and updated_balance.isdigit():
                try:
                    conn = sqlite3.connect('fingerprint_database.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET name=?, balance=? WHERE name=?", (updated_name, updated_balance, name))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("User Updated", "User details updated successfully.")
                    self.clear_entries()
                    self.users_listbox.delete(0, tk.END)
                    self.load_users()
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Error: {e}")
            else:
                messagebox.showerror("Invalid Input", "Please enter valid name and balance.")

def create_users_table():
    try:
        conn = sqlite3.connect('fingerprint_database.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        balance INTEGER NOT NULL,
                        fingerprint BLOB)''')
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
