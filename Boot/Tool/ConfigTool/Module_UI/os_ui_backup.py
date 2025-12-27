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
        
        # Cycle time options
        self.cycle_options = ['1ms', '10ms', '20ms', '100ms', '1000ms']
        self.task_type_options = ['init', 'cyclic', 'background']
    
    def setup_tab(self):
        """Setup OS configuration tab
        
        Returns:
            Treeview widget for task list
        """
        # Main container
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and description
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(title_frame, text="⚙️ OS Task Scheduler Configuration", 
                 style='Title.TLabel').pack(anchor=tk.W)
        ttk.Label(title_frame, 
                 text="Configure initialization, cyclic, and background tasks for the scheduler",
                 style='Info.TLabel').pack(anchor=tk.W, pady=(5, 0))
        
        # Tree view for tasks
        tree_frame = ttk.LabelFrame(main_frame, text="📋 Configured Tasks", padding="10")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview with scrollbar
        tree_container = ttk.Frame(tree_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_container, 
                                 columns=('type', 'function', 'cycle', 'description'),
                                 show='headings',
                                 yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        # Configure columns
        self.tree.heading('type', text='Type')
        self.tree.heading('function', text='Function Name')
        self.tree.heading('cycle', text='Cycle Time')
        self.tree.heading('description', text='Description')
        
        self.tree.column('type', width=100)
        self.tree.column('function', width=200)
        self.tree.column('cycle', width=100)
        self.tree.column('description', width=300)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Double-click to edit
        self.tree.bind('<Double-1>', lambda e: self.on_edit_callback() if hasattr(self, 'on_edit_callback') else None)
        
        return self.tree
    
    def setup_toolbar(self, add_cmd, edit_cmd, delete_cmd):
        """Setup toolbar with action buttons
        
        Args:
            add_cmd: Callback for add button
            edit_cmd: Callback for edit button
            delete_cmd: Callback for delete button
            
        Returns:
            StringVar for task count display
        """
        toolbar_frame = ttk.Frame(self.parent_frame)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Action buttons
        ttk.Button(toolbar_frame, text="➕ Add Task", command=add_cmd, 
                  style='Success.TButton', width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="✏️ Edit", command=edit_cmd,
                  style='TButton', width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="🗑️ Delete", command=delete_cmd,
                  style='Warning.TButton', width=15).pack(side=tk.LEFT, padx=2)
        
        # Store callbacks for double-click
        self.on_edit_callback = edit_cmd
        
        # Task count
        self.count_var = tk.StringVar(value="0")
        count_frame = ttk.Frame(toolbar_frame)
        count_frame.pack(side=tk.RIGHT)
        ttk.Label(count_frame, text="Total Tasks:", font=('', 9)).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(count_frame, textvariable=self.count_var, 
                 font=('', 9, 'bold'), foreground='#0066cc').pack(side=tk.LEFT)
        
        return self.count_var
    
    def refresh_tree(self, config):
        """Refresh tree view with task data
        
        Args:
            config: Full configuration dictionary
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Extract tasks from config
        tasks = config.get('os_tasks', []) if isinstance(config, dict) else []
        
        # Group tasks by type for better visualization
        init_tasks = [t for t in tasks if isinstance(t, dict) and t.get('task_type') == 'init']
        cyclic_tasks = [t for t in tasks if isinstance(t, dict) and t.get('task_type') == 'cyclic']
        bg_tasks = [t for t in tasks if isinstance(t, dict) and t.get('task_type') == 'background']
        
        # Add tasks with color coding
        for task in init_tasks:
            self._add_task_to_tree(task, 'init_tag')
        
        for task in cyclic_tasks:
            self._add_task_to_tree(task, 'cyclic_tag')
        
        for task in bg_tasks:
            self._add_task_to_tree(task, 'bg_tag')
        
        # Configure tags for color coding
        self.tree.tag_configure('init_tag', background='#e3f2fd')      # Light blue
        self.tree.tag_configure('cyclic_tag', background='#f3e5f5')    # Light purple
        self.tree.tag_configure('bg_tag', background='#fff3e0')        # Light orange
    
    def _add_task_to_tree(self, task, tag):
        """Add a single task to tree view"""
        task_type = task.get('task_type', '')
        func_name = task.get('function_name', '')
        cycle_time = task.get('cycle_time', '-')
        description = task.get('description', '')
        
        # Format type for display
        type_display = {
            'init': '🔧 Init',
            'cyclic': '🔄 Cyclic',
            'background': '⏳ Background'
        }.get(task_type, task_type)
        
        self.tree.insert('', tk.END,
                        values=(type_display, func_name, cycle_time, description),
                        tags=(tag,))
    
    def show_edit_form(self, config_panel_frame, index, config, callbacks):
        """Show task edit form in config panel (not dialog)
        
        Args:
            config_panel_frame: Parent frame to display form
            index: Task index to edit (None for new task)
            config: Full configuration dict
            callbacks: Dict with 'set_modified' and 'refresh_ui' functions
        """
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        tasks = config.get('os_tasks', [])
        task_data = tasks[index] if index is not None and index < len(tasks) else None
        is_new = task_data is None
        
        # Create scrollable form
        canvas = tk.Canvas(config_panel_frame)
        scrollbar = ttk.Scrollbar(config_panel_frame, orient="vertical", command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="20")
        
        canvas.create_window((0, 0), window=form_frame, anchor="nw", tags="canvas_frame")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Title
        title = "Add New OS Task" if is_new else f"Edit OS Task"
        ttk.Label(form_frame, text=title, font=('', 12, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=(0, 15), sticky=tk.W)
        
        row = 1
        
        # Info Box
        info_frame = ttk.LabelFrame(form_frame, text="ℹ️ Hướng Dẫn Nhanh", padding="10")
        info_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        info_text = (
            "• Init Task: Chạy 1 lần khi khởi động (VD: khởi tạo phần cứng)\n"
            "• Cyclic Task: Chạy định kỳ theo chu kỳ (VD: đọc CAN mỗi 10ms)\n"
            "• Background Task: Chạy khi CPU rảnh (VD: lập trình Flash)"
        )
        ttk.Label(info_frame, text=info_text, font=('', 8), foreground='#444').pack(anchor=tk.W)
        row += 1
        
        # Task Type
        ttk.Label(form_frame, text="Task Type:", font=('', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 5))
        row += 1
        
        task_type_var = tk.StringVar(value=task_data.get('task_type', 'cyclic') if task_data else 'cyclic')
        task_type_frame = ttk.Frame(form_frame)
        task_type_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        ttk.Label(form_frame, text="Task Type:", font=('', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 5))
        row += 1
        
        # Task Type
        task_type_var = tk.StringVar(value=task_data.get('task_type', 'cyclic') if task_data else 'cyclic')
        task_type_frame = ttk.Frame(form_frame)
        task_type_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Radiobutton(task_type_frame, text="🔧 Initialization (chạy 1 lần)", 
                       variable=task_type_var, value='init').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(task_type_frame, text="🔄 Cyclic (chạy định kỳ)", 
                       variable=task_type_var, value='cyclic').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(task_type_frame, text="⏳ Background (chạy khi rảnh)", 
                       variable=task_type_var, value='background').pack(side=tk.LEFT)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Task Name (also used as function name)
        ttk.Label(form_frame, text="Task Name:", font=('', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        task_name_var = tk.StringVar(value=task_data.get('task_name', '') if task_data else '')
        ttk.Entry(form_frame, textvariable=task_name_var, width=40).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        row += 1
        
        help_frame = ttk.Frame(form_frame)
        help_frame.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 10))
        ttk.Label(help_frame, text="📌 Tên task (dùng làm tên hàm C)", 
                 font=('', 8), foreground='#666').pack(anchor=tk.W)
        ttk.Label(help_frame, text="   Ví dụ: can_receive_task, sensor_read_task", 
                 font=('', 8), foreground='#888').pack(anchor=tk.W)
        ttk.Label(help_frame, text="   ⚙️ Hàm C: void <task_name>(void) { ... }", 
                 font=('', 8), foreground='#0066cc').pack(anchor=tk.W)
        row += 1
        
        # Cycle Time (only for cyclic tasks)
        cycle_label = ttk.Label(form_frame, text="Cycle Time:", font=('', 9, 'bold'))
        cycle_label.grid(row=row, column=0, sticky=tk.W, pady=5)
        
        # Convert integer to string with 'ms' for display
        cycle_value = task_data.get('cycle_time', 10) if task_data else 10
        cycle_str = f"{cycle_value}ms" if isinstance(cycle_value, int) else str(cycle_value)
        cycle_time_var = tk.StringVar(value=cycle_str)
        
        cycle_combo = ttk.Combobox(form_frame, textvariable=cycle_time_var, 
                                   values=['1ms', '10ms', '20ms', '100ms', '1000ms'],
                                   state='readonly', width=37)
        cycle_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        row += 1
        
        help_frame3 = ttk.Frame(form_frame)
        help_frame3.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 10))
        ttk.Label(help_frame3, text="⏱️ Task chạy mỗi bao lâu (chỉ cho Cyclic Task)", 
                 font=('', 8), foreground='#666').pack(anchor=tk.W)
        ttk.Label(help_frame3, text="   • 1ms → 1000 lần/giây (sensor nhanh, PWM)", 
                 font=('', 8), foreground='#888').pack(anchor=tk.W)
        ttk.Label(help_frame3, text="   • 10ms → 100 lần/giây (CAN, communication)", 
                 font=('', 8), foreground='#888').pack(anchor=tk.W)
        ttk.Label(help_frame3, text="   • 100ms → 10 lần/giây (diagnostics)", 
                 font=('', 8), foreground='#888').pack(anchor=tk.W)
        ttk.Label(help_frame3, text="   • 1000ms → 1 lần/giây (heartbeat, watchdog)", 
                 font=('', 8), foreground='#888').pack(anchor=tk.W)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        description_text = tk.Text(form_frame, width=40, height=4, wrap=tk.WORD)
        description_text.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        if task_data and task_data.get('description'):
            description_text.insert('1.0', task_data['description'])
        row += 1
        
        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=task_data.get('enabled', True) if task_data else True)
        ttk.Checkbutton(form_frame, text="Task Enabled (can be disabled at runtime)", 
                       variable=enabled_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        row += 1
        
        # Configure column weights
        form_frame.columnconfigure(1, weight=1)
        
        # Toggle cycle time visibility based on task type
        def on_task_type_change(*args):
            task_type = task_type_var.get()
            if task_type == 'cyclic':
                cycle_label.grid()
                cycle_combo.config(state='readonly')
                help_frame3.grid()
            else:
                cycle_label.grid_remove()
                cycle_combo.config(state='disabled')
                cycle_time_var.set('-')
                help_frame3.grid_remove()
        
        task_type_var.trace_add('write', on_task_type_change)
        on_task_type_change()  # Initial state
        
        # Auto-save function with re-entry protection
        saving = [False]  # Use list to allow modification in nested function
        
        def save_changes(*args):
            # Prevent re-entrant calls
            if saving[0]:
                return
            
            try:
                saving[0] = True
                
                task_name = task_name_var.get().strip()
                task_type = task_type_var.get()
                
                # Skip if essential fields are empty
                if not task_name:
                    return
                
                # Build task data (use task_name as function_name)
                task_obj = {
                    'task_type': task_type,
                    'task_name': task_name,
                    'function_name': task_name,  # Same as task_name
                    'description': description_text.get('1.0', tk.END).strip(),
                    'enabled': enabled_var.get()
                }
                
                # Add cycle time for cyclic tasks (convert to integer)
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
                if index is not None:
                    config['os_tasks'][index] = task_obj
                else:
                    config['os_tasks'].append(task_obj)
                
                # Mark as modified only (no refresh to avoid re-triggering)
                callbacks['set_modified']()
            except Exception as e:
                print(f"Error in auto-save: {e}")
            finally:
                saving[0] = False
        
        # Manual refresh button instead of auto-refresh
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        ttk.Button(button_frame, text="🔄 Refresh Tree", 
                  command=callbacks['refresh_tree']).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Bind auto-save to all variables (but don't refresh tree automatically)
        task_type_var.trace_add('write', save_changes)
        task_name_var.trace_add('write', save_changes)
        cycle_time_var.trace_add('write', save_changes)
        enabled_var.trace_add('write', save_changes)
        
        # Bind description text changes (different method for Text widget)
        description_text.bind('<<Modified>>', lambda e: (
            description_text.edit_modified(False),
            save_changes()
        ))
        
        # Configure canvas scrolling
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas.itemconfig("canvas_frame", width=event.width)
        
        form_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Bind mousewheel for scrolling - simple version
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
