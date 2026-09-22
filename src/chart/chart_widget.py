import json
from typing import Any, Dict, List, Optional
import pandas as pd
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

from PyQt6.QtWebChannel import QWebChannel

from src.chart.chart_html import get_chart_html
from src.drawings.base_tool import Drawing
from src.utils.logger import logger


class ChartBridge(QObject):
    """Bridge for communication from JavaScript to Python."""
    drawing_created = pyqtSignal(str)
    drawing_updated = pyqtSignal(str)
    drawing_deleted = pyqtSignal(str)
    open_properties_requested = pyqtSignal(str)
    position_modified = pyqtSignal(str, float, float)
    trade_executed_from_drawing = pyqtSignal(str)
    apply_to_order_panel = pyqtSignal(str)
    visible_range_changed = pyqtSignal(str)

    @pyqtSlot(str)
    def onDrawingCreated(self, drawing_json: str):
        self.drawing_created.emit(drawing_json)

    @pyqtSlot(str)
    def onDrawingUpdated(self, drawing_json: str):
        self.drawing_updated.emit(drawing_json)

    @pyqtSlot(str)
    def onDrawingDeleted(self, drawing_id: str):
        self.drawing_deleted.emit(drawing_id)

    @pyqtSlot(str)
    def openProperties(self, drawing_id: str):
        self.open_properties_requested.emit(drawing_id)

    @pyqtSlot(str, float, float)
    def onPositionModified(self, pos_id: str, new_sl: float, new_tp: float):
        self.position_modified.emit(pos_id, new_sl, new_tp)

    @pyqtSlot(str)
    def onExecuteTradeFromDrawing(self, trade_json: str):
        self.trade_executed_from_drawing.emit(trade_json)

    @pyqtSlot(str)
    def onApplyToOrderPanel(self, trade_json: str):
        self.apply_to_order_panel.emit(trade_json)

    @pyqtSlot(str)
    def onVisibleRangeChanged(self, range_json: str):
        self.visible_range_changed.emit(range_json)


