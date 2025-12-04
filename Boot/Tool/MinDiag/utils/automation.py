"""Automation script runner for UDS commands."""
import time
import os
import subprocess


class AutomationRunner:
    """Runs automation scripts from text files."""
    
    def __init__(self, min_handler, log_callback, config_manager=None):
        """
        Initialize automation runner.
        
        Args:
            min_handler: MINHandler instance
            log_callback: Callback function for logging (log_tx, log_rx, log_info, log_error)
            config_manager: ConfigManager instance (for security unlock)
        """
        self.min_handler = min_handler
        self.log_tx = log_callback.get('log_tx')
        self.log_info = log_callback.get('log_info')
        self.log_error = log_callback.get('log_error')
        self.config_manager = config_manager
        self.pending_seed_level = None
        
        # Register callback for seed responses
        if min_handler:
            min_handler.register_callback(self._handle_seed_response)
    
    def format_hex(self, hex_str):
        """
        Format hex string with spaces.
        
        Args:
            hex_str: Hex string
            
        Returns:
            str: Formatted hex string
        """
        return ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
    
    def run_script(self, script_path, min_id=16):
        """
        Run automation script from file.
        
        Args:
            script_path: Path to script file
            min_id: MIN ID to use for sending
        """
        if not os.path.exists(script_path):
            self.log_error(f"Script file not found: {script_path}")
            return
        
        if not self.min_handler.is_connected():
            self.log_error("Not connected to device!")
            return
        
        try:
            with open(script_path, 'r') as f:
                lines = f.readlines()
            
            self.log_info(f"=== Starting Automation Script: {os.path.basename(script_path)} ===")
            
            for line_num, line in enumerate(lines, start=1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse command: DELAY <ms>, SECURITY_UNLOCK/SA <level>, or HEX data
                if line.upper().startswith('DELAY'):
                    try:
                        delay_ms = int(line.split()[1])
                        self.log_info(f"Script: Delay {delay_ms}ms")
                        time.sleep(delay_ms / 1000.0)
                    except Exception as e:
                        self.log_error(f"Script line {line_num}: Invalid DELAY command - {str(e)}")
                
                elif line.upper().startswith('SECURITY_UNLOCK') or line.upper().startswith('SA'):
                    # SECURITY_UNLOCK <level> or SA <level>
                    try:
                        parts = line.split()
                        if len(parts) < 2:
                            self.log_error(f"Script line {line_num}: SA/SECURITY_UNLOCK requires level parameter")
                            continue
                        
                        level = int(parts[1], 16) if parts[1].startswith('0x') else int(parts[1])
                        self._security_unlock(level, min_id)
                        
                        # Wait for unlock to complete (seed request + key send)
                        time.sleep(0.5)
                    except Exception as e:
                        self.log_error(f"Script line {line_num}: SA/SECURITY_UNLOCK error - {str(e)}")
                
                else:
                    # Treat as hex data
                    try:
                        hex_data = line.replace(" ", "")
                        data_bytes = bytes.fromhex(hex_data)
                        
                        # Save and restore MIN ID
                        old_min_id = self.min_handler.min_id
                        self.min_handler.min_id = min_id
                        
                        # Send data
                        self.min_handler.send(data_bytes)
                        self.log_tx(f"[{self.min_handler.get_elapsed_time()}]  [{hex(self.min_handler.min_id)[2:]}] <<< {self.format_hex(hex_data).upper()}")
                        
                        # Restore MIN ID
                        self.min_handler.min_id = old_min_id
                        
                        # Small delay between commands
                        time.sleep(0.1)
                    except ValueError as e:
                        self.log_error(f"Script line {line_num}: Invalid hex data - {str(e)}")
                    except Exception as e:
                        self.log_error(f"Script line {line_num}: Error - {str(e)}")
            
            self.log_info("=== Automation Script Completed ===")
            
        except Exception as e:
            self.log_error(f"Script execution error: {str(e)}")
    
    def _security_unlock(self, security_level, min_id):
        """
        Perform security unlock for specified level.
        
        Args:
            security_level: Security level (1, 2, etc.)
            min_id: MIN ID for communication
        """
        if not self.config_manager:
            self.log_error("Security unlock not available (no config manager)")
            return
        
        # Send request seed (27 + odd subfunction)
        subfunction = (security_level * 2) - 1  # 1->0x01, 2->0x03
        payload = bytes([0x27, subfunction])
        
        old_min_id = self.min_handler.min_id
        self.min_handler.min_id = min_id
        
        self.min_handler.send(payload)
        self.log_tx(
            f"[{self.min_handler.get_elapsed_time()}]  "
            f"[{hex(self.min_handler.min_id)[2:]}] <<< 27 {subfunction:02X} (SA Level {security_level})"
        )
        self.min_handler.min_id = old_min_id
        
        # Set pending level for response handler
        self.pending_seed_level = security_level
        self.pending_min_id = min_id
    
    def _handle_seed_response(self, min_id, payload):
        """
        Handle seed response and send key.
        
        Args:
            min_id: MIN ID
            payload: Response payload
        """
        if self.pending_seed_level is None:
            return
        
        # Check for positive response (0x67)
        if len(payload) >= 2 and payload[0] == 0x67:
            subfunction = payload[1]
            
            # Check if odd subfunction (seed response)
            if subfunction % 2 == 1:
                seed_bytes = payload[2:]
                seed_hex = seed_bytes.hex().upper()
                
                # Calculate key using SecurityUnlock.exe
                exe_path = self.config_manager.get("security_exe_path", "")
                if not exe_path or not os.path.exists(exe_path):
                    self.log_error("Security Access EXE not configured")
                    self.pending_seed_level = None
                    return
                
                try:
                    result = subprocess.run(
                        [exe_path, f"0x{self.pending_seed_level:02X}", seed_hex],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        key_hex = result.stdout.strip()
                        
                        # Send key (27 + even subfunction + key)
                        key_subfunction = self.pending_seed_level * 2
                        key_bytes = bytes.fromhex(key_hex)
                        key_payload = bytes([0x27, key_subfunction]) + key_bytes
                        
                        old_min_id = self.min_handler.min_id
                        self.min_handler.min_id = self.pending_min_id
                        
                        self.min_handler.send(key_payload)
                        self.log_tx(
                            f"[{self.min_handler.get_elapsed_time()}]  "
                            f"[{hex(self.min_handler.min_id)[2:]}] <<< 27 {key_subfunction:02X} {key_hex} (SA Key)"
                        )
                        self.min_handler.min_id = old_min_id
                    else:
                        self.log_error(f"Key calculation failed: {result.stderr}")
                
                except Exception as e:
                    self.log_error(f"Security unlock error: {str(e)}")
                
                finally:
                    self.pending_seed_level = None

