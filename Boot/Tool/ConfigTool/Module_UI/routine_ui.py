"""
Routine UI Module
Handles UI rendering for Routine configuration (Service 0x31)
"""

import tkinter as tk
from tkinter import ttk, messagebox


class RoutineUI:
    """UI module for Routine configuration"""
    
    def __init__(self, parent_frame):
        """Initialize Routine UI module"""
        self.parent = parent_frame
        self.tree = None
    
    def setup_tab(self):
        """Setup Routines tab and return treeview"""
        # Toolbar
        toolbar = ttk.Frame(self.parent)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Treeview
        tree_frame = ttk.Frame(self.parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("RID", "Name", "Callback", "Subfunctions", "Sessions", "Security", "Description")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        widths = {"RID": 80, "Name": 200, "Callback": 180, "Subfunctions": 150, 
                  "Sessions": 120, "Security": 80, "Description": 200}
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
        
        ttk.Button(toolbar, text="➕ Add Routine", command=add_cmd, style='Success.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Routine", command=edit_cmd, style='TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Routine", command=delete_cmd, style='Warning.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text=f"Total Routines: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        return count_var
    
    def refresh_tree(self, routines):
        """Refresh treeview with Routines data"""
        self.tree.delete(*self.tree.get_children())
        
        for routine in routines:
            subfuncs = ', '.join(routine.get('supported_subfunctions', []))
            sessions_short = ', '.join([s.split('_')[1] if '_' in s else s 
                                       for s in routine.get('supported_sessions', [])])
            security = ', '.join([str(s) for s in routine.get('required_security_levels', [])]) or 'All'
            
            self.tree.insert('', tk.END, values=(
                routine['rid'],
                routine['routine_name'],
                routine['callback_function'],
                subfuncs,
                sessions_short,
                security,
                routine.get('description', '')
            ))
    
    def show_info_panel(self, info_text, routine):
        """Show routine info in the info panel"""
        info_text.insert(tk.END, f"Routine {routine['rid']}\n")
        info_text.insert(tk.END, f"{'='*30}\n")
        info_text.insert(tk.END, f"Name: {routine['routine_name']}\n")
        info_text.insert(tk.END, f"Callback: {routine['callback_function']}\n")
        info_text.insert(tk.END, f"\nSubfunctions:\n")
        for sf in routine.get('supported_subfunctions', []):
            info_text.insert(tk.END, f"  • {sf}\n")
        info_text.insert(tk.END, f"\nSessions:\n")
        for session in routine.get('supported_sessions', []):
            info_text.insert(tk.END, f"  • {session}\n")
        security_levels = routine.get('required_security_levels', [])
        if security_levels:
            info_text.insert(tk.END, f"\nSecurity Levels: {', '.join([str(s) for s in security_levels])}\n")
        else:
            info_text.insert(tk.END, f"\nSecurity: All levels allowed\n")
        info_text.insert(tk.END, f"\nDescription:\n{routine.get('description', 'N/A')}\n")
    
    def show_edit_form(self, config_panel_frame, index, config, callbacks):
        """Show Routine edit form with auto-save"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        routine = config['routines'][index]
        
        # Create scrollable form
        canvas = tk.Canvas(config_panel_frame, bg='white')
        scrollbar = ttk.Scrollbar(config_panel_frame, orient=tk.VERTICAL, command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="10")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas_frame = canvas.create_window((0, 0), window=form_frame, anchor=tk.NW)
        
        # Configure column weights
        form_frame.columnconfigure(1, weight=1)
        
        ttk.Label(form_frame, text="Edit Routine", font=('', 12, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # RID
        ttk.Label(form_frame, text="RID (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        rid_var = tk.StringVar(value=routine['rid'])
        ttk.Entry(form_frame, textvariable=rid_var, width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Routine Name
        ttk.Label(form_frame, text="Routine Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        routine_name_var = tk.StringVar(value=routine['routine_name'])
        ttk.Entry(form_frame, textvariable=routine_name_var, width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Callback Function
        ttk.Label(form_frame, text="Callback Function:").grid(row=row, column=0, sticky=tk.W, pady=5)
        callback_var = tk.StringVar(value=routine['callback_function'])
        ttk.Entry(form_frame, textvariable=callback_var, width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=routine.get('description', ''))
        ttk.Entry(form_frame, textvariable=desc_var, width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Supported Subfunctions
        ttk.Label(form_frame, text="Supported Subfunctions:", font=('', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        subfunction_frame = ttk.Frame(form_frame)
        subfunction_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        available_subfunctions = ['START', 'STOP', 'REQUEST_RESULTS']
        current_subfunctions = routine.get('supported_subfunctions', [])
        subfunction_vars = {}
        
        for i, subfunc in enumerate(available_subfunctions):
            var = tk.BooleanVar(value=subfunc in current_subfunctions)
            subfunction_vars[subfunc] = var
            cb = ttk.Checkbutton(subfunction_frame, text=subfunc, variable=var)
            cb.grid(row=0, column=i, sticky=tk.W, padx=10)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Supported Sessions
        ttk.Label(form_frame, text="Supported Sessions:", font=('', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        session_frame = ttk.Frame(form_frame)
        session_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        available_sessions = config.get('sessions', [])
        current_sessions = routine.get('supported_sessions', [])
        session_vars = {}
        
        for i, session in enumerate(available_sessions):
            var = tk.BooleanVar(value=session['session_name'] in current_sessions)
            session_vars[session['session_name']] = var
            cb = ttk.Checkbutton(session_frame, text=session['session_name'], variable=var)
            cb.grid(row=i, column=0, sticky=tk.W, pady=2)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Required Security Levels
        ttk.Label(form_frame, text="Required Security Levels:", font=('', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        security_frame = ttk.Frame(form_frame)
        security_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        available_security = config.get('security_levels', [])
        current_security = routine.get('required_security_levels', [])
        security_vars = {}
        
        if available_security:
            for i, sec in enumerate(available_security):
                sec_name = f"Level {sec['security_level']}"
                var = tk.BooleanVar(value=sec['security_level'] in current_security)
                security_vars[sec['security_level']] = var
                cb = ttk.Checkbutton(security_frame, text=sec_name, variable=var)
                cb.grid(row=i, column=0, sticky=tk.W, pady=2)
        else:
            ttk.Label(security_frame, text="No security levels defined", 
                     foreground='gray').grid(row=0, column=0, sticky=tk.W)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Subfunction Parameters Configuration
        ttk.Label(form_frame, text="Subfunction Parameters:", font=('', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Get current subfunction parameters
        current_params = routine.get('subfunction_parameters', {})
        subfunction_param_vars = {}
        subfunction_ui_frames = {}  # Store frames for each subfunction
        
        # Create parameter config for ALL subfunctions (always visible)
        for subfunc in ['START', 'STOP', 'REQUEST_RESULTS']:
            params = current_params.get(subfunc, {
                'option_record_length': 0,
                'option_record_description': 'No parameters',
                'status_record_length': 1,
                'status_record_description': 'Status byte'
            })
            
            # Create vars for all subfunctions
            opt_len_var = tk.IntVar(value=params.get('option_record_length', 0))
            opt_desc_var = tk.StringVar(value=params.get('option_record_description', 'No parameters'))
            stat_len_var = tk.IntVar(value=params.get('status_record_length', 1))
            stat_desc_var = tk.StringVar(value=params.get('status_record_description', 'Status byte'))
            
            # Store variables for saving
            subfunction_param_vars[subfunc] = {
                'option_length': opt_len_var,
                'option_description': opt_desc_var,
                'status_length': stat_len_var,
                'status_description': stat_desc_var
            }
            
            # Create frame for this subfunction (always create, will show/hide based on checkbox)
            subfunc_frame = ttk.Frame(form_frame)
            subfunc_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E))
            subfunction_ui_frames[subfunc] = subfunc_frame
            
            # Subfunction label
            ttk.Label(subfunc_frame, text=f"{subfunc}:", font=('', 9, 'bold')).grid(
                row=0, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
            
            # Option record length
            ttk.Label(subfunc_frame, text="  Option Length (bytes):").grid(
                row=1, column=0, sticky=tk.W, pady=2)
            ttk.Entry(subfunc_frame, textvariable=opt_len_var, width=10).grid(
                row=1, column=1, sticky=tk.W, pady=2)
            
            # Option description
            ttk.Label(subfunc_frame, text="  Option Description:").grid(
                row=2, column=0, sticky=tk.W, pady=2)
            ttk.Entry(subfunc_frame, textvariable=opt_desc_var, width=40).grid(
                row=2, column=1, sticky=(tk.W, tk.E), pady=2)
            
            # Status record length
            ttk.Label(subfunc_frame, text="  Status Length (bytes):").grid(
                row=3, column=0, sticky=tk.W, pady=2)
            ttk.Entry(subfunc_frame, textvariable=stat_len_var, width=10).grid(
                row=3, column=1, sticky=tk.W, pady=2)
            
            # Status description
            ttk.Label(subfunc_frame, text="  Status Description:").grid(
                row=4, column=0, sticky=tk.W, pady=2)
            ttk.Entry(subfunc_frame, textvariable=stat_desc_var, width=40).grid(
                row=4, column=1, sticky=(tk.W, tk.E), pady=2)
            
            # Show/hide frame based on current support
            if subfunc not in routine.get('supported_subfunctions', []):
                subfunc_frame.grid_remove()  # Hide but keep in grid manager
            
            row += 1
        
        # Function to toggle subfunction UI visibility
        def toggle_subfunction_ui(subfunc):
            """Show/hide subfunction parameter UI based on checkbox state"""
            if subfunction_vars[subfunc].get():
                subfunction_ui_frames[subfunc].grid()
            else:
                subfunction_ui_frames[subfunc].grid_remove()
        
        # Bind checkboxes to toggle UI visibility
        for subfunc in ['START', 'STOP', 'REQUEST_RESULTS']:
            subfunction_vars[subfunc].trace_add('write', lambda *args, sf=subfunc: toggle_subfunction_ui(sf))
        
        # Auto-save function (mark as modified on any change and update config)
        def on_change(*args):
            """Mark config as modified and update config when any field changes"""
            try:
                # Update config immediately
                config['routines'][index]['rid'] = rid_var.get()
                config['routines'][index]['routine_name'] = routine_name_var.get()
                config['routines'][index]['callback_function'] = callback_var.get()
                config['routines'][index]['description'] = desc_var.get()
                
                # Update sessions
                selected_sessions = [s for s, var in session_vars.items() if var.get()]
                config['routines'][index]['supported_sessions'] = selected_sessions
                
                # Mark as modified
                if 'save_callback' in callbacks:
                    callbacks['save_callback']()
            except Exception as e:
                print(f"[DEBUG] Error in on_change: {e}")
        
        # Bind all variables to auto-update
        rid_var.trace_add('write', on_change)
        routine_name_var.trace_add('write', on_change)
        callback_var.trace_add('write', on_change)
        desc_var.trace_add('write', on_change)
        
        # Bind subfunction checkboxes
        for var in subfunction_vars.values():
            var.trace_add('write', on_change)
        
        # Bind session checkboxes
        for var in session_vars.values():
            var.trace_add('write', on_change)
        
        # Bind security checkboxes
        for var in security_vars.values():
            var.trace_add('write', on_change)
        
        # Bind subfunction parameter variables
        for subfunc_vars in subfunction_param_vars.values():
            for var in subfunc_vars.values():
                var.trace_add('write', on_change)
        
        # Manual save function (called when closing form or generating code)
        def save_changes():
            """Save all form data to config"""
            print("[DEBUG] routine_ui.save_changes() called")
            try:
                # Update routine data
                config['routines'][index]['rid'] = rid_var.get()
                config['routines'][index]['routine_name'] = routine_name_var.get()
                config['routines'][index]['callback_function'] = callback_var.get()
                config['routines'][index]['description'] = desc_var.get()
                print(f"[DEBUG] Updated routine basic info: rid={rid_var.get()}")
                
                # Update subfunctions
                selected_subfunctions = [sf for sf, var in subfunction_vars.items() if var.get()]
                config['routines'][index]['supported_subfunctions'] = selected_subfunctions
                print(f"[DEBUG] Updated subfunctions: {selected_subfunctions}")
                
                # Update sessions
                selected_sessions = [s for s, var in session_vars.items() if var.get()]
                config['routines'][index]['supported_sessions'] = selected_sessions
                print(f"[DEBUG] Updated sessions: {selected_sessions}")
                
                # Update security levels
                selected_security = [sec for sec, var in security_vars.items() if var.get()]
                config['routines'][index]['required_security_levels'] = selected_security
                print(f"[DEBUG] Updated security: {selected_security}")
                
                # Update subfunction parameters - only save for selected subfunctions
                subfunction_parameters = {}
                
                # Save parameters only for selected subfunctions
                for subfunc in selected_subfunctions:
                    if subfunc not in subfunction_param_vars:
                        # Provide default if missing
                        subfunction_parameters[subfunc] = {
                            'option_record_length': 0,
                            'option_record_description': 'No parameters',
                            'status_record_length': 1,
                            'status_record_description': 'Status byte'
                        }
                    else:
                        vars_dict = subfunction_param_vars[subfunc]
                        subfunction_parameters[subfunc] = {
                            'option_record_length': vars_dict['option_length'].get(),
                            'option_record_description': vars_dict['option_description'].get(),
                            'status_record_length': vars_dict['status_length'].get(),
                            'status_record_description': vars_dict['status_description'].get()
                        }
                
                config['routines'][index]['subfunction_parameters'] = subfunction_parameters
                print(f"[DEBUG] Updated subfunction_parameters: {list(subfunction_parameters.keys())}")
                
                # Call save callback to save config to file
                if 'save_callback' in callbacks:
                    print("[DEBUG] Calling save_callback from save_changes()")
                    callbacks['save_callback']()
                else:
                    print("[DEBUG] No save_callback found in callbacks")
                
                print("[DEBUG] save_changes() completed successfully")
                return True
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
        
        # Store save function for external access
        form_frame.save_changes = save_changes
        
        # Info label
        info_label = ttk.Label(form_frame, text="✓ Changes are automatically saved", 
                              foreground='green', font=('', 9, 'italic'))
        info_label.grid(row=row, column=0, columnspan=2, pady=20)
        
        # Configure canvas scrolling
        def on_frame_configure(event):
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
            # Check if canvas still exists before scrolling
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Unbind mousewheel when canvas is destroyed
        def cleanup():
            canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Destroy>", lambda e: cleanup())
    
    def show_add_form(self, parent_window, config, on_add_callback):
        """Show dialog to add new routine"""
        dialog = tk.Toplevel(parent_window)
        dialog.title("Add New Routine")
        dialog.geometry("500x700")
        dialog.transient(parent_window)
        dialog.grab_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        
        # RID
        ttk.Label(form_frame, text="RID (hex, e.g., 0xFF00):").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        rid_var = tk.StringVar(value="0x")
        ttk.Entry(form_frame, textvariable=rid_var, width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Routine Name
        ttk.Label(form_frame, text="Routine Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        routine_name_var = tk.StringVar(value="ROUTINE_")
        ttk.Entry(form_frame, textvariable=routine_name_var, width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Callback Function
        ttk.Label(form_frame, text="Callback Function:").grid(row=row, column=0, sticky=tk.W, pady=5)
        callback_var = tk.StringVar(value="routine_")
        ttk.Entry(form_frame, textvariable=callback_var, width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=desc_var, width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Subfunctions
        ttk.Label(form_frame, text="Supported Subfunctions:").grid(
            row=row, column=0, sticky=(tk.N, tk.W), pady=5)
        subfunction_frame = ttk.Frame(form_frame)
        subfunction_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        subfunction_vars = {}
        for i, subfunc in enumerate(['START', 'STOP', 'REQUEST_RESULTS']):
            var = tk.BooleanVar(value=(subfunc == 'START'))
            subfunction_vars[subfunc] = var
            ttk.Checkbutton(subfunction_frame, text=subfunc, variable=var).grid(
                row=i, column=0, sticky=tk.W)
        row += 1
        
        # Sessions
        ttk.Label(form_frame, text="Supported Sessions:").grid(
            row=row, column=0, sticky=(tk.N, tk.W), pady=5)
        session_frame = ttk.Frame(form_frame)
        session_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        session_vars = {}
        for i, session in enumerate(config.get('sessions', [])):
            var = tk.BooleanVar()
            session_vars[session['session_name']] = var
            ttk.Checkbutton(session_frame, text=session['session_name'], variable=var).grid(
                row=i, column=0, sticky=tk.W)
        row += 1
        
        # Security Levels
        ttk.Label(form_frame, text="Required Security Levels:").grid(
            row=row, column=0, sticky=(tk.N, tk.W), pady=5)
        security_frame = ttk.Frame(form_frame)
        security_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        security_vars = {}
        for i, sec in enumerate(config.get('security_levels', [])):
            var = tk.BooleanVar()
            security_vars[sec['security_level']] = var
            ttk.Checkbutton(security_frame, text=f"Level {sec['security_level']}", 
                           variable=var).grid(row=i, column=0, sticky=tk.W)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def on_ok():
            """Validate and add routine"""
            rid = rid_var.get()
            routine_name = routine_name_var.get()
            callback = callback_var.get()
            
            if not rid.startswith('0x'):
                messagebox.showerror("Error", "RID must start with '0x'")
                return
            
            if not routine_name or not callback:
                messagebox.showerror("Error", "Routine name and callback are required")
                return
            
            # Build routine data
            new_routine = {
                'rid': rid,
                'routine_name': routine_name,
                'callback_function': callback,
                'description': desc_var.get(),
                'supported_subfunctions': [sf for sf, var in subfunction_vars.items() if var.get()],
                'supported_sessions': [s for s, var in session_vars.items() if var.get()],
                'required_security_levels': [sec for sec, var in security_vars.items() if var.get()],
                'option_record': {'description': 'No parameters', 'expected_length': 0},
                'status_record': {'description': 'Status byte'}
            }
            
            on_add_callback(new_routine)
            dialog.destroy()
        
        ttk.Button(button_frame, text="Add Routine", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