class ChartWidget(QWebEngineView):
    """
    High-performance PyQt6 WebEngine chart widget hosting Lightweight Charts
    and an interactive drawing / trade visualization canvas.
    """
    chart_ready = pyqtSignal()
    drawing_created_signal = pyqtSignal(dict)
    drawing_updated_signal = pyqtSignal(dict)
    drawing_deleted_signal = pyqtSignal(str)
    drawing_properties_signal = pyqtSignal(str)
    position_modified_signal = pyqtSignal(str, float, float)
    trade_executed_from_drawing_signal = pyqtSignal(dict)
    apply_to_order_panel_signal = pyqtSignal(dict)
    visible_range_changed_signal = pyqtSignal(dict)

    def __init__(self, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.theme = theme
        self._is_loaded = False
        self._pending_data: Optional[Dict[str, Any]] = None
        self.current_visible_range: Optional[Dict[str, Any]] = None

        self.bridge = ChartBridge()
        self.channel = QWebChannel(self.page())
        self.channel.registerObject("qtBridge", self.bridge)
        self.page().setWebChannel(self.channel)

        self.bridge.drawing_created.connect(self._on_js_drawing_created)
        self.bridge.drawing_updated.connect(self._on_js_drawing_updated)
        self.bridge.drawing_deleted.connect(self.drawing_deleted_signal.emit)
        self.bridge.open_properties_requested.connect(self.drawing_properties_signal.emit)
        self.bridge.position_modified.connect(self.position_modified_signal.emit)
        self.bridge.trade_executed_from_drawing.connect(self._on_js_trade_executed)
        self.bridge.apply_to_order_panel.connect(self._on_js_apply_to_panel)
        self.bridge.visible_range_changed.connect(self._on_js_visible_range_changed)

        self.loadFinished.connect(self._on_load_finished)
        self.init_chart_view()

    def init_chart_view(self) -> None:
        html_content = get_chart_html(theme=self.theme)
        self.setHtml(html_content, QUrl("http://localhost"))

    def _on_load_finished(self, ok: bool) -> None:
        self._is_loaded = ok
        if ok:
            logger.info("Chart WebEngine view loaded successfully.")
            if self._pending_data:
                self.set_chart_data(
                    self._pending_data["candles"],
                    self._pending_data.get("volume"),
                    self._pending_data.get("visible_range")
                )
                self._pending_data = None
            self.chart_ready.emit()
        else:
            logger.error("Failed to load Chart WebEngine view.")

    def _on_js_visible_range_changed(self, range_json: str) -> None:
        try:
            self.current_visible_range = json.loads(range_json)
            self.visible_range_changed_signal.emit(self.current_visible_range)
        except Exception:
            pass

    def _on_js_drawing_created(self, drawing_json: str) -> None:
        try:
            d = json.loads(drawing_json)
            self.drawing_created_signal.emit(d)
        except Exception as e:
            logger.error(f"Error parsing drawing created in JS: {e}")

    def _on_js_drawing_updated(self, drawing_json: str) -> None:
        try:
            d = json.loads(drawing_json)
            self.drawing_updated_signal.emit(d)
        except Exception as e:
            logger.error(f"Error parsing drawing updated in JS: {e}")

    def _on_js_trade_executed(self, trade_json: str) -> None:
        try:
            d = json.loads(trade_json)
            self.trade_executed_from_drawing_signal.emit(d)
        except Exception as e:
            logger.error(f"Error parsing executed trade from drawing: {e}")

    def _on_js_apply_to_panel(self, trade_json: str) -> None:
        try:
            d = json.loads(trade_json)
            self.apply_to_order_panel_signal.emit(d)
        except Exception as e:
            logger.error(f"Error parsing apply to panel from drawing: {e}")

    def set_symbol(self, symbol: str) -> None:
        """Updates active symbol, watermark, and price scale decimal precision."""
        if not self._is_loaded:
            return
        self.page().runJavaScript(f"setSymbol('{symbol}');")

    def set_chart_data(self, candle_data: List[Dict[str, Any]], volume_data: Optional[List[Dict[str, Any]]] = None, visible_range: Optional[Dict[str, Any]] = None) -> None:
        """Sets full historical candle data up to current replay position."""
        if not self._is_loaded:
            self._pending_data = {"candles": candle_data, "volume": volume_data or [], "visible_range": visible_range}
            return

        c_json = json.dumps(candle_data)
        v_json = json.dumps(volume_data or [])
        r_json = json.dumps(visible_range) if visible_range else "null"
        js_code = f"setChartData({c_json}, {v_json}, {r_json});"
        self.page().runJavaScript(js_code)


    def update_candle(self, candle: Dict[str, Any], volume: Optional[Dict[str, Any]] = None) -> None:
        """Appends or updates a single candle incrementally during replay."""
        if not self._is_loaded:
            return

        c_json = json.dumps(candle)
        v_json = json.dumps(volume) if volume else "null"
        js_code = f"updateCandle({c_json}, {v_json});"
        self.page().runJavaScript(js_code)

    def set_markers(self, markers: List[Dict[str, Any]]) -> None:
        """Sets trade entry/exit markers."""
        if not self._is_loaded:
            return
        m_json = json.dumps(markers)
        self.page().runJavaScript(f"setMarkers({m_json});")

    def set_drawings(self, drawings: List[Dict[str, Any]]) -> None:
        """Syncs all user drawings with chart overlay."""
        if not self._is_loaded:
            return
        d_json = json.dumps(drawings)
        self.page().runJavaScript(f"setDrawings({d_json});")

    def set_trade_overlays(self, overlays: Dict[str, Any]) -> None:
        """Syncs active position lines and SL/TP overlays."""
        if not self._is_loaded:
            return
        o_json = json.dumps(overlays)
        self.page().runJavaScript(f"setTradeOverlays({o_json});")

    def set_active_tool(self, tool_name: str) -> None:
        """Activates a drawing tool (e.g. 'TRENDLINE', 'RECTANGLE', 'CURSOR')."""
        if not self._is_loaded:
            return
        self.page().runJavaScript(f"setActiveTool('{tool_name}');")

    def set_volume_visible(self, visible: bool) -> None:
        """Toggles visibility of the bottom volume histogram."""
        if not self._is_loaded:
            return
        self.page().runJavaScript(f"setVolumeVisible({str(visible).lower()});")

    def set_indicator_data(self, indicator_id: str, series_data: List[Dict[str, Any]]) -> None:
        """Updates or creates indicator line/histogram series."""
        if not self._is_loaded:
            return
        payload = json.dumps(series_data)
        self.page().runJavaScript(f"setIndicatorData('{indicator_id}', {payload});")

    def remove_indicator(self, indicator_id: str) -> None:
        """Removes an indicator from the chart."""
        if not self._is_loaded:
            return
        self.page().runJavaScript(f"removeIndicator('{indicator_id}');")

    def set_indicator_visible(self, indicator_id: str, visible: bool) -> None:
        """Toggles an indicator's visibility."""
        if not self._is_loaded:
            return
        self.page().runJavaScript(f"setIndicatorVisible('{indicator_id}', {str(visible).lower()});")

    def set_theme(self, theme_name: str, colors: Dict[str, str]) -> None:
        """Dynamically applies theme colors to chart background, text, grid and toolbar."""
        self.theme = theme_name
        if not self._is_loaded:
            return
        bg = colors.get("bg_color", "#131722")
        txt = colors.get("text_color", "#d1d4dc")
        grid = colors.get("grid_color", "#1e222d")
        card = colors.get("card_bg", "#1e222d")
        border = colors.get("border_color", "#2a2e39")
        self.page().runJavaScript(f"setTheme('{theme_name}', '{bg}', '{txt}', '{grid}', '{card}', '{border}');")

    def reset_price_scale(self) -> None:
        """Forces the vertical price scale to auto-scale mode, fitting current candle prices."""
        if not self._is_loaded:
            return
        self.page().runJavaScript("resetPriceScale();")

    def reset_view(self) -> None:
        """Resets both vertical price scale and horizontal time scale to optimal default framing."""
        if not self._is_loaded:
            return
        self.page().runJavaScript("resetView();")

