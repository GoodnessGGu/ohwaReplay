from pathlib import Path
from typing import Optional, List
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.data.mt5_connector import mt5_connector, MT5SyncWorker
from src.utils.logger import logger


class MT5Dialog(QDialog):
    """
    Dialog for configuring and managing local MetaTrader 5 / FOREX.com bridge connectivity.
    Supports asynchronous historical dataset synchronization with live progress tracking.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FOREX.com / MetaTrader 5 Bridge Configuration")
        self.resize(540, 560)
        self.sync_worker: Optional[MT5SyncWorker] = None
        self.init_ui()
        self._refresh_status()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Status banner
        self.lbl_status = QLabel("Status: Disconnected")
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; border-radius: 6px; background-color: #2a2e39; color: #ef5350;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

        # Connection Settings Group
        grp_conn = QGroupBox("TERMINAL CONNECTION (OPTIONAL CREDENTIALS)")
        form_conn = QFormLayout(grp_conn)
        form_conn.setSpacing(6)

        # Terminal Path
        path_box = QHBoxLayout()
        self.edit_path = QLineEdit()
        default_path = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
        if Path(default_path).exists():
            self.edit_path.setText(default_path)
        else:
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

        # Historical Sync Group
        self.grp_sync = QGroupBox("HISTORICAL BROKER DATA SYNCHRONIZATION")
        sync_layout = QVBoxLayout(self.grp_sync)
        sync_layout.setSpacing(6)

        scope_box = QHBoxLayout()
        lbl_scope = QLabel("Sync Scope:")
        lbl_scope.setStyleSheet("font-weight: 600; color: #848e9c;")
        self.combo_sync_scope = QComboBox()
        self.combo_sync_scope.addItems([
            "Current Active Pair (Fastest - ~2s)",
            "Top 4 Forex & Gold (XAUUSD, EURUSD, GBPUSD, USDJPY)",
            "Major Assets (Gold, Silver, Forex Majors & BTC)",
        ])
        scope_box.addWidget(lbl_scope)
        scope_box.addWidget(self.combo_sync_scope, 1)
        sync_layout.addLayout(scope_box)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e222d;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #ff9800;
                border-radius: 4px;
            }
        """)
        self.progress_bar.setVisible(False)
        sync_layout.addWidget(self.progress_bar)

        self.lbl_sync_status = QLabel("")
        self.lbl_sync_status.setStyleSheet("color: #ff9800; font-size: 11px; font-weight: 600;")
        self.lbl_sync_status.setVisible(False)
        sync_layout.addWidget(self.lbl_sync_status)

        layout.addWidget(self.grp_sync)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_connect = QPushButton("Connect to MT5")
        self.btn_connect.setStyleSheet("background-color: #2962ff; color: #ffffff; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.btn_connect.clicked.connect(self._on_connect_clicked)

        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.setStyleSheet("background-color: #ef5350; color: #ffffff; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.btn_disconnect.clicked.connect(self._on_disconnect_clicked)
        self.btn_disconnect.setEnabled(False)

        self.btn_sync = QPushButton("📥 Sync Historical Data to Replay")
        self.btn_sync.setStyleSheet("background-color: #1e222d; border: 1px solid #ff9800; color: #ff9800; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.btn_sync.clicked.connect(self._on_sync_clicked)
        self.btn_sync.setEnabled(False)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_connect)
        btn_layout.addWidget(self.btn_disconnect)
        btn_layout.addWidget(self.btn_sync)
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
            self.btn_sync.setEnabled(True)

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
            self.btn_sync.setEnabled(False)
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
        if self.sync_worker and self.sync_worker.isRunning():
            self.sync_worker.stop()
            self.sync_worker.wait(1000)

        mt5_connector.disconnect()
        self._refresh_status()
        QMessageBox.information(self, "MT5 Disconnected", "MetaTrader 5 Bridge disconnected.")

    def _on_sync_clicked(self) -> None:
        if not mt5_connector.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to MT5 first.")
            return

        # If already running, cancel
        if self.sync_worker and self.sync_worker.isRunning():
            self.sync_worker.stop()
            self.btn_sync.setText("Canceling...")
            self.btn_sync.setEnabled(False)
            return

        # Determine symbols to sync
        scope_idx = self.combo_sync_scope.currentIndex()
        active_sym = "XAUUSD"
        if hasattr(self.parent(), "replay_controller") and self.parent().replay_controller:
            active_sym = self.parent().replay_controller.state.symbol

        if scope_idx == 0:
            symbols = [active_sym]
        elif scope_idx == 1:
            symbols = list(dict.fromkeys([active_sym, "XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]))
        else:
            symbols = list(dict.fromkeys([active_sym, "XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD"]))

        timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"]

        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(symbols) * len(timeframes))
        self.progress_bar.setValue(0)
        self.lbl_sync_status.setVisible(True)
        self.lbl_sync_status.setText(f"Starting sync for {len(symbols)} asset(s)...")

        self.btn_sync.setText("⏹ Stop Sync")
        self.btn_sync.setStyleSheet("background-color: #3b1414; border: 1px solid #ef5350; color: #ef5350; font-weight: bold; padding: 8px 16px; border-radius: 4px;")

        self.sync_worker = MT5SyncWorker(symbols=symbols, timeframes=timeframes, count=5000, parent=self)
        self.sync_worker.progress.connect(self._on_sync_progress)
        self.sync_worker.finished_sync.connect(self._on_sync_finished)
        self.sync_worker.start()

    def _on_sync_progress(self, current: int, total: int, msg: str) -> None:
        self.progress_bar.setValue(current)
        self.lbl_sync_status.setText(f"{msg} ({current}/{total})")

    def _on_sync_finished(self, res: dict) -> None:
        self.btn_sync.setText("📥 Sync Historical Data to Replay")
        self.btn_sync.setStyleSheet("background-color: #1e222d; border: 1px solid #ff9800; color: #ff9800; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.btn_sync.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_sync_status.setVisible(False)

        # Notify parent MainWindow to reload active dataset from fresh CSVs
        if hasattr(self.parent(), "_data_cache"):
            self.parent()._data_cache.clear()
            sym = self.parent().replay_controller.state.symbol
            tf = self.parent().replay_controller.state.timeframe
            self.parent()._load_asset_data(symbol=sym, timeframe=tf, preserve_timestamp=None)
            self.parent().chart_manager.load_dataset(self.parent().replay_controller.get_visible_candles())
            self.parent()._update_all_views()

        if res:
            total_bars = sum(res.values())
            QMessageBox.information(
                self,
                "Historical Data Synced",
                f"Successfully synced {len(res)} timeframe datasets ({total_bars:,} total candles) directly from MT5 into your local Replay storage.\n\n"
                "Both Replay and Live modes now share 100% exact broker Spot prices.",
            )
        else:
            QMessageBox.warning(self, "Sync Incomplete", "No candles could be downloaded. Check Market Watch symbols in MT5.")

