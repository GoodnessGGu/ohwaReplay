import pytest
from ui.theme_manager import ThemeManager


def test_theme_manager_themes():
    themes = ThemeManager.get_theme_names()
    assert len(themes) >= 5
    assert "Dark Charcoal" in themes
    assert "Midnight Blue" in themes
    assert "OLED Black" in themes
    assert "Light Clean" in themes
    assert "Forest Emerald" in themes


def test_theme_manager_generate_qss():
    for name in ThemeManager.get_theme_names():
        qss = ThemeManager.generate_qss(name)
        assert isinstance(qss, str)
        assert len(qss) > 100
        assert "QMainWindow" in qss
        assert "QToolBar" in qss
        assert "QPushButton" in qss


def test_theme_manager_chart_colors():
    for name in ThemeManager.get_theme_names():
        data = ThemeManager.get_theme_data(name)
        assert "bg_color" in data
        assert "text_color" in data
        assert "grid_color" in data
        assert "card_bg" in data
        assert "border_color" in data
