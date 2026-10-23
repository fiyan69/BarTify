"""
BarTify - Main Entry Point.
Launches the PyQt6 application and initializes the BarTify controller.
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from bartify.app import BarTifyApp


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("==================================================")
    print(" 🎵 BarTify - Real-Time Taskbar Lyrics for Windows")
    print("==================================================")
    print("[*] Menginisialisasi overlay taskbar...")

    app = QApplication(sys.argv)
    app.setApplicationName("BarTify")
    app.setQuitOnLastWindowClosed(False)

    bartify = BarTifyApp()
    bartify.start()

    print("[✓] BarTify aktif! Periksa taskbar atau tray icon kamu.")
    print("[*] Putar lagu di Spotify untuk menyinkronkan lirik.")
    print("[*] Info: Bar lirik bisa kamu klik & geser (drag) ke posisi mana saja!")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
