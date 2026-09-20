from typing import Any, Dict, List, Optional
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.analytics.statistics import TradeStatistics


class EquityCurveWidget(QWidget):
    """High-performance antialiased equity curve chart widget rendered with QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.equity_points: List[float] = [10000.0]
        self.initial_balance: float = 10000.0
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

    def set_data(self, equity_points: List[float], initial_balance: float = 10000.0) -> None:
        self.equity_points = equity_points if equity_points else [initial_balance]
        self.initial_balance = initial_balance
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        pad_left = 60
        pad_right = 20
        pad_top = 20
        pad_bottom = 25

        # Background
        painter.fillRect(0, 0, w, h, QColor("#1e222d"))

        plot_w = w - pad_left - pad_right
        plot_h = h - pad_top - pad_bottom

        if plot_w <= 10 or plot_h <= 10:
            return

        min_val = min(min(self.equity_points), self.initial_balance)
        max_val = max(max(self.equity_points), self.initial_balance)

        range_val = max(max_val - min_val, 100.0)
        min_plot = min_val - range_val * 0.08
        max_plot = max_val + range_val * 0.08
        plot_span = max_plot - min_plot

        # Grid lines and labels
        painter.setPen(QPen(QColor("#2a2e39"), 1, Qt.PenStyle.DashLine))
        painter.setFont(QFont("sans-serif", 8))
        num_grid_lines = 4
        for i in range(num_grid_lines + 1):
            val = min_plot + (plot_span * i / num_grid_lines)
            y = pad_top + plot_h - (plot_h * (val - min_plot) / plot_span)
            painter.drawLine(int(pad_left), int(y), int(w - pad_right), int(y))
            painter.setPen(QColor("#848e9c"))
            painter.drawText(QRectF(0, y - 8, pad_left - 6, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"${val:,.0f}")
            painter.setPen(QPen(QColor("#2a2e39"), 1, Qt.PenStyle.DashLine))

        # Initial balance benchmark line
        y_init = pad_top + plot_h - (plot_h * (self.initial_balance - min_plot) / plot_span)
        painter.setPen(QPen(QColor("#787b86"), 1, Qt.PenStyle.DotLine))
        painter.drawLine(int(pad_left), int(y_init), int(w - pad_right), int(y_init))

        # Convert equity points to coordinates
        n = len(self.equity_points)
        coords: List[QPointF] = []
        for idx, eq in enumerate(self.equity_points):
            if n == 1:
                cx = pad_left + plot_w / 2
            else:
                cx = pad_left + (plot_w * idx / (n - 1))
            cy = pad_top + plot_h - (plot_h * (eq - min_plot) / plot_span)
            coords.append(QPointF(cx, cy))

        if not coords:
            return

        # Curve gradient fill
        latest_equity = self.equity_points[-1]
        is_profit = latest_equity >= self.initial_balance
        curve_color = QColor("#26a69a") if is_profit else QColor("#ef5350")
        grad_color = QColor(38, 166, 154, 40) if is_profit else QColor(239, 83, 80, 40)

        path = QPainterPath()
        path.moveTo(coords[0])
        for pt in coords[1:]:
            path.lineTo(pt)

        fill_path = QPainterPath(path)
        fill_path.lineTo(coords[-1].x(), pad_top + plot_h)
        fill_path.lineTo(coords[0].x(), pad_top + plot_h)
        fill_path.closeSubpath()

        gradient = QLinearGradient(0, pad_top, 0, pad_top + plot_h)
        gradient.setColorAt(0.0, grad_color)
        gradient.setColorAt(1.0, QColor(grad_color.red(), grad_color.green(), grad_color.blue(), 5))
        painter.fillPath(fill_path, QBrush(gradient))

        # Stroke equity curve line
        painter.setPen(QPen(curve_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)

        # Draw point nodes
        painter.setBrush(QBrush(curve_color))
        for pt in coords:
            painter.drawEllipse(pt, 2.5, 2.5)

        # Final end point pulse
        last_pt = coords[-1]
        painter.setPen(QPen(QColor("#ffffff"), 1.5))
        painter.setBrush(QBrush(curve_color))
        painter.drawEllipse(last_pt, 4.0, 4.0)

        # X-Axis label
        painter.setPen(QColor("#848e9c"))
        painter.drawText(QRectF(pad_left, h - 20, plot_w, 18), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, f"Trades (Total: {max(0, n - 1)})")


class AnalyticsPanel(QWidget):
    """Analytics overview dashboard showing performance statistics and visual equity curve."""

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

        # Equity Curve Chart
        grp_curve = QGroupBox("EQUITY CURVE & GROWTH")
        layout_curve = QVBoxLayout(grp_curve)
        layout_curve.setContentsMargins(4, 12, 4, 4)
        self.equity_widget = EquityCurveWidget()
        layout_curve.addWidget(self.equity_widget)
        layout.addWidget(grp_curve)

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

        if hasattr(stats, "equity_curve") and stats.equity_curve:
            self.equity_widget.set_data(stats.equity_curve)
