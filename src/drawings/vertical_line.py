from typing import Optional
from src.drawings.base_tool import BaseDrawingTool, Drawing, DrawingPoint, DrawingStyle
from src.utils.constants import DrawingType

class VerticalLineTool(BaseDrawingTool):
    tool_type = DrawingType.VERTICAL_LINE

    @classmethod
    def create(cls, symbol: str, time: int, style: Optional[DrawingStyle] = None) -> Drawing:
        points = [DrawingPoint(time=time, price=0.0)]
        return cls.create_drawing(symbol=symbol, points=points, style=style)
