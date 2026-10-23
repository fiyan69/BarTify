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

        # Strip WS_EX_APPWINDOW to avoid taskbar icon clutter
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, (style & ~WS_EX_APPWINDOW))

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


def trim_process_memory():
    """
    Releases unused pages from the process working set back to the Windows OS.
    Drastically reduces RAM usage (often drops memory footprint by over 60%).
    """
    try:
        import gc
        gc.collect()
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        psapi.EmptyWorkingSet.argtypes = [wintypes.HANDLE]
        psapi.EmptyWorkingSet.restype = wintypes.BOOL
        psapi.EmptyWorkingSet(kernel32.GetCurrentProcess())
    except Exception:
        pass


def is_spotify_running() -> bool:
    """Checks whether Spotify process (Spotify.exe) is currently active in Windows."""
    TH32CS_SNAPPROCESS = 0x00000002
    kernel32 = ctypes.windll.kernel32

    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", ctypes.c_char * 260),
        ]

    hSnapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if hSnapshot == -1:
        return False

    pe = PROCESSENTRY32()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)

    success = kernel32.Process32First(hSnapshot, ctypes.byref(pe))
    running = False
    while success:
        name = pe.szExeFile.decode("utf-8", errors="ignore").lower()
        if "spotify.exe" in name:
            running = True
            break
        success = kernel32.Process32Next(hSnapshot, ctypes.byref(pe))

    kernel32.CloseHandle(hSnapshot)
    return running


def set_windows_autostart(enable: bool) -> bool:
    """Registers or unregisters BarTify in HKCU Run to auto-start with Windows in background."""
    import sys
    import os
    import winreg

    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "BarTify"

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_READ,
        )
        if enable:
            if getattr(sys, "frozen", False):
                # Compiled executable (.exe)
                cmd = f'"{sys.executable}" --minimized'
            else:
                # Python source
                root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                main_py = os.path.join(root_dir, "main.py")
                cmd = f'"{sys.executable}" "{main_py}" --minimized'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_windows_autostart_enabled() -> bool:
    """Checks whether BarTify is currently registered in Windows autorun."""
    import winreg

    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "BarTify"

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return bool(val)
    except FileNotFoundError:
        return False
    except Exception:
        return False

