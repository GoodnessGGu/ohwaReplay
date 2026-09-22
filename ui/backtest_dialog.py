import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.backtest.engine import BacktestEngine, BacktestResult
from src.backtest.strategies import EMACrossoverStrategy, FVGStrategy, MarketStructureStrategy
from src.backtest.tearsheet import TearsheetGenerator
from src.utils.logger import logger


class BacktestDialog(QDialog):
    """
    Automated Quantitative Strategy Backtesting Dialog with instant tearsheet generation.
    """

    def __init__(self, current_df: pd.DataFrame, symbol: str = "XAUUSD", timeframe: str = "5m", parent=None):
        super().__init__(parent)
        self.df = current_df
        self.symbol = symbol
        self.timeframe = timeframe
        self.result: Optional[BacktestResult] = None
        self.saved_tearsheet_path: Optional[str] = None

        self.setWindowTitle("🚀 Automated Strategy Backtesting & Tearsheet Generator")
        self.resize(720, 600)
        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # 1. Configuration Groups (Grid of Strategy & Capital)
        top_grid = QHBoxLayout()

        # Left Group: Strategy & Direction
        grp_strategy = QGroupBox("STRATEGY & DIRECTION")
        form_strat = QFormLayout(grp_strategy)

        self.combo_strategy = QComboBox()
        self.combo_strategy.addItems([
            "FVG Retest Strategy (Smart Money Concepts)",
            "Market Structure Strategy (BOS & CHoCH)",
            "EMA Crossover Trend Strategy (9/21)",
        ])
        form_strat.addRow("Strategy:", self.combo_strategy)

        self.combo_direction = QComboBox()
        self.combo_direction.addItems([
            "Both (Long & Short)",
            "Long Only",
            "Short Only",
        ])
        form_strat.addRow("Trade Direction:", self.combo_direction)

        self.spin_rr = QDoubleSpinBox()
        self.spin_rr.setRange(0.5, 20.0)
        self.spin_rr.setValue(2.0)
        self.spin_rr.setSuffix(" R")
        form_strat.addRow("Target Risk-Reward:", self.spin_rr)

        self.combo_scope = QComboBox()
        self.combo_scope.addItems([
            "Full Dataset (All Available)",
            "Last 500 Candles",
            "Last 1,000 Candles",
            "Last 2,000 Candles",
            "First 50% (In-Sample)",
            "Second 50% (Out-of-Sample)",
        ])
        form_strat.addRow("Data Scope:", self.combo_scope)

        top_grid.addWidget(grp_strategy)

        # Right Group: Capital & Execution Realism
        grp_capital = QGroupBox("CAPITAL & EXECUTION REALISM")
        form_cap = QFormLayout(grp_capital)

        self.spin_balance = QDoubleSpinBox()
        self.spin_balance.setRange(100.0, 10000000.0)
        self.spin_balance.setValue(10000.0)
        self.spin_balance.setPrefix("$ ")
        self.spin_balance.setSingleStep(1000.0)
        form_cap.addRow("Initial Balance:", self.spin_balance)

        self.combo_sizing = QComboBox()
        self.combo_sizing.addItems(["Risk Percentage (%)", "Fixed Lot Size"])
        self.combo_sizing.currentIndexChanged.connect(self._on_sizing_mode_changed)
        form_cap.addRow("Sizing Mode:", self.combo_sizing)

        self.spin_risk = QDoubleSpinBox()
        self.spin_risk.setRange(0.1, 50.0)
        self.spin_risk.setValue(1.0)
        self.spin_risk.setSuffix(" %")
        form_cap.addRow("Risk Per Trade:", self.spin_risk)

        self.spin_fixed_lot = QDoubleSpinBox()
        self.spin_fixed_lot.setRange(0.01, 100.0)
        self.spin_fixed_lot.setValue(1.0)
        self.spin_fixed_lot.setSingleStep(0.1)
        self.spin_fixed_lot.setVisible(False)
        self.lbl_fixed_lot = QLabel("Fixed Lot Size:")
        self.lbl_fixed_lot.setVisible(False)
        form_cap.addRow(self.lbl_fixed_lot, self.spin_fixed_lot)

        self.spin_comm = QDoubleSpinBox()
        self.spin_comm.setRange(0.0, 100.0)
        self.spin_comm.setValue(7.0)
        self.spin_comm.setPrefix("$ ")
        form_cap.addRow("Commission ($/lot):", self.spin_comm)

        self.spin_spread = QDoubleSpinBox()
        self.spin_spread.setRange(0.0, 50.0)
        self.spin_spread.setDecimals(4)
        self.spin_spread.setValue(0.20 if "XAU" in self.symbol else 0.00015)
        form_cap.addRow("Spread:", self.spin_spread)

        top_grid.addWidget(grp_capital)
        main_layout.addLayout(top_grid)

        # 2. Run Backtest Button
        btn_run = QPushButton("🚀 Run Automated Backtest")
        btn_run.setStyleSheet("background-color: #2962ff; color: #ffffff; font-weight: 700; font-size: 13px; padding: 10px 16px; border-radius: 4px;")
        btn_run.clicked.connect(self._run_backtest)
        main_layout.addWidget(btn_run)

        # 3. Results Summary Grid
        self.grp_results = QGroupBox("PERFORMANCE RESULTS")
        self.grid_results = QGridLayout(self.grp_results)
        self.grid_results.setHorizontalSpacing(24)
        self.grid_results.setVerticalSpacing(8)

        self.lbl_net_profit = self._add_stat(self.grid_results, "Net Profit:", "--", 0, 0)
        self.lbl_return = self._add_stat(self.grid_results, "Return on Capital:", "--", 0, 1)
        self.lbl_profit_factor = self._add_stat(self.grid_results, "Profit Factor:", "--", 0, 2)
        self.lbl_win_rate = self._add_stat(self.grid_results, "Win Rate:", "--", 1, 0)
        self.lbl_max_dd = self._add_stat(self.grid_results, "Max Drawdown:", "--", 1, 1)
        self.lbl_trades = self._add_stat(self.grid_results, "Total Trades:", "--", 1, 2)
        self.lbl_sharpe = self._add_stat(self.grid_results, "Sharpe Ratio:", "--", 2, 0)
        self.lbl_sortino = self._add_stat(self.grid_results, "Sortino Ratio:", "--", 2, 1)
        self.lbl_expectancy = self._add_stat(self.grid_results, "Expectancy:", "--", 2, 2)

        main_layout.addWidget(self.grp_results)

        # 4. Action Buttons (HTML Tearsheet)
        action_layout = QHBoxLayout()
        self.btn_open_tearsheet = QPushButton("🌐 View Interactive HTML Tearsheet")
        self.btn_open_tearsheet.setEnabled(False)
        self.btn_open_tearsheet.setStyleSheet("background-color: #26a69a; color: #ffffff; font-weight: 700; padding: 6px 14px; border-radius: 4px;")
        self.btn_open_tearsheet.clicked.connect(self._open_tearsheet_browser)
        action_layout.addWidget(self.btn_open_tearsheet)

        self.btn_export_tearsheet = QPushButton("💾 Export Report HTML...")
        self.btn_export_tearsheet.setEnabled(False)
        self.btn_export_tearsheet.clicked.connect(self._export_tearsheet)
        action_layout.addWidget(self.btn_export_tearsheet)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        action_layout.addWidget(btn_close)

        main_layout.addLayout(action_layout)

    def _on_sizing_mode_changed(self, idx: int) -> None:
        is_fixed = (idx == 1)
        self.spin_risk.setVisible(not is_fixed)
        self.spin_fixed_lot.setVisible(is_fixed)
        self.lbl_fixed_lot.setVisible(is_fixed)

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

    def _run_backtest(self) -> None:
        if self.df is None or self.df.empty:
            QMessageBox.warning(self, "No Data", "No historical candle dataset available to backtest.")
            return

        strat_idx = self.combo_strategy.currentIndex()
        rr = self.spin_rr.value()

        if strat_idx == 0:
            strategy = FVGStrategy(risk_reward=rr)
        elif strat_idx == 1:
            strategy = MarketStructureStrategy(risk_reward=rr)
        else:
            strategy = EMACrossoverStrategy(risk_reward=rr)

        # Direction filter
        dir_text = self.combo_direction.currentText()
        if "Long Only" in dir_text:
            dir_filter = "long_only"
        elif "Short Only" in dir_text:
            dir_filter = "short_only"
        else:
            dir_filter = "both"

        # Sizing mode
        sizing_mode = "fixed_lot" if self.combo_sizing.currentIndex() == 1 else "risk_pct"

        # Data slice
        scope_idx = self.combo_scope.currentIndex()
        total_len = len(self.df)
        start_idx = 0
        if scope_idx == 1:  # Last 500
            start_idx = max(0, total_len - 500)
        elif scope_idx == 2:  # Last 1000
            start_idx = max(0, total_len - 1000)
        elif scope_idx == 3:  # Last 2000
            start_idx = max(0, total_len - 2000)
        elif scope_idx == 4:  # First 50%
            eval_df = self.df.iloc[:total_len // 2]
            start_idx = 0
        elif scope_idx == 5:  # Second 50%
            start_idx = total_len // 2

        if scope_idx == 4:
            eval_df = self.df.iloc[:total_len // 2]
        elif start_idx > 0:
            eval_df = self.df.iloc[start_idx:].reset_index(drop=True)
        else:
            eval_df = self.df

        engine = BacktestEngine(
            initial_balance=self.spin_balance.value(),
            risk_pct=self.spin_risk.value(),
            commission_per_lot=self.spin_comm.value(),
            spread=self.spin_spread.value(),
            slippage=0.05,
            sizing_mode=sizing_mode,
            fixed_lot_size=self.spin_fixed_lot.value(),
            direction_filter=dir_filter,
        )

        try:
            self.result = engine.run(strategy, eval_df, symbol=self.symbol, timeframe=self.timeframe)
            self._display_results(self.result)


            # Auto-save report to reports/
            report_dir = Path("reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"backtest_{self.symbol}_{strategy.name}.html"
            self.saved_tearsheet_path = TearsheetGenerator.save_tearsheet(self.result, str(report_path))

            self.btn_open_tearsheet.setEnabled(True)
            self.btn_export_tearsheet.setEnabled(True)

        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            QMessageBox.critical(self, "Backtest Error", f"Failed to execute backtest:\n{e}")

    def _display_results(self, res: BacktestResult) -> None:
        p_col = "#26a69a" if res.total_net_profit >= 0 else "#ef5350"
        self.lbl_net_profit.setStyleSheet(f"color: {p_col}; font-weight: 700;")
        self.lbl_net_profit.setText(f"${res.total_net_profit:+,.2f}")

        self.lbl_return.setStyleSheet(f"color: {p_col}; font-weight: 700;")
        self.lbl_return.setText(f"{res.return_pct:+,.2f} %")

        self.lbl_profit_factor.setText(f"{res.profit_factor:.2f}")
        self.lbl_win_rate.setText(f"{res.win_rate_pct:.1f} %")
        self.lbl_max_dd.setText(f"${res.max_drawdown_amount:,.2f} ({res.max_drawdown_pct:.1f}%)")
        self.lbl_trades.setText(f"{res.total_trades} ({res.winning_trades}W / {res.losing_trades}L)")
        self.lbl_sharpe.setText(f"{res.sharpe_ratio:.2f}")
        self.lbl_sortino.setText(f"{res.sortino_ratio:.2f}")
        self.lbl_expectancy.setText(f"${res.expectancy:+,.2f}")

    def _open_tearsheet_browser(self) -> None:
        if self.saved_tearsheet_path and Path(self.saved_tearsheet_path).exists():
            webbrowser.open(f"file:///{Path(self.saved_tearsheet_path).resolve().as_posix()}")

    def _export_tearsheet(self) -> None:
        if not self.result:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Performance Tearsheet", f"backtest_{self.symbol}_{self.result.strategy_name}.html", "HTML Files (*.html)"
        )
        if file_path:
            TearsheetGenerator.save_tearsheet(self.result, file_path)
            QMessageBox.information(self, "Exported", f"Tearsheet saved to:\n{file_path}")
