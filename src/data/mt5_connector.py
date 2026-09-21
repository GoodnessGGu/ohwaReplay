import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.utils.logger import logger

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False


class MT5Connector:
    """
    High-performance MetaTrader 5 Bridge Connector.
    Enables zero-rate-limit real-time streaming, tick-level precision,
    and deep historical M1/M5/H1 candle extraction directly from FOREX.com / broker terminals.
    """

    _instance: Optional["MT5Connector"] = None

    def __new__(cls) -> "MT5Connector":
        if cls._instance is None:
            cls._instance = super(MT5Connector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._connected: bool = False
        self._terminal_path: Optional[str] = None
        self._symbol_cache: Dict[str, str] = {}
        self._initialized = True

    @property
    def is_available(self) -> bool:
        """Returns True if the MetaTrader5 Python library is available."""
        return MT5_AVAILABLE

    @property
    def is_connected(self) -> bool:
        """Returns True if an active IPC connection to an MT5 terminal is established."""
        return self._connected and MT5_AVAILABLE

    def connect(
        self,
        path: Optional[str] = None,
        login: Optional[int] = None,
        password: Optional[str] = None,
        server: Optional[str] = None,
        timeout: int = 4000,
    ) -> Tuple[bool, str]:
        """
        Connects to a running MT5 terminal instance or launches a specific terminal.
        """
        if not MT5_AVAILABLE:
            return False, "MetaTrader5 Python package is not installed."

        try:
            init_kwargs: Dict[str, Any] = {"timeout": timeout}
            if path:
                init_kwargs["path"] = path
            if login:
                init_kwargs["login"] = int(login)
            if password:
                init_kwargs["password"] = password
            if server:
                init_kwargs["server"] = server

            ok = mt5.initialize(**init_kwargs)
            if not ok:
                err_code, err_desc = mt5.last_error()
                self._connected = False
                msg = f"Failed to connect to MT5 (Error {err_code}: {err_desc}). Ensure your FOREX.com MT5 terminal is running."
                logger.warning(msg)
                return False, msg

            self._connected = True
            self._terminal_path = path
            self._refresh_symbol_cache()

            term_info = mt5.terminal_info()
            company = term_info.company if term_info else "MetaTrader 5"
            acc_info = mt5.account_info()
            acc_str = f"Account #{acc_info.login} ({acc_info.currency})" if acc_info else "Connected"

            success_msg = f"Connected to {company} MT5 [{acc_str}]"
            logger.info(success_msg)
            return True, success_msg

        except Exception as e:
            self._connected = False
            logger.error(f"Exception during MT5 connection: {e}")
            return False, str(e)

    def disconnect(self) -> None:
        """Shuts down MT5 IPC connection."""
        if MT5_AVAILABLE and self._connected:
            try:
                mt5.shutdown()
            except Exception as e:
                logger.debug(f"MT5 shutdown note: {e}")
        self._connected = False
        logger.info("MT5 Bridge disconnected.")

    def _refresh_symbol_cache(self) -> None:
        """Scans broker market watch symbols to map standardized tickers to broker symbols."""
        if not self.is_connected:
            return
        try:
            symbols = mt5.symbols_get()
            if symbols:
                self._symbol_cache = {s.name.upper(): s.name for s in symbols}
        except Exception as e:
            logger.debug(f"Error caching MT5 symbols: {e}")

    def resolve_symbol(self, symbol: str) -> Optional[str]:
        """
        Resolves a standard symbol (e.g. 'XAUUSD', 'EURUSD') to the broker's exact symbol name
        including potential suffixes (e.g. 'XAUUSD.pro', 'GOLD', 'EURUSD.r').
        """
        if not self.is_connected:
            return None

        sym_upper = symbol.upper().replace("/", "").replace("-", "")

        # 1. Direct match
        if sym_upper in self._symbol_cache:
            return self._symbol_cache[sym_upper]

        # 2. Check if already known in MT5
        sym_info = mt5.symbol_info(sym_upper)
        if sym_info:
            return sym_info.name

        # 3. Gold aliases
        if "XAU" in sym_upper or "GOLD" in sym_upper:
            for s in self._symbol_cache.values():
                if "XAUUSD" in s.upper() or "GOLD" in s.upper():
                    return s

        # 4. Suffix search (e.g. EURUSD.pro, EURUSD_i, EURUSDm)
        for s in self._symbol_cache.values():
            if s.upper().startswith(sym_upper):
                return s

        return sym_upper

    def _map_timeframe(self, timeframe: str) -> int:
        """Maps string timeframe to MT5 timeframe constants."""
        tf_map = {
            "1m": mt5.TIMEFRAME_M1,
            "3m": mt5.TIMEFRAME_M3,
            "5m": mt5.TIMEFRAME_M5,
            "15m": mt5.TIMEFRAME_M15,
            "30m": mt5.TIMEFRAME_M30,
            "1h": mt5.TIMEFRAME_H1,
            "4h": mt5.TIMEFRAME_H4,
            "1d": mt5.TIMEFRAME_D1,
        }
        return tf_map.get(timeframe.lower(), mt5.TIMEFRAME_M5)

    def fetch_candles(self, symbol: str, timeframe: str = "5m", count: int = 5000) -> Optional[pd.DataFrame]:
        """
        Fetches official broker historical OHLCV candle data directly from MT5 terminal.
        """
        if not self.is_connected:
            return None

        try:
            broker_symbol = self.resolve_symbol(symbol)
            if not broker_symbol:
                logger.warning(f"Could not resolve MT5 symbol for {symbol}")
                return None

            # Ensure symbol is selected in Market Watch
            mt5.symbol_select(broker_symbol, True)

            mt5_tf = self._map_timeframe(timeframe)
            rates = mt5.copy_rates_from_pos(broker_symbol, mt5_tf, 0, count)

            if rates is None or len(rates) == 0:
                logger.warning(f"No rates returned from MT5 for {broker_symbol}")
                return None

            df = pd.DataFrame(rates)
            df.rename(columns={"time": "timestamp", "tick_volume": "volume"}, inplace=True)
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
            df = df[["timestamp", "datetime", "open", "high", "low", "close", "volume"]]

            return df if not df.empty else None

        except Exception as e:
            logger.error(f"Error fetching candles from MT5 for {symbol}: {e}")
            return None

    def get_live_ticker(self, symbol: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Retrieves real-time broker tick quote: (bid, ask, last_price, volume).
        """
        if not self.is_connected:
            return None

        try:
            broker_symbol = self.resolve_symbol(symbol)
            if not broker_symbol:
                return None

            mt5.symbol_select(broker_symbol, True)
            tick = mt5.symbol_info_tick(broker_symbol)
            if tick is None:
                return None

            bid = float(tick.bid)
            ask = float(tick.ask)
            last_price = float(tick.last) if tick.last and tick.last > 0 else (bid + ask) / 2.0
            volume = float(tick.volume) if tick.volume and tick.volume > 0 else 1.0

            return bid, ask, last_price, volume

        except Exception as e:
            logger.debug(f"MT5 live ticker error for {symbol}: {e}")
            return None

    def get_account_summary(self) -> Optional[Dict[str, Any]]:
        """Retrieves active MT5 account metrics."""
        if not self.is_connected:
            return None
        try:
            acc = mt5.account_info()
            term = mt5.terminal_info()
            if not acc:
                return None
            return {
                "login": acc.login,
                "server": acc.server,
                "company": acc.company,
                "currency": acc.currency,
                "balance": acc.balance,
                "equity": acc.equity,
                "profit": acc.profit,
                "margin": acc.margin,
                "margin_free": acc.margin_free,
                "leverage": acc.leverage,
                "terminal_name": term.name if term else "MT5",
                "ping": term.ping_last if term else 0,
            }
        except Exception as e:
            logger.debug(f"Error getting MT5 account summary: {e}")
            return None


mt5_connector = MT5Connector()
