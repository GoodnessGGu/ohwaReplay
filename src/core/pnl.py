from typing import Tuple
from src.utils.constants import Direction


def calculate_pnl(
    direction: Direction,
    entry_price: float,
    exit_price: float,
    lot_size: float,
    point_value: float = 100.0,
) -> float:
    """
    Calculates gross PnL for a trade.
    BUY: (exit - entry) * lot_size * point_value
    SELL: (entry - exit) * lot_size * point_value
    """
    if direction == Direction.BUY:
        diff = exit_price - entry_price
    else:
        diff = entry_price - exit_price

    return round(diff * lot_size * point_value, 2)


def calculate_pips(
    direction: Direction,
    entry_price: float,
    current_price: float,
    pip_size: float = 0.1,
) -> float:
    """Calculates difference in pips."""
    if pip_size <= 0:
        return 0.0
    if direction == Direction.BUY:
        return round((current_price - entry_price) / pip_size, 1)
    return round((entry_price - current_price) / pip_size, 1)
