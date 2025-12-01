"""Configuration dialog for MinTool."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class ConfigDialog:
    """Configuration dialog window."""
    
    def __init__(self, parent, config_manager):
        """
        Initialize config dialog.
        
        Args:
            parent: Parent window
            config_manager: ConfigManager instance
        """
        self.parent = parent
        self.config_manager = config_manager
        self.window = None
    
    def show(self):
        """Show configuration dialog."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Configuration")
        self.window.geometry("500x420")
        self.window.resizable(False, False)
        
        # Default MIN ID
        tk.Label(self.window, text="Default MIN ID (Hex):").grid(
            row=0, column=0, padx=10, pady=10, sticky='w'
        )
        self.id_entry = tk.Entry(self.window, width=20)
        self.id_entry.insert(0, str(self.config_manager.get("default_min_id", 16)))
        self.id_entry.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        
        # Tester Present Interval
        tk.Label(self.window, text="Tester Present Interval (ms):").grid(
            row=1, column=0, padx=10, pady=10, sticky='w'
        )
        self.tester_interval_entry = tk.Entry(self.window, width=20)
        self.tester_interval_entry.insert(
            0, str(self.config_manager.get("tester_present_interval_ms", 3000))
        )
        self.tester_interval_entry.grid(row=1, column=1, padx=10, pady=10, sticky='w')
        
        # Enable Tester Present on Connect
        self.tester_enable_var = tk.BooleanVar(
            value=self.config_manager.get("enable_tester_present_on_connect", False)
        )
        self.tester_enable_check = tk.Checkbutton(
            self.window,
            text="Enable Tester Present on Connect",
            variable=self.tester_enable_var
        )
        self.tester_enable_check.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        
        # Tester Present Suppress Response
        self.tester_suppress_var = tk.BooleanVar(
            value=self.config_manager.get("tester_present_suppress", False)
        )
        self.tester_suppress_check = tk.Checkbutton(
            self.window,
            text="Suppress Positive Response (3E 80)",
            variable=self.tester_suppress_var
        )
        self.tester_suppress_check.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        
        # Security Access EXE Path
        tk.Label(self.window, text="Security Access EXE:").grid(
            row=4, column=0, padx=10, pady=10, sticky='w'
        )
        self.exe_path_entry = tk.Entry(self.window, width=30)
        self.exe_path_entry.insert(0, self.config_manager.get("security_exe_path", ""))
        self.exe_path_entry.grid(row=4, column=1, padx=10, pady=10, sticky='w')
        
        tk.Button(
            self.window,
            text="Browse",
            command=self._browse_exe
        ).grid(row=4, column=2, padx=5, pady=10)
        
        # Automation Script Path
        tk.Label(self.window, text="Automation Script (TXT):").grid(
            row=5, column=0, padx=10, pady=10, sticky='w'
        )
        self.script_path_entry = tk.Entry(self.window, width=30)
        self.script_path_entry.insert(
            0, self.config_manager.get("automation_script_path", "")
        )
        self.script_path_entry.grid(row=5, column=1, padx=10, pady=10, sticky='w')
        
        tk.Button(
            self.window,
            text="Browse",
            command=self._browse_script
        ).grid(row=5, column=2, padx=5, pady=10)
        
        # Security Levels Config Button
        tk.Button(
            self.window,
            text="Configure Security Levels",
            command=self._config_security_levels,
            bg="lightyellow",
            width=25
        ).grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky='w')
        
        # Save button
        tk.Button(
            self.window,
            text="Save",
            command=self._save_config,
            bg="lightgreen",
            width=15
        ).grid(row=7, column=1, pady=20)
    
    def _browse_exe(self):
        """Browse for security access EXE file."""
        filepath = filedialog.askopenfilename(
            title="Select Security Access EXE",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if filepath:
            self.exe_path_entry.delete(0, tk.END)
            self.exe_path_entry.insert(0, filepath)
    
    def _browse_script(self):
        """Browse for automation script file."""
        filepath = filedialog.askopenfilename(
            title="Select Automation Script",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            self.script_path_entry.delete(0, tk.END)
            self.script_path_entry.insert(0, filepath)
    
    def _config_security_levels(self):
        """Open security levels configuration dialog."""
        levels_window = tk.Toplevel(self.window)
        levels_window.title("Security Levels Configuration")
        levels_window.geometry("550x450")
        
        tk.Label(
            levels_window,
            text="Security Levels Configuration",
            font=("Arial", 12, "bold")
        ).pack(pady=10)
        
        # Frame for listbox and buttons
        list_frame = tk.Frame(levels_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Listbox with scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.levels_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=12, font=("Courier", 10))
        self.levels_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.levels_listbox.yview)
        
        # Load current levels
        current_levels = self.config_manager.get("security_levels", [])
        for lvl in current_levels:
            level_num = lvl.get("level", 1)
            name = lvl.get("name", "Unknown")
            color = lvl.get("color", "lightgray")
            self.levels_listbox.insert(tk.END, f"0x{level_num:02X} - {name:20s} [{color}]")
        
        # Store levels data
        self.temp_levels = current_levels.copy()
        
        # Buttons frame
        btn_frame = tk.Frame(levels_window)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="➕ Add Level",
            command=lambda: self._add_level(levels_window),
            bg="lightgreen",
            width=12
        ).grid(row=0, column=0, padx=5)
        
        tk.Button(
            btn_frame,
            text="✏️ Edit Selected",
            command=lambda: self._edit_level(levels_window),
            bg="lightyellow",
            width=12
        ).grid(row=0, column=1, padx=5)
        
        tk.Button(
            btn_frame,
            text="🗑️ Remove Selected",
            command=lambda: self._remove_level(levels_window),
            bg="lightcoral",
            width=12
        ).grid(row=0, column=2, padx=5)
        
        # Save button
        tk.Button(
            levels_window,
            text="💾 Save All",
            command=lambda: self._save_levels(levels_window),
            bg="lightblue",
            width=20,
            font=("Arial", 10, "bold")
        ).pack(pady=10)
    
    def _add_level(self, parent):
        """Add new security level."""
        dialog = tk.Toplevel(parent)
        dialog.title("Add Security Level")
        dialog.geometry("400x200")
        dialog.grab_set()
        
        tk.Label(dialog, text="Level (Hex):").grid(row=0, column=0, padx=10, pady=10, sticky='e')
        level_entry = tk.Entry(dialog, width=20)
        level_entry.insert(0, "01")
        level_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(dialog, text="Name:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
        name_entry = tk.Entry(dialog, width=20)
        name_entry.insert(0, "New Level")
        name_entry.grid(row=1, column=1, padx=10, pady=10)
        
        tk.Label(dialog, text="Color:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
        color_var = tk.StringVar(value="lightgray")
        color_combo = ttk.Combobox(dialog, textvariable=color_var, width=18, state='readonly')
        color_combo['values'] = ('lightblue', 'lightgreen', 'lightyellow', 'lightcoral', 'lightgray', 'pink', 'orange')
        color_combo.grid(row=2, column=1, padx=10, pady=10)
        
        def save_new():
            try:
                level = int(level_entry.get(), 16)
                name = name_entry.get().strip()
                color = color_var.get()
                
                if not name:
                    messagebox.showerror("Error", "Name cannot be empty")
                    return
                
                # Check duplicate
                for lvl in self.temp_levels:
                    if lvl["level"] == level:
                        messagebox.showerror("Error", f"Level 0x{level:02X} already exists")
                        return
                
                self.temp_levels.append({"level": level, "name": name, "color": color})
                self.temp_levels.sort(key=lambda x: x["level"])
                self._refresh_listbox()
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Invalid level value")
        
        tk.Button(dialog, text="Add", command=save_new, bg="lightgreen", width=15).grid(row=3, column=1, pady=20)
    
    def _edit_level(self, parent):
        """Edit selected security level."""
        selection = self.levels_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a level to edit")
            return
        
        idx = selection[0]
        current = self.temp_levels[idx]
        
        dialog = tk.Toplevel(parent)
        dialog.title("Edit Security Level")
        dialog.geometry("400x200")
        dialog.grab_set()
        
        tk.Label(dialog, text="Level (Hex):").grid(row=0, column=0, padx=10, pady=10, sticky='e')
        level_entry = tk.Entry(dialog, width=20)
        level_entry.insert(0, f"{current['level']:02X}")
        level_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(dialog, text="Name:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
        name_entry = tk.Entry(dialog, width=20)
        name_entry.insert(0, current['name'])
        name_entry.grid(row=1, column=1, padx=10, pady=10)
        
        tk.Label(dialog, text="Color:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
        color_var = tk.StringVar(value=current['color'])
        color_combo = ttk.Combobox(dialog, textvariable=color_var, width=18, state='readonly')
        color_combo['values'] = ('lightblue', 'lightgreen', 'lightyellow', 'lightcoral', 'lightgray', 'pink', 'orange')
        color_combo.grid(row=2, column=1, padx=10, pady=10)
        
        def save_edit():
            try:
                level = int(level_entry.get(), 16)
                name = name_entry.get().strip()
                color = color_var.get()
                
                if not name:
                    messagebox.showerror("Error", "Name cannot be empty")
                    return
                
                # Check duplicate (except current)
                for i, lvl in enumerate(self.temp_levels):
                    if i != idx and lvl["level"] == level:
                        messagebox.showerror("Error", f"Level 0x{level:02X} already exists")
                        return
                
                self.temp_levels[idx] = {"level": level, "name": name, "color": color}
                self.temp_levels.sort(key=lambda x: x["level"])
                self._refresh_listbox()
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Invalid level value")
        
        tk.Button(dialog, text="Save", command=save_edit, bg="lightgreen", width=15).grid(row=3, column=1, pady=20)
    
    def _remove_level(self, parent):
        """Remove selected security level."""
        selection = self.levels_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a level to remove")
            return
        
        idx = selection[0]
        del self.temp_levels[idx]
        self._refresh_listbox()
    
    def _refresh_listbox(self):
        """Refresh listbox display."""
        self.levels_listbox.delete(0, tk.END)
        for lvl in self.temp_levels:
            level_num = lvl["level"]
            name = lvl["name"]
            color = lvl["color"]
            self.levels_listbox.insert(tk.END, f"0x{level_num:02X} - {name:20s} [{color}]")
    
    def _save_levels(self, window):
        """Save security levels to config and file."""
        if not self.temp_levels:
            messagebox.showwarning("Warning", "At least one security level is required")
            return
        
        self.config_manager.set("security_levels", self.temp_levels)
        
        # Save to file immediately
        if self.config_manager.save_config():
            window.destroy()
        else:
            messagebox.showerror("Error", "Failed to save configuration")
    
    def _save_config(self):
        """Save configuration."""
        try:
            min_id = int(self.id_entry.get())
            if min_id < 0 or min_id > 63:
                messagebox.showerror("Error", "MIN ID must be between 0 and 63")
                return
            
            # Validate tester present interval
            tester_interval = int(self.tester_interval_entry.get())
            if tester_interval < 100 or tester_interval > 60000:
                messagebox.showerror("Error", "Tester Present interval must be between 100ms and 60000ms")
                return
            
            self.config_manager.set("default_min_id", min_id)
            self.config_manager.set("tester_present_interval_ms", tester_interval)
            self.config_manager.set("enable_tester_present_on_connect", self.tester_enable_var.get())
            self.config_manager.set("tester_present_suppress", self.tester_suppress_var.get())
            self.config_manager.set("security_exe_path", self.exe_path_entry.get())
            self.config_manager.set("automation_script_path", self.script_path_entry.get())
            
            if self.config_manager.save_config():
                self.window.destroy()
            else:
                messagebox.showerror("Error", "Failed to save configuration")
        except ValueError:
            messagebox.showerror("Error", "Invalid MIN ID format")
