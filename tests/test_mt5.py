import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from src.data.mt5_connector import MT5Connector, mt5_connector
from src.data.live_feed import LiveDataLoader, LiveFeedWorker


def test_mt5_connector_singleton():
    c1 = MT5Connector()
    c2 = MT5Connector()
    assert c1 is c2
    assert c1 is mt5_connector


def test_mt5_symbol_resolution():
    conn = MT5Connector()
    # When disconnected, returns None
    assert conn.resolve_symbol("EURUSD") is None

    # Test symbol mapping when cache populated
    conn._connected = True
    conn._symbol_cache = {
        "XAUUSD": "XAUUSD",
        "EURUSD.PRO": "EURUSD.pro",
        "GOLD": "GOLD",
        "GBPUSD": "GBPUSD",
    }
    assert conn.resolve_symbol("EURUSD") == "EURUSD.pro"
    assert conn.resolve_symbol("XAUUSD") == "XAUUSD"
    conn._connected = False


def test_mt5_timeframe_mapping():
    conn = MT5Connector()
    # Test internal mapping
    m1 = conn._map_timeframe("1m")
    m5 = conn._map_timeframe("5m")
    h1 = conn._map_timeframe("1h")
    d1 = conn._map_timeframe("1d")
    assert m1 != m5
    assert m5 != h1
    assert h1 != d1


def test_live_data_loader_with_mt5_fallback():
    # When MT5 is not connected, LiveDataLoader falls back to public feed cleanly
    df = LiveDataLoader.fetch_latest_candles("BTCUSD", "5m", limit=5)
    assert df is not None
    assert not df.empty
    assert "timestamp" in df.columns
    assert "close" in df.columns
