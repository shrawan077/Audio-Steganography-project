"""
main.py — CryptoWave entry point
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase, QFont
from gui import MainWindow


STYLE = """
/* ─── Global ─────────────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* ─── Cards ──────────────────────────────────────────────────────────────── */
QFrame#Card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 4px;
}

QLabel#CardTitle {
    font-size: 11px;
    font-weight: bold;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}

/* ─── App Title (Home) ───────────────────────────────────────────────────── */
QLabel#AppTitle {
    font-size: 42px;
    font-weight: 800;
    color: #58a6ff;
    margin-top: 20px;
    margin-bottom: 4px;
}

QLabel#AppSubtitle {
    font-size: 15px;
    color: #8b949e;
    margin-bottom: 10px;
}

QLabel#HintLabel {
    font-size: 13px;
    color: #6e7681;
    line-height: 1.6;
}

QLabel#IpBadge {
    font-size: 13px;
    color: #4ecca3;
    background-color: #0d2b20;
    border: 1px solid #4ecca3;
    border-radius: 8px;
    padding: 6px 18px;
    margin: 6px;
}

/* ─── Screen title ───────────────────────────────────────────────────────── */
QLabel#ScreenTitle {
    font-size: 20px;
    font-weight: 700;
    color: #e6edf3;
}

QLabel#InfoLabel {
    color: #8b949e;
    font-size: 13px;
}

/* ─── Navigation cards ───────────────────────────────────────────────────── */
QPushButton#NavCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1c2333, stop:1 #161b22);
    border: 1px solid #30363d;
    border-radius: 16px;
    color: #e6edf3;
    font-size: 15px;
    font-weight: 600;
    padding: 20px;
}
QPushButton#NavCard:hover {
    border-color: #58a6ff;
    color: #58a6ff;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1c2a42, stop:1 #1c2333);
}

/* ─── Buttons ────────────────────────────────────────────────────────────── */
QPushButton {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #58a6ff;
}
QPushButton:disabled {
    color: #484f58;
    border-color: #21262d;
    background-color: #161b22;
}

QPushButton#ActionBtn {
    background-color: #1a7f64;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-weight: 600;
}
QPushButton#ActionBtn:hover { background-color: #238a6f; }

QPushButton#SecondaryBtn {
    background-color: #21262d;
    color: #58a6ff;
    border: 1px solid #30363d;
}
QPushButton#SecondaryBtn:hover { border-color: #58a6ff; }

QPushButton#BigActionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0d4a8a, stop:1 #1a7f64);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 14px;
    font-size: 16px;
    font-weight: 700;
    min-height: 44px;
}
QPushButton#BigActionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1158a8, stop:1 #238a6f);
}
QPushButton#BigActionBtn:disabled {
    background: #21262d;
    color: #484f58;
}

QPushButton#ListenBtn {
    background-color: #0d4a8a;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-weight: 600;
}
QPushButton#ListenBtn:hover { background-color: #1158a8; }
QPushButton#ListenBtn:checked {
    background-color: #6e1f1f;
}
QPushButton#ListenBtn:checked:hover { background-color: #8a2323; }

QPushButton#PlayBtn {
    background-color: #1a7f64;
    color: #ffffff;
    border: none;
    border-radius: 20px;
    min-width: 40px;
    min-height: 40px;
    max-width: 40px;
    max-height: 40px;
    font-size: 16px;
    padding: 0;
}
QPushButton#PlayBtn:hover { background-color: #238a6f; }

QPushButton#PlayBtnLg {
    background-color: #1a7f64;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 24px;
    font-weight: 600;
    font-size: 14px;
}
QPushButton#PlayBtnLg:hover { background-color: #238a6f; }
QPushButton#PlayBtnLg:disabled { background-color: #161b22; color: #484f58; }

QPushButton#BackBtn {
    background-color: transparent;
    color: #8b949e;
    border: 1px solid #30363d;
    border-radius: 6px;
    font-size: 12px;
    padding: 5px 10px;
}
QPushButton#BackBtn:hover {
    color: #e6edf3;
    border-color: #8b949e;
}

/* ─── Inputs ─────────────────────────────────────────────────────────────── */
QLineEdit#InputField, QSpinBox {
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 13px;
}
QLineEdit#InputField:focus, QSpinBox:focus {
    border-color: #58a6ff;
}

QTextEdit {
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
}

QTextEdit#LogBox {
    color: #8b949e;
    font-size: 12px;
    border: 1px solid #21262d;
}

QTextEdit#ExtractBox {
    border: 1px solid #4ecca3;
    color: #4ecca3;
    font-size: 14px;
    font-weight: 500;
}

/* ─── Progress bar ───────────────────────────────────────────────────────── */
QProgressBar#RecBar {
    background-color: #21262d;
    border: none;
    border-radius: 4px;
    height: 6px;
}
QProgressBar#RecBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #58a6ff, stop:1 #4ecca3);
    border-radius: 4px;
}

/* ─── Scrollbars ─────────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #0d1117;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover { background: #58a6ff; }

QLabel {
    color: #8b949e;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CryptoWave")
    app.setStyleSheet(STYLE)

    window = MainWindow()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
