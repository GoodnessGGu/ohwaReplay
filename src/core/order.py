from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from src.utils.constants import OrderType, Direction


@dataclass
class Order:
    """Represents an order request to be processed by the account engine."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = "XAUUSD"
    order_type: OrderType = OrderType.MARKET_BUY
    lot_size: float = 1.0
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: Optional[int] = None
    datetime: Optional[datetime] = None
    strategy: str = ""
    notes: str = ""
    tags: str = ""

    @property
    def direction(self) -> Direction:
        if self.order_type in (OrderType.MARKET_BUY, OrderType.BUY_LIMIT, OrderType.BUY_STOP):
            return Direction.BUY
        return Direction.SELL

    @property
    def is_pending(self) -> bool:
        return self.order_type in (
            OrderType.BUY_LIMIT,
            OrderType.BUY_STOP,
            OrderType.SELL_LIMIT,
            OrderType.SELL_STOP,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "order_type": self.order_type.value if hasattr(self.order_type, "value") else str(self.order_type),
            "direction": self.direction.value,
            "lot_size": self.lot_size,
            "price": self.price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "timestamp": self.timestamp,
            "datetime": self.datetime.isoformat() if self.datetime else None,
            "strategy": self.strategy,
            "notes": self.notes,
            "tags": self.tags,
        }
