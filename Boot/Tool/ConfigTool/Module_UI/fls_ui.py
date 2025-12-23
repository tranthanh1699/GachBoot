"""
Fls UI Module - Render Flash Driver configuration UI
"""

import tkinter as tk
from tkinter import ttk, messagebox


class FlsUI:
    """UI renderer for Flash Driver Configuration"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.sector_tree = None
        self.sector_count_var = None
    
    def setup_tab(self):
        """Setup Fls tab with treeview for sectors"""
        # Tree view for flash sectors
        tree_frame = ttk.Frame(self.parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("Bank", "Sector", "Start Address", "Size", "Name", "Description")
        self.sector_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        widths = {"Bank": 60, "Sector": 60, "Start Address": 120, "Size": 100, 
                  "Name": 150, "Description": 200}
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
        
        ttk.Button(toolbar, text="➕ Add Sector", command=add_cmd, style='Success.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Sector", command=edit_cmd, style='TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Sector", command=delete_cmd, style='Warning.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text="Total Sectors: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.sector_count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=self.sector_count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        return self.sector_count_var
    
    def refresh_tree(self, fls_config):
        """Refresh sector treeview with data"""
        self.sector_tree.delete(*self.sector_tree.get_children())
        
        sectors = fls_config.get('sectors', [])
        for sector in sectors:
            start_addr = sector.get('start_address', '0x00000000')
            size = sector.get('size', 0)
            
            # Format size nicely
            if isinstance(size, int):
                size_kb = size // 1024
                size_str = f"{size_kb} KB" if size_kb > 0 else f"{size} B"
            else:
                size_str = str(size)
            
            self.sector_tree.insert('', tk.END, values=(
                sector.get('bank_index', 1),
                sector.get('sector_index', 0),
                start_addr,
                size_str,
                sector.get('name', ''),
                sector.get('description', '')
            ))
        
        if self.sector_count_var:
            self.sector_count_var.set(str(len(sectors)))
    
    def show_edit_form(self, config_panel_frame, config, set_modified_callback):
        """Render edit form for Fls hardware configuration"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        fls_config = config.get('fls_config', {})
        
        # Create scrollable form
        canvas = tk.Canvas(config_panel_frame)
        scrollbar = ttk.Scrollbar(config_panel_frame, orient="vertical", command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="10")
        
        canvas.create_window((0, 0), window=form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(form_frame, text="Flash Driver Configuration", 
                 font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # MCU Name
        ttk.Label(form_frame, text="MCU Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        mcu_var = tk.StringVar(value=fls_config.get('mcu_name', 'STM32H743VIT6'))
        ttk.Entry(form_frame, textvariable=mcu_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=fls_config.get('description', 'Flash Driver Configuration'))
        ttk.Entry(form_frame, textvariable=desc_var, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(form_frame, text="Hardware Parameters", 
                 font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Base Address
        ttk.Label(form_frame, text="Base Address (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        base_var = tk.StringVar(value=fls_config.get('base_address', '0x08000000'))
        ttk.Entry(form_frame, textvariable=base_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Total Size
        ttk.Label(form_frame, text="Total Size (bytes):").grid(row=row, column=0, sticky=tk.W, pady=5)
        size_var = tk.IntVar(value=fls_config.get('total_size', 2097152))
        ttk.Entry(form_frame, textvariable=size_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(2097152 = 2MB)", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Write Alignment
        ttk.Label(form_frame, text="Write Alignment:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_align_var = tk.IntVar(value=fls_config.get('write_alignment', 32))
        ttk.Entry(form_frame, textvariable=write_align_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="bytes (32 for STM32H7)", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Read Alignment
        ttk.Label(form_frame, text="Read Alignment:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_align_var = tk.IntVar(value=fls_config.get('read_alignment', 1))
        ttk.Entry(form_frame, textvariable=read_align_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="bytes", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Erase Value
        ttk.Label(form_frame, text="Erase Value (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        erase_var = tk.StringVar(value=f"0x{fls_config.get('erase_value', 0xFF):02X}")
        ttk.Entry(form_frame, textvariable=erase_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(0xFF for NOR flash)", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(form_frame, text="Timing Parameters", 
                 font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Write Timeout
        ttk.Label(form_frame, text="Write Timeout:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_timeout_var = tk.IntVar(value=fls_config.get('write_timeout_ms', 100))
        ttk.Entry(form_frame, textvariable=write_timeout_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="ms", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Erase Timeout
        ttk.Label(form_frame, text="Erase Timeout:").grid(row=row, column=0, sticky=tk.W, pady=5)
        erase_timeout_var = tk.IntVar(value=fls_config.get('erase_timeout_ms', 2000))
        ttk.Entry(form_frame, textvariable=erase_timeout_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="ms (per sector)", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Auto-save callback
        def save_changes(*args):
            if 'fls_config' not in config:
                config['fls_config'] = {}
            
            config['fls_config']['mcu_name'] = mcu_var.get()
            config['fls_config']['description'] = desc_var.get()
            config['fls_config']['base_address'] = base_var.get()
            config['fls_config']['total_size'] = size_var.get()
            config['fls_config']['write_alignment'] = write_align_var.get()
            config['fls_config']['read_alignment'] = read_align_var.get()
            
            # Parse erase value
            erase_str = erase_var.get()
            try:
                if erase_str.startswith('0x'):
                    erase_val = int(erase_str, 16)
                else:
                    erase_val = int(erase_str)
                config['fls_config']['erase_value'] = erase_val
            except ValueError:
                pass
            
            config['fls_config']['write_timeout_ms'] = write_timeout_var.get()
            config['fls_config']['erase_timeout_ms'] = erase_timeout_var.get()
            
            set_modified_callback()
        
        # Bind auto-save to all variables
        for var in [mcu_var, desc_var, base_var, size_var, write_align_var, 
                    read_align_var, erase_var, write_timeout_var, erase_timeout_var]:
            var.trace_add('write', save_changes)
        
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
        
        # Info label
        info_label = ttk.Label(form_frame, text="ℹ️ Changes are saved automatically", 
                              foreground='green', font=('', 9, 'italic'))
        info_label.grid(row=row, column=0, columnspan=3, pady=20)
    
    def show_sector_edit_form(self, config_panel_frame, index, config, set_modified_callback):
        """Render edit form for individual sector"""
        # Clear config panel
        for widget in config_panel_frame.winfo_children():
            widget.destroy()
        
        fls_config = config.get('fls_config', {})
        sectors = fls_config.get('sectors', [])
        
        if index >= len(sectors):
            return
        
        sector = sectors[index]
        
        # Create form
        form_frame = ttk.Frame(config_panel_frame, padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text=f"Edit Flash Sector {index}", 
                 font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # Sector Name
        ttk.Label(form_frame, text="Sector Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=sector.get('name', f'Sector_{index}'))
        ttk.Entry(form_frame, textvariable=name_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=sector.get('description', ''))
        ttk.Entry(form_frame, textvariable=desc_var, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Bank Index
        ttk.Label(form_frame, text="Bank Index:").grid(row=row, column=0, sticky=tk.W, pady=5)
        bank_var = tk.IntVar(value=sector.get('bank_index', 1))
        bank_spin = ttk.Spinbox(form_frame, from_=1, to=2, textvariable=bank_var, width=10)
        bank_spin.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Sector Index
        ttk.Label(form_frame, text="Sector Index:").grid(row=row, column=0, sticky=tk.W, pady=5)
        sector_idx_var = tk.IntVar(value=sector.get('sector_index', 0))
        sector_spin = ttk.Spinbox(form_frame, from_=0, to=7, textvariable=sector_idx_var, width=10)
        sector_spin.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Start Address
        ttk.Label(form_frame, text="Start Address (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        addr_var = tk.StringVar(value=sector.get('start_address', '0x08000000'))
        ttk.Entry(form_frame, textvariable=addr_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Size
        ttk.Label(form_frame, text="Size (bytes):").grid(row=row, column=0, sticky=tk.W, pady=5)
        size_var = tk.IntVar(value=sector.get('size', 131072))
        ttk.Entry(form_frame, textvariable=size_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(131072 = 128KB)", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Auto-save callback
        def save_sector(*args):
            sectors[index]['name'] = name_var.get()
            sectors[index]['description'] = desc_var.get()
            sectors[index]['bank_index'] = bank_var.get()
            sectors[index]['sector_index'] = sector_idx_var.get()
            sectors[index]['start_address'] = addr_var.get()
            sectors[index]['size'] = size_var.get()
            set_modified_callback()
        
        for var in [name_var, desc_var, bank_var, sector_idx_var, addr_var, size_var]:
            var.trace_add('write', save_sector)
        
        # Info label
        info_label = ttk.Label(form_frame, text="ℹ️ Changes are saved automatically", 
                              foreground='green', font=('', 9, 'italic'))
        info_label.grid(row=row, column=0, columnspan=3, pady=20)
    
    def show_info_panel(self, info_text_widget, fls_config):
        """Show Fls configuration summary in info panel"""
        sectors = fls_config.get('sectors', [])
        
        info = f"Flash Driver Configuration\n"
        info += f"{'='*30}\n"
        info += f"MCU: {fls_config.get('mcu_name', 'Unknown')}\n"
        info += f"Base: {fls_config.get('base_address', '0x08000000')}\n"
        info += f"Size: {fls_config.get('total_size', 0) // 1024}KB\n"
        info += f"Write Align: {fls_config.get('write_alignment', 0)} bytes\n"
        info += f"Sectors: {len(sectors)}\n"
        
        if sectors:
            info += f"\nConfigured Sectors:\n"
            for i, sector in enumerate(sectors):
                size_kb = sector.get('size', 0) // 1024
                info += f"  • {sector.get('name', f'Sector {i}')}: {size_kb}KB\n"
        
        info_text_widget.insert(tk.END, info)
