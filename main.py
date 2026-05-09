"""
main.py — Audio Steganography entry point
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase, QFont
from gui import MainWindow, get_style


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Steganography")
    
    # Initial style application
    app.setStyleSheet(get_style(900, 700))

    window = MainWindow()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
