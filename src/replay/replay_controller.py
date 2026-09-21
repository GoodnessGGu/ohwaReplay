from datetime import datetime, timezone
import random
from typing import Any, Callable, Dict, List, Optional, Union
import pandas as pd
import numpy as np

from src.events.event_bus import EventBus, event_bus
from src.replay.replay_events import CandleAdvancedEvent, ReplayStateChangedEvent
from src.replay.replay_state import ReplayState
from src.utils.constants import EventType, ReplayStateEnum, TIMEFRAMES
from src.utils.logger import logger
from src.data.resampler import TimeframeResampler


class ReplayController:
    """
    Manages the chronological replay of market OHLCV data.
    Enforces the HIDDEN FUTURE principle: no future candles can be queried.
    """

    def __init__(
        self,
        event_bus_instance: Optional[EventBus] = None,
        base_timer_interval_ms: int = 1000,
    ):
        self.bus = event_bus_instance or event_bus
        self.base_timer_interval_ms = base_timer_interval_ms

        self._base_df: pd.DataFrame = pd.DataFrame()  # Original resolution data (e.g. 1m or loaded)
        self._df: pd.DataFrame = pd.DataFrame()       # Active timeframe data
        self.state: ReplayState = ReplayState()
        self._on_tick_callbacks: list[Callable[[], None]] = []

    @property
    def is_playing(self) -> bool:
        return self.state.status == ReplayStateEnum.PLAYING

    @property
    def current_index(self) -> int:
        return self.state.current_index

    @current_index.setter
    def current_index(self, val: int) -> None:
        self.state.current_index = val

    @property
    def total_candles(self) -> int:
        return self.state.total_candles

    @total_candles.setter
    def total_candles(self, val: int) -> None:
        self.state.total_candles = val

    def load_data(
        self,
        df: pd.DataFrame,
        symbol: str = "XAUUSD",
        timeframe: str = "5m",
        start_index: Optional[int] = None,
    ) -> None:
        """Loads a dataset into the replay controller and initializes state."""
        if df.empty:
            logger.warning("Attempted to load empty DataFrame into ReplayController.")
            return

        self._base_df = df.copy().reset_index(drop=True)
        if not self._base_df.empty and "timestamp" in self._base_df.columns:
            self._base_timestamps = self._base_df["timestamp"].values
        else:
            self._base_timestamps = np.array([])
        self.state.symbol = symbol
        self.state.timeframe = timeframe

        is_already_target_tf = False
        if len(self._base_timestamps) >= 2:
            sample_diff = abs(self._base_timestamps[1] - self._base_timestamps[0])
            tf_seconds_map = {
                "1m": 60, "3m": 180, "5m": 300, "15m": 900,
                "30m": 1800, "1h": 3600, "4h": 14400, "1d": 86400
            }
            target_sec = tf_seconds_map.get(timeframe.lower(), 60)
            if sample_diff >= target_sec * 0.8:
                is_already_target_tf = True

        if timeframe != "1m" and not is_already_target_tf and "datetime" in self._base_df.columns:
            # Check if resampling is needed or if data is already in target timeframe
            try:
                self._df = TimeframeResampler.resample(self._base_df, timeframe)
            except Exception as e:
                logger.warning(f"Could not resample to {timeframe}, using raw data: {e}")
                self._df = self._base_df.copy()
        else:
            self._df = self._base_df.copy()

        self.state.total_candles = len(self._df)
        
        # Determine starting index (e.g. at least 50 historical candles if available)
        initial_idx = start_index if start_index is not None else min(50, max(0, len(self._df) - 1))
        self.state.start_index = initial_idx
        self.state.current_index = initial_idx
        self.state.status = ReplayStateEnum.PAUSED
        self.state.is_playing = False

        self._update_current_candle_state()
        logger.info(f"ReplayController loaded {len(self._df)} candles for {symbol} ({timeframe})")

        self.bus.emit(EventType.DATA_LOADED, {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_candles": len(self._df),
            "current_index": self.state.current_index,
        })
        self._emit_state_change()

    def set_timeframe(self, target_timeframe: str) -> bool:
        """Switches active timeframe while preserving current simulated timestamp."""
        if target_timeframe not in TIMEFRAMES:
            logger.warning(f"Unsupported timeframe: {target_timeframe}")
            return False

        if self._base_df.empty:
            self.state.timeframe = target_timeframe
            return True

        current_ts = self.state.current_timestamp

        try:
            resampled_df = TimeframeResampler.resample(self._base_df, target_timeframe)
            self._df = resampled_df
            self.state.timeframe = target_timeframe
            self.state.total_candles = len(self._df)

            # Re-align current_index based on timestamp
            if current_ts is not None:
                # Find the candle with timestamp <= current_ts
                matching = self._df[self._df["timestamp"] <= current_ts]
                if not matching.empty:
                    self.state.current_index = matching.index[-1]
                else:
                    self.state.current_index = 0
            else:
                self.state.current_index = min(50, len(self._df) - 1)

            self._update_current_candle_state()
            self.bus.emit(EventType.TIMEFRAME_CHANGED, {
                "timeframe": target_timeframe,
                "current_index": self.state.current_index,
            })
            self._emit_state_change()
            return True
        except Exception as e:
            logger.error(f"Error switching timeframe to {target_timeframe}: {e}")
            return False

    def play(self) -> None:
        """Starts replay playback."""
        if self._df.empty or self.state.current_index >= len(self._df) - 1:
            return
        self.state.status = ReplayStateEnum.PLAYING
        self.state.is_playing = True
        self.bus.emit(EventType.REPLAY_STARTED, {"index": self.state.current_index})
        self._emit_state_change()

    def pause(self) -> None:
        """Pauses replay playback."""
        self.state.status = ReplayStateEnum.PAUSED
        self.state.is_playing = False
        self.bus.emit(EventType.REPLAY_PAUSED, {"index": self.state.current_index})
        self._emit_state_change()

    def toggle_play_pause(self) -> None:
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def step_forward(self) -> bool:
        """Steps one candle forward into the future."""
        if self._df.empty:
            return False

        if self.state.current_index < len(self._df) - 1:
            self.state.current_index += 1
            self._update_current_candle_state()
            self._emit_candle_advanced()

            if self.state.current_index == len(self._df) - 1:
                self.state.status = ReplayStateEnum.COMPLETED
                self.state.is_playing = False
                self.bus.emit(EventType.REPLAY_COMPLETED, {"index": self.state.current_index})
                self._emit_state_change()
            return True
        else:
            if self.is_playing:
                self.pause()
            return False

    def step_backward(self) -> bool:
        """Steps one candle backward into the past."""
        if self._df.empty or self.state.current_index <= 0:
            return False

        self.state.current_index -= 1
        self._update_current_candle_state()
        self._emit_candle_advanced()
        self._emit_state_change()
        return True

    def jump_to_index(self, index: int) -> bool:
        """Jumps to a specific candle index."""
        if self._df.empty:
            return False

        target_idx = max(0, min(index, len(self._df) - 1))
        self.state.current_index = target_idx
        self._update_current_candle_state()
        self._emit_candle_advanced()
        self._emit_state_change()
        return True

    def jump_to_timestamp(self, timestamp: int) -> bool:
        """Jumps to the candle at or immediately before the specified unix timestamp."""
        if self._df.empty:
            return False

        matching = self._df[self._df["timestamp"] <= timestamp]
        if not matching.empty:
            return self.jump_to_index(matching.index[-1])
        else:
            return self.jump_to_index(0)

    def jump_to_date(self, target_date: Union[datetime, str]) -> bool:
        """Jumps to a specific datetime."""
        if isinstance(target_date, str):
            dt = pd.to_datetime(target_date, utc=True)
        else:
            dt = target_date.astimezone(timezone.utc) if target_date.tzinfo else target_date.replace(tzinfo=timezone.utc)
        return self.jump_to_timestamp(int(dt.timestamp()))

    def random_start(self, min_history_candles: int = 50, buffer_end_candles: int = 100) -> bool:
        """Jumps to a randomized candle index to start blind testing."""
        if len(self._df) <= min_history_candles + buffer_end_candles:
            return self.jump_to_index(min_history_candles)

        max_start = len(self._df) - buffer_end_candles
        rand_idx = random.randint(min_history_candles, max_start)
        return self.jump_to_index(rand_idx)

    def reset(self) -> None:
        """Resets replay to the initial start index."""
        self.pause()
        self.jump_to_index(self.state.start_index)
        self.bus.emit(EventType.REPLAY_RESET, {"index": self.state.current_index})

    def set_speed(self, speed: float) -> None:
        """Updates playback speed multiplier (e.g. 0.1, 1.0, 5.0, 10.0)."""
        self.state.speed = max(0.01, speed)
        self._emit_state_change()

    def get_timer_interval_ms(self) -> int:
        """Calculates actual millisecond timer interval adjusted for replay speed."""
        interval = int(self.base_timer_interval_ms / max(0.01, self.state.speed))
        return max(20, interval)

    def get_sub_candles_for_current(self) -> List[Dict[str, Any]]:
        """
        Returns underlying 1m sub-candles for the active candle if higher timeframe
        to allow exact sub-tick intrabar execution. Uses ultra-fast binary search slicing.
        """
        candle = self.get_current_candle()
        if not candle or self._base_df.empty or self.state.timeframe == "1m":
            return []

        c_ts = int(candle.get("timestamp", 0))
        tf_mins = TIMEFRAME_MINUTES.get(self.state.timeframe, 5)
        tf_secs = tf_mins * 60

        if hasattr(self, "_base_timestamps") and len(self._base_timestamps) > 0:
            i_start = int(np.searchsorted(self._base_timestamps, c_ts))
            i_end = int(np.searchsorted(self._base_timestamps, c_ts + tf_secs))
            if i_start >= i_end:
                return []
            return self._base_df.iloc[i_start:i_end].to_dict(orient="records")

        sub_slice = self._base_df[
            (self._base_df["timestamp"] >= c_ts) & (self._base_df["timestamp"] < c_ts + tf_secs)
        ]
        return sub_slice.to_dict(orient="records") if not sub_slice.empty else []

    def get_visible_candles(self) -> pd.DataFrame:
        """
        STRICT HIDDEN FUTURE:
        Returns only the historical slice [0 .. current_index].
        Future data is strictly inaccessible.
        """
        if self._df.empty:
            return pd.DataFrame()
        return self._df.iloc[: self.state.current_index + 1].copy()

    def get_current_candle(self) -> Optional[Dict[str, Any]]:
        """Returns the single current candle dictionary."""
        if self._df.empty or self.state.current_index < 0 or self.state.current_index >= len(self._df):
            return None
        return self._df.iloc[self.state.current_index].to_dict()

    def _update_current_candle_state(self) -> None:
        candle = self.get_current_candle()
        if candle:
            self.state.current_timestamp = int(candle.get("timestamp", 0))
            if "datetime" in candle:
                self.state.current_datetime = candle["datetime"]

    def _emit_candle_advanced(self) -> None:
        candle = self.get_current_candle()
        if not candle:
            return

        event = CandleAdvancedEvent(
            index=self.state.current_index,
            candle=candle,
            symbol=self.state.symbol,
            timeframe=self.state.timeframe,
            total_candles=self.state.total_candles,
            is_last=(self.state.current_index >= self.state.total_candles - 1),
        )
        self.bus.emit(EventType.CANDLE_ADVANCED, event)

    def _emit_state_change(self) -> None:
        event = ReplayStateChangedEvent(
            status=self.state.status.value,
            current_index=self.state.current_index,
            speed=self.state.speed,
            timeframe=self.state.timeframe,
        )
        self.bus.emit(EventType.REPLAY_STARTED if self.is_playing else EventType.REPLAY_PAUSED, event)
