from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QProgressBar, QLabel

class ProgressPanel(QGroupBox):
    def __init__(self):
        super().__init__("Progress")
        self.layout = QVBoxLayout(self)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.status_label = QLabel("Status: Idle")

        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.status_label)

    def reset(self):
        self.progress_bar.setValue(0)
        self.status_label.setText("Status: Idle")

    def set_progress(self, current: int, total: int):
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.status_label.setText(f"Status: Flashing {current}/{total} bytes ({percent}%)")
        
        if current == total:
            self.status_label.setText("Status: Finished")

    def set_status(self, text: str):
        self.status_label.setText(f"Status: {text}")
