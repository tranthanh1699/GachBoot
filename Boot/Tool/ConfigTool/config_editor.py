#!/usr/bin/env python3
"""
GachBoot Configuration Editor (Tkinter GUI)
AUTOSAR-style configuration tool with graphical interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from Module.nvm_module import validate_nvm_blocks, generate_nvm_code
from Module.did_module import validate_dids, generate_did_code
from Module.session_module import validate_sessions, generate_session_code
from Module.security_module import validate_security_levels, generate_security_code
from Module.cmake_module import generate_cmake_file

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
        self.setup_session_tab()
        self.setup_security_tab()
        
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
    
    def setup_session_tab(self):
        """Setup Sessions tab"""
        session_frame = ttk.Frame(self.config_panel_frame)
        
        # Toolbar
        toolbar = ttk.Frame(session_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Add Session", command=self.add_session).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Session", command=self.edit_session).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Session", command=self.delete_session).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text=f"Total Sessions: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.session_count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=self.session_count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        # Treeview
        tree_frame = ttk.Frame(session_frame)
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
    
    def setup_security_tab(self):
        """Setup Security Access tab"""
        security_frame = ttk.Frame(self.config_panel_frame)
        
        # Toolbar
        toolbar = ttk.Frame(security_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Add Security Level", command=self.add_security_level).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit Security Level", command=self.edit_security_level).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete Security Level", command=self.delete_security_level).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text=f"Total Levels: ", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.security_count_var = tk.StringVar(value="0")
        ttk.Label(toolbar, textvariable=self.security_count_var, font=('', 9, 'bold')).pack(side=tk.LEFT)
        
        # Treeview
        tree_frame = ttk.Frame(security_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("Level", "Seed Sub", "Key Sub", "Seed Size", "Key Size", "Max Attempts", "Delay")
        self.security_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        widths = {"Level": 60, "Seed Sub": 100, "Key Sub": 100, "Seed Size": 90, "Key Size": 90, "Max Attempts": 110, "Delay": 100}
        for col in columns:
            self.security_tree.heading(col, text=col)
            self.security_tree.column(col, width=widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.security_tree.yview)
        self.security_tree.configure(yscrollcommand=scrollbar.set)
        
        self.security_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
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
        
        # Sessions
        self.session_tree.delete(*self.session_tree.get_children())
        sessions = self.config.get('sessions', [])
        for session in sessions:
            self.session_tree.insert('', tk.END, values=(
                session['session_name'],
                session['session_value'],
                session.get('description', '')
            ))
        self.session_count_var.set(str(len(sessions)))
        
        # Security Levels
        self.security_tree.delete(*self.security_tree.get_children())
        security_levels = self.config.get('security_levels', [])
        for sec in security_levels:
            self.security_tree.insert('', tk.END, values=(
                sec['security_level'],
                sec['seed_request_sub'],
                sec['key_request_sub'],
                sec['seed_size'],
                sec['key_size'],
                sec['max_attempts'],
                f"{sec['delay_time']} ms"
            ))
        self.security_count_var.set(str(len(security_levels)))
    
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
        
        # Sessions branch with count
        sessions = self.config.get('sessions', [])
        session_count = len(sessions)
        session_root = self.nav_tree.insert(root, tk.END, text=f"🔐 Sessions ({session_count})", open=True, tags=('session_root',))
        for i, session in enumerate(sessions):
            self.nav_tree.insert(session_root, tk.END,
                text=f"  {session['session_name']}",
                tags=('session', str(i)))
        
        # Security Levels branch with count
        security_levels = self.config.get('security_levels', [])
        security_count = len(security_levels)
        security_root = self.nav_tree.insert(root, tk.END, text=f"🔒 Security Access ({security_count})", open=True, tags=('security_root',))
        for i, sec in enumerate(security_levels):
            self.nav_tree.insert(security_root, tk.END,
                text=f"  Level {sec['security_level']} (0x{int(sec['seed_request_sub'], 16):02X}/0x{int(sec['key_request_sub'], 16):02X})" if isinstance(sec['seed_request_sub'], str) else f"  Level {sec['security_level']}",
                tags=('security', str(i)))
    
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
        
        elif tags and tags[0] == 'session':
            # Show Session details in info panel
            idx = int(tags[1])
            session = self.config['sessions'][idx]
            info = f"Session Details\n"
            info += f"{'='*30}\n"
            info += f"Name: {session['session_name']}\n"
            info += f"Value: {session['session_value']}\n"
            info += f"\nDescription:\n{session.get('description', '')}\n"
            self.info_text.insert(1.0, info)
            
            # Show edit form in config panel
            self.show_session_edit_form(idx)
        
        elif tags and tags[0] == 'security':
            # Show Security details in info panel
            idx = int(tags[1])
            sec = self.config['security_levels'][idx]
            info = f"Security Level Details\n"
            info += f"{'='*30}\n"
            info += f"Level: {sec['security_level']}\n"
            info += f"Seed Request: {sec['seed_request_sub']}\n"
            info += f"Key Request: {sec['key_request_sub']}\n"
            info += f"Seed Size: {sec['seed_size']} bytes\n"
            info += f"Key Size: {sec['key_size']} bytes\n"
            info += f"Max Attempts: {sec['max_attempts']}\n"
            info += f"Delay Time: {sec['delay_time']} ms\n"
            info += f"Get Seed Func: {sec['get_seed_func']}\n"
            info += f"Compare Key Func: {sec['compare_key_func']}\n"
            info += f"\nSupported Sessions:\n"
            for sess in sec.get('supported_sessions', []):
                info += f"  • {sess}\n"
            self.info_text.insert(1.0, info)
            
            # Show edit form in config panel
            self.show_security_edit_form(idx)
        
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
        elif tags and tags[0] == 'session_root':
            menu.add_command(label="➕ Add New Session", command=self.add_session)
        elif tags and tags[0] == 'security_root':
            menu.add_command(label="➕ Add New Security Level", command=self.add_security_level)
        elif tags and tags[0] == 'nvm':
            menu.add_command(label="✏️ Edit Block", command=self.edit_nvm_block)
            menu.add_command(label="🗑️ Delete Block", command=self.delete_nvm_block)
        elif tags and tags[0] == 'did':
            menu.add_command(label="✏️ Edit DID", command=self.edit_did)
            menu.add_command(label="🗑️ Delete DID", command=self.delete_did)
        elif tags and tags[0] == 'session':
            menu.add_command(label="✏️ Edit Session", command=self.edit_session)
            menu.add_command(label="🗑️ Delete Session", command=self.delete_session)
        elif tags and tags[0] == 'security':
            menu.add_command(label="✏️ Edit Security Level", command=self.edit_security_level)
            menu.add_command(label="🗑️ Delete Security Level", command=self.delete_security_level)
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
        
        # Read Session Support
        ttk.Label(form_frame, text="Session Support:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_session_frame = ttk.Frame(form_frame)
        read_session_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Get available sessions
        available_sessions = self.config.get('sessions', [])
        read_session_vars = {}
        current_read_sessions = did.get('read_config', {}).get('supported_sessions', [])
        
        for i, session in enumerate(available_sessions):
            var = tk.BooleanVar(value=session['session_name'] in current_read_sessions)
            read_session_vars[session['session_name']] = var
            ttk.Checkbutton(read_session_frame, text=session['session_name'], variable=var).grid(row=i, column=0, sticky=tk.W)
        row += 1
        
        # Read Security Levels
        ttk.Label(form_frame, text="Required Security:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_security_frame = ttk.Frame(form_frame)
        read_security_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        available_security = self.config.get('security_levels', [])
        read_security_vars = {}
        current_read_security = did.get('read_config', {}).get('required_security_levels', [])
        
        for i, sec in enumerate(available_security):
            sec_name = f"Level {sec['security_level']}"
            var = tk.BooleanVar(value=sec['security_level'] in current_read_security)
            read_security_vars[sec['security_level']] = var
            ttk.Checkbutton(read_security_frame, text=sec_name, variable=var).grid(row=i, column=0, sticky=tk.W)
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
        
        # Write Session Support
        ttk.Label(form_frame, text="Session Support:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_session_frame = ttk.Frame(form_frame)
        write_session_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        write_session_vars = {}
        current_write_sessions = did.get('write_config', {}).get('supported_sessions', [])
        
        for i, session in enumerate(available_sessions):
            var = tk.BooleanVar(value=session['session_name'] in current_write_sessions)
            write_session_vars[session['session_name']] = var
            ttk.Checkbutton(write_session_frame, text=session['session_name'], variable=var).grid(row=i, column=0, sticky=tk.W)
        row += 1
        
        # Write Security Levels
        ttk.Label(form_frame, text="Required Security:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_security_frame = ttk.Frame(form_frame)
        write_security_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        write_security_vars = {}
        current_write_security = did.get('write_config', {}).get('required_security_levels', [])
        
        for i, sec in enumerate(available_security):
            sec_name = f"Level {sec['security_level']}"
            var = tk.BooleanVar(value=sec['security_level'] in current_write_security)
            write_security_vars[sec['security_level']] = var
            ttk.Checkbutton(write_security_frame, text=sec_name, variable=var).grid(row=i, column=0, sticky=tk.W)
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
                    # Save selected sessions
                    selected_read_sessions = [name for name, var in read_session_vars.items() if var.get()]
                    read_cfg['supported_sessions'] = selected_read_sessions
                    # Save selected security levels
                    selected_read_security = [level for level, var in read_security_vars.items() if var.get()]
                    read_cfg['required_security_levels'] = selected_read_security
                    self.config['dids'][index]['read_config'] = read_cfg
                elif 'read_config' in self.config['dids'][index]:
                    del self.config['dids'][index]['read_config']
                
                # Write config
                write_cfg = {}
                if write_callback_var.get():
                    write_cfg['callback'] = write_callback_var.get()
                    # Save selected sessions
                    selected_write_sessions = [name for name, var in write_session_vars.items() if var.get()]
                    write_cfg['supported_sessions'] = selected_write_sessions
                    # Save selected security levels
                    selected_write_security = [level for level, var in write_security_vars.items() if var.get()]
                    write_cfg['required_security_levels'] = selected_write_security
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
                    read_callback_var, read_length_getter_var,
                    write_callback_var, write_validation_var, desc_var]:
            if hasattr(var, 'trace'):
                var.trace('w', lambda *args: save_changes())
        
        # Bind session checkboxes
        for var in read_session_vars.values():
            if hasattr(var, 'trace'):
                var.trace('w', lambda *args: save_changes())
        
        for var in write_session_vars.values():
            if hasattr(var, 'trace'):
                var.trace('w', lambda *args: save_changes())
        
        # Bind security level checkboxes
        for var in read_security_vars.values():
            if hasattr(var, 'trace'):
                var.trace('w', lambda *args: save_changes())
        
        for var in write_security_vars.values():
            if hasattr(var, 'trace'):
                var.trace('w', lambda *args: save_changes())
        
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
    
    def show_session_edit_form(self, index):
        """Show Session edit form in config panel"""
        # Clear config panel
        for widget in self.config_panel_frame.winfo_children():
            widget.destroy()
        
        session = self.config['sessions'][index]
        
        # Create scrollable form
        canvas = tk.Canvas(self.config_panel_frame)
        scrollbar = ttk.Scrollbar(self.config_panel_frame, orient="vertical", command=canvas.yview)
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
        
        # Save changes function
        def save_changes(*args):
            try:
                self.config['sessions'][index]['session_name'] = session_name_var.get()
                self.config['sessions'][index]['session_value'] = session_value_var.get()
                self.config['sessions'][index]['description'] = desc_var.get()
                
                self.set_modified()
                self.refresh_ui()
            except Exception as e:
                pass
        
        # Bind to save on change
        for var in [session_name_var, session_value_var, desc_var]:
            if hasattr(var, 'trace'):
                var.trace('w', save_changes)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Update scroll region
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas_frame = canvas.find_withtag("canvas_frame")
            if canvas_frame:
                canvas.itemconfig(canvas_frame[0], width=event.width)
        
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
            "dids": [],
            "sessions": []
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
        dialog = DidDialog(self.root, None, self.config.get('sessions', []), self.config.get('security_levels', []))
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
            dialog = DidDialog(self.root, did, self.config.get('sessions', []), self.config.get('security_levels', []))
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
    
    def add_session(self):
        """Add new Session"""
        dialog = SessionDialog(self.root, None)
        if dialog.result:
            # Check for duplicate name/value
            for session in self.config.get('sessions', []):
                if session['session_name'] == dialog.result['session_name']:
                    messagebox.showerror("Error", f"Session name {dialog.result['session_name']} already exists!")
                    return
                if session['session_value'] == dialog.result['session_value']:
                    messagebox.showerror("Error", f"Session value {dialog.result['session_value']} already exists!")
                    return
            
            if 'sessions' not in self.config:
                self.config['sessions'] = []
            
            self.config['sessions'].append(dialog.result)
            self.refresh_ui()
            self.set_modified()
    
    def edit_session(self):
        """Edit selected Session"""
        selection = self.session_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a session to edit")
            return
        
        item = self.session_tree.item(selection[0])
        session_name = item['values'][0]
        session = next((s for s in self.config.get('sessions', []) if s['session_name'] == session_name), None)
        
        if session:
            dialog = SessionDialog(self.root, session)
            if dialog.result:
                # Update session
                idx = self.config['sessions'].index(session)
                self.config['sessions'][idx] = dialog.result
                self.refresh_ui()
                self.set_modified()
    
    def delete_session(self):
        """Delete selected Session"""
        selection = self.session_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a session to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected session?"):
            item = self.session_tree.item(selection[0])
            session_name = item['values'][0]
            self.config['sessions'] = [s for s in self.config.get('sessions', []) if s['session_name'] != session_name]
            self.refresh_ui()
            self.set_modified()
    
    def add_security_level(self):
        """Add new Security Level"""
        available_sessions = [s['session_name'] for s in self.config.get('sessions', [])]
        dialog = SecurityLevelDialog(self.root, None, available_sessions)
        if dialog.result:
            # Check for duplicate level
            for sec in self.config.get('security_levels', []):
                if sec['security_level'] == dialog.result['security_level']:
                    messagebox.showerror("Error", f"Security level {dialog.result['security_level']} already exists!")
                    return
            
            if 'security_levels' not in self.config:
                self.config['security_levels'] = []
            
            self.config['security_levels'].append(dialog.result)
            self.refresh_ui()
            self.set_modified()
    
    def edit_security_level(self):
        """Edit selected Security Level"""
        selection = self.security_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a security level to edit")
            return
        
        item = self.security_tree.item(selection[0])
        level = item['values'][0]
        sec = next((s for s in self.config.get('security_levels', []) if s['security_level'] == level), None)
        
        if sec:
            available_sessions = [s['session_name'] for s in self.config.get('sessions', [])]
            dialog = SecurityLevelDialog(self.root, sec, available_sessions)
            if dialog.result:
                # Update security level
                idx = self.config['security_levels'].index(sec)
                self.config['security_levels'][idx] = dialog.result
                self.refresh_ui()
                self.set_modified()
    
    def delete_security_level(self):
        """Delete selected Security Level"""
        selection = self.security_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a security level to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected security level?"):
            item = self.security_tree.item(selection[0])
            level = item['values'][0]
            self.config['security_levels'] = [s for s in self.config.get('security_levels', []) if s['security_level'] != level]
            self.refresh_ui()
            self.set_modified()
    
    def show_security_edit_form(self, index):
        """Show Security Level edit form in config panel"""
        # Clear config panel
        for widget in self.config_panel_frame.winfo_children():
            widget.destroy()
        
        sec = self.config['security_levels'][index]
        
        # Create form
        form_frame = ttk.Frame(self.config_panel_frame, padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text=f"Edit Security Level {sec['security_level']}", font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        row = 1
        
        # Level
        ttk.Label(form_frame, text="Security Level:").grid(row=row, column=0, sticky=tk.W, pady=5)
        level_var = tk.IntVar(value=sec['security_level'])
        ttk.Entry(form_frame, textvariable=level_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Seed Request Sub
        ttk.Label(form_frame, text="Seed Request Sub:").grid(row=row, column=0, sticky=tk.W, pady=5)
        seed_sub_var = tk.StringVar(value=sec['seed_request_sub'])
        ttk.Entry(form_frame, textvariable=seed_sub_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Key Request Sub
        ttk.Label(form_frame, text="Key Request Sub:").grid(row=row, column=0, sticky=tk.W, pady=5)
        key_sub_var = tk.StringVar(value=sec['key_request_sub'])
        ttk.Entry(form_frame, textvariable=key_sub_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Seed Size
        ttk.Label(form_frame, text="Seed Size (bytes):").grid(row=row, column=0, sticky=tk.W, pady=5)
        seed_size_var = tk.IntVar(value=sec['seed_size'])
        ttk.Entry(form_frame, textvariable=seed_size_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Key Size
        ttk.Label(form_frame, text="Key Size (bytes):").grid(row=row, column=0, sticky=tk.W, pady=5)
        key_size_var = tk.IntVar(value=sec['key_size'])
        ttk.Entry(form_frame, textvariable=key_size_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Max Attempts
        ttk.Label(form_frame, text="Max Attempts:").grid(row=row, column=0, sticky=tk.W, pady=5)
        max_attempts_var = tk.IntVar(value=sec['max_attempts'])
        ttk.Entry(form_frame, textvariable=max_attempts_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Delay Time
        ttk.Label(form_frame, text="Delay Time (ms):").grid(row=row, column=0, sticky=tk.W, pady=5)
        delay_time_var = tk.IntVar(value=sec['delay_time'])
        ttk.Entry(form_frame, textvariable=delay_time_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Get Seed Function
        ttk.Label(form_frame, text="Get Seed Func:").grid(row=row, column=0, sticky=tk.W, pady=5)
        get_seed_var = tk.StringVar(value=sec['get_seed_func'])
        ttk.Entry(form_frame, textvariable=get_seed_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Compare Key Function
        ttk.Label(form_frame, text="Compare Key Func:").grid(row=row, column=0, sticky=tk.W, pady=5)
        compare_key_var = tk.StringVar(value=sec['compare_key_func'])
        ttk.Entry(form_frame, textvariable=compare_key_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Sessions
        ttk.Label(form_frame, text="Supported Sessions:", font=('', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1
        
        session_frame = ttk.LabelFrame(form_frame, text="Select Sessions", padding="10")
        session_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        session_vars = {}
        available_sessions = [s['session_name'] for s in self.config.get('sessions', [])]
        for sess_name in available_sessions:
            var = tk.BooleanVar(value=sess_name in sec.get('supported_sessions', []))
            ttk.Checkbutton(session_frame, text=sess_name, variable=var).pack(anchor=tk.W)
            session_vars[sess_name] = var
            var.trace_add('write', lambda *args, idx=index, svars=session_vars: self.update_security_sessions(idx, svars))
        
        # Save button
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def save_changes():
            self.config['security_levels'][index]['security_level'] = level_var.get()
            self.config['security_levels'][index]['seed_request_sub'] = seed_sub_var.get()
            self.config['security_levels'][index]['key_request_sub'] = key_sub_var.get()
            self.config['security_levels'][index]['seed_size'] = seed_size_var.get()
            self.config['security_levels'][index]['key_size'] = key_size_var.get()
            self.config['security_levels'][index]['max_attempts'] = max_attempts_var.get()
            self.config['security_levels'][index]['delay_time'] = delay_time_var.get()
            self.config['security_levels'][index]['get_seed_func'] = get_seed_var.get()
            self.config['security_levels'][index]['compare_key_func'] = compare_key_var.get()
            self.refresh_ui()
            self.set_modified()
        
        ttk.Button(button_frame, text="💾 Save Changes", command=save_changes).pack(side=tk.LEFT, padx=5)
    
    def update_security_sessions(self, index, session_vars):
        """Update security level supported sessions"""
        selected_sessions = [name for name, var in session_vars.items() if var.get()]
        self.config['security_levels'][index]['supported_sessions'] = selected_sessions
        self.set_modified()
    
    def generate_code(self):
        """Generate code from configuration"""
        try:
            # Save first
            self.save_config()
            
            # Validate first
            nvm_valid, nvm_errors, nvm_warnings = validate_nvm_blocks(self.config['nvm_blocks'])
            did_valid, did_errors, did_warnings = validate_dids(self.config['dids'])
            session_valid, session_errors, session_warnings = validate_sessions(self.config.get('sessions', []))
            security_valid, security_errors, security_warnings = validate_security_levels(self.config.get('security_levels', []))
            
            if not nvm_valid or not did_valid or not session_valid or not security_valid:
                error_msg = "Validation failed:\n"
                if nvm_errors:
                    error_msg += "\nNVM Errors:\n" + "\n".join(nvm_errors)
                if did_errors:
                    error_msg += "\nDID Errors:\n" + "\n".join(did_errors)
                if session_errors:
                    error_msg += "\nSession Errors:\n" + "\n".join(session_errors)
                if security_errors:
                    error_msg += "\nSecurity Errors:\n" + "\n".join(security_errors)
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
            did_files = generate_did_code(self.config['dids'], self.config.get('sessions', []), 
                                          self.config.get('security_levels', []), project_name, version, output_path)
            session_files = []
            if self.config.get('sessions'):
                session_success = generate_session_code(self.config['sessions'], output_path)
                if session_success:
                    session_files = [
                        os.path.join(output_path, "DCM_Session_Gen", "DCM_Session_PBCfg.h"),
                        os.path.join(output_path, "DCM_Session_Gen", "DCM_Session_PBCfg.c")
                    ]
            security_files = []
            if self.config.get('security_levels'):
                security_files = generate_security_code(self.config['security_levels'], self.config.get('sessions', []), 
                                                       project_name, version, output_path)
            cmake_file = generate_cmake_file(output_path, project_name, version)
            
            all_files = nvm_files + did_files + session_files + security_files + [cmake_file]
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
            session_valid, session_errors, session_warnings = validate_sessions(self.config.get('sessions', []))
            security_valid, security_errors, security_warnings = validate_security_levels(self.config.get('security_levels', []))
            
            # Collect all messages
            all_errors = nvm_errors + did_errors + session_errors + security_errors
            all_warnings = nvm_warnings + did_warnings + session_warnings + security_warnings
            
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
    def __init__(self, parent, did_data, available_sessions=None, available_security=None):
        self.result = None
        self.available_sessions = available_sessions or []
        self.available_security = available_security or []
        
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
        
        ttk.Label(form_frame, text="Session Support:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_session_frame = ttk.Frame(form_frame)
        read_session_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        read_session_vars = {}
        current_read_sessions = did_data.get('read_config', {}).get('supported_sessions', []) if did_data else []
        for i, session in enumerate(self.available_sessions):
            var = tk.BooleanVar(value=session['session_name'] in current_read_sessions)
            read_session_vars[session['session_name']] = var
            ttk.Checkbutton(read_session_frame, text=session['session_name'], variable=var).grid(row=i, column=0, sticky=tk.W)
        row += 1
        
        ttk.Label(form_frame, text="Required Security:").grid(row=row, column=0, sticky=tk.W, pady=5)
        read_security_frame = ttk.Frame(form_frame)
        read_security_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        read_security_vars = {}
        current_read_security = did_data.get('read_config', {}).get('required_security_levels', []) if did_data else []
        for i, sec in enumerate(self.available_security):
            sec_name = f"Level {sec['security_level']}"
            var = tk.BooleanVar(value=sec['security_level'] in current_read_security)
            read_security_vars[sec['security_level']] = var
            ttk.Checkbutton(read_security_frame, text=sec_name, variable=var).grid(row=i, column=0, sticky=tk.W)
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
        
        ttk.Label(form_frame, text="Session Support:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_session_frame = ttk.Frame(form_frame)
        write_session_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        write_session_vars = {}
        current_write_sessions = did_data.get('write_config', {}).get('supported_sessions', []) if did_data else []
        for i, session in enumerate(self.available_sessions):
            var = tk.BooleanVar(value=session['session_name'] in current_write_sessions)
            write_session_vars[session['session_name']] = var
            ttk.Checkbutton(write_session_frame, text=session['session_name'], variable=var).grid(row=i, column=0, sticky=tk.W)
        row += 1
        
        ttk.Label(form_frame, text="Required Security:").grid(row=row, column=0, sticky=tk.W, pady=5)
        write_security_frame = ttk.Frame(form_frame)
        write_security_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        write_security_vars = {}
        current_write_security = did_data.get('write_config', {}).get('required_security_levels', []) if did_data else []
        for i, sec in enumerate(self.available_security):
            sec_name = f"Level {sec['security_level']}"
            var = tk.BooleanVar(value=sec['security_level'] in current_write_security)
            write_security_vars[sec['security_level']] = var
            ttk.Checkbutton(write_security_frame, text=sec_name, variable=var).grid(row=i, column=0, sticky=tk.W)
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
                selected_read_sessions = [name for name, var in read_session_vars.items() if var.get()]
                selected_read_security = [level for level, var in read_security_vars.items() if var.get()]
                result['read_config'] = {
                    "callback": read_cb_var.get(),
                    "length_getter": read_len_var.get() if read_len_var.get() else None,
                    "supported_sessions": selected_read_sessions,
                    "required_security_levels": selected_read_security
                }
            
            # Add write config if callback provided
            if write_cb_var.get():
                selected_write_sessions = [name for name, var in write_session_vars.items() if var.get()]
                selected_write_security = [level for level, var in write_security_vars.items() if var.get()]
                result['write_config'] = {
                    "callback": write_cb_var.get(),
                    "supported_sessions": selected_write_sessions,
                    "required_security_levels": selected_write_security,
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


class SessionDialog:
    """Dialog for adding/editing Session"""
    def __init__(self, parent, session_data):
        self.result = None
        
        dialog = tk.Toplevel(parent)
        dialog.title("Session Editor")
        dialog.geometry("550x500")
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
        
        # Session Name
        ttk.Label(form_frame, text="Session Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        session_name_var = tk.StringVar(value=session_data['session_name'] if session_data else "DCM_DEFAULT_SESSION")
        ttk.Entry(form_frame, textvariable=session_name_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Session Value
        ttk.Label(form_frame, text="Session Value (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        session_value_var = tk.StringVar(value=session_data['session_value'] if session_data else "0x01")
        ttk.Entry(form_frame, textvariable=session_value_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        description_var = tk.StringVar(value=session_data.get('description', '') if session_data else "")
        ttk.Entry(form_frame, textvariable=description_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def on_ok():
            result = {
                "session_name": session_name_var.get().upper(),
                "session_value": session_value_var.get(),
                "description": description_var.get()
            }
            
            self.result = result
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
        
        # Update scroll region
        form_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        dialog.wait_window()


class SecurityLevelDialog:
    """Dialog for adding/editing Security Level"""
    def __init__(self, parent, security_data, available_sessions):
        self.result = None
        
        dialog = tk.Toplevel(parent)
        dialog.title("Security Level Editor")
        dialog.geometry("600x700")
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
        
        # Security Level
        ttk.Label(form_frame, text="Security Level:").grid(row=row, column=0, sticky=tk.W, pady=5)
        level_var = tk.IntVar(value=security_data['security_level'] if security_data else 1)
        ttk.Entry(form_frame, textvariable=level_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Seed Request Sub
        ttk.Label(form_frame, text="Seed Request Sub (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        seed_sub_var = tk.StringVar(value=security_data['seed_request_sub'] if security_data else "0x01")
        ttk.Entry(form_frame, textvariable=seed_sub_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(odd: 0x01, 0x03, 0x05...)", foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Key Request Sub (auto-calculated)
        ttk.Label(form_frame, text="Key Request Sub (hex):").grid(row=row, column=0, sticky=tk.W, pady=5)
        key_sub_var = tk.StringVar(value=security_data['key_request_sub'] if security_data else "0x02")
        key_entry = ttk.Entry(form_frame, textvariable=key_sub_var, width=20, state='readonly')
        key_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(auto: seed + 1)", foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        def update_key_sub(*args):
            try:
                seed_val = int(seed_sub_var.get(), 16) if seed_sub_var.get().startswith('0x') else int(seed_sub_var.get())
                key_sub_var.set(f"0x{seed_val + 1:02X}")
            except:
                pass
        
        seed_sub_var.trace_add('write', update_key_sub)
        
        # Seed Size
        ttk.Label(form_frame, text="Seed Size (bytes):").grid(row=row, column=0, sticky=tk.W, pady=5)
        seed_size_var = tk.IntVar(value=security_data['seed_size'] if security_data else 4)
        ttk.Entry(form_frame, textvariable=seed_size_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(1-16)", foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Key Size
        ttk.Label(form_frame, text="Key Size (bytes):").grid(row=row, column=0, sticky=tk.W, pady=5)
        key_size_var = tk.IntVar(value=security_data['key_size'] if security_data else 4)
        ttk.Entry(form_frame, textvariable=key_size_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(1-16)", foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Max Attempts
        ttk.Label(form_frame, text="Max Attempts:").grid(row=row, column=0, sticky=tk.W, pady=5)
        max_attempts_var = tk.IntVar(value=security_data['max_attempts'] if security_data else 3)
        ttk.Entry(form_frame, textvariable=max_attempts_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Delay Time
        ttk.Label(form_frame, text="Delay Time (ms):").grid(row=row, column=0, sticky=tk.W, pady=5)
        delay_time_var = tk.IntVar(value=security_data['delay_time'] if security_data else 10000)
        ttk.Entry(form_frame, textvariable=delay_time_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Get Seed Function
        ttk.Label(form_frame, text="Get Seed Function:").grid(row=row, column=0, sticky=tk.W, pady=5)
        get_seed_var = tk.StringVar(value=security_data['get_seed_func'] if security_data else f"security_get_seed_level_{level_var.get()}")
        ttk.Entry(form_frame, textvariable=get_seed_var, width=35).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Compare Key Function
        ttk.Label(form_frame, text="Compare Key Function:").grid(row=row, column=0, sticky=tk.W, pady=5)
        compare_key_var = tk.StringVar(value=security_data['compare_key_func'] if security_data else f"security_compare_key_level_{level_var.get()}")
        ttk.Entry(form_frame, textvariable=compare_key_var, width=35).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Supported Sessions
        ttk.Label(form_frame, text="Supported Sessions:", font=('', 10, 'bold')).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        row += 1
        
        session_frame = ttk.LabelFrame(form_frame, text="Select Sessions", padding="10")
        session_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        session_vars = {}
        current_sessions = security_data.get('supported_sessions', []) if security_data else []
        
        for sess_name in available_sessions:
            var = tk.BooleanVar(value=sess_name in current_sessions)
            ttk.Checkbutton(session_frame, text=sess_name, variable=var).pack(anchor=tk.W)
            session_vars[sess_name] = var
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        def on_ok():
            selected_sessions = [name for name, var in session_vars.items() if var.get()]
            
            if not selected_sessions:
                messagebox.showerror("Error", "Please select at least one session")
                return
            
            result = {
                "security_level": level_var.get(),
                "seed_request_sub": seed_sub_var.get(),
                "key_request_sub": key_sub_var.get(),
                "seed_size": seed_size_var.get(),
                "key_size": key_size_var.get(),
                "max_attempts": max_attempts_var.get(),
                "delay_time": delay_time_var.get(),
                "supported_sessions": selected_sessions,
                "get_seed_func": get_seed_var.get(),
                "compare_key_func": compare_key_var.get()
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
