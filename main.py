import os
import sys
import ctypes
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from src.utils.logger import logger
from ui.main_window import MainWindow


def main():
    """Main entrypoint for Trading Replay Lab application."""
    # Force Windows to assign a unique AppUserModelID to this process
    # Prevents Windows from grouping the app under the generic 'python.exe' taskbar icon
    if sys.platform == "win32":
        try:
            my_app_id = "replayzone.tradingreplaylab.desktop.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)
        except Exception as e:
            logger.warning(f"Failed to set AppUserModelID: {e}")

    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)
    logger.info("Starting Trading Replay Lab...")

    app = QApplication(sys.argv)
    app.setApplicationName("Replay Zone")
    app.setApplicationVersion("1.0.0")

    # Set icon at App level
    icon_path = "replay_zone_filmstrip_dark_1024.png"
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    from ui.theme_manager import ThemeManager
    app.setStyleSheet(ThemeManager.generate_qss("OLED Black"))

    window = MainWindow()
    # Explicitly set icon on the window instance
    window.setWindowIcon(app_icon)
    
    window.show()
    window.raise_()
    window.activateWindow()

    logger.info("Application UI initialized and running.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()