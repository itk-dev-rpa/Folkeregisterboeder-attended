import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


ENTRY_FIELDS = (
    ("Cpr", "cpr", "ddmmyyxxxx"),
    ("eFlyt sagsnummer", "case_number", "xxxxxxxx"),
    ("Flyttedato", "move_date", "dd-mm-åååå"),
    ("Anmeldelsesdato", "register_date", "dd-mm-åååå")
)

BUTTONS = (
    ("Lav Nova sag", "create_case"),
    ("Hent eFlyt oplysninger", "get_eflyt_info"),
    ("Dan brev i Nova", "create_letter"),
    ("Dan faktura i SAP", "create_invoice"),
    ("Journaliser faktura i Nova", "journalize_invoice"),
    ("Næste sag", "next_case")
)


class App():
    def __init__(self):
        self.window = tk.Tk()

        self.window.title("Login App")
        self.window.geometry("400x300")

        self.login_screen()

    def login_screen(self):
        """Creates the login screen"""
        # Clear any existing widgets
        for widget in self.window.winfo_children():
            widget.destroy()

        # Create and place username and password labels and entry fields
        tk.Label(self.window, text="Username:").pack(pady=10)
        self.username_entry = tk.Entry(self.window)
        self.username_entry.pack()

        tk.Label(self.window, text="Password:").pack(pady=10)
        self.password_entry = tk.Entry(self.window, show="*")
        self.password_entry.pack()

        # Create login button
        login_button = tk.Button(self.window, text="Login", command=self.check_login)
        login_button.pack(pady=20)

    def check_login(self):
        """Check if the login credentials are correct"""
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Dummy login validation
        if True or username == "admin" and password == "password":
            self.show_new_view()  # Go to the next view if login is correct
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def show_new_view(self):
        """Creates the new view with 5 text inputs and 5 buttons"""
        # Clear the login screen widgets
        for widget in self.window.winfo_children():
            widget.destroy()

        # Create text inputs
        self.entries = {}
        text_frame = tk.Frame(self.window)
        text_frame.pack()

        for i, ef in enumerate(ENTRY_FIELDS):
            tk.Label(text_frame, text=ef[0]).grid(row=i, column=0, sticky='w')
            entry = tk.StringVar(value=ef[2])
            tk.Entry(text_frame, textvariable=entry).grid(row=i, column=1)
            self.entries[ef[1]] = entry

        ttk.Separator(self.window, orient="horizontal").pack(fill='x')

        # Create buttons
        self.buttons = {}
        self.button_labels = {}
        button_frame = tk.Frame(self.window)
        button_frame.pack()
        for i, b in enumerate(BUTTONS):
            button = tk.Button(button_frame, text=b[0], command=lambda v=b[1]: self.button_action(v))
            button.grid(row=i, column=0, pady=2, sticky='we')
            label = tk.StringVar(value="Afventer")
            tk.Label(button_frame, textvariable=label).grid(row=i, column=1, sticky='w')

            if i != 0:
                button.config(state="disabled")

            self.buttons[b[1]] = button
            self.button_labels[b[1]] = label

    def button_action(self, button_name):
        """Action for when a button is pressed"""
        inc = getattr(self, button_name)()
        if inc:
            self.increment_step(button_name)

    def create_case(self):
        print("Create case!")
        return True

    def get_eflyt_info(self):
        print("Get info!")
        return True

    def create_letter(self):
        print("Create letter!")
        return True

    def create_invoice(self):
        print("Create invoice!")
        return True

    def journalize_invoice(self):
        print("Journalize invoice!")
        return True

    def next_case(self):
        print("Next case!")
        self.show_new_view()
        return False

    def increment_step(self, current_step):
        self.buttons[current_step].config(state='disabled')
        self.button_labels[current_step].set("Done")

        next_step = None
        for i, step in enumerate(BUTTONS[:-1]):
            if step[1] == current_step:
                next_step = BUTTONS[i+1][1]

        self.buttons[next_step].config(state='active')


if __name__ == "__main__":
    app = App()
    app.window.mainloop()
