#!/usr/bin/env python3

import platform
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import datetime
import argparse
import time
from yaml_config import YamlConfig
from llm_service import get_llm_service_instance
import dotenv
dotenv.load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MINS = 25
TIME_FORMAT = "%H:%M:%S"
DATE_FORMAT = "%Y%m%d"

class StickyNote:
    def __init__(self, config_file, template_name, prompt_config):
        self._config = YamlConfig(config_file)
        self._title = self._config.get_config_item_2("config", "title")
        self._frame_size = self._config.get_config_item_2("config", "frame_size")
        self._started = False
        self._tomato_count = 0
        self._llm_service = get_llm_service_instance(prompt_config)

        today = datetime.date.today()
        self.datestr = today.strftime(DATE_FORMAT)
        self.folder = self._config.get_config_item_2("config", "folder")
        self.default_filename = f"diary_{self.datestr}.md"
        self.auto_save_interval = int(self._config.get_config_item_2("config", "save_interval_ms"))
        self.last_modified_time = None
        self.commands = self._config.get_config_item_2("config", "commands")
        self.command_dict = {}
        self._templates = self._config.get_config_item("templates")
        self._template_name = template_name
        self._note_text = self._templates.get(self._template_name, "")

    def adjust_location(self):
        # Get the screen width and height
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()

        # Get the window width and height
        window_width = int(self._frame_size.split('x')[0])
        window_height = int(self._frame_size.split('x')[1].split('+')[0])

        # Calculate the x and y coordinates for the top right corner
        x = screen_width - window_width
        y = 0

        # Set the window position
        self._root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Function to save a sticky note to a custom file
    def save_note(self, prompt=True):
        note_text = self.text_area.get("1.0", tk.END).strip()

        file_name = self.file_name_entry.get().strip()
        file_path = f"{self.folder}/{file_name}"
        if note_text == "":
            messagebox.showwarning("Empty Note", "Cannot save an empty note!")
            return

        if file_name == "":
            messagebox.showwarning("Missing Information", "Please enter file name!")
            return

        # Save the note to the specified file name
        with open(file_path, "w") as file:
            file.write(note_text)
        if prompt:
            messagebox.showinfo("Saved", f"saved to {file_path}")

        self.last_modified_time = os.path.getmtime(file_path)

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(title="Select a File", filetypes=(
            ("Text files", "*.txt"),
            ("Markdown files", "*.md"),
            ("Rst files", "*.rst"),
            ("All files", "*.*")))
        if file_path:
            file_name = file_path.split('/')[-1]
            self.folder = file_path.rsplit('/', 1)[0]
            self.file_name_entry.delete(0, tk.END)
            self.file_name_entry.insert(tk.END, file_name)

            self.load_note()

    # Function to load a sticky note from a file
    def load_note(self):
        file_name = self.file_name_entry.get().strip()
        file_path = f"{self.folder}/{file_name}"
        if file_name == "":
            messagebox.showwarning("Missing File Name", "Please enter a file name to load!")
            return

        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                self._note_text = file.read()
                #messagebox.showinfo("Saved", f"loaded from {file_path}")

            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, "\n".join(self._note_text.split('\n')))
        else:
            messagebox.showwarning("File Not Found", f"No note found with the name {file_name}")

    def auto_save(self):
        file_name = self.file_name_entry.get().strip()
        if self.is_already_modified():
            response = messagebox.askyesno("File changed", f"Something changed of {file_name}, overwrite?")
            if response:
                self.save_note(True)
        else:
            self.save_note(False)  # Save the note
        self._root.after(self.auto_save_interval, self.auto_save)

    def is_already_modified(self):
        file_name = self.file_name_entry.get().strip()
        file_path = f"{self.folder}/{file_name}"
        if os.path.exists(file_name):
            current_modified_time = os.path.getmtime(file_path)
            if self.last_modified_time and current_modified_time > self.last_modified_time:
                self.last_modified_time = current_modified_time
                return True
            else:
                return False
        return False

    def execute_command(self):
        selected_command = self.command_var.get()
        if selected_command in self.command_dict:
            command = self.command_dict[selected_command]
            os_type = platform.system()
            print(f"Executing command: {command} on {os_type}")
            if command.get("new_window"):
                if os_type == 'Windows':
                    subprocess.Popen(['start', 'cmd', '/k', command], shell=True)
                elif os_type == 'Darwin':
                    subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "{command}"'])
                else:
                    subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"{command}; exec bash"])
            else:
                os.system(self.command_dict[selected_command])
        else:
            messagebox.showwarning("Invalid Command", f"Command {selected_command} not found.")

    def load_commands(self):
        commands = self._config.get_config_item_2("config", "commands")
        result = []
        for command in commands:
            self.command_dict[command.get("name")] = command.get("shell")
            result.append(command.get("name"))
        return result

    def get_default_command(self):
        return self._config.get_config_item_2("config", "default_command")


    def quit_app(self):
        self._root.destroy()

    def on_template_select(self, event):
        selected_template = self.template_var.get()
        response = messagebox.askyesno("Load template", f"Will replace current note?")
        if response:
            self._note_text = self._templates.get(selected_template, "")
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, f"# {self.datestr}\n\n{self._note_text}")

            if not self.file_name_entry.get().startswith(selected_template):
                self.file_name_entry.delete(0, tk.END)
                self.file_name_entry.insert(tk.END, f"{selected_template}_{self.datestr}.md")

    def create_time_box(self, frame, label):
        return tk.Entry(frame, width=4,font=("Arial",18,""), justify='center', textvariable=label)

    def set_time(self, hour=0, min=DEFAULT_MINS, sec=0):
        self._hour.set("{0:2d}".format(hour))
        self._minute.set("{0:2d}".format(min))
        self._second.set("{0:2d}".format(sec))

    def reset(self):
        self._started = False
        self.set_time()

    def pause(self):
        self._started = False

    def get_hour_min_sec(self, left_seconds):

        mins,secs = divmod(left_seconds, 60)

        hours=0
        if mins > 60:
            hours, mins = divmod(mins, 60)
        return hours, mins, secs

    def countdown(self):
        self._started = True
        try:
            left_seconds = int(self._hour.get())*3600 + int(self._minute.get())*60 + int(self._second.get())
        except:
            messagebox.showwarning('hehe', 'Invalid Input Value!')

        while self._started:

            hours, mins, secs = self.get_hour_min_sec(left_seconds)
            self.set_time(hours, mins, secs)

            self._root.update()
            time.sleep(1)

            if (left_seconds == 0):
                self._tomato_count += 1
                response = messagebox.askyesnocancel('haha', "Have a rest at {} for {} tomatoes?".format( datetime.datetime.now().strftime(TIME_FORMAT),self._tomato_count))
                if response:
                    self.set_time(0, 5, 0)
                    left_seconds = 300
                elif response == False:
                    self.set_time(0, 25, 0)
                    left_seconds = 1500
                else:
                    break

            left_seconds -= 1

    def show_aigc_dialog(self):
            # Create a new top-level window
            dialog = tk.Toplevel(self._root)
            dialog.title("AI for sticky note")

            dialog_width = 300
            dialog_height = 200

            screen_width = self._root.winfo_screenwidth()
            screen_height = self._root.winfo_screenheight()

            x = (screen_width - dialog_width) // 2
            y = (screen_height - dialog_height) // 2

            dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

            # Create a listbox
            listbox = tk.Listbox(dialog, height=4)
            listbox.pack(pady=10)

            # Example list items
            items = ["Generate", "Proofread", "Polish", "Translate"]
            for item in items:
                listbox.insert(tk.END, item)

            # Create an entry for hint message
            hint_label = tk.Label(dialog, text="Hint Message:")
            hint_label.pack()
            hint_entry = tk.Entry(dialog, width=30)
            hint_entry.pack(pady=5)

            def on_yes():
                selected_index = listbox.curselection()
                if selected_index:
                    selected_item = listbox.get(selected_index)
                    hint_message = hint_entry.get()
                    print(f"Selected item: {selected_item}, Hint message: {hint_message}")
                    # You can add your AIGC logic here
                dialog.destroy()

            def on_cancel():
                dialog.destroy()

            # Create Yes and Cancel buttons
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=10)
            yes_button = tk.Button(button_frame, text="Yes", command=on_yes)
            yes_button.pack(side=tk.LEFT, padx=5)
            cancel_button = tk.Button(button_frame, text="Cancel", command=on_cancel)
            cancel_button.pack(side=tk.LEFT, padx=5)

    def initialize(self):
        # Create the main window
        self._root = tk.Tk()
        self._style = ttk.Style()
        self._style.theme_use('alt')
        self._root.attributes('-alpha', 0.9)  # 设置窗口透明度
        self._root.title(self._title)

        self._root.grid_rowconfigure(2, weight=1)
        self._root.grid_columnconfigure(0, weight=1)

        self.adjust_location()

        # row 0: Template selection combobox
        self.template_frame = tk.Frame(self._root)
        self.template_frame.grid(row=0, column=0, padx=10, pady=2, sticky="ew")

        self.template_label = tk.Label(self.template_frame, text="Template: ")
        self.template_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.template_var = tk.StringVar(self._root, self._template_name)
        self.template_choices = list(self._templates.keys())
        template_box = ttk.Combobox(self.template_frame, textvariable=self.template_var, values=self.template_choices, width=20)
        template_box.grid(row=0, column=1, padx=5)
        template_box.bind("<<ComboboxSelected>>", self.on_template_select)

        self._hour = tk.StringVar()
        self._minute = tk.StringVar()
        self._second = tk.StringVar()

        hour_box = self.create_time_box(self.template_frame, self._hour)
        hour_box.grid(row=0, column=2, padx=5)

        minute_box = self.create_time_box(self.template_frame, self._minute)
        minute_box.grid(row=0, column=3, padx=5)

        second_box = self.create_time_box(self.template_frame, self._second)
        second_box.grid(row=0, column=4, padx=5)

        self.set_time()

        # row 1: File name input field (one line)
        self.file_name_frame = tk.Frame(self._root)
        self.file_name_frame.grid(row=1, column=0, padx=10, pady=2, sticky="ew")

        self.file_name_label = tk.Label(self.file_name_frame, text="File name: ")
        self.file_name_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.file_name_entry = tk.Entry(self.file_name_frame, width=20)
        self.file_name_entry.grid(row=0, column=1, padx=5, pady=2)
        self.file_name_entry.insert(tk.END, self.default_filename)

        start_button = tk.Button(self.file_name_frame, text="start",  bd='5', fg="green", command=self.countdown)
        start_button.grid(row=0, column=3, padx=3)

        stop_button = tk.Button(self.file_name_frame, text="stop",  bd='5', fg="blue",command=self.pause)
        stop_button.grid(row=0, column=4, padx=3)

        reset_button = tk.Button(self.file_name_frame, text="reset",  bd='5', fg="red", command=self.reset)
        reset_button.grid(row=0, column=5, padx=3)

        # row 2: Text area to write notes (adjustable size)
        self.text_area = tk.Text(self._root, height=15, width=60, wrap=tk.WORD, bg='#9acd32', fg='#333333', font=('Arial', 14))
        self.scrollbar = tk.Scrollbar(self._root, command=self.text_area.yview)
        self.text_area.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=2, column=1, sticky="ns")
        self.text_area.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.text_area.insert(tk.END, f"# {self.datestr}")
        self.text_area.focus_set()

        file_path = f"{self.folder}/{self.default_filename}"

        if os.path.exists(file_path):
            self.load_note()
        else:
            if not self._note_text:
                messagebox.showwarning("Empty Note", "template {self.}")
            self.text_area.insert(tk.END, f"\n\n{self._note_text}")

        # Buttons for saving and loading notes
        self.button_frame = tk.Frame(self._root)
        self.button_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        load_button = tk.Button(self.button_frame, text="Load", bd='2', fg="blue", command=self.open_file_dialog)
        load_button.grid(row=0, column=0, padx=2)

        save_button = tk.Button(self.button_frame, text="Save", bd='2', fg="blue", command=self.save_note)
        save_button.grid(row=0, column=1, padx=2)

        self.command_var = tk.StringVar(self._root, self.get_default_command())
        self.command_choices = self.load_commands()
        command_box = ttk.Combobox(self.button_frame, textvariable=self.command_var, values=self.command_choices, width=15)
        command_box.grid(row=0, column=2, padx=2)

        execute_button = tk.Button(self.button_frame, text="Execute", bd='2', fg="green", command=self.execute_command)
        execute_button.grid(row=0, column=4, padx=2)

        aigc_button = tk.Button(self.button_frame, text="AIGC", bd='2', fg="red", command=self.show_aigc_dialog)
        aigc_button.grid(row=0, column=5, padx=2)

        quit_button = tk.Button(self.button_frame, text="Quit", bd='2', fg="black", command=self.quit_app)
        quit_button.grid(row=0, column=6, padx=2)
        self._root.attributes("-topmost", True)

        self._root.after(self.auto_save_interval, self.auto_save)  # Call auto_save function every n ms

        self._root.configure(bg='#9acd32')
        # Start the GUI loop
        self._root.mainloop()

        return self._root

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Sticky Note Application")
    parser.add_argument('-f', '--file', action='store', dest='file', default="./etc/sticky_note.yaml", help='Path to the YAML configuration file')
    parser.add_argument('-t', '--template', action='store', dest='template', default="diary", help='specify template name')
    parser.add_argument('-p', '--prompt_config', action='store', dest='prompt_config', default="./etc/prompt_template.yaml", help='specify template name')

    args = parser.parse_args()

    app = StickyNote(args.file, args.template, args.prompt_config)
    app.initialize()

