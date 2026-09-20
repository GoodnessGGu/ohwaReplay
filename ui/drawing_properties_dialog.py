from typing import Any, Dict, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.drawings.base_tool import Drawing, DrawingStyle


class DrawingPropertiesDialog(QDialog):
    """
    Comprehensive dialog to edit all visual and structural properties
    of a drawing (outline color, line width, line style, fill color,
    fill opacity, text label, font size, locked state, etc.).
    """

    def __init__(self, drawing_dict: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Drawing Properties - {drawing_dict.get('type', 'Drawing')}")
        self.setMinimumWidth(380)
        self._drawing_data = drawing_dict.copy()
        self._style_data = self._drawing_data.get("style", {}).copy()

        self._outline_color = self._style_data.get("color", "#2962ff")
        self._fill_color = self._style_data.get("fill_color", "rgba(41, 98, 255, 0.2)")

        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # 1. Line / Outline Group
        grp_line = QGroupBox("Line & Outline")
        form_line = QFormLayout(grp_line)

        # Color picker button
        h_color = QHBoxLayout()
        self.btn_color = QPushButton()
        self.btn_color.setFixedHeight(26)
        self._update_color_button(self.btn_color, self._outline_color)
        self.btn_color.clicked.connect(self._choose_outline_color)
        h_color.addWidget(self.btn_color)

        self.lbl_color_hex = QLabel(self._outline_color)
        self.lbl_color_hex.setStyleSheet("color: #848e9c; font-weight: bold;")
        h_color.addWidget(self.lbl_color_hex)
        form_line.addRow("Outline Color:", h_color)

        # Line Width
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 10)
        self.spin_width.setValue(int(self._style_data.get("line_width", 2)))
        form_line.addRow("Line Width:", self.spin_width)

        # Line Style
        self.combo_style = QComboBox()
        self.combo_style.addItems(["solid", "dashed", "dotted"])
        self.combo_style.setCurrentText(str(self._style_data.get("line_style", "solid")))
        form_line.addRow("Line Style:", self.combo_style)

        main_layout.addWidget(grp_line)

        # 2. Fill & Background Group
        grp_fill = QGroupBox("Fill & Transparency")
        form_fill = QFormLayout(grp_fill)

        h_fill = QHBoxLayout()
        self.btn_fill = QPushButton()
        self.btn_fill.setFixedHeight(26)
        self._update_color_button(self.btn_fill, self._fill_color)
        self.btn_fill.clicked.connect(self._choose_fill_color)
        h_fill.addWidget(self.btn_fill)

        self.lbl_fill_hex = QLabel(self._fill_color)
        self.lbl_fill_hex.setStyleSheet("color: #848e9c; font-weight: bold;")
        h_fill.addWidget(self.lbl_fill_hex)
        form_fill.addRow("Fill Color:", h_fill)

        # Opacity Slider
        h_op = QHBoxLayout()
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        init_op = int(float(self._style_data.get("opacity", 0.35)) * 100)
        self.slider_opacity.setValue(init_op)
        self.lbl_op_val = QLabel(f"{init_op}%")
        self.slider_opacity.valueChanged.connect(lambda v: self.lbl_op_val.setText(f"{v}%"))
        h_op.addWidget(self.slider_opacity)
        h_op.addWidget(self.lbl_op_val)
        form_fill.addRow("Fill Opacity:", h_op)

        main_layout.addWidget(grp_fill)

        # 3. Text & Typography Group (if applicable)
        grp_text = QGroupBox("Text & Label")
        form_text = QFormLayout(grp_text)

        self.txt_label = QLineEdit(str(self._drawing_data.get("text", "")))
        form_text.addRow("Text / Label:", self.txt_label)

        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 36)
        self.spin_font_size.setValue(int(self._style_data.get("font_size", 12)))
        form_text.addRow("Font Size:", self.spin_font_size)

        main_layout.addWidget(grp_text)

        # Buttons
        h_btns = QHBoxLayout()
        h_btns.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        h_btns.addWidget(btn_cancel)

        btn_save = QPushButton("Apply & Save")
        btn_save.setStyleSheet("background-color: #2962ff; color: #ffffff; font-weight: bold; padding: 6px 16px;")
        btn_save.clicked.connect(self.accept)
        h_btns.addWidget(btn_save)

        main_layout.addLayout(h_btns)

    def _update_color_button(self, btn: QPushButton, color_str: str) -> None:
        btn.setStyleSheet(f"background-color: {color_str}; border: 1px solid #434651; border-radius: 4px; min-width: 60px;")

    def _choose_outline_color(self) -> None:
        col = QColorDialog.getColor(QColor(self._outline_color), self, "Select Outline Color")
        if col.isValid():
            self._outline_color = col.name()
            self.lbl_color_hex.setText(self._outline_color)
            self._update_color_button(self.btn_color, self._outline_color)

    def _choose_fill_color(self) -> None:
        col = QColorDialog.getColor(QColor(self._fill_color), self, "Select Fill Color")
        if col.isValid():
            self._fill_color = col.name()
            self.lbl_fill_hex.setText(self._fill_color)
            self._update_color_button(self.btn_fill, self._fill_color)

    def get_updated_drawing_dict(self) -> Dict[str, Any]:
        """Returns updated drawing dictionary with modified properties."""
        res = self._drawing_data.copy()
        res_style = self._style_data.copy()

        res_style["color"] = self._outline_color
        res_style["line_width"] = self.spin_width.value()
        res_style["line_style"] = self.combo_style.currentText()
        res_style["font_size"] = self.spin_font_size.value()

        # Build rgba fill with opacity slider
        op_val = self.slider_opacity.value() / 100.0
        res_style["opacity"] = op_val
        fill_qcol = QColor(self._fill_color)
        res_style["fill_color"] = f"rgba({fill_qcol.red()}, {fill_qcol.green()}, {fill_qcol.blue()}, {op_val:.2f})"

        res["text"] = self.txt_label.text().strip()
        res["style"] = res_style
        return res
