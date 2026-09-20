from dataclasses import dataclass
from typing import Any, Dict, Optional
from src.drawings.base_tool import BaseDrawingTool, Drawing, DrawingPoint, DrawingStyle
from src.utils.constants import Direction, DrawingType


@dataclass
class PositionDrawingMetrics:
    direction: Direction
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float


class LongShortTool(BaseDrawingTool):
    """
    Analysis tool for visualizing Risk/Reward setups on the chart.
    CRITICAL: This tool does NOT open or close trades.
    """

    @classmethod
    def calculate_metrics(
        cls,
        direction: Direction,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
    ) -> PositionDrawingMetrics:
        if direction == Direction.BUY:
            risk = max(0.0, entry_price - stop_loss)
            reward = max(0.0, take_profit - entry_price)
        else:
            risk = max(0.0, stop_loss - entry_price)
            reward = max(0.0, entry_price - take_profit)

        rr = round(reward / risk, 2) if risk > 0 else 0.0

        return PositionDrawingMetrics(
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=round(risk, 4),
            reward_amount=round(reward, 4),
            risk_reward_ratio=rr,
        )

    @classmethod
    def create_long(
        cls,
        symbol: str,
        entry_point: DrawingPoint,
        sl_price: float,
        tp_price: float,
        style: Optional[DrawingStyle] = None,
    ) -> Drawing:
        metrics = cls.calculate_metrics(Direction.BUY, entry_point.price, sl_price, tp_price)
        points = [
            entry_point,
            DrawingPoint(time=entry_point.time, price=sl_price),
            DrawingPoint(time=entry_point.time, price=tp_price),
        ]
        return cls.create_drawing(
            symbol=symbol,
            points=points,
            style=style or DrawingStyle(color="#26a69a", fill_color="rgba(38, 166, 154, 0.2)"),
            metadata={
                "tool": "LONG_POSITION",
                "entry": entry_point.price,
                "sl": sl_price,
                "tp": tp_price,
                "rr": metrics.risk_reward_ratio,
                "risk": metrics.risk_amount,
                "reward": metrics.reward_amount,
            },
        )

    @classmethod
    def create_short(
        cls,
        symbol: str,
        entry_point: DrawingPoint,
        sl_price: float,
        tp_price: float,
        style: Optional[DrawingStyle] = None,
    ) -> Drawing:
        metrics = cls.calculate_metrics(Direction.SELL, entry_point.price, sl_price, tp_price)
        points = [
            entry_point,
            DrawingPoint(time=entry_point.time, price=sl_price),
            DrawingPoint(time=entry_point.time, price=tp_price),
        ]
        return Drawing(
            type=DrawingType.SHORT_POSITION,
            symbol=symbol,
            points=points,
            style=style or DrawingStyle(color="#ef5350", fill_color="rgba(239, 83, 80, 0.2)"),
            metadata={
                "tool": "SHORT_POSITION",
                "entry": entry_point.price,
                "sl": sl_price,
                "tp": tp_price,
                "rr": metrics.risk_reward_ratio,
                "risk": metrics.risk_amount,
                "reward": metrics.reward_amount,
            },
        )
