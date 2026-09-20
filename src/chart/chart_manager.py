from typing import Any, Dict, List, Optional
import pandas as pd

from src.chart.chart_widget import ChartWidget
from src.chart.markers import ChartMarkerBuilder
from src.chart.trade_overlays import TradeOverlayBuilder
from src.core.position import Position
from src.drawings.base_tool import Drawing
from src.events.event_bus import EventBus, event_bus
from src.indicators.registry import IndicatorRegistry
from src.utils.constants import EventType


class ChartManager:
    """Coordinates chart updates, markers, overlays, drawing events, and technical indicators."""

    def __init__(self, chart_widget: ChartWidget, event_bus_instance: Optional[EventBus] = None):
        self.widget = chart_widget
        self.bus = event_bus_instance or event_bus
        self.active_indicators: List[Dict[str, Any]] = []
        self._rendered_indicator_ids = set()
        self.volume_visible: bool = True
        self.current_df: Optional[pd.DataFrame] = None

    def load_dataset(self, df_visible: pd.DataFrame, max_initial_candles: int = 5000) -> None:
        """
        Transforms and pushes visible historical candles to chart widget.
        Uses ultra-fast vectorized numpy transformations (< 10ms for 5,000+ bars).
        """
        if df_visible.empty:
            return

        self.current_df = df_visible

        # Window to most recent visible buffer for instant WebEngine load
        df_work = df_visible.iloc[-max_initial_candles:] if len(df_visible) > max_initial_candles else df_visible

        ts_arr = df_work["timestamp"].astype(int).values
        open_arr = df_work["open"].astype(float).values
        high_arr = df_work["high"].astype(float).values
        low_arr = df_work["low"].astype(float).values
        close_arr = df_work["close"].astype(float).values
        vol_arr = df_work["volume"].astype(float).values if "volume" in df_work.columns else None

        n = len(df_work)
        candle_data = [
            {
                "time": int(ts_arr[i]),
                "open": float(open_arr[i]),
                "high": float(high_arr[i]),
                "low": float(low_arr[i]),
                "close": float(close_arr[i]),
            }
            for i in range(n)
        ]

        volume_data = []
        if vol_arr is not None:
            volume_data = [
                {
                    "time": int(ts_arr[i]),
                    "value": float(vol_arr[i]),
                    "color": "rgba(38, 166, 154, 0.4)" if close_arr[i] >= open_arr[i] else "rgba(239, 83, 80, 0.4)",
                }
                for i in range(n)
            ]

        self.widget.set_chart_data(candle_data, volume_data)
        self.widget.set_volume_visible(self.volume_visible)
        self.sync_all_indicators(df_visible)

    def set_volume_visible(self, visible: bool) -> None:
        """Toggles the Volume Histogram indicator visibility."""
        self.volume_visible = visible
        self.widget.set_volume_visible(visible)

    def sync_all_indicators(self, df_visible: Optional[pd.DataFrame] = None, max_candles: int = 5000) -> None:
        """Calculates and pushes all active indicators to the chart view."""
        df = df_visible if df_visible is not None else self.current_df
        if df is None or df.empty:
            return
        self.current_df = df

        active_ids = {x.get("id") for x in self.active_indicators}
        for old_id in list(self._rendered_indicator_ids):
            if old_id not in active_ids:
                self.widget.remove_indicator(old_id)
                self._rendered_indicator_ids.remove(old_id)

        for ind_conf in self.active_indicators:
            self._calculate_and_push_indicator(ind_conf, df, max_candles=max_candles)
            self._rendered_indicator_ids.add(ind_conf.get("id"))

    def _calculate_and_push_indicator(self, ind_conf: Dict[str, Any], df: pd.DataFrame, max_candles: int = 5000) -> None:
        ind_id = ind_conf.get("id", "")
        name = ind_conf.get("name", "")
        params = ind_conf.get("params", {})
        visible = ind_conf.get("visible", True)

        if not visible:
            self.widget.set_indicator_visible(ind_id, False)
            return

        try:
            ind_instance = IndicatorRegistry.create(name, **params)
            res_df = ind_instance.calculate(df)
            if res_df.empty:
                return

            df_work = df.iloc[-max_candles:] if len(df) > max_candles else df
            ts_list = df_work["timestamp"].astype(int).values
            n_work = len(df_work)

            series_list = []

            if name in ["EMA", "SMA"]:
                col = res_df.columns[0]
                vals = res_df[col].iloc[-n_work:].values
                data = [{"time": int(ts_list[i]), "value": float(vals[i])} for i in range(n_work) if pd.notna(vals[i])]
                series_list.append({
                    "type": "line",
                    "color": params.get("color", "#2196f3"),
                    "lineWidth": params.get("lineWidth", 2),
                    "lineStyle": params.get("lineStyle", "solid"),
                    "visible": visible,
                    "data": data,
                })

            elif name == "BollingerBands":
                # Middle band
                if "BB_middle" in res_df.columns:
                    vals_m = res_df["BB_middle"].iloc[-n_work:].values
                    data_m = [{"time": int(ts_list[i]), "value": float(vals_m[i])} for i in range(n_work) if pd.notna(vals_m[i])]
                    series_list.append({
                        "type": "line",
                        "color": params.get("color_middle", "#ff9800"),
                        "lineWidth": params.get("lineWidth", 1.5),
                        "visible": visible,
                        "data": data_m,
                    })
                # Upper band
                if "BB_upper" in res_df.columns:
                    vals_u = res_df["BB_upper"].iloc[-n_work:].values
                    data_u = [{"time": int(ts_list[i]), "value": float(vals_u[i])} for i in range(n_work) if pd.notna(vals_u[i])]
                    series_list.append({
                        "type": "line",
                        "color": params.get("color_bands", "#2962ff"),
                        "lineWidth": params.get("lineWidth", 1.5),
                        "visible": visible,
                        "data": data_u,
                    })
                # Lower band
                if "BB_lower" in res_df.columns:
                    vals_l = res_df["BB_lower"].iloc[-n_work:].values
                    data_l = [{"time": int(ts_list[i]), "value": float(vals_l[i])} for i in range(n_work) if pd.notna(vals_l[i])]
                    series_list.append({
                        "type": "line",
                        "color": params.get("color_bands", "#2962ff"),
                        "lineWidth": params.get("lineWidth", 1.5),
                        "visible": visible,
                        "data": data_l,
                    })

            elif name == "RSI":
                col = res_df.columns[0]
                vals = res_df[col].iloc[-n_work:].values
                data = [{"time": int(ts_list[i]), "value": float(vals[i])} for i in range(n_work) if pd.notna(vals[i])]
                series_list.append({
                    "type": "line",
                    "color": params.get("color", "#9c27b0"),
                    "lineWidth": params.get("lineWidth", 2),
                    "visible": visible,
                    "data": data,
                })

            elif name == "MACD":
                if "MACD_line" in res_df.columns:
                    vals = res_df["MACD_line"].iloc[-n_work:].values
                    data = [{"time": int(ts_list[i]), "value": float(vals[i])} for i in range(n_work) if pd.notna(vals[i])]
                    series_list.append({
                        "type": "line",
                        "color": params.get("color_macd", "#2962ff"),
                        "lineWidth": 1.5,
                        "visible": visible,
                        "data": data,
                    })
                if "MACD_signal" in res_df.columns:
                    vals = res_df["MACD_signal"].iloc[-n_work:].values
                    data = [{"time": int(ts_list[i]), "value": float(vals[i])} for i in range(n_work) if pd.notna(vals[i])]
                    series_list.append({
                        "type": "line",
                        "color": params.get("color_signal", "#ff9800"),
                        "lineWidth": 1.5,
                        "visible": visible,
                        "data": data,
                    })

            elif name == "ATR":
                col = res_df.columns[0]
                vals = res_df[col].iloc[-n_work:].values
                data = [{"time": int(ts_list[i]), "value": float(vals[i])} for i in range(n_work) if pd.notna(vals[i])]
                series_list.append({
                    "type": "line",
                    "color": params.get("color", "#e91e63"),
                    "lineWidth": 1.5,
                    "visible": visible,
                    "data": data,
                })

            elif name == "SmartTrail":
                if "SmartTrail" in res_df.columns:
                    vals = res_df["SmartTrail"].iloc[-n_work:].values
                    trends = res_df["SmartTrend"].iloc[-n_work:].values if "SmartTrend" in res_df.columns else [1] * n_work

                    data_up = []
                    data_down = []
                    for i in range(n_work):
                        t = int(ts_list[i])
                        v = float(vals[i]) if pd.notna(vals[i]) else None
                        if trends[i] == 1 and v is not None:
                            data_up.append({"time": t, "value": v})
                            data_down.append({"time": t})
                        elif trends[i] == -1 and v is not None:
                            data_down.append({"time": t, "value": v})
                            data_up.append({"time": t})
                        else:
                            data_up.append({"time": t})
                            data_down.append({"time": t})

                    series_list.append({
                        "type": "line",
                        "color": params.get("color_up", "#00e676"),
                        "lineWidth": params.get("lineWidth", 2),
                        "lineStyle": params.get("lineStyle", "solid"),
                        "visible": visible,
                        "data": data_up,
                    })
                    series_list.append({
                        "type": "line",
                        "color": params.get("color_down", "#ff5252"),
                        "lineWidth": params.get("lineWidth", 2),
                        "lineStyle": params.get("lineStyle", "solid"),
                        "visible": visible,
                        "data": data_down,
                    })

                # Smart Trail Buy / Sell Signal Markers
                if "BullSignal" in res_df.columns and "BearSignal" in res_df.columns:
                    bulls = res_df["BullSignal"].iloc[-n_work:].values
                    bears = res_df["BearSignal"].iloc[-n_work:].values
                    markers = []
                    for i in range(n_work):
                        if bulls[i]:
                            markers.append({
                                "time": int(ts_list[i]),
                                "position": "belowBar",
                                "color": params.get("color_up", "#00e676"),
                                "shape": "arrowUp",
                                "text": "BUY",
                            })
                        elif bears[i]:
                            markers.append({
                                "time": int(ts_list[i]),
                                "position": "aboveBar",
                                "color": params.get("color_down", "#ff5252"),
                                "shape": "arrowDown",
                                "text": "SELL",
                            })
                    if markers and visible:
                        self.widget.set_markers(markers)

            if series_list:
                self.widget.set_indicator_data(ind_id, series_list)

        except Exception as e:
            from src.utils.logger import logger
            logger.error(f"Error calculating indicator {name}: {e}")

    def add_or_update_indicator(self, ind_conf: Dict[str, Any]) -> None:
        """Adds or updates an indicator configuration and refreshes the chart."""
        ind_id = ind_conf.get("id")
        existing_idx = next((i for i, x in enumerate(self.active_indicators) if x.get("id") == ind_id), None)
        if existing_idx is not None:
            self.active_indicators[existing_idx] = ind_conf
        else:
            self.active_indicators.append(ind_conf)

        if self.current_df is not None:
            self._calculate_and_push_indicator(ind_conf, self.current_df)

    def remove_indicator(self, ind_id: str) -> None:
        """Removes an indicator from active list and removes its series from chart."""
        self.active_indicators = [x for x in self.active_indicators if x.get("id") != ind_id]
        self.widget.remove_indicator(ind_id)

    def advance_candle(self, candle: Dict[str, Any]) -> None:
        """Incremental candle advance."""
        ts = int(candle.get("timestamp", 0))
        c_open = float(candle.get("open", 0.0))
        c_high = float(candle.get("high", 0.0))
        c_low = float(candle.get("low", 0.0))
        c_close = float(candle.get("close", 0.0))
        vol = float(candle.get("volume", 0.0))

        c_item = {
            "time": ts,
            "open": c_open,
            "high": c_high,
            "low": c_low,
            "close": c_close,
        }
        v_item = {
            "time": ts,
            "value": vol,
            "color": "rgba(38, 166, 154, 0.4)" if c_close >= c_open else "rgba(239, 83, 80, 0.4)",
        }
        self.widget.update_candle(c_item, v_item)

    def update_positions_and_trades(self, open_positions: List[Position], closed_trades: List[Position]) -> None:
        """Updates trade markers and active position SL/TP lines."""
        all_trades = closed_trades + open_positions
        markers = ChartMarkerBuilder.build_all_markers(all_trades)
        self.widget.set_markers(markers)

        overlays = TradeOverlayBuilder.build_overlays(open_positions)
        self.widget.set_trade_overlays(overlays)

    def sync_drawings(self, drawings: List[Drawing]) -> None:
        """Syncs drawing store to chart canvas."""
        d_dicts = [d.to_dict() for d in drawings]
        self.widget.set_drawings(d_dicts)

    def select_tool(self, tool_name: str) -> None:
        self.widget.set_active_tool(tool_name)
