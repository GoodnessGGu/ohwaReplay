from typing import Any, Dict, List
from src.core.position import Position
from src.utils.constants import Direction


class TradeOverlayBuilder:
    """Builds horizontal price levels and overlay lines for active positions."""

    @staticmethod
    def build_overlays(positions: List[Position]) -> Dict[str, Any]:
        lines: List[Dict[str, Any]] = []

        for p in positions:
            # Entry line
            lines.append({
                "price": p.entry_price,
                "color": "#26a69a" if p.direction == Direction.BUY else "#ef5350",
                "width": 1,
                "style": "solid",
                "label": f"{p.direction.value} {p.lot_size}L",
            })

            # Stop Loss line
            if p.stop_loss is not None and p.stop_loss > 0:
                lines.append({
                    "price": p.stop_loss,
                    "color": "#ef5350",
                    "width": 1,
                    "style": "dashed",
                    "label": "SL",
                })

            # Take Profit line
            if p.take_profit is not None and p.take_profit > 0:
                lines.append({
                    "price": p.take_profit,
                    "color": "#26a69a",
                    "width": 1,
                    "style": "dashed",
                    "label": "TP",
                })

        return {"lines": lines}
