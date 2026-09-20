import pytest
from src.drawings.base_tool import Drawing, DrawingPoint, DrawingStyle
from src.drawings.drawing_store import DrawingStore
from src.drawings.fibonacci import FibonacciTool
from src.drawings.long_short import LongShortTool
from src.drawings.path import PathTool
from src.drawings.trendline import TrendlineTool
from src.drawings.volume_profile import FixedRangeVolumeProfileTool
from src.utils.constants import Direction, DrawingType


def test_drawing_serialization():
    p1 = DrawingPoint(time=1700000000, price=2000.0)
    p2 = DrawingPoint(time=1700000300, price=2015.0)
    style = DrawingStyle(color="#ff0000", line_width=3)

    drawing = TrendlineTool.create_drawing(
        symbol="XAUUSD",
        points=[p1, p2],
        style=style,
    )

    d_dict = drawing.to_dict()
    assert d_dict["type"] == "TRENDLINE"
    assert len(d_dict["points"]) == 2
    assert d_dict["style"]["color"] == "#ff0000"

    # Restore from dict
    restored = Drawing.from_dict(d_dict)
    assert restored.id == drawing.id
    assert restored.points[0].price == 2000.0
    assert restored.points[1].price == 2015.0


def test_fibonacci_calculations():
    # 2000 to 2100 (diff = 100)
    levels = FibonacciTool.calculate_levels(2000.0, 2100.0, [0.0, 0.5, 1.0])
    assert levels[0.0] == 2000.0
    assert levels[0.5] == 2050.0
    assert levels[1.0] == 2100.0


def test_long_short_tool_metrics():
    # Long: Entry 2000, SL 1990 (Risk 10), TP 2030 (Reward 30) -> RR 3.0
    metrics_long = LongShortTool.calculate_metrics(Direction.BUY, 2000.0, 1990.0, 2030.0)
    assert metrics_long.risk_amount == 10.0
    assert metrics_long.reward_amount == 30.0
    assert metrics_long.risk_reward_ratio == 3.0

    # Short: Entry 2000, SL 2010 (Risk 10), TP 1980 (Reward 20) -> RR 2.0
    metrics_short = LongShortTool.calculate_metrics(Direction.SELL, 2000.0, 2010.0, 1980.0)
    assert metrics_short.risk_amount == 10.0
    assert metrics_short.reward_amount == 20.0
    assert metrics_short.risk_reward_ratio == 2.0


def test_drawing_store_undo_redo():
    store = DrawingStore()
    d1 = TrendlineTool.create_drawing("XAUUSD", [DrawingPoint(100, 1000), DrawingPoint(200, 1010)])

    # Add drawing
    store.add_drawing(d1)
    assert len(store.get_all_drawings()) == 1

    # Undo Add
    store.undo()
    assert len(store.get_all_drawings()) == 0

    # Redo Add
    store.redo()
    assert len(store.get_all_drawings()) == 1

    # Remove drawing
    store.remove_drawing(d1.id)
    assert len(store.get_all_drawings()) == 0

    # Undo Remove
    store.undo()
    assert len(store.get_all_drawings()) == 1


def test_path_tool_creation():
    points = [
        DrawingPoint(time=1000, price=2000.0),
        DrawingPoint(time=1060, price=2010.0),
        DrawingPoint(time=1120, price=2005.0),
        DrawingPoint(time=1180, price=2025.0),
    ]
    path_drawing = PathTool.create_drawing(
        symbol="XAUUSD",
        points=points,
        text="Wave 1-2-3",
    )
    assert path_drawing.type == DrawingType.PATH
    assert len(path_drawing.points) == 4
    assert path_drawing.text == "Wave 1-2-3"
    
    # Serialization
    d_dict = path_drawing.to_dict()
    assert d_dict["type"] == "PATH"
    assert len(d_dict["points"]) == 4
    
    restored = Drawing.from_dict(d_dict)
    assert restored.id == path_drawing.id
    assert len(restored.points) == 4


def test_fixed_range_volume_profile_calculation():
    candles = [
        {"time": 100, "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 500.0},
        {"time": 200, "open": 105.0, "high": 115.0, "low": 100.0, "close": 112.0, "volume": 800.0},
        {"time": 300, "open": 112.0, "high": 114.0, "low": 102.0, "close": 104.0, "volume": 600.0},
        {"time": 400, "open": 104.0, "high": 108.0, "low": 98.0, "close": 106.0, "volume": 300.0},
    ]

    metrics = FixedRangeVolumeProfileTool.calculate_volume_profile(
        candles=candles,
        start_time=100,
        end_time=350,
        num_bins=20,
        va_percentage=0.70,
    )

    assert metrics is not None
    assert metrics.total_volume > 0
    assert metrics.val_price <= metrics.poc_price <= metrics.vah_price
    assert len(metrics.bins) == 20
    assert any(b["is_poc"] for b in metrics.bins)

