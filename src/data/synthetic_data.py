from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd

from src.utils.constants import TIMEFRAME_MINUTES


class SyntheticDataGenerator:
    """Generates realistic synthetic OHLCV market data for testing and offline replay."""

    PRESETS: Dict[str, Dict[str, Any]] = {
        "XAUUSD": {
            "start_price": 2000.0,
            "volatility": 1.5,
            "trend": 0.00005,
            "digits": 2,
            "base_volume": 1000.0,
            "spread": 0.20,
        },
        "EURUSD": {
            "start_price": 1.0850,
            "volatility": 0.0006,
            "trend": 0.0,
            "digits": 5,
            "base_volume": 5000.0,
            "spread": 0.0001,
        },
        "GBPUSD": {
            "start_price": 1.2650,
            "volatility": 0.0008,
            "trend": 0.00002,
            "digits": 5,
            "base_volume": 4000.0,
            "spread": 0.00015,
        },
        "USDJPY": {
            "start_price": 150.00,
            "volatility": 0.10,
            "trend": -0.00002,
            "digits": 3,
            "base_volume": 3500.0,
            "spread": 0.01,
        },
        "BTCUSD": {
            "start_price": 65000.0,
            "volatility": 150.0,
            "trend": 0.0002,
            "digits": 2,
            "base_volume": 50.0,
            "spread": 5.0,
        },
    }

    @classmethod
    def generate(
        cls,
        symbol: str = "XAUUSD",
        num_candles: int = 1000,
        timeframe: str = "5m",
        start_price: Optional[float] = None,
        volatility: Optional[float] = None,
        trend: Optional[float] = None,
        seed: Optional[int] = 42,
        start_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Generates realistic synthetic OHLCV candles deterministically.
        """
        if seed is not None:
            np.random.seed(seed)

        preset = cls.PRESETS.get(symbol.upper(), cls.PRESETS["XAUUSD"])
        price = start_price if start_price is not None else preset["start_price"]
        vol = volatility if volatility is not None else preset["volatility"]
        drift = trend if trend is not None else preset["trend"]
        digits = preset.get("digits", 2)
        base_vol = preset.get("base_volume", 1000.0)

        tf_minutes = TIMEFRAME_MINUTES.get(timeframe, 5)
        if start_time is None:
            # Start from a fixed reference past date for reproducible timestamps
            start_time = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)

        records = []
        current_time = start_time

        # Intrabar random steps to build realistic wicks and body
        for _ in range(num_candles):
            open_p = price
            # Candle returns with drift and volatility
            pct_change = np.random.normal(drift, 1.0)
            price_change = vol * pct_change
            close_p = max(open_p * 0.01, open_p + price_change)

            # High and Low wicks
            wick_high = abs(np.random.exponential(vol * 0.7))
            wick_low = abs(np.random.exponential(vol * 0.7))

            high_p = max(open_p, close_p) + wick_high
            low_p = min(open_p, close_p) - wick_low
            low_p = max(low_p, open_p * 0.001)  # prevent <= 0

            # Round prices to instrument precision
            open_p = round(open_p, digits)
            high_p = round(high_p, digits)
            low_p = round(low_p, digits)
            close_p = round(close_p, digits)

            # Ensure strict OHLC logic post-rounding
            high_p = max(high_p, open_p, close_p)
            low_p = min(low_p, open_p, close_p)

            # Volume
            vol_noise = np.random.lognormal(0.0, 0.5)
            volume = round(base_vol * vol_noise * (1.0 + abs(close_p - open_p) / (vol + 1e-9)), 2)

            ts_sec = int(current_time.timestamp())
            records.append({
                "timestamp": ts_sec,
                "datetime": current_time,
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
                "volume": volume,
            })

            # Next candle start price is previous close with tiny micro-gap
            micro_gap = np.random.normal(0, vol * 0.02)
            price = max(close_p * 0.01, close_p + micro_gap)
            current_time += timedelta(minutes=tf_minutes)

        df = pd.DataFrame(records)
        return df
