import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.core.order import Order
from src.core.position import Position
from src.core.risk import RiskCalculator
from src.events.event_bus import EventBus, event_bus
from src.utils.constants import (
    CloseReason,
    Direction,
    EventType,
    IntrabarExecutionMode,
    OrderType,
    PositionStatus,
)
from src.utils.logger import logger


class AccountEngine:
    """
    Simulates a high-precision broker trading account.
    Tracks balance, equity, margin, active positions, and trade history.
    Evaluates SL/TP execution on every candle step with configurable intrabar models.
    """

    def __init__(
        self,
        initial_balance: float = 10000.0,
        currency: str = "USD",
        leverage: int = 100,
        commission_per_lot: float = 7.0,
        spread: float = 0.20,
        slippage: float = 0.05,
        intrabar_mode: IntrabarExecutionMode = IntrabarExecutionMode.CONSERVATIVE,
        event_bus_instance: Optional[EventBus] = None,
    ):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.currency = currency
        self.leverage = max(1, leverage)
        self.commission_per_lot = commission_per_lot
        self.spread = spread
        self.slippage = slippage
        self.intrabar_mode = intrabar_mode
        self.bus = event_bus_instance or event_bus

        self.positions: Dict[str, Position] = {}  # Active open positions
        self.pending_orders: Dict[str, Order] = {}  # Active pending limit/stop orders
        self.trade_history: List[Position] = []   # Closed trades

        self.symbol_point_values: Dict[str, float] = {
            "XAUUSD": 100.0,
            "EURUSD": 100000.0,
            "GBPUSD": 100000.0,
            "USDJPY": 1000.0,
            "BTCUSD": 1.0,
        }

    @property
    def unrealized_pnl(self) -> float:
        """Sum of unrealized PnL across all open positions."""
        return round(sum(p.unrealized_pnl for p in self.positions.values()), 2)

    @property
    def realized_pnl(self) -> float:
        """Sum of realized PnL across all closed trades."""
        return round(sum(p.realized_pnl - p.commission for p in self.trade_history), 2)

    @property
    def equity(self) -> float:
        """Account equity = balance + unrealized PnL."""
        return round(self.balance + self.unrealized_pnl, 2)

    @property
    def used_margin(self) -> float:
        """Sum of margin required by open positions."""
        total_margin = 0.0
        for p in self.positions.values():
            notional = p.entry_price * p.lot_size * p.point_value
            total_margin += notional / self.leverage
        return round(total_margin, 2)

    @property
    def free_margin(self) -> float:
        """Free margin = equity - used margin."""
        return round(self.equity - self.used_margin, 2)

    @property
    def margin_level(self) -> float:
        """Margin level percentage."""
        if self.used_margin <= 0:
            return 0.0
        return round((self.equity / self.used_margin) * 100.0, 2)

    def get_point_value(self, symbol: str) -> float:
        return self.symbol_point_values.get(symbol.upper(), 100.0)

    def open_market_order(
        self,
        direction: Direction,
        symbol: str,
        lot_size: float,
        current_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        timestamp: Optional[int] = None,
        dt: Optional[datetime] = None,
        strategy: str = "",
        notes: str = "",
        tags: str = "",
    ) -> Tuple[bool, Optional[Position], str]:
        """
        Executes a market order with spread, commission, slippage and margin validation.
        """
        if lot_size <= 0:
            return False, None, "Lot size must be greater than 0."
        if current_price <= 0:
            return False, None, "Invalid current market price."

        point_val = self.get_point_value(symbol)

        # Validate SL/TP orientation
        if stop_loss is not None and stop_loss > 0:
            if direction == Direction.BUY and stop_loss >= current_price:
                return False, None, "For BUY order, Stop Loss must be below current price."
            if direction == Direction.SELL and stop_loss <= current_price:
                return False, None, "For SELL order, Stop Loss must be above current price."

        if take_profit is not None and take_profit > 0:
            if direction == Direction.BUY and take_profit <= current_price:
                return False, None, "For BUY order, Take Profit must be above current price."
            if direction == Direction.SELL and take_profit >= current_price:
                return False, None, "For SELL order, Take Profit must be below current price."

        # Compute execution fill price with spread and slippage
        # BUY fills at Ask = price + spread/2 + slippage
        # SELL fills at Bid = price - spread/2 - slippage
        half_spread = self.spread / 2.0
        if direction == Direction.BUY:
            fill_price = current_price + half_spread + self.slippage
        else:
            fill_price = current_price - half_spread - self.slippage

        # Check margin
        required_margin = (fill_price * lot_size * point_val) / self.leverage
        if required_margin > self.free_margin:
            return False, None, f"Insufficient margin: Required ${required_margin:,.2f}, Free ${self.free_margin:,.2f}"

        # Commission
        commission = round(self.commission_per_lot * lot_size, 2)
        # Deduct commission immediately from balance
        self.balance -= commission

        position = Position(
            symbol=symbol,
            direction=direction,
            entry_price=round(fill_price, 5),
            current_price=round(current_price, 5),
            lot_size=lot_size,
            point_value=point_val,
            stop_loss=stop_loss,
            take_profit=take_profit,
            open_time=dt or datetime.utcnow(),
            open_timestamp=timestamp,
            commission=commission,
            status=PositionStatus.OPEN,
            strategy=strategy,
            notes=notes,
            tags=tags,
        )
        position.calculate_unrealized_pnl(current_price)

        self.positions[position.id] = position
        logger.info(f"Opened {direction.value} position {position.id} @ {fill_price} (Lot: {lot_size})")

        self.bus.emit(EventType.ORDER_OPENED, position.to_dict())
        self.bus.emit(EventType.ACCOUNT_UPDATED, self.get_account_summary())

        return True, position, "Order executed successfully."

    def place_pending_order(
        self,
        order_type: OrderType,
        symbol: str,
        lot_size: float,
        target_price: float,
        current_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        timestamp: Optional[int] = None,
        dt: Optional[datetime] = None,
        strategy: str = "",
        notes: str = "",
        tags: str = "",
    ) -> Tuple[bool, Optional[Order], str]:
        """
        Places a pending limit or stop order (BUY_LIMIT, BUY_STOP, SELL_LIMIT, SELL_STOP).
        """
        if lot_size <= 0:
            return False, None, "Lot size must be greater than 0."
        if target_price <= 0:
            return False, None, "Target entry price must be greater than 0."

        # Validate order type vs current market price
        if order_type == OrderType.BUY_LIMIT and target_price >= current_price:
            return False, None, "For BUY LIMIT, entry price must be below current market price."
        if order_type == OrderType.BUY_STOP and target_price <= current_price:
            return False, None, "For BUY STOP, entry price must be above current market price."
        if order_type == OrderType.SELL_LIMIT and target_price <= current_price:
            return False, None, "For SELL LIMIT, entry price must be above current market price."
        if order_type == OrderType.SELL_STOP and target_price >= current_price:
            return False, None, "For SELL STOP, entry price must be below current market price."

        # Validate SL / TP relative to target price
        is_buy = order_type in (OrderType.BUY_LIMIT, OrderType.BUY_STOP)
        if stop_loss is not None and stop_loss > 0:
            if is_buy and stop_loss >= target_price:
                return False, None, "For BUY order, Stop Loss must be below target entry price."
            if not is_buy and stop_loss <= target_price:
                return False, None, "For SELL order, Stop Loss must be above target entry price."

        if take_profit is not None and take_profit > 0:
            if is_buy and take_profit <= target_price:
                return False, None, "For BUY order, Take Profit must be above target entry price."
            if not is_buy and take_profit >= target_price:
                return False, None, "For SELL order, Take Profit must be below target entry price."

        order = Order(
            symbol=symbol,
            order_type=order_type,
            lot_size=lot_size,
            price=round(target_price, 5),
            stop_loss=round(stop_loss, 5) if stop_loss else None,
            take_profit=round(take_profit, 5) if take_profit else None,
            timestamp=timestamp,
            datetime=dt or datetime.utcnow(),
            strategy=strategy,
            notes=notes,
            tags=tags,
        )

        self.pending_orders[order.id] = order
        logger.info(f"Placed pending {order_type.value} order {order.id} @ {target_price} (Lot: {lot_size})")

        self.bus.emit(EventType.PENDING_ORDER_CREATED, order.to_dict())
        self.bus.emit(EventType.ACCOUNT_UPDATED, self.get_account_summary())
        return True, order, f"Pending {order_type.value} placed successfully."

    def cancel_pending_order(self, order_id: str) -> bool:
        """Cancels an active pending order."""
        if order_id not in self.pending_orders:
            return False
        order = self.pending_orders.pop(order_id)
        logger.info(f"Cancelled pending order {order.id}")
        self.bus.emit(EventType.PENDING_ORDER_CANCELLED, order.to_dict())
        self.bus.emit(EventType.ACCOUNT_UPDATED, self.get_account_summary())
        return True

    def close_position(
        self,
        position_id: str,
        current_price: float,
        timestamp: Optional[int] = None,
        dt: Optional[datetime] = None,
        reason: CloseReason = CloseReason.MANUAL,
    ) -> Tuple[bool, Optional[Position], str]:
        """Closes an active position and updates account balance."""
        if position_id not in self.positions:
            return False, None, f"Position '{position_id}' not found."

        pos = self.positions.pop(position_id)

        # Apply spread and slippage on exit
        half_spread = self.spread / 2.0
        if pos.direction == Direction.BUY:
            exit_price = current_price - half_spread - self.slippage
        else:
            exit_price = current_price + half_spread + self.slippage

        realized = pos.close(
            close_price=round(exit_price, 5),
            close_time=dt or datetime.utcnow(),
            close_timestamp=timestamp,
            reason=reason,
        )

        self.balance += realized
        self.trade_history.append(pos)

        logger.info(
            f"Closed position {pos.id} @ {exit_price} (Reason: {reason.value}, Gross PnL: ${realized:,.2f}, Net: ${pos.net_pnl:,.2f})"
        )

        self.bus.emit(EventType.ORDER_CLOSED, pos.to_dict())
        self.bus.emit(EventType.ACCOUNT_UPDATED, self.get_account_summary())

        return True, pos, "Position closed."

    def close_partial_position(
        self,
        position_id: str,
        percentage: float = 0.5,
        current_price: Optional[float] = None,
        timestamp: Optional[int] = None,
        dt: Optional[datetime] = None,
        reason: CloseReason = CloseReason.MANUAL,
    ) -> Tuple[bool, Optional[Position], str]:
        """
        Closes a partial portion of an active position (e.g. 50%).
        Creates a closed Position record for trade history, and updates remaining position volume and account balance.
        """
        if position_id not in self.positions:
            return False, None, f"Position '{position_id}' not found."

        if percentage <= 0.0 or percentage > 1.0:
            return False, None, "Partial percentage must be between 0 and 1.0 (e.g. 0.5 for 50%)."

        pos = self.positions[position_id]
        if percentage >= 0.9999 or pos.lot_size <= 0.01:
            # Full close if 100% or minimum lot size
            return self.close_position(
                position_id=position_id,
                current_price=current_price if current_price is not None else pos.current_price,
                timestamp=timestamp,
                dt=dt,
                reason=reason,
            )

        close_lots = round(pos.lot_size * percentage, 2)
        remaining_lots = round(pos.lot_size - close_lots, 2)
        if close_lots <= 0 or remaining_lots <= 0:
            return self.close_position(
                position_id=position_id,
                current_price=current_price if current_price is not None else pos.current_price,
                timestamp=timestamp,
                dt=dt,
                reason=reason,
            )

        exec_price = current_price if current_price is not None else pos.current_price
        half_spread = self.spread / 2.0
        if pos.direction == Direction.BUY:
            exit_price = exec_price - half_spread - self.slippage
        else:
            exit_price = exec_price + half_spread + self.slippage

        # Calculate proportional commission
        trade_commission = round(pos.commission * (close_lots / pos.lot_size), 2)
        pos.commission = round(pos.commission - trade_commission, 2)

        # Create closed Position record for the partial execution
        partial_record = Position(
            id=f"{pos.id}_p{int(percentage * 100)}",
            symbol=pos.symbol,
            direction=pos.direction,
            entry_price=pos.entry_price,
            current_price=round(exec_price, 5),
            lot_size=close_lots,
            point_value=pos.point_value,
            stop_loss=pos.stop_loss,
            take_profit=pos.take_profit,
            open_time=pos.open_time,
            open_timestamp=pos.open_timestamp,
            commission=trade_commission,
            strategy=pos.strategy,
            notes=f"Partial close {int(percentage * 100)}% | {pos.notes}".strip(),
            tags=pos.tags,
        )

        realized = partial_record.close(
            close_price=round(exit_price, 5),
            close_time=dt or datetime.utcnow(),
            close_timestamp=timestamp,
            reason=reason,
        )

        self.balance += realized
        self.trade_history.append(partial_record)

        # Update remaining active position
        pos.lot_size = remaining_lots
        pos.calculate_unrealized_pnl(pos.current_price)

        logger.info(
            f"Partial close on {pos.id}: closed {close_lots} lots ({int(percentage * 100)}%) @ {exit_price}, remaining: {remaining_lots} lots, Realized PnL: ${realized:,.2f}"
        )

        self.bus.emit(EventType.ORDER_CLOSED, partial_record.to_dict())
        self.bus.emit(EventType.POSITION_UPDATED, pos.to_dict())
        self.bus.emit(EventType.ACCOUNT_UPDATED, self.get_account_summary())

        return True, partial_record, f"Partial position closed: {close_lots} lots ({int(percentage * 100)}%)."

    def move_sl_to_break_even(self, position_id: str, offset: float = 0.0) -> Tuple[bool, str]:
        """
        Moves the stop loss of an open position to its exact entry price (+/- optional offset/buffer).
        """
        if position_id not in self.positions:
            return False, f"Position '{position_id}' not found."

        pos = self.positions[position_id]
        if pos.direction == Direction.BUY:
            new_sl = round(pos.entry_price + offset, 5)
        else:
            new_sl = round(pos.entry_price - offset, 5)

        pos.stop_loss = new_sl
        logger.info(f"Moved SL to Break-Even on position {pos.id} @ {new_sl} (entry: {pos.entry_price})")

        self.bus.emit(EventType.POSITION_UPDATED, pos.to_dict())
        self.bus.emit(EventType.ACCOUNT_UPDATED, self.get_account_summary())
        return True, f"Stop loss moved to break-even ({new_sl:.2f})."

    def close_all_positions(
        self,
        current_price: float,
        timestamp: Optional[int] = None,
        dt: Optional[datetime] = None,
        reason: CloseReason = CloseReason.MANUAL,
    ) -> List[Position]:
        """Closes all currently open positions."""
        closed = []
        for pos_id in list(self.positions.keys()):
            success, pos, _ = self.close_position(pos_id, current_price, timestamp, dt, reason)
            if success and pos:
                closed.append(pos)
        return closed

    def modify_position(
        self,
        position_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """Updates SL / TP levels for an active position."""
        if position_id not in self.positions:
            return False, f"Position {position_id} not found."

        pos = self.positions[position_id]
        if stop_loss is not None:
            if pos.direction == Direction.BUY and stop_loss >= pos.current_price:
                return False, "For BUY, Stop Loss must be below current price."
            if pos.direction == Direction.SELL and stop_loss <= pos.current_price:
                return False, "For SELL, Stop Loss must be above current price."
            pos.stop_loss = stop_loss

        if take_profit is not None:
            if pos.direction == Direction.BUY and take_profit <= pos.current_price:
                return False, "For BUY, Take Profit must be above current price."
            if pos.direction == Direction.SELL and take_profit >= pos.current_price:
                return False, "For SELL, Take Profit must be below current price."
            pos.take_profit = take_profit

        self.bus.emit(EventType.POSITION_UPDATED, pos.to_dict())
        return True, "Position modified."

    def process_candle(
        self,
        candle: Dict[str, Any],
        sub_candles: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Position]:
        """
        Evaluates active positions against the new candle's High, Low, and Close.
        If sub_candles (e.g. 1m granular bars) are provided, walks sub-ticks in exact
        chronological sequence to resolve SL/TP hits with 100% intrabar realism.
        """
        high_p = float(candle.get("high", 0.0))
        low_p = float(candle.get("low", 0.0))
        close_p = float(candle.get("close", 0.0))
        open_p = float(candle.get("open", 0.0))
        ts = candle.get("timestamp")
        dt = candle.get("datetime")
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except Exception:
                dt = None

        # 1. Evaluate and trigger pending limit and stop orders
        for order_id, p_order in list(self.pending_orders.items()):
            triggered = False
            fill_price = p_order.price or close_p
            if p_order.order_type == OrderType.BUY_LIMIT:
                if low_p <= p_order.price:
                    triggered = True
            elif p_order.order_type == OrderType.BUY_STOP:
                if high_p >= p_order.price:
                    triggered = True
            elif p_order.order_type == OrderType.SELL_LIMIT:
                if high_p >= p_order.price:
                    triggered = True
            elif p_order.order_type == OrderType.SELL_STOP:
                if low_p <= p_order.price:
                    triggered = True

            if triggered:
                del self.pending_orders[order_id]
                logger.info(f"Triggered pending order {order_id} ({p_order.order_type.value}) @ {fill_price}")
                self.bus.emit(EventType.PENDING_ORDER_TRIGGERED, p_order.to_dict())
                self.open_market_order(
                    direction=p_order.direction,
                    symbol=p_order.symbol,
                    lot_size=p_order.lot_size,
                    current_price=fill_price,
                    stop_loss=p_order.stop_loss,
                    take_profit=p_order.take_profit,
                    timestamp=ts,
                    dt=dt,
                    strategy=p_order.strategy,
                    notes=p_order.notes,
                    tags=p_order.tags,
                )

        closed_this_candle: List[Position] = []

        for pos_id, pos in list(self.positions.items()):
            pos.calculate_unrealized_pnl(close_p)

            resolved_reason = None
            exit_price = None
            exit_time = dt or datetime.utcnow()
            exit_ts = ts

            # If sub-candles are available, walk through them chronologically
            if sub_candles and len(sub_candles) > 0:
                for sub in sub_candles:
                    s_high = float(sub.get("high", 0.0))
                    s_low = float(sub.get("low", 0.0))
                    s_ts = sub.get("timestamp", ts)
                    s_dt = sub.get("datetime", exit_time)

                    s_sl = False
                    s_tp = False

                    if pos.direction == Direction.BUY:
                        if pos.stop_loss is not None and s_low <= pos.stop_loss:
                            s_sl = True
                        if pos.take_profit is not None and s_high >= pos.take_profit:
                            s_tp = True
                    else:  # SELL
                        if pos.stop_loss is not None and s_high >= pos.stop_loss:
                            s_sl = True
                        if pos.take_profit is not None and s_low <= pos.take_profit:
                            s_tp = True

                    if s_sl and s_tp:
                        if self.intrabar_mode in (IntrabarExecutionMode.CONSERVATIVE, IntrabarExecutionMode.SL_FIRST):
                            resolved_reason = CloseReason.STOP_LOSS
                            exit_price = pos.stop_loss
                        else:
                            resolved_reason = CloseReason.TAKE_PROFIT
                            exit_price = pos.take_profit
                        exit_ts = s_ts
                        exit_time = s_dt
                        break
                    elif s_sl:
                        resolved_reason = CloseReason.STOP_LOSS
                        exit_price = pos.stop_loss
                        exit_ts = s_ts
                        exit_time = s_dt
                        break
                    elif s_tp:
                        resolved_reason = CloseReason.TAKE_PROFIT
                        exit_price = pos.take_profit
                        exit_ts = s_ts
                        exit_time = s_dt
                        break

            # Fallback to standard candle-level SL/TP check
            if resolved_reason is None:
                sl_hit = False
                tp_hit = False

                if pos.direction == Direction.BUY:
                    if pos.stop_loss is not None and low_p <= pos.stop_loss:
                        sl_hit = True
                    if pos.take_profit is not None and high_p >= pos.take_profit:
                        tp_hit = True
                elif pos.direction == Direction.SELL:
                    if pos.stop_loss is not None and high_p >= pos.stop_loss:
                        sl_hit = True
                    if pos.take_profit is not None and low_p <= pos.take_profit:
                        tp_hit = True

                if sl_hit and tp_hit:
                    if self.intrabar_mode in (IntrabarExecutionMode.CONSERVATIVE, IntrabarExecutionMode.SL_FIRST):
                        resolved_reason = CloseReason.STOP_LOSS
                        exit_price = pos.stop_loss
                    else:
                        resolved_reason = CloseReason.TAKE_PROFIT
                        exit_price = pos.take_profit
                elif sl_hit:
                    resolved_reason = CloseReason.STOP_LOSS
                    exit_price = pos.stop_loss
                elif tp_hit:
                    resolved_reason = CloseReason.TAKE_PROFIT
                    exit_price = pos.take_profit

            # Finalize closed position
            if resolved_reason is not None and exit_price is not None:
                del self.positions[pos_id]
                pos.close(
                    close_price=exit_price,
                    close_time=exit_time,
                    close_timestamp=exit_ts,
                    reason=resolved_reason,
                )
                self.balance += pos.realized_pnl
                self.trade_history.append(pos)
                closed_this_candle.append(pos)

                if resolved_reason == CloseReason.STOP_LOSS:
                    self.bus.emit(EventType.SL_HIT, pos.to_dict())
                else:
                    self.bus.emit(EventType.TP_HIT, pos.to_dict())

                self.bus.emit(EventType.ORDER_CLOSED, pos.to_dict())

        if self.positions:
            self.bus.emit(EventType.POSITION_UPDATED, [p.to_dict() for p in self.positions.values()])

        self.bus.emit(EventType.ACCOUNT_UPDATED, self.get_account_summary())
        return closed_this_candle

    def get_account_summary(self) -> Dict[str, Any]:
        """Returns snapshot of account balance, equity, margin, and positions."""
        return {
            "balance": round(self.balance, 2),
            "equity": self.equity,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "used_margin": self.used_margin,
            "free_margin": self.free_margin,
            "margin_level": self.margin_level,
            "open_positions_count": len(self.positions),
            "pending_orders_count": len(self.pending_orders),
            "total_trades_count": len(self.trade_history),
        }

    def reset(self, initial_balance: Optional[float] = None) -> None:
        """Resets account to starting state."""
        if initial_balance is not None:
            self.initial_balance = initial_balance
        self.balance = self.initial_balance
        self.positions.clear()
        self.pending_orders.clear()
        self.trade_history.clear()
        self.bus.emit(EventType.ACCOUNT_UPDATED, self.get_account_summary())

    def export_trade_history_csv(self, file_path: Union[str, Path]) -> bool:
        """Exports all completed trades to a CSV file."""
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
                for t in self.trade_history:
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
        except Exception as e:
            logger.error(f"Failed to export trade history to CSV: {e}")
            return False
