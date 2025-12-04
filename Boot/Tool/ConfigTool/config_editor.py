#!/usr/bin/env python3
"""
GachBoot Configuration Editor (Tkinter GUI)
AUTOSAR-style configuration tool with graphical interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from code_generator import CodeGenerator

class ConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("GachBoot ConfigTool - AUTOSAR Style Editor")
        self.root.geometry("1400x900")
        
        self.config_file = "gachboot_config.json"
        self.config = None
        self.modified = False
        
        # Apply theme
        style = ttk.Style()
        style.theme_use('clam')
        
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
        generate_menu.add_command(label="Generate Code", command=self.generate_code)
        generate_menu.add_command(label="Validate Config", command=self.validate_config)
        
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
        
        # Right panel: Content
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        # Configure grid weights for right panel
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Project info frame
        self.setup_project_frame(right_frame)
        
        # Content notebook (tabs)
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # NVM Blocks tab
        self.setup_nvm_tab()
        
        # DIDs tab
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
        nvm_frame = ttk.Frame(self.notebook)
        self.notebook.add(nvm_frame, text="💾 NVM Blocks")
        
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
        did_frame = ttk.Frame(self.notebook)
        self.notebook.add(did_frame, text="🔧 DIDs")
        
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
                self.status_var.set(f"Loaded: {self.config_file}")
            else:
                self.new_config()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
    
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
            default_str = ' '.join([f"{v:02X}" for v in block['default_value']])
            self.nvm_tree.insert('', tk.END, values=(
                block['block_id'],
                block['block_name'],
                block['data_length'],
                default_str,
                block['description']
            ))
        self.nvm_count_var.set(str(len(self.config['nvm_blocks'])))
        
        # DIDs
        self.did_tree.delete(*self.did_tree.get_children())
        for did in self.config['dids']:
            self.did_tree.insert('', tk.END, values=(
                did['did'],
                did['did_name'],
                did['data_type'],
                did['data_length'],
                '✓' if did['read_access'] else '✗',
                '✓' if did['write_access'] else '✗',
                did['description']
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
        nvm_root = self.nav_tree.insert(root, tk.END, text=f"💾 NVM Blocks ({nvm_count})", open=True)
        for i, block in enumerate(self.config['nvm_blocks']):
            block_node = self.nav_tree.insert(nvm_root, tk.END, 
                text=f"  [{block['block_id']}] {block['block_name']}", 
                tags=('nvm', str(i)))
        
        # DIDs branch with count
        did_count = len(self.config['dids'])
        did_root = self.nav_tree.insert(root, tk.END, text=f"🔧 DIDs ({did_count})", open=True)
        
        # Group DIDs by type
        did_types = {}
        for i, did in enumerate(self.config['dids']):
            dtype = did['data_type']
            if dtype not in did_types:
                did_types[dtype] = []
            did_types[dtype].append((i, did))
        
        for dtype, dids in sorted(did_types.items()):
            type_node = self.nav_tree.insert(did_root, tk.END, text=f"  📋 {dtype} ({len(dids)})", open=True)
            for i, did in dids:
                self.nav_tree.insert(type_node, tk.END, 
                    text=f"    {did['did']} - {did['did_name']}", 
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
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_path_var.get() if self.output_path_var.get() else "."
        )
        if directory:
            # Convert to relative path if possible
            try:
                rel_path = os.path.relpath(directory, os.path.dirname(self.config_file))
                self.output_path_var.set(rel_path)
            except ValueError:
                self.output_path_var.set(directory)
            self.modified = True
    
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
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        if tags and tags[0] == 'nvm':
            # Show NVM block details
            idx = int(tags[1])
            block = self.config['nvm_blocks'][idx]
            info = f"NVM Block Details\n"
            info += f"{'='*30}\n"
            info += f"Block ID: {block['block_id']}\n"
            info += f"Name: {block['block_name']}\n"
            info += f"Length: {block['data_length']} bytes\n"
            info += f"Default: {' '.join([f'{v:02X}' for v in block['default_value']])}\n"
            info += f"\nDescription:\n{block['description']}\n"
            self.info_text.insert(1.0, info)
            
            # Switch to NVM tab and select item
            self.notebook.select(0)
            self.select_nvm_item(idx)
            
        elif tags and tags[0] == 'did':
            # Show DID details
            idx = int(tags[1])
            did = self.config['dids'][idx]
            info = f"DID Details\n"
            info += f"{'='*30}\n"
            info += f"DID: {did['did']}\n"
            info += f"Name: {did['did_name']}\n"
            info += f"Type: {did['data_type']}\n"
            info += f"Length: {did['data_length']} bytes\n"
            info += f"Read: {'✓' if did['read_access'] else '✗'}\n"
            info += f"Write: {'✓' if did['write_access'] else '✗'}\n"
            info += f"Sessions: {', '.join(did['session_required'])}\n"
            info += f"Security: Level {did['security_level']}\n"
            if 'nvm_block_id' in did:
                info += f"NVM Block: {did['nvm_block_id']}\n"
            info += f"\nDescription:\n{did['description']}\n"
            self.info_text.insert(1.0, info)
            
            # Switch to DID tab and select item
            self.notebook.select(1)
            self.select_did_item(idx)
        
        self.info_text.config(state=tk.DISABLED)
    
    def select_nvm_item(self, index):
        """Select NVM item in tree by index"""
        children = self.nvm_tree.get_children()
        if index < len(children):
            self.nvm_tree.selection_set(children[index])
            self.nvm_tree.focus(children[index])
            self.nvm_tree.see(children[index])
    
    def select_did_item(self, index):
        """Select DID item in tree by index"""
        children = self.did_tree.get_children()
        if index < len(children):
            self.did_tree.selection_set(children[index])
            self.did_tree.focus(children[index])
            self.did_tree.see(children[index])
    
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
        self.modified = True
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
            
            self.modified = False
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
            self.modified = True
    
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
                self.modified = True
    
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
            self.modified = True
    
    def add_did(self):
        """Add new DID"""
        dialog = DidDialog(self.root, None, self.config['nvm_blocks'])
        if dialog.result:
            # Check for duplicate DID
            for did in self.config['dids']:
                if did['did'] == dialog.result['did']:
                    messagebox.showerror("Error", "DID already exists!")
                    return
            
            self.config['dids'].append(dialog.result)
            self.refresh_ui()
            self.modified = True
    
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
            dialog = DidDialog(self.root, did, self.config['nvm_blocks'])
            if dialog.result:
                did.update(dialog.result)
                self.refresh_ui()
                self.modified = True
    
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
            self.modified = True
    
    def generate_code(self):
        """Generate code from configuration"""
        try:
            # Save first
            self.save_config()
            
            # Generate
            generator = CodeGenerator(self.config_file)
            generator.generate_all()
            
            messagebox.showinfo("Success", "Code generated successfully!")
            self.status_var.set("Code generation complete")
        except Exception as e:
            messagebox.showerror("Error", f"Code generation failed: {e}")
    
    def validate_config(self):
        """Validate configuration"""
        try:
            # Basic validation
            errors = []
            
            if not self.config['project']['name']:
                errors.append("Project name is empty")
            
            if not self.config['nvm_blocks']:
                errors.append("No NVM blocks defined")
            
            if not self.config['dids']:
                errors.append("No DIDs defined")
            
            # Check for duplicate IDs
            block_ids = [b['block_id'] for b in self.config['nvm_blocks']]
            if len(block_ids) != len(set(block_ids)):
                errors.append("Duplicate NVM block IDs found")
            
            did_values = [d['did'] for d in self.config['dids']]
            if len(did_values) != len(set(did_values)):
                errors.append("Duplicate DIDs found")
            
            if errors:
                messagebox.showwarning("Validation Errors", "\n".join(errors))
            else:
                messagebox.showinfo("Validation", "Configuration is valid!")
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
        ttk.Label(form_frame, text="Data Length:").grid(row=2, column=0, sticky=tk.W, pady=5)
        data_length_var = tk.IntVar(value=block_data['data_length'] if block_data else 4)
        ttk.Entry(form_frame, textvariable=data_length_var, width=20).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Default Value
        ttk.Label(form_frame, text="Default Value (hex):").grid(row=3, column=0, sticky=tk.W, pady=5)
        default_str = ' '.join([f"{v:02X}" for v in block_data['default_value']]) if block_data else "00 00 00 00"
        default_var = tk.StringVar(value=default_str)
        ttk.Entry(form_frame, textvariable=default_var, width=40).grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text="(space-separated hex values)", font=('', 8)).grid(row=4, column=1, sticky=tk.W)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=5, column=0, sticky=tk.W, pady=5)
        description_var = tk.StringVar(value=block_data['description'] if block_data else "")
        ttk.Entry(form_frame, textvariable=description_var, width=40).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        
        def on_ok():
            try:
                # Parse default value
                default_values = [int(x, 16) for x in default_var.get().split()]
                
                self.result = {
                    "block_id": block_id_var.get(),
                    "block_name": block_name_var.get().upper(),
                    "data_length": data_length_var.get(),
                    "default_value": default_values,
                    "description": description_var.get()
                }
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid hex values in default data")
        
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()


class DidDialog:
    """Dialog for adding/editing DID"""
    def __init__(self, parent, did_data, nvm_blocks):
        self.result = None
        self.nvm_blocks = nvm_blocks
        
        dialog = tk.Toplevel(parent)
        dialog.title("DID Editor")
        dialog.geometry("600x550")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Form
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        
        # DID
        ttk.Label(form_frame, text="DID:").grid(row=row, column=0, sticky=tk.W, pady=5)
        did_var = tk.StringVar(value=did_data['did'] if did_data else "0xF190")
        ttk.Entry(form_frame, textvariable=did_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # DID Name
        ttk.Label(form_frame, text="DID Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        did_name_var = tk.StringVar(value=did_data['did_name'] if did_data else "")
        ttk.Entry(form_frame, textvariable=did_name_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        description_var = tk.StringVar(value=did_data['description'] if did_data else "")
        ttk.Entry(form_frame, textvariable=description_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Data Type
        ttk.Label(form_frame, text="Data Type:").grid(row=row, column=0, sticky=tk.W, pady=5)
        data_type_var = tk.StringVar(value=did_data['data_type'] if did_data else "NVM")
        type_combo = ttk.Combobox(form_frame, textvariable=data_type_var, values=["STATIC", "NVM", "DYNAMIC"], width=15, state="readonly")
        type_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # NVM Block ID
        ttk.Label(form_frame, text="NVM Block:").grid(row=row, column=0, sticky=tk.W, pady=5)
        nvm_block_var = tk.IntVar(value=did_data.get('nvm_block_id', 0) if did_data else 0)
        block_names = [f"{b['block_id']}: {b['block_name']}" for b in nvm_blocks]
        nvm_combo = ttk.Combobox(form_frame, values=block_names, width=37, state="readonly")
        if did_data and 'nvm_block_id' in did_data:
            nvm_combo.current(did_data['nvm_block_id'])
        nvm_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Data Length
        ttk.Label(form_frame, text="Data Length:").grid(row=row, column=0, sticky=tk.W, pady=5)
        data_length_var = tk.IntVar(value=did_data['data_length'] if did_data else 4)
        ttk.Entry(form_frame, textvariable=data_length_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Access
        ttk.Label(form_frame, text="Access:").grid(row=row, column=0, sticky=tk.W, pady=5)
        access_frame = ttk.Frame(form_frame)
        access_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        read_var = tk.BooleanVar(value=did_data['read_access'] if did_data else True)
        write_var = tk.BooleanVar(value=did_data['write_access'] if did_data else False)
        ttk.Checkbutton(access_frame, text="Read (0x22)", variable=read_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(access_frame, text="Write (0x2E)", variable=write_var).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Session Required
        ttk.Label(form_frame, text="Session Required:").grid(row=row, column=0, sticky=tk.W, pady=5)
        session_frame = ttk.Frame(form_frame)
        session_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        default_sess_var = tk.BooleanVar(value="DEFAULT" in did_data.get('session_required', []) if did_data else True)
        prog_sess_var = tk.BooleanVar(value="PROGRAMMING" in did_data.get('session_required', []) if did_data else False)
        ext_sess_var = tk.BooleanVar(value="EXTENDED_DIAGNOSTIC" in did_data.get('session_required', []) if did_data else False)
        ttk.Checkbutton(session_frame, text="Default", variable=default_sess_var).pack(anchor=tk.W)
        ttk.Checkbutton(session_frame, text="Programming", variable=prog_sess_var).pack(anchor=tk.W)
        ttk.Checkbutton(session_frame, text="Extended Diagnostic", variable=ext_sess_var).pack(anchor=tk.W)
        row += 1
        
        # Security Level
        ttk.Label(form_frame, text="Security Level:").grid(row=row, column=0, sticky=tk.W, pady=5)
        security_var = tk.IntVar(value=did_data.get('security_level', 0) if did_data else 0)
        ttk.Entry(form_frame, textvariable=security_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        
        def on_ok():
            try:
                # Build session list
                sessions = []
                if default_sess_var.get():
                    sessions.append("DEFAULT")
                if prog_sess_var.get():
                    sessions.append("PROGRAMMING")
                if ext_sess_var.get():
                    sessions.append("EXTENDED_DIAGNOSTIC")
                
                # Get NVM block ID from combo
                nvm_block_id = None
                if data_type_var.get() == "NVM" and nvm_combo.get():
                    nvm_block_id = int(nvm_combo.get().split(':')[0])
                
                self.result = {
                    "did": did_var.get(),
                    "did_name": did_name_var.get().upper(),
                    "description": description_var.get(),
                    "data_type": data_type_var.get(),
                    "data_length": data_length_var.get(),
                    "read_access": read_var.get(),
                    "write_access": write_var.get(),
                    "session_required": sessions,
                    "security_level": security_var.get()
                }
                
                if nvm_block_id is not None:
                    self.result['nvm_block_id'] = nvm_block_id
                
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")
        
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ConfigEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
