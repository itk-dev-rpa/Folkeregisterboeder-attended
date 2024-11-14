from datetime import datetime
import os
import tkinter as tk
from tkinter import ttk, messagebox

import dotenv

from folkeregisterboeder_attended import eflyt_process, nova_process, sap_process, word_process
from folkeregisterboeder_attended.task import Task


ENTRY_FIELDS = (
    # Label, id, placeholder
    ("Cpr", "cpr", "8412893981"),  # TODO
    ("eFlyt sagsnummer", "case_number", "XXXXXX"),
    ("Flyttedato", "move_date", "01-06-2024"),  # TODO
    ("Anmeldelsesdato", "register_date", "20-06-2024")  # TODO
)

STEPS = (
    # Label, id
    ("Lav Nova sag", "create_case"),
    ("Hent eFlyt oplysninger", "get_eflyt_info"),
    ("Dan brev i Nova", "create_letter"),
    ("Dan faktura i SAP", "create_invoice")
)


class App():
    def __init__(self):
        self.window = tk.Tk()

        self.window.title("Folkeregisterbøder")
        self.window.geometry("400x450")

        self.login_screen()

        self.nova_access = nova_process.create_nova_access()

    def login_screen(self):
        """Creates the login screen"""
        # Clear any existing widgets
        for widget in self.window.winfo_children():
            widget.destroy()

        # Create and place username and password labels and entry fields
        tk.Label(self.window, text="eFlyt brugernavn:").pack(pady=10)
        self.username_entry = tk.Entry(self.window)
        self.username_entry.pack()

        tk.Label(self.window, text="eFlyt kodeord:").pack(pady=10)
        self.password_entry = tk.Entry(self.window, show="*")
        self.password_entry.pack()

        # Create login button
        login_button = tk.Button(self.window, text="Login", command=self.check_login)
        login_button.pack(pady=20)

    def check_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        self.eflyt_browser = eflyt_process.login(username, password)
        sap_process.get_sap_session()
        self.work_view()

    def work_view(self):
        # Clear the login screen widgets
        for widget in self.window.winfo_children():
            widget.destroy()

        # Create text inputs
        self.entries = {}
        entry_frame = tk.Frame(self.window)
        entry_frame.pack()

        for i, ef in enumerate(ENTRY_FIELDS):
            tk.Label(entry_frame, text=ef[0]).grid(row=i, column=0, sticky='w')
            entry = tk.StringVar(value=ef[2])
            tk.Entry(entry_frame, textvariable=entry).grid(row=i, column=1)
            self.entries[ef[1]] = entry

        ttk.Separator(self.window, orient="horizontal").pack(fill='x')

        # Create buttons
        self.buttons = {}
        self.button_labels = {}
        button_frame = tk.Frame(self.window)
        button_frame.pack()
        for i, step in enumerate(STEPS):
            button = tk.Button(button_frame, text=step[0], command=lambda v=step[1]: self.button_action(v))
            button.pack(pady=2, fill='x')

            if i != 0:
                button.config(state="disabled")

            self.buttons[step[1]] = button

        tk.Button(button_frame, text="Nulstil", command=self.reset).pack(pady=2)

        tk.Button(button_frame, text="Journalisering", command=self.show_journalize_window).pack(pady=2)

        # Create text area
        text_frame = tk.Frame(self.window)
        text_frame.pack()

        self.text_area = tk.Text(text_frame, state='disabled', wrap='none')

        # Add scroll bars to text area
        text_yscroll = ttk.Scrollbar(text_frame, orient='vertical', command=self.text_area.yview)
        text_yscroll.pack(side='right', fill='y')
        self.text_area.configure(yscrollcommand=text_yscroll.set)

        text_xscroll = ttk.Scrollbar(text_frame, orient='horizontal', command=self.text_area.xview)
        text_xscroll.pack(side='bottom', fill='x')
        self.text_area.configure(xscrollcommand=text_xscroll.set)

        self.text_area.pack(fill='both')

    def button_action(self, step_id):
        """Action for when a button is pressed"""
        inc = getattr(self, step_id)()
        if inc:
            self.increment_step(step_id)

    def read_inputs(self):
        # TODO: Validation
        cpr = self.entries['cpr'].get()
        move_date = datetime.strptime(self.entries['move_date'].get(), "%d-%m-%Y")
        register_date = datetime.strptime(self.entries['register_date'].get(), "%d-%m-%Y")
        case_number = self.entries['case_number'].get()
        self.task = Task(cpr=cpr, move_date=move_date, register_date=register_date, eflyt_case_number=case_number)

    def create_case(self):
        self.read_inputs()
        self.print_text("Opretter sag i Nova...")
        self.task.nova_case_uuid, self.task.nova_case_number = nova_process.create_case(self.task.cpr, nova_access=self.nova_access)
        self.print_text(f"Sag oprettet: {self.task.nova_case_number}")
        return True

    def get_eflyt_info(self):
        self.print_text("Henter adresse og journal fra eFlyt...")
        self.task.address, journal_path = eflyt_process.search_case_info(self.eflyt_browser, self.task.eflyt_case_number)

        if journal_path is None:
            self.print_text("Kunne ikke hente eflyt data efter 3 forsøg. Sagen må behandles manuelt.")
            self.print_text("Tryk 'Nulstil' for at gå til næste sag.")
            return

        self.print_text(f"Adresse: {self.task.address}")

        self.print_text("Vedhæfter journal til sag i Nova...")
        # TODO
        # with open(journal_path, 'rb') as file:
        #     nova_process.add_journal_to_case(self.case_uuid, file, self.nova_access)
        os.remove(journal_path)

        self.print_text("Journal vedhæftet sag i Nova")
        return True

    def create_letter(self):
        self.print_text("Danner brev i Nova...")
        address_lines = nova_process.get_address_lines(self.task.cpr, self.nova_access)
        result_path = word_process.create_letter(self.task, address_lines)

        with open(result_path, 'rb') as file:
            self.task.document_uuid = nova_process.add_letter_to_case(self.task.nova_case_uuid, file, self.nova_access)
        os.remove(result_path)

        self.print_text("Brev dannet i Nova")
        self.print_text("Husk at sende brevet manuelt")
        return True

    def create_invoice(self):
        self.print_text("Danner faktura i SAP...")
        sap_process.create_invoice(self.task.cpr, self.task.move_date, self.task.register_date, self.task.address)
        self.print_text("Faktura dannet i SAP")
        self.print_text("Udfører straksfakturering...")
        sap_process.do_immediate_invoicing(self.task.cpr)
        self.print_text("Straksfakturering udført")
        return False

    def increment_step(self, current_step):
        self.buttons[current_step].config(state='disabled')

        next_step = None
        for i, step in enumerate(STEPS[:-1]):
            if step[1] == current_step:
                next_step = STEPS[i+1][1]

        self.buttons[next_step].config(state='active')

    def print_text(self, text: str) -> None:
        """Appends text to the text area.
        Is used to replace the functionality of sys.stdout.write (print).

        Args:
            string: The string to append.
        """
        # Insert text at the end
        self.text_area.configure(state='normal')
        self.text_area.insert('end', text+"\n")

        # If the number of lines are above 1000 delete 10 lines from the top
        num_lines = int(self.text_area.index('end').split('.', maxsplit=1)[0])
        if num_lines > 1000:
            self.text_area.delete("1.0", "10.0")

        # Scroll to end
        self.text_area.see('end')
        self.text_area.configure(state='disabled')
        self.text_area.update_idletasks()

    def reset(self):
        self.task = None

        for ef in ENTRY_FIELDS:
            entry = self.entries[ef[1]]
            entry.set(ef[2])

        self.buttons[STEPS[0][1]].config(state='active')
        for _, step in STEPS[1:]:
            self.buttons[step].config(state='disabled')

        self.print_text("Nulstillet")

    def show_journalize_window(self):
        popup = tk.Toplevel(self.window)
        popup.geometry("300x150")

        tk.Label(popup, text="Husk at journalisering af faktura først kan ske tidligst 5 minutter efter fakturering.", wraplength=250).pack()

        tk.Label(popup, text="CPR").pack()

        text_input = tk.Entry(popup, width=30)
        text_input.pack()

        def send_action():
            cpr_input = text_input.get()

            nova_case = nova_process.get_case(cpr_input, self.nova_access)

            if not nova_case:
                messagebox.showerror("Fejl", "Kunne ikke finde sag i Nova på det givne cpr-nummer.")
                return

            invoice_path = sap_process.save_invoice(cpr_input, datetime.now())
            with open(invoice_path, 'rb') as file:
                nova_process.add_invoice_to_case(nova_case.uuid, file, self.nova_access)
            os.remove(invoice_path)

        send_button = tk.Button(popup, text="Journaliser faktura", command=send_action)
        send_button.pack(pady=2)


if __name__ == "__main__":
    dotenv.load_dotenv()
    app = App()
    app.window.mainloop()
