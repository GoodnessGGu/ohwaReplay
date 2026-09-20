from typing import Any, Dict
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.analytics.statistics import TradeStatistics


class AnalyticsPanel(QWidget):
    """Analytics overview dashboard showing performance statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # Overview Grid
        grp_overview = QGroupBox("PERFORMANCE OVERVIEW")
        grid_overview = QGridLayout(grp_overview)
        grid_overview.setHorizontalSpacing(24)
        grid_overview.setVerticalSpacing(8)

        self.lbl_net_profit = self._add_stat(grid_overview, "Total Net Profit:", "$0.00", 0, 0)
        self.lbl_win_rate = self._add_stat(grid_overview, "Win Rate:", "0.00 %", 0, 1)
        self.lbl_profit_factor = self._add_stat(grid_overview, "Profit Factor:", "0.00", 0, 2)
        self.lbl_max_drawdown = self._add_stat(grid_overview, "Max Drawdown:", "$0.00 (0.00%)", 0, 3)

        self.lbl_gross_profit = self._add_stat(grid_overview, "Gross Profit:", "$0.00", 1, 0)
        self.lbl_gross_loss = self._add_stat(grid_overview, "Gross Loss:", "$0.00", 1, 1)
        self.lbl_total_trades = self._add_stat(grid_overview, "Total Trades:", "0", 1, 2)
        self.lbl_win_loss_count = self._add_stat(grid_overview, "Wins / Losses:", "0 / 0", 1, 3)

        self.lbl_avg_win = self._add_stat(grid_overview, "Average Win:", "$0.00", 2, 0)
        self.lbl_avg_loss = self._add_stat(grid_overview, "Average Loss:", "$0.00", 2, 1)
        self.lbl_expectancy = self._add_stat(grid_overview, "Expectancy:", "$0.00", 2, 2)
        self.lbl_streaks = self._add_stat(grid_overview, "Max Consecutive W/L:", "0 / 0", 2, 3)

        layout.addWidget(grp_overview)

        # Direction breakdown
        grp_dir = QGroupBox("DIRECTION ANALYSIS")
        grid_dir = QGridLayout(grp_dir)
        grid_dir.setHorizontalSpacing(24)

        self.lbl_long_stats = self._add_stat(grid_dir, "Long Trades:", "0 trades | 0% win | $0.00", 0, 0)
        self.lbl_short_stats = self._add_stat(grid_dir, "Short Trades:", "0 trades | 0% win | $0.00", 0, 1)

        layout.addWidget(grp_dir)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _add_stat(self, grid: QGridLayout, title: str, value: str, row: int, col: int) -> QLabel:
        box = QHBoxLayout()
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #848e9c; font-weight: 600;")
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet("color: #ffffff; font-weight: 700;")
        box.addWidget(t_lbl)
        box.addWidget(v_lbl)
        grid.addLayout(box, row, col)
        return v_lbl

    def update_statistics(self, stats: TradeStatistics) -> None:
        pnl_color = "#26a69a" if stats.total_net_profit >= 0 else "#ef5350"
        self.lbl_net_profit.setStyleSheet(f"color: {pnl_color}; font-weight: 700;")
        self.lbl_net_profit.setText(f"${stats.total_net_profit:+,.2f}")

        self.lbl_win_rate.setText(f"{stats.win_rate_pct:.2f} %")
        self.lbl_profit_factor.setText(f"{stats.profit_factor:.2f}")
        self.lbl_max_drawdown.setText(f"${stats.max_drawdown_amount:,.2f} ({stats.max_drawdown_pct:.2f}%)")

        self.lbl_gross_profit.setText(f"${stats.gross_profit:,.2f}")
        self.lbl_gross_loss.setText(f"${stats.gross_loss:,.2f}")
        self.lbl_total_trades.setText(str(stats.total_trades))
        self.lbl_win_loss_count.setText(f"{stats.winning_trades} / {stats.losing_trades}")

        self.lbl_avg_win.setText(f"${stats.average_win:,.2f}")
        self.lbl_avg_loss.setText(f"${stats.average_loss:,.2f}")
        self.lbl_expectancy.setText(f"${stats.expectancy:+,.2f}")
        self.lbl_streaks.setText(f"{stats.max_consecutive_wins} / {stats.max_consecutive_losses}")

        self.lbl_long_stats.setText(
            f"{stats.long_trades_count} trades | {stats.long_win_rate_pct:.1f}% win | ${stats.long_profit:+,.2f}"
        )
        self.lbl_short_stats.setText(
            f"{stats.short_trades_count} trades | {stats.short_win_rate_pct:.1f}% win | ${stats.short_profit:+,.2f}"
        )
