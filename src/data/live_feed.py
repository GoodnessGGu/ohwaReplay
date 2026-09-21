import json
import time
from datetime import datetime
from typing import Any, Dict, Optional
import urllib.request

from PyQt6.QtCore import pyqtSignal, QObject, QThread, QTimer

from src.utils.logger import logger


class LiveFeedWorker(QThread):
    """
    Background worker thread streaming live market data with zero external dependencies.
    Supports real-time Binance public API (crypto 24/7) and Yahoo Finance / public ticker polls (Gold & FX).
    """

    candle_received = pyqtSignal(dict)
    price_updated = pyqtSignal(str, float, int)
    status_changed = pyqtSignal(bool, str)

    def __init__(self, symbol: str = "BTCUSD", timeframe: str = "1m", interval_ms: int = 2000, parent=None):
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
                price, vol = self._fetch_live_ticker(self.symbol)
                if price and price > 0:
                    now_ts = int(time.time())
                    tf_seconds = self._timeframe_to_seconds(self.timeframe)
                    bar_start = (now_ts // tf_seconds) * tf_seconds

                    if self._current_candle is None or bar_start > self._last_candle_time:
                        # New candle start
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
                        # Update current forming bar
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

    def _fetch_live_ticker(self, symbol: str) -> tuple[float, float]:
        """Fetches live ticker price using free public REST API."""
        # 1. Binance Crypto pairs (BTCUSDT, ETHUSDT, etc.)
        if "BTC" in symbol or "ETH" in symbol or "SOL" in symbol or "CRYPTO" in symbol:
            binance_pair = "BTCUSDT" if "BTC" in symbol else ("ETHUSDT" if "ETH" in symbol else "SOLUSDT")
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_pair}"
            req = urllib.request.Request(url, headers={"User-Agent": "TradingReplayLab/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                price = float(data.get("lastPrice", 0.0))
                vol = float(data.get("volume", 0.0)) / 1000.0
                return price, vol

        # 2. Gold / Forex pairs via public yahoo finance query
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
