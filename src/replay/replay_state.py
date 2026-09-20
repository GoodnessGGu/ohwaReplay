from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.utils.constants import ReplayStateEnum


@dataclass
class ReplayState:
    """Represents the current state of the replay engine."""
    status: ReplayStateEnum = ReplayStateEnum.IDLE
    current_index: int = 0
    start_index: int = 0
    total_candles: int = 0
    speed: float = 1.0
    timeframe: str = "5m"
    symbol: str = "XAUUSD"
    current_timestamp: Optional[int] = None
    current_datetime: Optional[datetime] = None
    is_playing: bool = False

    @property
    def progress_pct(self) -> float:
        """Percentage of replay completed."""
        if self.total_candles <= 1:
            return 0.0
        return min(100.0, max(0.0, (self.current_index / (self.total_candles - 1)) * 100.0))
