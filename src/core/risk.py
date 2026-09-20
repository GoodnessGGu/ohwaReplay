from dataclasses import dataclass
from typing import Optional, Tuple
from src.utils.constants import Direction


@dataclass
class RiskCalculationResult:
    """Calculated position sizing and risk/reward metrics."""
    risk_amount: float
    suggested_lot_size: float
    stop_loss_distance: float
    take_profit_distance: float
    potential_loss: float
    potential_profit: float
    risk_reward_ratio: float
    is_valid: bool
    error_message: str = ""


class RiskCalculator:
    """Calculates trade risk, position sizing, and risk/reward profiles."""

    @staticmethod
    def calculate_lot_size(
        balance: float,
        risk_pct: float,
        entry_price: float,
        stop_loss_price: float,
        point_value: float = 100.0,
        min_lot: float = 0.01,
        max_lot: float = 100.0,
    ) -> float:
        """Calculates exact lot size to risk a given percentage of balance."""
        if balance <= 0 or risk_pct <= 0 or entry_price <= 0:
            return min_lot

        risk_amount = balance * (risk_pct / 100.0)
        sl_distance = abs(entry_price - stop_loss_price)

        if sl_distance <= 0:
            return min_lot

        # risk_amount = sl_distance * lot_size * point_value
        lot_size = risk_amount / (sl_distance * point_value)
        # Round to 2 decimals
        lot_size = round(max(min_lot, min(lot_size, max_lot)), 2)
        return lot_size

    @staticmethod
    def analyze_setup(
        balance: float,
        risk_pct: float,
        direction: Direction,
        entry_price: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
        lot_size: Optional[float] = None,
        point_value: float = 100.0,
    ) -> RiskCalculationResult:
        """Full risk analysis for hypothetical or actual trade setup."""
        if entry_price <= 0:
            return RiskCalculationResult(0, 0, 0, 0, 0, 0, 0, False, "Entry price must be > 0.")

        risk_amount = balance * (risk_pct / 100.0) if balance > 0 and risk_pct > 0 else 0.0

        # Validate SL direction
        sl_distance = 0.0
        if stop_loss is not None and stop_loss > 0:
            if direction == Direction.BUY and stop_loss >= entry_price:
                return RiskCalculationResult(
                    0, 0, 0, 0, 0, 0, 0, False, "For BUY, Stop Loss must be BELOW entry price."
                )
            if direction == Direction.SELL and stop_loss <= entry_price:
                return RiskCalculationResult(
                    0, 0, 0, 0, 0, 0, 0, False, "For SELL, Stop Loss must be ABOVE entry price."
                )
            sl_distance = abs(entry_price - stop_loss)

        # Validate TP direction
        tp_distance = 0.0
        if take_profit is not None and take_profit > 0:
            if direction == Direction.BUY and take_profit <= entry_price:
                return RiskCalculationResult(
                    0, 0, 0, 0, 0, 0, 0, False, "For BUY, Take Profit must be ABOVE entry price."
                )
            if direction == Direction.SELL and take_profit >= entry_price:
                return RiskCalculationResult(
                    0, 0, 0, 0, 0, 0, 0, False, "For SELL, Take Profit must be BELOW entry price."
                )
            tp_distance = abs(take_profit - entry_price)

        # Suggested lot size
        if lot_size is not None and lot_size > 0:
            actual_lot = lot_size
        elif sl_distance > 0:
            actual_lot = RiskCalculator.calculate_lot_size(
                balance, risk_pct, entry_price, stop_loss, point_value
            )
        else:
            actual_lot = 1.0

        potential_loss = round(sl_distance * actual_lot * point_value, 2)
        potential_profit = round(tp_distance * actual_lot * point_value, 2)

        rr_ratio = round(tp_distance / sl_distance, 2) if sl_distance > 0 and tp_distance > 0 else 0.0

        return RiskCalculationResult(
            risk_amount=risk_amount,
            suggested_lot_size=actual_lot,
            stop_loss_distance=round(sl_distance, 4),
            take_profit_distance=round(tp_distance, 4),
            potential_loss=potential_loss,
            potential_profit=potential_profit,
            risk_reward_ratio=rr_ratio,
            is_valid=True,
        )
