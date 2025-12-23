"""
Session UI Module - Render Session configuration UI
"""

import tkinter as tk
from tkinter import ttk


class SessionUI:
    """UI renderer for Sessions"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.session_tree = None
        self.session_count_var = None
    
    def setup_tab(self):
        """Setup session tab with treeview"""
        # Tree view for sessions
        tree_frame = ttk.Frame(self.parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("Name", "Value", "Description")
        self.session_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        widths = {"Name": 300, "Value": 100, "Description": 550}
        for col in columns:
            self.session_tree.heading(col, text=col)
            self.session_tree.column(col, width=widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.session_tree.yview)
        self.session_tree.configure(yscrollcommand=scrollbar.set)
        
        self.session_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return self.session_tree
    
    def setup_toolbar(self, add_cmd, edit_cmd, delete_cmd):
        """Setup toolbar with action buttons"""
        toolbar = ttk.Frame(self.parent_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Add Session", command=add_cmd, style='Success.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Session", command=edit_cmd, style='TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Session", command=delete_cmd, style='Warning.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text=f"Total Sessions: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.session_count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=self.session_count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        return self.session_count_var
    
    def refresh_tree(self, sessions):
        """Refresh session treeview with data"""
        self.session_tree.delete(*self.session_tree.get_children())
        
        for session in sessions:
            self.session_tree.insert('', tk.END, values=(
                session['session_name'],
                session['session_value'],
                session.get('description', '')
            ))
        
        if self.session_count_var:
            self.session_count_var.set(str(len(sessions)))
    
    def show_edit_form(self, config_panel_frame, index, config, set_modified_callback):
        """Render edit form for session with auto-save"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        session = config['sessions'][index]
        
        # Create scrollable form
        canvas = tk.Canvas(config_panel_frame)
        scrollbar = ttk.Scrollbar(config_panel_frame, orient="vertical", command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="10")
        
        canvas.create_window((0, 0), window=form_frame, anchor="nw", tags="canvas_frame")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(form_frame, text=f"Edit Session", font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # Session Name
        ttk.Label(form_frame, text="Session Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        session_name_var = tk.StringVar(value=session['session_name'])
        ttk.Entry(form_frame, textvariable=session_name_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Session Value
        ttk.Label(form_frame, text="Session Value (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        session_value_var = tk.StringVar(value=session['session_value'])
        ttk.Entry(form_frame, textvariable=session_value_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=session.get('description', ''))
        ttk.Entry(form_frame, textvariable=desc_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Auto-save function
        def save_changes(*args):
            config['sessions'][index]['session_name'] = session_name_var.get()
            config['sessions'][index]['session_value'] = session_value_var.get()
            config['sessions'][index]['description'] = desc_var.get()
            set_modified_callback()
        
        # Bind to save on change
        for var in [session_name_var, session_value_var, desc_var]:
            var.trace_add('write', save_changes)
        
        # Info label
        info_label = ttk.Label(form_frame, text="ℹ️ Changes are saved automatically", 
                              foreground='green', font=('', 9, 'italic'))
        info_label.grid(row=row, column=0, columnspan=2, pady=20)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Update scroll region
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas_width = event.width
            canvas.itemconfig("canvas_frame", width=canvas_width)
        
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
    
    def show_info_panel(self, info_text_widget, session):
        """Show session details in info panel"""
        info = f"Session Details\n"
        info += f"{'='*30}\n"
        info += f"Name: {session['session_name']}\n"
        info += f"Value: {session['session_value']}\n"
        info += f"\nDescription:\n{session.get('description', '')}\n"
        
        info_text_widget.config(state=tk.NORMAL)
        info_text_widget.delete(1.0, tk.END)
        info_text_widget.insert(1.0, info)
        info_text_widget.config(state=tk.DISABLED)

