from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from src.utils.constants import DrawingType


@dataclass
class DrawingPoint:
    """Represents an anchor point in time and price space."""
    time: int       # Unix timestamp in seconds
    price: float    # Price level
    bar_index: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time": self.time,
            "price": self.price,
            "bar_index": self.bar_index,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DrawingPoint":
        return cls(
            time=int(d.get("time", 0)),
            price=float(d.get("price", 0.0)),
            bar_index=d.get("bar_index"),
        )


@dataclass
class DrawingStyle:
    """Styling properties for visual chart drawings."""
    color: str = "#2962ff"
    line_width: int = 2
    line_style: str = "solid"  # solid, dashed, dotted
    fill_color: str = "rgba(41, 98, 255, 0.2)"
    text_color: str = "#ffffff"
    font_size: int = 12
    opacity: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "color": self.color,
            "line_width": self.line_width,
            "line_style": self.line_style,
            "fill_color": self.fill_color,
            "text_color": self.text_color,
            "font_size": self.font_size,
            "opacity": self.opacity,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DrawingStyle":
        return cls(
            color=d.get("color", "#2962ff"),
            line_width=int(d.get("line_width", 2)),
            line_style=d.get("line_style", "solid"),
            fill_color=d.get("fill_color", "rgba(41, 98, 255, 0.2)"),
            text_color=d.get("text_color", "#ffffff"),
            font_size=int(d.get("font_size", 12)),
            opacity=float(d.get("opacity", 1.0)),
        )


@dataclass
class Drawing:
    """Base persistent drawing object."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: DrawingType = DrawingType.TRENDLINE
    symbol: str = "XAUUSD"
    points: List[DrawingPoint] = field(default_factory=list)
    style: DrawingStyle = field(default_factory=DrawingStyle)
    text: str = ""
    locked: bool = False
    visible: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, DrawingType) else str(self.type),
            "symbol": self.symbol,
            "points": [p.to_dict() for p in self.points],
            "style": self.style.to_dict(),
            "text": self.text,
            "locked": self.locked,
            "visible": self.visible,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Drawing":
        return cls(
            id=d.get("id", str(uuid.uuid4())[:8]),
            type=DrawingType(d.get("type", "TRENDLINE")),
            symbol=d.get("symbol", "XAUUSD"),
            points=[DrawingPoint.from_dict(p) for p in d.get("points", [])],
            style=DrawingStyle.from_dict(d.get("style", {})),
            text=d.get("text", ""),
            locked=d.get("locked", False),
            visible=d.get("visible", True),
            metadata=d.get("metadata", {}),
        )


class BaseDrawingTool:
    """Abstract interface for drawing tool handlers."""
    tool_type: DrawingType = DrawingType.CURSOR

    @classmethod
    def create_drawing(
        cls,
        symbol: str,
        points: List[DrawingPoint],
        style: Optional[DrawingStyle] = None,
        text: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Drawing:
        return Drawing(
            type=cls.tool_type,
            symbol=symbol,
            points=points,
            style=style or DrawingStyle(),
            text=text,
            metadata=metadata or {},
        )
