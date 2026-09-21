from typing import Dict, List, Optional, Tuple
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.utils.constants import ASSET_CATEGORIES


class SymbolSearchDialog(QDialog):
    """
    Professional TradingView-style Symbol Search and Categorized Asset Selector.
    Supports instant search filtering, category tabs, and 1-click selection.
    """

    symbol_selected = pyqtSignal(str)

    def __init__(self, current_symbol: str = "XAUUSD", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Symbol Search & Markets")
        self.resize(600, 500)
        self.selected_symbol = current_symbol
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Title
        lbl_title = QLabel("Select Asset / Pair")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        layout.addWidget(lbl_title)

        # Search Input
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search symbol or market name (e.g., Gold, EUR, BTC, US30)...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2a2e39;
                color: #ffffff;
                font-size: 13px;
                padding: 8px 12px;
                border: 1px solid #434651;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border: 1px solid #2962ff;
            }
        """)
        self.search_edit.textChanged.connect(self._filter_table)
        layout.addWidget(self.search_edit)

        # Category Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #363c4e;
                background-color: #1e222d;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #1e222d;
                color: #848e9c;
                font-weight: 600;
                font-size: 12px;
                padding: 6px 14px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2a2e39;
                color: #2962ff;
                border-bottom: 2px solid #2962ff;
            }
        """)

        # Build tables for tabs
        self.category_tables: Dict[str, QTableWidget] = {}
        all_categories = ["All"] + list(ASSET_CATEGORIES.keys())

        for cat in all_categories:
            table = self._create_symbol_table(cat)
            self.category_tables[cat] = table
            self.tabs.addTab(table, cat)

        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        # Bottom Action Bar
        bottom_box = QHBoxLayout()
        btn_close = QPushButton("Cancel")
        btn_close.setStyleSheet("padding: 6px 14px; font-weight: 600;")
        btn_close.clicked.connect(self.reject)

        self.btn_select = QPushButton("Select Symbol")
        self.btn_select.setStyleSheet("background-color: #2962ff; color: #ffffff; font-weight: bold; padding: 6px 18px; border-radius: 4px;")
        self.btn_select.clicked.connect(self._on_select_clicked)

        bottom_box.addStretch()
        bottom_box.addWidget(btn_close)
        bottom_box.addWidget(self.btn_select)
        layout.addLayout(bottom_box)

        self.search_edit.setFocus()

    def _create_symbol_table(self, category: str) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Symbol", "Description", "Category"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1e222d;
                color: #d1d4dc;
                gridline-color: #2a2e39;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #2962ff;
                color: #ffffff;
            }
        """)

        symbols_list: List[Tuple[str, str, str]] = []
        if category == "All":
            for cat_name, items in ASSET_CATEGORIES.items():
                for sym, desc in items:
                    symbols_list.append((sym, desc, cat_name))
        else:
            items = ASSET_CATEGORIES.get(category, [])
            for sym, desc in items:
                symbols_list.append((sym, desc, category))

        table.setRowCount(len(symbols_list))
        for row, (sym, desc, cat_name) in enumerate(symbols_list):
            item_sym = QTableWidgetItem(sym)
            item_sym.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            item_sym.setData(Qt.ItemDataRole.UserRole, sym)

            item_desc = QTableWidgetItem(desc)
            item_cat = QTableWidgetItem(cat_name)
            item_cat.setForeground(Qt.GlobalColor.darkGray)

            table.setItem(row, 0, item_sym)
            table.setItem(row, 1, item_desc)
            table.setItem(row, 2, item_cat)

        table.itemDoubleClicked.connect(self._on_table_double_click)
        return table

    def _filter_table(self, text: str) -> None:
        query = text.strip().upper()
        current_table = self.tabs.currentWidget()
        if not isinstance(current_table, QTableWidget):
            return

        for row in range(current_table.rowCount()):
            sym_item = current_table.item(row, 0)
            desc_item = current_table.item(row, 1)
            cat_item = current_table.item(row, 2)

            sym_text = sym_item.text().upper() if sym_item else ""
            desc_text = desc_item.text().upper() if desc_item else ""
            cat_text = cat_item.text().upper() if cat_item else ""

            match = (query in sym_text) or (query in desc_text) or (query in cat_text)
            current_table.setRowHidden(row, not match)

    def _on_tab_changed(self, idx: int) -> None:
        self._filter_table(self.search_edit.text())

    def _on_table_double_click(self, item: QTableWidgetItem) -> None:
        table = self.tabs.currentWidget()
        if isinstance(table, QTableWidget):
            row = item.row()
            sym_item = table.item(row, 0)
            if sym_item:
                self.selected_symbol = sym_item.text()
                self.symbol_selected.emit(self.selected_symbol)
                self.accept()

    def _on_select_clicked(self) -> None:
        table = self.tabs.currentWidget()
        if isinstance(table, QTableWidget):
            sel_rows = table.selectionModel().selectedRows()
            if sel_rows:
                row = sel_rows[0].row()
                sym_item = table.item(row, 0)
                if sym_item:
                    self.selected_symbol = sym_item.text()
                    self.symbol_selected.emit(self.selected_symbol)
                    self.accept()
                    return
        self.accept()
