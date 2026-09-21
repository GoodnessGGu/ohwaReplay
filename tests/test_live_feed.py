import pytest
import pandas as pd
from src.data.live_feed import LiveFeedWorker, LiveDataLoader


def test_live_feed_worker_init():
    worker = LiveFeedWorker(symbol="BTCUSD", timeframe="5m", interval_ms=200)
    assert worker.symbol == "BTCUSD"
    assert worker.timeframe == "5m"
    assert worker.interval_ms == 200
    assert worker._timeframe_to_seconds("5m") == 300
    assert worker._timeframe_to_seconds("15m") == 900
    assert worker._timeframe_to_seconds("1h") == 3600
    assert worker._timeframe_to_seconds("1d") == 86400


def test_live_feed_pip_size_and_decimals():
    worker_gold = LiveFeedWorker(symbol="XAUUSD", timeframe="1m")
    assert worker_gold._pip_size == 0.05
    assert worker_gold._decimals == 2

    worker_fx = LiveFeedWorker(symbol="EURUSD", timeframe="15m")
    assert worker_fx._pip_size == 0.0001
    assert worker_fx._decimals == 5

    worker_jpy = LiveFeedWorker(symbol="USDJPY", timeframe="5m")
    assert worker_jpy._pip_size == 0.01
    assert worker_jpy._decimals == 3


def test_live_data_loader_merge():
    df1 = pd.DataFrame([
        {"timestamp": 100, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10},
        {"timestamp": 200, "open": 1.5, "high": 2.5, "low": 1.0, "close": 2.0, "volume": 15},
    ])
    df2 = pd.DataFrame([
        {"timestamp": 200, "open": 1.5, "high": 2.5, "low": 1.0, "close": 2.0, "volume": 15},
        {"timestamp": 300, "open": 2.0, "high": 3.0, "low": 1.5, "close": 2.5, "volume": 20},
    ])
    merged = LiveDataLoader.merge_with_live(df1, df2)
    assert len(merged) == 3
    assert list(merged["timestamp"]) == [100, 200, 300]


def test_fill_gap_to_now():
    import time
    now_ts = int(time.time())
    past_ts = now_ts - 1800  # 6 bars of 5m in the past
    df = pd.DataFrame([
        {"timestamp": past_ts - 300, "open": 2000.0, "high": 2005.0, "low": 1995.0, "close": 2002.0, "volume": 100},
        {"timestamp": past_ts, "open": 2002.0, "high": 2008.0, "low": 2000.0, "close": 2005.0, "volume": 120},
    ])
    filled = LiveDataLoader.fill_gap_to_now(df, timeframe="5m", symbol="XAUUSD")
    assert len(filled) >= len(df)
    assert filled.iloc[-1]["timestamp"] >= past_ts
