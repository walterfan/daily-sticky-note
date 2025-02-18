#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import datetime
import argparse

# refer to https://pyyaml.org/wiki/PyYAMLDocumentation
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class YamlConfig:
    def __init__(self, yaml_file):
        self._config_file = yaml_file
        self._config_data = self.read_config()

    def read_config(self):
        f = open(self._config_file, 'r', encoding='UTF-8')
        config_data = load(f, Loader=Loader)
        f.close()
        return config_data

    def get_config_data(self):
        return self._config_data

    def get(self, name):
        return self._config_data.get(name)

    def get_config_section(self, section):
        return self._config_data.get(section, {})

    def get_config_item(self, category, item):
        return self._config_data.get(category, {}).get(item)

    def __str__(self):
        return dump(self._config_data, Dumper=Dumper)

class StickyNote:
    def __init__(self, yaml_config, template_name):
        self.config = yaml_config
        self.title = self.config.get_config_item("config", "title")
        self.note_text = self.config.get_config_item("templates", template_name)

        today = datetime.date.today()
        self.datestr = today.strftime("%Y-%m-%d")
        self.folder = os.getenv("NOTE_FOLDER", self.config.get_config_item("config", "folder"))
        self.default_filename = f"diary_{self.datestr}.md"
        self.auto_save_interval = int(self.config.get_config_item("config", "save_interval_ms"))
        self.last_modified_time = None
        self.template_name = template_name
        self.commands = self.config.get_config_section("commands")
        self.command_dict = {}
        self.templates = self.config.get_config_section("templates")
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
            messagebox.showinfo("Saved", f"saved successfully of {file_name}")

        self.last_modified_time = os.path.getmtime(file_path)

    # Function to load a sticky note from a file
    def load_note(self):
        file_name = self.file_name_entry.get().strip()
        if file_name == "":
            messagebox.showwarning("Missing File Name", "Please enter a file name to load!")
            return
        file_path = f"{self.folder}/{file_name}"
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                self.note_text = file.read()

            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, "\n".join(self.note_text.split('\n')))
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
        self.root.after(self.auto_save_interval, self.auto_save)

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
        print(f"Executing command: {selected_command}")
        if selected_command in self.command_dict:
            os.system(self.command_dict[selected_command])
        else:
            messagebox.showwarning("Invalid Command", f"Command {selected_command} not found.")

    def load_commands(self):
        commands = self.config.get_config_item("config", "commands")
        result = []
        for command in commands:
            self.command_dict[command.get("name")] = command.get("shell")
            result.append(command.get("name"))
        return result

    def get_default_command(self):
        command = self.config.get_config_item("config", "default_command")
        self.command_dict[command.get("name")] = command.get("shell")
        return command.get("name")

    def quit_app(self):
        self.root.destroy()

    def on_template_select(self, event):
        selected_template = self.template_var.get()
        response = messagebox.askyesno("Load template", f"Will change current note, overwrite?")
        if response:
            self.note_text = self.templates.get(selected_template, "")
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, f"# {self.datestr}\n\n{self.note_text}")

    def initialize(self):
        # Create the main window
        self.root = tk.Tk()
        self.root.attributes('-alpha', 0.9)  # 设置窗口透明度
        self.root.title(self.title)

        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Template selection combobox
        self.template_frame = tk.Frame(self.root)
        self.template_frame.grid(row=0, column=0, padx=10, pady=2, sticky="ew")

        self.template_label = tk.Label(self.template_frame, text="Note Template: ")
        self.template_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.template_var = tk.StringVar(self.root, self.template_name)
        self.template_choices = list(self.templates.keys())
        template_box = ttk.Combobox(self.template_frame, textvariable=self.template_var, values=self.template_choices, width=30)
        template_box.grid(row=0, column=1, padx=5)
        template_box.bind("<<ComboboxSelected>>", self.on_template_select)

        # File name input field (one line)
        self.file_name_frame = tk.Frame(self.root)
        self.file_name_frame.grid(row=1, column=0, padx=10, pady=2, sticky="ew")

        self.file_name_label = tk.Label(self.file_name_frame, text="Note File:     ")
        self.file_name_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.file_name_entry = tk.Entry(self.file_name_frame, width=30)
        self.file_name_entry.grid(row=0, column=1, padx=5, pady=2)
        self.file_name_entry.insert(tk.END, self.default_filename)

        # Text area to write notes (adjustable size)
        self.text_area = tk.Text(self.root, height=15, width=60, wrap=tk.WORD, bg='#9acd32', fg='#333333', font=('Arial', 14))
        self.scrollbar = tk.Scrollbar(self.root, command=self.text_area.yview)
        self.text_area.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=2, column=1, sticky="ns")
        self.text_area.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.text_area.insert(tk.END, f"# {self.datestr}")
        self.text_area.focus_set()

        if os.path.exists(f"{self.folder}/{self.default_filename}"):
            self.load_note()
        else:
            self.text_area.insert(tk.END, f"\n\n{self.note_text}")

        # Buttons for saving and loading notes
        self.button_frame = tk.Frame(self.root)
        self.button_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        save_button = tk.Button(self.button_frame, text="Save Note", command=self.save_note)
        save_button.grid(row=0, column=0, padx=5)

        load_button = tk.Button(self.button_frame, text="Load Note", command=self.load_note)
        load_button.grid(row=0, column=1, padx=5)

        self.command_var = tk.StringVar(self.root, self.get_default_command())
        self.command_choices = self.load_commands()
        command_box = ttk.Combobox(self.button_frame, textvariable=self.command_var, values=self.command_choices, width=8)
        command_box.grid(row=0, column=2, padx=5)

        execute_button = tk.Button(self.button_frame, text="Execute", command=self.execute_command)
        execute_button.grid(row=0, column=3, padx=5)

        quit_button = tk.Button(self.button_frame, text="Quit", command=self.quit_app)
        quit_button.grid(row=0, column=4, padx=5)
        self.root.attributes("-topmost", True)

        self.root.after(self.auto_save_interval, self.auto_save)  # Call auto_save function every n ms

        self.root.configure(bg='#9acd32')
        # Start the GUI loop
        self.root.mainloop()

        return self.root

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Sticky Note Application")
    parser.add_argument('-f', '--file', action='store', dest='file', default=os.path.join(CURRENT_DIR, "sticky_note.yaml"), help='Path to the YAML configuration file')
    parser.add_argument('-t', '--template', action='store', dest='template', default="pdca", help='specify template name')

    args = parser.parse_args()

    yaml_file = args.file
    yaml_config = YamlConfig(yaml_file)

    app = StickyNote(yaml_config, args.template)
    app.initialize()

