from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkspaceSchema:
    """Versioned schema representing complete saved workstation state."""
    version: int = 1
    symbol: str = "XAUUSD"
    timeframe: str = "5m"
    replay_index: int = 0
    balance: float = 10000.0
    account_settings: Dict[str, Any] = field(default_factory=dict)
    chart_settings: Dict[str, Any] = field(default_factory=dict)
    drawings: List[Dict[str, Any]] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    indicators: List[Dict[str, Any]] = field(default_factory=list)
    journal_entries: List[Dict[str, Any]] = field(default_factory=list)
    layout: str = "single"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "replay_index": self.replay_index,
            "balance": self.balance,
            "account_settings": self.account_settings,
            "chart_settings": self.chart_settings,
            "drawings": self.drawings,
            "alerts": self.alerts,
            "indicators": self.indicators,
            "journal_entries": self.journal_entries,
            "layout": self.layout,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WorkspaceSchema":
        return cls(
            version=int(d.get("version", 1)),
            symbol=d.get("symbol", "XAUUSD"),
            timeframe=d.get("timeframe", "5m"),
            replay_index=int(d.get("replay_index", 0)),
            balance=float(d.get("balance", 10000.0)),
            account_settings=d.get("account_settings", {}),
            chart_settings=d.get("chart_settings", {}),
            drawings=d.get("drawings", []),
            alerts=d.get("alerts", []),
            indicators=d.get("indicators", []),
            journal_entries=d.get("journal_entries", []),
            layout=d.get("layout", "single"),
        )
