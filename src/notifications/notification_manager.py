from typing import Any, Callable, Dict, List, Optional
from src.events.event_bus import EventBus, event_bus
from src.notifications.alerts import Alert, AlertManager
from src.notifications.sound_manager import SoundManager
from src.utils.constants import EventType
from src.utils.logger import logger


class NotificationManager:
    """Coordinates alerts, sounds, and visual UI notifications via EventBus."""

    def __init__(
        self,
        event_bus_instance: Optional[EventBus] = None,
        sound_manager: Optional[SoundManager] = None,
        alert_manager: Optional[AlertManager] = None,
    ):
        self.bus = event_bus_instance or event_bus
        self.sound_mgr = sound_manager or SoundManager()
        self.alert_mgr = alert_manager or AlertManager(self.bus)
        self._setup_event_listeners()

    def _setup_event_listeners(self) -> None:
        self.bus.subscribe(EventType.ORDER_OPENED, self._on_order_opened)
        self.bus.subscribe(EventType.ORDER_CLOSED, self._on_order_closed)
        self.bus.subscribe(EventType.SL_HIT, self._on_sl_hit)
        self.bus.subscribe(EventType.TP_HIT, self._on_tp_hit)
        self.bus.subscribe(EventType.PRICE_ALERT, self._on_price_alert)
        self.bus.subscribe(EventType.CANDLE_ADVANCED, self._on_candle_advanced)

    def _on_order_opened(self, data: Dict[str, Any]) -> None:
        self.sound_mgr.play("order_open")

    def _on_order_closed(self, data: Dict[str, Any]) -> None:
        self.sound_mgr.play("order_close")

    def _on_sl_hit(self, data: Dict[str, Any]) -> None:
        self.sound_mgr.play("sl")

    def _on_tp_hit(self, data: Dict[str, Any]) -> None:
        self.sound_mgr.play("tp")

    def _on_price_alert(self, data: Dict[str, Any]) -> None:
        if data.get("sound", True):
            self.sound_mgr.play("alert")

    def _on_candle_advanced(self, event_obj: Any) -> None:
        if hasattr(event_obj, "candle") and hasattr(event_obj, "symbol"):
            c = event_obj.candle
            self.alert_mgr.process_price(
                symbol=event_obj.symbol,
                current_price=float(c.get("close", 0.0)),
                high=float(c.get("high", 0.0)),
                low=float(c.get("low", 0.0)),
            )
