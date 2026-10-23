"""
Taskbar Lyrics Overlay Window using PyQt6.
Features frameless translucent rendering, hover fade, and karaoke progress bar.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QLinearGradient
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QMenu,
    QApplication,
    QSystemTrayIcon,
)

from ..utils.windows_api import get_taskbar_rect, set_click_through


class KaraokeProgressBar(QProgressBar):
    """Custom sleek progress bar indicating the timing of the active lyric line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self.setTextVisible(False)
        self.setRange(0, 1000)
        self.setValue(0)
        self.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.15);
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #1DB954, stop: 1 #1ed760
                );
                border-radius: 1px;
            }
        """)


class TaskbarOverlayWindow(QWidget):
    """Floating transparent overlay displaying synced lyrics above the Windows taskbar."""

    offset_changed = pyqtSignal(float)
    reload_requested = pyqtSignal()

    def __init__(self, click_through: bool = False):
        super().__init__()
        self._click_through = click_through
        self._current_progress = 0.0

        self._init_window_flags()
        self._init_ui()
        self.reposition_to_taskbar()

    def _init_window_flags(self):
        """Sets frameless, tool-window (no alt-tab clutter), and top-most flags."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(2)

        # Main active lyric label
        self.lyric_label = QLabel("🎵 BarTify Ready", self)
        self.lyric_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        self.lyric_label.setFont(font)
        self.lyric_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: transparent;
            }
        """)

        # Next line preview label
        self.next_label = QLabel("", self)
        self.next_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        next_font = QFont("Segoe UI", 8, QFont.Weight.Normal)
        self.next_label.setFont(next_font)
        self.next_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.55);
                background-color: transparent;
            }
        """)

        # Progress bar
        self.progress_bar = KaraokeProgressBar(self)

        layout.addWidget(self.lyric_label)
        layout.addWidget(self.next_label)
        layout.addWidget(self.progress_bar)

    def reposition_to_taskbar(self, width_padding: int = 400):
        """
        Positions the overlay right on the taskbar.
        Leaves horizontal padding so center taskbar icons or tray aren't completely obscured.
        """
        rect = get_taskbar_rect()
        if rect:
            tb_x, tb_y, tb_w, tb_h = rect
            # Position centered or docked nicely
            overlay_w = max(400, tb_w - (width_padding * 2))
            overlay_x = tb_x + (tb_w - overlay_w) // 2
            overlay_y = tb_y + max(0, (tb_h - 44) // 2)
            self.setGeometry(overlay_x, overlay_y, overlay_w, 44)
        else:
            # Fallback to screen geometry
            screen = QApplication.primaryScreen().geometry()
            self.setGeometry(
                screen.width() // 4,
                screen.height() - 50,
                screen.width() // 2,
                44,
            )

    def update_lyrics_display(
        self,
        current_text: str,
        next_text: str = "",
        progress: float = 0.0,
    ):
        """Updates the text and karaoke progress bar."""
        self.lyric_label.setText(current_text or "♪")
        self.next_label.setText(next_text)
        self.next_label.setVisible(bool(next_text))
        self.progress_bar.setValue(int(progress * 1000))

    def set_click_through_enabled(self, enable: bool):
        self._click_through = enable
        set_click_through(int(self.winId()), enable)

    def enterEvent(self, event):
        """Auto-fade on hover so user can easily interact with taskbar underneath."""
        if not self._click_through:
            self.setWindowOpacity(0.2)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Restore full opacity when mouse leaves."""
        self.setWindowOpacity(1.0)
        super().leaveEvent(event)

    def contextMenuEvent(self, event):
        """Context menu for quick controls."""
        if self._click_through:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #1DB954;
                border-radius: 4px;
            }
        """)

        reload_act = menu.addAction("🔄 Reload Lyrics")
        reload_act.triggered.connect(self.reload_requested.emit)

        offset_plus = menu.addAction("⏩ Offset +0.5s")
        offset_plus.triggered.connect(lambda: self.offset_changed.emit(0.5))

        offset_minus = menu.addAction("⏪ Offset -0.5s")
        offset_minus.triggered.connect(lambda: self.offset_changed.emit(-0.5))

        menu.addSeparator()
        quit_act = menu.addAction("❌ Exit BarTify")
        quit_act.triggered.connect(QApplication.instance().quit)

        menu.exec(event.globalPos())
