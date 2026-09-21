import pytest
from src.data.live_feed import LiveFeedWorker


def test_live_feed_worker_init():
    worker = LiveFeedWorker(symbol="BTCUSD", timeframe="5m")
    assert worker.symbol == "BTCUSD"
    assert worker.timeframe == "5m"
    assert worker._timeframe_to_seconds("5m") == 300
    assert worker._timeframe_to_seconds("1h") == 3600
