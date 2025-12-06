#!/usr/bin/env python3
"""
GachBoot Configuration Editor (Tkinter GUI)
AUTOSAR-style configuration tool with graphical interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from nvm_module import validate_nvm_blocks, generate_nvm_code
from did_module import validate_dids, generate_did_code

class ConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("GachBoot ConfigTool - AUTOSAR Style Editor")
        self.root.geometry("1400x900")
        
        self.config_file = "gachboot_config.json"
        self.config = None
        self.set_modified(False)
        
        # Apply theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Bind Ctrl+S for save
        self.root.bind('<Control-s>', lambda e: self.save_config())
        
        self.setup_ui()
        self.load_config()
    
    def setup_ui(self):
        """Setup main UI layout"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Config", command=self.new_config)
        file_menu.add_command(label="Open...", command=self.open_config)
        file_menu.add_command(label="Save", command=self.save_config)
        file_menu.add_command(label="Save As...", command=self.save_as_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        generate_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Generate", menu=generate_menu)
        generate_menu.add_command(label="🔍 Validate Config", command=self.validate_config)
        generate_menu.add_command(label="⚙️ Generate Code", command=self.generate_code)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Main container with PanedWindow for resizable layout
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel: Tree view navigation
        left_frame = ttk.Frame(main_paned, width=300)
        main_paned.add(left_frame, weight=1)
        self.setup_tree_navigation(left_frame)
        
        # Right panel: Dynamic config editor
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        # Configure grid weights for right panel
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Project info frame
        self.setup_project_frame(right_frame)
        
        # Dynamic config panel (replaces tabs)
        self.config_panel_frame = ttk.LabelFrame(right_frame, text="Configuration Editor", padding="10")
        self.config_panel_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        self.config_panel_frame.columnconfigure(0, weight=1)
        self.config_panel_frame.rowconfigure(0, weight=1)
        
        # Welcome message (default view)
        welcome_label = ttk.Label(self.config_panel_frame, text="Select an item from the navigation tree", 
                                   font=('', 11), foreground='gray')
        welcome_label.pack(expand=True)
        
        # Initialize tree widgets (hidden)
        self.setup_nvm_tab()
        self.setup_did_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(right_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def setup_tree_navigation(self, parent):
        """Setup tree view navigation panel"""
        nav_label = ttk.Label(parent, text="Configuration Explorer", font=('', 10, 'bold'))
        nav_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Tree view
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.nav_tree = ttk.Treeview(tree_frame, show="tree")
        nav_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.nav_tree.yview)
        self.nav_tree.configure(yscrollcommand=nav_scrollbar.set)
        
        self.nav_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        nav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.nav_tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        # Bind right-click menu
        self.nav_tree.bind('<Button-3>', self.show_context_menu)
        
        # Info panel at bottom
        info_frame = ttk.LabelFrame(parent, text="Item Details", padding="10")
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        self.info_text = tk.Text(info_frame, height=8, width=35, wrap=tk.WORD, font=('Courier', 9))
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.config(state=tk.DISABLED)
    
    def setup_project_frame(self, parent):
        """Setup project info frame"""
        project_frame = ttk.LabelFrame(parent, text="📁 Project Configuration", padding="10")
        project_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Config file row
        ttk.Label(project_frame, text="Config File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.config_file_var = tk.StringVar(value=self.config_file)
        config_entry = ttk.Entry(project_frame, textvariable=self.config_file_var, width=50, state='readonly')
        config_entry.grid(row=0, column=1, columnspan=2, padx=5, sticky=(tk.W, tk.E))
        ttk.Button(project_frame, text="Browse...", command=self.browse_config_file, width=10).grid(row=0, column=3, padx=5)
        
        # Project name and version row
        ttk.Label(project_frame, text="Project Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.project_name_var = tk.StringVar()
        ttk.Entry(project_frame, textvariable=self.project_name_var, width=30).grid(row=1, column=1, padx=5, sticky=tk.W)
        
        ttk.Label(project_frame, text="Version:").grid(row=1, column=2, sticky=tk.W, padx=(10, 0))
        self.version_var = tk.StringVar()
        ttk.Entry(project_frame, textvariable=self.version_var, width=15).grid(row=1, column=3, padx=5, sticky=tk.W)
        
        # Output path row
        ttk.Label(project_frame, text="Output Path:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_path_var = tk.StringVar()
        output_entry = ttk.Entry(project_frame, textvariable=self.output_path_var, width=50)
        output_entry.grid(row=2, column=1, columnspan=2, padx=5, sticky=(tk.W, tk.E))
        ttk.Button(project_frame, text="Browse...", command=self.browse_output_path, width=10).grid(row=2, column=3, padx=5)
        
        # Configure column weights
        project_frame.columnconfigure(1, weight=1)
    
    def setup_nvm_tab(self):
        """Setup NVM Blocks tab"""
        nvm_frame = ttk.Frame(self.config_panel_frame)
        
        # Toolbar
        toolbar = ttk.Frame(nvm_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Add Block", command=self.add_nvm_block).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Block", command=self.edit_nvm_block).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Block", command=self.delete_nvm_block).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text=f"Total Blocks: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.nvm_count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=self.nvm_count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        # Treeview
        tree_frame = ttk.Frame(nvm_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("ID", "Name", "Length", "Default", "Description")
        self.nvm_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.nvm_tree.heading(col, text=col)
            self.nvm_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.nvm_tree.yview)
        self.nvm_tree.configure(yscrollcommand=scrollbar.set)
        
        self.nvm_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_did_tab(self):
        """Setup DIDs tab"""
        did_frame = ttk.Frame(self.config_panel_frame)
        
        # Toolbar
        toolbar = ttk.Frame(did_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Add DID", command=self.add_did).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit DID", command=self.edit_did).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete DID", command=self.delete_did).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text=f"Total DIDs: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.did_count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=self.did_count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="Add DID", command=self.add_did).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit DID", command=self.edit_did).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete DID", command=self.delete_did).pack(side=tk.LEFT, padx=2)
        
        # Treeview
        tree_frame = ttk.Frame(did_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("DID", "Name", "Type", "Length", "Read", "Write", "Description")
        self.did_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        widths = {"DID": 80, "Name": 200, "Type": 80, "Length": 70, "Read": 60, "Write": 60, "Description": 300}
        for col in columns:
            self.did_tree.heading(col, text=col)
            self.did_tree.column(col, width=widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.did_tree.yview)
        self.did_tree.configure(yscrollcommand=scrollbar.set)
        
        self.did_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.refresh_ui()
                self.set_modified(False)
                self.update_title()
                self.status_var.set(f"Loaded: {self.config_file}")
            else:
                self.new_config()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
    
    def update_title(self):
        """Update window title with file name and modified status"""
        filename = os.path.basename(self.config_file) if self.config_file else "Untitled"
        modified_mark = " *" if self.modified else ""
        self.root.title(f"GachBoot ConfigTool - {filename}{modified_mark}")
    
    def set_modified(self, modified=True):
        """Set modified flag and update title"""
        self.modified = modified
        self.update_title()
    
    def refresh_ui(self):
        """Refresh UI with current config"""
        if not self.config:
            return
        
        # Project info
        self.project_name_var.set(self.config['project']['name'])
        self.version_var.set(self.config['project']['version'])
        self.output_path_var.set(self.config['project']['generated_path'])
        self.config_file_var.set(self.config_file)
        
        # Navigation tree
        self.refresh_nav_tree()
        
        # NVM Blocks
        self.nvm_tree.delete(*self.nvm_tree.get_children())
        for block in self.config['nvm_blocks']:
            rom_data = block.get('rom_data', block.get('default_value', ''))
            # Check if rom_data is string (array name) or list (old format)
            if isinstance(rom_data, str):
                default_str = rom_data  # Display array name
            else:
                default_str = ' '.join([f"{v:02X}" for v in rom_data])  # Display hex values
            
            self.nvm_tree.insert('', tk.END, values=(
                block['block_id'],
                block['block_name'],
                block.get('block_size', block.get('data_length', 0)),
                default_str,
                block['description']
            ))
        self.nvm_count_var.set(str(len(self.config['nvm_blocks'])))
        
        # DIDs
        self.did_tree.delete(*self.did_tree.get_children())
        for did in self.config['dids']:
            has_read = 'read_config' in did and did['read_config'].get('callback')
            has_write = 'write_config' in did and did['write_config'].get('callback')
            self.did_tree.insert('', tk.END, values=(
                did['did'],
                did['did_name'],
                'Fixed' if did.get('fixed_length', True) else 'Variable',
                did.get('expected_length', 0),
                '✓' if has_read else '✗',
                '✓' if has_write else '✗',
                did.get('description', '')
            ))
        self.did_count_var.set(str(len(self.config['dids'])))
    
    def refresh_nav_tree(self):
        """Refresh navigation tree"""
        self.nav_tree.delete(*self.nav_tree.get_children())
        
        if not self.config:
            return
        
        # Root node
        root = self.nav_tree.insert('', tk.END, text=f"📦 {self.config['project']['name']}", open=True)
        
        # NVM Blocks branch with count
        nvm_count = len(self.config['nvm_blocks'])
        nvm_root = self.nav_tree.insert(root, tk.END, text=f"💾 NVM Blocks ({nvm_count})", open=True, tags=('nvm_root',))
        for i, block in enumerate(self.config['nvm_blocks']):
            block_node = self.nav_tree.insert(nvm_root, tk.END, 
                text=f"  [{block['block_id']}] {block['block_name']}", 
                tags=('nvm', str(i)))
        
        # DIDs branch with count
        did_count = len(self.config['dids'])
        did_root = self.nav_tree.insert(root, tk.END, text=f"🔧 DIDs ({did_count})", open=True, tags=('did_root',))
        
        # List all DIDs directly (no grouping)
        for i, did in enumerate(self.config['dids']):
            self.nav_tree.insert(did_root, tk.END, 
                text=f"  {did['did']} - {did['did_name']}", 
                tags=('did', str(i)))
    
    def browse_config_file(self):
        """Browse for config file"""
        filename = filedialog.askopenfilename(
            title="Select Configuration File",
            initialdir=os.path.dirname(self.config_file),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.config_file = filename
            self.load_config()
    
    def browse_output_path(self):
        """Browse for output directory"""
        try:
            # Get initial directory
            initial_dir = "."
            if self.output_path_var.get():
                # Try to use current output path
                if os.path.isabs(self.output_path_var.get()):
                    initial_dir = self.output_path_var.get()
                else:
                    # Relative path - resolve it
                    if self.config_file and os.path.exists(self.config_file):
                        base_dir = os.path.dirname(os.path.abspath(self.config_file))
                        initial_dir = os.path.join(base_dir, self.output_path_var.get())
                    else:
                        initial_dir = os.path.abspath(self.output_path_var.get())
            
            directory = filedialog.askdirectory(
                title="Select Output Directory",
                initialdir=initial_dir if os.path.exists(initial_dir) else "."
            )
            
            if directory:
                # Convert to relative path if possible
                if self.config_file and os.path.exists(self.config_file):
                    try:
                        base_dir = os.path.dirname(os.path.abspath(self.config_file))
                        rel_path = os.path.relpath(directory, base_dir)
                        self.output_path_var.set(rel_path)
                        print(f"[DEBUG] Set output path (relative): {rel_path}")
                    except (ValueError, TypeError) as e:
                        self.output_path_var.set(directory)
                        print(f"[DEBUG] Set output path (absolute): {directory}")
                else:
                    # No config file yet - use relative to current directory
                    try:
                        rel_path = os.path.relpath(directory)
                        self.output_path_var.set(rel_path)
                        print(f"[DEBUG] Set output path (relative to cwd): {rel_path}")
                    except (ValueError, TypeError) as e:
                        self.output_path_var.set(directory)
                        print(f"[DEBUG] Set output path (absolute): {directory}")
                
                # Update config immediately
                if self.config:
                    self.config['project']['generated_path'] = self.output_path_var.get()
                    print(f"[DEBUG] Updated config['project']['generated_path'] = {self.output_path_var.get()}")
                
                self.set_modified()
                self.status_var.set(f"Output path set to: {self.output_path_var.get()}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to browse directory: {e}")
    
    def open_config(self):
        """Open configuration file"""
        self.browse_config_file()
        # Group DIDs by type
        did_types = {}
        for i, did in enumerate(self.config['dids']):
            dtype = did['data_type']
            if dtype not in did_types:
                did_types[dtype] = []
            did_types[dtype].append((i, did))
        
        for dtype, dids in did_types.items():
            type_node = self.nav_tree.insert(did_root, tk.END, text=f"📋 {dtype} ({len(dids)})", open=True)
            for i, did in dids:
                self.nav_tree.insert(type_node, tk.END, 
                    text=f"{did['did']} {did['did_name']}", 
                    tags=('did', str(i)))
    
    def on_tree_select(self, event):
        """Handle tree selection"""
        selection = self.nav_tree.selection()
        if not selection:
            return
        
        item = self.nav_tree.item(selection[0])
        tags = item['tags']
        
        # Update info panel
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        if tags and tags[0] == 'nvm':
            # Show NVM block details in info panel
            idx = int(tags[1])
            block = self.config['nvm_blocks'][idx]
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
            self.info_text.insert(1.0, info)
            
            # Show edit form in config panel
            self.show_nvm_edit_form(idx)
            
        elif tags and tags[0] == 'did':
            # Show DID details in info panel
            idx = int(tags[1])
            did = self.config['dids'][idx]
            info = f"DID Details\n"
            info += f"{'='*30}\n"
            info += f"DID: {did['did']}\n"
            info += f"Name: {did['did_name']}\n"
            info += f"Length: {'Fixed' if did.get('fixed_length', True) else 'Variable'} ({did.get('expected_length', 0)} bytes)\n"
            if not did.get('fixed_length', True):
                info += f"Range: {did.get('min_length', 0)}-{did.get('max_length', 0)} bytes\n"
            if 'read_config' in did:
                info += f"Read: ✓ ({did['read_config'].get('callback', 'N/A')})\n"
            if 'write_config' in did:
                info += f"Write: ✓ ({did['write_config'].get('callback', 'N/A')})\n"
            info += f"\nDescription:\n{did.get('description', '')}\n"
            self.info_text.insert(1.0, info)
            
            # Show edit form in config panel
            self.show_did_edit_form(idx)
        
        self.info_text.config(state=tk.DISABLED)
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Identify clicked item
        item_id = self.nav_tree.identify_row(event.y)
        if not item_id:
            return
        
        self.nav_tree.selection_set(item_id)
        item = self.nav_tree.item(item_id)
        tags = item['tags']
        
        # Create context menu
        menu = tk.Menu(self.root, tearoff=0)
        
        if tags and tags[0] == 'nvm_root':
            menu.add_command(label="➕ Add New NVM Block", command=self.add_nvm_block)
        elif tags and tags[0] == 'did_root':
            menu.add_command(label="➕ Add New DID", command=self.add_did)
        elif tags and tags[0] == 'nvm':
            menu.add_command(label="✏️ Edit Block", command=self.edit_nvm_block)
            menu.add_command(label="🗑️ Delete Block", command=self.delete_nvm_block)
        elif tags and tags[0] == 'did':
            menu.add_command(label="✏️ Edit DID", command=self.edit_did)
            menu.add_command(label="🗑️ Delete DID", command=self.delete_did)
        else:
            return
        
        menu.post(event.x_root, event.y_root)
    
    def show_nvm_edit_form(self, index):
        """Show NVM block edit form in config panel"""
        # Clear config panel
        for widget in self.config_panel_frame.winfo_children():
            widget.destroy()
        
        block = self.config['nvm_blocks'][index]
        
        # Create form
        form_frame = ttk.Frame(self.config_panel_frame, padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text=f"Edit NVM Block", font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        # Block ID
        ttk.Label(form_frame, text="Block ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        block_id_var = tk.IntVar(value=block['block_id'])
        ttk.Entry(form_frame, textvariable=block_id_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Block Name
        ttk.Label(form_frame, text="Block Name:").grid(row=2, column=0, sticky=tk.W, pady=5)
        block_name_var = tk.StringVar(value=block['block_name'])
        ttk.Entry(form_frame, textvariable=block_name_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Data Length
        ttk.Label(form_frame, text="Block Size:").grid(row=3, column=0, sticky=tk.W, pady=5)
        block_size_var = tk.IntVar(value=block.get('block_size', block.get('data_length', 0)))
        ttk.Entry(form_frame, textvariable=block_size_var, width=30).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # ROM Data Array Name
        ttk.Label(form_frame, text="ROM Array Name:").grid(row=4, column=0, sticky=tk.W, pady=5)
        rom_var = tk.StringVar(value=block.get('rom_data', ''))
        ttk.Entry(form_frame, textvariable=rom_var, width=30).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # RAM Data Array Name
        ttk.Label(form_frame, text="RAM Array Name:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ram_var = tk.StringVar(value=block.get('ram_data', ''))
        ttk.Entry(form_frame, textvariable=ram_var, width=30).grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=6, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=block['description'])
        ttk.Entry(form_frame, textvariable=desc_var, width=30).grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Auto-save on field change
        def save_changes(*args):
            try:
                # Update config silently
                self.config['nvm_blocks'][index]['block_id'] = block_id_var.get()
                self.config['nvm_blocks'][index]['block_name'] = block_name_var.get()
                self.config['nvm_blocks'][index]['block_size'] = block_size_var.get()
                self.config['nvm_blocks'][index]['rom_data'] = rom_var.get().strip()
                self.config['nvm_blocks'][index]['ram_data'] = ram_var.get().strip()
                self.config['nvm_blocks'][index]['description'] = desc_var.get()
                self.set_modified()
                self.refresh_ui()
            except Exception as e:
                pass
        
        # Bind to save on focus out
        for var in [block_id_var, block_name_var, block_size_var, rom_var, ram_var, desc_var]:
            var.trace('w', save_changes)
        
        form_frame.columnconfigure(1, weight=1)
    
    def show_did_edit_form(self, index):
        """Show DID edit form in config panel - new structure"""
        # Clear config panel
        for widget in self.config_panel_frame.winfo_children():
            widget.destroy()
        
        did = self.config['dids'][index]
        
        # Create form with scrollbar (same style as NVM)
        canvas = tk.Canvas(self.config_panel_frame, bg='white')
        scrollbar = ttk.Scrollbar(self.config_panel_frame, orient=tk.VERTICAL, command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="10")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas_frame = canvas.create_window((0, 0), window=form_frame, anchor=tk.NW)
        
        ttk.Label(form_frame, text="Edit DID", font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # DID
        ttk.Label(form_frame, text="DID (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        did_var = tk.StringVar(value=did['did'])
        ttk.Entry(form_frame, textvariable=did_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # DID Name
        ttk.Label(form_frame, text="DID Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        did_name_var = tk.StringVar(value=did['did_name'])
        ttk.Entry(form_frame, textvariable=did_name_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Fixed Length
        fixed_var = tk.BooleanVar(value=did.get('fixed_length', True))
        ttk.Checkbutton(form_frame, text="Fixed Length", variable=fixed_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Expected Length
        ttk.Label(form_frame, text="Expected Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        expected_len_var = tk.IntVar(value=did.get('expected_length', 0))
        ttk.Entry(form_frame, textvariable=expected_len_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Min/Max Length
        ttk.Label(form_frame, text="Min Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        min_len_var = tk.IntVar(value=did.get('min_length', 0))
        ttk.Entry(form_frame, textvariable=min_len_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(form_frame, text="Max Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        max_len_var = tk.IntVar(value=did.get('max_length', 0))
        ttk.Entry(form_frame, textvariable=max_len_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Read Config
        ttk.Label(form_frame, text="Read Configuration", font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        read_callback_var = tk.StringVar(value=did.get('read_config', {}).get('callback', ''))
        ttk.Label(form_frame, text="Callback:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=read_callback_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        read_length_getter_var = tk.StringVar(value=did.get('read_config', {}).get('length_getter', '') or '')
        ttk.Label(form_frame, text="Length Getter:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=read_length_getter_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        read_session_var = tk.IntVar(value=did.get('read_config', {}).get('session_mask', 0))
        ttk.Label(form_frame, text="Session Mask:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=read_session_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        read_security_var = tk.IntVar(value=did.get('read_config', {}).get('security_mask', 0))
        ttk.Label(form_frame, text="Security Mask:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=read_security_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Write Config
        ttk.Label(form_frame, text="Write Configuration", font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        write_callback_var = tk.StringVar(value=did.get('write_config', {}).get('callback', ''))
        ttk.Label(form_frame, text="Callback:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=write_callback_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        write_session_var = tk.IntVar(value=did.get('write_config', {}).get('session_mask', 0))
        ttk.Label(form_frame, text="Session Mask:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=write_session_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        write_security_var = tk.IntVar(value=did.get('write_config', {}).get('security_mask', 0))
        ttk.Label(form_frame, text="Security Mask:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=write_security_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        write_validation_var = tk.BooleanVar(value=did.get('write_config', {}).get('semantic_validation', False))
        ttk.Checkbutton(form_frame, text="Semantic Validation", variable=write_validation_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=did.get('description', ''))
        ttk.Entry(form_frame, textvariable=desc_var, width=30).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Save button
        def save_changes():
            try:
                # Update config with new structure
                self.config['dids'][index]['did'] = did_var.get()
                self.config['dids'][index]['did_name'] = did_name_var.get()
                self.config['dids'][index]['fixed_length'] = fixed_var.get()
                self.config['dids'][index]['expected_length'] = expected_len_var.get()
                self.config['dids'][index]['min_length'] = min_len_var.get()
                self.config['dids'][index]['max_length'] = max_len_var.get()
                
                # Read config
                read_cfg = {}
                if read_callback_var.get():
                    read_cfg['callback'] = read_callback_var.get()
                    read_cfg['length_getter'] = read_length_getter_var.get() if read_length_getter_var.get() else None
                    read_cfg['session_mask'] = read_session_var.get()
                    read_cfg['security_mask'] = read_security_var.get()
                    self.config['dids'][index]['read_config'] = read_cfg
                elif 'read_config' in self.config['dids'][index]:
                    del self.config['dids'][index]['read_config']
                
                # Write config
                write_cfg = {}
                if write_callback_var.get():
                    write_cfg['callback'] = write_callback_var.get()
                    write_cfg['session_mask'] = write_session_var.get()
                    write_cfg['security_mask'] = write_security_var.get()
                    write_cfg['semantic_validation'] = write_validation_var.get()
                    self.config['dids'][index]['write_config'] = write_cfg
                elif 'write_config' in self.config['dids'][index]:
                    del self.config['dids'][index]['write_config']
                
                self.config['dids'][index]['description'] = desc_var.get()
                
                self.set_modified()
                self.refresh_ui()
            except Exception as e:
                pass
        
        # Bind to save on change
        for var in [did_var, did_name_var, fixed_var, expected_len_var, min_len_var, max_len_var,
                    read_callback_var, read_length_getter_var, read_session_var, read_security_var,
                    write_callback_var, write_session_var, write_security_var, write_validation_var, desc_var]:
            if hasattr(var, 'trace'):
                var.trace('w', save_changes)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Update scroll region and bind canvas width
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        
        form_frame.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)
        
        # Initial update
        form_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def new_config(self):
        """Create new configuration"""
        self.config = {
            "project": {
                "name": "GachBoot",
                "version": "1.0.0",
                "generated_path": "../../service/svc_dcm/generated"
            },
            "nvm_blocks": [],
            "dids": []
        }
        self.refresh_ui()
        self.set_modified()
        self.update_title()
        self.status_var.set("New configuration created")
    
    def open_config(self):
        """Open configuration file"""
        filename = filedialog.askopenfilename(
            title="Open Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.config_file = filename
            self.load_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Update config from UI
            self.config['project']['name'] = self.project_name_var.get()
            self.config['project']['version'] = self.version_var.get()
            self.config['project']['generated_path'] = self.output_path_var.get()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            
            self.set_modified(False)
            self.update_title()
            self.status_var.set(f"Saved: {self.config_file}")
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")
    
    def save_as_config(self):
        """Save configuration as new file"""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.config_file = filename
            self.save_config()
    
    def add_nvm_block(self):
        """Add new NVM block"""
        dialog = NvmBlockDialog(self.root, None)
        if dialog.result:
            # Check for duplicate ID
            for block in self.config['nvm_blocks']:
                if block['block_id'] == dialog.result['block_id']:
                    messagebox.showerror("Error", "Block ID already exists!")
                    return
            
            self.config['nvm_blocks'].append(dialog.result)
            self.refresh_ui()
            self.set_modified()
    
    def edit_nvm_block(self):
        """Edit selected NVM block"""
        selection = self.nvm_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a block to edit")
            return
        
        item = self.nvm_tree.item(selection[0])
        block_id = int(item['values'][0])
        
        # Find block
        block = next((b for b in self.config['nvm_blocks'] if b['block_id'] == block_id), None)
        if block:
            dialog = NvmBlockDialog(self.root, block)
            if dialog.result:
                block.update(dialog.result)
                self.refresh_ui()
                self.set_modified()
    
    def delete_nvm_block(self):
        """Delete selected NVM block"""
        selection = self.nvm_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a block to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected block?"):
            item = self.nvm_tree.item(selection[0])
            block_id = int(item['values'][0])
            self.config['nvm_blocks'] = [b for b in self.config['nvm_blocks'] if b['block_id'] != block_id]
            self.refresh_ui()
            self.set_modified()
    
    def add_did(self):
        """Add new DID"""
        dialog = DidDialog(self.root, None)
        if dialog.result:
            # Check for duplicate DID
            for did in self.config['dids']:
                if did['did'] == dialog.result['did']:
                    messagebox.showerror("Error", "DID already exists!")
                    return
            
            self.config['dids'].append(dialog.result)
            self.refresh_ui()
            self.set_modified()
    
    def edit_did(self):
        """Edit selected DID"""
        selection = self.did_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a DID to edit")
            return
        
        item = self.did_tree.item(selection[0])
        did_value = item['values'][0]
        
        # Find DID
        did = next((d for d in self.config['dids'] if d['did'] == did_value), None)
        if did:
            dialog = DidDialog(self.root, did)
            if dialog.result:
                did.update(dialog.result)
                self.refresh_ui()
                self.set_modified()
    
    def delete_did(self):
        """Delete selected DID"""
        selection = self.did_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a DID to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected DID?"):
            item = self.did_tree.item(selection[0])
            did_value = item['values'][0]
            self.config['dids'] = [d for d in self.config['dids'] if d['did'] != did_value]
            self.refresh_ui()
            self.set_modified()
    
    def generate_code(self):
        """Generate code from configuration"""
        try:
            # Save first
            self.save_config()
            
            # Validate first
            nvm_valid, nvm_errors, nvm_warnings = validate_nvm_blocks(self.config['nvm_blocks'])
            did_valid, did_errors, did_warnings = validate_dids(self.config['dids'])
            
            if not nvm_valid or not did_valid:
                error_msg = "Validation failed:\n"
                if nvm_errors:
                    error_msg += "\nNVM Errors:\n" + "\n".join(nvm_errors)
                if did_errors:
                    error_msg += "\nDID Errors:\n" + "\n".join(did_errors)
                messagebox.showerror("Validation Error", error_msg)
                return
            
            # Generate code
            output_path = self.output_path_var.get() or "GenCode"
            
            # Convert to absolute path if relative
            if not os.path.isabs(output_path):
                if self.config_file and os.path.exists(self.config_file):
                    # Relative to config file location
                    config_dir = os.path.dirname(os.path.abspath(self.config_file))
                    output_path = os.path.join(config_dir, output_path)
                else:
                    # Relative to current working directory
                    output_path = os.path.abspath(output_path)
            
            # Create output directory if not exists
            os.makedirs(output_path, exist_ok=True)
            
            project_name = self.config['project']['name']
            version = self.config['project']['version']
            
            print(f"[DEBUG] Generating code to: {output_path}")
            
            nvm_files = generate_nvm_code(self.config['nvm_blocks'], project_name, version, output_path)
            did_files = generate_did_code(self.config['dids'], project_name, version, output_path)
            
            all_files = nvm_files + did_files
            messagebox.showinfo("Success", f"Generated {len(all_files)} files:\n" + "\n".join([os.path.basename(f) for f in all_files]))
            self.status_var.set("Code generation complete")
        except Exception as e:
            messagebox.showerror("Error", f"Code generation failed: {e}")
    
    def validate_config(self):
        """Validate configuration"""
        try:
            # Validate using modules
            nvm_valid, nvm_errors, nvm_warnings = validate_nvm_blocks(self.config['nvm_blocks'])
            did_valid, did_errors, did_warnings = validate_dids(self.config['dids'])
            
            # Collect all messages
            all_errors = nvm_errors + did_errors
            all_warnings = nvm_warnings + did_warnings
            
            # Basic project validation
            if not self.config['project']['name']:
                all_errors.append("Project name is empty")
            
            # Show results
            if all_errors:
                msg = "❌ Validation Failed:\n\n" + "\n".join(all_errors)
                if all_warnings:
                    msg += "\n\n⚠️ Warnings:\n" + "\n".join(all_warnings)
                messagebox.showerror("Validation Errors", msg)
            elif all_warnings:
                msg = "⚠️ Validation Passed with Warnings:\n\n" + "\n".join(all_warnings)
                messagebox.showwarning("Validation Warnings", msg)
            else:
                messagebox.showinfo("Validation", "✓ Configuration is valid!")
        except Exception as e:
            messagebox.showerror("Error", f"Validation failed: {e}")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", 
            "GachBoot ConfigTool v1.0\n\n"
            "AUTOSAR-style configuration tool\n"
            "Generate C/H files from JSON config\n\n"
            "© 2025 GachBoot Project")


class NvmBlockDialog:
    """Dialog for adding/editing NVM block"""
    def __init__(self, parent, block_data):
        self.result = None
        
        dialog = tk.Toplevel(parent)
        dialog.title("NVM Block Editor")
        dialog.geometry("500x350")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Form
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Block ID
        ttk.Label(form_frame, text="Block ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        block_id_var = tk.IntVar(value=block_data['block_id'] if block_data else 0)
        ttk.Entry(form_frame, textvariable=block_id_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Block Name
        ttk.Label(form_frame, text="Block Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        block_name_var = tk.StringVar(value=block_data['block_name'] if block_data else "")
        ttk.Entry(form_frame, textvariable=block_name_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Data Length
        ttk.Label(form_frame, text="Block Size:").grid(row=2, column=0, sticky=tk.W, pady=5)
        data_length_var = tk.IntVar(value=block_data.get('block_size', block_data.get('data_length', 4)) if block_data else 4)
        ttk.Entry(form_frame, textvariable=data_length_var, width=20).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Default Value
        ttk.Label(form_frame, text="ROM Array Name:").grid(row=3, column=0, sticky=tk.W, pady=5)
        rom_data = block_data.get('rom_data', block_data.get('default_value', '')) if block_data else ''
        if isinstance(rom_data, list):
            # Old format - convert to suggested name
            rom_data = f"rom_{block_data.get('block_name', 'data').lower()}"
        default_var = tk.StringVar(value=rom_data)
        ttk.Entry(form_frame, textvariable=default_var, width=40).grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(array name, e.g. rom_default_vin)", font=('', 8)).grid(row=4, column=1, sticky=tk.W)
        
        # RAM Array Name
        ttk.Label(form_frame, text="RAM Array Name:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ram_data = block_data.get('ram_data', '') if block_data else ''
        if isinstance(ram_data, list):
            ram_data = f"ram_{block_data.get('block_name', 'data').lower()}"
        ram_var = tk.StringVar(value=ram_data)
        ttk.Entry(form_frame, textvariable=ram_var, width=40).grid(row=5, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(optional, e.g. ram_mirror_vin)", font=('', 8)).grid(row=6, column=1, sticky=tk.W)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=7, column=0, sticky=tk.W, pady=5)
        description_var = tk.StringVar(value=block_data['description'] if block_data else "")
        ttk.Entry(form_frame, textvariable=description_var, width=40).grid(row=7, column=1, sticky=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        
        def on_ok():
            self.result = {
                "block_id": block_id_var.get(),
                "block_name": block_name_var.get().upper(),
                "block_size": data_length_var.get(),
                "block_type": "NATIVE",
                "rom_data": default_var.get().strip(),
                "ram_data": ram_var.get().strip(),
                "write_protection": False,
                "use_crc": True,
                "description": description_var.get()
            }
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()


class DidDialog:
    """Dialog for adding/editing DID - new schema"""
    def __init__(self, parent, did_data):
        self.result = None
        
        dialog = tk.Toplevel(parent)
        dialog.title("DID Editor")
        dialog.geometry("550x650")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Form with scrollbar
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=canvas.yview)
        form_frame = ttk.Frame(canvas, padding="20")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.create_window((0, 0), window=form_frame, anchor=tk.NW)
        
        row = 0
        
        # DID
        ttk.Label(form_frame, text="DID (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        did_var = tk.StringVar(value=did_data['did'] if did_data else "0xF190")
        ttk.Entry(form_frame, textvariable=did_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # DID Name
        ttk.Label(form_frame, text="DID Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        did_name_var = tk.StringVar(value=did_data['did_name'] if did_data else "")
        ttk.Entry(form_frame, textvariable=did_name_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Fixed Length
        fixed_var = tk.BooleanVar(value=did_data.get('fixed_length', True) if did_data else True)
        ttk.Checkbutton(form_frame, text="Fixed Length", variable=fixed_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Expected Length
        ttk.Label(form_frame, text="Expected Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        expected_len_var = tk.IntVar(value=did_data.get('expected_length', 4) if did_data else 4)
        ttk.Entry(form_frame, textvariable=expected_len_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Min Length (for variable)
        ttk.Label(form_frame, text="Min Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        min_len_var = tk.IntVar(value=did_data.get('min_length', 0) if did_data else 0)
        ttk.Entry(form_frame, textvariable=min_len_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Max Length (for variable)
        ttk.Label(form_frame, text="Max Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        max_len_var = tk.IntVar(value=did_data.get('max_length', 0) if did_data else 0)
        ttk.Entry(form_frame, textvariable=max_len_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Read Configuration
        ttk.Label(form_frame, text="Read Configuration", font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(form_frame, text="Read Callback:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_cb_var = tk.StringVar(value=did_data.get('read_config', {}).get('callback', '') if did_data else '')
        ttk.Entry(form_frame, textvariable=read_cb_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(form_frame, text="Length Getter:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_len_var = tk.StringVar(value=did_data.get('read_config', {}).get('length_getter', '') if did_data else '')
        ttk.Entry(form_frame, textvariable=read_len_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(form_frame, text="Session Mask:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_session_var = tk.IntVar(value=did_data.get('read_config', {}).get('session_mask', 1) if did_data else 1)
        ttk.Entry(form_frame, textvariable=read_session_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(form_frame, text="Security Mask:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_security_var = tk.IntVar(value=did_data.get('read_config', {}).get('security_mask', 0) if did_data else 0)
        ttk.Entry(form_frame, textvariable=read_security_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Write Configuration
        ttk.Label(form_frame, text="Write Configuration", font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(form_frame, text="Write Callback:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_cb_var = tk.StringVar(value=did_data.get('write_config', {}).get('callback', '') if did_data else '')
        ttk.Entry(form_frame, textvariable=write_cb_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(form_frame, text="Session Mask:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_session_var = tk.IntVar(value=did_data.get('write_config', {}).get('session_mask', 2) if did_data else 2)
        ttk.Entry(form_frame, textvariable=write_session_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(form_frame, text="Security Mask:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_security_var = tk.IntVar(value=did_data.get('write_config', {}).get('security_mask', 0) if did_data else 0)
        ttk.Entry(form_frame, textvariable=write_security_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        write_validation_var = tk.BooleanVar(value=did_data.get('write_config', {}).get('semantic_validation', False) if did_data else False)
        ttk.Checkbutton(form_frame, text="Semantic Validation", variable=write_validation_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Separator
        ttk.Separator(form_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        description_var = tk.StringVar(value=did_data.get('description', '') if did_data else "")
        ttk.Entry(form_frame, textvariable=description_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def on_ok():
            result = {
                "did": did_var.get(),
                "did_name": did_name_var.get().upper(),
                "fixed_length": fixed_var.get(),
                "expected_length": expected_len_var.get(),
                "min_length": min_len_var.get(),
                "max_length": max_len_var.get(),
                "description": description_var.get()
            }
            
            # Add read config if callback provided
            if read_cb_var.get():
                result['read_config'] = {
                    "callback": read_cb_var.get(),
                    "length_getter": read_len_var.get() if read_len_var.get() else None,
                    "session_mask": read_session_var.get(),
                    "security_mask": read_security_var.get()
                }
            
            # Add write config if callback provided
            if write_cb_var.get():
                result['write_config'] = {
                    "callback": write_cb_var.get(),
                    "session_mask": write_session_var.get(),
                    "security_mask": write_security_var.get(),
                    "semantic_validation": write_validation_var.get()
                }
            
            self.result = result
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
        
        # Update scroll region
        form_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        dialog.wait_window()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ConfigEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
