from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class IndicatorPropertyDialog(QDialog):
    """Dialog for editing detailed parameters and styling of a specific indicator."""

    def __init__(self, ind_config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.ind_config = ind_config.copy()
        self.params = self.ind_config.get("params", {}).copy()
        name = self.ind_config.get("name", "Indicator")
        self.setWindowTitle(f"Indicator Settings - {name}")
        self.setMinimumWidth(360)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        name = self.ind_config.get("name", "")

        # Inputs Group
        grp_inputs = QGroupBox("Inputs & Parameters")
        form_inputs = QFormLayout(grp_inputs)

        if name in ["EMA", "SMA", "ATR"]:
            self.spin_period = QSpinBox()
            self.spin_period.setRange(1, 500)
            self.spin_period.setValue(int(self.params.get("period", 20 if name != "SMA" else 50)))
            form_inputs.addRow("Period (Length):", self.spin_period)

        elif name == "RSI":
            self.spin_period = QSpinBox()
            self.spin_period.setRange(1, 200)
            self.spin_period.setValue(int(self.params.get("period", 14)))
            form_inputs.addRow("RSI Period:", self.spin_period)

        elif name == "BollingerBands":
            self.spin_period = QSpinBox()
            self.spin_period.setRange(1, 200)
            self.spin_period.setValue(int(self.params.get("period", 20)))
            form_inputs.addRow("Basis Period:", self.spin_period)

            self.spin_std = QDoubleSpinBox()
            self.spin_std.setRange(0.1, 10.0)
            self.spin_std.setSingleStep(0.1)
            self.spin_std.setValue(float(self.params.get("std_dev", 2.0)))
            form_inputs.addRow("Std Dev Multiplier:", self.spin_std)

        elif name == "MACD":
            self.spin_fast = QSpinBox()
            self.spin_fast.setRange(1, 100)
            self.spin_fast.setValue(int(self.params.get("fast", 12)))
            form_inputs.addRow("Fast Length:", self.spin_fast)

            self.spin_slow = QSpinBox()
            self.spin_slow.setRange(1, 200)
            self.spin_slow.setValue(int(self.params.get("slow", 26)))
            form_inputs.addRow("Slow Length:", self.spin_slow)

            self.spin_sig = QSpinBox()
            self.spin_sig.setRange(1, 100)
            self.spin_sig.setValue(int(self.params.get("signal", 9)))
            form_inputs.addRow("Signal Length:", self.spin_sig)

        elif name == "SmartTrail":
            self.spin_len = QSpinBox()
            self.spin_len.setRange(1, 100)
            self.spin_len.setValue(int(self.params.get("length", 14)))
            form_inputs.addRow("Smart Trail Length:", self.spin_len)

            self.spin_mult = QDoubleSpinBox()
            self.spin_mult.setRange(0.1, 10.0)
            self.spin_mult.setSingleStep(0.1)
            self.spin_mult.setValue(float(self.params.get("multiplier", 2.0)))
            form_inputs.addRow("Smart Trail Multiplier:", self.spin_mult)

            self.spin_sens = QSpinBox()
            self.spin_sens.setRange(1, 5)
            self.spin_sens.setValue(int(self.params.get("sensitivity", 3)))
            form_inputs.addRow("Sensitivity (1-5):", self.spin_sens)

            self.combo_source = QComboBox()
            self.combo_source.addItems(["close", "open", "high", "low", "hl2", "hlc3"])
            self.combo_source.setCurrentText(str(self.params.get("source", "close")))
            form_inputs.addRow("Source:", self.combo_source)

        elif name == "FVG":
            self.spin_min_gap = QDoubleSpinBox()
            self.spin_min_gap.setRange(0.0, 100.0)
            self.spin_min_gap.setSingleStep(0.1)
            self.spin_min_gap.setValue(float(self.params.get("min_gap_points", 0.0)))
            form_inputs.addRow("Min Gap Points:", self.spin_min_gap)

            self.chk_show_mit = QCheckBox("Show Mitigated FVGs")
            self.chk_show_mit.setChecked(bool(self.params.get("show_mitigated", False)))
            form_inputs.addRow("", self.chk_show_mit)

        elif name == "MarketStructure":
            self.spin_swing_len = QSpinBox()
            self.spin_swing_len.setRange(2, 50)
            self.spin_swing_len.setValue(int(self.params.get("swing_length", 5)))
            form_inputs.addRow("Swing Pivot Length:", self.spin_swing_len)

            self.chk_show_bos = QCheckBox("Show BOS (Break of Structure)")
            self.chk_show_bos.setChecked(bool(self.params.get("show_bos", True)))
            form_inputs.addRow("", self.chk_show_bos)

            self.chk_show_choch = QCheckBox("Show CHoCH (Change of Character)")
            self.chk_show_choch.setChecked(bool(self.params.get("show_choch", True)))
            form_inputs.addRow("", self.chk_show_choch)

        layout.addWidget(grp_inputs)

        # Style Group
        grp_style = QGroupBox("Style & Colors")
        form_style = QFormLayout(grp_style)

        if name in ["EMA", "SMA", "RSI", "ATR"]:
            self.btn_color = QPushButton()
            self.cur_color = self.params.get("color", "#2196f3" if name != "RSI" else "#9c27b0")
            self._update_color_btn(self.btn_color, self.cur_color)
            self.btn_color.clicked.connect(lambda: self._choose_color("color", self.btn_color))
            form_style.addRow("Line Color:", self.btn_color)

            self.combo_width = QComboBox()
            self.combo_width.addItems(["1px", "1.5px", "2px", "3px", "4px"])
            cur_w = str(self.params.get("lineWidth", 2)) + "px"
            idx = self.combo_width.findText(cur_w)
            if idx >= 0:
                self.combo_width.setCurrentIndex(idx)
            form_style.addRow("Line Thickness:", self.combo_width)

            self.combo_style = QComboBox()
            self.combo_style.addItems(["solid", "dashed", "dotted"])
            self.combo_style.setCurrentText(self.params.get("lineStyle", "solid"))
            form_style.addRow("Line Style:", self.combo_style)

        elif name == "SmartTrail":
            self.btn_up_color = QPushButton()
            self.cur_up_color = self.params.get("color_up", "#00e676")
            self._update_color_btn(self.btn_up_color, self.cur_up_color)
            self.btn_up_color.clicked.connect(lambda: self._choose_color("color_up", self.btn_up_color))
            form_style.addRow("Bullish Trail Color:", self.btn_up_color)

            self.btn_down_color = QPushButton()
            self.cur_down_color = self.params.get("color_down", "#ff5252")
            self._update_color_btn(self.btn_down_color, self.cur_down_color)
            self.btn_down_color.clicked.connect(lambda: self._choose_color("color_down", self.btn_down_color))
            form_style.addRow("Bearish Trail Color:", self.btn_down_color)

            self.combo_width = QComboBox()
            self.combo_width.addItems(["1px", "1.5px", "2px", "3px", "4px"])
            cur_w = str(self.params.get("lineWidth", 2)) + "px"
            idx = self.combo_width.findText(cur_w)
            if idx >= 0:
                self.combo_width.setCurrentIndex(idx)
            form_style.addRow("Line Thickness:", self.combo_width)

            self.combo_style = QComboBox()
            self.combo_style.addItems(["solid", "dashed", "dotted"])
            self.combo_style.setCurrentText(self.params.get("lineStyle", "solid"))
            form_style.addRow("Line Style:", self.combo_style)

        elif name == "BollingerBands":
            self.btn_mid_color = QPushButton()
            self.cur_mid_color = self.params.get("color_middle", "#ff9800")
            self._update_color_btn(self.btn_mid_color, self.cur_mid_color)
            self.btn_mid_color.clicked.connect(lambda: self._choose_color("color_middle", self.btn_mid_color))
            form_style.addRow("Basis (Middle) Color:", self.btn_mid_color)

            self.btn_band_color = QPushButton()
            self.cur_band_color = self.params.get("color_bands", "#2962ff")
            self._update_color_btn(self.btn_band_color, self.cur_band_color)
            self.btn_band_color.clicked.connect(lambda: self._choose_color("color_bands", self.btn_band_color))
            form_style.addRow("Upper / Lower Bands Color:", self.btn_band_color)

        elif name == "MACD":
            self.btn_macd_color = QPushButton()
            self.cur_macd_color = self.params.get("color_macd", "#2962ff")
            self._update_color_btn(self.btn_macd_color, self.cur_macd_color)
            self.btn_macd_color.clicked.connect(lambda: self._choose_color("color_macd", self.btn_macd_color))
            form_style.addRow("MACD Line Color:", self.btn_macd_color)

            self.btn_sig_color = QPushButton()
            self.cur_sig_color = self.params.get("color_signal", "#ff9800")
            self._update_color_btn(self.btn_sig_color, self.cur_sig_color)
            self.btn_sig_color.clicked.connect(lambda: self._choose_color("color_signal", self.btn_sig_color))
            form_style.addRow("Signal Line Color:", self.btn_sig_color)

        elif name == "FVG":
            self.btn_bull_color = QPushButton()
            self.cur_bull_color = self.params.get("bullish_color", "#26a69a")
            self._update_color_btn(self.btn_bull_color, self.cur_bull_color)
            self.btn_bull_color.clicked.connect(lambda: self._choose_color("bullish_color", self.btn_bull_color))
            form_style.addRow("Bullish FVG Color:", self.btn_bull_color)

            self.btn_bear_color = QPushButton()
            self.cur_bear_color = self.params.get("bearish_color", "#ef5350")
            self._update_color_btn(self.btn_bear_color, self.cur_bear_color)
            self.btn_bear_color.clicked.connect(lambda: self._choose_color("bearish_color", self.btn_bear_color))
            form_style.addRow("Bearish FVG Color:", self.btn_bear_color)

        elif name == "MarketStructure":
            self.btn_bos_color = QPushButton()
            self.cur_bos_color = self.params.get("bos_color", "#2962ff")
            self._update_color_btn(self.btn_bos_color, self.cur_bos_color)
            self.btn_bos_color.clicked.connect(lambda: self._choose_color("bos_color", self.btn_bos_color))
            form_style.addRow("BOS Level Color:", self.btn_bos_color)

            self.btn_choch_color = QPushButton()
            self.cur_choch_color = self.params.get("choch_color", "#ff9800")
            self._update_color_btn(self.btn_choch_color, self.cur_choch_color)
            self.btn_choch_color.clicked.connect(lambda: self._choose_color("choch_color", self.btn_choch_color))
            form_style.addRow("CHoCH Level Color:", self.btn_choch_color)

        layout.addWidget(grp_style)

        # Buttons
        h_btn = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Save & Apply")
        btn_save.setStyleSheet("background-color: #2962ff; color: #ffffff; font-weight: bold; padding: 6px 14px;")
        btn_save.clicked.connect(self._save_and_accept)

        h_btn.addStretch()
        h_btn.addWidget(btn_cancel)
        h_btn.addWidget(btn_save)
        layout.addLayout(h_btn)

    def _update_color_btn(self, btn: QPushButton, color_hex: str) -> None:
        btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #ffffff; height: 24px; border-radius: 4px;")

    def _choose_color(self, key: str, btn: QPushButton) -> None:
        init_c = QColor(self.params.get(key, "#2962ff"))
        col = QColorDialog.getColor(init_c, self, f"Select Color")
        if col.isValid():
            hex_c = col.name()
            self.params[key] = hex_c
            self._update_color_btn(btn, hex_c)

    def _save_and_accept(self) -> None:
        name = self.ind_config.get("name", "")
        if name in ["EMA", "SMA", "ATR"]:
            self.params["period"] = self.spin_period.value()
            self.params["lineWidth"] = float(self.combo_width.currentText().replace("px", ""))
            self.params["lineStyle"] = self.combo_style.currentText()
            self.ind_config["display_name"] = f"{name} ({self.params['period']})"
        elif name == "RSI":
            self.params["period"] = self.spin_period.value()
            self.params["lineWidth"] = float(self.combo_width.currentText().replace("px", ""))
            self.ind_config["display_name"] = f"RSI ({self.params['period']})"
        elif name == "BollingerBands":
            self.params["period"] = self.spin_period.value()
            self.params["std_dev"] = self.spin_std.value()
            self.ind_config["display_name"] = f"BB ({self.params['period']}, {self.params['std_dev']})"
        elif name == "MACD":
            self.params["fast"] = self.spin_fast.value()
            self.params["slow"] = self.spin_slow.value()
            self.params["signal"] = self.spin_sig.value()
            self.ind_config["display_name"] = f"MACD ({self.params['fast']}, {self.params['slow']}, {self.params['signal']})"
        elif name == "SmartTrail":
            self.params["length"] = self.spin_len.value()
            self.params["multiplier"] = self.spin_mult.value()
            self.params["sensitivity"] = self.spin_sens.value()
            self.params["source"] = self.combo_source.currentText()
            self.params["lineWidth"] = float(self.combo_width.currentText().replace("px", ""))
            self.params["lineStyle"] = self.combo_style.currentText()
            self.ind_config["display_name"] = f"Smart Trail ({self.params['length']}, {self.params['multiplier']})"
        elif name == "FVG":
            self.params["min_gap_points"] = self.spin_min_gap.value()
            self.params["show_mitigated"] = self.chk_show_mit.isChecked()
            self.ind_config["display_name"] = f"SMC FVG ({self.params['min_gap_points']} pts)"
        elif name == "MarketStructure":
            self.params["swing_length"] = self.spin_swing_len.value()
            self.params["show_bos"] = self.chk_show_bos.isChecked()
            self.params["show_choch"] = self.chk_show_choch.isChecked()
            self.ind_config["display_name"] = f"Market Structure ({self.params['swing_length']})"

        self.ind_config["params"] = self.params
        self.accept()

    def get_updated_config(self) -> Dict[str, Any]:
        return self.ind_config


class IndicatorDialog(QDialog):
    """
    Comprehensive TradingView-style Indicators Manager Dialog.
    Allows toggling the Volume Histogram, adding/removing technical indicators,
    and editing fine parameters and styling.
    """

    applied = pyqtSignal(bool, list)  # (volume_visible, active_indicators)

    def __init__(self, volume_visible: bool, active_indicators: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Indicators & Strategies")
        self.setMinimumSize(540, 420)
        self.volume_visible = volume_visible
        self.active_indicators = [ind.copy() for ind in active_indicators]

        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # 1. Built-in Volume Section
        grp_volume = QGroupBox("Chart Volume")
        layout_vol = QHBoxLayout(grp_volume)

        self.chk_volume = QCheckBox("Show Volume Histogram")
        self.chk_volume.setChecked(self.volume_visible)
        self.chk_volume.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout_vol.addWidget(self.chk_volume)
        layout_vol.addStretch()

        main_layout.addWidget(grp_volume)

        # 2. Add New Indicator Header & Dropdown
        grp_add = QGroupBox("Add Technical Indicator")
        h_add = QHBoxLayout(grp_add)

        self.combo_ind_type = QComboBox()
        self.combo_ind_type.addItems([
            "Smart Trail Signals (14, 2.0, 3)",
            "Fair Value Gaps (SMC FVG)",
            "Market Structure (BOS / CHoCH)",
            "EMA - Exponential Moving Average (20)",
            "SMA - Simple Moving Average (50)",
            "Bollinger Bands (20, 2.0)",
            "RSI - Relative Strength Index (14)",
            "MACD - Moving Average Convergence Divergence",
            "ATR - Average True Range (14)",
        ])
        self.combo_ind_type.setStyleSheet("padding: 4px 8px; font-weight: bold;")
        h_add.addWidget(self.combo_ind_type, 1)

        btn_add = QPushButton("+ Add to Chart")
        btn_add.setStyleSheet("background-color: #2962ff; color: white; font-weight: bold; padding: 6px 12px;")
        btn_add.clicked.connect(self._add_selected_indicator)
        h_add.addWidget(btn_add)

        main_layout.addWidget(grp_add)

        # 3. Active Indicators Table
        grp_active = QGroupBox("Active Indicators on Chart")
        v_active = QVBoxLayout(grp_active)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Show", "Indicator", "Settings", "Remove"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("QTableWidget { background-color: #1e222d; color: #d1d4dc; }")

        v_active.addWidget(self.table)
        main_layout.addWidget(grp_active, 1)

        # 4. Dialog Action Buttons
        h_actions = QHBoxLayout()
        btn_close = QPushButton("Cancel")
        btn_close.clicked.connect(self.reject)

        btn_apply = QPushButton("Apply Changes")
        btn_apply.setStyleSheet("background-color: #26a69a; color: white; font-weight: bold; padding: 6px 16px;")
        btn_apply.clicked.connect(self._apply_and_close)

        h_actions.addStretch()
        h_actions.addWidget(btn_close)
        h_actions.addWidget(btn_apply)
        main_layout.addLayout(h_actions)

        self._refresh_table()

    def _refresh_table(self) -> None:
        self.table.setRowCount(len(self.active_indicators))
        for row, ind in enumerate(self.active_indicators):
            # Checkbox
            chk = QCheckBox()
            chk.setChecked(ind.get("visible", True))
            chk.stateChanged.connect(lambda state, r=row: self._on_visibility_changed(r, state))
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, chk_widget)

            # Name / Details
            disp_name = ind.get("display_name", ind.get("name", "Indicator"))
            item_name = QTableWidgetItem(disp_name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, item_name)

            # Settings Button
            btn_edit = QPushButton("⚙ Edit")
            btn_edit.setStyleSheet("padding: 2px 8px; font-size: 11px;")
            btn_edit.clicked.connect(lambda checked, r=row: self._edit_indicator(r))
            self.table.setCellWidget(row, 2, btn_edit)

            # Remove Button
            btn_del = QPushButton("🗑")
            btn_del.setStyleSheet("color: #ef5350; font-weight: bold; padding: 2px 6px;")
            btn_del.clicked.connect(lambda checked, r=row: self._remove_indicator(r))
            self.table.setCellWidget(row, 3, btn_del)

    def _on_visibility_changed(self, row: int, state: int) -> None:
        if row < len(self.active_indicators):
            self.active_indicators[row]["visible"] = (state == Qt.CheckState.Checked.value)

    def _edit_indicator(self, row: int) -> None:
        if row >= len(self.active_indicators):
            return
        ind = self.active_indicators[row]
        dlg = IndicatorPropertyDialog(ind, self)
        if dlg.exec():
            self.active_indicators[row] = dlg.get_updated_config()
            self._refresh_table()

    def _remove_indicator(self, row: int) -> None:
        if row < len(self.active_indicators):
            del self.active_indicators[row]
            self._refresh_table()

    def _add_selected_indicator(self) -> None:
        choice = self.combo_ind_type.currentText()
        import time
        uid = f"ind_{int(time.time() * 1000)}"

        if "Smart" in choice or "Trail" in choice:
            new_ind = {
                "id": uid,
                "name": "SmartTrail",
                "display_name": "Smart Trail (14, 2.0)",
                "visible": True,
                "params": {
                    "length": 14,
                    "multiplier": 2.0,
                    "sensitivity": 3,
                    "source": "close",
                    "color_up": "#00e676",
                    "color_down": "#ff5252",
                    "lineWidth": 2,
                    "lineStyle": "solid",
                }
            }
        elif "FVG" in choice or "Fair Value" in choice:
            new_ind = {
                "id": uid,
                "name": "FVG",
                "display_name": "SMC FVG (0.0 pts)",
                "visible": True,
                "params": {
                    "min_gap_points": 0.0,
                    "show_mitigated": False,
                    "bullish_color": "#26a69a",
                    "bearish_color": "#ef5350",
                }
            }
        elif "Structure" in choice or "BOS" in choice:
            new_ind = {
                "id": uid,
                "name": "MarketStructure",
                "display_name": "Market Structure (5)",
                "visible": True,
                "params": {
                    "swing_length": 5,
                    "show_bos": True,
                    "show_choch": True,
                    "bos_color": "#2962ff",
                    "choch_color": "#ff9800",
                }
            }
        elif "EMA" in choice:
            new_ind = {
                "id": uid,
                "name": "EMA",
                "display_name": "EMA (20)",
                "visible": True,
                "params": {"period": 20, "color": "#2196f3", "lineWidth": 2, "lineStyle": "solid"}
            }
        elif "SMA" in choice:
            new_ind = {
                "id": uid,
                "name": "SMA",
                "display_name": "SMA (50)",
                "visible": True,
                "params": {"period": 50, "color": "#ff9800", "lineWidth": 2, "lineStyle": "solid"}
            }
        elif "Bollinger" in choice:
            new_ind = {
                "id": uid,
                "name": "BollingerBands",
                "display_name": "BB (20, 2.0)",
                "visible": True,
                "params": {"period": 20, "std_dev": 2.0, "color_middle": "#ff9800", "color_bands": "#2962ff", "lineWidth": 1.5}
            }
        elif "RSI" in choice:
            new_ind = {
                "id": uid,
                "name": "RSI",
                "display_name": "RSI (14)",
                "visible": True,
                "params": {"period": 14, "color": "#9c27b0", "lineWidth": 2}
            }
        elif "MACD" in choice:
            new_ind = {
                "id": uid,
                "name": "MACD",
                "display_name": "MACD (12, 26, 9)",
                "visible": True,
                "params": {"fast": 12, "slow": 26, "signal": 9, "color_macd": "#2962ff", "color_signal": "#ff9800"}
            }
        else:
            new_ind = {
                "id": uid,
                "name": "ATR",
                "display_name": "ATR (14)",
                "visible": True,
                "params": {"period": 14, "color": "#e91e63", "lineWidth": 1.5}
            }

        self.active_indicators.append(new_ind)
        self._refresh_table()

    def _apply_and_close(self) -> None:
        vol_vis = self.chk_volume.isChecked()
        self.applied.emit(vol_vis, self.active_indicators)
        self.accept()

    def get_result(self) -> tuple:
        return self.chk_volume.isChecked(), self.active_indicators
