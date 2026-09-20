import pytest
from datetime import datetime
from src.core.position import Position
from src.analytics.statistics import StatisticsCalculator
from src.analytics.analytics import AnalyticsEngine
from src.utils.constants import Direction, PositionStatus, CloseReason


def test_statistics_calculator():
    # Trade 1: +$300 (Net $290 after $10 comm)
    t1 = Position(direction=Direction.BUY, lot_size=1.0, commission=10.0, status=PositionStatus.CLOSED)
    t1.realized_pnl = 300.0

    # Trade 2: -$100 (Net -$110 after $10 comm)
    t2 = Position(direction=Direction.SELL, lot_size=1.0, commission=10.0, status=PositionStatus.CLOSED)
    t2.realized_pnl = -100.0

    # Trade 3: +$500 (Net $490 after $10 comm)
    t3 = Position(direction=Direction.BUY, lot_size=1.0, commission=10.0, status=PositionStatus.CLOSED)
    t3.realized_pnl = 500.0

    stats = StatisticsCalculator.calculate([t1, t2, t3], initial_balance=10000.0)

    assert stats.total_trades == 3
    assert stats.winning_trades == 2
    assert stats.losing_trades == 1
    assert pytest.approx(stats.win_rate_pct, 0.1) == 66.67
    assert stats.total_net_profit == 290.0 - 110.0 + 490.0  # 670.0
    assert stats.gross_profit == 290.0 + 490.0  # 780.0
    assert stats.gross_loss == 110.0
    assert pytest.approx(stats.profit_factor, 0.05) == 7.09
    assert stats.max_consecutive_wins == 1
    assert stats.long_trades_count == 2
    assert stats.short_trades_count == 1


def test_analytics_engine_curves():
    engine = AnalyticsEngine(initial_balance=10000.0)
    t1 = Position(status=PositionStatus.CLOSED, commission=0.0)
    t1.realized_pnl = 500.0
    t2 = Position(status=PositionStatus.CLOSED, commission=0.0)
    t2.realized_pnl = -200.0

    eq_curve = engine.compute_equity_curve([t1, t2])
    assert len(eq_curve) == 3
    assert eq_curve[0]["equity"] == 10000.0
    assert eq_curve[1]["equity"] == 10500.0
    assert eq_curve[2]["equity"] == 10300.0

    dd_curve = engine.compute_drawdown_curve([t1, t2])
    assert len(dd_curve) == 2
    assert dd_curve[0]["drawdown_amount"] == 0.0
    assert dd_curve[1]["drawdown_amount"] == 200.0
