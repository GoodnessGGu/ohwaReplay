import numpy as np
import pandas as pd
import pytest

from src.indicators.registry import IndicatorRegistry
from src.indicators.all_indicators import (
    EMAIndicator,
    SMAIndicator,
    RSIIndicator,
    MACDIndicator,
    ATRIndicator,
    BollingerBandsIndicator,
    SmartTrailIndicator,
)


@pytest.fixture
def sample_ohlcv_df():
    np.random.seed(42)
    n = 100
    prices = 2000.0 + np.cumsum(np.random.randn(n) * 2)
    df = pd.DataFrame({
        "timestamp": 1700000000 + np.arange(n) * 300,
        "open": prices + np.random.randn(n) * 0.5,
        "high": prices + 2.0,
        "low": prices - 2.0,
        "close": prices,
        "volume": np.random.randint(100, 1000, size=n).astype(float),
    })
    return df


def test_indicator_registry():
    all_inds = IndicatorRegistry.get_all()
    assert "EMA" in all_inds
    assert "SMA" in all_inds
    assert "RSI" in all_inds
    assert "BollingerBands" in all_inds
    assert "MACD" in all_inds
    assert "ATR" in all_inds
    assert "SmartTrail" in all_inds

    ema = IndicatorRegistry.create("EMA", period=20)
    assert isinstance(ema, EMAIndicator)
    assert ema.params["period"] == 20

    st = IndicatorRegistry.create("SmartTrail", length=14, multiplier=2.0, sensitivity=3)
    assert isinstance(st, SmartTrailIndicator)
    assert st.params["length"] == 14
    assert st.params["multiplier"] == 2.0


def test_ema_calculation(sample_ohlcv_df):
    ema_ind = EMAIndicator(period=20)
    res = ema_ind.calculate(sample_ohlcv_df)
    assert "EMA_20" in res.columns
    assert len(res) == len(sample_ohlcv_df)
    assert not res["EMA_20"].isna().all()


def test_sma_calculation(sample_ohlcv_df):
    sma_ind = SMAIndicator(period=50)
    res = sma_ind.calculate(sample_ohlcv_df)
    assert "SMA_50" in res.columns
    assert len(res) == len(sample_ohlcv_df)
    assert pd.isna(res["SMA_50"].iloc[0])  # first 49 are NaN
    assert not pd.isna(res["SMA_50"].iloc[55])


def test_bollinger_bands_calculation(sample_ohlcv_df):
    bb_ind = BollingerBandsIndicator(period=20, std_dev=2.0)
    res = bb_ind.calculate(sample_ohlcv_df)
    assert "BB_middle" in res.columns
    assert "BB_upper" in res.columns
    assert "BB_lower" in res.columns
    valid_idx = 25
    assert res["BB_upper"].iloc[valid_idx] >= res["BB_middle"].iloc[valid_idx]
    assert res["BB_lower"].iloc[valid_idx] <= res["BB_middle"].iloc[valid_idx]


def test_rsi_calculation(sample_ohlcv_df):
    rsi_ind = RSIIndicator(period=14)
    res = rsi_ind.calculate(sample_ohlcv_df)
    assert "RSI_14" in res.columns
    vals = res["RSI_14"].dropna()
    assert (vals >= 0).all() and (vals <= 100).all()


def test_macd_calculation(sample_ohlcv_df):
    macd_ind = MACDIndicator(fast=12, slow=26, signal=9)
    res = macd_ind.calculate(sample_ohlcv_df)
    assert "MACD_line" in res.columns
    assert "MACD_signal" in res.columns
    assert "MACD_hist" in res.columns


def test_atr_calculation(sample_ohlcv_df):
    atr_ind = ATRIndicator(period=14)
    res = atr_ind.calculate(sample_ohlcv_df)
    assert "ATR_14" in res.columns
    vals = res["ATR_14"].dropna()
    assert (vals > 0).all()


def test_smart_trail_calculation(sample_ohlcv_df):
    st_ind = SmartTrailIndicator(length=14, multiplier=2.0, sensitivity=3)
    res = st_ind.calculate(sample_ohlcv_df)
    assert "SmartTrail" in res.columns
    assert "SmartTrend" in res.columns
    assert "BullSignal" in res.columns
    assert "BearSignal" in res.columns
    assert len(res) == len(sample_ohlcv_df)
    assert not res["SmartTrail"].isna().all()
    # Check trend is either 1 or -1
    assert set(res["SmartTrend"].unique()).issubset({1, -1})
    # Check signal booleans
    assert res["BullSignal"].dtype == bool
    assert res["BearSignal"].dtype == bool
