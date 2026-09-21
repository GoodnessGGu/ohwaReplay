import pytest
from PyQt6.QtWidgets import QApplication

from src.utils.constants import ASSET_CATEGORIES
from ui.chart_tab_bar import ChartTabBar, ChartTabInfo
from ui.symbol_search_dialog import SymbolSearchDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_chart_tab_bar_basics(qapp):
    tab_bar = ChartTabBar(max_tabs=4)
    assert len(tab_bar.tabs) == 0

    # Add first tab
    idx0 = tab_bar.add_tab("XAUUSD", "5m", mode="replay")
    assert idx0 == 0
    assert len(tab_bar.tabs) == 1
    assert tab_bar.tabs[0].symbol == "XAUUSD"
    assert tab_bar.tabs[0].timeframe == "5m"

    # Add second and third tab
    idx1 = tab_bar.add_tab("EURUSD", "15m", mode="replay")
    idx2 = tab_bar.add_tab("BTCUSD", "1h", mode="live")
    assert idx1 == 1
    assert idx2 == 2
    assert len(tab_bar.tabs) == 3

    # Add 4th tab (limit reached)
    idx3 = tab_bar.add_tab("USDJPY", "4h", mode="replay")
    assert idx3 == 3
    assert len(tab_bar.tabs) == 4
    assert not tab_bar.btn_add_tab.isEnabled()

    # Attempt to add 5th tab (should be rejected)
    idx4 = tab_bar.add_tab("GBPUSD", "15m", mode="replay")
    assert idx4 is None
    assert len(tab_bar.tabs) == 4

    # Update tab label
    tab_bar.update_tab_label(0, "XAUUSD", "1m", "live")
    assert tab_bar.tabs[0].timeframe == "1m"
    assert tab_bar.tabs[0].mode == "live"

    # Remove tab
    tab_bar.remove_tab(1)
    assert len(tab_bar.tabs) == 3
    assert tab_bar.btn_add_tab.isEnabled()



def test_asset_categories():
    assert "Forex Majors" in ASSET_CATEGORIES
    assert "Forex Crosses" in ASSET_CATEGORIES
    assert "Metals & Commodities" in ASSET_CATEGORIES
    assert "Indices" in ASSET_CATEGORIES
    assert "Crypto (24/7)" in ASSET_CATEGORIES

    # Check some essential assets
    crypto_symbols = [sym for sym, _ in ASSET_CATEGORIES["Crypto (24/7)"]]
    assert "BTCUSD" in crypto_symbols
    assert "ETHUSD" in crypto_symbols
    assert "SOLUSD" in crypto_symbols

    forex_symbols = [sym for sym, _ in ASSET_CATEGORIES["Forex Majors"]]
    assert "EURUSD" in forex_symbols
    assert "GBPUSD" in forex_symbols
    assert "USDJPY" in forex_symbols
