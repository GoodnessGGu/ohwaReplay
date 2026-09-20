from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from src.core.position import Position
from src.utils.constants import Direction


@dataclass
class TradeStatistics:
    """Comprehensive statistical metrics derived from trade history."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    break_even_trades: int = 0
    win_rate_pct: float = 0.0
    loss_rate_pct: float = 0.0

    total_net_profit: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0

    max_drawdown_amount: float = 0.0
    max_drawdown_pct: float = 0.0

    average_trade: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    win_loss_ratio: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    expectancy: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0

    long_trades_count: int = 0
    long_win_rate_pct: float = 0.0
    long_profit: float = 0.0

    short_trades_count: int = 0
    short_win_rate_pct: float = 0.0
    short_profit: float = 0.0

    equity_curve: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


class StatisticsCalculator:
    """Calculates robust trading performance metrics."""

    @staticmethod
    def calculate(trades: List[Position], initial_balance: float = 10000.0) -> TradeStatistics:
        stats = TradeStatistics()
        if not trades:
            stats.equity_curve = [initial_balance]
            return stats

        stats.total_trades = len(trades)
        net_pnls = [t.net_pnl for t in trades]

        wins = [p for p in net_pnls if p > 0]
        losses = [p for p in net_pnls if p < 0]
        be = [p for p in net_pnls if p == 0]

        stats.winning_trades = len(wins)
        stats.losing_trades = len(losses)
        stats.break_even_trades = len(be)

        stats.win_rate_pct = round((stats.winning_trades / stats.total_trades) * 100.0, 2)
        stats.loss_rate_pct = round((stats.losing_trades / stats.total_trades) * 100.0, 2)

        stats.gross_profit = round(sum(wins), 2)
        stats.gross_loss = round(abs(sum(losses)), 2)
        stats.total_net_profit = round(sum(net_pnls), 2)

        if stats.gross_loss > 0:
            stats.profit_factor = round(stats.gross_profit / stats.gross_loss, 2)
        else:
            stats.profit_factor = round(stats.gross_profit, 2) if stats.gross_profit > 0 else 0.0

        stats.average_trade = round(stats.total_net_profit / stats.total_trades, 2)
        stats.average_win = round(stats.gross_profit / stats.winning_trades, 2) if stats.winning_trades > 0 else 0.0
        stats.average_loss = round(stats.gross_loss / stats.losing_trades, 2) if stats.losing_trades > 0 else 0.0
        stats.win_loss_ratio = round(stats.average_win / (stats.average_loss + 1e-9), 2) if stats.average_loss > 0 else 0.0

        stats.largest_win = round(max(wins), 2) if wins else 0.0
        stats.largest_loss = round(min(losses), 2) if losses else 0.0

        # Expectancy = (Win% * AvgWin) - (Loss% * AvgLoss)
        win_prob = stats.winning_trades / stats.total_trades
        loss_prob = stats.losing_trades / stats.total_trades
        stats.expectancy = round((win_prob * stats.average_win) - (loss_prob * stats.average_loss), 2)

        # Streaks
        max_cw = 0
        current_cw = 0
        max_cl = 0
        current_cl = 0
        for p in net_pnls:
            if p > 0:
                current_cw += 1
                current_cl = 0
            elif p < 0:
                current_cl += 1
                current_cw = 0
            else:
                current_cw = 0
                current_cl = 0
            max_cw = max(max_cw, current_cw)
            max_cl = max(max_cl, current_cl)
        stats.max_consecutive_wins = max_cw
        stats.max_consecutive_losses = max_cl

        # Equity Curve and Max Drawdown calculation
        equity = initial_balance
        peak = initial_balance
        max_dd_amt = 0.0
        max_dd_pct = 0.0
        eq_curve = [initial_balance]

        for pnl in net_pnls:
            equity += pnl
            eq_curve.append(round(equity, 2))
            if equity > peak:
                peak = equity
            dd_amt = peak - equity
            dd_pct = (dd_amt / peak) * 100.0 if peak > 0 else 0.0
            if dd_amt > max_dd_amt:
                max_dd_amt = dd_amt
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct

        stats.equity_curve = eq_curve
        stats.max_drawdown_amount = round(max_dd_amt, 2)
        stats.max_drawdown_pct = round(max_dd_pct, 2)

        # Long vs Short
        longs = [t for t in trades if t.direction == Direction.BUY]
        shorts = [t for t in trades if t.direction == Direction.SELL]

        stats.long_trades_count = len(longs)
        long_wins = len([t for t in longs if t.net_pnl > 0])
        stats.long_win_rate_pct = round((long_wins / len(longs)) * 100.0, 2) if longs else 0.0
        stats.long_profit = round(sum(t.net_pnl for t in longs), 2)

        stats.short_trades_count = len(shorts)
        short_wins = len([t for t in shorts if t.net_pnl > 0])
        stats.short_win_rate_pct = round((short_wins / len(shorts)) * 100.0, 2) if shorts else 0.0
        stats.short_profit = round(sum(t.net_pnl for t in shorts), 2)

        return stats
