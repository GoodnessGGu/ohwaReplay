import pandas as pd
from src.indicators.base_indicator import BaseIndicator


class EMAIndicator(BaseIndicator):
    name = "EMA"
    display_name = "Exponential Moving Average"
    overlay = True

    def __init__(self, period: int = 20, color: str = "#2196f3", **kwargs):
        super().__init__(period=period, color=color, **kwargs)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "close" not in df.columns:
            return pd.DataFrame()
        period = int(self.params.get("period", 20))
        res = pd.DataFrame(index=df.index)
        res[f"EMA_{period}"] = df["close"].ewm(span=period, adjust=False).mean()
        return res


class SMAIndicator(BaseIndicator):
    name = "SMA"
    display_name = "Simple Moving Average"
    overlay = True

    def __init__(self, period: int = 50, color: str = "#ff9800", **kwargs):
        super().__init__(period=period, color=color, **kwargs)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "close" not in df.columns:
            return pd.DataFrame()
        period = int(self.params.get("period", 50))
        res = pd.DataFrame(index=df.index)
        res[f"SMA_{period}"] = df["close"].rolling(window=period).mean()
        return res


class RSIIndicator(BaseIndicator):
    name = "RSI"
    display_name = "Relative Strength Index"
    overlay = False

    def __init__(self, period: int = 14, color: str = "#9c27b0", **kwargs):
        super().__init__(period=period, color=color, **kwargs)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "close" not in df.columns or len(df) < 2:
            return pd.DataFrame()
        period = int(self.params.get("period", 14))
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0.0)).ewm(alpha=1 / period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1 / period, adjust=False).mean()

        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))

        res = pd.DataFrame(index=df.index)
        res[f"RSI_{period}"] = rsi
        return res


class MACDIndicator(BaseIndicator):
    name = "MACD"
    display_name = "Moving Average Convergence Divergence"
    overlay = False

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9, **kwargs):
        super().__init__(fast=fast, slow=slow, signal=signal, **kwargs)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "close" not in df.columns:
            return pd.DataFrame()
        fast = int(self.params.get("fast", 12))
        slow = int(self.params.get("slow", 26))
        signal = int(self.params.get("signal", 9))

        fast_ema = df["close"].ewm(span=fast, adjust=False).mean()
        slow_ema = df["close"].ewm(span=slow, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        hist = macd_line - signal_line

        res = pd.DataFrame(index=df.index)
        res["MACD_line"] = macd_line
        res["MACD_signal"] = signal_line
        res["MACD_hist"] = hist
        return res


class ATRIndicator(BaseIndicator):
    name = "ATR"
    display_name = "Average True Range"
    overlay = False

    def __init__(self, period: int = 14, **kwargs):
        super().__init__(period=period, **kwargs)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or len(df) < 2:
            return pd.DataFrame()
        period = int(self.params.get("period", 14))
        high = df["high"]
        low = df["low"]
        close = df["close"]
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.ewm(span=period, adjust=False).mean()
        res = pd.DataFrame(index=df.index)
        res[f"ATR_{period}"] = atr
        return res


class BollingerBandsIndicator(BaseIndicator):
    name = "BollingerBands"
    display_name = "Bollinger Bands"
    overlay = True

    def __init__(self, period: int = 20, std_dev: float = 2.0, **kwargs):
        super().__init__(period=period, std_dev=std_dev, **kwargs)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        period = int(self.params.get("period", 20))
        std_dev = float(self.params.get("std_dev", 2.0))

        sma = df["close"].rolling(window=period).mean()
        std = df["close"].rolling(window=period).std()

        res = pd.DataFrame(index=df.index)
        res["BB_middle"] = sma
        res["BB_upper"] = sma + (std * std_dev)
        res["BB_lower"] = sma - (std * std_dev)
        return res


class SmartTrailIndicator(BaseIndicator):
    """
    Smart Trail Signals (Continuous Operation).
    ATR-based volatility trailing stop with dynamic trend filtering and diamond signal markers.
    """
    name = "SmartTrail"
    display_name = "Smart Trail Signals"
    overlay = True

    def __init__(
        self,
        length: int = 14,
        multiplier: float = 2.0,
        sensitivity: int = 3,
        source: str = "close",
        color_up: str = "#00e676",
        color_down: str = "#ff5252",
        **kwargs,
    ):
        super().__init__(
            length=length,
            multiplier=multiplier,
            sensitivity=sensitivity,
            source=source,
            color_up=color_up,
            color_down=color_down,
            **kwargs,
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "close" not in df.columns or len(df) < 2:
            return pd.DataFrame()

        import numpy as np

        length = int(self.params.get("length", 14))
        multiplier = float(self.params.get("multiplier", 2.0))
        sensitivity = int(self.params.get("sensitivity", 3))
        src_col = str(self.params.get("source", "close"))
        if src_col not in df.columns:
            src_col = "close"

        src = df[src_col]
        high = df["high"]
        low = df["low"]
        close = df["close"]
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.ewm(alpha=1.0 / max(1, length), adjust=False).mean()
        volatility_factor = atr * multiplier * (sensitivity / 3.0)

        basic_up = src - volatility_factor
        basic_down = src + volatility_factor

        n = len(df)
        trail_up = np.zeros(n)
        trail_down = np.zeros(n)
        smart_trend = np.ones(n, dtype=int)
        smart_trail_value = np.zeros(n)
        bull_signals = np.zeros(n, dtype=bool)
        bear_signals = np.zeros(n, dtype=bool)

        src_vals = src.values
        b_up = basic_up.values
        b_down = basic_down.values

        for i in range(n):
            if i == 0:
                trail_up[0] = b_up[0] if not np.isnan(b_up[0]) else src_vals[0]
                trail_down[0] = b_down[0] if not np.isnan(b_down[0]) else src_vals[0]
                smart_trend[0] = 1
                smart_trail_value[0] = trail_up[0]
                continue

            prev_tu = trail_up[i - 1]
            prev_td = trail_down[i - 1]
            prev_trend = smart_trend[i - 1]

            if src_vals[i] > prev_tu and src_vals[i - 1] > prev_tu:
                trail_up[i] = max(prev_tu, b_up[i]) if not np.isnan(b_up[i]) else prev_tu
            else:
                trail_up[i] = b_up[i] if not np.isnan(b_up[i]) else prev_tu

            if src_vals[i] < prev_td and src_vals[i - 1] < prev_td:
                trail_down[i] = min(prev_td, b_down[i]) if not np.isnan(b_down[i]) else prev_td
            else:
                trail_down[i] = b_down[i] if not np.isnan(b_down[i]) else prev_td

            if src_vals[i] > prev_td:
                smart_trend[i] = 1
            elif src_vals[i] < prev_tu:
                smart_trend[i] = -1
            else:
                smart_trend[i] = prev_trend

            smart_trail_value[i] = trail_up[i] if smart_trend[i] == 1 else trail_down[i]

            if i > 1 and smart_trend[i] != prev_trend:
                if smart_trend[i] == 1:
                    bull_signals[i] = True
                elif smart_trend[i] == -1:
                    bear_signals[i] = True

        res = pd.DataFrame(index=df.index)
        res["SmartTrail"] = smart_trail_value
        res["SmartTrend"] = smart_trend
        res["BullSignal"] = bull_signals
        res["BearSignal"] = bear_signals
        return res


from src.indicators.smc import FVGIndicator, MarketStructureIndicator

