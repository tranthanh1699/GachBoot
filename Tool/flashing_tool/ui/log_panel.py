from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt
import datetime

class LogPanel(QGroupBox):
    def __init__(self):
        super().__init__("Logs")
        self.layout = QVBoxLayout(self)

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        
        self.layout.addWidget(self.log_edit)

    def log(self, message: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_edit.append(f"[{timestamp}] {message}")
        self.log_edit.verticalScrollBar().setValue(self.log_edit.verticalScrollBar().maximum())
