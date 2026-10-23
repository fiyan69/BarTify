"""
Win32 API utilities for Windows taskbar detection and window styling.
Uses Python ctypes standard library (no extra third-party binary needed).
"""

import ctypes
from ctypes import wintypes
from typing import Optional, Tuple

user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32


class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", wintypes.LPARAM),
    ]


def is_taskbar_autohide() -> bool:
    """Checks if the Windows taskbar has 'Automatically hide the taskbar' enabled."""
    try:
        data = APPBARDATA()
        data.cbSize = ctypes.sizeof(APPBARDATA)
        # ABM_GETSTATE = 4; ABS_AUTOHIDE = 0x01
        state = shell32.SHAppBarMessage(4, ctypes.byref(data))
        return bool(state & 1)
    except Exception:
        return False


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


def make_overlay_capture_safe(hwnd: int):
    """
    Ensures the window is capture-safe (visible to Snipping Tool / screen capture)
    and stays atop without being filtered as an ephemeral tool window.
    """
    try:
        # Set Display Affinity to WDA_NONE (0) to ensure screen capture tools include it
        user32.SetWindowDisplayAffinity(hwnd, 0)

        # Ensure TopMost and NoActivate flags
        HWND_TOPMOST = -1
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010
        SWP_SHOWWINDOW = 0x0040
        user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
    except Exception:
        pass
