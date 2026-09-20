import pytest
from src.workspace.workspace_schema import WorkspaceSchema
from src.workspace.workspace_manager import WorkspaceManager


def test_workspace_save_and_load(tmp_path):
    mgr = WorkspaceManager()
    schema = WorkspaceSchema(
        symbol="EURUSD",
        timeframe="15m",
        replay_index=350,
        balance=12500.0,
        drawings=[{"id": "d1", "type": "TRENDLINE", "points": []}],
        alerts=[{"id": "a1", "target_price": 1.0900}],
    )

    file_path = tmp_path / "test_workspace.json"
    saved = mgr.save_workspace(schema, file_path)
    assert saved is True
    assert file_path.exists()

    loaded = mgr.load_workspace(file_path)
    assert loaded is not None
    assert loaded.symbol == "EURUSD"
    assert loaded.timeframe == "15m"
    assert loaded.replay_index == 350
    assert loaded.balance == 12500.0
    assert len(loaded.drawings) == 1
    assert len(loaded.alerts) == 1
