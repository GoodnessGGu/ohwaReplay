from typing import List, Tuple
import numpy as np
import pandas as pd


class DataValidationError(Exception):
    """Custom exception raised when OHLCV data validation fails."""
    pass


class DataValidator:
    """Validates OHLCV pandas DataFrames for trading analysis and replay."""

    REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

    TIMESTAMP_CANDIDATES = ["timestamp", "datetime", "date", "time"]
    OPEN_CANDIDATES = ["open"]
    HIGH_CANDIDATES = ["high"]
    LOW_CANDIDATES = ["low"]
    CLOSE_CANDIDATES = ["close"]
    VOLUME_CANDIDATES = ["volume", "vol", "v"]

    @classmethod
    def normalize_columns(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Standardizes column names to canonical names without duplication."""
        df = df.copy()
        col_map_lower = {str(c).strip().lower(): c for c in df.columns}

        result_df = pd.DataFrame(index=df.index)

        # 1. Resolve timestamp
        for candidate in cls.TIMESTAMP_CANDIDATES:
            if candidate in col_map_lower:
                result_df["timestamp"] = df[col_map_lower[candidate]]
                break

        # 2. Resolve OHLCV
        for candidate in cls.OPEN_CANDIDATES:
            if candidate in col_map_lower:
                result_df["open"] = df[col_map_lower[candidate]]
                break

        for candidate in cls.HIGH_CANDIDATES:
            if candidate in col_map_lower:
                result_df["high"] = df[col_map_lower[candidate]]
                break

        for candidate in cls.LOW_CANDIDATES:
            if candidate in col_map_lower:
                result_df["low"] = df[col_map_lower[candidate]]
                break

        for candidate in cls.CLOSE_CANDIDATES:
            if candidate in col_map_lower:
                result_df["close"] = df[col_map_lower[candidate]]
                break

        for candidate in cls.VOLUME_CANDIDATES:
            if candidate in col_map_lower:
                result_df["volume"] = df[col_map_lower[candidate]]
                break

        if "volume" not in result_df.columns:
            result_df["volume"] = 0.0

        return result_df

    @classmethod
    def validate(cls, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validates the normalized dataframe.
        Returns (is_valid, list_of_error_messages).
        """
        errors: List[str] = []

        if df is None or df.empty:
            return False, ["Dataset is empty."]

        # 1. Check required columns
        for col in cls.REQUIRED_COLUMNS:
            if col not in df.columns:
                errors.append(f"Missing required column: '{col}'")

        if errors:
            return False, errors

        # 2. Check for NaN or missing values
        null_counts = df[cls.REQUIRED_COLUMNS].isnull().sum()
        for col, count in null_counts.items():
            if count > 0:
                errors.append(f"Column '{col}' contains {count} missing/null values.")

        # 3. Validate timestamp column
        try:
            if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
                if not pd.api.types.is_numeric_dtype(df["timestamp"]):
                    pd.to_datetime(df["timestamp"])
        except Exception as e:
            errors.append(f"Invalid timestamp format in dataset: {e}")

        # Check chronological order & duplicates
        if "timestamp" in df.columns and len(df) > 1:
            ts = pd.to_datetime(df["timestamp"]) if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]) else df["timestamp"]
            if not ts.is_monotonic_increasing:
                errors.append("Dataset timestamps are not in chronological ascending order.")
            if ts.duplicated().any():
                dup_count = ts.duplicated().sum()
                errors.append(f"Dataset contains {dup_count} duplicate timestamps.")

        # 4. Numeric type validation
        numeric_cols = ["open", "high", "low", "close", "volume"]
        for col in numeric_cols:
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    pd.to_numeric(df[col])
                except Exception:
                    errors.append(f"Column '{col}' must contain numeric values.")

        if errors:
            return False, errors

        # 5. Logical OHLC relationship validation
        invalid_high_low = (df["high"] < df["low"]).sum()
        if invalid_high_low > 0:
            errors.append(f"Found {invalid_high_low} candles where High < Low.")

        invalid_high_open = (df["high"] < df["open"]).sum()
        if invalid_high_open > 0:
            errors.append(f"Found {invalid_high_open} candles where High < Open.")

        invalid_high_close = (df["high"] < df["close"]).sum()
        if invalid_high_close > 0:
            errors.append(f"Found {invalid_high_close} candles where High < Close.")

        invalid_low_open = (df["low"] > df["open"]).sum()
        if invalid_low_open > 0:
            errors.append(f"Found {invalid_low_open} candles where Low > Open.")

        invalid_low_close = (df["low"] > df["close"]).sum()
        if invalid_low_close > 0:
            errors.append(f"Found {invalid_low_close} candles where Low > Close.")

        # 6. Non-negative prices/volumes
        if (df[["open", "high", "low", "close"]] <= 0).any().any():
            errors.append("Found non-positive price values (price <= 0).")

        if (df["volume"] < 0).any():
            errors.append("Found negative volume values (volume < 0).")

        return len(errors) == 0, errors
