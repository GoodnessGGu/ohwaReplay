from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid

from src.events.event_bus import EventBus, event_bus
from src.utils.constants import EventType
from src.utils.logger import logger


class AlertCondition(str, Enum):
    PRICE_ABOVE = "PRICE_ABOVE"
    PRICE_BELOW = "PRICE_BELOW"
    PRICE_CROSSES = "PRICE_CROSSES"
    LINE_TOUCHED = "LINE_TOUCHED"


@dataclass
class Alert:
    """Represents a price or technical level alert."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = "XAUUSD"
    condition: AlertCondition = AlertCondition.PRICE_CROSSES
    target_price: float = 0.0
    message: str = ""
    enabled: bool = True
    sound_enabled: bool = True
    notification_enabled: bool = True
    is_triggered: bool = False
    is_recurring: bool = False
    last_price: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "condition": self.condition.value if isinstance(self.condition, AlertCondition) else str(self.condition),
            "target_price": self.target_price,
            "message": self.message,
            "enabled": self.enabled,
            "sound_enabled": self.sound_enabled,
            "notification_enabled": self.notification_enabled,
            "is_triggered": self.is_triggered,
            "is_recurring": self.is_recurring,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Alert":
        return cls(
            id=d.get("id", str(uuid.uuid4())[:8]),
            symbol=d.get("symbol", "XAUUSD"),
            condition=AlertCondition(d.get("condition", "PRICE_CROSSES")),
            target_price=float(d.get("target_price", 0.0)),
            message=d.get("message", ""),
            enabled=d.get("enabled", True),
            sound_enabled=d.get("sound_enabled", True),
            notification_enabled=d.get("notification_enabled", True),
            is_triggered=d.get("is_triggered", False),
            is_recurring=d.get("is_recurring", False),
        )


class AlertManager:
    """Manages active alerts and checks price triggers on candle events."""

    def __init__(self, event_bus_instance: Optional[EventBus] = None):
        self.bus = event_bus_instance or event_bus
        self.alerts: Dict[str, Alert] = {}

    def add_alert(self, alert: Alert) -> None:
        self.alerts[alert.id] = alert

    def remove_alert(self, alert_id: str) -> bool:
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            return True
        return False

    def process_price(self, symbol: str, current_price: float, high: float, low: float) -> List[Alert]:
        """Evaluates all active alerts for the given symbol."""
        triggered: List[Alert] = []

        for alert in list(self.alerts.values()):
            if not alert.enabled or (alert.is_triggered and not alert.is_recurring):
                continue
            if alert.symbol.upper() != symbol.upper():
                continue

            hit = False
            prev_price = alert.last_price if alert.last_price is not None else current_price

            if alert.condition == AlertCondition.PRICE_ABOVE:
                if high >= alert.target_price:
                    hit = True
            elif alert.condition == AlertCondition.PRICE_BELOW:
                if low <= alert.target_price:
                    hit = True
            elif alert.condition == AlertCondition.PRICE_CROSSES or alert.condition == AlertCondition.LINE_TOUCHED:
                if low <= alert.target_price <= high:
                    hit = True
                elif (prev_price < alert.target_price <= current_price) or (prev_price > alert.target_price >= current_price):
                    hit = True

            alert.last_price = current_price

            if hit:
                alert.is_triggered = True
                if not alert.is_recurring:
                    alert.enabled = False
                triggered.append(alert)
                msg = alert.message or f"Price alert triggered for {symbol} at {current_price:.2f}"
                self.bus.emit(EventType.PRICE_ALERT, {
                    "alert_id": alert.id,
                    "symbol": symbol,
                    "price": current_price,
                    "target_price": alert.target_price,
                    "message": msg,
                    "sound": alert.sound_enabled,
                })

        return triggered

    def clear(self) -> None:
        self.alerts.clear()

    def serialize(self) -> List[dict]:
        return [a.to_dict() for a in self.alerts.values()]

    def deserialize(self, data: List[dict]) -> None:
        self.clear()
        for item in data:
            try:
                a = Alert.from_dict(item)
                self.alerts[a.id] = a
            except Exception as e:
                logger.error(f"Failed to deserialize alert: {e}")
