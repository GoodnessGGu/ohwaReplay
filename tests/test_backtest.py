from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import BacktestEngine
from src.backtest.strategies import EMACrossoverStrategy, FVGStrategy, MarketStructureStrategy
from src.backtest.tearsheet import TearsheetGenerator


@pytest.fixture
def backtest_ohlcv_df():
    np.random.seed(42)
    n = 300
    prices = 2000.0 + np.cumsum(np.random.randn(n) * 3)
    df = pd.DataFrame({
        "timestamp": 1700000000 + np.arange(n) * 300,
        "open": prices + np.random.randn(n) * 0.5,
        "high": prices + 3.0,
        "low": prices - 3.0,
        "close": prices,
        "volume": np.random.randint(100, 1000, size=n).astype(float),
    })
    return df


def test_fvg_strategy_backtest(backtest_ohlcv_df):
    strat = FVGStrategy(risk_reward=2.0)
    engine = BacktestEngine(initial_balance=10000.0, risk_pct=1.0)
    res = engine.run(strat, backtest_ohlcv_df)

    assert res.strategy_name == "FVG_Retest"
    assert res.initial_balance == 10000.0
    assert len(res.equity_curve) > 0
    assert isinstance(res.total_net_profit, float)


def test_market_structure_strategy_backtest(backtest_ohlcv_df):
    strat = MarketStructureStrategy(swing_length=3, risk_reward=2.5)
    engine = BacktestEngine(initial_balance=10000.0, risk_pct=1.0)
    res = engine.run(strat, backtest_ohlcv_df)

    assert res.strategy_name == "MarketStructure_Breakout"
    assert res.win_rate_pct >= 0.0


def test_ema_cross_strategy_backtest(backtest_ohlcv_df):
    strat = EMACrossoverStrategy(fast_period=9, slow_period=21, risk_reward=2.0)
    engine = BacktestEngine(initial_balance=10000.0, risk_pct=1.0)
    res = engine.run(strat, backtest_ohlcv_df)

    assert res.strategy_name == "EMA_Cross"


def test_tearsheet_html_generation(backtest_ohlcv_df, tmp_path):
    strat = FVGStrategy()
    engine = BacktestEngine()
    res = engine.run(strat, backtest_ohlcv_df)

    html = TearsheetGenerator.generate_html(res)
    assert "<!DOCTYPE html>" in html
    assert "FVG_Retest" in html
    assert "Cumulative Equity Curve" in html

    out_file = tmp_path / "tearsheet.html"
    saved_path = TearsheetGenerator.save_tearsheet(res, str(out_file))
    assert Path(saved_path).exists()
