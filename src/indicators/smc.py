from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from src.indicators.base_indicator import BaseIndicator


class FVGIndicator(BaseIndicator):
    """
    Fair Value Gap (FVG) / Imbalance Indicator.
    Identifies 3-candle imbalances (Bullish FVG: Low[i] > High[i-2], Bearish FVG: High[i] < Low[i-2])
    and tracks mitigation status as price trades through the gap.
    """
    name = "FVG"
    display_name = "Fair Value Gaps (SMC FVG)"
    overlay = True

    def __init__(
        self,
        min_gap_points: float = 0.0,
        show_mitigated: bool = False,
        bullish_color: str = "#26a69a",
        bearish_color: str = "#ef5350",
        **params: Any
    ):
        super().__init__(
            min_gap_points=min_gap_points,
            show_mitigated=show_mitigated,
            bullish_color=bullish_color,
            bearish_color=bearish_color,
            **params
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or len(df) < 3:
            return pd.DataFrame(index=df.index)

        res = pd.DataFrame(index=df.index)
        n = len(df)

        fvg_top = [np.nan] * n
        fvg_bottom = [np.nan] * n
        fvg_type = [""] * n
        fvg_mitigated = [False] * n

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values
        times = df["time"].values if "time" in df.columns else np.arange(n)

        min_gap = float(self.params.get("min_gap_points", 0.0))
        show_mit = bool(self.params.get("show_mitigated", False))

        active_fvgs: List[Dict[str, Any]] = []

        for i in range(2, n):
            # 1. Bullish FVG: Low of candle i > High of candle i-2
            if lows[i] > highs[i - 2] + min_gap:
                top = lows[i]
                bot = highs[i - 2]
                active_fvgs.append({
                    "start_idx": i - 1,
                    "type": "bullish",
                    "top": top,
                    "bottom": bot,
                    "mitigated": False,
                    "mitigated_idx": None,
                })

            # 2. Bearish FVG: High of candle i < Low of candle i-2
            elif highs[i] < lows[i - 2] - min_gap:
                top = lows[i - 2]
                bot = highs[i]
                active_fvgs.append({
                    "start_idx": i - 1,
                    "type": "bearish",
                    "top": top,
                    "bottom": bot,
                    "mitigated": False,
                    "mitigated_idx": None,
                })

            # Check mitigation of existing active FVGs by candle i
            for fvg in active_fvgs:
                if not fvg["mitigated"]:
                    if fvg["type"] == "bullish" and lows[i] <= fvg["bottom"]:
                        fvg["mitigated"] = True
                        fvg["mitigated_idx"] = i
                    elif fvg["type"] == "bearish" and highs[i] >= fvg["top"]:
                        fvg["mitigated"] = True
                        fvg["mitigated_idx"] = i

        # Assign values for series representation
        for fvg in active_fvgs:
            if not fvg["mitigated"] or show_mit:
                idx = fvg["start_idx"]
                fvg_top[idx] = fvg["top"]
                fvg_bottom[idx] = fvg["bottom"]
                fvg_type[idx] = fvg["type"]
                fvg_mitigated[idx] = fvg["mitigated"]

        res["fvg_top"] = fvg_top
        res["fvg_bottom"] = fvg_bottom
        res["fvg_type"] = fvg_type
        res["fvg_mitigated"] = fvg_mitigated
        return res


class MarketStructureIndicator(BaseIndicator):
    """
    Market Structure Indicator (Break of Structure BOS & Change of Character CHoCH).
    Identifies fractal swing points, tracks trend direction, and marks structural breaks.
    """
    name = "MarketStructure"
    display_name = "Market Structure (BOS / CHoCH)"
    overlay = True

    def __init__(
        self,
        swing_length: int = 5,
        show_bos: bool = True,
        show_choch: bool = True,
        **params: Any
    ):
        super().__init__(
            swing_length=swing_length,
            show_bos=show_bos,
            show_choch=show_choch,
            **params
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or len(df) < 10:
            return pd.DataFrame(index=df.index)

        res = pd.DataFrame(index=df.index)
        n = len(df)
        k = int(self.params.get("swing_length", 5))

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        swing_highs: List[Dict[str, Any]] = []
        swing_lows: List[Dict[str, Any]] = []

        # Find pivot swing highs and swing lows
        for i in range(k, n - k):
            # Pivot High
            if all(highs[i] >= highs[i - j] for j in range(1, k + 1)) and \
               all(highs[i] > highs[i + j] for j in range(1, k + 1)):
                swing_highs.append({"index": i, "price": highs[i], "broken": False})

            # Pivot Low
            if all(lows[i] <= lows[i - j] for j in range(1, k + 1)) and \
               all(lows[i] < lows[i + j] for j in range(1, k + 1)):
                swing_lows.append({"index": i, "price": lows[i], "broken": False})

        bos_levels = [np.nan] * n
        choch_levels = [np.nan] * n
        structure_type = [""] * n
        trend_direction = [0] * n  # +1 bullish, -1 bearish

        current_trend = 0  # 1 = up, -1 = down

        # Detect BOS and CHoCH events
        for i in range(n):
            close = closes[i]

            # Check break of recent swing highs
            for sh in swing_highs:
                if sh["index"] < i and not sh["broken"] and close > sh["price"]:
                    sh["broken"] = True
                    if current_trend == 1:
                        # Continuation in uptrend -> BOS
                        bos_levels[i] = sh["price"]
                        structure_type[i] = "BOS_BULL"
                    else:
                        # Reversal from downtrend/neutral -> CHoCH
                        choch_levels[i] = sh["price"]
                        structure_type[i] = "CHOCH_BULL"
                        current_trend = 1

            # Check break of recent swing lows
            for sl in swing_lows:
                if sl["index"] < i and not sl["broken"] and close < sl["price"]:
                    sl["broken"] = True
                    if current_trend == -1:
                        # Continuation in downtrend -> BOS
                        bos_levels[i] = sl["price"]
                        structure_type[i] = "BOS_BEAR"
                    else:
                        # Reversal from uptrend/neutral -> CHoCH
                        choch_levels[i] = sl["price"]
                        structure_type[i] = "CHOCH_BEAR"
                        current_trend = -1

            trend_direction[i] = current_trend

        res["bos_level"] = bos_levels
        res["choch_level"] = choch_levels
        res["structure_type"] = structure_type
        res["trend_direction"] = trend_direction
        return res
