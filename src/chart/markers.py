from typing import Any, Dict, List, Optional
from src.core.position import Position
from src.utils.constants import CloseReason, Direction


class ChartMarkerBuilder:
    """Formats trade entries and exits into Lightweight Charts marker objects."""

    @staticmethod
    def build_entry_marker(position: Position) -> Dict[str, Any]:
        """Creates a buy or sell entry marker."""
        is_buy = position.direction == Direction.BUY
        return {
            "time": position.open_timestamp,
            "position": "belowBar" if is_buy else "aboveBar",
            "color": "#26a69a" if is_buy else "#ef5350",
            "shape": "arrowUp" if is_buy else "arrowDown",
            "text": f"{position.direction.value} {position.lot_size}L @ {position.entry_price:.2f}",
        }

    @staticmethod
    def build_exit_marker(position: Position) -> Optional[Dict[str, Any]]:
        """Creates an exit marker when a trade closes."""
        if not position.close_timestamp or position.close_price is None:
            return None

        is_profit = position.net_pnl >= 0
        shape = "circle"
        if position.close_reason == CloseReason.TAKE_PROFIT:
            shape = "arrowDown" if position.direction == Direction.BUY else "arrowUp"
        elif position.close_reason == CloseReason.STOP_LOSS:
            shape = "square"

        return {
            "time": position.close_timestamp,
            "position": "aboveBar" if position.direction == Direction.BUY else "belowBar",
            "color": "#26a69a" if is_profit else "#ef5350",
            "shape": shape,
            "text": f"EXIT ${position.net_pnl:+,.2f} ({position.close_reason.value if position.close_reason else 'CLOSE'})",
        }

    @classmethod
    def build_all_markers(cls, trades: List[Position]) -> List[Dict[str, Any]]:
        """Generates sorted list of all entry & exit markers."""
        markers = []
        for t in trades:
            if t.open_timestamp:
                markers.append(cls.build_entry_marker(t))
            if t.close_timestamp:
                exit_m = cls.build_exit_marker(t)
                if exit_m:
                    markers.append(exit_m)
        markers.sort(key=lambda x: x.get("time", 0))
        return markers
