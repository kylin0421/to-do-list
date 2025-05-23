import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import re
from datetime import datetime

# Constants
SAVE_FILE = "weekly_schedule.json"

class Autodo:
    def __init__(self, title, geometry, SAVE_FILE):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(geometry)  # Fixed: Changed from assignment to method call
        self.SAVE_FILE = SAVE_FILE
        self.DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        self.HOURS = [f"{h}:00" for h in range(5, 24)]
        self.entries = {}
        self.task_frames = {}  # Store frames for tasks
        self.task_details = {}  # Dictionary to store task details
        self.saved_schedule = {}
        
        # Apply theme
        self.style = ttk.Style()
        self.current_theme = "light"  # Default theme
        self.apply_theme(self.current_theme)
        
        # Task priority colors
        self.priority_colors = {
            "high": "#ffcccc",  # Light red
            "medium": "#ffffcc",  # Light yellow
            "low": "#ccffcc",  # Light green
            "completed": "#e6e6e6"  # Light gray
        }
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()

    def apply_theme(self, theme_name):
        """Apply the selected theme to the application"""
        if theme_name == "light":
            self.style.theme_use("default")
            bg_color = "#f0f0f0"
            fg_color = "black"
        else:  # dark theme
            try:
                # Try using a dark theme if available
                self.style.theme_use("clam")
                bg_color = "#333333"
                fg_color = "white"
            except tk.TclError:
                # Fallback to default with dark colors
                self.style.theme_use("default")
                bg_color = "#333333"
                fg_color = "white"
        
        self.root.configure(bg=bg_color)
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color)
        self.style.configure("TButton", background=bg_color)
        self.current_theme = theme_name

    def setup_shortcuts(self):
        """Set up keyboard shortcuts for the application"""
        self.root.bind("<Control-s>", lambda e: self.save_schedule())
        self.root.bind("<Control-q>", lambda e: self.on_close())
        self.root.bind("<F1>", lambda e: self.open_help_window())
        self.root.bind("<Control-f>", lambda e: self.open_search_window())
        self.root.bind("<Control-n>", lambda e: self.open_add_task_window())

    def load_schedule(self):
        """Load schedule from JSON file with task details"""
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    
                    # Load task details if available
                    if "tasks" in data:
                        self.task_details = data["tasks"]
                        
                        # Convert tasks to the schedule format
                        schedule = {}
                        for key, task_info in self.task_details.items():
                            day, hour = key.split('|')
                            schedule[(day, hour)] = task_info.get("name", "")
                        return schedule
                    else:
                        # Legacy format support
                        return {tuple(key.split('|')): task for key, task in data.items()}
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Failed to load schedule. File may be corrupted.")
                return {}
        else:
            return {}  # Default empty schedule

    def save_schedule(self):
        """Save schedule with task details to JSON file"""
        # Collect current data from entries
        data = {}
        for (day, hour), entry in self.entries.items():
            content = entry.get().strip()
            priority = "medium"  # Default priority
            
            # Check if this task already has details
            key = f"{day}|{hour}"
            if key in self.task_details:
                # Update name but keep other details
                if content:
                    self.task_details[key]["name"] = content
                else:
                    # If content is now empty, remove this task
                    if key in self.task_details:
                        del self.task_details[key]
            elif content:
                # Create new task details
                self.task_details[key] = {
                    "name": content,
                    "priority": priority,
                    "notes": "",
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "completed": False
                }
        
        # Save to file
        with open(self.SAVE_FILE, 'w') as f:
            json.dump({"tasks": self.task_details}, f, indent=2)
        
        # Update saved state
        self.saved_schedule = {
            (day, hour): entry.get().strip()
            for (day, hour), entry in self.entries.items()
            if entry.get().strip()
        }
        
        messagebox.showinfo("Success", "Schedule saved successfully!")

    def export_to_csv(self):
        """Export the schedule to a CSV file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Schedule to CSV"
        )
        
        if not filename:
            return  # User cancelled
            
        try:
            with open(filename, 'w') as f:
                # Write header
                f.write("Day,Hour,Task,Priority,Notes,Completed\n")
                
                # Write tasks
                for key, task_info in self.task_details.items():
                    day, hour = key.split('|')
                    name = task_info.get("name", "")
                    priority = task_info.get("priority", "medium")
                    notes = task_info.get("notes", "").replace(",", ";")  # Avoid CSV confusion
                    completed = "Yes" if task_info.get("completed", False) else "No"
                    
                    f.write(f"{day},{hour},{name},{priority},{notes},{completed}\n")
                    
            messagebox.showinfo("Export Successful", f"Schedule exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred: {str(e)}")

    def open_add_task_window(self):
        """Open window to add a new task with more details"""
        window = tk.Toplevel(self.root)
        window.title("Add New Task")
        window.geometry("400x350")
        
        # Apply current theme
        if self.current_theme == "dark":
            window.configure(bg="#333333")
            label_bg = "#333333"
            label_fg = "white"
        else:
            window.configure(bg="#f0f0f0")
            label_bg = "#f0f0f0"
            label_fg = "black"
        
        # Create frame for the form
        form_frame = ttk.Frame(window)
        form_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Task input fields
        ttk.Label(form_frame, text="Task Name:").grid(row=0, column=0, sticky="w", pady=5)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky="we", pady=5)
        
        ttk.Label(form_frame, text="Day:").grid(row=1, column=0, sticky="w", pady=5)
        day_combo = ttk.Combobox(form_frame, values=self.DAYS, state="readonly")
        day_combo.grid(row=1, column=1, sticky="we", pady=5)
        day_combo.current(0)  # Default to Monday
        
        ttk.Label(form_frame, text="Time:").grid(row=2, column=0, sticky="w", pady=5)
        hour_combo = ttk.Combobox(form_frame, values=self.HOURS, state="readonly")
        hour_combo.grid(row=2, column=1, sticky="we", pady=5)
        hour_combo.current(3)  # Default to 8:00
        
        ttk.Label(form_frame, text="Priority:").grid(row=3, column=0, sticky="w", pady=5)
        priority_combo = ttk.Combobox(form_frame, values=["high", "medium", "low"], state="readonly")
        priority_combo.grid(row=3, column=1, sticky="we", pady=5)
        priority_combo.current(1)  # Default to medium
        
        ttk.Label(form_frame, text="Notes:").grid(row=4, column=0, sticky="nw", pady=5)
        notes_text = tk.Text(form_frame, width=30, height=5)
        notes_text.grid(row=4, column=1, sticky="we", pady=5)
        
        # Recurrence option
        ttk.Label(form_frame, text="Repeat:").grid(row=5, column=0, sticky="w", pady=5)
        repeat_combo = ttk.Combobox(form_frame, values=["None", "Daily", "Weekly", "Weekdays"], state="readonly")
        repeat_combo.grid(row=5, column=1, sticky="we", pady=5)
        repeat_combo.current(0)  # Default to no recurrence
        
        # Submit button
        def submit():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Task name cannot be empty")
                return
                
            day = day_combo.get()
            hour = hour_combo.get()
            priority = priority_combo.get()
            notes = notes_text.get("1.0", tk.END).strip()
            repeat = repeat_combo.get()
            
            # Add task to the selected time slot
            key = f"{day}|{hour}"
            self.task_details[key] = {
                "name": name,
                "priority": priority,
                "notes": notes,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "completed": False,
                "repeat": repeat
            }
            
            # Update the entry in the grid
            if (day, hour) in self.entries:
                self.entries[(day, hour)].delete(0, tk.END)
                self.entries[(day, hour)].insert(0, name)
                self.update_task_color((day, hour))
            
            # Handle recurrence
            if repeat != "None":
                self.add_recurring_tasks(day, hour, name, priority, notes, repeat)
            
            window.destroy()
            messagebox.showinfo("Success", "Task added successfully!")
        
        ttk.Button(form_frame, text="Add Task", command=submit).grid(row=6, column=0, columnspan=2, pady=10)
        
        # Make columns expandable
        form_frame.columnconfigure(1, weight=1)

    def add_recurring_tasks(self, start_day, hour, name, priority, notes, repeat_type):
        """Add recurring tasks based on the pattern"""
        if repeat_type == "Daily":
            # Add to all days
            for day in self.DAYS:
                if day != start_day:  # Skip the original day
                    key = f"{day}|{hour}"
                    self.task_details[key] = {
                        "name": name,
                        "priority": priority,
                        "notes": notes,
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "completed": False,
                        "repeat": repeat_type
                    }
                    
                    # Update entry in grid
                    if (day, hour) in self.entries:
                        self.entries[(day, hour)].delete(0, tk.END)
                        self.entries[(day, hour)].insert(0, name)
                        self.update_task_color((day, hour))
        
        elif repeat_type == "Weekly":
            # Already added for current week in the main function
            pass
            
        elif repeat_type == "Weekdays":
            # Add to Monday-Friday only
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            for day in weekdays:
                if day != start_day:  # Skip the original day
                    key = f"{day}|{hour}"
                    self.task_details[key] = {
                        "name": name,
                        "priority": priority,
                        "notes": notes,
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "completed": False,
                        "repeat": repeat_type
                    }
                    
                    # Update entry in grid
                    if (day, hour) in self.entries:
                        self.entries[(day, hour)].delete(0, tk.END)
                        self.entries[(day, hour)].insert(0, name)
                        self.update_task_color((day, hour))

    def open_task_details(self, day, hour):
        """Open a window to show and edit task details"""
        key = f"{day}|{hour}"
        
        # Check if task exists at this location
        if key not in self.task_details and not self.entries[(day, hour)].get().strip():
            messagebox.showinfo("No Task", "No task exists at this time slot.")
            return
            
        # Create or update task details if entry has content but no details
        if key not in self.task_details and self.entries[(day, hour)].get().strip():
            content = self.entries[(day, hour)].get().strip()
            self.task_details[key] = {
                "name": content,
                "priority": "medium",
                "notes": "",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "completed": False,
                "repeat": "None"
            }
        
        # Create task details window
        window = tk.Toplevel(self.root)
        window.title(f"Task Details: {day} {hour}")
        window.geometry("400x350")
        
        # Apply current theme
        if self.current_theme == "dark":
            window.configure(bg="#333333")
        else:
            window.configure(bg="#f0f0f0")
        
        # Create form
        form_frame = ttk.Frame(window)
        form_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        task_info = self.task_details.get(key, {})
        
        ttk.Label(form_frame, text="Task Name:").grid(row=0, column=0, sticky="w", pady=5)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.insert(0, task_info.get("name", ""))
        name_entry.grid(row=0, column=1, sticky="we", pady=5)
        
        ttk.Label(form_frame, text="Priority:").grid(row=1, column=0, sticky="w", pady=5)
        priority_combo = ttk.Combobox(form_frame, values=["high", "medium", "low"], state="readonly")
        priority_combo.grid(row=1, column=1, sticky="we", pady=5)
        priority_current = task_info.get("priority", "medium")
        priority_options = ["high", "medium", "low"]
        priority_combo.current(priority_options.index(priority_current))
        
        ttk.Label(form_frame, text="Notes:").grid(row=2, column=0, sticky="nw", pady=5)
        notes_text = tk.Text(form_frame, width=30, height=5)
        notes_text.insert("1.0", task_info.get("notes", ""))
        notes_text.grid(row=2, column=1, sticky="we", pady=5)
        
        # Show creation date
        ttk.Label(form_frame, text="Created:").grid(row=3, column=0, sticky="w", pady=5)
        created_label = ttk.Label(form_frame, text=task_info.get("created", ""))
        created_label.grid(row=3, column=1, sticky="w", pady=5)
        
        # Completed checkbox
        completed_var = tk.BooleanVar(value=task_info.get("completed", False))
        completed_check = ttk.Checkbutton(form_frame, text="Completed", variable=completed_var)
        completed_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
        # Save and delete buttons
        def save_details():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Task name cannot be empty")
                return
                
            # Update task details
            self.task_details[key] = {
                "name": name,
                "priority": priority_combo.get(),
                "notes": notes_text.get("1.0", tk.END).strip(),
                "created": task_info.get("created", datetime.now().strftime("%Y-%m-%d %H:%M")),
                "completed": completed_var.get(),
                "repeat": task_info.get("repeat", "None")
            }
            
            # Update the entry in the grid
            self.entries[(day, hour)].delete(0, tk.END)
            self.entries[(day, hour)].insert(0, name)
            self.update_task_color((day, hour))
            
            window.destroy()
        
        def delete_task():
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?"):
                # Remove task from details
                if key in self.task_details:
                    del self.task_details[key]
                
                # Clear entry in grid
                self.entries[(day, hour)].delete(0, tk.END)
                
                # Reset background color
                self.entries[(day, hour)].configure(bg="white")
                
                window.destroy()
        
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Save", command=save_details).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Delete", command=delete_task).pack(side=tk.LEFT, padx=10)
        
        # Make columns expandable
        form_frame.columnconfigure(1, weight=1)

    def update_task_color(self, cell_key):
        """Update the color of a task cell based on priority and completion status"""
        day, hour = cell_key
        key = f"{day}|{hour}"
        
        if key in self.task_details:
            task_info = self.task_details[key]
            priority = task_info.get("priority", "medium")
            completed = task_info.get("completed", False)
            
            if completed:
                color = self.priority_colors["completed"]
            else:
                color = self.priority_colors[priority]
                
            self.entries[cell_key].configure(bg=color)
        else:
            # Reset to default if no task
            self.entries[cell_key].configure(bg="white")

    def open_search_window(self):
        """Open window to search for tasks"""
        window = tk.Toplevel(self.root)
        window.title("Search Tasks")
        window.geometry("500x400")
        
        # Apply current theme
        if self.current_theme == "dark":
            window.configure(bg="#333333")
            bg_color = "#333333"
            fg_color = "white"
        else:
            window.configure(bg="#f0f0f0")
            bg_color = "#f0f0f0"
            fg_color = "black"
        
        # Create search frame
        search_frame = ttk.Frame(window)
        search_frame.pack(padx=20, pady=10, fill=tk.X)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(search_frame, width=30)
        search_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Create results frame
        results_frame = ttk.Frame(window)
        results_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Create scrollable results
        results_canvas = tk.Canvas(results_frame, bg=bg_color)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=results_canvas.yview)
        scrollable_frame = ttk.Frame(results_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: results_canvas.configure(scrollregion=results_canvas.bbox("all"))
        )
        
        results_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        results_canvas.configure(yscrollcommand=scrollbar.set)
        
        results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Function to perform search
        def perform_search():
            # Clear previous results
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
                
            query = search_entry.get().lower().strip()
            if not query:
                ttk.Label(scrollable_frame, text="Enter a search term").pack(pady=10)
                return
                
            # Search in tasks
            results = []
            for key, task_info in self.task_details.items():
                name = task_info.get("name", "").lower()
                notes = task_info.get("notes", "").lower()
                
                if query in name or query in notes:
                    day, hour = key.split('|')
                    results.append((day, hour, task_info))
            
            # Display results
            if not results:
                ttk.Label(scrollable_frame, text="No tasks found").pack(pady=10)
            else:
                for day, hour, task_info in results:
                    result_frame = ttk.Frame(scrollable_frame)
                    result_frame.pack(fill=tk.X, pady=5, padx=5)
                    
                    # Priority indicator
                    priority = task_info.get("priority", "medium")
                    priority_color = self.priority_colors[priority]
                    
                    indicator = tk.Frame(result_frame, width=10, bg=priority_color)
                    indicator.pack(side=tk.LEFT, fill=tk.Y)
                    
                    # Task details
                    details_frame = ttk.Frame(result_frame)
                    details_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                    
                    name_label = ttk.Label(
                        details_frame, 
                        text=task_info.get("name", ""),
                        font=("TkDefaultFont", 10, "bold")
                    )
                    name_label.pack(anchor="w")
                    
                    time_label = ttk.Label(details_frame, text=f"{day} at {hour}")
                    time_label.pack(anchor="w")
                    
                    if task_info.get("completed", False):
                        status_label = ttk.Label(details_frame, text="Completed", foreground="green")
                        status_label.pack(anchor="w")
                    
                    # Go to button
                    def make_goto_function(d, h):
                        return lambda: self.goto_task(d, h, window)
                    
                    goto_btn = ttk.Button(
                        result_frame, 
                        text="Go to", 
                        command=make_goto_function(day, hour)
                    )
                    goto_btn.pack(side=tk.RIGHT, padx=5)
        
        # Search button
        search_button = ttk.Button(search_frame, text="Search", command=perform_search)
        search_button.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        search_entry.bind("<Return>", lambda e: perform_search())
        
        # Initial search results placeholder
        ttk.Label(scrollable_frame, text="Enter a search term and press Search").pack(pady=10)



    def goto_task(self, day, hour, search_window=None):
        """Navigate to a specific task in the schedule"""
        # Close search window if provided
        if search_window:
            search_window.destroy()
            
        # Get row and column of the task
        row = self.HOURS.index(hour) + 1
        col = self.DAYS.index(day) + 1
        
        # Flash the cell to highlight it
        for i in range(5):  # Flash 5 times
            self.entries[(day, hour)].configure(bg="lightblue")
            self.root.update()
            self.root.after(200)  # Wait for 200ms
            self.update_task_color((day, hour))
            self.root.update()
            self.root.after(200)
            
        # Open task details
        self.open_task_details(day, hour)

    def open_help_window(self):
        """Open window with help information"""
        window = tk.Toplevel(self.root)
        window.title("Help")
        window.geometry("600x500")
        
        # Apply current theme
        if self.current_theme == "dark":
            window.configure(bg="#333333")
            text_bg = "#444444"
            text_fg = "white"
        else:
            window.configure(bg="#f0f0f0")
            text_bg = "white"
            text_fg = "black"
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Basic usage tab
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic Usage")
        
        basic_text = """
