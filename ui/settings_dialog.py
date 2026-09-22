from typing import Any, Dict
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
)

from src.utils.constants import IntrabarExecutionMode
from ui.theme_manager import ThemeManager


class SettingsDialog(QDialog):
    """Configuration dialog for simulation realism and application preferences."""

    def __init__(self, current_settings: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Workstation & Realism Settings")
        self.setMinimumWidth(440)
        self.settings = current_settings.copy()
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 1. Appearance Group
        grp_appearance = QGroupBox("APPEARANCE & THEME")
        form_appearance = QFormLayout(grp_appearance)

        self.combo_theme = QComboBox()
        self.combo_theme.addItems(ThemeManager.get_theme_names())
        cur_theme = self.settings.get("theme", "OLED Black")
        idx = self.combo_theme.findText(cur_theme)
        if idx >= 0:
            self.combo_theme.setCurrentIndex(idx)
        form_appearance.addRow("Color Theme:", self.combo_theme)

        layout.addWidget(grp_appearance)

        # 2. Realism Group
        grp_realism = QGroupBox("TRADING REALISM SETTINGS")
        form_realism = QFormLayout(grp_realism)

        self.spin_balance = QDoubleSpinBox()
        self.spin_balance.setRange(100.0, 10000000.0)
        self.spin_balance.setValue(float(self.settings.get("balance", 10000.0)))
        form_realism.addRow("Initial Balance ($):", self.spin_balance)

        self.spin_leverage = QSpinBox()
        self.spin_leverage.setRange(1, 1000)
        self.spin_leverage.setValue(int(self.settings.get("leverage", 100)))
        form_realism.addRow("Leverage (1:X):", self.spin_leverage)

        self.spin_comm = QDoubleSpinBox()
        self.spin_comm.setRange(0.0, 100.0)
        self.spin_comm.setValue(float(self.settings.get("commission", 7.0)))
        form_realism.addRow("Commission ($ / lot):", self.spin_comm)

        self.spin_spread = QDoubleSpinBox()
        self.spin_spread.setRange(0.0, 100.0)
        self.spin_spread.setDecimals(4)
        self.spin_spread.setValue(float(self.settings.get("spread", 0.20)))
        form_realism.addRow("Spread:", self.spin_spread)

        self.spin_slippage = QDoubleSpinBox()
        self.spin_slippage.setRange(0.0, 100.0)
        self.spin_slippage.setDecimals(4)
        self.spin_slippage.setValue(float(self.settings.get("slippage", 0.05)))
        form_realism.addRow("Slippage:", self.spin_slippage)

        self.combo_intrabar = QComboBox()
        self.combo_intrabar.addItems([
            IntrabarExecutionMode.CONSERVATIVE.value,
            IntrabarExecutionMode.SL_FIRST.value,
            IntrabarExecutionMode.TP_FIRST.value,
            IntrabarExecutionMode.OPTIMISTIC.value,
        ])
        current_mode = self.settings.get("intrabar_mode", IntrabarExecutionMode.CONSERVATIVE.value)
        self.combo_intrabar.setCurrentText(str(current_mode))
        form_realism.addRow("Intrabar SL/TP Ambiguity:", self.combo_intrabar)

        layout.addWidget(grp_realism)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> Dict[str, Any]:
        return {
            "theme": self.combo_theme.currentText(),
            "balance": self.spin_balance.value(),
            "leverage": self.spin_leverage.value(),
            "commission": self.spin_comm.value(),
            "spread": self.spin_spread.value(),
            "slippage": self.spin_slippage.value(),
            "intrabar_mode": self.combo_intrabar.currentText(),
        }

