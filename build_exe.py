"""
Build Script for BarTify Standalone Executable.
Generates dist/BarTify.exe using PyInstaller with full assets,
icons, windowless GUI mode, and WinRT dependencies.
"""

import os
import subprocess
import sys


def build():
    print("[BarTify Build] Starting PyInstaller build...")

    # Terminate running BarTify.exe if any to prevent Windows file lock errors
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "BarTify.exe"],
                capture_output=True,
                check=False,
            )
        except Exception:
            pass

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=BarTify",
        "--onefile",
        "--noconsole",
        "--clean",
        "--icon=assets/icon.ico",
        "--hidden-import=winrt",
        "--hidden-import=winrt.windows.media.control",
        "--hidden-import=winrt.windows.foundation",
        "--hidden-import=winrt.windows.foundation.collections",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=requests",
        "main.py",
    ]

    result = subprocess.run(args)
    if result.returncode == 0:
        exe_path = os.path.abspath("dist/BarTify.exe")
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"[BarTify Build] [✓] Build sukses!")
        print(f"[BarTify Build] [✓] Lokasi: {exe_path}")
        print(f"[BarTify Build] [✓] Ukuran: {size_mb:.2f} MB")
    else:
        print("[BarTify Build] [!] Build gagal!")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
