import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from src.utils.logger import logger
from ui.main_window import MainWindow


def main():
    """Main entrypoint for Trading Replay Lab application."""
    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)
    logger.info("Starting Trading Replay Lab...")

    app = QApplication(sys.argv)
    app.setApplicationName("Trading Replay Lab")
    app.setApplicationVersion("1.0.0")

    from ui.theme_manager import ThemeManager
    app.setStyleSheet(ThemeManager.generate_qss("Dark Charcoal"))

    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()

    logger.info("Application UI initialized and running.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
