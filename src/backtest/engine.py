from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from src.backtest.strategy import BaseStrategy
from src.core.pnl import calculate_pnl
from src.core.risk import RiskCalculator
from src.utils.constants import Direction


@dataclass
class BacktestTrade:
    id: int
    entry_index: int
    exit_index: int
    entry_time: Any
    exit_time: Any
    direction: Direction
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    lot_size: float
    gross_pnl: float
    net_pnl: float
    commission: float
    exit_reason: str
    comment: str


@dataclass
class BacktestResult:
    strategy_name: str
    symbol: str
    timeframe: str
    initial_balance: float
    final_balance: float
    total_net_profit: float
    return_pct: float
    profit_factor: float
    win_rate_pct: float
    loss_rate_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    max_drawdown_amount: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    expectancy: float
    avg_win: float
    avg_loss: float
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = self.__dict__.copy()
        d["trades"] = [t.__dict__.copy() for t in self.trades]
        return d


class BacktestEngine:
    """
    High-performance event-driven backtesting engine for quantitative evaluation.
    """

    def __init__(
        self,
        initial_balance: float = 10000.0,
        risk_pct: float = 1.0,
        commission_per_lot: float = 7.0,
        spread: float = 0.20,
        slippage: float = 0.05,
        point_value: float = 100.0,
        sizing_mode: str = "risk_pct",
        fixed_lot_size: float = 1.0,
        direction_filter: str = "both",
        leverage: int = 100,
    ):
        self.initial_balance = initial_balance
        self.risk_pct = risk_pct
        self.commission_per_lot = commission_per_lot
        self.spread = spread
        self.slippage = slippage
        self.point_value = point_value
        self.sizing_mode = sizing_mode
        self.fixed_lot_size = max(0.01, fixed_lot_size)
        self.direction_filter = direction_filter.lower()
        self.leverage = max(1, leverage)

    def run(
        self,
        strategy: BaseStrategy,
        df: pd.DataFrame,
        symbol: str = "XAUUSD",
        timeframe: str = "5m",
        start_index: int = 0,
    ) -> BacktestResult:
        if df.empty or len(df) < 10:
            return BacktestResult(
                strategy_name=strategy.name,
                symbol=symbol,
                timeframe=timeframe,
                initial_balance=self.initial_balance,
                final_balance=self.initial_balance,
                total_net_profit=0.0,
                return_pct=0.0,
                profit_factor=0.0,
                win_rate_pct=0.0,
                loss_rate_pct=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                max_drawdown_amount=0.0,
                max_drawdown_pct=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                expectancy=0.0,
                avg_win=0.0,
                avg_loss=0.0,
            )

        if start_index > 0 and start_index < len(df) - 10:
            eval_df = df.iloc[start_index:].reset_index(drop=True)
        else:
            eval_df = df.reset_index(drop=True)

        signals_df = strategy.generate_signals(eval_df)

        n = len(eval_df)
        balance = self.initial_balance
        equity = self.initial_balance
        peak_equity = self.initial_balance
        max_dd_amt = 0.0
        max_dd_pct = 0.0

        trades: List[BacktestTrade] = []
        equity_curve: List[Dict[str, Any]] = []

        timestamps = eval_df["timestamp"].values
        highs = eval_df["high"].values
        lows = eval_df["low"].values
        closes = eval_df["close"].values
        sig_arr = signals_df["signal"].values
        sl_arr = signals_df["stop_loss"].values
        tp_arr = signals_df["take_profit"].values
        comm_arr = signals_df["comment"].values

        active_trade: Optional[Dict[str, Any]] = None
        trade_id = 1

        for i in range(n):
            ts = int(timestamps[i])
            c_high = highs[i]
            c_low = lows[i]
            c_close = closes[i]

            # 1. Evaluate open active trade
            if active_trade is not None:
                is_long = (active_trade["direction"] == Direction.BUY)
                sl = active_trade["stop_loss"]
                tp = active_trade["take_profit"]

                hit_sl = (c_low <= sl) if is_long else (c_high >= sl)
                hit_tp = (c_high >= tp) if is_long else (c_low <= tp)

                if hit_sl or hit_tp:
                    exit_price = sl if hit_sl else tp
                    # Apply half spread + slippage
                    if is_long:
                        fill_exit = exit_price - (self.spread / 2.0) - self.slippage
                    else:
                        fill_exit = exit_price + (self.spread / 2.0) + self.slippage

                    gross = calculate_pnl(
                        active_trade["direction"],
                        active_trade["entry_price"],
                        fill_exit,
                        active_trade["lot_size"],
                        self.point_value,
                    )
                    comm = round(self.commission_per_lot * active_trade["lot_size"], 2)
                    net = round(gross - comm, 2)
                    balance += net

                    bt_trade = BacktestTrade(
                        id=active_trade["id"],
                        entry_index=active_trade["entry_index"],
                        exit_index=i,
                        entry_time=active_trade["entry_time"],
                        exit_time=ts,
                        direction=active_trade["direction"],
                        entry_price=active_trade["entry_price"],
                        exit_price=round(fill_exit, 5),
                        stop_loss=sl,
                        take_profit=tp,
                        lot_size=active_trade["lot_size"],
                        gross_pnl=gross,
                        net_pnl=net,
                        commission=comm,
                        exit_reason="TP" if hit_tp else "SL",
                        comment=active_trade["comment"],
                    )
                    trades.append(bt_trade)
                    active_trade = None

            # 2. Check for new trade entry if no active position
            if active_trade is None and i < n - 1:
                sig = sig_arr[i]
                # Check direction filter
                if sig == 1 and self.direction_filter in ("short_only", "short"):
                    sig = 0
                elif sig == -1 and self.direction_filter in ("long_only", "long"):
                    sig = 0

                if sig != 0 and pd.notna(sl_arr[i]) and pd.notna(tp_arr[i]):
                    direction = Direction.BUY if sig == 1 else Direction.SELL
                    raw_entry = c_close
                    sl = sl_arr[i]
                    tp = tp_arr[i]

                    # Sizing via risk calculator or fixed lot
                    if self.sizing_mode in ("fixed_lot", "fixed"):
                        lot = round(self.fixed_lot_size, 2)
                    else:
                        lot = RiskCalculator.calculate_lot_size(
                            balance=balance,
                            risk_pct=self.risk_pct,
                            entry_price=raw_entry,
                            stop_loss_price=sl,
                            point_value=self.point_value,
                        )

                    if lot >= 0.01:
                        fill_entry = raw_entry + (self.spread / 2.0) + self.slippage if direction == Direction.BUY else raw_entry - (self.spread / 2.0) - self.slippage
                        active_trade = {
                            "id": trade_id,
                            "entry_index": i,
                            "entry_time": ts,
                            "direction": direction,
                            "entry_price": round(fill_entry, 5),
                            "stop_loss": sl,
                            "take_profit": tp,
                            "lot_size": lot,
                            "comment": comm_arr[i],
                        }
                        trade_id += 1

            # Track equity curve
            equity = balance
            if active_trade is not None:
                unrealized = calculate_pnl(
                    active_trade["direction"],
                    active_trade["entry_price"],
                    c_close,
                    active_trade["lot_size"],
                    self.point_value,
                )
                equity += unrealized

            if equity > peak_equity:
                peak_equity = equity
            dd_amt = peak_equity - equity
            dd_pct = (dd_amt / peak_equity) * 100.0 if peak_equity > 0 else 0.0
            if dd_amt > max_dd_amt:
                max_dd_amt = dd_amt
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct

            if i % max(1, n // 500) == 0 or i == n - 1:
                equity_curve.append({
                    "time": ts,
                    "equity": round(equity, 2),
                    "balance": round(balance, 2),
                    "drawdown_pct": round(dd_pct, 2),
                })

        # Calculate statistics
        net_profits = [t.net_pnl for t in trades]
        wins = [p for p in net_profits if p > 0]
        losses = [p for p in net_profits if p < 0]

        total_net = round(sum(net_profits), 2)
        ret_pct = round((total_net / self.initial_balance) * 100.0, 2)
        gross_p = sum(wins)
        gross_l = abs(sum(losses))
        pf = round(gross_p / gross_l, 2) if gross_l > 0 else (round(gross_p, 2) if gross_p > 0 else 0.0)

        n_trades = len(trades)
        win_rate = round((len(wins) / n_trades) * 100.0, 2) if n_trades > 0 else 0.0
        loss_rate = round((len(losses) / n_trades) * 100.0, 2) if n_trades > 0 else 0.0

        avg_w = round(gross_p / len(wins), 2) if wins else 0.0
        avg_l = round(gross_l / len(losses), 2) if losses else 0.0
        win_p = len(wins) / n_trades if n_trades > 0 else 0.0
        loss_p = len(losses) / n_trades if n_trades > 0 else 0.0
        expectancy = round((win_p * avg_w) - (loss_p * avg_l), 2)

        # Sharpe & Sortino ratios (annualized returns / standard deviation)
        if len(net_profits) > 2:
            returns = np.array(net_profits) / self.initial_balance
            mean_ret = np.mean(returns)
            std_ret = np.std(returns) + 1e-9
            sharpe = round(float(np.sqrt(252) * (mean_ret / std_ret)), 2)

            downside = returns[returns < 0]
            downside_std = np.std(downside) + 1e-9 if len(downside) > 0 else std_ret
            sortino = round(float(np.sqrt(252) * (mean_ret / downside_std)), 2)
        else:
            sharpe = 0.0
            sortino = 0.0

        return BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            timeframe=timeframe,
            initial_balance=self.initial_balance,
            final_balance=round(balance, 2),
            total_net_profit=total_net,
            return_pct=ret_pct,
            profit_factor=pf,
            win_rate_pct=win_rate,
            loss_rate_pct=loss_rate,
            total_trades=n_trades,
            winning_trades=len(wins),
            losing_trades=len(losses),
            max_drawdown_amount=round(max_dd_amt, 2),
            max_drawdown_pct=round(max_dd_pct, 2),
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            expectancy=expectancy,
            avg_win=avg_w,
            avg_loss=avg_l,
            trades=trades,
            equity_curve=equity_curve,
        )
