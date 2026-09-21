from typing import Any, Dict
import numpy as np
import pandas as pd

from src.backtest.strategy import BaseStrategy
from src.indicators.smc import MarketStructureIndicator


class MarketStructureStrategy(BaseStrategy):
    """
    SMC Break of Structure (BOS) & Change of Character (CHoCH) Strategy.
    Enters on structural break confirmation in the direction of newly established market structure.
    """
    name = "MarketStructure_Breakout"
    description = "SMC BOS / CHoCH Trend Continuation with 2.5 R:R"

    def __init__(self, swing_length: int = 5, risk_reward: float = 2.5, **params: Any):
        super().__init__(swing_length=swing_length, risk_reward=risk_reward, **params)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        signals = pd.DataFrame(index=df.index)
        signals["signal"] = 0
        signals["stop_loss"] = np.nan
        signals["take_profit"] = np.nan
        signals["comment"] = ""

        if df.empty or len(df) < 15:
            return signals

        k = int(self.params.get("swing_length", 5))
        rr = float(self.params.get("risk_reward", 2.5))

        ms_ind = MarketStructureIndicator(swing_length=k)
        ms_df = ms_ind.calculate(df)

        n = len(df)
        closes = df["close"].values
        lows = df["low"].values
        highs = df["high"].values

        sig = np.zeros(n, dtype=int)
        sl_arr = np.full(n, np.nan)
        tp_arr = np.full(n, np.nan)
        comm = [""] * n

        st_types = ms_df["structure_type"].values

        for i in range(1, n):
            st = st_types[i]
            entry = closes[i]

            if "BULL" in st:
                # Bullish BOS or CHoCH
                recent_low = np.min(lows[max(0, i - k):i + 1])
                risk = entry - recent_low
                if risk > 0:
                    sig[i] = 1
                    sl_arr[i] = round(recent_low, 5)
                    tp_arr[i] = round(entry + (risk * rr), 5)
                    comm[i] = f"Bullish {st}"

            elif "BEAR" in st:
                # Bearish BOS or CHoCH
                recent_high = np.max(highs[max(0, i - k):i + 1])
                risk = recent_high - entry
                if risk > 0:
                    sig[i] = -1
                    sl_arr[i] = round(recent_high, 5)
                    tp_arr[i] = round(entry - (risk * rr), 5)
                    comm[i] = f"Bearish {st}"

        signals["signal"] = sig
        signals["stop_loss"] = sl_arr
        signals["take_profit"] = tp_arr
        signals["comment"] = comm
        return signals
