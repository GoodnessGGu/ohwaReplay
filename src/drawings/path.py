from typing import List, Optional, Dict, Any
from src.drawings.base_tool import BaseDrawingTool, Drawing, DrawingPoint, DrawingStyle
from src.utils.constants import DrawingType


class PathTool(BaseDrawingTool):
    """
    Multi-point Path / Polyline tool.
    Connects multiple sequential anchor points on the chart to trace waves and price paths.
    """
    tool_type = DrawingType.PATH

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
            line_width=2,
            line_style="solid",
        )
        return Drawing(
            type=cls.tool_type,
            symbol=symbol,
            points=points,
            style=default_style,
            text=text,
            metadata=metadata or {},
        )
