"""
Win32 API utilities for Windows taskbar detection and window styling.
Uses Python ctypes standard library (no extra third-party binary needed).
"""

import ctypes
from ctypes import wintypes
from typing import Optional, Tuple

user32 = ctypes.windll.user32


def get_taskbar_rect() -> Optional[Tuple[int, int, int, int]]:
    """
    Finds the Windows taskbar window ('Shell_TrayWnd') and returns
    its exact screen coordinates: (x, y, width, height).
    """
    try:
        hwnd = user32.FindWindowW("Shell_TrayWnd", None)
        if not hwnd:
            return None

        rect = wintypes.RECT()
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            return (rect.left, rect.top, width, height)
    except Exception:
        pass
    return None


def set_click_through(hwnd: int, enable: bool = True) -> bool:
    """
    Toggles WS_EX_TRANSPARENT on a window so that mouse clicks
    pass straight through to underlying windows (e.g. taskbar icons).
    """
    GWL_EXSTYLE = -20
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_LAYERED = 0x00080000

    try:
        current_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if enable:
            new_style = current_style | WS_EX_TRANSPARENT | WS_EX_LAYERED
        else:
            new_style = current_style & ~WS_EX_TRANSPARENT

        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        return True
    except Exception:
        return False
