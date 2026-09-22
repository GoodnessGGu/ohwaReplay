from typing import Optional
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.risk import RiskCalculator
from src.utils.constants import Direction, OrderType


class SetBalanceDialog(QDialog):
    """Quick dialog to configure or reset starting account capital."""

    def __init__(self, current_balance: float = 10000.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙ Set Starting Capital / Balance")
        self.setMinimumWidth(320)
        self.init_ui(current_balance)

    def init_ui(self, current_balance: float) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel("Configure starting balance for retest & replay:")
        lbl.setStyleSheet("color: #848e9c; font-size: 12px;")
        layout.addWidget(lbl)

        form = QFormLayout()
        self.spin_bal = QDoubleSpinBox()
        self.spin_bal.setRange(100.0, 10000000.0)
        self.spin_bal.setValue(current_balance)
        self.spin_bal.setPrefix("$ ")
        self.spin_bal.setSingleStep(1000.0)
        self.spin_bal.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        form.addRow("Starting Balance:", self.spin_bal)

        self.combo_preset = QComboBox()
        self.combo_preset.addItems(["Choose Preset...", "$1,000", "$5,000", "$10,000", "$25,000", "$50,000", "$100,000", "$200,000"])
        self.combo_preset.currentIndexChanged.connect(self._on_preset)
        form.addRow("Quick Presets:", self.combo_preset)
        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_apply = QPushButton("Apply & Reset Balance")
        btn_apply.setStyleSheet("background-color: #2962ff; color: #ffffff; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        btn_apply.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_apply)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def _on_preset(self, idx: int) -> None:
        presets = {
            1: 1000.0,
            2: 5000.0,
            3: 10000.0,
            4: 25000.0,
            5: 50000.0,
            6: 100000.0,
            7: 200000.0,
        }
        if idx in presets:
            self.spin_bal.setValue(presets[idx])

    def get_balance(self) -> float:
        return self.spin_bal.value()


class ExecutionPanel(QFrame):
    """Trading execution and risk management panel supporting Market and Pending orders."""

    buy_clicked = pyqtSignal(float, float, float)     # lot_size, sl, tp
    sell_clicked = pyqtSignal(float, float, float)    # lot_size, sl, tp
    pending_order_clicked = pyqtSignal(str, float, float, float, float)  # order_type, lot, entry, sl, tp
    close_all_clicked = pyqtSignal()
    reset_capital_requested = pyqtSignal(float)       # new_starting_balance

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            ExecutionPanel {
                background-color: #1e222d;
                border-left: 1px solid #2a2e39;
                padding: 10px;
                min-width: 260px;
                max-width: 320px;
            }
        """)

        self.current_symbol = "XAUUSD"
        self.current_price = 2000.0
        self.spread = 0.20
        self.account_balance = 10000.0
        self.account_equity = 10000.0
        self.point_value = 100.0

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 1. Account & Starting Capital Section
        grp_account = QGroupBox("ACCOUNT & CAPITAL")
        acc_layout = QVBoxLayout(grp_account)
        acc_layout.setContentsMargins(6, 6, 6, 6)
        acc_layout.setSpacing(4)

        acc_grid = QGridLayout()
        acc_grid.addWidget(QLabel("Balance:"), 0, 0)
        self.lbl_balance_val = QLabel("$10,000.00")
        self.lbl_balance_val.setStyleSheet("font-weight: 700; color: #26a69a;")
        acc_grid.addWidget(self.lbl_balance_val, 0, 1)

        acc_grid.addWidget(QLabel("Equity:"), 1, 0)
        self.lbl_equity_val = QLabel("$10,000.00")
        self.lbl_equity_val.setStyleSheet("font-weight: 700; color: #ffffff;")
        acc_grid.addWidget(self.lbl_equity_val, 1, 1)
        acc_layout.addLayout(acc_grid)

        self.btn_set_capital = QPushButton("⚙ Set / Reset Capital...")
        self.btn_set_capital.setStyleSheet(
            "background-color: #2a2e39; color: #d1d4dc; font-size: 11px; font-weight: 600; padding: 4px; border-radius: 3px;"
        )
        self.btn_set_capital.clicked.connect(self._open_set_capital_dialog)
        acc_layout.addWidget(self.btn_set_capital)

        layout.addWidget(grp_account)

        # 2. Header / Live Prices
        self.lbl_sym_header = QLabel("XAUUSD")
        self.lbl_sym_header.setStyleSheet("font-size: 15px; font-weight: 800; color: #ffffff;")
        self.lbl_sym_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_sym_header)

        price_box = QHBoxLayout()
        self.lbl_bid = QLabel("BID: 1999.90")
        self.lbl_bid.setStyleSheet("color: #ef5350; font-weight: 700; font-size: 13px;")
        self.lbl_ask = QLabel("ASK: 2000.10")
        self.lbl_ask.setStyleSheet("color: #26a69a; font-weight: 700; font-size: 13px;")
        price_box.addWidget(self.lbl_bid)
        price_box.addStretch()
        price_box.addWidget(self.lbl_ask)
        layout.addLayout(price_box)

        # Order Type Group
        grp_type = QGroupBox("ORDER TYPE")
        type_layout = QVBoxLayout(grp_type)
        self.combo_order_type = QComboBox()
        self.combo_order_type.addItems([
            "Market Order",
            "Buy Limit",
            "Buy Stop",
            "Sell Limit",
            "Sell Stop"
        ])
        self.combo_order_type.setStyleSheet("font-weight: bold; padding: 4px;")
        self.combo_order_type.currentTextChanged.connect(self._on_order_type_changed)
        type_layout.addWidget(self.combo_order_type)

        # Entry Price (for pending orders)
        self.entry_container = QWidget()
        entry_lay = QHBoxLayout(self.entry_container)
        entry_lay.setContentsMargins(0, 2, 0, 0)
        lbl_ep = QLabel("Entry Price:")
        lbl_ep.setStyleSheet("color: #848e9c; font-size: 12px; font-weight: 600;")
        self.spin_entry = QDoubleSpinBox()
        self.spin_entry.setRange(0.01, 1000000.0)
        self.spin_entry.setDecimals(2)
        self.spin_entry.setValue(2000.0)
        self.spin_entry.valueChanged.connect(self._recalc_risk)
        entry_lay.addWidget(lbl_ep)
        entry_lay.addWidget(self.spin_entry)
        self.entry_container.setVisible(False)
        type_layout.addWidget(self.entry_container)

        layout.addWidget(grp_type)

        # Lot size group
        grp_lot = QGroupBox("POSITION SIZE (LOTS)")
        lot_layout = QHBoxLayout(grp_lot)
        btn_minus = QPushButton("-0.1")
        btn_minus.clicked.connect(lambda: self._adjust_lot(-0.1))
        btn_plus = QPushButton("+0.1")
        btn_plus.clicked.connect(lambda: self._adjust_lot(0.1))

        self.spin_lot = QDoubleSpinBox()
        self.spin_lot.setRange(0.01, 100.0)
        self.spin_lot.setSingleStep(0.01)
        self.spin_lot.setValue(1.0)
        self.spin_lot.valueChanged.connect(self._recalc_risk)

        lot_layout.addWidget(btn_minus)
        lot_layout.addWidget(self.spin_lot, 1)
        lot_layout.addWidget(btn_plus)
        layout.addWidget(grp_lot)

        # SL / TP levels
        grp_orders = QGroupBox("PROTECTIVE ORDERS")
        ord_layout = QGridLayout(grp_orders)

        ord_layout.addWidget(QLabel("Stop Loss:"), 0, 0)
        self.spin_sl = QDoubleSpinBox()
        self.spin_sl.setRange(0.0, 1000000.0)
        self.spin_sl.setDecimals(2)
        self.spin_sl.setValue(0.0)
        self.spin_sl.valueChanged.connect(self._recalc_risk)
        ord_layout.addWidget(self.spin_sl, 0, 1)

        ord_layout.addWidget(QLabel("Take Profit:"), 1, 0)
        self.spin_tp = QDoubleSpinBox()
        self.spin_tp.setRange(0.0, 1000000.0)
        self.spin_tp.setDecimals(2)
        self.spin_tp.setValue(0.0)
        self.spin_tp.valueChanged.connect(self._recalc_risk)
        ord_layout.addWidget(self.spin_tp, 1, 1)
        layout.addWidget(grp_orders)

        # Risk Management Calculator
        grp_risk = QGroupBox("RISK CALCULATOR")
        risk_layout = QGridLayout(grp_risk)

        risk_layout.addWidget(QLabel("Risk %:"), 0, 0)
        self.spin_risk_pct = QDoubleSpinBox()
        self.spin_risk_pct.setRange(0.1, 100.0)
        self.spin_risk_pct.setValue(1.0)
        self.spin_risk_pct.setSuffix(" %")
        risk_layout.addWidget(self.spin_risk_pct, 0, 1)

        btn_auto_size = QPushButton("Calculate Lot from SL")
        btn_auto_size.clicked.connect(self._auto_size_lot)
        risk_layout.addWidget(btn_auto_size, 1, 0, 1, 2)

        self.lbl_risk_info = QLabel("Est. Risk: $0.00 | R:R: 0.0")
        self.lbl_risk_info.setStyleSheet("color: #848e9c; font-size: 11px;")
        risk_layout.addWidget(self.lbl_risk_info, 2, 0, 1, 2)
        layout.addWidget(grp_risk)

        # Execution Buttons Container
        self.market_buttons_widget = QWidget()
        btn_box = QHBoxLayout(self.market_buttons_widget)
        btn_box.setContentsMargins(0, 0, 0, 0)
        self.btn_buy = QPushButton("BUY\nMarket")
        self.btn_buy.setObjectName("buyButton")
        self.btn_buy.clicked.connect(self._on_buy)

        self.btn_sell = QPushButton("SELL\nMarket")
        self.btn_sell.setObjectName("sellButton")
        self.btn_sell.clicked.connect(self._on_sell)

        btn_box.addWidget(self.btn_buy)
        btn_box.addWidget(self.btn_sell)
        layout.addWidget(self.market_buttons_widget)

        # Pending Order Place Button
        self.btn_place_pending = QPushButton("Place Pending Order")
        self.btn_place_pending.setStyleSheet("background-color: #2962ff; color: #ffffff; font-weight: bold; padding: 8px; font-size: 13px; border-radius: 4px;")
        self.btn_place_pending.clicked.connect(self._on_place_pending)
        self.btn_place_pending.setVisible(False)
        layout.addWidget(self.btn_place_pending)

        # Close all button
        self.btn_close_all = QPushButton("Close Active Position(s)")
        self.btn_close_all.setObjectName("closeButton")
        self.btn_close_all.clicked.connect(self.close_all_clicked.emit)
        layout.addWidget(self.btn_close_all)

        layout.addStretch()

    def _adjust_lot(self, delta: float) -> None:
        new_val = max(0.01, round(self.spin_lot.value() + delta, 2))
        self.spin_lot.setValue(new_val)

    def _auto_size_lot(self) -> None:
        sl_val = self.spin_sl.value()
        if sl_val <= 0:
            QMessageBox.warning(self, "Invalid Stop Loss", "Please enter a valid Stop Loss price first.")
            return

        suggested = RiskCalculator.calculate_lot_size(
            balance=self.account_balance,
            risk_pct=self.spin_risk_pct.value(),
            entry_price=self.current_price,
            stop_loss_price=sl_val,
            point_value=self.point_value,
        )
        self.spin_lot.setValue(suggested)
        self._recalc_risk()

    def _recalc_risk(self) -> None:
        sl = self.spin_sl.value() if self.spin_sl.value() > 0 else None
        tp = self.spin_tp.value() if self.spin_tp.value() > 0 else None
        lot = self.spin_lot.value()

        if sl is not None:
            dist = abs(self.current_price - sl)
            pot_loss = dist * lot * self.point_value
            rr_str = f"{(abs(tp - self.current_price) / dist):.1f}" if tp else "0.0"
            self.lbl_risk_info.setText(f"Est. Risk: ${pot_loss:,.2f} | R:R: 1:{rr_str}")
        else:
            self.lbl_risk_info.setText("Est. Risk: $0.00 | R:R: --")

    def _on_order_type_changed(self, text: str) -> None:
        is_market = (text == "Market Order")
        self.entry_container.setVisible(not is_market)
        self.market_buttons_widget.setVisible(is_market)
        self.btn_place_pending.setVisible(not is_market)
        if not is_market:
            self.btn_place_pending.setText(f"Place Pending Order ({text.upper()})")
            if "BUY" in text.upper():
                self.btn_place_pending.setStyleSheet("background-color: #26a69a; color: #ffffff; font-weight: bold; padding: 8px; font-size: 13px; border-radius: 4px;")
            else:
                self.btn_place_pending.setStyleSheet("background-color: #ef5350; color: #ffffff; font-weight: bold; padding: 8px; font-size: 13px; border-radius: 4px;")

    def set_order_parameters(
        self,
        entry: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        lot: Optional[float] = None,
        order_type: Optional[str] = None,
    ) -> None:
        """Sets protective orders (SL/TP), entry price, and order type."""
        if entry is not None and entry > 0:
            self.spin_entry.setValue(float(entry))
        if sl is not None:
            self.spin_sl.setValue(float(sl))
        if tp is not None:
            self.spin_tp.setValue(float(tp))
        if lot is not None:
            self.spin_lot.setValue(float(lot))
        if order_type is not None:
            ot_upper = order_type.upper().replace("_", " ")
            for i in range(self.combo_order_type.count()):
                item_text = self.combo_order_type.itemText(i).upper()
                if item_text in ot_upper or ot_upper in item_text:
                    self.combo_order_type.setCurrentIndex(i)
                    break
        self._recalc_risk()

    def _on_buy(self) -> None:
        lot = self.spin_lot.value()
        sl = self.spin_sl.value() if self.spin_sl.value() > 0 else None
        tp = self.spin_tp.value() if self.spin_tp.value() > 0 else None

        if sl is not None and sl >= self.current_price:
            QMessageBox.warning(self, "Invalid SL", "For BUY order, Stop Loss must be BELOW current price.")
            return
        if tp is not None and tp <= self.current_price:
            QMessageBox.warning(self, "Invalid TP", "For BUY order, Take Profit must be ABOVE current price.")
            return

        self.buy_clicked.emit(lot, sl or 0.0, tp or 0.0)

    def _on_sell(self) -> None:
        lot = self.spin_lot.value()
        sl = self.spin_sl.value() if self.spin_sl.value() > 0 else None
        tp = self.spin_tp.value() if self.spin_tp.value() > 0 else None

        if sl is not None and sl <= self.current_price:
            QMessageBox.warning(self, "Invalid SL", "For SELL order, Stop Loss must be ABOVE current price.")
            return
        if tp is not None and tp >= self.current_price:
            QMessageBox.warning(self, "Invalid TP", "For SELL order, Take Profit must be BELOW current price.")
            return

        self.sell_clicked.emit(lot, sl or 0.0, tp or 0.0)

    def _on_place_pending(self) -> None:
        lot = self.spin_lot.value()
        entry = self.spin_entry.value()
        sl = self.spin_sl.value() if self.spin_sl.value() > 0 else None
        tp = self.spin_tp.value() if self.spin_tp.value() > 0 else None
        type_text = self.combo_order_type.currentText()

        # Map to OrderType string
        type_map = {
            "Buy Limit": "BUY_LIMIT",
            "Buy Stop": "BUY_STOP",
            "Sell Limit": "SELL_LIMIT",
            "Sell Stop": "SELL_STOP",
        }
        order_type = type_map.get(type_text, "BUY_LIMIT")
        self.pending_order_clicked.emit(order_type, lot, entry, sl or 0.0, tp or 0.0)

    def _get_precision(self, symbol: str) -> int:
        sym = symbol.upper()
        if "JPY" in sym:
            return 3
        elif any(fx in sym for fx in ["EUR", "GBP", "AUD", "NZD", "USD", "CAD", "CHF"]) and not any(k in sym for k in ["XAU", "GOLD", "BTC", "ETH", "US30", "SPX"]):
            return 5
        elif "BTC" in sym or "ETH" in sym or "SOL" in sym:
            return 2
        return 2

    def _open_set_capital_dialog(self) -> None:
        dlg = SetBalanceDialog(current_balance=self.account_balance, parent=self)
        if dlg.exec():
            new_bal = dlg.get_balance()
            self.account_balance = new_bal
            self.lbl_balance_val.setText(f"${new_bal:,.2f}")
            self.reset_capital_requested.emit(new_bal)

    def update_account_info(self, balance: float, equity: float) -> None:
        self.account_balance = balance
        self.account_equity = equity
        self.lbl_balance_val.setText(f"${balance:,.2f}")
        bal_color = "#26a69a" if equity >= balance else "#ef5350"
        self.lbl_equity_val.setStyleSheet(f"font-weight: 700; color: {bal_color};")
        self.lbl_equity_val.setText(f"${equity:,.2f}")
        self._recalc_risk()

    def update_market_price(self, symbol: str, price: float, spread: float, balance: float, point_val: float, equity: Optional[float] = None) -> None:
        self.current_symbol = symbol
        self.current_price = price
        self.spread = spread
        self.account_balance = balance
        if equity is not None:
            self.account_equity = equity
        self.point_value = point_val

        self.lbl_balance_val.setText(f"${balance:,.2f}")
        eq = self.account_equity if equity is None else equity
        bal_color = "#26a69a" if eq >= balance else "#ef5350"
        self.lbl_equity_val.setStyleSheet(f"font-weight: 700; color: {bal_color};")
        self.lbl_equity_val.setText(f"${eq:,.2f}")

        prec = self._get_precision(symbol)
        self.spin_entry.setDecimals(prec)
        self.spin_sl.setDecimals(prec)
        self.spin_tp.setDecimals(prec)
        if prec == 5:
            self.spin_entry.setSingleStep(0.0001)
            self.spin_sl.setSingleStep(0.0001)
            self.spin_tp.setSingleStep(0.0001)
        elif prec == 3:
            self.spin_entry.setSingleStep(0.01)
            self.spin_sl.setSingleStep(0.01)
            self.spin_tp.setSingleStep(0.01)
        else:
            self.spin_entry.setSingleStep(0.1)
            self.spin_sl.setSingleStep(0.1)
            self.spin_tp.setSingleStep(0.1)

        bid = price - (spread / 2.0)
        ask = price + (spread / 2.0)

        self.lbl_sym_header.setText(symbol)
        self.lbl_bid.setText(f"BID: {bid:.{prec}f}")
        self.lbl_ask.setText(f"ASK: {ask:.{prec}f}")
        self.btn_buy.setText(f"BUY\n{ask:.{prec}f}")
        self.btn_sell.setText(f"SELL\n{bid:.{prec}f}")

