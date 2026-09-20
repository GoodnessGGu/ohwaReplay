from typing import Dict, List, Any


class ThemeManager:
    """
    Centralized theme engine for Trading Replay Lab.
    Provides coordinated QSS palettes for PyQt6 widgets and
    matched color schemes for the HTML5 Lightweight Charts engine.
    """

    THEMES = {
        "Dark Charcoal": {
            "id": "dark",
            "name": "Dark Charcoal",
            "bg_color": "#131722",
            "card_bg": "#1e222d",
            "hover_bg": "#2a2e39",
            "active_bg": "#363c4e",
            "border_color": "#2a2e39",
            "text_color": "#d1d4dc",
            "text_muted": "#848e9c",
            "text_bright": "#ffffff",
            "accent": "#2962ff",
            "accent_hover": "#1e53e5",
            "grid_color": "#1e222d",
            "success": "#26a69a",
            "danger": "#ef5350",
            "warning": "#ff9800",
        },
        "Midnight Blue": {
            "id": "midnight",
            "name": "Midnight Blue",
            "bg_color": "#0b0e17",
            "card_bg": "#131826",
            "hover_bg": "#1c2438",
            "active_bg": "#26324d",
            "border_color": "#1d263b",
            "text_color": "#c8d1e0",
            "text_muted": "#6c7d99",
            "text_bright": "#ffffff",
            "accent": "#388bfd",
            "accent_hover": "#1f6feb",
            "grid_color": "#141a29",
            "success": "#00e676",
            "danger": "#ff5252",
            "warning": "#ffa726",
        },
        "OLED Black": {
            "id": "oled",
            "name": "OLED Black",
            "bg_color": "#000000",
            "card_bg": "#0c0c0c",
            "hover_bg": "#1a1a1a",
            "active_bg": "#262626",
            "border_color": "#1e1e1e",
            "text_color": "#e0e0e0",
            "text_muted": "#757575",
            "text_bright": "#ffffff",
            "accent": "#2962ff",
            "accent_hover": "#1e53e5",
            "grid_color": "#121212",
            "success": "#00e676",
            "danger": "#ff5252",
            "warning": "#ffb300",
        },
        "Light Clean": {
            "id": "light",
            "name": "Light Clean",
            "bg_color": "#f0f3fa",
            "card_bg": "#ffffff",
            "hover_bg": "#e6eaf2",
            "active_bg": "#d8deeb",
            "border_color": "#d6dcff",
            "text_color": "#1e222d",
            "text_muted": "#5d6588",
            "text_bright": "#131722",
            "accent": "#2962ff",
            "accent_hover": "#1e53e5",
            "grid_color": "#e6eaf2",
            "success": "#26a69a",
            "danger": "#ef5350",
            "warning": "#f57c00",
        },
        "Forest Emerald": {
            "id": "forest",
            "name": "Forest Emerald",
            "bg_color": "#0a140e",
            "card_bg": "#112219",
            "hover_bg": "#193325",
            "active_bg": "#224734",
            "border_color": "#1b3829",
            "text_color": "#d0e6d8",
            "text_muted": "#6e947d",
            "text_bright": "#ffffff",
            "accent": "#00e676",
            "accent_hover": "#00c853",
            "grid_color": "#12241b",
            "success": "#00e676",
            "danger": "#ff5252",
            "warning": "#ffb74d",
        },
    }

    @classmethod
    def get_theme_names(cls) -> List[str]:
        return list(cls.THEMES.keys())

    @classmethod
    def get_theme_data(cls, theme_name: str) -> Dict[str, str]:
        return cls.THEMES.get(theme_name, cls.THEMES["Dark Charcoal"])

    @classmethod
    def generate_qss(cls, theme_name: str) -> str:
        """Generates dynamic, coherent PyQt6 stylesheet for the given theme."""
        t = cls.get_theme_data(theme_name)

        return f"""
QMainWindow {{
    background-color: {t['bg_color']};
    color: {t['text_color']};
}}

QWidget {{
    background-color: {t['bg_color']};
    color: {t['text_color']};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    font-size: 12px;
}}

QMenuBar {{
    background-color: {t['card_bg']};
    color: {t['text_color']};
    border-bottom: 1px solid {t['border_color']};
    padding: 2px 6px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {t['hover_bg']};
    color: {t['text_bright']};
}}

QMenu {{
    background-color: {t['card_bg']};
    color: {t['text_color']};
    border: 1px solid {t['border_color']};
    padding: 4px;
    border-radius: 6px;
}}

QMenu::item {{
    padding: 6px 20px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {t['accent']};
    color: #ffffff;
}}

QToolBar {{
    background-color: {t['card_bg']};
    border-bottom: 1px solid {t['border_color']};
    spacing: 6px;
    padding: 4px 8px;
}}

QPushButton {{
    background-color: {t['hover_bg']};
    color: {t['text_color']};
    border: 1px solid {t['border_color']};
    border-radius: 4px;
    padding: 5px 12px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {t['active_bg']};
    color: {t['text_bright']};
    border-color: {t['accent']};
}}

QPushButton:pressed {{
    background-color: {t['card_bg']};
}}

QPushButton#buyButton {{
    background-color: {t['success']};
    color: #ffffff;
    border: none;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 16px;
}}

QPushButton#buyButton:hover {{
    filter: brightness(115%);
}}

QPushButton#sellButton {{
    background-color: {t['danger']};
    color: #ffffff;
    border: none;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 16px;
}}

QPushButton#sellButton:hover {{
    filter: brightness(115%);
}}

QPushButton#closeButton {{
    background-color: {t['hover_bg']};
    color: {t['warning']};
    font-weight: 600;
    border: 1px solid {t['warning']};
}}

QPushButton#closeButton:hover {{
    background-color: {t['warning']};
    color: {t['bg_color']};
}}

QPushButton#toolButtonActive {{
    background-color: {t['accent']};
    color: #ffffff;
    border-color: {t['accent']};
}}

QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
    background-color: {t['card_bg']};
    color: {t['text_bright']};
    border: 1px solid {t['border_color']};
    border-radius: 4px;
    padding: 4px 8px;
}}

QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {t['accent']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {t['card_bg']};
    color: {t['text_color']};
    selection-background-color: {t['accent']};
    selection-color: #ffffff;
    border: 1px solid {t['border_color']};
}}

QTabWidget::pane {{
    border-top: 1px solid {t['border_color']};
    background-color: {t['bg_color']};
}}

QTabBar::tab {{
    background-color: {t['card_bg']};
    color: {t['text_muted']};
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}

QTabBar::tab:selected {{
    background-color: {t['bg_color']};
    color: {t['text_bright']};
    border-top: 2px solid {t['accent']};
}}

QTableWidget {{
    background-color: {t['bg_color']};
    color: {t['text_color']};
    border: 1px solid {t['border_color']};
    gridline-color: {t['border_color']};
    selection-background-color: {t['hover_bg']};
    selection-color: {t['text_bright']};
}}

QHeaderView::section {{
    background-color: {t['card_bg']};
    color: {t['text_muted']};
    border: none;
    border-bottom: 1px solid {t['border_color']};
    border-right: 1px solid {t['border_color']};
    padding: 6px;
    font-weight: 600;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {t['hover_bg']};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {t['accent']};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {t['text_bright']};
    border: 1px solid {t['accent']};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}

QScrollBar:vertical, QScrollBar:horizontal {{
    background: {t['bg_color']};
    width: 8px;
    height: 8px;
}}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: {t['hover_bg']};
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background: {t['active_bg']};
}}

QStatusBar {{
    background-color: {t['card_bg']};
    color: {t['text_muted']};
    border-top: 1px solid {t['border_color']};
}}

QGroupBox {{
    border: 1px solid {t['border_color']};
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 10px;
    font-weight: 600;
    color: {t['text_muted']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}}
"""
