from typing import Any, Dict
import numpy as np
import pandas as pd

from src.backtest.strategy import BaseStrategy
from src.indicators.smc import FVGIndicator


class FVGStrategy(BaseStrategy):
    """
    Smart Money Concepts Fair Value Gap (FVG) Strategy.
    Enters long when price retraces into a fresh Bullish FVG with stop loss below FVG bottom.
    Enters short when price retraces into a fresh Bearish FVG with stop loss above FVG top.
    """
    name = "FVG_Retest"
    description = "SMC Fair Value Gap Retest with 2.0+ R:R"

    def __init__(self, risk_reward: float = 2.0, min_gap_points: float = 0.0, **params: Any):
        super().__init__(risk_reward=risk_reward, min_gap_points=min_gap_points, **params)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        signals = pd.DataFrame(index=df.index)
        signals["signal"] = 0
        signals["stop_loss"] = np.nan
        signals["take_profit"] = np.nan
        signals["comment"] = ""

        if df.empty or len(df) < 5:
            return signals

        fvg_ind = FVGIndicator(min_gap_points=float(self.params.get("min_gap_points", 0.0)), show_mitigated=True)
        fvg_df = fvg_ind.calculate(df)

        rr = float(self.params.get("risk_reward", 2.0))
        n = len(df)
        closes = df["close"].values
        lows = df["low"].values
        highs = df["high"].values

        sig = np.zeros(n, dtype=int)
        sl_arr = np.full(n, np.nan)
        tp_arr = np.full(n, np.nan)
        comm = [""] * n

        fvg_types = fvg_df["fvg_type"].values
        fvg_tops = fvg_df["fvg_top"].values
        fvg_bots = fvg_df["fvg_bottom"].values

        for i in range(3, n):
            # Bullish FVG formation
            if fvg_types[i - 1] == "bullish" and pd.notna(fvg_bots[i - 1]):
                bot = fvg_bots[i - 1]
                entry = closes[i]
                if entry > bot:
                    risk = entry - bot
                    if risk > 0:
                        sig[i] = 1
                        sl_arr[i] = round(bot - (risk * 0.1), 5)
                        tp_arr[i] = round(entry + (risk * rr), 5)
                        comm[i] = "Bullish FVG Retest"

            # Bearish FVG formation
            elif fvg_types[i - 1] == "bearish" and pd.notna(fvg_tops[i - 1]):
                top = fvg_tops[i - 1]
                entry = closes[i]
                if entry < top:
                    risk = top - entry
                    if risk > 0:
                        sig[i] = -1
                        sl_arr[i] = round(top + (risk * 0.1), 5)
                        tp_arr[i] = round(entry - (risk * rr), 5)
                        comm[i] = "Bearish FVG Retest"

        signals["signal"] = sig
        signals["stop_loss"] = sl_arr
        signals["take_profit"] = tp_arr
        signals["comment"] = comm
        return signals
