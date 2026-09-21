from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.data.mt5_connector import mt5_connector
from src.utils.logger import logger


class MT5Dialog(QDialog):
    """
    Dialog for configuring and managing local MetaTrader 5 / FOREX.com bridge connectivity.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FOREX.com / MetaTrader 5 Bridge Configuration")
        self.resize(520, 480)
        self.init_ui()
        self._refresh_status()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Status banner
        self.lbl_status = QLabel("Status: Disconnected")
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; border-radius: 6px; background-color: #2a2e39; color: #ef5350;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

        # Connection Settings Group
        grp_conn = QGroupBox("TERMINAL CONNECTION (OPTIONAL CREDENTIALS)")
        form_conn = QFormLayout(grp_conn)
        form_conn.setSpacing(8)

        # Terminal Path
        path_box = QHBoxLayout()
        self.edit_path = QLineEdit()
        self.edit_path.setPlaceholderText("Auto-detect running terminal (or select terminal64.exe)")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_terminal)
        path_box.addWidget(self.edit_path)
        path_box.addWidget(btn_browse)
        form_conn.addRow("MT5 Terminal Path:", path_box)

        self.edit_login = QLineEdit()
        self.edit_login.setPlaceholderText("Account number (optional if terminal logged in)")
        form_conn.addRow("Account Login:", self.edit_login)

        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_password.setPlaceholderText("Account password (optional)")
        form_conn.addRow("Password:", self.edit_password)

        self.edit_server = QLineEdit()
        self.edit_server.setPlaceholderText("e.g., Forex.com-Live / Forex.com-Demo")
        form_conn.addRow("Server:", self.edit_server)

        layout.addWidget(grp_conn)

        # Account Details Group
        self.grp_info = QGroupBox("CONNECTED BROKER & ACCOUNT DETAILS")
        self.form_info = QFormLayout(self.grp_info)
        self.lbl_broker = QLabel("--")
        self.lbl_account = QLabel("--")
        self.lbl_balance = QLabel("--")
        self.lbl_server = QLabel("--")
        self.lbl_ping = QLabel("--")

        self.form_info.addRow("Broker Company:", self.lbl_broker)
        self.form_info.addRow("Account Number:", self.lbl_account)
        self.form_info.addRow("Balance / Currency:", self.lbl_balance)
        self.form_info.addRow("Trade Server:", self.lbl_server)
        self.form_info.addRow("Terminal Ping:", self.lbl_ping)
        layout.addWidget(self.grp_info)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_connect = QPushButton("Connect to MT5")
        self.btn_connect.setStyleSheet("background-color: #2962ff; color: #ffffff; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.btn_connect.clicked.connect(self._on_connect_clicked)

        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.setStyleSheet("background-color: #ef5350; color: #ffffff; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.btn_disconnect.clicked.connect(self._on_disconnect_clicked)
        self.btn_disconnect.setEnabled(False)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_connect)
        btn_layout.addWidget(self.btn_disconnect)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _browse_terminal(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select MetaTrader 5 terminal64.exe", "C:\\Program Files", "Executable (terminal64.exe *.exe)"
        )
        if file_path:
            self.edit_path.setText(file_path)

    def _refresh_status(self) -> None:
        if mt5_connector.is_connected:
            self.lbl_status.setText("● Connected to MetaTrader 5 Bridge")
            self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; border-radius: 6px; background-color: #1b3a2f; color: #26a69a;")
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)

            acc = mt5_connector.get_account_summary()
            if acc:
                self.lbl_broker.setText(str(acc.get("company", "--")))
                self.lbl_account.setText(str(acc.get("login", "--")))
                self.lbl_balance.setText(f"${acc.get('balance', 0.0):,.2f} {acc.get('currency', '')}")
                self.lbl_server.setText(str(acc.get("server", "--")))
                self.lbl_ping.setText(f"{acc.get('ping', 0)} ms")
        else:
            self.lbl_status.setText("○ MetaTrader 5 Bridge: Disconnected")
            self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; border-radius: 6px; background-color: #3a1e1e; color: #ef5350;")
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.lbl_broker.setText("--")
            self.lbl_account.setText("--")
            self.lbl_balance.setText("--")
            self.lbl_server.setText("--")
            self.lbl_ping.setText("--")

    def _on_connect_clicked(self) -> None:
        path = self.edit_path.text().strip() or None
        login = self.edit_login.text().strip() or None
        pw = self.edit_password.text().strip() or None
        server = self.edit_server.text().strip() or None

        self.btn_connect.setText("Connecting...")
        self.btn_connect.setEnabled(False)
        self.repaint()

        ok, msg = mt5_connector.connect(
            path=path,
            login=int(login) if login and login.isdigit() else None,
            password=pw,
            server=server,
            timeout=5000,
        )

        self.btn_connect.setText("Connect to MT5")
        self._refresh_status()

        if ok:
            QMessageBox.information(self, "MT5 Connected", msg)
        else:
            QMessageBox.warning(self, "MT5 Connection Failed", msg)

    def _on_disconnect_clicked(self) -> None:
        mt5_connector.disconnect()
        self._refresh_status()
        QMessageBox.information(self, "MT5 Disconnected", "MetaTrader 5 Bridge disconnected.")
