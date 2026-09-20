from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from src.utils.constants import CloseReason, Direction, PositionStatus


@dataclass
class Position:
    """Represents an open or closed simulated trading position."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = "XAUUSD"
    direction: Direction = Direction.BUY
    entry_price: float = 0.0
    current_price: float = 0.0
    lot_size: float = 1.0
    point_value: float = 100.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    open_time: Optional[datetime] = None
    open_timestamp: Optional[int] = None
    close_time: Optional[datetime] = None
    close_timestamp: Optional[int] = None
    close_price: Optional[float] = None
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    gross_pnl: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    close_reason: Optional[CloseReason] = None
    strategy: str = ""
    notes: str = ""
    tags: str = ""

    @property
    def is_open(self) -> bool:
        return self.status == PositionStatus.OPEN

    @property
    def net_pnl(self) -> float:
        """Net PnL taking commissions and fees into account."""
        if self.is_open:
            return round(self.unrealized_pnl - self.commission, 2)
        return round(self.realized_pnl - self.commission, 2)

    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """Calculates and updates unrealized gross PnL given market price."""
        self.current_price = current_price
        if self.direction == Direction.BUY:
            price_diff = current_price - self.entry_price
        else:
            price_diff = self.entry_price - current_price

        self.unrealized_pnl = round(price_diff * self.lot_size * self.point_value, 2)
        return self.unrealized_pnl

    def close(
        self,
        close_price: float,
        close_time: Optional[datetime] = None,
        close_timestamp: Optional[int] = None,
        reason: CloseReason = CloseReason.MANUAL,
    ) -> float:
        """Closes the position and finalizes realized PnL."""
        self.close_price = close_price
        self.close_time = close_time
        self.close_timestamp = close_timestamp
        self.close_reason = reason
        self.status = PositionStatus.CLOSED

        if self.direction == Direction.BUY:
            price_diff = close_price - self.entry_price
        else:
            price_diff = self.entry_price - close_price

        self.gross_pnl = round(price_diff * self.lot_size * self.point_value, 2)
        self.realized_pnl = self.gross_pnl
        self.unrealized_pnl = 0.0
        return self.realized_pnl

    def to_dict(self) -> Dict[str, Any]:
        """Serializes position to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "direction": self.direction.value if isinstance(self.direction, Direction) else str(self.direction),
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "close_price": self.close_price,
            "lot_size": self.lot_size,
            "point_value": self.point_value,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "open_time": self.open_time.isoformat() if self.open_time else None,
            "open_timestamp": self.open_timestamp,
            "close_time": self.close_time.isoformat() if self.close_time else None,
            "close_timestamp": self.close_timestamp,
            "gross_pnl": self.gross_pnl,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "net_pnl": self.net_pnl,
            "commission": self.commission,
            "status": self.status.value if isinstance(self.status, PositionStatus) else str(self.status),
            "close_reason": self.close_reason.value if self.close_reason else None,
            "strategy": self.strategy,
            "notes": self.notes,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Position":
        """Deserializes position from dictionary."""
        return cls(
            id=d.get("id", str(uuid.uuid4())[:8]),
            symbol=d.get("symbol", "XAUUSD"),
            direction=Direction(d.get("direction", "BUY")),
            entry_price=float(d.get("entry_price", 0.0)),
            current_price=float(d.get("current_price", 0.0)),
            close_price=float(d["close_price"]) if d.get("close_price") is not None else None,
            lot_size=float(d.get("lot_size", 1.0)),
            point_value=float(d.get("point_value", 100.0)),
            stop_loss=float(d["stop_loss"]) if d.get("stop_loss") is not None else None,
            take_profit=float(d["take_profit"]) if d.get("take_profit") is not None else None,
            open_time=datetime.fromisoformat(d["open_time"]) if d.get("open_time") else None,
            open_timestamp=d.get("open_timestamp"),
            close_time=datetime.fromisoformat(d["close_time"]) if d.get("close_time") else None,
            close_timestamp=d.get("close_timestamp"),
            gross_pnl=float(d.get("gross_pnl", 0.0)),
            realized_pnl=float(d.get("realized_pnl", 0.0)),
            unrealized_pnl=float(d.get("unrealized_pnl", 0.0)),
            commission=float(d.get("commission", 0.0)),
            status=PositionStatus(d.get("status", "OPEN")),
            close_reason=CloseReason(d["close_reason"]) if d.get("close_reason") else None,
            strategy=d.get("strategy", ""),
            notes=d.get("notes", ""),
            tags=d.get("tags", ""),
        )
