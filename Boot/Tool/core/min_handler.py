"""MIN protocol handler for UDS communication."""
import time
from min import MINTransportSerial, MINConnectionError


class MINHandler:
    """Handles MIN protocol communication."""
    
    def __init__(self, config_manager):
        """
        Initialize MIN handler.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config_manager = config_manager
        self.min_handle = None
        self.connect_state = False
        self.min_id = config_manager.get("default_min_id", 16)
        self._start_time = time.perf_counter()
        self._elapsed_time = 0
        self.tester_present_enabled = False
        self.tester_present_suppress = False
        self._response_callbacks = []  # List of callback functions
    
    def is_connected(self):
        """
        Check if connected to serial port.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connect_state
    
    def connect(self, port, baudrate):
        """
        Connect to serial port.
        
        Args:
            port: Serial port name
            baudrate: Baudrate
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.min_handle = MINTransportSerial(port=port, baudrate=int(baudrate))
            self.connect_state = True
            return True
        except MINConnectionError as e:
            print(f"Connection error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port."""
        if self.min_handle:
            try:
                self.min_handle.close()
                self.min_handle.portStatus = False
            except:
                pass
        self.connect_state = False
    
    def send(self, payload):
        """
        Send MIN frame.
        
        Args:
            payload: Bytes to send
        """
        if self.min_handle and self.connect_state:
            self.min_handle.send_frame(min_id=self.min_id, payload=payload)
    
    def poll(self):
        """
        Poll for received frames.
        
        Returns:
            list: List of received frames
        """
        if self.min_handle and self.connect_state:
            frames = self.min_handle.poll()
            # Notify callbacks
            for frame in frames:
                self._notify_callbacks(frame.min_id, frame.payload)
            return frames
        return []
    
    def register_callback(self, callback):
        """
        Register callback for received frames.
        
        Args:
            callback: Function(min_id, payload) to call on frame received
        """
        if callback not in self._response_callbacks:
            self._response_callbacks.append(callback)
    
    def unregister_callback(self, callback):
        """
        Unregister callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._response_callbacks:
            self._response_callbacks.remove(callback)
    
    def _notify_callbacks(self, min_id, payload):
        """
        Notify all registered callbacks.
        
        Args:
            min_id: MIN ID
            payload: Frame payload
        """
        for callback in self._response_callbacks[:]:  # Copy list to avoid modification during iteration
            try:
                callback(min_id, payload)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def reset_timer(self):
        """Reset elapsed time timer."""
        self._start_time = time.perf_counter()
    
    def get_elapsed_time(self):
        """
        Get elapsed time since last reset.
        
        Returns:
            str: Formatted elapsed time
        """
        current_time = time.perf_counter()
        self._elapsed_time = current_time - self._start_time
        return f"{self._elapsed_time:.4f}"
