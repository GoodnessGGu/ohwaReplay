import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.analytics.analytics import AnalyticsEngine
from src.analytics.statistics import StatisticsCalculator
from src.chart.chart_manager import ChartManager
from src.chart.chart_widget import ChartWidget
from src.core.account_engine import AccountEngine
from src.data.data_loader import DataLoader
from src.data.live_feed import LiveDataLoader, LiveFeedWorker
from src.data.mt5_connector import mt5_connector
from src.data.synthetic_data import SyntheticDataGenerator
from src.drawings.base_tool import Drawing
from src.drawings.drawing_store import DrawingStore
from src.events.event_bus import EventBus, event_bus
from src.notifications.notification_manager import NotificationManager
from src.replay.replay_controller import ReplayController
from src.utils.audio_manager import audio_manager
from src.utils.constants import Direction, EventType, IntrabarExecutionMode, OrderType
from src.utils.helpers import load_yaml_config
from src.utils.logger import logger
from src.workspace.workspace_manager import WorkspaceManager
from src.workspace.workspace_schema import WorkspaceSchema

from ui.analytics_panel import AnalyticsPanel
from ui.backtest_dialog import BacktestDialog
from ui.chart_tab_bar import ChartTabBar, ChartTabInfo
from ui.dashboard import DashboardWidget
from ui.drawing_properties_dialog import DrawingPropertiesDialog
from ui.drawing_toolbar import DrawingToolBar
from ui.execution_panel import ExecutionPanel
from ui.history_panel import HistoryPanel
from ui.journal_panel import JournalPanel
from ui.mt5_dialog import MT5Dialog
from ui.positions_panel import PositionsPanel
from ui.replay_bar import ReplayBar
from ui.settings_dialog import SettingsDialog
from ui.symbol_search_dialog import SymbolSearchDialog
from ui.theme_manager import ThemeManager
from ui.toolbar import MainToolBar


