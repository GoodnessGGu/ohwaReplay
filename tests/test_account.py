import pytest
from src.core.account_engine import AccountEngine
from src.core.pnl import calculate_pnl, calculate_pips
from src.core.risk import RiskCalculator
from src.utils.constants import Direction, CloseReason, IntrabarExecutionMode, OrderType


def test_pnl_calculation():
    # BUY: 2000 -> 2010 with 1.0 lot, point_val=100
    pnl_buy = calculate_pnl(Direction.BUY, 2000.0, 2010.0, 1.0, 100.0)
    assert pnl_buy == 1000.0

    # SELL: 2000 -> 1990 with 2.0 lots, point_val=100
    pnl_sell = calculate_pnl(Direction.SELL, 2000.0, 1990.0, 2.0, 100.0)
    assert pnl_sell == 2000.0


def test_risk_calculator():
    # Balance $10,000, 1% risk ($100), entry 2000, SL 1990 (dist 10), point_val=100
    # Expected lot size = 100 / (10 * 100) = 0.10
    lot = RiskCalculator.calculate_lot_size(
        balance=10000.0,
        risk_pct=1.0,
        entry_price=2000.0,
        stop_loss_price=1990.0,
        point_value=100.0,
    )
    assert lot == 0.10

    analysis = RiskCalculator.analyze_setup(
        balance=10000.0,
        risk_pct=1.0,
        direction=Direction.BUY,
        entry_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
        lot_size=0.10,
        point_value=100.0,
    )
    assert analysis.is_valid is True
    assert analysis.risk_reward_ratio == 2.0
    assert analysis.potential_loss == 100.0
    assert analysis.potential_profit == 200.0


def test_account_buy_and_manual_close():
    account = AccountEngine(
        initial_balance=10000.0,
        commission_per_lot=7.0,
        spread=0.20,
        slippage=0.05,
    )

    # Market Buy 1.0 lot at 2000.0
    # Fill price = 2000 + 0.10 + 0.05 = 2000.15
    # Balance before close = 10000 - 7 (commission) = 9993.0
    success, pos, msg = account.open_market_order(
        direction=Direction.BUY,
        symbol="XAUUSD",
        lot_size=1.0,
        current_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
    )
    assert success is True
    assert pos is not None
    assert pos.entry_price == 2000.15
    assert account.balance == 9993.0
    assert len(account.positions) == 1

    # Price moves to 2010.0 and we close manually
    # Exit fill = 2010.0 - 0.10 - 0.05 = 2009.85
    # Gross PnL = (2009.85 - 2000.15) * 1.0 * 100 = 9.70 * 100 = 970.0
    # Final Balance = 9993 + 970 = 10963.0
    success, closed_pos, msg = account.close_position(
        position_id=pos.id,
        current_price=2010.0,
        reason=CloseReason.MANUAL,
    )
    assert success is True
    assert closed_pos.realized_pnl == 970.0
    assert account.balance == 10963.0
    assert len(account.positions) == 0
    assert len(account.trade_history) == 1


def test_account_sl_hit():
    account = AccountEngine(initial_balance=10000.0, spread=0.0, slippage=0.0, commission_per_lot=0.0)
    success, pos, _ = account.open_market_order(
        direction=Direction.BUY,
        symbol="XAUUSD",
        lot_size=1.0,
        current_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
    )
    assert success is True

    # Candle dips to 1988 (below SL 1990)
    candle = {
        "open": 2000.0,
        "high": 2005.0,
        "low": 1988.0,
        "close": 1992.0,
        "timestamp": 1700000000,
    }
    closed = account.process_candle(candle)
    assert len(closed) == 1
    assert closed[0].close_reason == CloseReason.STOP_LOSS
    assert closed[0].close_price == 1990.0
    # Loss = (1990 - 2000) * 100 = -1000
    assert account.balance == 9000.0


def test_account_tp_hit():
    account = AccountEngine(initial_balance=10000.0, spread=0.0, slippage=0.0, commission_per_lot=0.0)
    account.open_market_order(
        direction=Direction.SELL,
        symbol="XAUUSD",
        lot_size=1.0,
        current_price=2000.0,
        stop_loss=2010.0,
        take_profit=1980.0,
    )
    # Candle drops to 1975 (below TP 1980 for SELL)
    candle = {
        "open": 1995.0,
        "high": 1998.0,
        "low": 1975.0,
        "close": 1978.0,
        "timestamp": 1700000060,
    }
    closed = account.process_candle(candle)
    assert len(closed) == 1
    assert closed[0].close_reason == CloseReason.TAKE_PROFIT
    assert closed[0].close_price == 1980.0
    # SELL profit: (2000 - 1980) * 100 = +2000
    assert account.balance == 12000.0


def test_intrabar_ambiguity_conservative():
    # If candle touches both SL and TP in conservative mode, SL is prioritized
    account = AccountEngine(
        initial_balance=10000.0,
        spread=0.0,
        slippage=0.0,
        commission_per_lot=0.0,
        intrabar_mode=IntrabarExecutionMode.CONSERVATIVE,
    )
    account.open_market_order(
        direction=Direction.BUY,
        symbol="XAUUSD",
        lot_size=1.0,
        current_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
    )
    # Wild spike candle: Low 1985 (SL hit) and High 2025 (TP hit)
    wild_candle = {
        "open": 2000.0,
        "high": 2025.0,
        "low": 1985.0,
        "close": 2015.0,
        "timestamp": 1700000120,
    }
    closed = account.process_candle(wild_candle)
    assert len(closed) == 1
    assert closed[0].close_reason == CloseReason.STOP_LOSS
    assert account.balance == 9000.0


