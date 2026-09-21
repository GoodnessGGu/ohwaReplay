from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabBar,
    QToolButton,
    QWidget,
)


class ChartTabInfo:
    """Encapsulates state for an individual chart tab."""

    def __init__(self, tab_id: str, symbol: str = "XAUUSD", timeframe: str = "5m", mode: str = "replay"):
        self.tab_id = tab_id
        self.symbol = symbol
        self.timeframe = timeframe
        self.mode = mode  # "replay" or "live"
        self.replay_index: Optional[int] = None
        self.drawings: List[Dict[str, Any]] = []
        self.indicators: List[Dict[str, Any]] = []
        self.visible_range: Optional[Dict[str, Any]] = None


    @property
    def display_text(self) -> str:
        icon = "🔴" if self.mode == "live" else "📊"
        return f"{icon} {self.symbol} • {self.timeframe}"


class ChartTabBar(QWidget):
    """
    Top Tab Bar for Multi-Chart Management (Up to 4 Tabs with '+' button).
    """

    tab_selected = pyqtSignal(int)
    tab_closed = pyqtSignal(int)
    tab_add_requested = pyqtSignal()

    def __init__(self, max_tabs: int = 4, parent=None):
        super().__init__(parent)
        self.max_tabs = max_tabs
        self.tabs: List[ChartTabInfo] = []
        self.current_tab_index = 0
        self.init_ui()

    def init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        self.setStyleSheet("""
            ChartTabBar {
                background-color: #131722;
                border-bottom: 1px solid #2a2e39;
                max-height: 34px;
            }
        """)

        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(False)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setStyleSheet("""
            QTabBar::tab {
                background: #1e222d;
                color: #848e9c;
                font-weight: 700;
                font-size: 11px;
                padding: 5px 12px;
                margin-right: 3px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #2a2e39;
                border-bottom: none;
                min-width: 110px;
            }
            QTabBar::tab:hover {
                background: #262b3d;
                color: #d1d4dc;
            }
            QTabBar::tab:selected {
                background: #2a2e39;
                color: #2962ff;
                border-top: 2px solid #2962ff;
            }
            QTabBar::close-button {
                image: none;
                subcontrol-position: right;
            }
        """)
        self.tab_bar.currentChanged.connect(self._on_tab_bar_changed)
        self.tab_bar.tabCloseRequested.connect(self._on_tab_close_requested)
        layout.addWidget(self.tab_bar)

        # '+' Add Tab Button
        self.btn_add_tab = QToolButton()
        self.btn_add_tab.setText("+")
        self.btn_add_tab.setToolTip("Open New Chart Tab (Max 4)")
        self.btn_add_tab.setStyleSheet("""
            QToolButton {
                background-color: #1e222d;
                color: #2962ff;
                font-weight: 800;
                font-size: 16px;
                border: 1px solid #363c4e;
                border-radius: 4px;
                padding: 0px 8px;
                height: 22px;
            }
            QToolButton:hover {
                background-color: #2962ff;
                color: #ffffff;
            }
        """)
        self.btn_add_tab.clicked.connect(self.tab_add_requested.emit)
        layout.addWidget(self.btn_add_tab)
        layout.addStretch()

    def add_tab(self, symbol: str = "XAUUSD", timeframe: str = "5m", mode: str = "replay") -> Optional[int]:
        """Adds a new tab if under max limit (4)."""
        if len(self.tabs) >= self.max_tabs:
            return None

        tab_id = f"tab_{len(self.tabs) + 1}"
        tab_info = ChartTabInfo(tab_id=tab_id, symbol=symbol, timeframe=timeframe, mode=mode)
        self.tabs.append(tab_info)

        idx = self.tab_bar.addTab(tab_info.display_text)
        self._update_add_button_state()
        self.tab_bar.setCurrentIndex(idx)
        return idx

    def close_tab(self, index: int) -> bool:
        """Closes a tab by index (preserves minimum 1 tab)."""
        if len(self.tabs) <= 1 or index < 0 or index >= len(self.tabs):
            return False

        self.tabs.pop(index)
        self.tab_bar.removeTab(index)
        self._update_add_button_state()
        return True

    def update_tab_label(self, index: int, symbol: str, timeframe: str, mode: str = "replay") -> None:
        """Updates symbol/timeframe display on an existing tab."""
        if 0 <= index < len(self.tabs):
            tab_info = self.tabs[index]
            tab_info.symbol = symbol
            tab_info.timeframe = timeframe
            tab_info.mode = mode
            self.tab_bar.setTabText(index, tab_info.display_text)

    def remove_tab(self, index: int) -> bool:
        """Alias for close_tab."""
        return self.close_tab(index)

    def select_tab(self, index: int) -> None:
        """Selects tab at specified index."""
        if 0 <= index < len(self.tabs):
            self.tab_bar.setCurrentIndex(index)

    def get_tab(self, index: int) -> Optional[ChartTabInfo]:
        """Returns ChartTabInfo at specified index."""
        if 0 <= index < len(self.tabs):
            return self.tabs[index]
        return None

    def get_current_tab(self) -> Optional[ChartTabInfo]:
        if 0 <= self.current_tab_index < len(self.tabs):
            return self.tabs[self.current_tab_index]
        return None


    def _on_tab_bar_changed(self, index: int) -> None:
        if 0 <= index < len(self.tabs):
            self.current_tab_index = index
            self.tab_selected.emit(index)

    def _on_tab_close_requested(self, index: int) -> None:
        if len(self.tabs) > 1:
            self.tab_closed.emit(index)

    def _update_add_button_state(self) -> None:
        can_add = len(self.tabs) < self.max_tabs
        self.btn_add_tab.setEnabled(can_add)
        self.btn_add_tab.setToolTip(f"Open New Chart Tab ({len(self.tabs)}/{self.max_tabs})" if can_add else "Maximum 4 tabs reached")
