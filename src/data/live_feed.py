import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import pandas as pd
import numpy as np

from PyQt6.QtCore import pyqtSignal, QObject, QThread, QTimer

from src.data.data_loader import DataLoader
from src.data.mt5_connector import mt5_connector
from src.utils.logger import logger


class LiveDataLoader:
    """
    Fetches real-time up-to-date historical candles from MetaTrader 5 (FOREX.com / broker) or public APIs
    (Binance for Crypto, Yahoo Finance for Gold & FX) to fill the gap between offline datasets and live market price.
    """

    @staticmethod
    def fetch_latest_candles(symbol: str, timeframe: str = "5m", limit: int = 1000) -> Optional[pd.DataFrame]:
        # 1. Primary: If MetaTrader 5 Bridge is active, fetch direct from broker
        if mt5_connector.is_connected:
            try:
                mt5_df = mt5_connector.fetch_candles(symbol, timeframe=timeframe, count=limit)
                if mt5_df is not None and not mt5_df.empty:
                    logger.info(f"Fetched {len(mt5_df)} candles for {symbol} directly from MT5 Bridge.")
                    return mt5_df
            except Exception as e:
                logger.warning(f"MT5 candle fetch failed for {symbol}: {e}. Falling back to public feed.")

        symbol_upper = symbol.upper()
        try:
            if "BTC" in symbol_upper or "ETH" in symbol_upper or "SOL" in symbol_upper:
                return LiveDataLoader._fetch_binance_klines(symbol_upper, timeframe, limit)
            else:
                return LiveDataLoader._fetch_yahoo_klines(symbol_upper, timeframe)
        except Exception as e:
            logger.warning(f"Failed to fetch live historical candles for {symbol}: {e}")
            return None

    @staticmethod
    def _fetch_binance_klines(symbol: str, timeframe: str, limit: int = 1000) -> Optional[pd.DataFrame]:
        binance_pair = "BTCUSDT" if "BTC" in symbol else ("ETHUSDT" if "ETH" in symbol else "SOLUSDT")
        tf_map = {
            "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m",
            "30m": "30m", "1h": "1h", "4h": "4h", "1d": "1d"
        }
        interval = tf_map.get(timeframe.lower(), "5m")
        url = f"https://api.binance.com/api/v3/klines?symbol={binance_pair}&interval={interval}&limit={limit}"

        req = urllib.request.Request(url, headers={"User-Agent": "TradingReplayLab/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        rows = []
        for k in data:
            ts = int(k[0]) // 1000
            rows.append({
                "timestamp": ts,
                "datetime": datetime.utcfromtimestamp(ts),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            })

        df = pd.DataFrame(rows)
        return df if not df.empty else None

    @staticmethod
    def _fetch_yahoo_klines(symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        yahoo_sym = "GC=F" if "XAU" in symbol or "GOLD" in symbol else f"{symbol}=X"
        tf_map = {
            "1m": ("1m", "7d"),
            "3m": ("5m", "7d"),
            "5m": ("5m", "7d"),
            "15m": ("15m", "7d"),
            "30m": ("30m", "1mo"),
            "1h": ("60m", "1mo"),
            "4h": ("60m", "3mo"),
            "1d": ("1d", "1y"),
        }
        interval, range_str = tf_map.get(timeframe.lower(), ("5m", "5d"))
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_sym}?interval={interval}&range={range_str}"

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        res = data["chart"]["result"][0]
        timestamps = res.get("timestamp", [])
        quote = res["indicators"]["quote"][0]

        opens = quote.get("open", [])
        highs = quote.get("high", [])
        lows = quote.get("low", [])
        closes = quote.get("close", [])
        volumes = quote.get("volume", [])

        rows = []
        for i in range(len(timestamps)):
            if timestamps[i] and opens[i] is not None and closes[i] is not None:
                ts = int(timestamps[i])
                rows.append({
                    "timestamp": ts,
                    "datetime": datetime.utcfromtimestamp(ts),
                    "open": float(opens[i]),
                    "high": float(highs[i]) if highs[i] is not None else float(opens[i]),
                    "low": float(lows[i]) if lows[i] is not None else float(opens[i]),
                    "close": float(closes[i]),
                    "volume": float(volumes[i]) if volumes[i] is not None else 10.0,
                })

        df = pd.DataFrame(rows)
        return df if not df.empty else None

    @staticmethod
    def merge_with_live(existing_df: pd.DataFrame, live_df: pd.DataFrame) -> pd.DataFrame:
        """Merges historical candles with newly fetched live candles smoothly without duplicates."""
        if existing_df is None or existing_df.empty:
            return live_df
        if live_df is None or live_df.empty:
            return existing_df

        combined = pd.concat([existing_df, live_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["timestamp"]).sort_values(by="timestamp").reset_index(drop=True)
        return combined


class LiveFeedWorker(QThread):
    """
    Background worker thread streaming live market data with zero external dependencies.
    Supports real-time Binance public API (crypto 24/7) and Yahoo Finance / public ticker polls (Gold & FX).
    """

    candle_received = pyqtSignal(dict)
    price_updated = pyqtSignal(str, float, int)
    status_changed = pyqtSignal(bool, str)

    def __init__(self, symbol: str = "BTCUSD", timeframe: str = "1m", interval_ms: int = 1500, parent=None):
        super().__init__(parent)
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        self.interval_ms = interval_ms
        self._running = False

        self._last_candle_time: int = 0
        self._current_candle: Optional[Dict[str, Any]] = None

    def stop(self) -> None:
        self._running = False
        self.wait(1500)

    def run(self) -> None:
        self._running = True
        self.status_changed.emit(True, f"Live connected to {self.symbol}")
        logger.info(f"Live market feed started for {self.symbol}")

        while self._running:
            try:
                # 1. Check MT5 Bridge live quote & forming bar
                if mt5_connector.is_connected:
                    tick_res = mt5_connector.get_live_ticker(self.symbol)
                    price = None
                    vol = 1.0
                    if tick_res:
                        bid, ask, last_p, tick_vol = tick_res
                        price = last_p if last_p > 0 else ((bid + ask) / 2.0 if bid > 0 and ask > 0 else bid)
                        vol = tick_vol or 1.0

                    forming_df = mt5_connector.fetch_candles(self.symbol, self.timeframe, count=1)
                    if forming_df is not None and not forming_df.empty:
                        last_row = forming_df.iloc[-1]
                        bar_start = int(last_row["timestamp"])
                        c_open = float(last_row["open"])
                        c_high = float(last_row["high"])
                        c_low = float(last_row["low"])
                        c_close = price if (price is not None and price > 0) else float(last_row["close"])
                        c_high = max(c_high, c_close)
                        c_low = min(c_low, c_close)
                        c_vol = float(last_row.get("volume", 1.0))

                        self._last_candle_time = bar_start
                        self._current_candle = {
                            "time": bar_start,
                            "open": c_open,
                            "high": c_high,
                            "low": c_low,
                            "close": c_close,
                            "volume": c_vol,
                            "timestamp": bar_start,
                            "datetime": str(last_row.get("datetime", "")),
                        }
                        self.price_updated.emit(self.symbol, c_close, bar_start)
                        self.candle_received.emit(self._current_candle.copy())
                        time.sleep(self.interval_ms / 1000.0)
                        continue

                # 2. Public Fallback (Crypto Binance 24/7 or Yahoo Finance)
                price, vol = self._fetch_live_ticker(self.symbol)
                if price and price > 0:
                    now_ts = int(time.time())
                    tf_seconds = self._timeframe_to_seconds(self.timeframe)
                    bar_start = (now_ts // tf_seconds) * tf_seconds

                    if self._current_candle is None or bar_start > self._last_candle_time:
                        self._last_candle_time = bar_start
                        self._current_candle = {
                            "time": bar_start,
                            "open": price,
                            "high": price,
                            "low": price,
                            "close": price,
                            "volume": vol or 1.0,
                            "timestamp": bar_start,
                            "datetime": datetime.utcfromtimestamp(bar_start).isoformat(),
                        }
                    else:
                        self._current_candle["high"] = max(self._current_candle["high"], price)
                        self._current_candle["low"] = min(self._current_candle["low"], price)
                        self._current_candle["close"] = price
                        self._current_candle["volume"] += (vol or 0.1)

                    self.price_updated.emit(self.symbol, price, now_ts)
                    self.candle_received.emit(self._current_candle.copy())

            except Exception as e:
                logger.debug(f"Live feed polling tick note: {e}")

            time.sleep(self.interval_ms / 1000.0)

        self.status_changed.emit(False, "Live feed stopped")


    def _fetch_live_ticker(self, symbol: str) -> Tuple[float, float]:
        """Fetches live ticker price using MT5 bridge or public REST API."""
        # 1. Primary: MetaTrader 5 direct broker tick quote
        if mt5_connector.is_connected:
            try:
                res = mt5_connector.get_live_ticker(symbol)
                if res:
                    bid, ask, last_p, vol = res
                    return last_p, vol
            except Exception as e:
                logger.debug(f"MT5 live ticker tick note: {e}")

        # 2. Binance Crypto pairs (BTCUSDT, ETHUSDT, etc.)
        if "BTC" in symbol or "ETH" in symbol or "SOL" in symbol or "CRYPTO" in symbol:
            binance_pair = "BTCUSDT" if "BTC" in symbol else ("ETHUSDT" if "ETH" in symbol else "SOLUSDT")
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_pair}"
            req = urllib.request.Request(url, headers={"User-Agent": "TradingReplayLab/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                price = float(data.get("lastPrice", 0.0))
                vol = float(data.get("volume", 0.0)) / 1000.0
                return price, vol

        # 3. Gold / Forex pairs via public yahoo finance query
        yahoo_sym = "GC=F" if "XAU" in symbol or "GOLD" in symbol else f"{symbol}=X"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_sym}?interval=1m&range=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            meta = data["chart"]["result"][0]["meta"]
            price = float(meta.get("regularMarketPrice", 0.0))
            return price, 10.0

    def _timeframe_to_seconds(self, tf: str) -> int:
        tf_map = {
            "1m": 60,
            "3m": 180,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400,
        }
        return tf_map.get(tf.lower(), 60)
