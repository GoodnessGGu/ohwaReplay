from typing import Optional
from src.drawings.base_tool import BaseDrawingTool, Drawing, DrawingPoint, DrawingStyle
from src.utils.constants import DrawingType

class TextTool(BaseDrawingTool):
    tool_type = DrawingType.TEXT

    @classmethod
    def create(cls, symbol: str, time: int, price: float, text: str, style: Optional[DrawingStyle] = None) -> Drawing:
        points = [DrawingPoint(time=time, price=price)]
        return cls.create_drawing(symbol=symbol, points=points, style=style, text=text)
