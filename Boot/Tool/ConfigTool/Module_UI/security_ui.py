"""
Security UI Module - Render Security Access configuration UI
"""

import tkinter as tk
from tkinter import ttk


class SecurityUI:
    """UI renderer for Security Access Levels"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.security_tree = None
        self.security_count_var = None
    
    def setup_tab(self):
        """Setup security tab with treeview"""
        # Tree view for security levels
        tree_frame = ttk.Frame(self.parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("Level", "Seed Sub", "Key Sub", "Seed Size", "Key Size", "Max Attempts", "Delay")
        self.security_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        widths = {"Level": 60, "Seed Sub": 100, "Key Sub": 100, "Seed Size": 90, 
                  "Key Size": 90, "Max Attempts": 110, "Delay": 100}
        for col in columns:
            self.security_tree.heading(col, text=col)
            self.security_tree.column(col, width=widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.security_tree.yview)
        self.security_tree.configure(yscrollcommand=scrollbar.set)
        
        self.security_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return self.security_tree
    
    def setup_toolbar(self, add_cmd, edit_cmd, delete_cmd):
        """Setup toolbar with action buttons"""
        toolbar = ttk.Frame(self.parent_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Add Security Level", command=add_cmd, style='Success.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Security Level", command=edit_cmd, style='TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Security Level", command=delete_cmd, style='Warning.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text=f"Total Levels: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.security_count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=self.security_count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        return self.security_count_var
    
    def refresh_tree(self, security_levels):
        """Refresh security treeview with data"""
        self.security_tree.delete(*self.security_tree.get_children())
        
        for sec in security_levels:
            self.security_tree.insert('', tk.END, values=(
                sec['security_level'],
                sec['seed_request_sub'],
                sec['key_request_sub'],
                sec['seed_size'],
                sec['key_size'],
                sec['max_attempts'],
                f"{sec['delay_time']} ms"
            ))
        
        if self.security_count_var:
            self.security_count_var.set(str(len(security_levels)))
    
    def show_edit_form(self, config_panel_frame, index, config, set_modified_callback):
        """Render edit form for security level with auto-save"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        sec = config['security_levels'][index]
        
        # Create form
        form_frame = ttk.Frame(config_panel_frame, padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text=f"Edit Security Level {sec['security_level']}", 
                 font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # Level
        ttk.Label(form_frame, text="Security Level:").grid(row=row, column=0, sticky=tk.W, pady=5)
        level_var = tk.IntVar(value=sec['security_level'])
        ttk.Entry(form_frame, textvariable=level_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Seed Request Sub
        ttk.Label(form_frame, text="Seed Request Sub:").grid(row=row, column=0, sticky=tk.W, pady=5)
        seed_sub_var = tk.StringVar(value=sec['seed_request_sub'])
        ttk.Entry(form_frame, textvariable=seed_sub_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Key Request Sub
        ttk.Label(form_frame, text="Key Request Sub:").grid(row=row, column=0, sticky=tk.W, pady=5)
        key_sub_var = tk.StringVar(value=sec['key_request_sub'])
        ttk.Entry(form_frame, textvariable=key_sub_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Seed Size
        ttk.Label(form_frame, text="Seed Size (bytes):").grid(row=row, column=0, sticky=tk.W, pady=5)
        seed_size_var = tk.IntVar(value=sec['seed_size'])
        ttk.Entry(form_frame, textvariable=seed_size_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Key Size
        ttk.Label(form_frame, text="Key Size (bytes):").grid(row=row, column=0, sticky=tk.W, pady=5)
        key_size_var = tk.IntVar(value=sec['key_size'])
        ttk.Entry(form_frame, textvariable=key_size_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Max Attempts
        ttk.Label(form_frame, text="Max Attempts:").grid(row=row, column=0, sticky=tk.W, pady=5)
        max_attempts_var = tk.IntVar(value=sec['max_attempts'])
        ttk.Entry(form_frame, textvariable=max_attempts_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Delay Time
        ttk.Label(form_frame, text="Delay Time (ms):").grid(row=row, column=0, sticky=tk.W, pady=5)
        delay_time_var = tk.IntVar(value=sec['delay_time'])
        ttk.Entry(form_frame, textvariable=delay_time_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Get Seed Function
        ttk.Label(form_frame, text="Get Seed Func:").grid(row=row, column=0, sticky=tk.W, pady=5)
        get_seed_var = tk.StringVar(value=sec['get_seed_func'])
        ttk.Entry(form_frame, textvariable=get_seed_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Compare Key Function
        ttk.Label(form_frame, text="Compare Key Func:").grid(row=row, column=0, sticky=tk.W, pady=5)
        compare_key_var = tk.StringVar(value=sec['compare_key_func'])
        ttk.Entry(form_frame, textvariable=compare_key_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Sessions
        ttk.Label(form_frame, text="Supported Sessions:", font=('', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1
        
        session_frame = ttk.LabelFrame(form_frame, text="Select Sessions", padding="10")
        session_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        session_vars = {}
        available_sessions = [s['session_name'] for s in config.get('sessions', [])]
        
        def update_sessions(*args):
            selected = [name for name, var in session_vars.items() if var.get()]
            config['security_levels'][index]['supported_sessions'] = selected
            set_modified_callback()
        
        for sess_name in available_sessions:
            var = tk.BooleanVar(value=sess_name in sec.get('supported_sessions', []))
            session_vars[sess_name] = var
            cb = ttk.Checkbutton(session_frame, text=sess_name, variable=var)
            cb.pack(anchor=tk.W, pady=2)
            var.trace_add('write', update_sessions)
        
        # Auto-save for text fields
        def save_text_changes(*args):
            config['security_levels'][index]['security_level'] = level_var.get()
            config['security_levels'][index]['seed_request_sub'] = seed_sub_var.get()
            config['security_levels'][index]['key_request_sub'] = key_sub_var.get()
            config['security_levels'][index]['seed_size'] = seed_size_var.get()
            config['security_levels'][index]['key_size'] = key_size_var.get()
            config['security_levels'][index]['max_attempts'] = max_attempts_var.get()
            config['security_levels'][index]['delay_time'] = delay_time_var.get()
            config['security_levels'][index]['get_seed_func'] = get_seed_var.get()
            config['security_levels'][index]['compare_key_func'] = compare_key_var.get()
            set_modified_callback()
        
        for var in [level_var, seed_sub_var, key_sub_var, seed_size_var, key_size_var,
                    max_attempts_var, delay_time_var, get_seed_var, compare_key_var]:
            var.trace_add('write', save_text_changes)
        
        # Info label
        info_label = ttk.Label(form_frame, text="ℹ️ Changes are saved automatically", 
                              foreground='green', font=('', 9, 'italic'))
        info_label.grid(row=row, column=0, columnspan=2, pady=20)
    
    def show_info_panel(self, info_text_widget, sec):
        """Show security level details in info panel"""
        info = f"Security Level Details\n"
        info += f"{'='*30}\n"
        info += f"Level: {sec['security_level']}\n"
        info += f"Seed Request: {sec['seed_request_sub']}\n"
        info += f"Key Request: {sec['key_request_sub']}\n"
        info += f"Seed Size: {sec['seed_size']} bytes\n"
        info += f"Key Size: {sec['key_size']} bytes\n"
        info += f"Max Attempts: {sec['max_attempts']}\n"
        info += f"Delay Time: {sec['delay_time']} ms\n"
        info += f"Get Seed Func: {sec['get_seed_func']}\n"
        info += f"Compare Key Func: {sec['compare_key_func']}\n"
        info += f"\nSupported Sessions:\n"
        for sess in sec.get('supported_sessions', []):
            info += f"  • {sess}\n"
        
        info_text_widget.config(state=tk.NORMAL)
        info_text_widget.delete(1.0, tk.END)
        info_text_widget.insert(1.0, info)
        info_text_widget.config(state=tk.DISABLED)

