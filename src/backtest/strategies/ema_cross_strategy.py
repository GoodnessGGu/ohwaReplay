from typing import Any, Dict
import numpy as np
import pandas as pd

from src.backtest.strategy import BaseStrategy
from src.indicators.all_indicators import ATRIndicator, EMAIndicator


class EMACrossoverStrategy(BaseStrategy):
    """
    Dual Moving Average Trend Following Strategy with Dynamic ATR Stop Loss & Target.
    """
    name = "EMA_Cross"
    description = "Fast/Slow EMA Crossover with ATR Volatility Filter"

    def __init__(self, fast_period: int = 9, slow_period: int = 21, atr_multiplier: float = 1.5, risk_reward: float = 2.0, **params: Any):
        super().__init__(
            fast_period=fast_period,
            slow_period=slow_period,
            atr_multiplier=atr_multiplier,
            risk_reward=risk_reward,
            **params
        )

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        signals = pd.DataFrame(index=df.index)
        signals["signal"] = 0
        signals["stop_loss"] = np.nan
        signals["take_profit"] = np.nan
        signals["comment"] = ""

        fast_p = int(self.params.get("fast_period", 9))
        slow_p = int(self.params.get("slow_period", 21))
        atr_mult = float(self.params.get("atr_multiplier", 1.5))
        rr = float(self.params.get("risk_reward", 2.0))

        if df.empty or len(df) < max(fast_p, slow_p) + 5:
            return signals

        fast_ema = EMAIndicator(period=fast_p).calculate(df)[f"EMA_{fast_p}"].values
        slow_ema = EMAIndicator(period=slow_p).calculate(df)[f"EMA_{slow_p}"].values
        atr_vals = ATRIndicator(period=14).calculate(df)["ATR_14"].values

        n = len(df)
        closes = df["close"].values
        sig = np.zeros(n, dtype=int)
        sl_arr = np.full(n, np.nan)
        tp_arr = np.full(n, np.nan)
        comm = [""] * n

        for i in range(1, n):
            if pd.isna(fast_ema[i]) or pd.isna(slow_ema[i]) or pd.isna(atr_vals[i]):
                continue

            entry = closes[i]
            atr = atr_vals[i]
            risk = atr * atr_mult

            # Golden cross (Bullish)
            if fast_ema[i - 1] <= slow_ema[i - 1] and fast_ema[i] > slow_ema[i]:
                sig[i] = 1
                sl_arr[i] = round(entry - risk, 5)
                tp_arr[i] = round(entry + (risk * rr), 5)
                comm[i] = f"EMA {fast_p}/{slow_p} Bullish Cross"

            # Death cross (Bearish)
            elif fast_ema[i - 1] >= slow_ema[i - 1] and fast_ema[i] < slow_ema[i]:
                sig[i] = -1
                sl_arr[i] = round(entry + risk, 5)
                tp_arr[i] = round(entry - (risk * rr), 5)
                comm[i] = f"EMA {fast_p}/{slow_p} Bearish Cross"

        signals["signal"] = sig
        signals["stop_loss"] = sl_arr
        signals["take_profit"] = tp_arr
        signals["comment"] = comm
        return signals
