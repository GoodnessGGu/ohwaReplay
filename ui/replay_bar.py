from typing import Optional
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QWidget,
)


class ReplayBar(QFrame):
    """Bottom replay control toolbar."""

    play_pause_clicked = pyqtSignal()
    step_forward_clicked = pyqtSignal()
    step_backward_clicked = pyqtSignal()
    reset_clicked = pyqtSignal()
    random_start_clicked = pyqtSignal()
    speed_changed = pyqtSignal(float)
    seek_requested = pyqtSignal(int)
    jump_to_date_clicked = pyqtSignal()
    go_to_latest_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            ReplayBar {
                background-color: #1e222d;
                border-top: 1px solid #2a2e39;
                padding: 4px 10px;
            }
        """)
        self._is_playing = False
        self.init_ui()

    def init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(10)

        # Replay from Date button
        self.btn_jump_date = QPushButton("📅 Replay from Date...")
        self.btn_jump_date.setStyleSheet("background-color: #363c4e; color: #2962ff; font-weight: 700; border: 1px solid #2962ff;")
        self.btn_jump_date.clicked.connect(self.jump_to_date_clicked.emit)
        layout.addWidget(self.btn_jump_date)

        # Reset button
        self.btn_reset = QPushButton("⏮ Start")
        self.btn_reset.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(self.btn_reset)

        # Step Back
        self.btn_step_back = QPushButton("◀ Step")
        self.btn_step_back.clicked.connect(self.step_backward_clicked.emit)
        layout.addWidget(self.btn_step_back)

        # Play / Pause
        self.btn_play_pause = QPushButton("▶ Play")
        self.btn_play_pause.setStyleSheet("background-color: #2962ff; color: #ffffff; font-weight: 700; padding: 6px 16px;")
        self.btn_play_pause.clicked.connect(self.play_pause_clicked.emit)
        layout.addWidget(self.btn_play_pause)

        # Step Forward
        self.btn_step_fwd = QPushButton("Step ▶")
        self.btn_step_fwd.clicked.connect(self.step_forward_clicked.emit)
        layout.addWidget(self.btn_step_fwd)

        # Go to Latest
        self.btn_latest = QPushButton("⏩ Latest")
        self.btn_latest.setStyleSheet("background-color: #2a2e39; color: #26a69a; font-weight: 700;")
        self.btn_latest.clicked.connect(self.go_to_latest_clicked.emit)
        layout.addWidget(self.btn_latest)

        # Speed selector
        lbl_speed = QLabel("Speed:")
        lbl_speed.setStyleSheet("color: #848e9c; font-weight: 600;")
        layout.addWidget(lbl_speed)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.1x", "0.25x", "0.5x", "1.0x", "2.0x", "5.0x", "10.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        layout.addWidget(self.speed_combo)

        # Random start button
        self.btn_random = QPushButton("🎲 Random")
        self.btn_random.clicked.connect(self.random_start_clicked.emit)
        layout.addWidget(self.btn_random)

        # Progress Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(0)
        self.slider.sliderMoved.connect(self.seek_requested.emit)
        layout.addWidget(self.slider, 1)

        # Candle index / time label
        self.lbl_status = QLabel("Candle: 0 / 0 | Time: --")
        self.lbl_status.setStyleSheet("color: #d1d4dc; font-weight: 600; font-family: monospace;")
        layout.addWidget(self.lbl_status)

    def _on_speed_changed(self, text: str) -> None:
        try:
            val = float(text.replace("x", ""))
            self.speed_changed.emit(val)
        except Exception:
            pass

    def set_playing(self, is_playing: bool) -> None:
        self._is_playing = is_playing
        if is_playing:
            self.btn_play_pause.setText("⏸ Pause")
            self.btn_play_pause.setStyleSheet("background-color: #ff9800; color: #131722; font-weight: 700; padding: 6px 16px;")
        else:
            self.btn_play_pause.setText("▶ Play")
            self.btn_play_pause.setStyleSheet("background-color: #2962ff; color: #ffffff; font-weight: 700; padding: 6px 16px;")

    def update_progress(self, current_idx: int, total_candles: int, current_time: str = "--") -> None:
        self.slider.blockSignals(True)
        self.slider.setMaximum(max(1, total_candles - 1))
        self.slider.setValue(current_idx)
        self.slider.blockSignals(False)
        self.lbl_status.setText(f"Candle: {current_idx + 1} / {total_candles} | Time: {current_time}")