class MainWindow(QMainWindow):
    """
    Main application window for Trading Replay Lab.
    Integrates all subsystems: Chart, Replay, Account, Analytics, Drawings, Workspace.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Replay Lab - Professional Manual Workstation")
        self.resize(1440, 900)

        # 1. Load config
        self.config = load_yaml_config("config.yaml")
        self.current_theme = self.config.get("appearance", {}).get("theme", "Dark Charcoal")

        # 2. Core services
        self.bus = event_bus
        self.replay_controller = ReplayController(event_bus_instance=self.bus)
        self.account_engine = AccountEngine(
            initial_balance=float(self.config.get("account", {}).get("initial_balance", 10000.0)),
            leverage=int(self.config.get("account", {}).get("leverage", 100)),
            commission_per_lot=float(self.config.get("account", {}).get("commission", 7.0)),
            spread=float(self.config.get("account", {}).get("spread", 0.20)),
            slippage=float(self.config.get("account", {}).get("slippage", 0.05)),
            intrabar_mode=IntrabarExecutionMode(
                self.config.get("account", {}).get("intrabar_execution", "CONSERVATIVE")
            ),
            event_bus_instance=self.bus,
        )
        self.drawing_store = DrawingStore(event_bus_instance=self.bus)
        self.analytics_engine = AnalyticsEngine(initial_balance=self.account_engine.initial_balance)
        self.notification_manager = NotificationManager(event_bus_instance=self.bus)
        self.workspace_manager = WorkspaceManager(event_bus_instance=self.bus)

        # High-Performance In-Memory Data Cache & UI Throttling
        self._data_cache: Dict[tuple, pd.DataFrame] = {}
        self._heavy_update_timer = QTimer(self)
        self._heavy_update_timer.setSingleShot(True)
        self._heavy_update_timer.timeout.connect(self._update_heavy_views)

        # 3. Playback & Live streaming services
        self.replay_timer = QTimer(self)
        self.replay_timer.timeout.connect(self._on_replay_timer_tick)
        self.live_worker: Optional[LiveFeedWorker] = None
        self.audio_manager = audio_manager

        # 4. Initialize UI
        self.init_ui()
        self.setup_menu_bar()
        self.setup_shortcuts()
        self.wire_events()

        # 5. Load default dataset
        self.load_initial_data()

    def init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Dashboard Header
        self.dashboard = DashboardWidget(self)
        main_layout.addWidget(self.dashboard)

        # Toolbar
        self.toolbar = MainToolBar(self)
        self.addToolBar(self.toolbar)

        # Main splitter (Top: Chart + Execution Panel, Bottom: Tabbed Information Panel)
        v_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top area splitter (Chart + Execution)
        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Chart container with left Drawing Toolbar (TradingView style) and bottom Replay Bar
        chart_container = QWidget()
        chart_outer_layout = QHBoxLayout(chart_container)
        chart_outer_layout.setContentsMargins(0, 0, 0, 0)
        chart_outer_layout.setSpacing(0)

        # Left Vertical Drawing Toolbar (Locked to left side)
        self.drawing_toolbar = DrawingToolBar(self)
        chart_outer_layout.addWidget(self.drawing_toolbar)

        # Central Chart and Replay Bar area
        chart_center_widget = QWidget()
        chart_center_layout = QVBoxLayout(chart_center_widget)
        chart_center_layout.setContentsMargins(0, 0, 0, 0)
        chart_center_layout.setSpacing(0)

        # Multi-Chart Tab Bar (Up to 4 Tabs with '+')
        self.chart_tab_bar = ChartTabBar(max_tabs=4, parent=self)
        self.current_tab_index = 0
        chart_center_layout.addWidget(self.chart_tab_bar)

        # Splitter for Multi-Chart View (Single vs Dual Split)
        self.chart_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.chart_widget = ChartWidget(theme="dark", parent=self)
        self.chart_manager = ChartManager(self.chart_widget, event_bus_instance=self.bus)
        self.chart_splitter.addWidget(self.chart_widget)

        # Secondary HTF Chart (Hidden by default, shown in dual layout)
        self.chart_widget_htf = ChartWidget(theme="dark", parent=self)
        self.chart_manager_htf = ChartManager(self.chart_widget_htf, event_bus_instance=self.bus)
        self.chart_widget_htf.setVisible(False)
        self.chart_splitter.addWidget(self.chart_widget_htf)

        chart_center_layout.addWidget(self.chart_splitter, 1)

        self.replay_bar = ReplayBar(self)
        chart_center_layout.addWidget(self.replay_bar)

        chart_outer_layout.addWidget(chart_center_widget, 1)

        h_splitter.addWidget(chart_container)

        # Right Trading Execution Panel
        self.exec_panel = ExecutionPanel(self)
        h_splitter.addWidget(self.exec_panel)
        h_splitter.setStretchFactor(0, 4)
        h_splitter.setStretchFactor(1, 1)

        v_splitter.addWidget(h_splitter)

        # Bottom Tabbed Information Panel
        self.tabs = QTabWidget()
        self.positions_panel = PositionsPanel(self)
        self.history_panel = HistoryPanel(self)
        self.analytics_panel = AnalyticsPanel(self)
        self.journal_panel = JournalPanel(self)

        self.tabs.addTab(self.positions_panel, "Positions (0)")
        self.tabs.addTab(self.history_panel, "Trade History")
        self.tabs.addTab(self.analytics_panel, "Analytics")
        self.tabs.addTab(self.journal_panel, "Trade Journal")

        v_splitter.addWidget(self.tabs)
        v_splitter.setStretchFactor(0, 3)
        v_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(v_splitter)

    def setup_menu_bar(self) -> None:
        mb = self.menuBar()

        # File Menu
        file_menu = mb.addMenu("&File")

        act_open_csv = QAction("Open &CSV Market Data...", self)
        act_open_csv.triggered.connect(self._menu_open_csv)
        file_menu.addAction(act_open_csv)

        act_new_ws = QAction("&New Workspace", self)
        act_new_ws.triggered.connect(self._menu_new_workspace)
        file_menu.addAction(act_new_ws)

        act_open_ws = QAction("&Open Workspace...", self)
        act_open_ws.triggered.connect(self._menu_open_workspace)
        file_menu.addAction(act_open_ws)

        act_save_ws = QAction("&Save Workspace", self)
        act_save_ws.setShortcut(QKeySequence("Ctrl+S"))
        act_save_ws.triggered.connect(self._menu_save_workspace)
        file_menu.addAction(act_save_ws)

        act_export_csv = QAction("&Export Trade History CSV...", self)
        act_export_csv.triggered.connect(self._menu_export_history)
        file_menu.addAction(act_export_csv)

        file_menu.addSeparator()
        act_exit = QAction("E&xit", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # Data & Broker Menu
        data_menu = mb.addMenu("&Data")
        act_mt5 = QAction("🔌 &MetaTrader 5 / FOREX.com Bridge...", self)
        act_mt5.setShortcut(QKeySequence("Ctrl+M"))
        act_mt5.triggered.connect(self._open_mt5_dialog)
        data_menu.addAction(act_mt5)

        act_sync_mt5 = QAction("📥 &Sync Historical Broker Data from MT5", self)
        act_sync_mt5.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_sync_mt5.triggered.connect(self._sync_mt5_history)
        data_menu.addAction(act_sync_mt5)

        data_menu.addSeparator()
        act_open_csv2 = QAction("Open &CSV Market Data...", self)
        act_open_csv2.triggered.connect(self._menu_open_csv)
        data_menu.addAction(act_open_csv2)

        # Replay Menu
        replay_menu = mb.addMenu("&Replay")
        act_play = QAction("&Play / Pause", self)
        act_play.setShortcut(QKeySequence("Space"))
        act_play.triggered.connect(self._toggle_replay)
        replay_menu.addAction(act_play)

        act_step_fwd = QAction("Step &Forward", self)
        act_step_fwd.setShortcut(QKeySequence("Right"))
        act_step_fwd.triggered.connect(self._step_forward)
        replay_menu.addAction(act_step_fwd)

        act_step_back = QAction("Step &Backward", self)
        act_step_back.setShortcut(QKeySequence("Left"))
        act_step_back.triggered.connect(self._step_backward)
        replay_menu.addAction(act_step_back)

        act_random = QAction("&Random Start", self)
        act_random.triggered.connect(self._random_start)
        replay_menu.addAction(act_random)

        # Trading Menu
        trading_menu = mb.addMenu("&Trading")
        act_buy = QAction("Market &Buy", self)
        act_buy.setShortcut(QKeySequence("B"))
        act_buy.triggered.connect(lambda: self.exec_panel._on_buy())
        trading_menu.addAction(act_buy)

        act_sell = QAction("Market &Sell", self)
        act_sell.setShortcut(QKeySequence("S"))
        act_sell.triggered.connect(lambda: self.exec_panel._on_sell())
        trading_menu.addAction(act_sell)

        act_close = QAction("&Close Active Position(s)", self)
        act_close.setShortcut(QKeySequence("C"))
        act_close.triggered.connect(self._close_all_positions)
        trading_menu.addAction(act_close)

        trading_menu.addSeparator()
        act_backtest = QAction("🚀 &Automated Strategy Backtester...", self)
        act_backtest.setShortcut(QKeySequence("Ctrl+B"))
        act_backtest.triggered.connect(self._open_backtest_dialog)
        trading_menu.addAction(act_backtest)

        # View Menu
        view_menu = mb.addMenu("&View")
        theme_menu = view_menu.addMenu("🎨 &Themes")
        for th_name in ThemeManager.get_theme_names():
            act_th = QAction(th_name, self)
            act_th.triggered.connect(lambda checked, name=th_name: self._apply_theme(name))
            theme_menu.addAction(act_th)

        # Chart Menu
        chart_menu = mb.addMenu("&Chart")
        act_indicators = QAction("𝑓𝑥 &Indicators & Strategies...", self)
        act_indicators.setShortcut(QKeySequence("Ctrl+I"))
        act_indicators.triggered.connect(self._open_indicators_dialog)
        chart_menu.addAction(act_indicators)

        # Help Menu
        help_menu = mb.addMenu("&Help")
        act_shortcuts = QAction("&Keyboard Shortcuts", self)
        act_shortcuts.triggered.connect(self._show_shortcuts_dialog)
        help_menu.addAction(act_shortcuts)

        act_about = QAction("&About Trading Replay Lab", self)
        act_about.triggered.connect(self._show_about_dialog)
        help_menu.addAction(act_about)

    def setup_shortcuts(self) -> None:
        # Indicators & Tools shortcuts
        QShortcut(QKeySequence("Ctrl+I"), self, activated=self._open_indicators_dialog)
        QShortcut(QKeySequence("Ctrl+B"), self, activated=self._open_backtest_dialog)
        QShortcut(QKeySequence("Ctrl+M"), self, activated=self._open_mt5_dialog)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, activated=self._sync_mt5_history)
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self._open_symbol_search_dialog)

        # Multi-Chart Tabs shortcuts (Ctrl+T for new tab, Ctrl+W for close, Ctrl+1..4 for direct switch)
        QShortcut(QKeySequence("Ctrl+T"), self, activated=self._on_tab_add_requested)
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self._close_current_tab)
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self._switch_to_tab_index(0))
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self._switch_to_tab_index(1))
        QShortcut(QKeySequence("Ctrl+3"), self, activated=lambda: self._switch_to_tab_index(2))
        QShortcut(QKeySequence("Ctrl+4"), self, activated=lambda: self._switch_to_tab_index(3))

        # Drawing shortcuts (Left Toolbar)
        QShortcut(QKeySequence("T"), self, activated=lambda: self.drawing_toolbar.set_active_tool("TRENDLINE"))
        QShortcut(QKeySequence("R"), self, activated=lambda: self.drawing_toolbar.set_active_tool("RECTANGLE"))
        QShortcut(QKeySequence("F"), self, activated=lambda: self.drawing_toolbar.set_active_tool("FIBONACCI"))
        QShortcut(QKeySequence("L"), self, activated=lambda: self.drawing_toolbar.set_active_tool("LONG_POSITION"))
        QShortcut(QKeySequence("Shift+L"), self, activated=lambda: self.drawing_toolbar.set_active_tool("SHORT_POSITION"))
        QShortcut(QKeySequence("Esc"), self, activated=lambda: self.drawing_toolbar.set_active_tool("CURSOR"))
        QShortcut(QKeySequence("Ctrl+Z"), self, activated=self._undo_drawing)
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=self._redo_drawing)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, activated=self._redo_drawing)

    def wire_events(self) -> None:
        # Multi-Chart Tab Bar
        self.chart_tab_bar.tab_selected.connect(self._on_tab_selected)
        self.chart_tab_bar.tab_closed.connect(self._on_tab_closed)
        self.chart_tab_bar.tab_add_requested.connect(self._on_tab_add_requested)

        # Drawing Left Toolbar
        self.drawing_toolbar.tool_selected.connect(self.chart_manager.select_tool)
        self.drawing_toolbar.undo_requested.connect(self._undo_drawing)
        self.drawing_toolbar.redo_requested.connect(self._redo_drawing)
        self.drawing_toolbar.clear_requested.connect(self._clear_drawings)

        # Top Toolbar
        self.toolbar.mode_changed.connect(self._on_mode_changed)
        self.toolbar.symbol_changed.connect(self._on_symbol_changed)
        self.toolbar.symbol_search_requested.connect(self._open_symbol_search_dialog)
        self.toolbar.timeframe_changed.connect(self._on_timeframe_changed)
        self.toolbar.indicators_requested.connect(self._open_indicators_dialog)
        self.toolbar.backtest_requested.connect(self._open_backtest_dialog)
        self.toolbar.mt5_requested.connect(self._open_mt5_dialog)
        self.toolbar.layout_toggle_requested.connect(self._toggle_layout)
        self.toolbar.audio_toggled.connect(self.audio_manager.set_enabled)
        self.toolbar.settings_requested.connect(self._open_settings)
        self.toolbar.theme_changed.connect(self._on_theme_changed)

        # Replay Bar
        self.replay_bar.play_pause_clicked.connect(self._toggle_replay)
        self.replay_bar.step_forward_clicked.connect(self._step_forward)
        self.replay_bar.step_backward_clicked.connect(self._step_backward)
        self.replay_bar.reset_clicked.connect(self._reset_replay)
        self.replay_bar.random_start_clicked.connect(self._random_start)
        self.replay_bar.speed_changed.connect(self._on_speed_changed)
        self.replay_bar.seek_requested.connect(self._on_slider_seek)
        self.replay_bar.jump_to_date_clicked.connect(self._open_jump_to_date_dialog)
        self.replay_bar.go_to_latest_clicked.connect(self._go_to_latest_date)

        # Execution Panel
        self.exec_panel.buy_clicked.connect(self._execute_buy)
        self.exec_panel.sell_clicked.connect(self._execute_sell)
        self.exec_panel.pending_order_clicked.connect(self._execute_pending_order)
        self.exec_panel.close_all_clicked.connect(self._close_all_positions)

        # Positions & History Panels
        self.positions_panel.close_position_requested.connect(self._close_single_position)
        self.positions_panel.partial_close_requested.connect(self._partial_close_position)
        self.positions_panel.move_to_be_requested.connect(self._move_position_to_be)
        self.positions_panel.cancel_pending_order_requested.connect(self._cancel_pending_order)
        self.history_panel.export_requested.connect(self.account_engine.export_trade_history_csv)

        # Chart Ready & Interaction Signals
        self.chart_widget.chart_ready.connect(self._on_chart_ready)
        self.chart_widget.drawing_created_signal.connect(self._handle_drawing_created)
        self.chart_widget.drawing_updated_signal.connect(self._handle_drawing_updated)
        self.chart_widget.drawing_deleted_signal.connect(self._handle_drawing_deleted)
        self.chart_widget.drawing_properties_signal.connect(self._open_drawing_properties_dialog)
        self.chart_widget.position_modified_signal.connect(self._handle_position_modified)
        self.chart_widget.trade_executed_from_drawing_signal.connect(self._handle_execute_trade_from_drawing)
        self.chart_widget.apply_to_order_panel_signal.connect(self._handle_apply_to_order_panel)

        # Event Bus
        self.bus.subscribe(EventType.CANDLE_ADVANCED, self._handle_candle_advanced)
        self.bus.subscribe(EventType.ACCOUNT_UPDATED, self.dashboard.update_account)

    def _open_indicators_dialog(self) -> None:
        """Opens TradingView-style Indicators Manager Dialog."""
        from ui.indicator_dialog import IndicatorDialog
        dlg = IndicatorDialog(
            volume_visible=self.chart_manager.volume_visible,
            active_indicators=self.chart_manager.active_indicators,
            parent=self
        )
        if dlg.exec():
            vol_vis, updated_inds = dlg.get_result()
            self.chart_manager.set_volume_visible(vol_vis)
            self.chart_manager.active_indicators = updated_inds
            vis_df = self.replay_controller.get_visible_candles()
            self.chart_manager.sync_all_indicators(vis_df)
            if hasattr(self, 'chart_manager_htf'):
                self.chart_manager_htf.set_volume_visible(vol_vis)
                self.chart_manager_htf.active_indicators = [x.copy() for x in updated_inds]
                if self.chart_widget_htf.isVisible():
                    self.chart_manager_htf.sync_all_indicators(vis_df)

    def _open_drawing_properties_dialog(self, drawing_id: str) -> None:
        """Opens comprehensive Drawing Properties dialog for editing outline, fill, text, etc."""
        drawing = self.drawing_store.get_drawing(drawing_id)
        if not drawing:
            return
        dlg = DrawingPropertiesDialog(drawing.to_dict(), self)
        if dlg.exec():
            updated_dict = dlg.get_updated_drawing_dict()
            updated_drawing = Drawing.from_dict(updated_dict)
            self.drawing_store.update_drawing(updated_drawing)
            self.chart_manager.sync_drawings(self.drawing_store.get_all_drawings())

    def _open_jump_to_date_dialog(self) -> None:
        """Opens dialog to jump/rewind replay back to a specific historical date."""
        from ui.jump_date_dialog import JumpToDateDialog
        curr_dt = self.replay_controller.state.current_datetime
        latest_candle = self.replay_controller._df.iloc[-1].to_dict() if not self.replay_controller._df.empty else {}
        latest_dt = latest_candle.get("datetime")
        dlg = JumpToDateDialog(current_dt=curr_dt, latest_dt=latest_dt, parent=self)
        if dlg.exec():
            target_ts = dlg.get_selected_timestamp()
            self.replay_timer.stop()
            self.replay_bar.set_playing(False)
            self.replay_controller.jump_to_timestamp(target_ts)
            self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
            self._update_all_views()

    def _go_to_latest_date(self) -> None:
        """Fast-forwards replay to the current latest available date."""
        if not self.replay_controller._df.empty:
            self.replay_timer.stop()
            self.replay_bar.set_playing(False)
            latest_idx = len(self.replay_controller._df) - 1
            self.replay_controller.jump_to_index(latest_idx)
            self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
            self._update_all_views()

    def load_initial_data(self) -> None:
        sym = self.config.get("market", {}).get("default_symbol", "XAUUSD")
        tf = self.config.get("market", {}).get("default_timeframe", "5m")
        if len(self.chart_tab_bar.tabs) == 0:
            self.chart_tab_bar.add_tab(sym, tf, mode="replay")
        else:
            self.chart_tab_bar.update_tab_label(0, sym, tf, mode="replay")
        self._load_asset_data(sym, tf)

    def _load_asset_data(self, symbol: str, timeframe: str = "5m", preserve_timestamp: Optional[int] = None) -> None:
        """Loads historical dataset with in-memory caching for instantaneous switching."""
        cache_key = (symbol, "1m")
        if cache_key in self._data_cache:
            df_base = self._data_cache[cache_key]
            self.replay_controller.load_data(df_base, symbol=symbol, timeframe=timeframe)
            if preserve_timestamp is not None:
                self.replay_controller.jump_to_timestamp(preserve_timestamp)
            else:
                latest_idx = len(self.replay_controller._df) - 1
                self.replay_controller.jump_to_index(latest_idx)
            return

        hist_1m = Path(f"data/historical/{symbol}_1m.csv")
        hist_tf = Path(f"data/historical/{symbol}_{timeframe}.csv")

        if hist_1m.exists():
            try:
                df_base = DataLoader.load_csv(hist_1m)
                self._data_cache[cache_key] = df_base
                self.replay_controller.load_data(df_base, symbol=symbol, timeframe=timeframe)
                if preserve_timestamp is not None:
                    self.replay_controller.jump_to_timestamp(preserve_timestamp)
                else:
                    latest_idx = len(self.replay_controller._df) - 1
                    self.replay_controller.jump_to_index(latest_idx)
                return
            except Exception as e:
                logger.error(f"Error loading historical 1m base for {symbol}: {e}")

        if hist_tf.exists():
            try:
                df = DataLoader.load_csv(hist_tf)
                self.replay_controller.load_data(df, symbol=symbol, timeframe=timeframe)
                if preserve_timestamp is not None:
                    self.replay_controller.jump_to_timestamp(preserve_timestamp)
                else:
                    latest_idx = len(df) - 1
                    self.replay_controller.jump_to_index(latest_idx)
                return
            except Exception as e:
                logger.error(f"Error loading historical {timeframe} for {symbol}: {e}")

        # Fallback to sample or synthetic data
        df_synth = SyntheticDataGenerator.generate(symbol, num_candles=1000, timeframe=timeframe, seed=42)
        self.replay_controller.load_data(df_synth, symbol=symbol, timeframe=timeframe, start_index=len(df_synth) - 1)

    def _on_chart_ready(self) -> None:
        """Called once the JavaScript chart layer has initialized."""
        self._apply_theme(self.current_theme)
        visible_candles = self.replay_controller.get_visible_candles()
        self.chart_manager.load_dataset(visible_candles)
        self._update_all_views()

    def _on_theme_changed(self, theme_name: str) -> None:
        self._apply_theme(theme_name)

    def _apply_theme(self, theme_name: str) -> None:
        """Applies dynamic theme stylesheets to PyQt6 and Lightweight Charts."""
        self.current_theme = theme_name
        self.toolbar.set_active_theme(theme_name)
        qss = ThemeManager.generate_qss(theme_name)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)

        theme_data = ThemeManager.get_theme_data(theme_name)
        self.chart_widget.set_theme(theme_name, theme_data)
        if hasattr(self, "chart_widget_htf"):
            self.chart_widget_htf.set_theme(theme_name, theme_data)

    def _toggle_replay(self) -> None:
        self.replay_controller.toggle_play_pause()
        is_playing = self.replay_controller.is_playing
        self.replay_bar.set_playing(is_playing)
        if is_playing:
            interval = self.replay_controller.get_timer_interval_ms()
            self.replay_timer.start(interval)
        else:
            self.replay_timer.stop()
            self._update_all_views()

    def _on_replay_timer_tick(self) -> None:
        success = self.replay_controller.step_forward()
        if not success or not self.replay_controller.is_playing:
            self.replay_timer.stop()
            self.replay_bar.set_playing(False)
            self._update_all_views()

    def _step_forward(self) -> None:
        self.replay_controller.step_forward()
        self._update_all_views()

    def _step_backward(self) -> None:
        self.replay_controller.step_backward()
        self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
        self._update_all_views()

    def _reset_replay(self) -> None:
        self.replay_timer.stop()
        self.replay_bar.set_playing(False)
        self.replay_controller.reset()
        self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
        self._update_all_views()

    def _random_start(self) -> None:
        self.replay_timer.stop()
        self.replay_bar.set_playing(False)
        self.replay_controller.random_start()
        self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
        self._update_all_views()

    def _on_speed_changed(self, speed: float) -> None:
        self.replay_controller.set_speed(speed)
        if self.replay_controller.is_playing:
            self.replay_timer.setInterval(self.replay_controller.get_timer_interval_ms())

    def _on_slider_seek(self, idx: int) -> None:
        self.replay_controller.jump_to_index(idx)
        self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
        self._update_all_views()

    def _on_symbol_changed(self, symbol: str) -> None:
        tf = self.replay_controller.state.timeframe
        self.chart_widget.set_symbol(symbol)
        if hasattr(self, "chart_widget_htf"):
            self.chart_widget_htf.set_symbol(symbol)

        mode_str = "live" if (self.live_worker and self.live_worker.isRunning()) else "replay"
        self.chart_tab_bar.update_tab_label(self.current_tab_index, symbol, tf, mode_str)

        # 1. Load dataset for newly selected asset
        if mt5_connector.is_connected:
            live_df = LiveDataLoader.fetch_latest_candles(symbol, timeframe=tf, limit=2000)
            if live_df is not None and not live_df.empty:
                self.replay_controller.load_data(live_df, symbol=symbol, timeframe=tf, start_index=len(live_df) - 1)
            else:
                self._load_asset_data(symbol=symbol, timeframe=tf, preserve_timestamp=None)
        else:
            self._load_asset_data(symbol=symbol, timeframe=tf, preserve_timestamp=None)

        # 2. If live mode is active, restart live worker
        if self.live_worker and self.live_worker.isRunning():
            self.live_worker.stop()
            self.live_worker = LiveFeedWorker(symbol=symbol, timeframe=tf, interval_ms=1000)
            self.live_worker.candle_received.connect(self._on_live_candle_received)
            self.live_worker.start()

        self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
        self._update_all_views()

    def _on_timeframe_changed(self, tf: str) -> None:
        sym = self.replay_controller.state.symbol
        mode_str = "live" if (self.live_worker and self.live_worker.isRunning()) else "replay"
        self.chart_tab_bar.update_tab_label(self.current_tab_index, sym, tf, mode_str)

        if mt5_connector.is_connected:
            live_df = LiveDataLoader.fetch_latest_candles(sym, timeframe=tf, limit=2000)
            if live_df is not None and not live_df.empty:
                self.replay_controller.load_data(live_df, symbol=sym, timeframe=tf, start_index=len(live_df) - 1)
                self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
                self._update_all_views()
        else:
            success = self.replay_controller.set_timeframe(tf)
            if success:
                self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
                self._update_all_views()

        if self.live_worker and self.live_worker.isRunning():
            self.live_worker.timeframe = tf

    def _on_mode_changed(self, mode: str) -> None:
        """Toggles between historical replay mode and live streaming feed."""
        sym = self.replay_controller.state.symbol
        tf = self.replay_controller.state.timeframe
        self.chart_tab_bar.update_tab_label(self.current_tab_index, sym, tf, mode)

        if mode == "live":
            # Stop replay playback
            self.replay_timer.stop()
            self.replay_bar.set_playing(False)
            self.replay_bar.setEnabled(False)

            if self.live_worker:
                self.live_worker.stop()

            # Fill the gap: fetch latest candles up to the current moment and load
            if mt5_connector.is_connected:
                live_df = LiveDataLoader.fetch_latest_candles(sym, timeframe=tf, limit=2000)
                if live_df is not None and not live_df.empty:
                    self.replay_controller.load_data(live_df, symbol=sym, timeframe=tf, start_index=len(live_df) - 1)
                    self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
                    self._update_all_views()
            else:
                live_df = LiveDataLoader.fetch_latest_candles(sym, timeframe=tf)
                if live_df is not None and not live_df.empty:
                    merged = LiveDataLoader.merge_with_live(self.replay_controller._df, live_df)
                    self.replay_controller.load_data(merged, symbol=sym, timeframe=tf, start_index=len(merged) - 1)
                    self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
                    self._update_all_views()
                else:
                    self._go_to_latest_date()

            self.live_worker = LiveFeedWorker(symbol=sym, timeframe=tf, interval_ms=1000)
            self.live_worker.candle_received.connect(self._on_live_candle_received)
            self.live_worker.start()
            logger.info(f"Switched to LIVE Mode ({sym} - {tf})")
        else:
            if self.live_worker:
                self.live_worker.stop()
                self.live_worker = None
            self.replay_bar.setEnabled(True)
            logger.info("Switched to REPLAY Mode")

    def _open_symbol_search_dialog(self) -> None:
        """Opens TradingView-style Search & Filter Dialog for selecting assets."""
        curr_sym = self.replay_controller.state.symbol
        dlg = SymbolSearchDialog(current_symbol=curr_sym, parent=self)
        if dlg.exec():
            selected = dlg.get_selected_symbol()
            if selected and selected != curr_sym:
                self.toolbar.set_active_symbol(selected)
                self._on_symbol_changed(selected)

    def _save_current_tab_state(self) -> None:
        """Persists the runtime state of the currently active chart tab."""
        tab_info = self.chart_tab_bar.get_tab(self.current_tab_index)
        if tab_info:
            tab_info.symbol = self.replay_controller.state.symbol
            tab_info.timeframe = self.replay_controller.state.timeframe
            tab_info.mode = "live" if (self.live_worker and self.live_worker.isRunning()) else "replay"
            tab_info.replay_index = self.replay_controller.current_index
            tab_info.drawings = self.drawing_store.serialize()
            tab_info.indicators = [x.copy() for x in self.chart_manager.active_indicators]

    def _on_tab_selected(self, index: int) -> None:
        """Switches active chart tab, restoring its symbol, timeframe, drawings, and replay state."""
        if index == self.current_tab_index:
            return

        # 1. Save state of current tab
        self._save_current_tab_state()

        # 2. Update index
        self.current_tab_index = index
        target_tab = self.chart_tab_bar.get_tab(index)
        if not target_tab:
            return

        # 3. Restore toolbar controls
        self.toolbar.set_active_symbol(target_tab.symbol)
        self.toolbar.set_active_timeframe(target_tab.timeframe)
        self.toolbar.set_active_mode(target_tab.mode)

        # 4. Restore drawings
        self.drawing_store.deserialize(target_tab.drawings)
        self.chart_manager.sync_drawings(self.drawing_store.get_all_drawings())

        # 5. Restore indicators
        self.chart_manager.active_indicators = [x.copy() for x in target_tab.indicators]

        # 6. Load data for tab's symbol and timeframe
        self.chart_widget.set_symbol(target_tab.symbol)
        self._load_asset_data(target_tab.symbol, target_tab.timeframe, preserve_timestamp=None)

        # 7. Restore replay position
        if target_tab.replay_index is not None and 0 <= target_tab.replay_index < len(self.replay_controller._df):
            self.replay_controller.jump_to_index(target_tab.replay_index)
        else:
            latest_idx = max(0, len(self.replay_controller._df) - 1)
            self.replay_controller.jump_to_index(latest_idx)

        vis_candles = self.replay_controller.get_visible_candles()
        self.chart_manager.load_dataset(vis_candles)
        self.chart_manager.sync_all_indicators(vis_candles)

        # 8. Set live mode vs replay mode
        if target_tab.mode == "live":
            self._on_mode_changed("live")
        else:
            if self.live_worker:
                self.live_worker.stop()
                self.live_worker = None
            self.replay_bar.setEnabled(True)

        self._update_all_views()

    def _on_tab_add_requested(self) -> None:
        """Opens a new chart tab up to a maximum of 4 tabs."""
        if len(self.chart_tab_bar.tabs) >= self.chart_tab_bar.max_tabs:
            return

        # Determine a reasonable default symbol for the new tab
        current_sym = self.replay_controller.state.symbol
        default_pairs = ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "ETHUSD", "XAUUSD"]
        new_sym = "EURUSD"
        for p in default_pairs:
            if p != current_sym and not any(t.symbol == p for t in self.chart_tab_bar.tabs):
                new_sym = p
                break

        new_idx = self.chart_tab_bar.add_tab(new_sym, "15m", mode="replay")
        if new_idx is not None and new_idx >= 0:
            self._on_tab_selected(new_idx)

    def _on_tab_closed(self, index: int) -> None:
        """Closes a chart tab and switches to the nearest available tab."""
        if len(self.chart_tab_bar.tabs) <= 1:
            return

        # If closing the currently selected tab, select adjacent tab first
        if index == self.current_tab_index:
            new_index = max(0, index - 1)
            self.chart_tab_bar.remove_tab(index)
            self.current_tab_index = new_index
            target_tab = self.chart_tab_bar.get_tab(new_index)
            if target_tab:
                self.toolbar.set_active_symbol(target_tab.symbol)
                self.toolbar.set_active_timeframe(target_tab.timeframe)
                self.toolbar.set_active_mode(target_tab.mode)
                self.drawing_store.deserialize(target_tab.drawings)
                self.chart_manager.sync_drawings(self.drawing_store.get_all_drawings())
                self.chart_manager.active_indicators = [x.copy() for x in target_tab.indicators]
                self.chart_widget.set_symbol(target_tab.symbol)
                self._load_asset_data(target_tab.symbol, target_tab.timeframe)
                if target_tab.replay_index is not None and 0 <= target_tab.replay_index < len(self.replay_controller._df):
                    self.replay_controller.jump_to_index(target_tab.replay_index)
                else:
                    latest_idx = max(0, len(self.replay_controller._df) - 1)
                    self.replay_controller.jump_to_index(latest_idx)
                vis_candles = self.replay_controller.get_visible_candles()
                self.chart_manager.load_dataset(vis_candles)
                self.chart_manager.sync_all_indicators(vis_candles)
                self._update_all_views()
        else:
            if index < self.current_tab_index:
                self.current_tab_index -= 1
            self.chart_tab_bar.remove_tab(index)


    def _close_current_tab(self) -> None:
        """Keyboard shortcut (Ctrl+W) to close the active tab."""
        if len(self.chart_tab_bar.tabs) > 1:
            self._on_tab_closed(self.current_tab_index)

    def _switch_to_tab_index(self, idx: int) -> None:
        """Keyboard shortcut (Ctrl+1..4) to directly switch to tab by index."""
        if 0 <= idx < len(self.chart_tab_bar.tabs):
            self.chart_tab_bar.select_tab(idx)

    def _on_live_candle_received(self, candle: Dict[str, Any]) -> None:
        """Handles live streaming tick / candle update."""
        self.chart_manager.advance_candle(candle)
        self.account_engine.process_candle(candle)
        self._update_fast_views(candle)
        if not self._heavy_update_timer.isActive():
            self._heavy_update_timer.start(120)

    def _open_backtest_dialog(self) -> None:
        """Opens the Quantitative Automated Strategy Backtester Dialog."""
        df = self.replay_controller._df
        sym = self.replay_controller.state.symbol
        tf = self.replay_controller.state.timeframe
        dlg = BacktestDialog(current_df=df, symbol=sym, timeframe=tf, parent=self)
        dlg.exec()

    def _open_mt5_dialog(self) -> None:
        """Opens the MetaTrader 5 / FOREX.com connection configuration dialog."""
        dlg = MT5Dialog(self)
        dlg.exec()

    def _sync_mt5_history(self) -> None:
        """Downloads full spot history from MT5 and reloads the active asset dataset."""
        if not mt5_connector.is_connected:
            ok, msg = mt5_connector.connect(timeout=3000)
            if not ok:
                QMessageBox.warning(self, "MT5 Not Connected", f"Could not connect to MT5:\n{msg}\n\nPlease ensure your MT5 terminal is open.")
                return

        res = mt5_connector.download_historical_dataset(count=5000)
        if res:
            total_bars = sum(res.values())
            # Clear in-memory data cache to force reload of fresh MT5 CSVs
            self._data_cache.clear()
            sym = self.replay_controller.state.symbol
            tf = self.replay_controller.state.timeframe
            self._load_asset_data(symbol=sym, timeframe=tf, preserve_timestamp=None)
            self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
            self._update_all_views()
            QMessageBox.information(
                self,
                "Broker Data Synced",
                f"Successfully synced {len(res)} timeframe datasets ({total_bars:,} total candles) directly from MT5!\n\n"
                "Both Replay Mode and Live Mode are now 100% aligned to your broker's Spot prices.",
            )
        else:
            QMessageBox.warning(self, "Sync Incomplete", "No candles could be downloaded. Check Market Watch symbols in MT5.")

    def _handle_candle_advanced(self, event_data: Any) -> None:
        candle = event_data.candle
        # 1. Update chart incrementally (O(1) 60fps)
        self.chart_manager.advance_candle(candle)

        # 2. Process active trades (SL/TP)
        self.account_engine.process_candle(candle)

        # 3. High-speed fast view updates (Slider + Live Price)
        self._update_fast_views(candle)

        # 4. Debounced heavy view updates for table metrics
        if not self._heavy_update_timer.isActive():
            self._heavy_update_timer.start(120)

    def _update_fast_views(self, candle: Dict[str, Any]) -> None:
        """Lightweight O(1) view updates called on every tick during replay."""
        curr_price = float(candle.get("close", 2000.0))
        ts_str = str(candle.get("datetime", candle.get("timestamp", "--")))

        self.replay_bar.update_progress(
            self.replay_controller.current_index,
            self.replay_controller.total_candles,
            ts_str,
        )

        sym = self.replay_controller.state.symbol
        point_val = self.account_engine.get_point_value(sym)
        self.exec_panel.update_market_price(
            symbol=sym,
            price=curr_price,
            spread=self.account_engine.spread,
            balance=self.account_engine.balance,
            point_val=point_val,
        )

    def _update_heavy_views(self) -> None:
        """Recalculates heavy trade statistics, table widgets, and journal views."""
        open_pos_list = list(self.account_engine.positions.values())
        pending_orders_list = list(self.account_engine.pending_orders.values())
        candle = self.replay_controller.get_current_candle()
        curr_p = float(candle["close"]) if candle else None

        self.positions_panel.update_positions(open_pos_list, pending_orders_list, current_price=curr_p)
        tab_label = f"Positions ({len(open_pos_list)})"
        if pending_orders_list:
            tab_label = f"Positions ({len(open_pos_list)}) | Orders ({len(pending_orders_list)})"
        self.tabs.setTabText(0, tab_label)

        self.history_panel.update_history(self.account_engine.trade_history)
        self.journal_panel.update_trades(self.account_engine.trade_history)

        stats = StatisticsCalculator.calculate(
            self.account_engine.trade_history, self.account_engine.initial_balance
        )
        self.analytics_panel.update_statistics(stats)

        self.chart_manager.update_positions_and_trades(
            open_positions=open_pos_list,
            closed_trades=self.account_engine.trade_history,
        )

    def _update_all_views(self) -> None:
        """Executes full immediate update of all views (fast + heavy)."""
        candle = self.replay_controller.get_current_candle()
        if candle:
            self._update_fast_views(candle)
        self._update_heavy_views()

    def _execute_buy(self, lot: float, sl: float, tp: float) -> None:
        candle = self.replay_controller.get_current_candle()
        if not candle:
            return
        price = float(candle["close"])
        ts = int(candle["timestamp"])
        dt = candle.get("datetime")
        sym = self.replay_controller.state.symbol

        success, pos, msg = self.account_engine.open_market_order(
            direction=Direction.BUY,
            symbol=sym,
            lot_size=lot,
            current_price=price,
            stop_loss=sl if sl > 0 else None,
            take_profit=tp if tp > 0 else None,
            timestamp=ts,
            dt=dt,
        )
        if not success:
            QMessageBox.warning(self, "Order Rejected", msg)
        else:
            self._update_all_views()

    def _execute_sell(self, lot: float, sl: float, tp: float) -> None:
        candle = self.replay_controller.get_current_candle()
        if not candle:
            return
        price = float(candle["close"])
        ts = int(candle["timestamp"])
        dt = candle.get("datetime")
        sym = self.replay_controller.state.symbol

        success, pos, msg = self.account_engine.open_market_order(
            direction=Direction.SELL,
            symbol=sym,
            lot_size=lot,
            current_price=price,
            stop_loss=sl if sl > 0 else None,
            take_profit=tp if tp > 0 else None,
            timestamp=ts,
            dt=dt,
        )
        if not success:
            QMessageBox.warning(self, "Order Rejected", msg)
        else:
            self._update_all_views()

    def _execute_pending_order(self, order_type_str: str, lot: float, entry: float, sl: float, tp: float) -> None:
        candle = self.replay_controller.get_current_candle()
        if not candle:
            return
        curr_price = float(candle["close"])
        ts = int(candle["timestamp"])
        dt = candle.get("datetime")
        sym = self.replay_controller.state.symbol

        # Map to OrderType
        ot_map = {
            "BUY_LIMIT": OrderType.BUY_LIMIT,
            "BUY_STOP": OrderType.BUY_STOP,
            "SELL_LIMIT": OrderType.SELL_LIMIT,
            "SELL_STOP": OrderType.SELL_STOP,
        }
        order_type = ot_map.get(order_type_str, OrderType.BUY_LIMIT)

        success, ord_obj, msg = self.account_engine.place_pending_order(
            order_type=order_type,
            symbol=sym,
            lot_size=lot,
            target_price=entry,
            current_price=curr_price,
            stop_loss=sl if sl > 0 else None,
            take_profit=tp if tp > 0 else None,
            timestamp=ts,
            dt=dt,
        )
        if not success:
            QMessageBox.warning(self, "Order Rejected", msg)
        else:
            self._update_all_views()

    def _close_single_position(self, pos_id: str) -> None:
        candle = self.replay_controller.get_current_candle()
        if not candle:
            return
        price = float(candle["close"])
        ts = int(candle["timestamp"])
        dt = candle.get("datetime")
        self.account_engine.close_position(pos_id, current_price=price, timestamp=ts, dt=dt)
        self._update_all_views()

    def _partial_close_position(self, pos_id: str, percentage: float = 0.5) -> None:
        candle = self.replay_controller.get_current_candle()
        if not candle:
            return
        price = float(candle["close"])
        ts = int(candle["timestamp"])
        dt = candle.get("datetime")
        self.account_engine.close_partial_position(
            position_id=pos_id,
            percentage=percentage,
            current_price=price,
            timestamp=ts,
            dt=dt,
        )
        self._update_all_views()

    def _move_position_to_be(self, pos_id: str) -> None:
        self.account_engine.move_sl_to_break_even(pos_id)
        self._update_all_views()

    def _cancel_pending_order(self, order_id: str) -> None:
        self.account_engine.cancel_pending_order(order_id)
        self._update_all_views()

    def _close_all_positions(self) -> None:
        candle = self.replay_controller.get_current_candle()
        if not candle:
            return
        price = float(candle["close"])
        ts = int(candle["timestamp"])
        dt = candle.get("datetime")
        self.account_engine.close_all_positions(current_price=price, timestamp=ts, dt=dt)
        self._update_all_views()

    def _toggle_layout(self, mode: str) -> None:
        """Toggles between single-chart view and dual-chart multi-timeframe view."""
        if mode == "dual":
            self.chart_widget_htf.setVisible(True)
            sym = self.replay_controller.state.symbol
            htf_path = Path(f"data/historical/{sym}_1h.csv")
            if htf_path.exists():
                try:
                    df_htf = DataLoader.load_csv(htf_path)
                    curr_ts = self.replay_controller.state.current_timestamp
                    if curr_ts:
                        df_htf_vis = df_htf[df_htf["timestamp"] <= curr_ts]
                    else:
                        df_htf_vis = df_htf
                    self.chart_manager_htf.load_dataset(df_htf_vis)
                except Exception as e:
                    logger.error(f"Error loading HTF data for dual view: {e}")
        else:
            self.chart_widget_htf.setVisible(False)

    def _handle_drawing_created(self, drawing_data: Any) -> None:
        try:
            if isinstance(drawing_data, dict):
                drawing = Drawing.from_dict(drawing_data)
            elif isinstance(drawing_data, Drawing):
                drawing = drawing_data
            else:
                return
            self.drawing_store.add_drawing(drawing, emit_event=False)

            # Auto-sync SL/TP into Execution Panel if Long/Short Position tool
            dtype = drawing.type.value if hasattr(drawing.type, "value") else str(drawing.type)
            if dtype in ("LONG_POSITION", "SHORT_POSITION") and len(drawing.points) >= 3:
                entry = drawing.points[0].price
                sl = drawing.points[1].price
                tp = drawing.points[2].price

                candle = self.replay_controller.get_current_candle()
                curr_price = float(candle["close"]) if candle else entry
                is_long = (dtype == "LONG_POSITION")

                if abs(entry - curr_price) <= 0.05:
                    ot = "Market Order"
                elif is_long:
                    ot = "Buy Limit" if entry < curr_price else "Buy Stop"
                else:
                    ot = "Sell Limit" if entry > curr_price else "Sell Stop"

                self.exec_panel.set_order_parameters(entry=entry, sl=sl, tp=tp, order_type=ot)
        except Exception as e:
            logger.error(f"Error handling drawing created: {e}")

    def _handle_drawing_updated(self, drawing_data: Any) -> None:
        try:
            if isinstance(drawing_data, dict):
                drawing = Drawing.from_dict(drawing_data)
            elif isinstance(drawing_data, Drawing):
                drawing = drawing_data
            else:
                return
            self.drawing_store.update_drawing(drawing, emit_event=False)

            # Auto-sync SL/TP into Execution Panel if Long/Short Position tool
            dtype = drawing.type.value if hasattr(drawing.type, "value") else str(drawing.type)
            if dtype in ("LONG_POSITION", "SHORT_POSITION") and len(drawing.points) >= 3:
                entry = drawing.points[0].price
                sl = drawing.points[1].price
                tp = drawing.points[2].price

                candle = self.replay_controller.get_current_candle()
                curr_price = float(candle["close"]) if candle else entry
                is_long = (dtype == "LONG_POSITION")

                if abs(entry - curr_price) <= 0.05:
                    ot = "Market Order"
                elif is_long:
                    ot = "Buy Limit" if entry < curr_price else "Buy Stop"
                else:
                    ot = "Sell Limit" if entry > curr_price else "Sell Stop"

                self.exec_panel.set_order_parameters(entry=entry, sl=sl, tp=tp, order_type=ot)
        except Exception as e:
            logger.error(f"Error updating drawing: {e}")

    def _handle_drawing_deleted(self, drawing_id_or_data: Any) -> None:
        try:
            if isinstance(drawing_id_or_data, dict):
                drawing_id = str(drawing_id_or_data.get("id", ""))
            else:
                drawing_id = str(drawing_id_or_data)
            if drawing_id:
                self.drawing_store.delete_drawing(drawing_id, emit_event=False)
        except Exception as e:
            logger.error(f"Error deleting drawing: {e}")

    def _handle_execute_trade_from_drawing(self, data: dict) -> None:
        try:
            order_type_str = data.get("order_type", "")
            action_str = data.get("action", "")

            if order_type_str == "MOVE_BE" or action_str == "MOVE_BE":
                # Move all active positions on current symbol to break-even
                sym = self.replay_controller.state.symbol
                for pid, pos in list(self.account_engine.positions.items()):
                    if pos.symbol == sym:
                        self.account_engine.move_sl_to_break_even(pid)
                self._update_all_views()
                return

            direction_str = data.get("direction", "BUY")
            entry = float(data.get("entry", 0.0))
            sl = float(data.get("sl", 0.0))
            tp = float(data.get("tp", 0.0))
            lot = self.exec_panel.spin_lot.value()

            # Synchronize protective orders and entry to the execution panel
            self.exec_panel.set_order_parameters(entry=entry, sl=sl, tp=tp, order_type=order_type_str)

            if order_type_str in ("BUY_LIMIT", "BUY_STOP", "SELL_LIMIT", "SELL_STOP"):
                self._execute_pending_order(order_type_str, lot, entry, sl, tp)
            elif direction_str == "BUY":
                self._execute_buy(lot, sl, tp)
            else:
                self._execute_sell(lot, sl, tp)
        except Exception as e:
            logger.error(f"Error executing trade from drawing: {e}")

    def _handle_apply_to_order_panel(self, data: dict) -> None:
        try:
            entry = float(data.get("entry", 0.0))
            sl = float(data.get("sl", 0.0))
            tp = float(data.get("tp", 0.0))
            order_type_str = data.get("order_type", "")
            self.exec_panel.set_order_parameters(entry=entry, sl=sl, tp=tp, order_type=order_type_str)
        except Exception as e:
            logger.error(f"Error applying drawing levels to order panel: {e}")

    def _handle_position_modified(self, data: dict) -> None:
        pos_id = data.get("position_id")
        sl = data.get("sl")
        tp = data.get("tp")
        if pos_id and pos_id in self.account_engine.positions:
            pos = self.account_engine.positions[pos_id]
            if sl is not None:
                pos.stop_loss = float(sl) if sl > 0 else None
            if tp is not None:
                pos.take_profit = float(tp) if tp > 0 else None
            self._update_all_views()

    def _undo_drawing(self) -> None:
        self.drawing_store.undo()
        self.chart_manager.sync_drawings(self.drawing_store.get_all_drawings())

    def _redo_drawing(self) -> None:
        self.drawing_store.redo()
        self.chart_manager.sync_drawings(self.drawing_store.get_all_drawings())

    def _clear_drawings(self) -> None:
        self.drawing_store.clear()
        self.chart_manager.sync_drawings([])

    def _open_settings(self) -> None:
        curr = {
            "theme": self.current_theme,
            "balance": self.account_engine.balance,
            "leverage": self.account_engine.leverage,
            "commission": self.account_engine.commission_per_lot,
            "spread": self.account_engine.spread,
            "slippage": self.account_engine.slippage,
            "intrabar_mode": self.account_engine.intrabar_mode.value,
        }
        dlg = SettingsDialog(curr, self)
        if dlg.exec():
            res = dlg.get_settings()
            new_theme = res.get("theme", self.current_theme)
            if new_theme != self.current_theme:
                self._apply_theme(new_theme)
            self.account_engine.leverage = int(res["leverage"])
            self.account_engine.commission_per_lot = float(res["commission"])
            self.account_engine.spread = float(res["spread"])
            self.account_engine.slippage = float(res["slippage"])
            self.account_engine.intrabar_mode = IntrabarExecutionMode(res["intrabar_mode"])
            self._update_all_views()

    def _menu_open_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV Market Data", "", "CSV Files (*.csv *.txt)"
        )
        if file_path:
            try:
                df = DataLoader.load_csv(file_path)
                sym = Path(file_path).stem.split("_")[0] or "CUSTOM"
                self.replay_controller.load_data(df, symbol=sym, timeframe="5m", start_index=50)
                self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
                self._update_all_views()
                QMessageBox.information(self, "Data Loaded", f"Successfully loaded {len(df)} candles for {sym}.")
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load CSV:\n{e}")

    def _menu_new_workspace(self) -> None:
        if QMessageBox.question(
            self, "New Workspace", "Reset current workspace, balance, and drawings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.account_engine.reset(10000.0)
            self.drawing_store.clear()
            self.chart_manager.sync_drawings([])
            self.load_initial_data()
            self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
            self._update_all_views()

    def _menu_save_workspace(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Workspace", "workspace.json", "JSON Files (*.json)"
        )
        if file_path:
            schema = WorkspaceSchema(
                symbol=self.replay_controller.state.symbol,
                timeframe=self.replay_controller.state.timeframe,
                replay_index=self.replay_controller.current_index,
                balance=self.account_engine.balance,
                drawings=self.drawing_store.serialize(),
                alerts=self.notification_manager.alert_mgr.serialize(),
            )
            saved = self.workspace_manager.save_workspace(schema, file_path)
            if saved:
                QMessageBox.information(self, "Saved", f"Workspace saved to {Path(file_path).name}")

    def _menu_open_workspace(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Workspace", "", "JSON Files (*.json)"
        )
        if file_path:
            schema = self.workspace_manager.load_workspace(file_path)
            if schema:
                self.account_engine.reset(schema.balance)
                self.drawing_store.deserialize(schema.drawings)
                self.notification_manager.alert_mgr.deserialize(schema.alerts)
                self.chart_manager.sync_drawings(self.drawing_store.get_all_drawings())
                self.replay_controller.jump_to_index(schema.replay_index)
                self.chart_manager.load_dataset(self.replay_controller.get_visible_candles())
                self._update_all_views()
                QMessageBox.information(self, "Loaded", f"Workspace restored from {Path(file_path).name}")

    def _menu_export_history(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Trade History", "trade_history.csv", "CSV Files (*.csv)"
        )
        if file_path:
            self.account_engine.export_trade_history_csv(file_path)
            QMessageBox.information(self, "Exported", f"Trade history exported to {Path(file_path).name}")

    def _show_shortcuts_dialog(self) -> None:
        msg = (
            "<b>Keyboard Shortcuts:</b><br><br>"
            "<b>Space:</b> Play / Pause Replay<br>"
            "<b>Right Arrow:</b> Next Candle (Step Forward)<br>"
            "<b>Left Arrow:</b> Previous Candle (Step Backward)<br>"
            "<b>B:</b> Market Buy<br>"
            "<b>S:</b> Market Sell<br>"
            "<b>C:</b> Close Active Position(s)<br>"
            "<b>T:</b> Trendline Tool<br>"
            "<b>R:</b> Rectangle Tool<br>"
            "<b>F:</b> Fibonacci Retracement Tool<br>"
            "<b>L:</b> Long Position Setup Tool<br>"
            "<b>Shift+L:</b> Short Position Setup Tool<br>"
            "<b>Esc:</b> Cursor / Cancel Tool<br>"
            "<b>Ctrl+Z:</b> Undo Drawing<br>"
            "<b>Ctrl+Y / Ctrl+Shift+Z:</b> Redo Drawing<br>"
            "<b>Ctrl+S:</b> Save Workspace<br>"
        )
        QMessageBox.information(self, "Keyboard Shortcuts", msg)

    def _show_about_dialog(self) -> None:
        msg = (
            "<h3>Trading Replay Lab</h3>"
            "<p><b>Version 1.0.0</b></p>"
            "<p>A professional desktop trading analysis and manual backtesting workstation.</p>"
            "<p>Features candle-by-candle replay with strict hidden-future enforcement, "
            "simulated broker execution, interactive chart drawings, analytics, and journal.</p>"
        )
        QMessageBox.about(self, "About", msg)
