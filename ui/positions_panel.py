from typing import Any, Dict, List, Optional
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.order import Order
from src.core.position import Position
from src.utils.constants import Direction


class PositionsPanel(QWidget):
    """Panel displaying active open trading positions and pending orders."""

    close_position_requested = pyqtSignal(str)
    cancel_pending_order_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "Symbol", "Type / Direction", "Volume", "Entry Price", "Current Price", "SL", "TP", "PnL ($)", "Time", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

    def update_positions(self, positions: List[Position], pending_orders: Optional[List[Order]] = None, current_price: Optional[float] = None) -> None:
        pending = pending_orders or []
        total_rows = len(positions) + len(pending)
        self.table.setRowCount(total_rows)

        # 1. Open Active Positions
        for row, p in enumerate(positions):
            self.table.setItem(row, 0, QTableWidgetItem(p.id))
            self.table.setItem(row, 1, QTableWidgetItem(p.symbol))

            dir_item = QTableWidgetItem(f"● {p.direction.value}")
            dir_item.setForeground(Qt.GlobalColor.green if p.direction == Direction.BUY else Qt.GlobalColor.red)
            self.table.setItem(row, 2, dir_item)

            self.table.setItem(row, 3, QTableWidgetItem(f"{p.lot_size:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{p.entry_price:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{p.current_price:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{p.stop_loss:.2f}" if p.stop_loss else "--"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{p.take_profit:.2f}" if p.take_profit else "--"))

            pnl_item = QTableWidgetItem(f"${p.net_pnl:+,.2f}")
            pnl_item.setForeground(Qt.GlobalColor.green if p.net_pnl >= 0 else Qt.GlobalColor.red)
            self.table.setItem(row, 8, pnl_item)

            time_str = p.open_time.strftime("%Y-%m-%d %H:%M") if p.open_time else "--"
            self.table.setItem(row, 9, QTableWidgetItem(time_str))

            # Close button
            btn_close = QPushButton("Close")
            btn_close.setStyleSheet("background-color: #ef5350; color: #ffffff; padding: 2px 8px; font-weight: bold; border-radius: 3px;")
            btn_close.clicked.connect(lambda checked, pid=p.id: self.close_position_requested.emit(pid))
            self.table.setCellWidget(row, 10, btn_close)

        # 2. Pending Orders
        offset = len(positions)
        for idx, o in enumerate(pending):
            row = offset + idx
            self.table.setItem(row, 0, QTableWidgetItem(o.id))
            self.table.setItem(row, 1, QTableWidgetItem(o.symbol))

            ot_name = o.order_type.value if hasattr(o.order_type, "value") else str(o.order_type)
            type_item = QTableWidgetItem(f"⏳ {ot_name.replace('_', ' ')}")
            type_item.setForeground(Qt.GlobalColor.cyan if "BUY" in ot_name else Qt.GlobalColor.yellow)
            self.table.setItem(row, 2, type_item)

            self.table.setItem(row, 3, QTableWidgetItem(f"{o.lot_size:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{o.price:.2f}" if o.price else "--"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{current_price:.2f}" if current_price else "--"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{o.stop_loss:.2f}" if o.stop_loss else "--"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{o.take_profit:.2f}" if o.take_profit else "--"))

            pnl_item = QTableWidgetItem("PENDING")
            pnl_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 8, pnl_item)

            time_str = o.datetime.strftime("%Y-%m-%d %H:%M") if o.datetime else "--"
            self.table.setItem(row, 9, QTableWidgetItem(time_str))

            # Cancel button
            btn_cancel = QPushButton("Cancel")
            btn_cancel.setStyleSheet("background-color: #434651; color: #ffffff; padding: 2px 8px; font-weight: 600; border-radius: 3px;")
            btn_cancel.clicked.connect(lambda checked, oid=o.id: self.cancel_pending_order_requested.emit(oid))
            self.table.setCellWidget(row, 10, btn_cancel)
