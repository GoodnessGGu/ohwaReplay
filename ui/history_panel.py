from typing import List
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.position import Position
from src.utils.constants import Direction


class HistoryPanel(QWidget):
    """Panel displaying closed trades history with CSV export capabilities."""

    export_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.trades: List[Position] = []
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        top_bar = QHBoxLayout()
        self.lbl_count = QLabel("Total Closed Trades: 0")
        self.lbl_count.setStyleSheet("font-weight: 600; color: #848e9c;")
        top_bar.addWidget(self.lbl_count)
        top_bar.addStretch()

        btn_export = QPushButton("📥 Export CSV")
        btn_export.clicked.connect(self._on_export)
        top_bar.addWidget(btn_export)
        layout.addLayout(top_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Trade ID", "Symbol", "Direction", "Volume", "Entry", "Exit",
            "SL", "TP", "Gross PnL", "Comm", "Net PnL", "Close Reason"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

    def update_history(self, trades: List[Position]) -> None:
        self.trades = trades
        self.lbl_count.setText(f"Total Closed Trades: {len(trades)}")
        self.table.setRowCount(len(trades))

        for row, t in enumerate(trades):
            self.table.setItem(row, 0, QTableWidgetItem(t.id))
            self.table.setItem(row, 1, QTableWidgetItem(t.symbol))

            dir_item = QTableWidgetItem(t.direction.value)
            dir_item.setForeground(Qt.GlobalColor.green if t.direction == Direction.BUY else Qt.GlobalColor.red)
            self.table.setItem(row, 2, dir_item)

            self.table.setItem(row, 3, QTableWidgetItem(f"{t.lot_size:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{t.entry_price:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{t.close_price:.2f}" if t.close_price else "--"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{t.stop_loss:.2f}" if t.stop_loss else "--"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{t.take_profit:.2f}" if t.take_profit else "--"))
            self.table.setItem(row, 8, QTableWidgetItem(f"${t.gross_pnl:+,.2f}"))
            self.table.setItem(row, 9, QTableWidgetItem(f"${t.commission:.2f}"))

            net_item = QTableWidgetItem(f"${t.net_pnl:+,.2f}")
            net_item.setForeground(Qt.GlobalColor.green if t.net_pnl >= 0 else Qt.GlobalColor.red)
            self.table.setItem(row, 10, net_item)

            reason_str = t.close_reason.value if t.close_reason else "--"
            self.table.setItem(row, 11, QTableWidgetItem(reason_str))

    def _on_export(self) -> None:
        if not self.trades:
            QMessageBox.information(self, "Export CSV", "No closed trades to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Trade History", "trade_history.csv", "CSV Files (*.csv)"
        )
        if file_path:
            self.export_requested.emit(file_path)