def test_sub_candle_intrabar_chronological_resolution():
    # When 1m sub-candles are provided, TP that hit at minute 5 takes precedence even if SL was hit at minute 30
    account = AccountEngine(
        initial_balance=10000.0,
        spread=0.0,
        slippage=0.0,
        commission_per_lot=0.0,
        intrabar_mode=IntrabarExecutionMode.CONSERVATIVE,
    )
    account.open_market_order(
        direction=Direction.BUY,
        symbol="XAUUSD",
        lot_size=1.0,
        current_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
    )

    # 1h candle has low 1980 and high 2030
    hourly_candle = {
        "open": 2000.0,
        "high": 2030.0,
        "low": 1980.0,
        "close": 2005.0,
        "timestamp": 1700000000,
    }

    # Sub-candles: Minute 5 hits TP (2025), Minute 30 hits SL (1985)
    sub_1m = [
        {"timestamp": 1700000300, "open": 2010.0, "high": 2025.0, "low": 2008.0, "close": 2022.0},  # Min 5 -> TP!
        {"timestamp": 1700001800, "open": 2000.0, "high": 2002.0, "low": 1985.0, "close": 1995.0},  # Min 30 -> SL
    ]

    closed = account.process_candle(hourly_candle, sub_candles=sub_1m)
    assert len(closed) == 1
    assert closed[0].close_reason == CloseReason.TAKE_PROFIT
    assert closed[0].close_price == 2020.0
    assert account.balance == 12000.0


def test_export_trade_history_csv(tmp_path):
    account = AccountEngine(initial_balance=10000.0, spread=0.0, slippage=0.0, commission_per_lot=0.0)
    account.open_market_order(Direction.BUY, "XAUUSD", 1.0, 2000.0)
    pos_id = list(account.positions.keys())[0]
    account.close_position(pos_id, 2010.0)

    csv_path = tmp_path / "history.csv"
    success = account.export_trade_history_csv(csv_path)
    assert success is True
    assert csv_path.exists()
    content = csv_path.read_text(encoding="utf-8")
    assert "XAUUSD" in content
    assert "1000.0" in content


def test_pending_orders_limit_and_stop():
    account = AccountEngine(initial_balance=10000.0, spread=0.0, slippage=0.0, commission_per_lot=0.0)

    # 1. Place BUY LIMIT @ 1990 (when current price is 2000)
    success, ord1, _ = account.place_pending_order(
        order_type=OrderType.BUY_LIMIT,
        symbol="XAUUSD",
        lot_size=1.0,
        target_price=1990.0,
        current_price=2000.0,
        stop_loss=1980.0,
        take_profit=2010.0,
    )
    assert success is True
    assert ord1.id in account.pending_orders
    assert len(account.pending_orders) == 1

    # Candle that doesn't reach 1990 (Low 1995)
    c1 = {"open": 2000.0, "high": 2005.0, "low": 1995.0, "close": 1998.0, "timestamp": 1700000000}
    account.process_candle(c1)
    assert len(account.pending_orders) == 1
    assert len(account.positions) == 0

    # Candle that reaches 1990 (Low 1988) -> Triggers BUY LIMIT
    c2 = {"open": 1998.0, "high": 2002.0, "low": 1988.0, "close": 1995.0, "timestamp": 1700000060}
    account.process_candle(c2)
    assert len(account.pending_orders) == 0
    assert len(account.positions) == 1
    pos = list(account.positions.values())[0]
    assert pos.direction == Direction.BUY
    assert pos.entry_price == 1990.0
    assert pos.stop_loss == 1980.0
    assert pos.take_profit == 2010.0

    # 2. Place SELL STOP @ 1980 (when current price is 1995)
    success, ord2, _ = account.place_pending_order(
        order_type=OrderType.SELL_STOP,
        symbol="XAUUSD",
        lot_size=1.0,
        target_price=1980.0,
        current_price=1995.0,
        stop_loss=1990.0,
        take_profit=1960.0,
    )
    assert success is True
    assert len(account.pending_orders) == 1

    # Cancel pending order
    assert account.cancel_pending_order(ord2.id) is True
    assert len(account.pending_orders) == 0


def test_close_partial_position():
    account = AccountEngine(initial_balance=10000.0, spread=0.0, slippage=0.0, commission_per_lot=0.0)
    success, pos, _ = account.open_market_order(
        direction=Direction.BUY,
        symbol="XAUUSD",
        lot_size=1.0,
        current_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
    )
    assert success is True
    assert pos.lot_size == 1.0

    # Partial close 50% @ 2010.0
    success, part_pos, msg = account.close_partial_position(
        position_id=pos.id,
        percentage=0.5,
        current_price=2010.0,
    )
    assert success is True
    assert part_pos is not None
    assert part_pos.lot_size == 0.50
    # Profit for 0.50 lots: (2010 - 2000) * 0.50 * 100 = 500.0
    assert part_pos.realized_pnl == 500.0
    assert account.balance == 10500.0
    assert len(account.trade_history) == 1

    # Remaining position check
    assert pos.id in account.positions
    assert account.positions[pos.id].lot_size == 0.50


def test_move_sl_to_break_even():
    account = AccountEngine(initial_balance=10000.0, spread=0.0, slippage=0.0, commission_per_lot=0.0)
    success, pos, _ = account.open_market_order(
        direction=Direction.BUY,
        symbol="XAUUSD",
        lot_size=1.0,
        current_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
    )
    assert success is True
    assert pos.stop_loss == 1990.0

    success, msg = account.move_sl_to_break_even(pos.id)
    assert success is True
    assert pos.stop_loss == 2000.0
