from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import Signal

class FirmwarePanel(QGroupBox):
    flash_requested = Signal(str)

    def __init__(self):
        super().__init__("Firmware")
        self.layout = QVBoxLayout(self)

        # Firmware selection row
        self.fw_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select signed firmware package (.bin)...")
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        self.fw_layout.addWidget(self.file_path_edit)
        self.fw_layout.addWidget(self.browse_btn)

        # Flash button row
        self.btn_layout = QHBoxLayout()
        self.flash_btn = QPushButton("Flash")
        self.flash_btn.clicked.connect(self._on_flash_clicked)
        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.flash_btn)

        self.layout.addLayout(self.fw_layout)
        self.layout.addLayout(self.btn_layout)

    def _on_browse_clicked(self):
        file_filter = (
            "Signed Firmware Package (*.bin);;"
            "All Files (*)"
        )
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Firmware", "", file_filter)
        if file_path:
            self.file_path_edit.setText(file_path)

    def _on_flash_clicked(self):
        file_path = self.file_path_edit.text()
        if file_path:
            self.flash_requested.emit(file_path)
