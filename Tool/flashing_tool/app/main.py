import sys
import os

# Add parent directory to sys.path to allow imports from sibling packages
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # If a file is passed as an argument, pre-fill the firmware path
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            window.fw_panel.file_path_edit.setText(os.path.abspath(file_path))
            
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