How to Use Autodo:

1. Direct Editing:
   - Click on any cell in the schedule to enter a task
   - Double-click a cell to open detailed task editor

2. Task Management:
   - Add Task (Ctrl+N): Open form to add detailed tasks
   - Click on existing tasks to view/edit details
   - Set priorities and mark tasks as completed

3. Save & Export:
   - Save Schedule (Ctrl+S): Save your current plan
   - Data is automatically loaded next time
   - Export to CSV: Share or print your schedule

4. Search:
   - Search Tasks (Ctrl+F): Find tasks by name or content
   - Click "Go to" to navigate to the task in schedule
"""
        basic_help = tk.Text(basic_frame, wrap="word", width=70, height=20, bg=text_bg, fg=text_fg)
        basic_help.insert("1.0", basic_text)
        basic_help.configure(state="disabled")
        basic_help.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Shortcuts tab
        shortcut_frame = ttk.Frame(notebook)
        notebook.add(shortcut_frame, text="Keyboard Shortcuts")
        
        shortcuts_text = """
Keyboard Shortcuts:

Ctrl+S - Save schedule
Ctrl+Q - Quit application
Ctrl+F - Search tasks
Ctrl+N - Add new task
F1     - Open this help window
"""
        shortcut_help = tk.Text(shortcut_frame, wrap="word", width=70, height=20, bg=text_bg, fg=text_fg)
        shortcut_help.insert("1.0", shortcuts_text)
        shortcut_help.configure(state="disabled")
        shortcut_help.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Features tab
        features_frame = ttk.Frame(notebook)
        notebook.add(features_frame, text="Features")
        
        features_text = """
