"""
Fee UI Module - Render Flash EEPROM Emulation configuration UI
"""

import tkinter as tk
from tkinter import ttk, messagebox


class FeeUI:
    """UI renderer for Flash EEPROM Emulation Configuration"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.sector_tree = None
        self.sector_count_var = None
    
    def setup_tab(self):
        """Setup Fee tab with treeview for sector mappings"""
        # Tree view for Fee sector mappings
        tree_frame = ttk.Frame(self.parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("Fee ID", "Fls Sector", "Primary", "Name", "Description")
        self.sector_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        widths = {"Fee ID": 80, "Fls Sector": 100, "Primary": 80, 
                  "Name": 150, "Description": 250}
        for col in columns:
            self.sector_tree.heading(col, text=col)
            self.sector_tree.column(col, width=widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.sector_tree.yview)
        self.sector_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sector_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return self.sector_tree
    
    def setup_toolbar(self, add_cmd, edit_cmd, delete_cmd):
        """Setup toolbar with action buttons"""
        toolbar = ttk.Frame(self.parent_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Add Mapping", command=add_cmd, style='Success.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Mapping", command=edit_cmd, style='TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Mapping", command=delete_cmd, style='Warning.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text="Total Mappings: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.sector_count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=self.sector_count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        return self.sector_count_var
    
    def refresh_tree(self, fee_config):
        """Refresh sector mapping treeview with data"""
        self.sector_tree.delete(*self.sector_tree.get_children())
        
        mappings = fee_config.get('sector_mapping', [])
        for i, mapping in enumerate(mappings):
            self.sector_tree.insert('', tk.END, values=(
                i,
                mapping.get('fls_sector_index', 0),
                "✓ Yes" if mapping.get('is_primary', False) else "No",
                mapping.get('name', ''),
                mapping.get('description', '')
            ))
        
        if self.sector_count_var:
            self.sector_count_var.set(str(len(mappings)))
    
    def show_edit_form(self, config_panel_frame, config, set_modified_callback):
        """Render edit form for Fee virtual address space configuration"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        fee_config = config.get('fee_config', {})
        
        # Create scrollable form
        canvas = tk.Canvas(config_panel_frame)
        scrollbar = ttk.Scrollbar(config_panel_frame, orient="vertical", command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="10")
        
        canvas.create_window((0, 0), window=form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(form_frame, text="Fee Configuration (Flash EEPROM Emulation)", 
                 font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=fee_config.get('description', 'Flash EEPROM Emulation'))
        ttk.Entry(form_frame, textvariable=desc_var, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(form_frame, text="Virtual Address Space", 
                 font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Virtual Start
        ttk.Label(form_frame, text="Virtual Start (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        virt_start_var = tk.StringVar(value=fee_config.get('virtual_start', '0x00000000'))
        ttk.Entry(form_frame, textvariable=virt_start_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(typically 0x00000000)", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Virtual Size
        ttk.Label(form_frame, text="Virtual Size (bytes):").grid(row=row, column=0, sticky=tk.W, pady=5)
        virt_size_var = tk.IntVar(value=fee_config.get('virtual_size', 128 * 1024))
        ttk.Entry(form_frame, textvariable=virt_size_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text=f"(131072 = 128KB)", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(form_frame, text="Wear Leveling Parameters", 
                 font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Sector Full Threshold
        ttk.Label(form_frame, text="Sector Full Threshold:").grid(row=row, column=0, sticky=tk.W, pady=5)
        threshold_var = tk.IntVar(value=fee_config.get('sector_full_threshold', 127 * 1024))
        ttk.Entry(form_frame, textvariable=threshold_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="bytes (127KB = leave 1KB margin)", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Write Alignment
        ttk.Label(form_frame, text="Write Alignment:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_align_var = tk.IntVar(value=fee_config.get('write_alignment', 32))
        ttk.Entry(form_frame, textvariable=write_align_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="bytes (must match Fls)", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Erase Value
        ttk.Label(form_frame, text="Erase Value (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        erase_var = tk.StringVar(value=f"0x{fee_config.get('erase_value', 0xFF):02X}")
        ttk.Entry(form_frame, textvariable=erase_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(0xFF for NOR flash)", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Info panel
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        info_frame = ttk.LabelFrame(form_frame, text="ℹ️ Configuration Info", padding="10")
        info_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        virtual_size = virt_size_var.get()
        threshold = threshold_var.get()
        margin = virtual_size - threshold if virtual_size > 0 and threshold > 0 else 0
        
        info_text = f"""• Virtual address space: {hex(int(virt_start_var.get(), 16) if isinstance(virt_start_var.get(), str) else 0)} - {hex(int(virt_start_var.get(), 16) + virtual_size - 1) if virtual_size > 0 else '0x00000000'}
• Total virtual space: {virtual_size // 1024}KB
• Sector switch at: {threshold // 1024}KB
• Metadata margin: {margin // 1024}KB
• Write alignment: {write_align_var.get()} bytes

Fee provides continuous virtual address space for NvM.
Physical sectors alternate for wear leveling (ping-pong).
When active sector reaches threshold, Fee switches to standby sector."""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, foreground='blue').pack(anchor=tk.W)
        
        # Auto-save callback
        def save_changes(*args):
            if 'fee_config' not in config:
                config['fee_config'] = {}
            
            config['fee_config']['description'] = desc_var.get()
            config['fee_config']['virtual_start'] = virt_start_var.get()
            config['fee_config']['virtual_size'] = virt_size_var.get()
            config['fee_config']['sector_full_threshold'] = threshold_var.get()
            config['fee_config']['write_alignment'] = write_align_var.get()
            
            # Parse erase value
            erase_str = erase_var.get()
            try:
                if erase_str.startswith('0x'):
                    erase_val = int(erase_str, 16)
                else:
                    erase_val = int(erase_str)
                config['fee_config']['erase_value'] = erase_val
            except ValueError:
                pass
            
            set_modified_callback()
        
        # Bind all variables to auto-save
        desc_var.trace('w', save_changes)
        virt_start_var.trace('w', save_changes)
        virt_size_var.trace('w', save_changes)
        threshold_var.trace('w', save_changes)
        write_align_var.trace('w', save_changes)
        erase_var.trace('w', save_changes)
        
        # Update canvas scroll region
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
    
    def show_mapping_edit_form(self, config_panel_frame, index, config, set_modified_callback):
        """Render edit form for individual Fee sector mapping"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        fee_config = config.get('fee_config', {})
        fls_config = config.get('fls_config', {})
        mappings = fee_config.get('sector_mapping', [])
        
        if index >= len(mappings):
            messagebox.showerror("Error", "Invalid mapping index")
            return
        
        mapping = mappings[index]
        
        # Create scrollable form
        canvas = tk.Canvas(config_panel_frame)
        scrollbar = ttk.Scrollbar(config_panel_frame, orient="vertical", command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="10")
        
        canvas.create_window((0, 0), window=form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(form_frame, text=f"Edit Fee Sector Mapping #{index}", 
                 font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # Name
        ttk.Label(form_frame, text="Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=mapping.get('name', f'Fee_Sector_{index}'))
        ttk.Entry(form_frame, textvariable=name_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=mapping.get('description', ''))
        ttk.Entry(form_frame, textvariable=desc_var, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Fls Sector Index
        ttk.Label(form_frame, text="Fls Sector Index:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        # Get available Fls sectors
        fls_sectors = fls_config.get('sectors', [])
        fls_options = [f"{i}: {s.get('name', 'Sector')} ({s.get('start_address', '0x00000000')})" 
                       for i, s in enumerate(fls_sectors)]
        
        if not fls_options:
            fls_options = ["No Fls sectors available"]
        
        fls_idx_var = tk.IntVar(value=mapping.get('fls_sector_index', 0))
        fls_combo = ttk.Combobox(form_frame, values=fls_options, state="readonly", width=50)
        if fls_idx_var.get() < len(fls_options):
            fls_combo.current(fls_idx_var.get())
        fls_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Primary Flag
        ttk.Label(form_frame, text="Primary Sector:").grid(row=row, column=0, sticky=tk.W, pady=5)
        primary_var = tk.BooleanVar(value=mapping.get('is_primary', False))
        ttk.Checkbutton(form_frame, text="Use as primary sector (active at startup)", 
                       variable=primary_var).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Info
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        info_frame = ttk.LabelFrame(form_frame, text="ℹ️ Sector Mapping Info", padding="10")
        info_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        info_text = """Fee logical sectors map to physical Fls sectors.
• Fee ping-pongs between mapped sectors for wear leveling
• Primary sector is used first at initialization
• Each Fls sector should only be mapped once
• Need at least 2 sectors for wear leveling to work"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, foreground='blue').pack(anchor=tk.W)
        
        # Auto-save callback
        def save_changes(*args):
            mapping['name'] = name_var.get()
            mapping['description'] = desc_var.get()
            mapping['is_primary'] = primary_var.get()
            
            # Get selected Fls sector index
            combo_idx = fls_combo.current()
            if combo_idx >= 0 and combo_idx < len(fls_sectors):
                mapping['fls_sector_index'] = combo_idx
            
            set_modified_callback()
        
        # Bind variables
        name_var.trace('w', save_changes)
        desc_var.trace('w', save_changes)
        primary_var.trace('w', save_changes)
        fls_combo.bind('<<ComboboxSelected>>', save_changes)
        
        # Update canvas scroll region
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
