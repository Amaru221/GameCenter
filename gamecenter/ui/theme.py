"""The dark theme, as one stylesheet."""

ACCENT = "#4cc9f0"
BACKGROUND = "#12151b"

STYLESHEET = f"""
QMainWindow, QWidget#Root {{
    background: {BACKGROUND};
}}
QWidget#Header {{
    background: #151922;
    border-bottom: 1px solid #232a37;
}}
QLabel {{
    color: #e6e9ef;
}}
QLabel#Title {{
    font-size: 22px;
    font-weight: 700;
    color: #f2f5fa;
}}
QLabel#Subtitle {{
    color: #8f9aab;
    font-size: 12px;
}}
QLabel#Empty {{
    color: #8f9aab;
    font-size: 14px;
}}
QLineEdit, QComboBox {{
    background: #1a1e26;
    border: 1px solid #2a3140;
    border-radius: 8px;
    padding: 7px 10px;
    color: #e6e9ef;
    selection-background-color: {ACCENT};
    selection-color: #08131a;
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox QAbstractItemView {{
    background: #1a1e26;
    border: 1px solid #2a3140;
    selection-background-color: #263247;
    outline: none;
}}
QPushButton {{
    background: #222836;
    border: 1px solid #2f394b;
    border-radius: 8px;
    padding: 7px 14px;
    color: #e6e9ef;
}}
QPushButton:hover {{
    background: #2a3244;
    border-color: #3a4a63;
}}
QPushButton:pressed {{
    background: #202634;
}}
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    color: #c9d2e0;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 8px;
}}
QListWidget::item:hover {{
    background: #1a1f29;
    border-color: #2a3140;
}}
QListWidget::item:selected {{
    background: #1e2a3a;
    border-color: {ACCENT};
    color: #ffffff;
}}
QMenu {{
    background: #1a1e26;
    border: 1px solid #2a3140;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 18px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background: #263247;
}}
QMenu::item:disabled {{
    color: #5c6677;
}}
QStatusBar {{
    color: #8f9aab;
    background: #151922;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #2c3546;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #3a465c;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
}}
"""
