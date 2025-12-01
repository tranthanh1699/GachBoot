"""Security access dialog for Service 0x27."""
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import threading


class SecurityDialog:
    """Security access dialog window."""
    
    def __init__(self, parent, config_manager, min_handler, log_callbacks, id_entry):
        """
        Initialize security dialog.
        
        Args:
            parent: Parent window
            config_manager: ConfigManager instance
            min_handler: MINHandler instance
            log_callbacks: Dict with log_tx, log_info, log_error callbacks
            id_entry: Entry widget for MIN ID
        """
        self.parent = parent
        self.config_manager = config_manager
        self.min_handler = min_handler
        self.log_tx = log_callbacks['log_tx']
        self.log_info = log_callbacks['log_info']
        self.log_error = log_callbacks['log_error']
        self.id_entry = id_entry
        self.window = None
        self.pending_unlock_level = None  # Track which level is being unlocked
        
        # Register response handler
        self.min_handler.register_callback(self._handle_response)
    
    def show(self):
        """Show security access quick unlock dialog."""
        exe_path = self.config_manager.get("security_exe_path", "")
        
        if not exe_path:
            result = messagebox.askyesno(
                "No EXE Configured",
                "Security Access EXE is not configured.\nDo you want to select it now?"
            )
            if result:
                exe_path = filedialog.askopenfilename(
                    title="Select Security Access EXE",
                    filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
                )
                if exe_path:
                    self.config_manager.set("security_exe_path", exe_path)
                    self.config_manager.save_config()
                else:
                    return
            else:
                return
        
        if not os.path.exists(exe_path):
            messagebox.showerror("Error", f"EXE file not found:\n{exe_path}")
            return
        
        if not self.min_handler.is_connected():
            messagebox.showerror("Error", "Not connected to device!")
            return
        
        # Create dialog
        self.window = tk.Toplevel(self.parent)
        self.window.title("Security Access - Quick Unlock")
        self.window.geometry("350x250")
        
        tk.Label(
            self.window,
            text="Select Security Level to Unlock:",
            font=("Arial", 11, "bold")
        ).pack(pady=15)
        
        # Create buttons from config
        security_levels = self.config_manager.get("security_levels", [])
        
        if not security_levels:
            tk.Label(
                self.window,
                text="No security levels configured",
                fg="red"
            ).pack(pady=20)
            return
        
        for level_config in security_levels:
            level = level_config.get("level", 1)
            name = level_config.get("name", f"Level {level}")
            color = level_config.get("color", "lightgray")
            
            btn = tk.Button(
                self.window,
                text=f"Level 0x{level:02X} - {name}",
                command=lambda l=level: self._quick_unlock(l),
                bg=color,
                width=35,
                height=2
            )
            btn.pack(pady=5)
        
        tk.Label(
            self.window,
            text="Will auto: Request Seed → Calculate Key → Send Key",
            font=("Arial", 8),
            fg="gray"
        ).pack(pady=10)
    
    def _quick_unlock(self, security_level):
        """
        Quick unlock: Auto request seed, calculate key, send key.
        
        Args:
            security_level: Security level (0x01, 0x03, 0x05, etc.)
        """
        self.pending_unlock_level = security_level
        
        # Send request seed (27 + odd subfunction)
        subfunction = (security_level * 2) - 1  # 0x01->0x01, 0x03->0x05, 0x05->0x09
        payload = bytes([0x27, subfunction])
        
        old_min_id = self.min_handler.min_id
        try:
            min_id_str = self.id_entry.get()
            self.min_handler.min_id = int(min_id_str, 16) if min_id_str else 16
        except:
            self.min_handler.min_id = 16
        
        self.min_handler.send(payload)
        self.log_tx(
            f"[{self.min_handler.get_elapsed_time()}]  "
            f"[{hex(self.min_handler.min_id)[2:]}] <<< 27 {subfunction:02X} (Request Seed Level 0x{security_level:02X})"
        )
        self.min_handler.min_id = old_min_id
    
    def _handle_response(self, min_id, payload):
        """
        Handle MIN response - auto-process seed and send key.
        
        Args:
            min_id: MIN ID
            payload: Response payload bytes
        """
        # Check if we're waiting for a seed response
        if self.pending_unlock_level is None:
            return
        
        # Check if response is for Service 0x27 (positive response = 0x67)
        if len(payload) < 2:
            return
        
        if payload[0] == 0x67:  # Positive response to 0x27
            subfunction = payload[1]
            
            # Check if this is a seed response (odd subfunction)
            if subfunction % 2 == 1:
                # Extract seed (skip SID and subfunction)
                seed_bytes = payload[2:]
                seed_hex = seed_bytes.hex().upper()
                
                # Calculate key using EXE
                threading.Thread(
                    target=self._calculate_and_send_key,
                    args=(self.pending_unlock_level, seed_hex),
                    daemon=True
                ).start()
                
                self.pending_unlock_level = None
        
        elif payload[0] == 0x7F and len(payload) >= 3:  # Negative response
            if payload[1] == 0x27:  # For Service 0x27
                nrc = payload[2]
                nrc_names = {
                    0x11: "serviceNotSupported",
                    0x12: "subFunctionNotSupported",
                    0x13: "incorrectMessageLengthOrInvalidFormat",
                    0x22: "conditionsNotCorrect",
                    0x24: "requestSequenceError",
                    0x31: "requestOutOfRange",
                    0x35: "invalidKey",
                    0x36: "exceededNumberOfAttempts",
                    0x37: "requiredTimeDelayNotExpired",
                }
                nrc_desc = nrc_names.get(nrc, f"Unknown NRC 0x{nrc:02X}")
                self.log_error(f"Security Access failed: {nrc_desc}")
                
                if self.window:
                    messagebox.showerror(
                        "Security Access Failed",
                        f"ECU rejected request:\n{nrc_desc} (NRC 0x{nrc:02X})"
                    )
                
                self.pending_unlock_level = None
    
    def _calculate_and_send_key(self, security_level, seed_hex):
        """
        Calculate key and send it (runs in background thread).
        
        Args:
            security_level: Security level
            seed_hex: Seed as hex string
        """
        exe_path = self.config_manager.get("security_exe_path", "")
        
        try:
            # Run SecurityUnlock.exe with level and seed
            result = subprocess.run(
                [exe_path, f"0x{security_level:02X}", seed_hex],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                key_hex = result.stdout.strip()
                
                # Send key (27 + even subfunction + key)
                subfunction = security_level * 2  # 0x01->0x02, 0x03->0x06, 0x05->0x0A
                key_bytes = bytes.fromhex(key_hex)
                payload = bytes([0x27, subfunction]) + key_bytes
                
                old_min_id = self.min_handler.min_id
                try:
                    min_id_str = self.id_entry.get()
                    self.min_handler.min_id = int(min_id_str, 16) if min_id_str else 16
                except:
                    self.min_handler.min_id = 16
                
                self.min_handler.send(payload)
                self.log_tx(
                    f"[{self.min_handler.get_elapsed_time()}]  "
                    f"[{hex(self.min_handler.min_id)[2:]}] <<< 27 {subfunction:02X} {key_hex} (Send Key Level 0x{security_level:02X})"
                )
                self.min_handler.min_id = old_min_id
                
                # Close dialog on success
                if self.window:
                    self.window.after(100, self.window.destroy)
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.log_error(f"Key calculation failed: {error_msg}")
                self.parent.after(0, lambda: messagebox.showerror(
                    "Calculation Error",
                    f"Failed to calculate key:\n{error_msg}"
                ))
        
        except subprocess.TimeoutExpired:
            self.log_error("Key calculation timeout")
            self.parent.after(0, lambda: messagebox.showerror(
                "Timeout",
                "Key calculation took too long"
            ))
        except Exception as e:
            self.log_error(f"Key calculation error: {e}")
            self.parent.after(0, lambda: messagebox.showerror(
                "Error",
                f"Failed to calculate key:\n{str(e)}"
            ))
