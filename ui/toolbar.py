from typing import Optional
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolBar,
    QWidget,
)

from src.utils.constants import TIMEFRAMES
from ui.theme_manager import ThemeManager


class MainToolBar(QToolBar):
    """
    Top application toolbar with symbol selection, timeframe switcher,
    live vs replay mode toggle, automated backtester, indicators, audio toggle, and theme switcher.
    """

    symbol_changed = pyqtSignal(str)
    timeframe_changed = pyqtSignal(str)
    settings_requested = pyqtSignal()
    indicators_requested = pyqtSignal()
    backtest_requested = pyqtSignal()
    layout_toggle_requested = pyqtSignal(str)
    mode_changed = pyqtSignal(str)  # "replay" or "live"
    audio_toggled = pyqtSignal(bool)
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)
        self.setMovable(False)
        self.is_live_mode = False
        self.audio_enabled = True
        self.init_ui()

    def init_ui(self) -> None:
        # Mode Switcher (Replay vs Live Market)
        self.btn_mode = QPushButton("🔁 Replay Mode")
        self.btn_mode.setCheckable(True)
        self.btn_mode.setStyleSheet("font-weight: bold; padding: 4px 10px; background-color: #2a2e39; color: #2962ff; border: 1px solid #2962ff; border-radius: 4px;")
        self.btn_mode.clicked.connect(self._on_mode_clicked)
        self.addWidget(self.btn_mode)

        self.addSeparator()

        # Symbol selector
        lbl_sym = QLabel(" Symbol: ")
        lbl_sym.setStyleSheet("font-weight: bold; color: #848e9c; font-size: 12px;")
        self.addWidget(lbl_sym)

        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD"])
        self.symbol_combo.setMinimumWidth(110)
        self.symbol_combo.setStyleSheet("font-weight: bold; padding: 3px 8px;")
        self.symbol_combo.currentTextChanged.connect(self.symbol_changed.emit)
        self.addWidget(self.symbol_combo)

        self.addSeparator()

        # Timeframe buttons
        lbl_tf = QLabel(" TF: ")
        lbl_tf.setStyleSheet("font-weight: bold; color: #848e9c; font-size: 12px;")
        self.addWidget(lbl_tf)

        self.tf_combo = QComboBox()
        self.tf_combo.addItems(TIMEFRAMES)
        self.tf_combo.setCurrentText("5m")
        self.tf_combo.setMinimumWidth(80)
        self.tf_combo.setStyleSheet("font-weight: bold; padding: 3px 6px;")
        self.tf_combo.currentTextChanged.connect(self.timeframe_changed.emit)
        self.addWidget(self.tf_combo)

        self.addSeparator()

        # Indicators Button
        self.btn_indicators = QPushButton("𝑓𝑥 Indicators")
        self.btn_indicators.setStyleSheet("font-weight: bold; padding: 4px 10px; background-color: #2a2e39; border: 1px solid #434651; border-radius: 4px;")
        self.btn_indicators.clicked.connect(self.indicators_requested.emit)
        self.addWidget(self.btn_indicators)

        # Strategy Backtester Button
        self.btn_backtest = QPushButton("🚀 Backtester")
        self.btn_backtest.setStyleSheet("font-weight: bold; padding: 4px 10px; background-color: #1e222d; border: 1px solid #ff9800; color: #ff9800; border-radius: 4px;")
        self.btn_backtest.clicked.connect(self.backtest_requested.emit)
        self.addWidget(self.btn_backtest)

        self.addSeparator()

        # Layout Toggle (Single vs Dual Split)
        self.btn_layout = QPushButton("⊞ 2 Charts (Dual View)")
        self.btn_layout.setCheckable(True)
        self.btn_layout.setStyleSheet("font-weight: bold; padding: 4px 10px;")
        self.btn_layout.clicked.connect(self._on_layout_clicked)
        self.addWidget(self.btn_layout)

        # Expanding spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        # Audio Toggle
        self.btn_audio = QPushButton("🔊 Sound: ON")
        self.btn_audio.setStyleSheet("font-weight: bold; padding: 4px 8px; font-size: 11px;")
        self.btn_audio.clicked.connect(self._on_audio_clicked)
        self.addWidget(self.btn_audio)

        self.addSeparator()

        # Far Right: Live Theme Switcher
        lbl_theme = QLabel("🎨 Theme: ")
        lbl_theme.setStyleSheet("font-weight: bold; color: #848e9c; font-size: 12px;")
        self.addWidget(lbl_theme)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(ThemeManager.get_theme_names())
        self.theme_combo.setCurrentText("Dark Charcoal")
        self.theme_combo.setStyleSheet("font-weight: bold; padding: 3px 8px;")
        self.theme_combo.currentTextChanged.connect(self.theme_changed.emit)
        self.addWidget(self.theme_combo)

        self.addSeparator()

        # Settings Button
        self.btn_settings = QPushButton("⚙ Settings")
        self.btn_settings.setStyleSheet("font-weight: bold; padding: 4px 12px;")
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        self.addWidget(self.btn_settings)

    def _on_mode_clicked(self, checked: bool) -> None:
        self.is_live_mode = checked
        if checked:
            self.btn_mode.setText("🔴 Live Market Mode")
            self.btn_mode.setStyleSheet("font-weight: bold; padding: 4px 10px; background-color: #3b1414; color: #ef5350; border: 1px solid #ef5350; border-radius: 4px;")
            self.mode_changed.emit("live")
        else:
            self.btn_mode.setText("🔁 Replay Mode")
            self.btn_mode.setStyleSheet("font-weight: bold; padding: 4px 10px; background-color: #2a2e39; color: #2962ff; border: 1px solid #2962ff; border-radius: 4px;")
            self.mode_changed.emit("replay")

    def _on_audio_clicked(self) -> None:
        self.audio_enabled = not self.audio_enabled
        self.btn_audio.setText("🔊 Sound: ON" if self.audio_enabled else "🔇 Sound: OFF")
        self.btn_audio.setStyleSheet("color: #d1d4dc;" if self.audio_enabled else "color: #ef5350;")
        self.audio_toggled.emit(self.audio_enabled)

    def set_active_theme(self, theme_name: str) -> None:
        idx = self.theme_combo.findText(theme_name)
        if idx >= 0:
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(idx)
            self.theme_combo.blockSignals(False)

    def _on_layout_clicked(self, checked: bool) -> None:
        mode = "dual" if checked else "single"
        self.btn_layout.setText("⊞ 1 Chart (Single View)" if checked else "⊞ 2 Charts (Dual View)")
        self.layout_toggle_requested.emit(mode)
