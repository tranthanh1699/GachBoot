"""
Service UI Module - Render DCM Service configuration UI
"""

import tkinter as tk
from tkinter import ttk


class ServiceUI:
    """UI renderer for DCM Services"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.service_tree = None
        self.service_count_var = None
    
    def setup_tab(self):
        """Setup service tab with treeview and toolbar"""
        # Tree view for services
        tree_frame = ttk.Frame(self.parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('Service ID', 'Handler Function', 'Sessions', 'Security Levels')
        self.service_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        widths = {'Service ID': 100, 'Handler Function': 250, 'Sessions': 300, 'Security Levels': 150}
        for col in columns:
            self.service_tree.heading(col, text=col)
            self.service_tree.column(col, width=widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.service_tree.yview)
        self.service_tree.configure(yscrollcommand=scrollbar.set)
        
        self.service_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return self.service_tree
    
    def setup_toolbar(self, add_cmd, edit_cmd, delete_cmd):
        """Setup toolbar with action buttons"""
        toolbar = ttk.Frame(self.parent_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Add Service", command=add_cmd, style='Success.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Service", command=edit_cmd, style='TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Service", command=delete_cmd, style='Warning.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text=f"Total Services: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.service_count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=self.service_count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        return self.service_count_var
    
    def refresh_tree(self, services):
        """Refresh service treeview with data"""
        self.service_tree.delete(*self.service_tree.get_children())
        
        for service in services:
            sessions_str = ', '.join(service.get('supported_sessions', []))
            security_levels = service.get('required_security_levels', [])
            security_str = ', '.join([f"L{l}" for l in security_levels]) if security_levels else 'None'
            
            self.service_tree.insert('', tk.END, values=(
                service['service_id'],
                service['handler_name'],
                sessions_str,
                security_str
            ))
        
        if self.service_count_var:
            self.service_count_var.set(str(len(services)))
    
    def show_edit_form(self, config_panel_frame, index, config, 
                       on_change_callback, set_modified_callback):
        """Render edit form for service"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        # Update panel title
        service = config['dcm_services'][index]
        config_panel_frame.config(text=f"⚙️ Edit Service - {service['service_id']}")
        
        # Create form frame
        form_frame = ttk.Frame(config_panel_frame, padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Service ID
        ttk.Label(form_frame, text="Service ID (0x10-0xFF):").grid(row=0, column=0, sticky=tk.W, pady=5)
        service_id_var = tk.StringVar(value=service['service_id'])
        ttk.Entry(form_frame, textvariable=service_id_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Auto-save for service_id
        def update_service_id(*args):
            config['dcm_services'][index]['service_id'] = service_id_var.get()
            set_modified_callback()
        service_id_var.trace_add('write', update_service_id)
        
        # Handler name
        ttk.Label(form_frame, text="Handler Function:").grid(row=1, column=0, sticky=tk.W, pady=5)
        handler_var = tk.StringVar(value=service['handler_name'])
        ttk.Entry(form_frame, textvariable=handler_var, width=40).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Auto-save for handler
        def update_handler(*args):
            config['dcm_services'][index]['handler_name'] = handler_var.get()
            set_modified_callback()
        handler_var.trace_add('write', update_handler)
        
        # Sessions
        ttk.Label(form_frame, text="Supported Sessions:").grid(row=2, column=0, sticky=(tk.N, tk.W), pady=5)
        session_frame = ttk.Frame(form_frame)
        session_frame.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        session_vars = {}
        current_sessions = service.get('supported_sessions', [])
        available_sessions = [s['session_name'] for s in config.get('sessions', [])]
        
        def update_sessions(*args):
            selected = [name for name, var in session_vars.items() if var.get()]
            config['dcm_services'][index]['supported_sessions'] = selected
            set_modified_callback()
        
        for i, sess_name in enumerate(available_sessions):
            var = tk.BooleanVar(value=sess_name in current_sessions)
            session_vars[sess_name] = var
            cb = ttk.Checkbutton(session_frame, text=sess_name, variable=var)
            cb.grid(row=i, column=0, sticky=tk.W, pady=2)
            var.trace_add('write', update_sessions)
        
        # Security levels
        ttk.Label(form_frame, text="Required Security Levels:").grid(row=3, column=0, sticky=(tk.N, tk.W), pady=5)
        security_frame = ttk.Frame(form_frame)
        security_frame.grid(row=3, column=1, sticky=tk.W, padx=5)
        
        security_vars = {}
        current_security = service.get('required_security_levels', [])
        available_security = [s['security_level'] for s in config.get('security_levels', [])]
        
        def update_security(*args):
            selected = [level for level, var in security_vars.items() if var.get()]
            config['dcm_services'][index]['required_security_levels'] = selected
            set_modified_callback()
        
        if available_security:
            for i, level in enumerate(available_security):
                var = tk.BooleanVar(value=level in current_security)
                security_vars[level] = var
                cb = ttk.Checkbutton(security_frame, text=f"Level {level}", variable=var)
                cb.grid(row=i, column=0, sticky=tk.W, pady=2)
                var.trace_add('write', update_security)
        else:
            ttk.Label(security_frame, text="(No security levels configured)", 
                     foreground='gray').grid(row=0, column=0, sticky=tk.W)
        
        # Info label (no save button needed - auto-save active)
        info_label = ttk.Label(form_frame, text="ℹ️ Changes are saved automatically", 
                              foreground='green', font=('', 9, 'italic'))
        info_label.grid(row=4, column=0, columnspan=2, pady=20)
    
    def show_info_panel(self, info_text_widget, service):
        """Show service details in info panel"""
        info = f"DCM Service Details\n"
        info += f"{'='*30}\n"
        info += f"Service ID: {service['service_id']}\n"
        info += f"Handler: {service['handler_name']}\n"
        info += f"\nSupported Sessions:\n"
        for sess in service.get('supported_sessions', []):
            info += f"  • {sess}\n"
        security_levels = service.get('required_security_levels', [])
        if security_levels:
            info += f"\nRequired Security Levels:\n"
            for lvl in security_levels:
                info += f"  • Level {lvl}\n"
        else:
            info += f"\nSecurity: None required\n"
        
        info_text_widget.config(state=tk.NORMAL)
        info_text_widget.delete(1.0, tk.END)
        info_text_widget.insert(1.0, info)
        info_text_widget.config(state=tk.DISABLED)
