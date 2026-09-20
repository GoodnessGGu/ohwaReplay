from typing import Any, Dict, List, Optional
import pandas as pd
from src.analytics.statistics import StatisticsCalculator, TradeStatistics
from src.core.position import Position


class AnalyticsEngine:
    """Computes time-series curves and breakdown metrics from trade history."""

    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance

    def compute_equity_curve(self, trades: List[Position]) -> List[Dict[str, Any]]:
        """Generates cumulative equity progression data."""
        data = [{"trade_num": 0, "equity": self.initial_balance, "pnl": 0.0, "time": None}]
        eq = self.initial_balance
        for i, t in enumerate(trades, 1):
            eq += t.net_pnl
            data.append({
                "trade_num": i,
                "equity": round(eq, 2),
                "pnl": t.net_pnl,
                "time": t.close_time.isoformat() if t.close_time else None,
            })
        return data

    def compute_drawdown_curve(self, trades: List[Position]) -> List[Dict[str, Any]]:
        """Generates drawdown progression data."""
        data = []
        eq = self.initial_balance
        peak = self.initial_balance

        for i, t in enumerate(trades, 1):
            eq += t.net_pnl
            if eq > peak:
                peak = eq
            dd_amt = peak - eq
            dd_pct = (dd_amt / peak) * 100.0 if peak > 0 else 0.0
            data.append({
                "trade_num": i,
                "drawdown_amount": round(dd_amt, 2),
                "drawdown_pct": round(dd_pct, 2),
            })
        return data

    def get_full_analysis(self, trades: List[Position]) -> Dict[str, Any]:
        """Returns comprehensive analytics summary."""
        stats = StatisticsCalculator.calculate(trades, self.initial_balance)
        return {
            "statistics": stats.to_dict(),
            "equity_curve": self.compute_equity_curve(trades),
            "drawdown_curve": self.compute_drawdown_curve(trades),
        }
