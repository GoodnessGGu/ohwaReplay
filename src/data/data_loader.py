import os
from pathlib import Path
from typing import Optional, Tuple, Union
import pandas as pd
import numpy as np

from src.data.data_validator import DataValidator, DataValidationError
from src.utils.logger import logger


class DataLoader:
    """Loads and standardizes OHLCV market data from various sources."""

    @staticmethod
    def load_csv(file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Loads, validates, and normalizes a CSV file containing OHLCV candles.
        Raises DataValidationError with user-friendly error messages if invalid.
        """
        path = Path(file_path)
        if not path.exists():
            raise DataValidationError(f"File not found: {file_path}")

        try:
            df = pd.read_csv(path, sep=None, engine="python")
        except Exception as e:
            raise DataValidationError(f"Could not read CSV file: {e}")

        return DataLoader.process_dataframe(df)

    @staticmethod
    def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalizes column names, converts data types, formats timestamps to unix seconds,
        and validates OHLC integrity.
        """
        if df is None or df.empty:
            raise DataValidationError("Dataframe is empty.")

        # Normalize columns
        df_norm = DataValidator.normalize_columns(df)

        # Basic required column check before conversion
        for col in ["timestamp", "open", "high", "low", "close"]:
            if col not in df_norm.columns:
                raise DataValidationError(f"CSV is missing required column: '{col}'")

        if "volume" not in df_norm.columns:
            df_norm["volume"] = 0.0

        # Convert timestamp to standard datetime and integer unix seconds
        try:
            ts_col = df_norm["timestamp"]
            if pd.api.types.is_numeric_dtype(ts_col):
                first_val = ts_col.dropna().iloc[0]
                unit = "ms" if first_val > 1e11 else "s"
                dt_series = pd.to_datetime(ts_col, unit=unit, utc=True)
            else:
                dt_series = pd.to_datetime(ts_col, utc=True)

            df_norm["datetime"] = dt_series
            df_norm["timestamp"] = (dt_series.astype("int64") // 10**9).astype("int64")
        except Exception as e:
            raise DataValidationError(f"Error parsing timestamp column: {e}")

        # Ensure numeric OHLCV
        for col in ["open", "high", "low", "close", "volume"]:
            df_norm[col] = pd.to_numeric(df_norm[col], errors="coerce")

        # Sort chronologically & drop duplicates
        df_norm = df_norm.sort_values(by="timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

        # Validate
        is_valid, errors = DataValidator.validate(df_norm)
        if not is_valid:
            raise DataValidationError("Data validation failed:\n - " + "\n - ".join(errors))

        # Reorder canonical columns
        canonical_cols = ["timestamp", "datetime", "open", "high", "low", "close", "volume"]
        return df_norm[canonical_cols]
