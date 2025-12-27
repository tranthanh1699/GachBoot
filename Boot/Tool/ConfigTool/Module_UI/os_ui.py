"""
OS UI Module - Task Scheduler Configuration Interface
Provides UI components for OS task configuration
"""

import tkinter as tk
from tkinter import ttk, messagebox


class OsUI:
    """UI handler for OS task configuration"""
    
    def __init__(self, parent_frame, root_window):
        self.parent_frame = parent_frame
        self.root_window = root_window
        self.tree = None
        self.count_var = None
    
    def setup_tab(self):
        """Setup OS Tasks tab and return treeview"""
        # Task tree with scrollbar
        tree_frame = ttk.Frame(self.parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('Type', 'Function', 'Cycle', 'Enabled')
        self.tree = ttk.Treeview(tree_frame, columns=columns, 
                                 show='tree headings', height=15)
        
        # Column headers
        self.tree.heading('#0', text='Task Name')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Function', text='Function')
        self.tree.heading('Cycle', text='Cycle Time')
        self.tree.heading('Enabled', text='Enabled')
        
        # Column widths
        self.tree.column('#0', width=200)
        self.tree.column('Type', width=100)
        self.tree.column('Function', width=200)
        self.tree.column('Cycle', width=80)
        self.tree.column('Enabled', width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return self.tree
    
    def setup_toolbar(self, add_cmd, edit_cmd, delete_cmd):
        """Setup toolbar with action buttons"""
        # Create toolbar frame at top
        toolbar = ttk.Frame(self.parent_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, before=self.tree.master)
        
        ttk.Button(toolbar, text="➕ Add Task", command=add_cmd, style='Success.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Task", command=edit_cmd, style='TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Task", command=delete_cmd, style='Warning.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text="Total Tasks: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        return count_var
    
    def refresh_tree(self, config):
        """Refresh task tree with config data"""
        if not self.tree:
            return
        
        self.tree.delete(*self.tree.get_children())
        
        tasks = config.get('os_tasks', [])
        for i, task in enumerate(tasks):
            task_type = task.get('task_type', 'unknown')
            task_name = task.get('task_name', f'Task_{i}')
            func_name = task.get('function_name', task_name)
            cycle_time = task.get('cycle_time', '-')
            if isinstance(cycle_time, int):
                cycle_time = f"{cycle_time}ms"
            enabled = '✓' if task.get('enabled', True) else '✗'
            
            self.tree.insert('', tk.END, text=task_name, 
                           values=(task_type, func_name, cycle_time, enabled),
                           tags=(f'task_{i}',))
    
    def show_edit_form(self, config_panel_frame, index, config, callbacks):
        """Show OS task edit form with auto-save"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        task_data = None
        is_new = index is None
        if not is_new and 'os_tasks' in config and index < len(config['os_tasks']):
            task_data = config['os_tasks'][index]
        
        # Create scrollable form
        canvas = tk.Canvas(config_panel_frame)
        scrollbar = ttk.Scrollbar(config_panel_frame, orient="vertical", command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="10")
        
        canvas.create_window((0, 0), window=form_frame, anchor="nw", tags="canvas_frame")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Title
        title = "Add New OS Task" if is_new else "Edit OS Task"
        ttk.Label(form_frame, text=title, font=('', 12, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # Info label
        ttk.Label(form_frame, text="ℹ️ Changes are saved automatically", 
                 foreground='green', font=('', 9)).grid(
            row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        # Task Type
        ttk.Label(form_frame, text="Task Type:").grid(row=row, column=0, sticky=tk.W, pady=5)
        task_type_var = tk.StringVar(value=task_data.get('task_type', 'cyclic') if task_data else 'cyclic')
        type_frame = ttk.Frame(form_frame)
        type_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(type_frame, text="Init", variable=task_type_var, value='init').pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Cyclic", variable=task_type_var, value='cyclic').pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Background", variable=task_type_var, value='background').pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Task Name
        ttk.Label(form_frame, text="Task Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        task_name_var = tk.StringVar(value=task_data.get('task_name', '') if task_data else '')
        task_name_entry = ttk.Entry(form_frame, textvariable=task_name_var, width=30)
        task_name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Cycle Time (only for cyclic tasks)
        cycle_label = ttk.Label(form_frame, text="Cycle Time:")
        cycle_label.grid(row=row, column=0, sticky=tk.W, pady=5)
        
        cycle_value = task_data.get('cycle_time', 10) if task_data else 10
        cycle_str = f"{cycle_value}ms" if isinstance(cycle_value, int) else str(cycle_value)
        cycle_time_var = tk.StringVar(value=cycle_str)
        
        cycle_combo = ttk.Combobox(form_frame, textvariable=cycle_time_var, 
                                   values=['1ms', '10ms', '20ms', '100ms', '1000ms'],
                                   state='readonly', width=27)
        cycle_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        description_text = tk.Text(form_frame, width=30, height=4, wrap=tk.WORD)
        description_text.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        if task_data and task_data.get('description'):
            description_text.insert('1.0', task_data['description'])
        row += 1
        
        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=task_data.get('enabled', True) if task_data else True)
        ttk.Checkbutton(form_frame, text="Enabled", variable=enabled_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        row += 1
        
        # Configure column weights
        form_frame.columnconfigure(1, weight=1)
        
        # Toggle cycle time visibility based on task type
        def on_task_type_change(*args):
            task_type = task_type_var.get()
            if task_type == 'cyclic':
                cycle_label.grid()
                cycle_combo.grid()
            else:
                cycle_label.grid_remove()
                cycle_combo.grid_remove()
        
        task_type_var.trace_add('write', on_task_type_change)
        on_task_type_change()  # Initial state
        
        # Track current index (mutable to update after first save)
        current_index = [index]  # Use list to allow mutation in nested function
        
        # Save function (called on FocusOut/Enter)
        def save_changes():
            try:
                task_name = task_name_var.get().strip()
                task_type = task_type_var.get()
                
                print(f"[OS_UI] save_changes called: name='{task_name}', type='{task_type}'")
                
                # Validate - don't save if empty
                if not task_name:
                    print("[OS_UI] Skipping save - empty task name")
                    return
                
                # Build task data
                task_obj = {
                    'task_type': task_type,
                    'task_name': task_name,
                    'function_name': task_name,
                    'description': description_text.get('1.0', tk.END).strip(),
                    'enabled': enabled_var.get()
                }
                
                # Add cycle time for cyclic tasks
                if task_type == 'cyclic':
                    cycle_str = cycle_time_var.get()
                    try:
                        task_obj['cycle_time'] = int(cycle_str.replace('ms', ''))
                    except:
                        task_obj['cycle_time'] = 10
                
                # Ensure os_tasks exists
                if 'os_tasks' not in config:
                    config['os_tasks'] = []
                
                # Update or add task
                if current_index[0] is not None:
                    # Update existing task
                    config['os_tasks'][current_index[0]] = task_obj
                    print(f"[OS_UI] Updated task at index {current_index[0]}")
                else:
                    # Add new task and track its index for future updates
                    config['os_tasks'].append(task_obj)
                    current_index[0] = len(config['os_tasks']) - 1
                    print(f"[OS_UI] Added new task at index {current_index[0]}")
                
                print("[OS_UI] Calling set_modified...")
                callbacks['set_modified']()
                print("[OS_UI] Calling refresh_ui...")
                callbacks['refresh_ui']()
            except Exception as e:
                print(f"[OS_UI] Error in save_changes: {e}")
        
        # Bind save to FocusOut event (save when user leaves form)
        def on_focus_out(event):
            save_changes()
        
        for widget in [task_name_entry, cycle_combo, description_text]:
            widget.bind('<FocusOut>', on_focus_out)
        
        # Also save on Enter key in entry fields
        task_name_entry.bind('<Return>', lambda e: save_changes())
        
        # Configure canvas scrolling
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas.itemconfig("canvas_frame", width=event.width)
        
        form_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        on_frame_configure()
        
        # Mousewheel scrolling
        def on_mousewheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Unbind mousewheel when canvas is destroyed
        def cleanup():
            canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Destroy>", lambda e: cleanup())
