"""
Main application controller for BarTify.
Coordinates media listening, lyric fetching (in background thread), and UI overlay updates.
"""

import asyncio
import logging
import threading
import time
from typing import Optional

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .config import AppConfig, load_config, save_config
from .core.lrc_parser import ParsedLyrics
from .core.lyrics_client import LyricsClient
from .core.media_listener import MediaTrack, WindowsMediaListener
from .ui.overlay_window import TaskbarOverlayWindow
from .utils.windows_api import trim_process_memory

logger = logging.getLogger("BarTify.App")


class MediaPollerThread(QThread):
    """
    Dedicated background worker thread for querying Windows WinRT GSMTC.
    Emits track snapshots safely across thread boundaries via Qt Signals.
    """
    track_updated = pyqtSignal(object)

    def __init__(self, media_listener: WindowsMediaListener):
        super().__init__()
        self.media_listener = media_listener
        self._running = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self._running:
            try:
                track = loop.run_until_complete(self.media_listener.get_current_track())
                self.track_updated.emit(track)
            except Exception as e:
                logger.debug(f"Media polling worker exception: {e}")

            time.sleep(0.7)

        loop.close()

    def stop(self):
        self._running = False
        self.wait(1000)


class BarTifyApp(QObject):
    """Central controller managing BarTify's lifecycle, threads, and UI synchronization."""

    lyrics_loaded_signal = pyqtSignal(object)  # Emits ParsedLyrics or None

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.media_listener = WindowsMediaListener(target_app_keyword="spotify")
        self.lyrics_client = LyricsClient()
        self.overlay = TaskbarOverlayWindow()
        self.overlay.apply_config(self.config)

        self.current_track: Optional[MediaTrack] = None
        self.current_lyrics: Optional[ParsedLyrics] = None
        self.manual_offset: float = self.config.overlay.manual_offset
        self._fetching_track_id: Optional[str] = None

        # Dedicated WinRT Poller Thread
        self.poller_thread = MediaPollerThread(self.media_listener)
        self.poller_thread.track_updated.connect(self._on_track_polled)

        # Setup Signals
        self.lyrics_loaded_signal.connect(self._on_lyrics_loaded)
        self.overlay.offset_changed.connect(self._adjust_offset)
        self.overlay.reload_requested.connect(self._force_reload_lyrics)
        self.overlay.settings_requested.connect(self._open_settings_dialog)

        # Timers
        # 1. Fast UI Render Timer (every 50ms = 20 FPS for smooth progress bar and line updates)
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._render_tick)

        # 2. Periodic memory optimization timer (every 60s)
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(trim_process_memory)
        self.cleanup_timer.start(60000)

        self._init_tray_icon()

    def _create_tray_icon_pixmap(self) -> QPixmap:
        """Generates a clean programmatic Spotify-green musical note tray icon."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#1DB954"))
        painter.setPen(QColor("#1DB954"))
        painter.drawEllipse(2, 2, 28, 28)
        painter.setPen(QColor("#FFFFFF"))
        font = painter.font()
        font.setPixelSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x0084, "♫")  # AlignCenter
        painter.end()
        return pixmap

    def _init_tray_icon(self):
        """Initializes the Windows system tray icon and context menu."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(self._create_tray_icon_pixmap()))
        self.tray_icon.setToolTip("BarTify - Taskbar Lyrics")

        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #1DB954;
            }
        """)

        toggle_act = QAction("Toggle Overlay Visibility", self)
        toggle_act.triggered.connect(lambda: self.overlay.setVisible(not self.overlay.isVisible()))
        tray_menu.addAction(toggle_act)

        settings_act = QAction("⚙️ Pengaturan Tampilan & Font...", self)
        settings_act.triggered.connect(self._open_settings_dialog)
        tray_menu.addAction(settings_act)

        tray_menu.addSeparator()

        snap_left_act = QAction("📌 Dock to Left (Default)", self)
        snap_left_act.triggered.connect(lambda: self.overlay.reposition_to_taskbar("left"))
        tray_menu.addAction(snap_left_act)

        snap_center_act = QAction("📌 Dock to Center", self)
        snap_center_act.triggered.connect(lambda: self.overlay.reposition_to_taskbar("center"))
        tray_menu.addAction(snap_center_act)

        snap_right_act = QAction("📌 Dock to Right", self)
        snap_right_act.triggered.connect(lambda: self.overlay.reposition_to_taskbar("right"))
        tray_menu.addAction(snap_right_act)

        tray_menu.addSeparator()

        quit_act = QAction("Quit BarTify", self)
        quit_act.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_act)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _open_settings_dialog(self):
        """Opens the Settings GUI dialog (lazy-loaded to keep base RAM footprint low)."""
        from .ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.config)
        dialog.config_saved.connect(self._on_config_saved)
        dialog.exec()
        trim_process_memory()

    def _on_config_saved(self, new_config: AppConfig):
        """Applies newly saved settings immediately to the active overlay."""
        self.config = new_config
        self.manual_offset = new_config.overlay.manual_offset
        self.overlay.apply_config(self.config)
        print("[BarTify] [✓] Pengaturan tampilan berhasil diperbarui!")

    def start(self):
        """Starts the application timers, worker thread, and displays the overlay."""
        self.overlay.show()
        self.render_timer.start(50)
        self.poller_thread.start()
        # Initial memory trim after GUI structures have loaded
        QTimer.singleShot(1500, trim_process_memory)

    def _quit_app(self):
        self.poller_thread.stop()
        QApplication.instance().quit()

    def _on_track_polled(self, track: Optional[MediaTrack]):
        """Slot running on the Main Thread handling media state changes."""
        if track:
            track_key = f"{track.artist} - {track.title}"
            old_key = f"{self.current_track.artist} - {self.current_track.title}" if self.current_track else None

            self.current_track = track

            if track_key != old_key:
                print(f"[Spotify] 🎵 Lagu terdeteksi: {track.artist} - {track.title}")
                self.manual_offset = self.config.overlay.manual_offset
                self._trigger_lyrics_fetch(track)
        else:
            self.current_track = None

    def _trigger_lyrics_fetch(self, track: MediaTrack):
        """Dispatches lyrics retrieval to a daemon thread to avoid blocking the GUI."""
        track_id = f"{track.artist}::{track.title}"
        if self._fetching_track_id == track_id:
            return

        self._fetching_track_id = track_id
        self.current_lyrics = None

        # Main-thread safe UI update
        self.overlay.update_lyrics_display(
            f"🔍 Mencari lirik: {track.title}...",
            track.artist,
            0.0,
        )

        def worker():
            lyrics = self.lyrics_client.get_lyrics(
                title=track.title,
                artist=track.artist,
                album=track.album,
                duration=track.duration_seconds,
            )
            self.lyrics_loaded_signal.emit(lyrics)

        threading.Thread(target=worker, daemon=True).start()

    def _on_lyrics_loaded(self, lyrics: Optional[ParsedLyrics]):
        self.current_lyrics = lyrics
        if lyrics:
            print(f"[LRCLIB] [✓] Berhasil memuat lirik: {len(lyrics)} baris.")
        else:
            print("[LRCLIB] [!] Lirik tidak ditemukan di database.")
            if self.current_track:
                self.overlay.update_lyrics_display(
                    f"🎵 {self.current_track.title}",
                    f"{self.current_track.artist} (No synced lyrics found)",
                    0.0,
                )
        self._fetching_track_id = None
        # Clean up temporary strings and network buffers
        trim_process_memory()

    def _render_tick(self):
        """Called every 50ms to update the current line and progress bar."""
        # Continuously keep overlay visible and atop Windows taskbar
        if not self.overlay.isVisible():
            self.overlay.show()
        self.overlay.raise_()

        if not self.current_track:
            self.overlay.update_lyrics_display("🎵 BarTify - Menunggu Spotify", "", 0.0)
            return

        if not self.current_track.is_playing:
            return

        if not self.current_lyrics or self.current_lyrics.is_empty():
            return

        pos = self.current_track.current_position + self.manual_offset
        current_line = self.current_lyrics.get_current_line(pos)
        progress = self.current_lyrics.get_line_progress(pos)

        # Look up next line preview
        idx = self.current_lyrics.get_current_line_index(pos)
        next_text = ""
        if idx is not None and idx + 1 < len(self.current_lyrics.lines):
            next_text = self.current_lyrics.lines[idx + 1].text

        current_text = current_line.text if current_line else "♪"
        self.overlay.update_lyrics_display(current_text, next_text, progress)

    def _adjust_offset(self, delta: float):
        self.manual_offset += delta
        print(f"[BarTify] [⏱] Offset lirik disesuaikan: {self.manual_offset:+.1f}s")

    def _force_reload_lyrics(self):
        if self.current_track:
            self._trigger_lyrics_fetch(self.current_track)
