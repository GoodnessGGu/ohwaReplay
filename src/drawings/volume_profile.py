from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from src.drawings.base_tool import BaseDrawingTool, Drawing, DrawingPoint, DrawingStyle
from src.utils.constants import DrawingType


@dataclass
class VolumeProfileMetrics:
    poc_price: float
    vah_price: float
    val_price: float
    total_volume: float
    value_area_volume: float
    bins: List[Dict[str, Any]]


class FixedRangeVolumeProfileTool(BaseDrawingTool):
    """
    Fixed Range Volume Profile (FRVP) tool.
    Computes horizontal volume distribution, Point of Control (POC),
    and Value Area (VAH/VAL) over a specified historical range.
    """
    tool_type = DrawingType.VOLUME_PROFILE

    @classmethod
    def create_drawing(
        cls,
        symbol: str,
        points: List[DrawingPoint],
        style: Optional[DrawingStyle] = None,
        text: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Drawing:
        default_style = style or DrawingStyle(
            color="#2962ff",
            line_width=1,
            fill_color="rgba(41, 98, 255, 0.5)",
            opacity=0.6,
        )
        return Drawing(
            type=cls.tool_type,
            symbol=symbol,
            points=points,
            style=default_style,
            text=text,
            metadata=metadata or {
                "num_bins": 30,
                "va_percentage": 0.70,
                "poc_color": "#ff9800",
                "vah_val_color": "#2962ff",
            },
        )

    @staticmethod
    def calculate_volume_profile(
        candles: List[Dict[str, Any]],
        start_time: int,
        end_time: int,
        num_bins: int = 30,
        va_percentage: float = 0.70,
    ) -> Optional[VolumeProfileMetrics]:
        """
        Calculates volume profile bins, POC, VAH, and VAL from candlestick data.
        """
        t_min = min(start_time, end_time)
        t_max = max(start_time, end_time)

        # Filter candles in range
        range_candles = [c for c in candles if t_min <= c["time"] <= t_max]
        if not range_candles:
            return None

        lows = [float(c["low"]) for c in range_candles]
        highs = [float(c["high"]) for c in range_candles]
        min_p = min(lows)
        max_p = max(highs)

        if max_p <= min_p:
            max_p = min_p + 1.0

        bin_size = (max_p - min_p) / num_bins
        bin_up_vol = np.zeros(num_bins)
        bin_down_vol = np.zeros(num_bins)

        for c in range_candles:
            c_open = float(c["open"])
            c_close = float(c["close"])
            c_low = float(c["low"])
            c_high = float(c["high"])
            c_vol = float(c.get("volume", 100.0))

            is_up = c_close >= c_open

            # Distribute volume across touched bins
            low_idx = max(0, min(num_bins - 1, int((c_low - min_p) / bin_size)))
            high_idx = max(0, min(num_bins - 1, int((c_high - min_p) / bin_size)))

            span_bins = max(1, high_idx - low_idx + 1)
            vol_per_bin = c_vol / span_bins

            for b in range(low_idx, high_idx + 1):
                if is_up:
                    bin_up_vol[b] += vol_per_bin
                else:
                    bin_down_vol[b] += vol_per_bin

        total_bin_vol = bin_up_vol + bin_down_vol
        total_vol = float(np.sum(total_bin_vol))
        if total_vol <= 0:
            return None

        # Point of Control (POC) = bin with max total volume
        poc_idx = int(np.argmax(total_bin_vol))
        poc_price = min_p + (poc_idx + 0.5) * bin_size

        # Value Area calculation (e.g. 70% of total volume expanding outward from POC)
        target_va_vol = total_vol * va_percentage
        curr_va_vol = float(total_bin_vol[poc_idx])
        va_indices = {poc_idx}

        up_idx = poc_idx + 1
        down_idx = poc_idx - 1

        while curr_va_vol < target_va_vol and (up_idx < num_bins or down_idx >= 0):
            up_v = total_bin_vol[up_idx] if up_idx < num_bins else 0.0
            down_v = total_bin_vol[down_idx] if down_idx >= 0 else 0.0

            if up_v >= down_v and up_idx < num_bins:
                curr_va_vol += up_v
                va_indices.add(up_idx)
                up_idx += 1
            elif down_idx >= 0:
                curr_va_vol += down_v
                va_indices.add(down_idx)
                down_idx -= 1
            elif up_idx < num_bins:
                curr_va_vol += up_v
                va_indices.add(up_idx)
                up_idx += 1
            else:
                break

        val_idx = min(va_indices)
        vah_idx = max(va_indices)

        val_price = min_p + val_idx * bin_size
        vah_price = min_p + (vah_idx + 1) * bin_size

        bins_data = []
        for i in range(num_bins):
            b_low = min_p + i * bin_size
            b_high = b_low + bin_size
            b_mid = (b_low + b_high) / 2.0
            bins_data.append({
                "index": i,
                "price_low": b_low,
                "price_high": b_high,
                "price_mid": b_mid,
                "up_volume": float(bin_up_vol[i]),
                "down_volume": float(bin_down_vol[i]),
                "total_volume": float(total_bin_vol[i]),
                "is_poc": (i == poc_idx),
                "in_value_area": (i in va_indices),
            })

        return VolumeProfileMetrics(
            poc_price=poc_price,
            vah_price=vah_price,
            val_price=val_price,
            total_volume=total_vol,
            value_area_volume=curr_va_vol,
            bins=bins_data,
        )
