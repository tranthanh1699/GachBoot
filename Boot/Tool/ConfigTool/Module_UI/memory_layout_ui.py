"""
Memory Layout UI Module
Provides UI components for memory layout configuration
"""

import tkinter as tk
from tkinter import ttk, messagebox


class MemoryLayoutUI:
    """UI components for Memory Layout configuration"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.form_frame = None
        
        # Variables for form fields
        self.bl_start_var = None
        self.bl_size_var = None
        self.bl_name_var = None
        self.bl_desc_var = None
        
        self.app_start_var = None
        self.app_size_var = None
        self.app_name_var = None
        self.app_desc_var = None
        
        self.dl_start_var = None
        self.dl_size_var = None
        self.dl_align_var = None
        self.dl_max_block_var = None
        self.dl_enabled_var = None
        self.on_change_callback = None
        self.on_save_callback = None
    
    def show_edit_form(self, memory_layout, on_save_callback, on_change_callback=None):
        """Show memory layout edit form"""
        self.on_change_callback = on_change_callback
        self.on_save_callback = on_save_callback
        
        # Clear parent frame
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Create scrollable canvas with modern look
        canvas = tk.Canvas(self.parent_frame, bg='#ffffff', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.form_frame = ttk.Frame(canvas, padding="20")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas_frame = canvas.create_window((0, 0), window=self.form_frame, anchor=tk.NW)
        
        # Bind canvas resize for full width
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        
        self.form_frame.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)
        
        # Mousewheel scrolling
        def on_mousewheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Unbind mousewheel when canvas is destroyed
        def cleanup():
            canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Destroy>", lambda e: cleanup())
        
        # Configure column weights for responsive layout
        self.form_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Title with modern style
        title_label = ttk.Label(self.form_frame, text="🔧 Memory Layout Configuration", 
                                style='Title.TLabel')
        title_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 20))
        row += 1
        
        # ===== Bootloader Region =====
        ttk.Separator(self.form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        ttk.Label(self.form_frame, text="🔷 Bootloader Region", 
                  style='Section.TLabel').grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(5, 10))
        row += 1
        
        bootloader = memory_layout.get('bootloader_region', {})
        
        ttk.Label(self.form_frame, text="Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.bl_name_var = tk.StringVar(value=bootloader.get('name', 'Bootloader'))
        if self.on_change_callback:
            self.bl_name_var.trace_add('write', lambda *args: self.on_change_callback())
        ttk.Entry(self.form_frame, textvariable=self.bl_name_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        row += 1
        
        ttk.Label(self.form_frame, text="Start Address:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.bl_start_var = tk.StringVar(value=bootloader.get('start_address', '0x08000000'))
        if self.on_change_callback:
            self.bl_start_var.trace_add('write', lambda *args: self.on_change_callback())
        ttk.Entry(self.form_frame, textvariable=self.bl_start_var, width=20).grid(row=row, column=1, sticky=tk.W, padx=5)
        ttk.Label(self.form_frame, text="(Bank 1 start)", foreground='gray').grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        ttk.Label(self.form_frame, text="Size:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.bl_size_var = tk.StringVar(value=bootloader.get('size', '0x00040000'))
        if self.on_change_callback:
            self.bl_size_var.trace_add('write', lambda *args: self.on_change_callback())
        ttk.Entry(self.form_frame, textvariable=self.bl_size_var, width=20).grid(row=row, column=1, sticky=tk.W, padx=5)
        ttk.Label(self.form_frame, text="(256KB = 0x40000)", foreground='gray').grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        ttk.Label(self.form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.bl_desc_var = tk.StringVar(value=bootloader.get('description', 'Bootloader firmware region'))
        if self.on_change_callback:
            self.bl_desc_var.trace_add('write', lambda *args: self.on_change_callback())
        ttk.Entry(self.form_frame, textvariable=self.bl_desc_var, width=50).grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        row += 1
        
        # Show calculated end address
        def update_bl_end(*args):
            try:
                start = int(self.bl_start_var.get(), 16)
                size = int(self.bl_size_var.get(), 16)
                end = start + size - 1
                bl_end_label.config(text=f"End: 0x{end:08X} (Size: {size//1024}KB)")
            except:
                bl_end_label.config(text="End: Invalid")
        
        self.bl_start_var.trace_add('write', update_bl_end)
        self.bl_size_var.trace_add('write', update_bl_end)
        
        bl_end_label = ttk.Label(self.form_frame, text="", foreground='blue')
        bl_end_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        ttk.Separator(self.form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # ===== Application Region =====
        ttk.Separator(self.form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 10))
        row += 1
        ttk.Label(self.form_frame, text="📱 Application Region", 
                  style='Section.TLabel').grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(5, 10))
        row += 1
        
        application = memory_layout.get('application_region', {})
        
        ttk.Label(self.form_frame, text="Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.app_name_var = tk.StringVar(value=application.get('name', 'Application'))
        if self.on_change_callback:
            self.app_name_var.trace_add('write', lambda *args: self.on_change_callback())
        ttk.Entry(self.form_frame, textvariable=self.app_name_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        row += 1
        
        ttk.Label(self.form_frame, text="Start Address:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.app_start_var = tk.StringVar(value=application.get('start_address', '0x08100000'))
        if self.on_change_callback:
            self.app_start_var.trace_add('write', lambda *args: self.on_change_callback())
        ttk.Entry(self.form_frame, textvariable=self.app_start_var, width=20).grid(row=row, column=1, sticky=tk.W, padx=5)
        ttk.Label(self.form_frame, text="(Bank 2 start)", foreground='gray').grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        ttk.Label(self.form_frame, text="Size:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.app_size_var = tk.StringVar(value=application.get('size', '0x00100000'))
        if self.on_change_callback:
            self.app_size_var.trace_add('write', lambda *args: self.on_change_callback())
        ttk.Entry(self.form_frame, textvariable=self.app_size_var, width=20).grid(row=row, column=1, sticky=tk.W, padx=5)
        ttk.Label(self.form_frame, text="(1MB = 0x100000)", foreground='gray').grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        ttk.Label(self.form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.app_desc_var = tk.StringVar(value=application.get('description', 'Application firmware region'))
        if self.on_change_callback:
            self.app_desc_var.trace_add('write', lambda *args: self.on_change_callback())
        ttk.Entry(self.form_frame, textvariable=self.app_desc_var, width=50).grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        row += 1
        
        # Show calculated end address
        def update_app_end(*args):
            try:
                start = int(self.app_start_var.get(), 16)
                size = int(self.app_size_var.get(), 16)
                end = start + size - 1
                app_end_label.config(text=f"End: 0x{end:08X} (Size: {size//1024}KB)")
            except:
                app_end_label.config(text="End: Invalid")
        
        self.app_start_var.trace_add('write', update_app_end)
        self.app_size_var.trace_add('write', update_app_end)
        
        app_end_label = ttk.Label(self.form_frame, text="", foreground='blue')
        app_end_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        ttk.Separator(self.form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # ===== Download Region (UDS 0x34) =====
        ttk.Separator(self.form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 10))
        row += 1
        ttk.Label(self.form_frame, text="📥 Download Region (UDS Service 0x34)", 
                  style='Section.TLabel').grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(5, 10))
        row += 1
        
        download = memory_layout.get('download_region', {})
        
        self.dl_enabled_var = tk.BooleanVar(value=bool(download))
        if self.on_change_callback:
            self.dl_enabled_var.trace_add('write', lambda *args: self.on_change_callback())
        dl_check = ttk.Checkbutton(self.form_frame, text="Enable separate download region (otherwise uses Application region)", 
                                   variable=self.dl_enabled_var, command=lambda: update_dl_state())
        dl_check.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(self.form_frame, text="Start Address:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.dl_start_var = tk.StringVar(value=download.get('start_address', application.get('start_address', '0x08100000')))
        if self.on_change_callback:
            self.dl_start_var.trace_add('write', lambda *args: self.on_change_callback())
        dl_start_entry = ttk.Entry(self.form_frame, textvariable=self.dl_start_var, width=20)
        dl_start_entry.grid(row=row, column=1, sticky=tk.W, padx=5)
        ttk.Label(self.form_frame, text="(must be aligned)", foreground='gray').grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        ttk.Label(self.form_frame, text="Size:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.dl_size_var = tk.StringVar(value=download.get('size', application.get('size', '0x00100000')))
        if self.on_change_callback:
            self.dl_size_var.trace_add('write', lambda *args: self.on_change_callback())
        dl_size_entry = ttk.Entry(self.form_frame, textvariable=self.dl_size_var, width=20)
        dl_size_entry.grid(row=row, column=1, sticky=tk.W, padx=5)
        ttk.Label(self.form_frame, text="(max download size)", foreground='gray').grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        ttk.Label(self.form_frame, text="Alignment:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.dl_align_var = tk.StringVar(value=str(download.get('alignment', '32')))
        if self.on_change_callback:
            self.dl_align_var.trace_add('write', lambda *args: self.on_change_callback())
        dl_align_combo = ttk.Combobox(self.form_frame, textvariable=self.dl_align_var, width=18, 
                                      values=['1', '2', '4', '8', '16', '32'], state='readonly')
        dl_align_combo.grid(row=row, column=1, sticky=tk.W, padx=5)
        ttk.Label(self.form_frame, text="(STM32H7 requires 32)", foreground='gray').grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        ttk.Label(self.form_frame, text="Max Block Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.dl_max_block_var = tk.StringVar(value=str(download.get('max_block_length', '256')))
        if self.on_change_callback:
            self.dl_max_block_var.trace_add('write', lambda *args: self.on_change_callback())
        dl_block_entry = ttk.Entry(self.form_frame, textvariable=self.dl_max_block_var, width=20)
        dl_block_entry.grid(row=row, column=1, sticky=tk.W, padx=5)
        ttk.Label(self.form_frame, text="(bytes per 0x36 transfer)", foreground='gray').grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        # Store widgets for enable/disable
        dl_widgets = [dl_start_entry, dl_size_entry, dl_align_combo, dl_block_entry]
        
        def update_dl_state():
            state = 'normal' if self.dl_enabled_var.get() else 'disabled'
            for widget in dl_widgets:
                widget.config(state=state if isinstance(widget, ttk.Entry) else 'readonly' if self.dl_enabled_var.get() else 'disabled')
        
        update_dl_state()
        
        ttk.Separator(self.form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # ===== Info Panel =====
        info_frame = ttk.LabelFrame(self.form_frame, text="ℹ️  Memory Map Overview", padding="15")
        info_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        info_text = tk.Text(info_frame, height=10, wrap=tk.WORD, font=('Consolas', 9), 
                           bg='#f8f9fa', fg='#2d3436', relief=tk.FLAT, padx=10, pady=10)
        info_text.pack(fill=tk.BOTH, expand=True)
        
        def update_info(*args):
            """Update memory map overview with color-coded info"""
            info_text.config(state=tk.NORMAL)
            info_text.delete(1.0, tk.END)
            
            try:
                bl_start = int(self.bl_start_var.get(), 16)
                bl_size = int(self.bl_size_var.get(), 16)
                bl_end = bl_start + bl_size - 1
                
                app_start = int(self.app_start_var.get(), 16)
                app_size = int(self.app_size_var.get(), 16)
                app_end = app_start + app_size - 1
                
                # Header
                info_text.insert(tk.END, "=" * 60 + "\n", 'header')
                info_text.insert(tk.END, "         STM32H743 Flash Memory Layout\n", 'header')
                info_text.insert(tk.END, "=" * 60 + "\n\n", 'header')
                
                # Bootloader
                info_text.insert(tk.END, "🔷 BOOTLOADER REGION\n", 'section')
                info_text.insert(tk.END, f"   Start:  0x{bl_start:08X}\n", 'normal')
                info_text.insert(tk.END, f"   End:    0x{bl_end:08X}\n", 'normal')
                info_text.insert(tk.END, f"   Size:   {bl_size//1024}KB (0x{bl_size:X})\n\n", 'size')
                
                # Application
                info_text.insert(tk.END, "📱 APPLICATION REGION\n", 'section')
                info_text.insert(tk.END, f"   Start:  0x{app_start:08X}\n", 'normal')
                info_text.insert(tk.END, f"   End:    0x{app_end:08X}\n", 'normal')
                info_text.insert(tk.END, f"   Size:   {app_size//1024}KB (0x{app_size:X})\n\n", 'size')
                
                # Download region if enabled
                if self.dl_enabled_var and self.dl_enabled_var.get():
                    try:
                        dl_start = int(self.dl_start_var.get(), 16)
                        dl_size = int(self.dl_size_var.get(), 16)
                        dl_end = dl_start + dl_size - 1
                        
                        info_text.insert(tk.END, "📥 DOWNLOAD REGION (UDS 0x34)\n", 'section')
                        info_text.insert(tk.END, f"   Start:  0x{dl_start:08X}\n", 'normal')
                        info_text.insert(tk.END, f"   End:    0x{dl_end:08X}\n", 'normal')
                        info_text.insert(tk.END, f"   Size:   {dl_size//1024}KB (0x{dl_size:X})\n", 'size')
                        info_text.insert(tk.END, f"   Align:  {self.dl_align_var.get()} bytes\n", 'normal')
                        info_text.insert(tk.END, f"   Block:  {self.dl_max_block_var.get()} bytes\n\n", 'normal')
                    except:
                        pass
                
                # Validation
                info_text.insert(tk.END, "-" * 60 + "\n", 'separator')
                overlap = False
                
                # Check for overlaps
                if bl_end >= app_start:
                    info_text.insert(tk.END, "⚠️  WARNING: Bootloader overlaps with Application!\n", 'error')
                    overlap = True
                
                if self.dl_enabled_var and self.dl_enabled_var.get():
                    try:
                        dl_start = int(self.dl_start_var.get(), 16)
                        dl_end = dl_start + int(self.dl_size_var.get(), 16) - 1
                        
                        if (dl_start <= app_end and dl_end >= app_start):
                            info_text.insert(tk.END, "⚠️  WARNING: Download region overlaps with Application!\n", 'error')
                            overlap = True
                        if (dl_start <= bl_end and dl_end >= bl_start):
                            info_text.insert(tk.END, "⚠️  WARNING: Download region overlaps with Bootloader!\n", 'error')
                            overlap = True
                    except:
                        pass
                
                if not overlap:
                    info_text.insert(tk.END, "✅ Memory layout is valid - No overlaps detected\n", 'success')
                    
            except ValueError:
                info_text.insert(tk.END, "⚠️  Invalid hex values - Cannot compute memory map\n", 'error')
            
            # Configure text tags for colors
            info_text.tag_config('header', foreground='#0066cc', font=('Consolas', 9, 'bold'))
            info_text.tag_config('section', foreground='#0066cc', font=('Consolas', 9, 'bold'))
            info_text.tag_config('normal', foreground='#2d3436')
            info_text.tag_config('size', foreground='#00b894', font=('Consolas', 9, 'bold'))
            info_text.tag_config('error', foreground='#d63031', font=('Consolas', 9, 'bold'))
            info_text.tag_config('success', foreground='#00b894', font=('Consolas', 9, 'bold'))
            info_text.tag_config('separator', foreground='#b2bec3')
            
            info_text.config(state=tk.DISABLED)
        
        self.bl_start_var.trace_add('write', update_info)
        self.bl_size_var.trace_add('write', update_info)
        self.app_start_var.trace_add('write', update_info)
        self.app_size_var.trace_add('write', update_info)
        
        update_info()
        
        # Configure grid weights
        self.form_frame.columnconfigure(1, weight=1)
        
        # Update canvas scroll region
        self.form_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Make form accessible for saving
        return self.form_frame
    
    def save_changes(self):
        """Save method called by parent - returns updated dict and calls callback"""
        if not self.form_frame:
            return None
        
        layout = {
            'bootloader_region': {
                'name': self.bl_name_var.get(),
                'start_address': self.bl_start_var.get(),
                'size': self.bl_size_var.get(),
                'description': self.bl_desc_var.get()
            },
            'application_region': {
                'name': self.app_name_var.get(),
                'start_address': self.app_start_var.get(),
                'size': self.app_size_var.get(),
                'description': self.app_desc_var.get()
            }
        }
        
        if self.dl_enabled_var and self.dl_enabled_var.get():
            layout['download_region'] = {
                'start_address': self.dl_start_var.get(),
                'size': self.dl_size_var.get(),
                'alignment': self.dl_align_var.get(),
                'max_block_length': self.dl_max_block_var.get()
            }
        
        # Call the save callback to actually save to config (silently, without messagebox)
        if self.on_save_callback:
            try:
                # Call callback with show_message=False to suppress messagebox
                self.on_save_callback(layout, show_message=False)
            except TypeError:
                # Fallback if callback doesn't accept show_message parameter
                self.on_save_callback(layout)
        
        return layout
