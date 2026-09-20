from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from src.drawings.base_tool import Drawing, DrawingPoint, DrawingStyle
from src.events.event_bus import EventBus, event_bus
from src.utils.constants import EventType
from src.utils.logger import logger


class Command(ABC):
    """Abstract command for undo/redo operations."""
    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass


class AddDrawingCommand(Command):
    def __init__(self, store: "DrawingStore", drawing: Drawing, emit_event: bool = True):
        self.store = store
        self.drawing = drawing
        self.emit_event = emit_event

    def execute(self) -> None:
        self.store._drawings[self.drawing.id] = self.drawing
        if self.emit_event:
            self.store.bus.emit(EventType.DRAWING_CREATED, self.drawing.to_dict())

    def undo(self) -> None:
        if self.drawing.id in self.store._drawings:
            del self.store._drawings[self.drawing.id]
            if self.emit_event:
                self.store.bus.emit(EventType.DRAWING_DELETED, {"id": self.drawing.id})


class DeleteDrawingCommand(Command):
    def __init__(self, store: "DrawingStore", drawing: Drawing, emit_event: bool = True):
        self.store = store
        self.drawing = drawing
        self.emit_event = emit_event

    def execute(self) -> None:
        if self.drawing.id in self.store._drawings:
            del self.store._drawings[self.drawing.id]
            if self.emit_event:
                self.store.bus.emit(EventType.DRAWING_DELETED, {"id": self.drawing.id})

    def undo(self) -> None:
        self.store._drawings[self.drawing.id] = self.drawing
        if self.emit_event:
            self.store.bus.emit(EventType.DRAWING_CREATED, self.drawing.to_dict())


class ModifyDrawingCommand(Command):
    def __init__(
        self,
        store: "DrawingStore",
        drawing_id: str,
        old_points: List[DrawingPoint],
        new_points: List[DrawingPoint],
        old_style: DrawingStyle,
        new_style: DrawingStyle,
        emit_event: bool = True,
    ):
        self.store = store
        self.drawing_id = drawing_id
        self.old_points = old_points
        self.new_points = new_points
        self.old_style = old_style
        self.new_style = new_style
        self.emit_event = emit_event

    def execute(self) -> None:
        if self.drawing_id in self.store._drawings:
            d = self.store._drawings[self.drawing_id]
            d.points = [DrawingPoint(p.time, p.price, p.bar_index) for p in self.new_points]
            d.style = DrawingStyle.from_dict(self.new_style.to_dict())
            if self.emit_event:
                self.store.bus.emit(EventType.DRAWING_UPDATED, d.to_dict())

    def undo(self) -> None:
        if self.drawing_id in self.store._drawings:
            d = self.store._drawings[self.drawing_id]
            d.points = [DrawingPoint(p.time, p.price, p.bar_index) for p in self.old_points]
            d.style = DrawingStyle.from_dict(self.old_style.to_dict())
            if self.emit_event:
                self.store.bus.emit(EventType.DRAWING_UPDATED, d.to_dict())


class DrawingStore:
    """Manages drawings on the chart with full undo/redo capabilities."""

    def __init__(self, event_bus_instance: Optional[EventBus] = None):
        self.bus = event_bus_instance or event_bus
        self._drawings: Dict[str, Drawing] = {}
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self.selected_drawing_id: Optional[str] = None

    def add_drawing(self, drawing: Any, emit_event: bool = False) -> None:
        """Adds a new drawing and pushes to undo stack."""
        if isinstance(drawing, dict):
            drawing = Drawing.from_dict(drawing)
        if not isinstance(drawing, Drawing):
            return

        cmd = AddDrawingCommand(self, drawing, emit_event=emit_event)
        cmd.execute()
        self._undo_stack.append(cmd)
        self._redo_stack.clear()

    def remove_drawing(self, drawing_id: str, emit_event: bool = False) -> bool:
        """Removes a drawing and pushes to undo stack."""
        if drawing_id not in self._drawings:
            return False
        d = self._drawings[drawing_id]
        cmd = DeleteDrawingCommand(self, d, emit_event=emit_event)
        cmd.execute()
        self._undo_stack.append(cmd)
        self._redo_stack.clear()
        if self.selected_drawing_id == drawing_id:
            self.selected_drawing_id = None
        return True

    def delete_drawing(self, drawing_id: str, emit_event: bool = False) -> bool:
        """Alias for remove_drawing."""
        return self.remove_drawing(drawing_id, emit_event=emit_event)

    def update_drawing(
        self,
        drawing_or_id: Any,
        new_points: Optional[List[DrawingPoint]] = None,
        new_style: Optional[DrawingStyle] = None,
        emit_event: bool = False,
    ) -> bool:
        """Updates drawing points/styles with command tracking."""
        if isinstance(drawing_or_id, dict):
            drawing_obj = Drawing.from_dict(drawing_or_id)
            drawing_id = drawing_obj.id
            new_points = new_points or drawing_obj.points
            new_style = new_style or drawing_obj.style
        elif isinstance(drawing_or_id, Drawing):
            drawing_id = drawing_or_id.id
            new_points = new_points or drawing_or_id.points
            new_style = new_style or drawing_or_id.style
        else:
            drawing_id = str(drawing_or_id)

        if drawing_id not in self._drawings:
            if isinstance(drawing_or_id, Drawing):
                self.add_drawing(drawing_or_id, emit_event=emit_event)
                return True
            return False

        d = self._drawings[drawing_id]
        old_points = [DrawingPoint(p.time, p.price, p.bar_index) for p in d.points]
        old_style = DrawingStyle.from_dict(d.style.to_dict())

        pts = new_points or old_points
        stl = new_style or old_style

        cmd = ModifyDrawingCommand(self, drawing_id, old_points, pts, old_style, stl, emit_event=emit_event)
        cmd.execute()
        self._undo_stack.append(cmd)
        self._redo_stack.clear()
        return True

    def undo(self) -> bool:
        """Undoes the latest drawing action."""
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        return True

    def redo(self) -> bool:
        """Redoes the latest undone drawing action."""
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
        return True

    def get_all_drawings(self) -> List[Drawing]:
        return list(self._drawings.values())

    def get_drawing(self, drawing_id: str) -> Optional[Drawing]:
        return self._drawings.get(drawing_id)

    def clear(self) -> None:
        self._drawings.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.selected_drawing_id = None

    def serialize(self) -> List[dict]:
        return [d.to_dict() for d in self._drawings.values()]

    def deserialize(self, data: List[dict]) -> None:
        self.clear()
        for item in data:
            try:
                d = Drawing.from_dict(item)
                self._drawings[d.id] = d
            except Exception as e:
                logger.error(f"Failed to deserialize drawing: {e}")
