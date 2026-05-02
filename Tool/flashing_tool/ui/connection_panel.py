from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QComboBox, QPushButton, QLabel
from PySide6.QtCore import Signal
import serial.tools.list_ports

class ConnectionPanel(QGroupBox):
    connect_requested = Signal(str, int)

    def __init__(self):
        super().__init__("Connection")
        self.layout = QHBoxLayout(self)

        self.port_combo = QComboBox()
        self._refresh_ports()
        
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baud_combo.setCurrentText("115200")

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_ports)

        self.layout.addWidget(QLabel("Port:"))
        self.layout.addWidget(self.port_combo)
        self.layout.addWidget(self.refresh_btn)
        self.layout.addWidget(QLabel("Baudrate:"))
        self.layout.addWidget(self.baud_combo)
        self.layout.addWidget(self.connect_btn)

    def _refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.port_combo.addItem(p.device)

    def _on_connect_clicked(self):
        port = self.port_combo.currentText()
        baud = int(self.baud_combo.currentText())
        if port:
            self.connect_requested.emit(port, baud)

    def set_connected(self, connected: bool):
        if connected:
            self.connect_btn.setText("Disconnect")
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
            self.refresh_btn.setEnabled(False)
        else:
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
