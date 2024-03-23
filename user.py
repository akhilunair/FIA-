import tkinter as tk
from tkinter import messagebox
import sqlite3
import pickle
from pyfingerprint.pyfingerprint import PyFingerprint

# Calculate the similarity score between two fingerprint templates
def calculate_similarity(template1, template2):
    # Example: Hamming distance calculation
    if len(template1) != len(template2):
        return 0.0  # Return 0 if templates are of different lengths
    else:
        score = sum(a != b for a, b in zip(template1, template2))
        return 1.0 - (score / len(template1))  # Normalize the score to range [0, 1]

class FingerprintVerificationGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Fingerprint Verification")
        self.master.configure(bg='#009688')

        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()
        self.master.attributes('-fullscreen', True)  # Make the window fullscreen

        self.create_widgets()

    def create_widgets(self):
        self.welcome_label = tk.Label(self.master, text="Welcome to FIA ATM !", bg='#009688', fg='white', font=('Helvetica', 24, 'bold'))
        self.welcome_label.pack(pady=20)

        self.header_label = tk.Label(self.master, text="Fingerprint Verification", bg='#009688', fg='white', font=('Helvetica', 24, 'bold'))
        self.header_label.pack(pady=10)

        self.note1_label = tk.Label(self.master, text="* Before touching the fingerprint sensor, use the cotton cloth provided for cleaning the sensor surface.", bg='#009688', fg='white', font=('Helvetica', 12))
        self.note1_label.pack(pady=(0, 5))

        self.note2_label = tk.Label(self.master, text="* Don't touch the sensor surface with dirty fingers, clean before touching it for better accuracy.", bg='#009688', fg='white', font=('Helvetica', 12))
        self.note2_label.pack(pady=(0, 20))

        self.verify_button = tk.Button(self.master, text="Verify Fingerprint", command=self.verify_fingerprint, bg='#FF5722', fg='white', font=('Helvetica', 14))
        self.verify_button.pack(pady=10)

    def verify_fingerprint(self):
        try:
            f = PyFingerprint('/dev/ttyAMA0', 57600, 0xFFFFFFFF, 0x00000000)
            if not f.verifyPassword():
                raise ValueError('The fingerprint sensor password is incorrect!')

            print('Place your finger on the sensor...')
            while not f.readImage():
                pass

            f.convertImage(0x01)
            print('Remove your finger...')

            # Ensure proper conversion and extraction of the fingerprint template
            template = f.downloadCharacteristics(0x01)
            if template == None:
                raise ValueError('Failed to download the fingerprint template from the sensor.')

            # Search for a fingerprint match in the database
            conn = sqlite3.connect('fingerprint_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, balance, fingerprint FROM users")
            users = cursor.fetchall()

            # Set the threshold for matching
            MATCH_THRESHOLD = 0.6

            max_similarity_score = 0.0
            best_match_user = None

            for user in users:
                user_id, name, balance, fingerprint_blob = user
                stored_fingerprint = pickle.loads(fingerprint_blob)

                # Calculate the similarity score
                similarity_score = calculate_similarity(template, stored_fingerprint)
                print("Similarity Score:", similarity_score)

                # Compare similarity score with threshold and update best match if applicable
                if similarity_score >= MATCH_THRESHOLD and similarity_score > max_similarity_score:
                    max_similarity_score = similarity_score
                    best_match_user = {'id': user_id, 'name': name, 'balance': balance}

            if best_match_user:
                messagebox.showinfo("Successfully Verified", "Fingerprint successfully verified.")
                self.show_action_page(best_match_user)
            else:
                messagebox.showinfo("Fingerprint Verification", "Fingerprint not recognized.")
            
        except Exception as e:
            messagebox.showerror("Fingerprint Verification Error", f"Error: {e}")

    def show_action_page(self, user):
        self.master.withdraw()  # Hide verification GUI window
        action_window = tk.Tk()
        action_page = ActionPage(action_window, user, self)

class ActionPage:
    def __init__(self, master, user, verification_gui):
        self.master = master
        self.user = user
        self.verification_gui = verification_gui
        self.master.title(f"Welcome {user['name']} to FIA ATM !")
        self.master.configure(bg='#009688')

        # Calculate window position based on screen size
        window_width = int(master.winfo_screenwidth() * 0.8)
        window_height = int(master.winfo_screenheight() * 0.8)
        window_x = int((master.winfo_screenwidth() - window_width) / 2)
        window_y = int((master.winfo_screenheight() - window_height) / 2)
        self.master.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")

        self.create_widgets()

    def create_widgets(self):
        # Header
        self.header_label = tk.Label(self.master, text=f"Welcome {self.user['name']} to FIA ATM !", bg='#009688', fg='white', font=('Helvetica', 24, 'bold'))
        self.header_label.pack(pady=(20, 10))

        # Transaction Welcome Note
        welcome_note_text = "Welcome to FIA ATM!\nPlease select your transaction:"
        self.welcome_note_label = tk.Label(self.master, text=welcome_note_text, bg='#009688', fg='white', font=('Helvetica', 18))
        self.welcome_note_label.pack(pady=(10, 20))

        # Remaining widgets (keypad, buttons, etc.) can be added below

        self.balance_label = tk.Label(self.master, text=f"Balance: ₹{self.user['balance']:.2f}", bg='#009688', fg='white', font=('Helvetica', 14))
        self.balance_label.pack(pady=10)

        self.amount_label = tk.Label(self.master, text="Enter amount:", bg='#009688', fg='white', font=('Helvetica', 14))
        self.amount_label.pack()

        self.amount_entry = tk.Entry(self.master, font=('Helvetica', 14))
        self.amount_entry.pack()

        self.keypad_frame = tk.Frame(self.master, bg='#009688')
        self.keypad_frame.pack(pady=10)

        keypad_buttons = [
            '1', '2', '3',
            '4', '5', '6',
            '7', '8', '9',
            '0', 'Clear', 'Enter'
        ]

        for btn_text in keypad_buttons:
            tk.Button(self.keypad_frame, text=btn_text, font=('Helvetica', 14), width=5, height=2, command=lambda b=btn_text: self.keypad_input(b)).grid(row=keypad_buttons.index(btn_text)//3, column=keypad_buttons.index(btn_text)%3)

        self.withdraw_button = tk.Button(self.master, text="Withdraw", command=self.withdraw_money, bg='#FF5722', fg='white', font=('Helvetica', 14))
        self.withdraw_button.pack(pady=10)

        self.deposit_button = tk.Button(self.master, text="Deposit", command=self.deposit_money, bg='#FF5722', fg='white', font=('Helvetica', 14))
        self.deposit_button.pack(pady=10)

        self.exit_button = tk.Button(self.master, text="Exit", command=self.exit_action_page, bg='#FF5722', fg='white', font=('Helvetica', 14))
        self.exit_button.pack(pady=10)

    def withdraw_money(self):
        # Placeholder logic for withdrawal
        amount = self.amount_entry.get()
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0.")
            if amount > self.user['balance']:
                raise ValueError("Insufficient balance.")
            self.user['balance'] -= amount
            messagebox.showinfo("Withdrawal Success", f"Withdrawal of ₹{amount:.2f} successful.\nNew balance: ₹{self.user['balance']:.2f}")
            self.balance_label.config(text=f"Balance: ₹{self.user['balance']:.2f}")
        except ValueError as e:
            messagebox.showerror("Withdrawal Error", str(e))

    def deposit_money(self):
        # Placeholder logic for deposit
        amount = self.amount_entry.get()
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0.")
            self.user['balance'] += amount
            messagebox.showinfo("Deposit Success", f"Deposit of ₹{amount:.2f} successful.\nNew balance: ₹{self.user['balance']:.2f}")
            self.balance_label.config(text=f"Balance: ₹{self.user['balance']:.2f}")
        except ValueError as e:
            messagebox.showerror("Deposit Error", str(e))

    def exit_action_page(self):
        self.master.destroy()  # Close the transaction page window
        self.verification_gui.master.deiconify()  # Show the verification GUI window

    def keypad_input(self, value):
        # Placeholder function for handling keypad input
        current_value = self.amount_entry.get()
        if value == 'Clear':
            self.amount_entry.delete(0, tk.END)
        elif value == 'Enter':
            # Perform transaction logic here
            pass
        else:
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(tk.END, current_value + value)

def main():
    root = tk.Tk()
    verification_gui = FingerprintVerificationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
