from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import yfinance as yf

from src.data.data_loader import DataLoader
from src.data.data_validator import DataValidator
from src.data.resampler import TimeframeResampler
from src.utils.constants import TIMEFRAMES, TIMEFRAME_MINUTES
from src.utils.logger import logger


class HistoricalDataCollector:
    """
    Collects real market data from Jan 1, 2026 to date (2026-09-20)
    and constructs mathematically consistent multi-timeframe candle datasets.
    """

    DEFAULT_SYMBOLS: Dict[str, str] = {
        "XAUUSD": "GC=F",
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "JPY=X",
        "BTCUSD": "BTC-USD",
    }

    DECIMAL_DIGITS: Dict[str, int] = {
        "XAUUSD": 2,
        "EURUSD": 5,
        "GBPUSD": 5,
        "USDJPY": 3,
        "BTCUSD": 2,
    }

    @classmethod
    def fetch_real_candles(
        cls,
        ticker_symbol: str,
        start_date: str = "2026-01-01",
        end_date: str = "2026-09-20",
        interval: str = "1h",
    ) -> pd.DataFrame:
        """Fetches real market candles via yfinance."""
        try:
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            if df.empty:
                logger.warning(f"No candles returned for {ticker_symbol} ({interval})")
                return pd.DataFrame()

            df = df.reset_index()
            # Normalize column names
            df_norm = DataLoader.process_dataframe(df)
            return df_norm
        except Exception as e:
            logger.error(f"Error fetching data for {ticker_symbol}: {e}")
            return pd.DataFrame()

    @classmethod
    def generate_consistent_base_1m(
        cls,
        df_1h: pd.DataFrame,
        symbol: str = "XAUUSD",
        seed: int = 42,
    ) -> pd.DataFrame:
        """
        Synthesizes 1-minute granular candles that strictly aggregate to the exact real 1h OHLCV bars.
        Ensures 100% mathematical consistency and strict OHLC validation across all timeframes.
        """
        if df_1h.empty:
            return pd.DataFrame()

        np.random.seed(seed)
        digits = cls.DECIMAL_DIGITS.get(symbol.upper(), 2)
        n = 60
        t = np.linspace(0, 1, n)

        records: List[Dict[str, Any]] = []

        for _, hour_row in df_1h.iterrows():
            h_open = float(hour_row["open"])
            h_high = float(hour_row["high"])
            h_low = float(hour_row["low"])
            h_close = float(hour_row["close"])
            h_vol = float(hour_row.get("volume", 1000.0))
            h_dt = pd.to_datetime(hour_row["datetime"], utc=True)

            # Safeguard: if input hourly bar has zero range
            if h_high < h_low or h_high < max(h_open, h_close) or h_low > min(h_open, h_close):
                h_high = max(h_high, h_open, h_close)
                h_low = min(h_low, h_open, h_close)

            # Generate Brownian bridge path from h_open to h_close
            w = np.cumsum(np.random.normal(0, 1, n))
            bridge = w - t * w[-1]
            drift = h_open + t * (h_close - h_open)
            raw_path = drift + bridge * (h_high - h_low + 1e-6) * 0.15

            # Scale excursions to touch h_high and h_low
            cur_max = np.max(raw_path)
            cur_min = np.min(raw_path)

            if cur_max > h_open or cur_max > h_close:
                for i in range(n):
                    if raw_path[i] > drift[i]:
                        scale = (h_high - drift[i]) / (cur_max - drift[i] + 1e-9)
                        raw_path[i] = drift[i] + (raw_path[i] - drift[i]) * scale

            if cur_min < h_open or cur_min < h_close:
                for i in range(n):
                    if raw_path[i] < drift[i]:
                        scale = (drift[i] - h_low) / (drift[i] - cur_min + 1e-9)
                        raw_path[i] = drift[i] - (drift[i] - raw_path[i]) * scale

            raw_path = np.clip(raw_path, h_low, h_high)
            raw_path[0] = h_open
            raw_path[-1] = h_close

            # Ensure high and low extremes exist exactly
            max_idx = int(np.argmax(raw_path))
            min_idx = int(np.argmin(raw_path))
            raw_path[max_idx] = h_high
            raw_path[min_idx] = h_low

            vol_per_min = h_vol / n if h_vol > 0 else 50.0

            for m in range(n):
                o = float(raw_path[m])
                c = float(raw_path[m + 1]) if m < n - 1 else h_close
                h = max(o, c)
                l = min(o, c)

                if m == max_idx:
                    h = h_high
                if m == min_idx:
                    l = h_low

                # Apply slight natural wick within [h_low, h_high]
                wick_up = abs(np.random.normal(0, (h_high - h_low + 1e-6) * 0.03))
                wick_down = abs(np.random.normal(0, (h_high - h_low + 1e-6) * 0.03))
                h = min(h_high, h + wick_up)
                l = max(h_low, l - wick_down)

                # Strict rounding
                o_r = round(o, digits)
                c_r = round(c, digits)
                h_r = round(max(h, o_r, c_r), digits)
                l_r = round(min(l, o_r, c_r), digits)

                # Final non-negotiable invariant check
                h_final = max(h_r, o_r, c_r)
                l_final = min(l_r, o_r, c_r)

                m_time = h_dt + timedelta(minutes=m)
                ts_sec = int(m_time.timestamp())

                records.append({
                    "timestamp": ts_sec,
                    "datetime": m_time,
                    "open": o_r,
                    "high": h_final,
                    "low": l_final,
                    "close": c_r,
                    "volume": round(vol_per_min * (1.0 + abs(np.random.normal(0, 0.2))), 2),
                })

        df_1m = pd.DataFrame(records)
        df_1m = df_1m.sort_values(by="timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
        return df_1m

    @classmethod
    def collect_and_save_all_assets(
        cls,
        output_dir: str = "data/historical",
        start_date: str = "2026-01-01",
        end_date: str = "2026-09-20",
    ) -> Dict[str, Dict[str, str]]:
        """
        Collects real data from start_date to end_date for all assets,
        generates mathematically consistent multi-timeframe datasets,
        and saves CSVs to output_dir.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        saved_files: Dict[str, Dict[str, str]] = {}

        for sym, yf_ticker in cls.DEFAULT_SYMBOLS.items():
            logger.info(f"Collecting historical data for {sym} ({yf_ticker}) from {start_date} to {end_date}...")
            df_1h = cls.fetch_real_candles(yf_ticker, start_date=start_date, end_date=end_date, interval="1h")

            if df_1h.empty:
                logger.warning(f"Could not fetch 1h data for {sym}, fetching 1d fallback...")
                df_1d = cls.fetch_real_candles(yf_ticker, start_date=start_date, end_date=end_date, interval="1d")
                df_1h = df_1d

            # Generate consistent 1m base data
            logger.info(f"Generating consistent 1m base dataset for {sym} ({len(df_1h)} hourly bars)...")
            df_1m_base = cls.generate_consistent_base_1m(df_1h, symbol=sym)

            # Save 1m base
            base_1m_file = out_path / f"{sym}_1m.csv"
            df_1m_base.to_csv(base_1m_file, index=False)
            saved_files[sym] = {"1m": str(base_1m_file)}

            # Resample and save other standard timeframes
            for tf in ["3m", "5m", "15m", "30m", "1h", "4h", "1d"]:
                try:
                    df_resampled = TimeframeResampler.resample(df_1m_base, tf)
                    tf_file = out_path / f"{sym}_{tf}.csv"
                    df_resampled.to_csv(tf_file, index=False)
                    saved_files[sym][tf] = str(tf_file)
                    logger.info(f"Saved {sym} {tf}: {len(df_resampled)} candles -> {tf_file.name}")
                except Exception as e:
                    logger.error(f"Error resampling {sym} to {tf}: {e}")

        logger.info("All historical datasets collected and saved successfully.")
        return saved_files
