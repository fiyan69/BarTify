# BarTify 🎵

> Real-time synchronized Spotify lyrics directly on your Windows Taskbar. Sing along while working, studying, or multitasking.

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%2011%20%7C%2010-lightgrey)
![Framework](https://img.shields.io/badge/GUI-PyQt6-green)
![License](https://img.shields.io/badge/license-MIT-purple)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

---

## 🌟 Overview

**BarTify** is a lightweight, non-intrusive desktop utility engineered for Windows that renders synchronized song lyrics directly on top of the taskbar. Designed specifically for students and developers who want a seamless karaoke experience while coding or writing papers without window clutter.

Unlike conventional lyric apps that require fragile web scraping, browser cookies (`sp_dc`), or Spotify Developer API authentication, BarTify leverages native **Windows System Media Transport Controls (GSMTC)** via WinRT to monitor active playback locally with zero credential overhead.

---

## 🚀 Key Technical Highlights

1. **Native OS-Level Media Tracking (WinRT GSMTC)**:
   - Connects to Windows `GlobalSystemMediaTransportControlsSessionManager` to extract real-time media metadata, timeline positions, and playback status directly from the Spotify desktop client.
   - Interpolates timeline drift locally with high-resolution timestamps, minimizing IPC polling overhead.

2. **Custom Pure-Python LRC Synchronizer**:
   - Built from scratch without external parsing libraries.
   - Utilizes `bisect` binary search for O(log N) lyric line lookup.
   - Calculates fractional line progress (0.0 to 1.0) for smooth karaoke-style progress bars.

3. **High-Performance PyQt6 Translucent Overlay**:
   - Frameless, top-most, tool-window flags (`FramelessWindowHint`, `WindowStaysOnTopHint`, `Tool`) to prevent taskbar and Alt+Tab clutter.
   - Dynamic hover fade: automatically dims to 20% opacity when the cursor approaches, ensuring unrestricted access to Windows Start and taskbar icons.
   - Native Win32 API integration via `ctypes` for pixel-perfect taskbar coordinate calculation and optional `WS_EX_TRANSPARENT` click-through.

4. **Public & Legal Lyrics Integration**:
   - Integrates with the open-source **LRCLIB API** with intelligent title sanitization (removing `- Remastered`, `[Live]`, `(feat. ...)` tags) and fuzzy search fallbacks.

---

## 📐 System Architecture

```
+-------------------------------------------------------------------------+
|                              Windows OS                                 |
|   +-----------------------+              +--------------------------+   |
|   | Spotify Desktop App   |              | Windows Taskbar Window   |   |
|   +-----------+-----------+              +------------+-------------+   |
|               | (WinRT GSMTC Session)                 |                 |
+---------------v---------------------------------------v-----------------+
                |                                       | (Coordinates via Win32)
+---------------v---------------------------------------v-----------------+
|                           BarTify Engine                                |
|                                                                         |
|   +-----------------------+              +--------------------------+   |
|   |  WindowsMediaListener |              |   TaskbarOverlayWindow   |   |
|   |  (Async WinRT API)    |              |   (Translucent PyQt6)    |   |
|   +-----------+-----------+              +------------^-------------+   |
|               | Track Info                            | Text & Progress |
|   +-----------v-----------+              +------------+-------------+   |
|   |      BarTifyApp       | ------------>|     LRC Parser & Sync    |   |
|   |  (Central Controller) |  Timestamp   |    (Bisect Line Match)   |   |
|   +-----------+-----------+              +------------^-------------+   |
|               |                                       | Parsed Lyrics   |
|   +-----------v-----------+                           |                 |
|   |     LyricsClient      | --------------------------+                 |
|   |  (LRCLIB REST Client) |                                             |
|   +-----------------------+                                             |
+-------------------------------------------------------------------------+
```

---

## 📁 Repository Structure

```text
BarTify/
├── bartify/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── media_listener.py     # WinRT GSMTC session polling & timeline interpolation
│   │   ├── lyrics_client.py      # LRCLIB REST client with title normalization & caching
│   │   └── lrc_parser.py         # Pure-Python LRC parser and bisect synchronizer
│   ├── ui/
│   │   ├── __init__.py
│   │   └── overlay_window.py     # Frameless, translucent PyQt6 taskbar overlay
│   ├── utils/
│   │   ├── __init__.py
│   │   └── windows_api.py        # Win32 taskbar geometry detection & click-through
│   ├── __init__.py
│   ├── app.py                    # Main controller, event loop, and system tray
│   └── config.py                 # Central configuration constants
├── tests/
│   └── test_lrc_parser.py        # Unit test suite for LRC synchronization logic
├── requirements.txt              # Production dependencies
├── LICENSE                       # MIT License
├── README.md                     # Documentation
└── main.py                       # Application bootstrap entry point
```

---

## 🛠️ Installation & Setup

### Prerequisites
- **OS**: Windows 10 or Windows 11
- **Python**: Python 3.12+
- **Spotify**: Desktop client running and playing audio

### 1. Clone the Repository
```bash
git clone https://github.com/fiyan69/BarTify.git
cd BarTify
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```

---

## 🧪 Running Unit Tests

To run the automated test suite:

```bash
python -m unittest discover tests
```

---

## 🎮 Controls & Shortcuts

- **Mouse Hover**: Moving your mouse over the overlay automatically fades it to 20% opacity so you can click taskbar icons underneath.
- **Right Click**: Opens context menu to:
  - 🔄 Reload Lyrics for current song
  - ⏩ Offset +0.5s / ⏪ Offset -0.5s (adjust lyric timing)
  - ❌ Exit BarTify
- **System Tray**: Left-click or right-click the green Spotify note icon in your Windows notification tray to toggle visibility or center the overlay.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

*Authored with ❤️ by [fiyantsu](https://github.com/fiyan69)*
