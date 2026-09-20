from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional
import traceback

from src.utils.constants import EventType
from src.utils.logger import logger


class EventBus:
    """A lightweight decoupled publish-subscribe event bus."""

    _instance: Optional["EventBus"] = None

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[..., None]]] = defaultdict(list)

    @classmethod
    def get_instance(cls) -> "EventBus":
        """Singleton accessor if global access is needed."""
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance

    def subscribe(self, event_type: str | EventType, handler: Callable[..., None]) -> None:
        """Subscribes a callback handler to an event type."""
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        if handler not in self._subscribers[key]:
            self._subscribers[key].append(handler)

    def unsubscribe(self, event_type: str | EventType, handler: Callable[..., None]) -> None:
        """Unsubscribes a callback handler."""
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        if handler in self._subscribers[key]:
            self._subscribers[key].remove(handler)

    def emit(self, event_type: str | EventType, data: Any = None) -> None:
        """Dispatches an event with associated data to all registered listeners."""
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        handlers = list(self._subscribers.get(key, []))
        for handler in handlers:
            try:
                if data is not None:
                    handler(data)
                else:
                    handler()
            except Exception as e:
                logger.error(
                    f"Error executing event handler {handler.__name__ if hasattr(handler, '__name__') else handler} "
                    f"for event {key}: {e}\n{traceback.format_exc()}"
                )

    def clear(self) -> None:
        """Clears all subscribers."""
        self._subscribers.clear()


# Default singleton instance for convenience
event_bus = EventBus.get_instance()
