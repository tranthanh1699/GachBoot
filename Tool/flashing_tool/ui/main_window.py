from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from .connection_panel import ConnectionPanel
from .firmware_panel import FirmwarePanel
from .progress_panel import ProgressPanel
from .log_panel import LogPanel
from services.flash_service import FlashService
from protocol.protocol_client import ProtocolClient
from transport.serial_transport import SerialTransport
from firmware.firmware_image import FirmwareImage
from firmware.signer import FirmwareSigner
import threading

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GachBoot Flashing Tool")
        self.setMinimumSize(800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Panels
        self.conn_panel = ConnectionPanel()
        self.fw_panel = FirmwarePanel()
        self.progress_panel = ProgressPanel()
        self.log_panel = LogPanel()

        self.layout.addWidget(self.conn_panel)
        self.layout.addWidget(self.fw_panel)
        self.layout.addWidget(self.progress_panel)
        self.layout.addWidget(self.log_panel)

        # Wiring
        self.conn_panel.connect_requested.connect(self._on_connect)
        self.fw_panel.flash_requested.connect(self._on_flash)
        
        self.transport = None
        self.service = None

    def _on_connect(self, port, baudrate):
        try:
            if self.transport and self.transport.is_open():
                self.transport.close()
                self.conn_panel.set_connected(False)
                self.log_panel.log("Disconnected.")
                return

            self.transport = SerialTransport(port, baudrate)
            self.transport.open()
            self.client = ProtocolClient(self.transport)
            self.service = FlashService(self.client)
            
            # Try HELLO
            info = self.service.hello()
            self.conn_panel.set_connected(True)
            self.log_panel.log(f"Connected to Bootloader v{info.major}.{info.minor}.{info.patch}")
            self.log_panel.log(f"App Start: 0x{info.app_start:08X}, Max Payload: {info.max_payload}")
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))
            if self.transport:
                self.transport.close()
            self.conn_panel.set_connected(False)

    def _on_flash(self, file_path, key_path):
        if not self.service:
            QMessageBox.warning(self, "Flash Error", "Not connected to target.")
            return

        def flash_thread():
            try:
                signer = FirmwareSigner(key_path) if key_path else None
                fw = FirmwareImage.from_file(file_path, signer)
                self.log_panel.log(f"Starting flash: {file_path} ({fw.size} bytes)")
                
                def update_progress(current, total):
                    self.progress_panel.set_progress(current, total)
                
                self.service.flash_firmware(fw, progress_callback=update_progress)
                self.log_panel.log("Flashing successful!")
                
            except Exception as e:
                self.log_panel.log(f"Flashing failed: {str(e)}")
                # QMessageBox.critical is not thread-safe, 
                # but we'll handle UI updates via signals in a real implementation.
                # For this prototype, we just log.
        
        threading.Thread(target=flash_thread, daemon=True).start()
