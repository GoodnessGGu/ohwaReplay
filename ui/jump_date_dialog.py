from datetime import datetime, timedelta, timezone
from typing import Optional
from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class JumpToDateDialog(QDialog):
    """Dialog for jumping/rewinding the market replay to a specific date."""

    def __init__(self, current_dt: Optional[datetime] = None, latest_dt: Optional[datetime] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Replay from Historical Date")
        self.setMinimumWidth(380)

        self.latest_dt = latest_dt or datetime(2026, 9, 20, 0, 0, tzinfo=timezone.utc)
        self.current_dt = current_dt or self.latest_dt

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        grp_date = QGroupBox("SELECT REPLAY START DATE & TIME")
        form = QFormLayout(grp_date)

        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")

        # Convert to QDateTime
        qdt = QDateTime(
            self.current_dt.year,
            self.current_dt.month,
            self.current_dt.day,
            self.current_dt.hour,
            self.current_dt.minute,
        )
        self.date_edit.setDateTime(qdt)
        form.addRow("Jump To Date:", self.date_edit)

        layout.addWidget(grp_date)

        # Quick preset buttons
        grp_quick = QGroupBox("QUICK REWIND PRESETS")
        quick_layout = QHBoxLayout(grp_quick)

        btn_1d = QPushButton("⏪ 1 Day")
        btn_1d.clicked.connect(lambda: self._apply_delta(days=1))
        quick_layout.addWidget(btn_1d)

        btn_1w = QPushButton("⏪ 1 Week")
        btn_1w.clicked.connect(lambda: self._apply_delta(days=7))
        quick_layout.addWidget(btn_1w)

        btn_1m = QPushButton("⏪ 1 Month")
        btn_1m.clicked.connect(lambda: self._apply_delta(days=30))
        quick_layout.addWidget(btn_1m)

        btn_start_2026 = QPushButton("⏪ Jan 1, 2026")
        btn_start_2026.clicked.connect(self._set_start_2026)
        quick_layout.addWidget(btn_start_2026)

        layout.addWidget(grp_quick)

        lbl_hint = QLabel("Future price action after the selected date will be hidden for backtesting.")
        lbl_hint.setStyleSheet("color: #848e9c; font-style: italic; font-size: 11px;")
        layout.addWidget(lbl_hint)

        # Standard dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_delta(self, days: int) -> None:
        target = self.latest_dt - timedelta(days=days)
        qdt = QDateTime(target.year, target.month, target.day, target.hour, target.minute)
        self.date_edit.setDateTime(qdt)

    def _set_start_2026(self) -> None:
        qdt = QDateTime(2026, 1, 1, 0, 0)
        self.date_edit.setDateTime(qdt)

    def get_selected_timestamp(self) -> int:
        py_dt = self.date_edit.dateTime().toPyDateTime().replace(tzinfo=timezone.utc)
        return int(py_dt.timestamp())
