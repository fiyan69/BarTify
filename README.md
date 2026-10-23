# BarTify 🎵

> Real-time synchronized Spotify lyrics directly on your Windows Taskbar. Sing along while working, studying, or multitasking.

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%2011%20%7C%2010-lightgrey)
![Framework](https://img.shields.io/badge/GUI-PyQt6-green)
![License](https://img.shields.io/badge/license-MIT-purple)

---

## 🌟 Overview

**BarTify** is a lightweight, non-intrusive desktop utility that displays synchronized song lyrics right above the Windows taskbar. By interfacing directly with Windows' native **Global System Media Transport Controls (GSMTC)**, BarTify tracks Spotify playback in real time without requiring login credentials, developer tokens, or brittle cookie extraction.

## 🚀 Key Features

- **Native Windows Media Integration**: Uses Windows Runtime WinRT APIs to listen to playback state and timeline without third-party web tokens.
- **Accurate Realtime Lyrics**: Fetches synchronized LRC lyrics from open, community-driven lyrics providers (LRCLIB).
- **Non-Intrusive Taskbar Docking**: Seamlessly floats on top of the taskbar with smooth fade / click-through on hover.
- **Pure & Lightweight**: Clean modular Python architecture with minimal dependencies.

## 📐 Architecture

```
BarTify/
├── bartify/
│   ├── core/
│   │   ├── media_listener.py   # Windows WinRT GSMTC session listener
│   │   ├── lyrics_client.py    # LRCLIB API client
│   │   └── lrc_parser.py       # Timestamp parser & line matcher
│   ├── ui/
│   │   └── overlay_window.py   # Transparent PyQt6 taskbar overlay
│   └── utils/
├── requirements.txt
└── main.py                     # Application entry point
```

## 🛠️ Installation

```bash
git clone https://github.com/fiyan69/BarTify.git
cd BarTify
pip install -r requirements.txt
```

---

*Authored with ❤️ by [fiyantsu](https://github.com/fiyan69)*
