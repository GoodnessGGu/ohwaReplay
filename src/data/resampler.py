from typing import Dict
import pandas as pd

from src.utils.constants import TIMEFRAMES, TIMEFRAME_MINUTES
from src.data.data_validator import DataValidationError


class TimeframeResampler:
    """Resamples OHLCV candle datasets to higher timeframes."""

    PANDAS_FREQS: Dict[str, str] = {
        "1m": "1min",
        "3m": "3min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "1d": "1D",
    }

    @classmethod
    def resample(cls, df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
        """
        Resamples a 1m or base OHLCV dataframe to a target timeframe.
        target_timeframe must be one of: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d.
        """
        if target_timeframe not in cls.PANDAS_FREQS:
            raise DataValidationError(
                f"Unsupported timeframe: '{target_timeframe}'. Supported: {', '.join(TIMEFRAMES)}"
            )

        if df.empty:
            return df.copy()

        # If 1m and target is 1m, return normalized copy
        if target_timeframe == "1m":
            return df.copy()

        df_work = df.copy()
        if "datetime" not in df_work.columns:
            if "timestamp" in df_work.columns:
                df_work["datetime"] = pd.to_datetime(df_work["timestamp"], unit="s", utc=True)
            else:
                raise DataValidationError("Dataframe must contain 'datetime' or 'timestamp' for resampling.")

        df_work = df_work.set_index("datetime").sort_index()

        freq = cls.PANDAS_FREQS[target_timeframe]

        resampled = df_work.resample(freq, closed="left", label="left").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna(subset=["open", "high", "low", "close"]).reset_index()

        # Update timestamp to integer seconds
        resampled["timestamp"] = (resampled["datetime"].astype("int64") // 10**9).astype("int64")

        canonical_cols = ["timestamp", "datetime", "open", "high", "low", "close", "volume"]
        return resampled[canonical_cols]
