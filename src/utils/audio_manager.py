import io
import math
import struct
import tempfile
import wave
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer, QSoundEffect

from src.events.event_bus import EventBus, event_bus
from src.utils.constants import CloseReason, EventType
from src.utils.logger import logger


class AudioManager:
    """
    Synthesizes and manages trader sound effects (order execution, TP, SL, BE, alerts).
    Generates pure-tone uncompressed PCM WAV files on-the-fly with zero external dependencies.
    """

    def __init__(self, event_bus_instance: Optional[EventBus] = None, enabled: bool = True):
        self.bus = event_bus_instance or event_bus
        self.enabled = enabled
        self.volume: float = 0.70
        self._sound_files: Dict[str, Path] = {}
        self._effects: Dict[str, QSoundEffect] = {}

        self._init_sounds()
        self._subscribe_events()

    def _init_sounds(self) -> None:
        """Generates crisp audio tone WAVs in temporary directory."""
        temp_dir = Path(tempfile.gettempdir()) / "trading_replay_sounds"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 1. Order Placed / Filled (Crisp double pop)
        self._sound_files["order_placed"] = self._create_wav(
            temp_dir / "order_placed.wav",
            tones=[(880, 0.04, 0.5), (0, 0.02, 0), (1320, 0.06, 0.7)],
        )

        # 2. Take Profit (Pleasant ascending major chord C5 -> E5 -> G5)
        self._sound_files["take_profit"] = self._create_wav(
            temp_dir / "take_profit.wav",
            tones=[(523.25, 0.08, 0.5), (659.25, 0.08, 0.6), (783.99, 0.18, 0.7)],
        )

        # 3. Stop Loss (Muted low tone)
        self._sound_files["stop_loss"] = self._create_wav(
            temp_dir / "stop_loss.wav",
            tones=[(240, 0.10, 0.6), (180, 0.15, 0.5)],
        )

        # 4. Break Even (High electronic blip)
        self._sound_files["break_even"] = self._create_wav(
            temp_dir / "break_even.wav",
            tones=[(1046.50, 0.05, 0.5), (1318.51, 0.08, 0.6)],
        )

        # 5. Price Alert (Double beep)
        self._sound_files["alert"] = self._create_wav(
            temp_dir / "alert.wav",
            tones=[(900, 0.08, 0.6), (0, 0.04, 0), (900, 0.12, 0.7)],
        )

        # Lazily instantiate QSoundEffects when needed
        pass

    def _create_wav(self, file_path: Path, tones: list) -> Path:
        """Synthesizes a 44.1kHz 16-bit mono PCM WAV file."""
        sample_rate = 44100
        total_samples = []

        for freq, duration, amp in tones:
            num_samples = int(sample_rate * duration)
            for i in range(num_samples):
                if freq == 0:
                    val = 0
                else:
                    # Apply smooth envelope attack & decay to eliminate clicking
                    fade = min(1.0, i / (sample_rate * 0.01), (num_samples - i) / (sample_rate * 0.01))
                    t = float(i) / sample_rate
                    val = int(amp * fade * 32767.0 * math.sin(2.0 * math.pi * freq * t))
                total_samples.append(val)

        with wave.open(str(file_path), "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            raw_data = struct.pack(f"<{len(total_samples)}h", *total_samples)
            wav_file.writeframes(raw_data)

        return file_path

    def _subscribe_events(self) -> None:
        """Wires up event bus listener to automatically trigger sounds."""
        self.bus.subscribe(EventType.ORDER_OPENED, self._on_order_opened)
        self.bus.subscribe(EventType.ORDER_CLOSED, self._on_order_closed)
        self.bus.subscribe(EventType.PRICE_ALERT, self._on_alert_triggered)

    def _on_order_opened(self, event_data: Any) -> None:
        self.play("order_placed")

    def _on_order_closed(self, event_data: Any) -> None:
        pos_data = event_data.data if hasattr(event_data, "data") else event_data
        reason = pos_data.get("close_reason") if isinstance(pos_data, dict) else getattr(pos_data, "close_reason", None)
        reason_val = reason.value if hasattr(reason, "value") else str(reason)

        if reason_val == CloseReason.TAKE_PROFIT.value:
            self.play("take_profit")
        elif reason_val == CloseReason.STOP_LOSS.value:
            self.play("stop_loss")
        else:
            # Check if closed in profit or loss
            pnl = pos_data.get("realized_pnl", 0.0) if isinstance(pos_data, dict) else getattr(pos_data, "realized_pnl", 0.0)
            if pnl > 0:
                self.play("take_profit")
            else:
                self.play("order_placed")

    def _on_alert_triggered(self, event_data: Any) -> None:
        self.play("alert")

    def play(self, sound_name: str) -> None:
        """Plays a preloaded sound effect if audio is enabled."""
        if not self.enabled:
            return
        path = self._sound_files.get(sound_name)
        if not path or not path.exists():
            return
        try:
            from PyQt6.QtCore import QCoreApplication
            if not QCoreApplication.instance():
                return
            if sound_name not in self._effects:
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(self.volume)
                self._effects[sound_name] = effect
            self._effects[sound_name].play()
        except Exception as e:
            logger.debug(f"Audio playback note: {e}")

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        for effect in self._effects.values():
            effect.setVolume(self.volume)


audio_manager = AudioManager()
