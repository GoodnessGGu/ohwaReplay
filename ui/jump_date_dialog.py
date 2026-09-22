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

    def __init__(
        self,
        current_dt: Optional[datetime] = None,
        earliest_dt: Optional[datetime] = None,
        latest_dt: Optional[datetime] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Replay from Historical Date")
        self.setMinimumWidth(440)

        now_utc = datetime.now(timezone.utc)
        self.latest_dt = latest_dt or now_utc
        self.earliest_dt = earliest_dt or (self.latest_dt - timedelta(days=260))
        self.current_dt = current_dt or self.latest_dt

        # Ensure timezone-aware
        if self.latest_dt.tzinfo is None:
            self.latest_dt = self.latest_dt.replace(tzinfo=timezone.utc)
        if self.earliest_dt.tzinfo is None:
            self.earliest_dt = self.earliest_dt.replace(tzinfo=timezone.utc)
        if self.current_dt.tzinfo is None:
            self.current_dt = self.current_dt.replace(tzinfo=timezone.utc)

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Available Data Information Banner
        earliest_str = self.earliest_dt.strftime("%Y-%m-%d %H:%M")
        latest_str = self.latest_dt.strftime("%Y-%m-%d %H:%M")
        days_span = max(1, (self.latest_dt - self.earliest_dt).days)
        lbl_range = QLabel(f"📊 Available Dataset: {earliest_str} ➔ {latest_str} ({days_span} days)")
        lbl_range.setStyleSheet(
            "color: #26a69a; font-weight: bold; font-size: 11px; padding: 6px 10px; "
            "background-color: #132724; border-radius: 4px; border: 1px solid #26a69a;"
        )
        layout.addWidget(lbl_range)

        grp_date = QGroupBox("SELECT REPLAY START DATE & TIME")
        form = QFormLayout(grp_date)

        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")

        qdt_min = QDateTime(self.earliest_dt.year, self.earliest_dt.month, self.earliest_dt.day, self.earliest_dt.hour, self.earliest_dt.minute)
        qdt_max = QDateTime(self.latest_dt.year, self.latest_dt.month, self.latest_dt.day, self.latest_dt.hour, self.latest_dt.minute)
        self.date_edit.setMinimumDateTime(qdt_min)
        self.date_edit.setMaximumDateTime(qdt_max)

        # Clamped initial value
        clamped_init = max(self.earliest_dt, min(self.current_dt, self.latest_dt))
        qdt = QDateTime(
            clamped_init.year,
            clamped_init.month,
            clamped_init.day,
            clamped_init.hour,
            clamped_init.minute,
        )
        self.date_edit.setDateTime(qdt)
        self.date_edit.setStyleSheet("padding: 4px; font-weight: bold; font-size: 13px;")
        form.addRow("Replay Start Date:", self.date_edit)

        layout.addWidget(grp_date)

        # Quick preset buttons
        grp_quick = QGroupBox("QUICK REWIND PRESETS")
        quick_vbox = QVBoxLayout(grp_quick)

        row1 = QHBoxLayout()
        btn_1d = QPushButton("⏪ 1 Day")
        btn_1d.clicked.connect(lambda: self._apply_delta(days=1))
        row1.addWidget(btn_1d)

        btn_1w = QPushButton("⏪ 1 Week")
        btn_1w.clicked.connect(lambda: self._apply_delta(days=7))
        row1.addWidget(btn_1w)

        btn_1m = QPushButton("⏪ 1 Month")
        btn_1m.clicked.connect(lambda: self._apply_delta(days=30))
        row1.addWidget(btn_1m)
        quick_vbox.addLayout(row1)

        row2 = QHBoxLayout()
        btn_3m = QPushButton("⏪ 3 Months")
        btn_3m.clicked.connect(lambda: self._apply_delta(days=90))
        row2.addWidget(btn_3m)

        btn_6m = QPushButton("⏪ 6 Months")
        btn_6m.clicked.connect(lambda: self._apply_delta(days=180))
        row2.addWidget(btn_6m)

        btn_start = QPushButton("⏮ Jan 1, 2026")
        btn_start.clicked.connect(self._set_start_2026)
        row2.addWidget(btn_start)
        quick_vbox.addLayout(row2)

        layout.addWidget(grp_quick)

        lbl_hint = QLabel(
            "💡 Full technical analysis context: All prior historical candles up to this date\n"
            "remain visible on your chart so you can analyze trends, structure, and indicators."
        )
        lbl_hint.setStyleSheet("color: #2962ff; font-weight: 600; font-size: 11px;")
        layout.addWidget(lbl_hint)

        # Standard dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_delta(self, days: int) -> None:
        target = max(self.earliest_dt, self.latest_dt - timedelta(days=days))
        qdt = QDateTime(target.year, target.month, target.day, target.hour, target.minute)
        self.date_edit.setDateTime(qdt)

    def _set_start_2026(self) -> None:
        target = max(self.earliest_dt, datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc))
        qdt = QDateTime(target.year, target.month, target.day, target.hour, target.minute)
        self.date_edit.setDateTime(qdt)

    def get_selected_timestamp(self) -> int:
        py_dt = self.date_edit.dateTime().toPyDateTime().replace(tzinfo=timezone.utc)
        return int(py_dt.timestamp())
