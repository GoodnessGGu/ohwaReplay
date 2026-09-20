import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from src.data.data_validator import DataValidator, DataValidationError
from src.data.data_loader import DataLoader
from src.data.resampler import TimeframeResampler
from src.data.synthetic_data import SyntheticDataGenerator


def test_synthetic_data_generation():
    df = SyntheticDataGenerator.generate(symbol="XAUUSD", num_candles=100, timeframe="5m", seed=123)
    assert len(df) == 100
    assert "timestamp" in df.columns
    assert "open" in df.columns
    assert "high" in df.columns
    assert "low" in df.columns
    assert "close" in df.columns
    assert "volume" in df.columns

    # Verify OHLC relationships
    assert (df["high"] >= df["low"]).all()
    assert (df["high"] >= df["open"]).all()
    assert (df["high"] >= df["close"]).all()
    assert (df["low"] <= df["open"]).all()
    assert (df["low"] <= df["close"]).all()
    assert (df["volume"] >= 0).all()


def test_data_validator_valid():
    df = SyntheticDataGenerator.generate(symbol="EURUSD", num_candles=50, timeframe="1m", seed=42)
    is_valid, errors = DataValidator.validate(df)
    assert is_valid is True
    assert len(errors) == 0


def test_data_validator_invalid_ohlc():
    df = pd.DataFrame({
        "timestamp": [1700000000, 1700000060],
        "open": [100.0, 105.0],
        "high": [95.0, 110.0],  # high < open
        "low": [90.0, 100.0],
        "close": [98.0, 108.0],
        "volume": [10, 20]
    })
    is_valid, errors = DataValidator.validate(df)
    assert is_valid is False
    assert any("High < Open" in e for e in errors)


def test_data_validator_missing_column():
    df = pd.DataFrame({
        "timestamp": [1700000000],
        "open": [100.0],
        "low": [90.0],
        "close": [98.0],
    })
    is_valid, errors = DataValidator.validate(df)
    assert is_valid is False
    assert any("Missing required column" in e for e in errors)


def test_resampler():
    # 15 1-minute candles to 5m
    df_1m = SyntheticDataGenerator.generate(symbol="XAUUSD", num_candles=15, timeframe="1m", seed=99)
    df_5m = TimeframeResampler.resample(df_1m, "5m")
    assert len(df_5m) == 3

    # Check aggregation correctness
    first_chunk = df_1m.iloc[0:5]
    assert df_5m.iloc[0]["open"] == first_chunk.iloc[0]["open"]
    assert df_5m.iloc[0]["high"] == first_chunk["high"].max()
    assert df_5m.iloc[0]["low"] == first_chunk["low"].min()
    assert df_5m.iloc[0]["close"] == first_chunk.iloc[-1]["close"]
    assert pytest.approx(df_5m.iloc[0]["volume"]) == first_chunk["volume"].sum()


def test_data_loader_csv(tmp_path):
    df_orig = SyntheticDataGenerator.generate(symbol="BTCUSD", num_candles=50, timeframe="5m", seed=7)
    csv_file = tmp_path / "test_btc.csv"
    df_orig.to_csv(csv_file, index=False)

    df_loaded = DataLoader.load_csv(csv_file)
    assert len(df_loaded) == 50
    assert df_loaded.iloc[0]["close"] == df_orig.iloc[0]["close"]


def test_historical_multi_timeframe_consistency():
    from src.data.collector import HistoricalDataCollector

    # Create dummy 1h dataset
    df_1h = pd.DataFrame({
        "timestamp": [1735689600, 1735693200], # 2 hours
        "datetime": [
            pd.to_datetime(1735689600, unit="s", utc=True),
            pd.to_datetime(1735693200, unit="s", utc=True),
        ],
        "open": [2000.0, 2020.0],
        "high": [2030.0, 2045.0],
        "low": [1990.0, 2015.0],
        "close": [2020.0, 2040.0],
        "volume": [1200.0, 1500.0],
    })

    # Generate 1m base
    df_1m = HistoricalDataCollector.generate_consistent_base_1m(df_1h, symbol="XAUUSD", seed=42)
    assert len(df_1m) == 120 # 60 min * 2 hours

    # Resample 1m back to 1h
    df_resampled_1h = TimeframeResampler.resample(df_1m, "1h")
    assert len(df_resampled_1h) == 2

    # Verify exact equality of 1h OHLC
    assert df_resampled_1h.iloc[0]["open"] == df_1h.iloc[0]["open"]
    assert df_resampled_1h.iloc[0]["high"] == df_1h.iloc[0]["high"]
    assert df_resampled_1h.iloc[0]["low"] == df_1h.iloc[0]["low"]
    assert df_resampled_1h.iloc[0]["close"] == df_1h.iloc[0]["close"]
