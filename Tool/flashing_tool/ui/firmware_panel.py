from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QCheckBox
from PySide6.QtCore import Signal

class FirmwarePanel(QGroupBox):
    flash_requested = Signal(str, str)

    def __init__(self):
        super().__init__("Firmware")
        self.layout = QVBoxLayout(self)

        # Firmware selection row
        self.fw_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select firmware binary...")
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        self.fw_layout.addWidget(self.file_path_edit)
        self.fw_layout.addWidget(self.browse_btn)

        # Signature row
        self.sig_layout = QHBoxLayout()
        self.sign_checkbox = QCheckBox("Sign Firmware")
        self.sign_checkbox.stateChanged.connect(self._on_sign_toggled)
        self.key_path_edit = QLineEdit()
        self.key_path_edit.setPlaceholderText("Select private key (PEM)...")
        self.key_path_edit.setEnabled(False)
        self.key_browse_btn = QPushButton("Browse Key")
        self.key_browse_btn.setEnabled(False)
        self.key_browse_btn.clicked.connect(self._on_key_browse_clicked)
        self.sig_layout.addWidget(self.sign_checkbox)
        self.sig_layout.addWidget(self.key_path_edit)
        self.sig_layout.addWidget(self.key_browse_btn)

        # Flash button row
        self.btn_layout = QHBoxLayout()
        self.flash_btn = QPushButton("Flash")
        self.flash_btn.clicked.connect(self._on_flash_clicked)
        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.flash_btn)

        self.layout.addLayout(self.fw_layout)
        self.layout.addLayout(self.sig_layout)
        self.layout.addLayout(self.btn_layout)

    def _on_sign_toggled(self, state):
        is_checked = state != 0
        self.key_path_edit.setEnabled(is_checked)
        self.key_browse_btn.setEnabled(is_checked)

    def _on_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Firmware", "", "Firmware Files (*.bin *.hex);;Binary Files (*.bin);;Hex Files (*.hex);;All Files (*)")
        if file_path:
            self.file_path_edit.setText(file_path)

    def _on_key_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Private Key", "", "PEM Files (*.pem);;All Files (*)")
        if file_path:
            self.key_path_edit.setText(file_path)

    def _on_flash_clicked(self):
        file_path = self.file_path_edit.text()
        key_path = self.key_path_edit.text() if self.sign_checkbox.isChecked() else ""
        if file_path:
            self.flash_requested.emit(file_path, key_path)
