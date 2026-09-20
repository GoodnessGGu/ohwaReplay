from typing import Any, Dict
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from src.utils.helpers import format_currency


class DashboardWidget(QFrame):
    """Header dashboard widget displaying real-time financial and account metrics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            DashboardWidget {
                background-color: #1e222d;
                border-bottom: 1px solid #2a2e39;
                padding: 4px 10px;
            }
        """)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(20)

        self.lbl_balance = self._create_metric("BALANCE", "$10,000.00")
        self.lbl_equity = self._create_metric("EQUITY", "$10,000.00")
        self.lbl_open_pnl = self._create_metric("OPEN PNL", "$0.00", "#848e9c")
        self.lbl_realized_pnl = self._create_metric("REALIZED PNL", "$0.00", "#848e9c")
        self.lbl_margin = self._create_metric("MARGIN", "$0.00")
        self.lbl_free_margin = self._create_metric("FREE MARGIN", "$10,000.00")
        self.lbl_positions = self._create_metric("POSITIONS", "0")

        layout.addLayout(self.lbl_balance[0])
        layout.addLayout(self.lbl_equity[0])
        layout.addLayout(self.lbl_open_pnl[0])
        layout.addLayout(self.lbl_realized_pnl[0])
        layout.addLayout(self.lbl_margin[0])
        layout.addLayout(self.lbl_free_margin[0])
        layout.addLayout(self.lbl_positions[0])
        layout.addStretch()

    def _create_metric(self, title: str, value: str, val_color: str = "#ffffff"):
        box = QHBoxLayout()
        box.setSpacing(6)

        t_lbl = QLabel(title + ":")
        t_lbl.setStyleSheet("color: #848e9c; font-size: 11px; font-weight: 600;")

        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {val_color}; font-size: 12px; font-weight: 700;")

        box.addWidget(t_lbl)
        box.addWidget(v_lbl)
        return box, v_lbl

    def update_account(self, data: Dict[str, Any]) -> None:
        """Updates dashboard metric values."""
        bal = float(data.get("balance", 10000.0))
        eq = float(data.get("equity", 10000.0))
        open_pnl = float(data.get("unrealized_pnl", 0.0))
        real_pnl = float(data.get("realized_pnl", 0.0))
        margin = float(data.get("used_margin", 0.0))
        free_m = float(data.get("free_margin", 10000.0))
        pos_count = int(data.get("open_positions_count", 0))

        self.lbl_balance[1].setText(f"${bal:,.2f}")
        self.lbl_equity[1].setText(f"${eq:,.2f}")

        # Open PnL color
        pnl_color = "#26a69a" if open_pnl > 0 else ("#ef5350" if open_pnl < 0 else "#848e9c")
        self.lbl_open_pnl[1].setStyleSheet(f"color: {pnl_color}; font-size: 12px; font-weight: 700;")
        self.lbl_open_pnl[1].setText(f"{format_currency(open_pnl)}")

        # Realized PnL color
        r_color = "#26a69a" if real_pnl > 0 else ("#ef5350" if real_pnl < 0 else "#848e9c")
        self.lbl_realized_pnl[1].setStyleSheet(f"color: {r_color}; font-size: 12px; font-weight: 700;")
        self.lbl_realized_pnl[1].setText(f"{format_currency(real_pnl)}")

        self.lbl_margin[1].setText(f"${margin:,.2f}")
        self.lbl_free_margin[1].setText(f"${free_m:,.2f}")
        self.lbl_positions[1].setText(str(pos_count))
