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
        
        # Create scrollable canvas
        canvas = tk.Canvas(self.parent_frame)
        scrollbar = ttk.Scrollbar(self.parent_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.form_frame = ttk.Frame(canvas, padding="20")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas_frame = canvas.create_window((0, 0), window=self.form_frame, anchor=tk.NW)
        
        # Bind canvas resize
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = event.width
            canvas.itemconfig(canvas_frame, width=canvas_width)
        
        self.form_frame.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_frame, width=e.width))
        
        row = 0
        
        # Title
        title_label = ttk.Label(self.form_frame, text="Memory Layout Configuration", 
                                font=('TkDefaultFont', 12, 'bold'))
        title_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 20))
        row += 1
        
        # ===== Bootloader Region =====
        ttk.Label(self.form_frame, text="🔧 Bootloader Region", 
                  font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
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
        ttk.Label(self.form_frame, text="📱 Application Region", 
                  font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
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
        ttk.Label(self.form_frame, text="📥 Download Region (UDS Service 0x34)", 
                  font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
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
        info_frame = ttk.LabelFrame(self.form_frame, text="ℹ️  Memory Map Overview", padding="10")
        info_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        info_text = tk.Text(info_frame, height=8, width=70, font=('Courier', 9), wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True)
        
        def update_info(*args):
            try:
                bl_start = int(self.bl_start_var.get(), 16)
                bl_size = int(self.bl_size_var.get(), 16)
                app_start = int(self.app_start_var.get(), 16)
                app_size = int(self.app_size_var.get(), 16)
                
                info_text.config(state=tk.NORMAL)
                info_text.delete(1.0, tk.END)
                info_text.insert(tk.END, f"Memory Map:\n")
                info_text.insert(tk.END, f"{'='*60}\n")
                info_text.insert(tk.END, f"Bootloader: 0x{bl_start:08X} - 0x{bl_start+bl_size-1:08X} ({bl_size//1024}KB)\n")
                info_text.insert(tk.END, f"Application: 0x{app_start:08X} - 0x{app_start+app_size-1:08X} ({app_size//1024}KB)\n")
                
                # Check overlap
                if app_start < bl_start + bl_size:
                    info_text.insert(tk.END, f"\n⚠️  WARNING: Regions overlap!\n", 'warning')
                else:
                    gap = app_start - (bl_start + bl_size)
                    info_text.insert(tk.END, f"\n✓ Gap between regions: {gap//1024}KB\n", 'ok')
                
                info_text.tag_config('warning', foreground='red')
                info_text.tag_config('ok', foreground='green')
                info_text.config(state=tk.DISABLED)
            except:
                pass
        
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
