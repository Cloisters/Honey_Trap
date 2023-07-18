import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import time
from pyngrok import ngrok
import pyperclip
import configparser

class AuthTokenWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Enter Authentication Token")
        self.geometry("300x100")

        self.auth_token = tk.StringVar()
        self.auth_token_entry = tk.Entry(self, show="*", width=30, textvariable=self.auth_token)
        self.auth_token_entry.pack(pady=10)

        auth_button = tk.Button(self, text="Continue", command=self.on_continue_clicked)
        auth_button.pack(pady=5)

    def on_continue_clicked(self):
        if self.auth_token.get():
            self.destroy()
        else:
            tk.messagebox.showwarning("Authentication Token", "Please enter your ngrok authentication token.")

class PhpServerGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PHP Server GUI")
        self.geometry("500x300")

        self.php_file_path = ""
        self.server_process = None
        self.auth_token = None

        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        if not self.config.has_section("ngrok"):
            self.config.add_section("ngrok")
            self.save_config()

        self.check_auth_token()

    def save_config(self):
        with open("config.ini", "w") as configfile:
            self.config.write(configfile)

    def check_auth_token(self):
        if self.config.has_option("ngrok", "auth_token"):
            self.auth_token = self.config.get("ngrok", "auth_token")
            self.show_main_page()
        else:
            self.show_auth_token_window()

    def show_auth_token_window(self):
        self.auth_token_window = AuthTokenWindow(self)
        self.wait_window(self.auth_token_window)

        if self.auth_token_window.auth_token.get():
            self.auth_token = self.auth_token_window.auth_token.get()
            self.config.set("ngrok", "auth_token", self.auth_token)
            self.save_config()
            self.show_main_page()
        else:
            tk.messagebox.showinfo("Authentication Token", "Please provide an authentication token.")

    def show_main_page(self):
        self.file_button = tk.Button(self, text="Select PHP File", command=self.select_php_file)
        self.file_button.pack(pady=10)

        self.start_button = tk.Button(self, text="Start Server", command=self.start_server, state=tk.DISABLED)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.status_label = tk.Label(self, text="Server not running", fg="red")
        self.status_label.pack()

        self.ngrok_link_entry = tk.Entry(self, width=40, state=tk.DISABLED)
        self.ngrok_link_entry.pack(pady=5)

        self.copy_button = tk.Button(self, text="Copy ngrok Link", command=self.copy_ngrok_link, state=tk.DISABLED)
        self.copy_button.pack(pady=5)

    def select_php_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PHP Files", "*.php")])
        if file_path:
            self.php_file_path = file_path
            self.start_button.config(state=tk.NORMAL)

    def start_server(self):
        if not self.php_file_path:
            self.status_label.config(text="Please select a PHP file", fg="red")
            return

        self.status_label.config(text="Starting server...", fg="orange")
        self.start_button.config(state=tk.DISABLED)

        def start_php_server():
            self.server_process = subprocess.Popen(["php", "-S", "localhost:8000", self.php_file_path])

        def start_ngrok_tunnel():
            ngrok.set_auth_token(self.auth_token)
            public_url = ngrok.connect(8000)
            self.status_label.config(text=f"Server is running at:\n{public_url}", fg="green")
            self.ngrok_link_entry.config(state=tk.NORMAL)
            self.ngrok_link_entry.delete(0, tk.END)
            self.ngrok_link_entry.insert(0, public_url)
            self.copy_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)

        server_thread = threading.Thread(target=start_php_server)
        server_thread.start()

        time.sleep(2)  # Give some time for the PHP server to start

        ngrok_thread = threading.Thread(target=start_ngrok_tunnel)
        ngrok_thread.start()

    def stop_server(self):
        self.status_label.config(text="Stopping server...", fg="orange")
        self.stop_button.config(state=tk.DISABLED)

        if self.server_process:
            self.server_process.terminate()
            self.server_process = None

        ngrok.kill()
        self.status_label.config(text="Server stopped", fg="red")
        self.start_button.config(state=tk.NORMAL)
        self.ngrok_link_entry.config(state=tk.DISABLED)
        self.copy_button.config(state=tk.DISABLED)

    def copy_ngrok_link(self):
        link = self.ngrok_link_entry.get()
        if link:
            pyperclip.copy(link)

if __name__ == "__main__":
    app = PhpServerGui()
    app.mainloop()
