from typing import Optional
from src.drawings.base_tool import BaseDrawingTool, Drawing, DrawingPoint, DrawingStyle
from src.utils.constants import DrawingType

class HorizontalLineTool(BaseDrawingTool):
    tool_type = DrawingType.HORIZONTAL_LINE

    @classmethod
    def create(cls, symbol: str, price: float, style: Optional[DrawingStyle] = None) -> Drawing:
        points = [DrawingPoint(time=0, price=price)]
        return cls.create_drawing(symbol=symbol, points=points, style=style)
