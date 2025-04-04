import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# Sample tasks, format: {(day, hour): "task content"}
SAVE_FILE = "weekly_schedule.json"

class Autodo:
    def __init__(self, title, geometry, SAVE_FILE):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry = geometry
        self.SAVE_FILE = SAVE_FILE
        self.DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        self.HOURS = [f"{h}:00" for h in range(5, 24)]
        self.entries = {}
        self.saved_schedule = {}

    def load_schedule(self):
        if os.path.exists(self.SAVE_FILE):
            with open(self.SAVE_FILE, 'r') as f:
                data = json.load(f)
                return {tuple(key.split('|')): task for key, task in data.items()}
        else:
            return {}  # Default empty schedule

    def save_schedule(self):
        data = {}
        for (day, hour), entry in self.entries.items():
            content = entry.get().strip()
            if content:  # Only save non-empty tasks
                data[(day, hour)] = content
        # Note: JSON doesn't support tuple keys, so convert to strings
        data_str_keys = {f"{day}|{hour}": task for (day, hour), task in data.items()}
        with open(SAVE_FILE, 'w') as f:
            json.dump(data_str_keys, f)
        self.saved_schedule = {
            (day, hour): entry.get().strip()
            for (day, hour), entry in self.entries.items()
            if entry.get().strip()
        }

    def open_add_task_window(self):
        window = tk.Toplevel(self.root)
        window.title("Add New Task")

        tk.Label(window,text="Currently not implemented, cool functions coming soon, stay tuned!").grid(row=0,column=0,columnspan=2)
        tk.Label(window, text="Task Name").grid(row=1, column=0)
        tk.Label(window, text="Estimated Duration (hours)").grid(row=2, column=0)
        tk.Label(window, text="Start time (e.g., Monday 8:00)").grid(row=3, column=0)
        tk.Label(window, text="Deadline (e.g., Monday 14:00)").grid(row=4, column=0)

        name_entry = tk.Entry(window)
        duration_entry = tk.Entry(window)
        start_time_entry=tk.Entry(window)
        ddl_entry = tk.Entry(window)

        name_entry.grid(row=1, column=1)
        duration_entry.grid(row=2, column=1)
        start_time_entry.grid(row=3,column=1)
        ddl_entry.grid(row=4, column=1)

        def submit():
            name = name_entry.get().strip()

            
            ddl = ddl_entry.get().strip()
            if "|" in ddl:
                day, hour = ddl.split("|")
            elif " " in ddl:
                day, hour = ddl.split()
            else:
                tk.messagebox.showerror("Format Error", "Deadline format should be 'Monday 14:00'")
                return

            if (day, hour) in self.entries:
                self.entries[(day, hour)].delete(0, tk.END)
                self.entries[(day, hour)].insert(0, name)
                window.destroy()
            else:
                tk.messagebox.showerror("Invalid Time", f"No time slot found for {day} {hour}")

            raise NotImplementedError("More intelligent task-adding coming, stay tuned!")

        submit_btn = tk.Button(window, text="Add Task", command=submit)
        submit_btn.grid(row=5, columnspan=2)

    def open_help_window(self):
        window = tk.Toplevel(self.root)
        window.title("Help")

        help_text = """
How to Use:

1. Enter task content directly in the schedule table
2. Click 'Actions' -> 'Save Schedule' to save your current plan
3. Click 'Add Task' to open a window for adding task name and time
4. Supported formats: Monday 14:00 or Monday|14:00
5. Data is saved in a JSON file and will be loaded automatically next time
"""

        text_widget = tk.Text(window, wrap="word", width=60, height=15)
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")
        text_widget.pack(padx=10, pady=10)

    def has_unsaved_changes(self):
        current = {
            (day, hour): entry.get().strip()
            for (day, hour), entry in self.entries.items()
            if entry.get().strip()
        }
        return current != self.saved_schedule

    def on_close(self):
        if self.has_unsaved_changes():
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "There are unsaved changes. Do you want to save them before exiting?\n\nYes = Save and Exit\nNo = Exit without Saving\nCancel = Stay"
            )
            if result is True:
                self.save_schedule()
                self.root.destroy()
            elif result is False:
                self.root.destroy()
            else:
                pass  # Cancelled, do nothing
        else:
            self.root.destroy()

    def create_week_schedule(self):
        root = self.root
        SCHEDULE = self.load_schedule()
        self.saved_schedule = SCHEDULE

        # Create weekday headers
        for col, day in enumerate([''] + self.DAYS):
            label = tk.Label(root, text=day, borderwidth=1, relief="ridge", width=15, anchor='center')
            label.grid(row=0, column=col, sticky='nsew')

        # Create hourly rows and task cells
        for row, hour in enumerate(self.HOURS, start=1):
            # Hour label
            label = tk.Label(root, text=hour, borderwidth=1, relief="ridge", width=10)
            label.grid(row=row, column=0, sticky='nsew')

            # Day entries
            for col, day in enumerate(self.DAYS, start=1):
                cell_key = (day, hour)
                task = SCHEDULE.get(cell_key, "")
                entry = tk.Entry(root, width=18, justify='center')
                entry.insert(0, task)
                entry.grid(row=row, column=col, sticky='nsew')
                self.entries[(day, hour)] = entry

        # Make columns and rows auto-resize
        for i in range(8):
            root.grid_columnconfigure(i, weight=1)
        for i in range(len(self.HOURS) + 1):
            root.grid_rowconfigure(i, weight=1)

        # Save button
        save_button = tk.Button(root, text="Save Schedule", command=self.save_schedule)
        save_button.grid(row=len(self.HOURS) + 1, column=0, columnspan=2, sticky='nsew')

        # Create top menu bar
        menubar = tk.Menu(root)
        root.config(menu=menubar)

        # Add 'Actions' menu
        action_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Actions", menu=action_menu)

        # Add menu items
        action_menu.add_command(label="Save Schedule", command=self.save_schedule)
        action_menu.add_command(label="Add Task", command=self.open_add_task_window)
        action_menu.add_command(label="Help", command=self.open_help_window)

        # Intercept close button to check for unsaved changes
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

if __name__ == "__main__":
    autodo = Autodo(title="Weekly Schedule", geometry="1024x720", SAVE_FILE="weekly_schedule.json")
    autodo.create_week_schedule()
    autodo.root.mainloop()
