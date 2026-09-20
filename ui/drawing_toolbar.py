from typing import Dict, Optional
from PyQt6.QtCore import pyqtSignal, QSize, Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from ui.icons import get_svg_icon


class DrawingToolBar(QFrame):
    """
    Vertical left-docked drawing toolbar locked to the left side of the chart
    (TradingView style). Features crisp vector icons, tooltips, shortcuts,
    and active tool state management.
    """

    tool_selected = pyqtSignal(str)
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    clear_requested = pyqtSignal()
    properties_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DrawingToolBar")
        self.setFixedWidth(46)
        self._active_tool = "CURSOR"
        self._buttons: Dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Drawing Tools Config: (ToolID, IconName, Tooltip, KeyShortcut)
        tools = [
            ("CURSOR", "cursor", "Cursor / Select", "Esc"),
            ("TRENDLINE", "trendline", "Trendline", "T"),
            ("RAY", "ray", "Ray Line", ""),
            ("PATH", "path", "Path / Polyline Tool", ""),
            ("HORIZONTAL_LINE", "horizontal_line", "Horizontal Line", "Alt+H"),
            ("VERTICAL_LINE", "vertical_line", "Vertical Line", "Alt+V"),
            ("RECTANGLE", "rectangle", "Rectangle / Box Zone", "R"),
            ("FIBONACCI", "fibonacci", "Fibonacci Retracement", "F"),
            ("VOLUME_PROFILE", "volume_profile", "Fixed Range Volume Profile (FRVP)", ""),
            ("TEXT", "text", "Text Label", ""),
            ("ARROW", "arrow", "Arrow Tool", ""),
            ("LONG_POSITION", "long_position", "Long Position Setup (R:R)", "L"),
            ("SHORT_POSITION", "short_position", "Short Position Setup (R:R)", "Shift+L"),
            ("MEASURE", "measure", "Measure / Ruler Tool", "M"),
        ]

        for tool_id, icon_name, label, shortcut in tools:
            btn = QPushButton()
            btn.setFixedSize(36, 36)
            btn.setIcon(get_svg_icon(icon_name, size=20))
            btn.setIconSize(QSize(20, 20))
            btn.setCheckable(True)

            tip_text = f"<b>{label}</b>"
            if shortcut:
                tip_text += f" <span style='color: #848e9c;'>({shortcut})</span>"
            btn.setToolTip(tip_text)

            btn.clicked.connect(lambda checked, tid=tool_id: self._on_tool_clicked(tid))
            self._group.addButton(btn)
            self._buttons[tool_id] = btn
            layout.addWidget(btn)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #2a2e39; max-height: 1px; margin: 4px 2px;")
        layout.addWidget(sep)

        # Quick Actions (Undo, Redo, Clear)
        btn_undo = QPushButton()
        btn_undo.setFixedSize(36, 36)
        btn_undo.setIcon(get_svg_icon("undo", size=18))
        btn_undo.setIconSize(QSize(18, 18))
        btn_undo.setToolTip("<b>Undo Drawing</b> <span style='color: #848e9c;'>(Ctrl+Z)</span>")
        btn_undo.clicked.connect(self.undo_requested.emit)
        layout.addWidget(btn_undo)

        btn_redo = QPushButton()
        btn_redo.setFixedSize(36, 36)
        btn_redo.setIcon(get_svg_icon("redo", size=18))
        btn_redo.setIconSize(QSize(18, 18))
        btn_redo.setToolTip("<b>Redo Drawing</b> <span style='color: #848e9c;'>(Ctrl+Y)</span>")
        btn_redo.clicked.connect(self.redo_requested.emit)
        layout.addWidget(btn_redo)

        btn_clear = QPushButton()
        btn_clear.setFixedSize(36, 36)
        btn_clear.setIcon(get_svg_icon("trash", size=18))
        btn_clear.setIconSize(QSize(18, 18))
        btn_clear.setToolTip("<b>Clear All Drawings</b>")
        btn_clear.clicked.connect(self.clear_requested.emit)
        layout.addWidget(btn_clear)

        # Set default active tool
        if "CURSOR" in self._buttons:
            self._buttons["CURSOR"].setChecked(True)

        self.setStyleSheet("""
            #DrawingToolBar {
                background-color: #131722;
                border-right: 1px solid #1e222d;
            }
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #2a2e39;
                border: 1px solid #363c4e;
            }
            QPushButton:checked {
                background-color: rgba(41, 98, 255, 0.2);
                border: 1px solid #2962ff;
            }
            QPushButton:pressed {
                background-color: #1e222d;
            }
        """)

    def _on_tool_clicked(self, tool_id: str) -> None:
        self._active_tool = tool_id
        if tool_id in self._buttons:
            self._buttons[tool_id].setChecked(True)
        self.tool_selected.emit(tool_id)

    def set_active_tool(self, tool_id: str) -> None:
        self._on_tool_clicked(tool_id)

    @property
    def active_tool(self) -> str:
        return self._active_tool
