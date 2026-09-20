import csv
from pathlib import Path
from typing import List, Union
from src.core.position import Position


class TradeExporter:
    """Exports trades and performance reports to CSV and JSON formats."""

    @staticmethod
    def export_csv(trades: List[Position], file_path: Union[str, Path]) -> bool:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Trade ID", "Symbol", "Direction", "Volume", "Entry Price", "Exit Price",
                    "Stop Loss", "Take Profit", "Open Time", "Close Time", "Gross PnL",
                    "Commission", "Net PnL", "Close Reason", "Strategy", "Notes"
                ])
                for t in trades:
                    writer.writerow([
                        t.id, t.symbol, t.direction.value, t.lot_size, t.entry_price, t.close_price,
                        t.stop_loss or "", t.take_profit or "",
                        t.open_time.isoformat() if t.open_time else "",
                        t.close_time.isoformat() if t.close_time else "",
                        t.gross_pnl, t.commission, t.net_pnl,
                        t.close_reason.value if t.close_reason else "",
                        t.strategy, t.notes
                    ])
            return True
        except Exception:
            return False
