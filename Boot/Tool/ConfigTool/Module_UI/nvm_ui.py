"""
NVM Block UI Module
Handles UI rendering for NVM Block configuration
"""

import tkinter as tk
from tkinter import ttk


class NvmUI:
    """UI module for NVM Block configuration"""
    
    def __init__(self, parent_frame):
        """Initialize NVM UI module"""
        self.parent = parent_frame
        self.tree = None
    
    def setup_tab(self):
        """Setup NVM Blocks tab and return treeview"""
        # Toolbar
        toolbar = ttk.Frame(self.parent)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Treeview
        tree_frame = ttk.Frame(self.parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("Block ID", "Block Name", "Size", "ROM Data", "RAM Data")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        widths = {"Block ID": 80, "Block Name": 150, "Size": 80, "ROM Data": 200, "RAM Data": 200}
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
        
        ttk.Button(toolbar, text="➕ Add NVM Block", command=add_cmd).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Block", command=edit_cmd).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Block", command=delete_cmd).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text=f"Total Blocks: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        return count_var
    
    def refresh_tree(self, nvm_blocks):
        """Refresh treeview with NVM blocks data"""
        self.tree.delete(*self.tree.get_children())
        
        for block in nvm_blocks:
            rom_data = block.get('rom_data', block.get('default_value', ''))
            if isinstance(rom_data, list):
                rom_display = ' '.join([f'{v:02X}' for v in rom_data[:8]])
                if len(rom_data) > 8:
                    rom_display += '...'
            else:
                rom_display = str(rom_data)
            
            ram_data = block.get('ram_data', '')
            
            self.tree.insert('', tk.END, values=(
                block['block_id'],
                block['block_name'],
                f"{block.get('block_size', block.get('data_length', 0))} bytes",
                rom_display,
                ram_data
            ))
    
    def show_edit_form(self, config_panel_frame, index, config, callbacks):
        """Show NVM block edit form with auto-save"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        block = config['nvm_blocks'][index]
        
        # Create scrollable form
        canvas = tk.Canvas(config_panel_frame)
        scrollbar = ttk.Scrollbar(config_panel_frame, orient="vertical", command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="10")
        
        canvas.create_window((0, 0), window=form_frame, anchor="nw", tags="canvas_frame")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(form_frame, text=f"Edit NVM Block", font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # Block ID
        ttk.Label(form_frame, text="Block ID:").grid(row=row, column=0, sticky=tk.W, pady=5)
        block_id_var = tk.IntVar(value=block['block_id'])
        ttk.Entry(form_frame, textvariable=block_id_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Block Name
        ttk.Label(form_frame, text="Block Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        block_name_var = tk.StringVar(value=block['block_name'])
        ttk.Entry(form_frame, textvariable=block_name_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Block Size
        ttk.Label(form_frame, text="Block Size:").grid(row=row, column=0, sticky=tk.W, pady=5)
        block_size_var = tk.IntVar(value=block.get('block_size', block.get('data_length', 0)))
        ttk.Entry(form_frame, textvariable=block_size_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # ROM Data Array Name
        ttk.Label(form_frame, text="ROM Array Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        rom_var = tk.StringVar(value=block.get('rom_data', ''))
        ttk.Entry(form_frame, textvariable=rom_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # RAM Data Array Name
        ttk.Label(form_frame, text="RAM Array Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ram_var = tk.StringVar(value=block.get('ram_data', ''))
        ttk.Entry(form_frame, textvariable=ram_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=block['description'])
        ttk.Entry(form_frame, textvariable=desc_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Info label
        ttk.Label(form_frame, text="ℹ️ Changes are saved automatically", 
                 foreground='green', font=('', 9)).grid(row=row, column=0, columnspan=2, pady=10)
        
        # Auto-save function
        def save_changes(*args):
            try:
                config['nvm_blocks'][index]['block_id'] = block_id_var.get()
                config['nvm_blocks'][index]['block_name'] = block_name_var.get()
                config['nvm_blocks'][index]['block_size'] = block_size_var.get()
                config['nvm_blocks'][index]['rom_data'] = rom_var.get().strip()
                config['nvm_blocks'][index]['ram_data'] = ram_var.get().strip()
                config['nvm_blocks'][index]['description'] = desc_var.get()
                callbacks['set_modified']()
                callbacks['refresh_ui']()
            except Exception:
                pass
        
        # Bind all variables to auto-save
        for var in [block_id_var, block_name_var, block_size_var, rom_var, ram_var, desc_var]:
            var.trace_add('write', save_changes)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Configure canvas scrolling
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas.itemconfig("canvas_frame", width=event.width)
        
        form_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        on_frame_configure()
    
    def show_info_panel(self, info_widget, block):
        """Display NVM block details in info panel"""
        info = f"NVM Block Details\n"
        info += f"{'='*30}\n"
        info += f"Block ID: {block['block_id']}\n"
        info += f"Name: {block['block_name']}\n"
        info += f"Length: {block.get('block_size', block.get('data_length', 0))} bytes\n"
        
        rom_data = block.get('rom_data', block.get('default_value', ''))
        if isinstance(rom_data, str):
            info += f"ROM Data: {rom_data}\n"
        else:
            info += f"ROM Data: {' '.join([f'{v:02X}' for v in rom_data])}\n"
        
        ram_data = block.get('ram_data', '')
        if ram_data:
            info += f"RAM Data: {ram_data}\n"
        
        info += f"\nDescription:\n{block['description']}\n"
        info_widget.insert(1.0, info)
