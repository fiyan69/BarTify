"""
Taskbar Lyrics Overlay Window using PyQt6.
Features frameless translucent rendering, hover fade, and karaoke progress bar.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QLinearGradient
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFrame,
    QLabel,
    QProgressBar,
    QMenu,
    QApplication,
    QSystemTrayIcon,
)

from ..utils.windows_api import get_taskbar_rect, set_click_through, is_taskbar_autohide


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
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Seamless container frame blending directly into the Windows taskbar
        self.container = QFrame(self)
        self.container.setObjectName("Container")
        self.container.setStyleSheet("""
            QFrame#Container {
                background-color: transparent;
                border: none;
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(12, 4, 12, 2)
        layout.setSpacing(1)

        # Main active lyric label (rendered directly on taskbar)
        self.lyric_label = QLabel("🎵 BarTify Ready", self.container)
        self.lyric_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.lyric_label.setFont(font)
        self.lyric_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: transparent;
            }
        """)

        # Next line preview label
        self.next_label = QLabel("", self.container)
        self.next_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        next_font = QFont("Segoe UI", 8, QFont.Weight.Normal)
        self.next_label.setFont(next_font)
        self.next_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.60);
                background-color: transparent;
            }
        """)

        # 2px sleek progress bar at the bottom edge of taskbar
        self.progress_bar = KaraokeProgressBar(self.container)
        self.progress_bar.setFixedHeight(2)

        layout.addWidget(self.lyric_label)
        layout.addWidget(self.next_label)
        layout.addWidget(self.progress_bar)

        root_layout.addWidget(self.container)

    def reposition_to_taskbar(self, width: int = 520, height: int = 48):
        """
        Positions the overlay directly ON the Windows taskbar surface
        using DPR-scaled Win32 coordinates.
        """
        screen = QApplication.primaryScreen()
        if not screen:
            return

        s_geo = screen.geometry()
        sw = s_geo.width()
        sh = s_geo.height()
        dpr = screen.devicePixelRatio()

        tb = get_taskbar_rect()
        if tb:
            # Convert physical pixels from Win32 to Qt logical units
            logical_tb_y = int(tb[1] / dpr)
            logical_tb_h = int(tb[3] / dpr)
            overlay_h = min(height, logical_tb_h)
            overlay_y = logical_tb_y + (logical_tb_h - overlay_h) // 2
        else:
            overlay_h = height
            overlay_y = sh - 48

        overlay_w = min(width, sw - 40)
        overlay_x = (sw - overlay_w) // 2

        self.setGeometry(overlay_x, overlay_y, overlay_w, overlay_h)

    def mousePressEvent(self, event):
        """Allow dragging the overlay widget with left mouse button."""
        if event.button() == Qt.MouseButton.LeftButton and not self._click_through:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle dragging position updates."""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "_drag_pos") and not self._click_through:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

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
            self.setWindowOpacity(0.05)
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
