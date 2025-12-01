"""Main window for MinTool application."""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import serial.tools.list_ports
import threading
import sys
import os

from .config_dialog import ConfigDialog
from .security_dialog import SecurityDialog
from utils import AutomationRunner


class MainWindow:
    """Main application window."""
    
    def __init__(self, root, min_handler, config_manager):
        """
        Initialize main window.
        
        Args:
            root: Tkinter root window
            min_handler: MINHandler instance
            config_manager: ConfigManager instance
        """
        self.root = root
        self.min_handler = min_handler
        self.config_manager = config_manager
        
        self.root.title("MinDiagnostic")
        self.root.geometry("700x600")  # Reduced height since tester frame removed
        self.root.resizable(False, False)
        
        # Tester present timer
        self.tester_present_timer = None
        
        # Build UI
        self._create_menubar()
        self._create_connection_frame()
        self._create_input_frame()
        self._create_log_frame()
        self._create_buttons()
        
        # Initialize
        self.refresh_ports()
    
    def _create_menubar(self):
        """Create menubar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Config menu
        config_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Config", menu=config_menu)
        config_menu.add_command(label="Settings", command=self._open_config_dialog)
        config_menu.add_separator()
        config_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Security Access (0x27)", command=self._show_security_dialog)
        tools_menu.add_command(label="Run Automation Script", command=self._run_automation)
    
    def _create_connection_frame(self):
        """Create connection control frame."""
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(pady=10, anchor='w')
        
        # Connect button
        self.connect_button = tk.Button(
            self.top_frame,
            text="Connect",
            command=self.toggle_connection,
            bg="lightgreen",
            width=15
        )
        self.connect_button.grid(row=0, column=0, padx=5)
        
        # Port dropdown
        tk.Label(self.top_frame, text="Select Port:").grid(row=0, column=1, padx=5)
        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(
            self.top_frame,
            textvariable=self.port_var,
            state="readonly",
            width=15
        )
        self.port_dropdown.grid(row=0, column=2, padx=5)
        
        # Baudrate dropdown
        tk.Label(self.top_frame, text="Baudrate:").grid(row=0, column=3, padx=5)
        self.baudrate_var = tk.StringVar()
        self.baudrate_dropdown = ttk.Combobox(
            self.top_frame,
            textvariable=self.baudrate_var,
            state="readonly",
            width=10
        )
        self.baudrate_dropdown['values'] = ['9600', '115200', '57600', '38400']
        self.baudrate_dropdown.grid(row=0, column=4, padx=5)
        self.baudrate_dropdown.current(1)  # Default to 115200
        
        # Refresh button
        self.refresh_button = tk.Button(
            self.top_frame,
            text="Refresh Ports",
            command=self.refresh_ports,
            bg="lightblue"
        )
        self.refresh_button.grid(row=0, column=5, padx=5)
    
    def _create_input_frame(self):
        """Create input frame for sending data."""
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(pady=10, anchor='w')
        
        # MIN ID entry
        tk.Label(self.input_frame, text="ID:").grid(row=0, column=0, padx=5)
        self.id_entry = tk.Entry(self.input_frame, width=10)
        self.id_entry.insert(0, str(self.config_manager.get("default_min_id", 16)))
        self.id_entry.grid(row=0, column=1, padx=5)
        
        # Data entry
        self.data_entry = tk.Entry(self.input_frame, width=50)
        self.data_entry.grid(row=0, column=2, padx=5)
        self.data_entry.bind('<Return>', lambda e: self.send_data())
        
        # Send button
        self.send_button = tk.Button(
            self.input_frame,
            text="Send",
            command=self.send_data,
            bg="lightblue",
            width=15
        )
        self.send_button.grid(row=0, column=3, padx=5)
        self.send_button.config(state='disabled')
    
    def _create_log_frame(self):
        """Create log frame."""
        self.log_text = scrolledtext.ScrolledText(
            self.root,
            width=80,
            height=26,
            state='disabled'
        )
        self.log_text.pack(pady=10)
    
    def _create_buttons(self):
        """Create control buttons."""
        self.clear_button = tk.Button(
            self.root,
            text="Clear Data",
            command=self.clear_data,
            bg="lightgray"
        )
        self.clear_button.pack(pady=5)
    
    def refresh_ports(self):
        """Refresh available serial ports."""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_dropdown['values'] = port_list
        if port_list:
            self.port_dropdown.current(0)
    
    def toggle_connection(self):
        """Toggle serial connection."""
        if self.min_handler.is_connected():
            self.disable_tester_present()
            self.min_handler.disconnect()
            self.log_info("Disconnected.")
            self.connect_button.config(text="Connect", bg="lightgreen")
            self.send_button.config(state='disabled')
        else:
            self.clear_data()
            self.min_handler.reset_timer()
            port = self.port_var.get()
            baudrate = self.baudrate_var.get()
            
            if port and baudrate:
                if self.min_handler.connect(port=port, baudrate=baudrate):
                    self.log_info(f"Connected to {port} at {baudrate} baudrate.")
                    self.connect_button.config(text="Disconnect", bg="lightcoral")
                    self.send_button.config(state='normal')
                    
                    # Auto-enable tester present if configured
                    if self.config_manager.get("enable_tester_present_on_connect", False):
                        suppress = self.config_manager.get("tester_present_suppress", False)
                        self.enable_tester_present(suppress)
                else:
                    self.log_error(f"Serial port {port} opening error!")
            else:
                self.log_error("Please select a port and baudrate!")
    
    def send_data(self):
        """Send data over MIN protocol."""
        if not self.min_handler.is_connected():
            self.log_error("Not connected to any port!")
            return
        
        hex_data = self.data_entry.get().replace(" ", "")
        id_data = self.id_entry.get().replace(" ", "")
        
        if not id_data:
            self.log_error("Please enter ID data!")
            return
        
        try:
            min_id = int(id_data, 16)
            if min_id > 0x3F:
                raise ValueError("Please enter ID below 0x40!")
            self.min_handler.min_id = min_id
        except ValueError as e:
            self.log_error(str(e))
            return
        
        if not hex_data:
            self.log_error("Please enter hex data!")
            return
        
        try:
            data_bytes = bytes.fromhex(hex_data)
            self.min_handler.send(data_bytes)
            self.log_tx(
                f"[{self.min_handler.get_elapsed_time()}]  "
                f"[{hex(self.min_handler.min_id)[2:]}] <<< {self.format_hex(hex_data)}".upper()
            )
        except ValueError:
            self.log_error("Invalid hex data!")
    
    def enable_tester_present(self, suppress=False):
        """Enable tester present (called from auto-enable on connect)."""
        if self.min_handler.is_connected():
            self.min_handler.tester_present_enabled = True
            self.min_handler.tester_present_suppress = suppress
            self.send_tester_present()
            mode = "3E 80" if suppress else "3E 00"
            self.log_info(f"Tester Present enabled ({mode})")
        
    def disable_tester_present(self):
        """Disable tester present."""
        self.min_handler.tester_present_enabled = False
        if self.tester_present_timer:
            self.root.after_cancel(self.tester_present_timer)
            self.tester_present_timer = None
        self.log_info("Tester Present disabled")
    
    def send_tester_present(self):
        """Send tester present message."""
        if self.min_handler.is_connected() and self.min_handler.tester_present_enabled:
            if self.min_handler.tester_present_suppress:
                payload = bytes([0x3E, 0x80])
                hex_str = "3E 80"
            else:
                payload = bytes([0x3E, 0x00])
                hex_str = "3E 00"
            
            old_min_id = self.min_handler.min_id
            self.min_handler.min_id = 16
            self.min_handler.send(payload)
            self.log_tx(
                f"[{self.min_handler.get_elapsed_time()}]  "
                f"[{hex(self.min_handler.min_id)[2:]}] <<< {hex_str}"
            )
            self.min_handler.min_id = old_min_id
            
            # Get interval from config
            interval = self.config_manager.get("tester_present_interval_ms", 3000)
            self.tester_present_timer = self.root.after(interval, self.send_tester_present)
        else:
            self.disable_tester_present()
    
    def format_hex(self, hex_str):
        """Format hex string with spaces."""
        return ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
    
    def log_tx(self, message):
        """Log transmitted message."""
        self._log(message, "orange")
    
    def log_rx(self, message):
        """Log received message."""
        self._log(message, "blue")
    
    def log_info(self, message):
        """Log info message."""
        self._log(message, "green")
    
    def log_error(self, message):
        """Log error message."""
        self._log(message, "red")
    
    def _log(self, message, color):
        """Log message with color."""
        self.log_text.config(state='normal')
        self.log_text.tag_configure(color, foreground=color, font=("Helvetica", 13))
        self.log_text.insert(tk.END, message + "\n", color)
        self.log_text.config(state='disabled')
        self.log_text.yview(tk.END)
    
    def clear_data(self):
        """Clear log window."""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def _open_config_dialog(self):
        """Open configuration dialog."""
        dialog = ConfigDialog(self.root, self.config_manager)
        dialog.show()
    
    def _show_security_dialog(self):
        """Show security access dialog."""
        log_callbacks = {
            'log_tx': self.log_tx,
            'log_info': self.log_info,
            'log_error': self.log_error
        }
        dialog = SecurityDialog(
            self.root,
            self.config_manager,
            self.min_handler,
            log_callbacks,
            self.id_entry
        )
        dialog.show()
    
    def _run_automation(self):
        """Run automation script."""
        script_path = self.config_manager.get("automation_script_path", "")
        
        if not script_path:
            result = messagebox.askyesno(
                "No Script Configured",
                "Automation script is not configured.\nDo you want to select it now?"
            )
            if result:
                script_path = filedialog.askopenfilename(
                    title="Select Automation Script",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
                )
                if script_path:
                    self.config_manager.set("automation_script_path", script_path)
                    self.config_manager.save_config()
                else:
                    return
            else:
                return
        
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"Script file not found:\n{script_path}")
            return
        
        if not self.min_handler.is_connected():
            messagebox.showerror("Error", "Please connect to device first!")
            return
        
        # Run in separate thread
        def execute():
            log_callbacks = {
                'log_tx': self.log_tx,
                'log_info': self.log_info,
                'log_error': self.log_error
            }
            runner = AutomationRunner(self.min_handler, log_callbacks, self.config_manager)
            
            try:
                min_id = int(self.id_entry.get(), 16) if self.id_entry.get() else 16
            except:
                min_id = 16
            
            runner.run_script(script_path, min_id)
        
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
    
    def on_closing(self):
        """Handle window closing."""
        if self.tester_present_timer:
            self.root.after_cancel(self.tester_present_timer)
        if self.min_handler.is_connected():
            self.min_handler.disconnect()
        self.root.destroy()
        sys.exit()