Key Features:

1. Color-Coded Tasks:
   - High Priority: Light Red
   - Medium Priority: Light Yellow
   - Low Priority: Light Green
   - Completed: Light Gray

2. Task Details:
   - Add notes to tasks
   - Track creation date
   - Mark tasks as completed
   - Set task priorities

3. Recurring Tasks:
   - Create daily tasks
   - Create weekday-only tasks
   - Create weekly recurring tasks

4. Data Management:
   - Automatic saving
   - Export to CSV
   - Unsaved changes detection
"""
        features_help = tk.Text(features_frame, wrap="word", width=70, height=20, bg=text_bg, fg=text_fg)
        features_help.insert("1.0", features_text)
        features_help.configure(state="disabled")
        features_help.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def has_unsaved_changes(self):
        """Comprehensive check for unsaved changes, including tasks added via the Add Task window"""
        
        # 1. 检查条目内容与保存状态的差异
        current_entries = {}
        for (day, hour), entry in self.entries.items():
            content = entry.get().strip()
            if content:  # 只考虑非空条目
                current_entries[(day, hour)] = content
        
        # 条目集比较 - 检查是否有新增或删除的任务
        if set(current_entries.keys()) != set(self.saved_schedule.keys()):
            return True
        
        # 条目内容比较 - 检查任务名称是否已更改
        for (day, hour), content in current_entries.items():
            if content != self.saved_schedule.get((day, hour), ""):
                return True
        
        # 2. 检查任务详情变化
        # 将当前task_details的键从"day|hour"格式转换为(day, hour)元组以便比较
        current_task_keys = {tuple(k.split('|')): k for k in self.task_details.keys()}
        
        # 通过Add Task窗口添加的新任务会出现在self.task_details中但不在self.saved_schedule中
        for (day, hour) in current_task_keys:
            if (day, hour) not in self.saved_schedule:
                return True
        
        # 3. 检查任务详情属性变化 (如果需要)
        # 这部分可以添加更详细的属性比较，如优先级、备注等
        # 但是对于基本的"添加任务检测"，上面的检查应该足够了
        
        # 如果上述所有检查都通过，说明没有未保存的更改
        return False

    def on_close(self):
            """Handle window close event"""
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
        """Create the weekly schedule grid with all enhancements"""
        root = self.root
        SCHEDULE = self.load_schedule()
        self.saved_schedule = SCHEDULE
        
        # Configure root to expand properly
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        # Main container frame with scrolling support
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure main_frame to expand
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(main_frame)
        scrollbar_y = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Pack scrollbars and canvas with proper fill and expand
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create schedule frame inside canvas
        schedule_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=schedule_frame, anchor="nw")
        
        # Configure canvas to resize with the window
        def on_configure(event):
            # Update the scroll region to include the entire inner frame
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            # Adjust the canvas window width to match the canvas width
            canvas.itemconfigure(canvas_window, width=event.width)
            
        canvas.bind("<Configure>", on_configure)
        
        # Create weekday headers
        for col, day in enumerate([''] + self.DAYS):
            label = ttk.Label(schedule_frame, text=day, borderwidth=1, relief="ridge", width=15, anchor='center')
            label.grid(row=0, column=col, sticky='nsew')
        
        # Create hourly rows and task cells
        for row, hour in enumerate(self.HOURS, start=1):
            # Hour label
            label = ttk.Label(schedule_frame, text=hour, borderwidth=1, relief="ridge", width=10)
            label.grid(row=row, column=0, sticky='nsew')
            
            # Day entries
            for col, day in enumerate(self.DAYS, start=1):
                cell_key = (day, hour)
                
                # Create entry widget with adjusted size
                entry = tk.Entry(schedule_frame, width=18, justify='center')
                
                # Get task content
                task = ""
                key = f"{day}|{hour}"
                if key in self.task_details:
                    task = self.task_details[key].get("name", "")
                elif cell_key in SCHEDULE:
                    task = SCHEDULE[cell_key]
                    
                entry.insert(0, task)
                entry.grid(row=row, column=col, sticky='nsew', padx=1, pady=1)
                self.entries[cell_key] = entry
                
                # Set background color based on priority
                if key in self.task_details:
                    priority = self.task_details[key].get("priority", "medium")
                    completed = self.task_details[key].get("completed", False)
                    
                    if completed:
                        entry.configure(bg=self.priority_colors["completed"])
                    else:
                        entry.configure(bg=self.priority_colors[priority])
                
                # Bind double-click to open task details
                entry.bind("<Double-Button-1>", lambda e, d=day, h=hour: self.open_task_details(d, h))
        
        # Make columns and rows auto-resize
        for i in range(len(self.DAYS) + 1):
            schedule_frame.grid_columnconfigure(i, weight=1)
        for i in range(len(self.HOURS) + 1):
            schedule_frame.grid_rowconfigure(i, weight=1)
        
        # Make the entries expand with the grid
        def update_entry_widths(event):
            cell_width = event.width // (len(self.DAYS) + 1) - 2  # Account for padding
            for entry in self.entries.values():
                entry.config(width=max(cell_width // 8, 10))  # Approximate character width
                
        schedule_frame.bind("<Configure>", update_entry_widths)
        
        # Update canvas scroll region
        schedule_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        # Create bottom button bar
        button_bar = ttk.Frame(root)
        button_bar.pack(fill=tk.X, padx=10, pady=5)
        
        # Add buttons
        save_btn = ttk.Button(button_bar, text="Save Schedule", command=self.save_schedule)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        add_btn = ttk.Button(button_bar, text="Add Task", command=self.open_add_task_window)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        search_btn = ttk.Button(button_bar, text="Search Tasks", command=self.open_search_window)
        search_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(button_bar, text="Export to CSV", command=self.export_to_csv)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Theme toggle button
        def toggle_theme():
            if self.current_theme == "light":
                self.apply_theme("dark")
            else:
                self.apply_theme("light")
        
        theme_btn = ttk.Button(button_bar, text="Toggle Theme", command=toggle_theme)
        theme_btn.pack(side=tk.RIGHT, padx=5)
        
        help_btn = ttk.Button(button_bar, text="Help", command=self.open_help_window)
        help_btn.pack(side=tk.RIGHT, padx=5)
        
        # Create top menu bar
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        # Add 'File' menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Schedule (Ctrl+S)", command=self.save_schedule)
        file_menu.add_command(label="Export to CSV", command=self.export_to_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit (Ctrl+Q)", command=self.on_close)
        
        # Add 'Tasks' menu
        task_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tasks", menu=task_menu)
        task_menu.add_command(label="Add Task (Ctrl+N)", command=self.open_add_task_window)
        task_menu.add_command(label="Search Tasks (Ctrl+F)", command=self.open_search_window)
        
        # Add 'View' menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=toggle_theme)
        
        # Add 'Help' menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Help (F1)", command=self.open_help_window)
        
        # Bind mousewheel to scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows and MacOS
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Linux
        
        # Intercept close button to check for unsaved changes
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)


if __name__ == "__main__":
    autodo = Autodo(title="Autodo - Weekly Schedule", geometry="1200x800", SAVE_FILE="weekly_schedule.json")
    autodo.create_week_schedule()
    autodo.root.mainloop()