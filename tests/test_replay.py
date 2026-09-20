import pytest
import pandas as pd
from src.events.event_bus import EventBus
from src.data.synthetic_data import SyntheticDataGenerator
from src.replay.replay_controller import ReplayController
from src.utils.constants import EventType, ReplayStateEnum


def test_replay_initialization_and_hidden_future():
    bus = EventBus()
    controller = ReplayController(event_bus_instance=bus)
    df = SyntheticDataGenerator.generate(symbol="XAUUSD", num_candles=200, timeframe="5m", seed=42)

    controller.load_data(df, symbol="XAUUSD", timeframe="5m", start_index=50)

    assert controller.current_index == 50
    assert controller.total_candles == 200

    # Test Hidden Future: Only candles 0..50 are returned
    visible = controller.get_visible_candles()
    assert len(visible) == 51
    assert visible.iloc[-1]["timestamp"] == df.iloc[50]["timestamp"]


def test_replay_step_forward_and_backward():
    bus = EventBus()
    controller = ReplayController(event_bus_instance=bus)
    df = SyntheticDataGenerator.generate(symbol="EURUSD", num_candles=100, timeframe="5m", seed=10)
    controller.load_data(df, symbol="EURUSD", timeframe="5m", start_index=10)

    events = []
    bus.subscribe(EventType.CANDLE_ADVANCED, lambda e: events.append(e))

    # Step forward
    success = controller.step_forward()
    assert success is True
    assert controller.current_index == 11
    assert len(events) == 1
    assert events[-1].index == 11

    # Step backward
    success = controller.step_backward()
    assert success is True
    assert controller.current_index == 10
    assert len(events) == 2
    assert events[-1].index == 10


def test_replay_play_pause_and_completion():
    bus = EventBus()
    controller = ReplayController(event_bus_instance=bus)
    df = SyntheticDataGenerator.generate(symbol="BTCUSD", num_candles=5, timeframe="5m", seed=1)
    controller.load_data(df, symbol="BTCUSD", timeframe="5m", start_index=2)

    controller.play()
    assert controller.is_playing is True

    controller.pause()
    assert controller.is_playing is False

    # Step to completion
    controller.step_forward() # idx 3
    controller.step_forward() # idx 4 (last)
    assert controller.state.status == ReplayStateEnum.COMPLETED
    assert controller.is_playing is False


def test_replay_jump_and_speed():
    bus = EventBus()
    controller = ReplayController(event_bus_instance=bus)
    df = SyntheticDataGenerator.generate(symbol="GBPUSD", num_candles=100, timeframe="5m", seed=55)
    controller.load_data(df, symbol="GBPUSD", timeframe="5m", start_index=10)

    controller.set_speed(5.0)
    assert controller.state.speed == 5.0
    assert controller.get_timer_interval_ms() == 200

    controller.jump_to_index(75)
    assert controller.current_index == 75
    assert len(controller.get_visible_candles()) == 76
