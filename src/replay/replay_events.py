from dataclasses import dataclass
from typing import Any, Dict, Optional
import pandas as pd


@dataclass
class CandleAdvancedEvent:
    """Event payload emitted whenever the replay advances to a new candle."""
    index: int
    candle: Dict[str, Any]
    symbol: str
    timeframe: str
    total_candles: int
    is_last: bool


@dataclass
class ReplayStateChangedEvent:
    """Event payload emitted when play/pause/reset/speed status changes."""
    status: str
    current_index: int
    speed: float
    timeframe: str
