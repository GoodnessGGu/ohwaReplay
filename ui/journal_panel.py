from typing import Any, Dict, List, Optional
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.position import Position


class JournalPanel(QWidget):
    """Trade journal panel for annotating and reviewing trading decisions."""

    journal_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.trades: List[Position] = []
        self.selected_trade_id: Optional[str] = None
        self.init_ui()

    def init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        # Left list of trades
        left_box = QVBoxLayout()
        lbl_list = QLabel("Journal Trades:")
        lbl_list.setStyleSheet("font-weight: 600; color: #848e9c;")
        left_box.addWidget(lbl_list)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Symbol", "Net PnL", "Strategy"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_trade_selected)
        left_box.addWidget(self.table)
        layout.addLayout(left_box, 1)

        # Right editor form
        right_box = QVBoxLayout()
        grp_editor = QGroupBox("TRADE LOG & NOTES")
        form = QFormLayout(grp_editor)

        self.txt_strategy = QLineEdit()
        self.txt_strategy.setPlaceholderText("e.g. Breakout, FVG, Support/Resistance")
        form.addRow("Strategy:", self.txt_strategy)

        self.txt_setup = QLineEdit()
        self.txt_setup.setPlaceholderText("e.g. London open expansion")
        form.addRow("Setup:", self.txt_setup)

        self.txt_tags = QLineEdit()
        self.txt_tags.setPlaceholderText("e.g. A+ setup, FOMC, follow-the-trend")
        form.addRow("Tags:", self.txt_tags)

        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Enter detailed execution rationale, psychology notes, lessons learned...")
        form.addRow("Notes:", self.txt_notes)

        btn_save = QPushButton("Save Journal Entry")
        btn_save.clicked.connect(self._on_save)
        form.addRow("", btn_save)

        right_box.addWidget(grp_editor)
        layout.addLayout(right_box, 2)

    def update_trades(self, trades: List[Position]) -> None:
        self.trades = trades
        self.table.setRowCount(len(trades))
        for row, t in enumerate(trades):
            self.table.setItem(row, 0, QTableWidgetItem(t.id))
            self.table.setItem(row, 1, QTableWidgetItem(t.symbol))
            self.table.setItem(row, 2, QTableWidgetItem(f"${t.net_pnl:+,.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(t.strategy or "--"))

    def _on_trade_selected(self) -> None:
        sel = self.table.selectedItems()
        if not sel:
            return
        row = sel[0].row()
        if 0 <= row < len(self.trades):
            t = self.trades[row]
            self.selected_trade_id = t.id
            self.txt_strategy.setText(t.strategy)
            self.txt_notes.setPlainText(t.notes)
            self.txt_tags.setText(t.tags)

    def _on_save(self) -> None:
        if not self.selected_trade_id:
            return
        for t in self.trades:
            if t.id == self.selected_trade_id:
                t.strategy = self.txt_strategy.text().strip()
                t.notes = self.txt_notes.toPlainText().strip()
                t.tags = self.txt_tags.text().strip()
                self.update_trades(self.trades)
                self.journal_saved.emit({
                    "id": t.id,
                    "strategy": t.strategy,
                    "notes": t.notes,
                    "tags": t.tags,
                })
                break
