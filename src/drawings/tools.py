from typing import List, Optional
from src.drawings.base_tool import BaseDrawingTool, Drawing, DrawingPoint, DrawingStyle
from src.utils.constants import DrawingType


class TrendlineTool(BaseDrawingTool):
    tool_type = DrawingType.TRENDLINE


class RayTool(BaseDrawingTool):
    tool_type = DrawingType.RAY


class HorizontalLineTool(BaseDrawingTool):
    tool_type = DrawingType.HORIZONTAL_LINE

    @classmethod
    def create(cls, symbol: str, price: float, style: Optional[DrawingStyle] = None) -> Drawing:
        points = [DrawingPoint(time=0, price=price)]
        return cls.create_drawing(symbol=symbol, points=points, style=style)


class VerticalLineTool(BaseDrawingTool):
    tool_type = DrawingType.VERTICAL_LINE

    @classmethod
    def create(cls, symbol: str, time: int, style: Optional[DrawingStyle] = None) -> Drawing:
        points = [DrawingPoint(time=time, price=0.0)]
        return cls.create_drawing(symbol=symbol, points=points, style=style)


class RectangleTool(BaseDrawingTool):
    tool_type = DrawingType.RECTANGLE


class TextTool(BaseDrawingTool):
    tool_type = DrawingType.TEXT

    @classmethod
    def create(cls, symbol: str, time: int, price: float, text: str, style: Optional[DrawingStyle] = None) -> Drawing:
        points = [DrawingPoint(time=time, price=price)]
        return cls.create_drawing(symbol=symbol, points=points, style=style, text=text)


class ArrowTool(BaseDrawingTool):
    tool_type = DrawingType.ARROW
