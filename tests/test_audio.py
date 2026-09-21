import pytest
from pathlib import Path
from src.utils.audio_manager import AudioManager


def test_audio_manager_wav_generation():
    audio = AudioManager(enabled=False)
    assert "order_placed" in audio._sound_files
    assert "take_profit" in audio._sound_files
    assert "stop_loss" in audio._sound_files
    assert "break_even" in audio._sound_files
    assert "alert" in audio._sound_files

    for name, path in audio._sound_files.items():
        assert path.exists()
        assert path.stat().st_size > 100

    audio.set_enabled(True)
    assert audio.enabled is True
    audio.set_volume(0.5)
    assert audio.volume == 0.5
