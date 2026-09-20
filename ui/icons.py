from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer


# Crisp, high-contrast TradingView-style SVG definitions
SVG_ICONS = {
    "cursor": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 3l7 18 3-7 7-3L3 3z" fill="#2962ff" fill-opacity="0.3"/>
    </svg>""",

    "trendline": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="20" x2="20" y2="4"/>
        <circle cx="4" cy="20" r="2.5" fill="#2962ff" stroke="#2962ff"/>
        <circle cx="20" cy="4" r="2.5" fill="#2962ff" stroke="#2962ff"/>
    </svg>""",

    "ray": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="19" x2="20" y2="5"/>
        <circle cx="4" cy="19" r="2.5" fill="#2962ff" stroke="#2962ff"/>
        <polyline points="15 5 20 5 20 10"/>
    </svg>""",

    "horizontal_line": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="2" y1="12" x2="22" y2="12"/>
        <circle cx="12" cy="12" r="2.5" fill="#2962ff" stroke="#2962ff"/>
    </svg>""",

    "vertical_line": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="2" x2="12" y2="22"/>
        <circle cx="12" cy="12" r="2.5" fill="#2962ff" stroke="#2962ff"/>
    </svg>""",

    "rectangle": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="5" width="16" height="14" rx="1.5" fill="#2962ff" fill-opacity="0.2"/>
        <circle cx="4" cy="5" r="2" fill="#2962ff"/>
        <circle cx="20" cy="19" r="2" fill="#2962ff"/>
    </svg>""",

    "fibonacci": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#ff9800" stroke-width="1.8" stroke-linecap="round">
        <line x1="3" y1="4" x2="21" y2="4"/>
        <line x1="3" y1="9" x2="21" y2="9" stroke-dasharray="2 2"/>
        <line x1="3" y1="15" x2="21" y2="15" stroke-dasharray="2 2"/>
        <line x1="3" y1="20" x2="21" y2="20"/>
        <line x1="4" y1="20" x2="20" y2="4" stroke="#d1d4dc" stroke-width="1.2"/>
    </svg>""",

    "text": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="4 7 4 4 20 4 20 7"/>
        <line x1="12" y1="4" x2="12" y2="20"/>
        <line x1="9" y1="20" x2="15" y2="20"/>
    </svg>""",

    "arrow": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="5" y1="19" x2="19" y2="5"/>
        <polyline points="10 5 19 5 19 14"/>
    </svg>""",

    "path": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#2962ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="3 17 8 8 15 14 21 6" stroke="#d1d4dc"/>
        <circle cx="3" cy="17" r="2.5" fill="#2962ff" stroke="#2962ff"/>
        <circle cx="8" cy="8" r="2.5" fill="#2962ff" stroke="#2962ff"/>
        <circle cx="15" cy="14" r="2.5" fill="#2962ff" stroke="#2962ff"/>
        <circle cx="21" cy="6" r="2.5" fill="#2962ff" stroke="#2962ff"/>
    </svg>""",

    "volume_profile": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" stroke="#434651" fill="#1e222d" fill-opacity="0.3"/>
        <rect x="3" y="5" width="8" height="2.5" fill="#2962ff" fill-opacity="0.6"/>
        <rect x="3" y="8" width="13" height="2.5" fill="#2962ff" fill-opacity="0.7"/>
        <rect x="3" y="11" width="16" height="2.5" fill="#ff9800" fill-opacity="0.9"/>
        <rect x="3" y="14" width="10" height="2.5" fill="#2962ff" fill-opacity="0.7"/>
        <rect x="3" y="17" width="5" height="2.5" fill="#2962ff" fill-opacity="0.6"/>
        <line x1="3" y1="12.2" x2="21" y2="12.2" stroke="#ff9800" stroke-width="1.5"/>
    </svg>""",

    "long_position": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#26a69a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="16" height="7" fill="#26a69a" fill-opacity="0.35"/>
        <rect x="4" y="11" width="16" height="9" fill="#ef5350" fill-opacity="0.35" stroke="#ef5350"/>
        <line x1="3" y1="11" x2="21" y2="11" stroke="#ffffff" stroke-width="2"/>
        <polyline points="9 7 12 4 15 7"/>
    </svg>""",

    "short_position": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#ef5350" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="16" height="9" fill="#ef5350" fill-opacity="0.35"/>
        <rect x="4" y="13" width="16" height="7" fill="#26a69a" fill-opacity="0.35" stroke="#26a69a"/>
        <line x1="3" y1="13" x2="21" y2="13" stroke="#ffffff" stroke-width="2"/>
        <polyline points="9 17 12 20 15 17"/>
    </svg>""",

    "measure": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M2 12h20M12 2v20M5 9v6M19 9v6M9 10v4M15 10v4"/>
    </svg>""",

    "undo": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 14L4 9l5-5"/>
        <path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"/>
    </svg>""",

    "redo": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 14l5-5-5-5"/>
        <path d="M20 9H9.5A5.5 5.5 0 0 0 4 14.5v0A5.5 5.5 0 0 0 9.5 20H13"/>
    </svg>""",

    "trash": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#ef5350" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        <line x1="10" y1="11" x2="10" y2="17"/>
        <line x1="14" y1="11" x2="14" y2="17"/>
    </svg>""",

    "settings": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </svg>""",

    "lock": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>""",

    "unlock": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#d1d4dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
        <path d="M7 11V7a5 5 0 0 1 9.9-1"/>
    </svg>"""
}


def get_svg_icon(name: str, size: int = 20, active_color: str = "#2962ff") -> QIcon:
    """Renders an SVG string into a crisp high-DPI QIcon."""
    svg_str = SVG_ICONS.get(name)
    if not svg_str:
        return QIcon()

    renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)
