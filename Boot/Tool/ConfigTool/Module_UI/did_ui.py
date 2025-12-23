"""
DID UI Module
Handles UI rendering for DID configuration
"""

import tkinter as tk
from tkinter import ttk


class DidUI:
    """UI module for DID configuration"""
    
    def __init__(self, parent_frame):
        """Initialize DID UI module"""
        self.parent = parent_frame
        self.tree = None
    
    def setup_tab(self):
        """Setup DIDs tab and return treeview"""
        # Toolbar
        toolbar = ttk.Frame(self.parent)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Treeview
        tree_frame = ttk.Frame(self.parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("DID", "Name", "Length Type", "Length", "Read", "Write", "Description")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        widths = {"DID": 100, "Name": 150, "Length Type": 100, "Length": 80, "Read": 60, "Write": 60, "Description": 200}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return self.tree
    
    def setup_toolbar(self, add_cmd, edit_cmd, delete_cmd):
        """Setup toolbar with action buttons"""
        toolbar = self.parent.winfo_children()[0]  # Get toolbar frame
        
        ttk.Button(toolbar, text="➕ Add DID", command=add_cmd, style='Success.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit DID", command=edit_cmd, style='TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete DID", command=delete_cmd, style='Warning.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text=f"Total DIDs: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        return count_var
    
    def refresh_tree(self, dids):
        """Refresh treeview with DIDs data"""
        self.tree.delete(*self.tree.get_children())
        
        for did in dids:
            has_read = 'read_config' in did and did['read_config'].get('callback')
            has_write = 'write_config' in did and did['write_config'].get('callback')
            
            self.tree.insert('', tk.END, values=(
                did['did'],
                did['did_name'],
                'Fixed' if did.get('fixed_length', True) else 'Variable',
                did.get('expected_length', 0),
                '✓' if has_read else '✗',
                '✓' if has_write else '✗',
                did.get('description', '')
            ))
    
    def show_edit_form(self, config_panel_frame, index, config, callbacks):
        """Show DID edit form with auto-save"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        did = config['dids'][index]
        
        # Create scrollable form
        canvas = tk.Canvas(config_panel_frame, bg='white')
        scrollbar = ttk.Scrollbar(config_panel_frame, orient=tk.VERTICAL, command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="10")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas_frame = canvas.create_window((0, 0), window=form_frame, anchor=tk.NW)
        
        ttk.Label(form_frame, text="Edit DID", font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # DID
        ttk.Label(form_frame, text="DID (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        did_var = tk.StringVar(value=did['did'])
        ttk.Entry(form_frame, textvariable=did_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # DID Name
        ttk.Label(form_frame, text="DID Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        did_name_var = tk.StringVar(value=did['did_name'])
        ttk.Entry(form_frame, textvariable=did_name_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Fixed Length
        fixed_var = tk.BooleanVar(value=did.get('fixed_length', True))
        ttk.Checkbutton(form_frame, text="Fixed Length", variable=fixed_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Expected Length
        ttk.Label(form_frame, text="Expected Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        expected_len_var = tk.IntVar(value=did.get('expected_length', 0))
        ttk.Entry(form_frame, textvariable=expected_len_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Min/Max Length
        ttk.Label(form_frame, text="Min Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        min_len_var = tk.IntVar(value=did.get('min_length', 0))
        ttk.Entry(form_frame, textvariable=min_len_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(form_frame, text="Max Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        max_len_var = tk.IntVar(value=did.get('max_length', 0))
        ttk.Entry(form_frame, textvariable=max_len_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Read Config
        ttk.Label(form_frame, text="Read Configuration", font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        read_callback_var = tk.StringVar(value=did.get('read_config', {}).get('callback', ''))
        ttk.Label(form_frame, text="Callback:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=read_callback_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        read_length_getter_var = tk.StringVar(value=did.get('read_config', {}).get('length_getter', '') or '')
        ttk.Label(form_frame, text="Length Getter:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=read_length_getter_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Read Session Support
        ttk.Label(form_frame, text="Session Support:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_session_frame = ttk.Frame(form_frame)
        read_session_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        available_sessions = config.get('sessions', [])
        read_session_vars = {}
        current_read_sessions = did.get('read_config', {}).get('supported_sessions', [])
        
        for i, session in enumerate(available_sessions):
            var = tk.BooleanVar(value=session['session_name'] in current_read_sessions)
            read_session_vars[session['session_name']] = var
            ttk.Checkbutton(read_session_frame, text=session['session_name'], variable=var).grid(row=i, column=0, sticky=tk.W)
        row += 1
        
        # Read Security Levels
        ttk.Label(form_frame, text="Required Security:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_security_frame = ttk.Frame(form_frame)
        read_security_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        available_security = config.get('security_levels', [])
        read_security_vars = {}
        current_read_security = did.get('read_config', {}).get('required_security_levels', [])
        
        for i, sec in enumerate(available_security):
            sec_name = f"Level {sec['security_level']}"
            var = tk.BooleanVar(value=sec['security_level'] in current_read_security)
            read_security_vars[sec['security_level']] = var
            ttk.Checkbutton(read_security_frame, text=sec_name, variable=var).grid(row=i, column=0, sticky=tk.W)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Write Config
        ttk.Label(form_frame, text="Write Configuration", font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        write_callback_var = tk.StringVar(value=did.get('write_config', {}).get('callback', ''))
        ttk.Label(form_frame, text="Callback:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=write_callback_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Write Session Support
        ttk.Label(form_frame, text="Session Support:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_session_frame = ttk.Frame(form_frame)
        write_session_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        write_session_vars = {}
        current_write_sessions = did.get('write_config', {}).get('supported_sessions', [])
        
        for i, session in enumerate(available_sessions):
            var = tk.BooleanVar(value=session['session_name'] in current_write_sessions)
            write_session_vars[session['session_name']] = var
            ttk.Checkbutton(write_session_frame, text=session['session_name'], variable=var).grid(row=i, column=0, sticky=tk.W)
        row += 1
        
        # Write Security Levels
        ttk.Label(form_frame, text="Required Security:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_security_frame = ttk.Frame(form_frame)
        write_security_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        write_security_vars = {}
        current_write_security = did.get('write_config', {}).get('required_security_levels', [])
        
        for i, sec in enumerate(available_security):
            sec_name = f"Level {sec['security_level']}"
            var = tk.BooleanVar(value=sec['security_level'] in current_write_security)
            write_security_vars[sec['security_level']] = var
            ttk.Checkbutton(write_security_frame, text=sec_name, variable=var).grid(row=i, column=0, sticky=tk.W)
        row += 1
        
        write_validation_var = tk.BooleanVar(value=did.get('write_config', {}).get('semantic_validation', False))
        ttk.Checkbutton(form_frame, text="Semantic Validation", variable=write_validation_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=did.get('description', ''))
        ttk.Entry(form_frame, textvariable=desc_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Info label
        ttk.Label(form_frame, text="ℹ️ Changes are saved automatically", 
                 foreground='green', font=('', 9)).grid(row=row, column=0, columnspan=2, pady=10)
        
        # Auto-save function
        def save_changes(*args):
            try:
                config['dids'][index]['did'] = did_var.get()
                config['dids'][index]['did_name'] = did_name_var.get()
                config['dids'][index]['fixed_length'] = fixed_var.get()
                config['dids'][index]['expected_length'] = expected_len_var.get()
                config['dids'][index]['min_length'] = min_len_var.get()
                config['dids'][index]['max_length'] = max_len_var.get()
                
                # Read config
                read_cfg = {}
                if read_callback_var.get():
                    read_cfg['callback'] = read_callback_var.get()
                    read_cfg['length_getter'] = read_length_getter_var.get() if read_length_getter_var.get() else None
                    selected_read_sessions = [name for name, var in read_session_vars.items() if var.get()]
                    read_cfg['supported_sessions'] = selected_read_sessions
                    selected_read_security = [level for level, var in read_security_vars.items() if var.get()]
                    read_cfg['required_security_levels'] = selected_read_security
                    config['dids'][index]['read_config'] = read_cfg
                elif 'read_config' in config['dids'][index]:
                    del config['dids'][index]['read_config']
                
                # Write config
                write_cfg = {}
                if write_callback_var.get():
                    write_cfg['callback'] = write_callback_var.get()
                    selected_write_sessions = [name for name, var in write_session_vars.items() if var.get()]
                    write_cfg['supported_sessions'] = selected_write_sessions
                    selected_write_security = [level for level, var in write_security_vars.items() if var.get()]
                    write_cfg['required_security_levels'] = selected_write_security
                    write_cfg['semantic_validation'] = write_validation_var.get()
                    config['dids'][index]['write_config'] = write_cfg
                elif 'write_config' in config['dids'][index]:
                    del config['dids'][index]['write_config']
                
                config['dids'][index]['description'] = desc_var.get()
                
                callbacks['set_modified']()
                callbacks['refresh_ui']()
            except Exception:
                pass
        
        # Bind all text variables
        for var in [did_var, did_name_var, fixed_var, expected_len_var, min_len_var, max_len_var,
                    read_callback_var, read_length_getter_var,
                    write_callback_var, write_validation_var, desc_var]:
            var.trace_add('write', save_changes)
        
        # Bind session checkboxes
        for var in list(read_session_vars.values()) + list(write_session_vars.values()):
            var.trace_add('write', save_changes)
        
        # Bind security level checkboxes
        for var in list(read_security_vars.values()) + list(write_security_vars.values()):
            var.trace_add('write', save_changes)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Configure canvas scrolling
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        
        form_frame.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)
        
        # Initial update
        form_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Mousewheel scrolling
        def on_mousewheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Unbind mousewheel when canvas is destroyed
        def cleanup():
            canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Destroy>", lambda e: cleanup())
    
    def show_info_panel(self, info_widget, did):
        """Display DID details in info panel"""
        info = f"DID Details\n"
        info += f"{'='*30}\n"
        info += f"DID: {did['did']}\n"
        info += f"Name: {did['did_name']}\n"
        info += f"Length: {'Fixed' if did.get('fixed_length', True) else 'Variable'} ({did.get('expected_length', 0)} bytes)\n"
        if not did.get('fixed_length', True):
            info += f"Range: {did.get('min_length', 0)}-{did.get('max_length', 0)} bytes\n"
        if 'read_config' in did:
            info += f"Read: ✓ ({did['read_config'].get('callback', 'N/A')})\n"
        if 'write_config' in did:
            info += f"Write: ✓ ({did['write_config'].get('callback', 'N/A')})\n"
        info += f"\nDescription:\n{did.get('description', '')}\n"
        info_widget.insert(1.0, info)