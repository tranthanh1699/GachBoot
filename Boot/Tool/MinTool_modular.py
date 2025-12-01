"""
MinTool - UDS Diagnostic Tool
Main entry point for the application.
"""
import tkinter as tk
import threading
import time

from config import ConfigManager
from core import MINHandler
from ui import MainWindow


def background_task(main_window, min_handler):
    """
    Background task for polling received frames.
    
    Args:
        main_window: MainWindow instance
        min_handler: MINHandler instance
    """
    while True:
        if min_handler.is_connected():
            frames = min_handler.poll()
            if frames:
                for frame in frames:
                    hexdata = frame.payload.hex()
                    formatted_hex = main_window.format_hex(hexdata).upper()
                    main_window.log_rx(
                        f"[{min_handler.get_elapsed_time()}]  "
                        f"[{hex(frame.min_id)[2:]}] >>> {formatted_hex}"
                    )
        time.sleep(0.1)


def main():
    """Main application entry point."""
    # Initialize core components
    config_manager = ConfigManager()
    min_handler = MINHandler(config_manager)
    
    # Initialize UI
    root = tk.Tk()
    main_window = MainWindow(root, min_handler, config_manager)
    
    # Start background polling thread
    background_thread = threading.Thread(
        target=background_task,
        args=(main_window, min_handler),
        daemon=True
    )
    background_thread.start()
    
    # Set up window close protocol
    root.protocol("WM_DELETE_WINDOW", main_window.on_closing)
    
    # Start main loop
    root.mainloop()


if __name__ == "__main__":
    main()
