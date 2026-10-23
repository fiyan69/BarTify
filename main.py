"""
BarTify - Main Entry Point.
Launches the PyQt6 application and initializes the BarTify controller.
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from bartify.app import BarTifyApp


# Robust output stream wrapper preventing Windows CP1252 UnicodeEncodeError
class SafeWriter:
    def __init__(self, stream):
        self.stream = stream

    def write(self, s):
        if self.stream is not None:
            try:
                self.stream.write(s)
            except Exception:
                try:
                    self.stream.write(s.encode("ascii", errors="replace").decode("ascii"))
                except Exception:
                    pass

    def flush(self):
        if self.stream is not None:
            try:
                self.stream.flush()
            except Exception:
                pass


if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        sys.stdout = SafeWriter(sys.stdout)
else:
    sys.stdout = SafeWriter(None)

if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        sys.stderr = SafeWriter(sys.stderr)
else:
    sys.stderr = SafeWriter(None)


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

    is_minimized = "--minimized" in sys.argv
    bartify = BarTifyApp(start_minimized=is_minimized)
    bartify.start()

    print("[✓] BarTify aktif! Periksa taskbar atau tray icon kamu.")
    print("[*] Putar lagu di Spotify untuk menyinkronkan lirik.")
    print("[*] Info: Bar lirik bisa kamu klik & geser (drag) ke posisi mana saja!")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
