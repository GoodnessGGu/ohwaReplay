import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.events.event_bus import EventBus, event_bus
from src.utils.constants import EventType
from src.utils.logger import logger
from src.workspace.workspace_schema import WorkspaceSchema


class WorkspaceManager:
    """Manages saving, loading, and serializing application workspaces safely."""

    CURRENT_VERSION = 1

    def __init__(self, event_bus_instance: Optional[EventBus] = None):
        self.bus = event_bus_instance or event_bus
        self.current_workspace_path: Optional[Path] = None

    def save_workspace(self, workspace_data: WorkspaceSchema, file_path: Union[str, Path]) -> bool:
        """Saves workspace state to a JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(workspace_data.to_dict(), f, indent=2)
            self.current_workspace_path = path
            logger.info(f"Workspace successfully saved to {path}")
            self.bus.emit(EventType.WORKSPACE_SAVED, {"path": str(path)})
            return True
        except Exception as e:
            logger.error(f"Failed to save workspace to {path}: {e}")
            return False

    def load_workspace(self, file_path: Union[str, Path]) -> Optional[WorkspaceSchema]:
        """Loads and validates a workspace file."""
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Workspace file does not exist: {path}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.error(f"Invalid workspace format in {path}: Root must be a JSON object.")
                return None

            schema = WorkspaceSchema.from_dict(data)
            self.current_workspace_path = path
            logger.info(f"Workspace loaded from {path} (version {schema.version})")
            self.bus.emit(EventType.WORKSPACE_LOADED, schema.to_dict())
            return schema
        except Exception as e:
            logger.error(f"Failed to parse workspace JSON from {path}: {e}")
            return None
