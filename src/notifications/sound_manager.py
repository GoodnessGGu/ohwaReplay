import math
from pathlib import Path
import struct
from typing import Optional
import wave

from src.utils.logger import logger


def generate_wav_file(file_path: Path, freq: float = 440.0, duration_sec: float = 0.2, volume: float = 0.5) -> None:
    """Generates a clean simple sine wave WAV audio file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 44100
    n_samples = int(sample_rate * duration_sec)

    with wave.open(str(file_path), "w") as wav_file:
        wav_file.setnchannels(1)        # mono
        wav_file.setsampwidth(2)        # 16-bit
        wav_file.setframerate(sample_rate)

        for i in range(n_samples):
            # Apply decay envelope
            envelope = (1.0 - (i / n_samples))
            val = math.sin(2.0 * math.pi * freq * (i / sample_rate)) * volume * envelope
            sample = int(max(-32767, min(32767, val * 32767)))
            data = struct.pack("<h", sample)
            wav_file.writeframesraw(data)


class SoundManager:
    """Manages audio feedback for trading and alerts."""

    def __init__(self, sounds_dir: str = "assets/sounds", enabled: bool = True, volume: float = 0.8):
        self.sounds_dir = Path(sounds_dir)
        self.enabled = enabled
        self.volume = volume
        self._ensure_default_sounds()

    def _ensure_default_sounds(self) -> None:
        """Generates crisp audio cues if sound files do not already exist."""
        sound_configs = {
            "order_open.wav": (587.33, 0.15),   # D5 chime
            "order_close.wav": (440.0, 0.15),   # A4
            "tp.wav": (880.0, 0.25),            # High A5 happy chime
            "sl.wav": (220.0, 0.3),             # Low A3 alert tone
            "alert.wav": (784.0, 0.2),          # G5 chime
        }
        for filename, (freq, dur) in sound_configs.items():
            path = self.sounds_dir / filename
            if not path.exists():
                try:
                    generate_wav_file(path, freq=freq, duration_sec=dur, volume=self.volume)
                except Exception as e:
                    logger.debug(f"Could not generate sound file {filename}: {e}")

    def play(self, sound_name: str) -> None:
        """Plays a sound asynchronously if enabled."""
        if not self.enabled:
            return

        sound_file = self.sounds_dir / f"{sound_name}.wav"
        if not sound_file.exists():
            sound_file = self.sounds_dir / sound_name
            if not sound_file.exists():
                return

        # Attempt playback via platform-native audio or Qt if available
        try:
            import winsound
            winsound.PlaySound(str(sound_file), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass  # Fallback gracefully in headless/unsupported test environments
