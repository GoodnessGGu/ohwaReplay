from typing import Dict, List, Optional
from src.drawings.base_tool import BaseDrawingTool, Drawing, DrawingPoint, DrawingStyle
from src.utils.constants import DrawingType


class FibonacciTool(BaseDrawingTool):
    tool_type = DrawingType.FIBONACCI
    DEFAULT_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618]

    @classmethod
    def calculate_levels(
        cls,
        p1_price: float,
        p2_price: float,
        custom_levels: Optional[List[float]] = None,
    ) -> Dict[float, float]:
        """
        Calculates absolute price levels for each fibonacci ratio.
        p1 is start (0.0), p2 is end (1.0).
        """
        levels = custom_levels or cls.DEFAULT_LEVELS
        diff = p2_price - p1_price
        result = {}
        for lvl in levels:
            price = p1_price + (diff * lvl)
            result[lvl] = round(price, 5)
        return result

    @classmethod
    def create(
        cls,
        symbol: str,
        p1: DrawingPoint,
        p2: DrawingPoint,
        levels: Optional[List[float]] = None,
        style: Optional[DrawingStyle] = None,
    ) -> Drawing:
        metadata = {"levels": levels or cls.DEFAULT_LEVELS}
        return cls.create_drawing(
            symbol=symbol,
            points=[p1, p2],
            style=style or DrawingStyle(color="#ff9800"),
            metadata=metadata,
        )
