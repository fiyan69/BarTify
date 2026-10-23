"""
Taskbar Lyrics Overlay Window using PyQt6.
Features frameless translucent rendering, hover fade, and karaoke progress bar.
"""

from PyQt6.QtCore import QEasingCurve, Qt, QTimer, QVariantAnimation, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QWidget,
)

from ..config import AppConfig
from ..core.i18n import tr
from ..utils.windows_api import (
    get_taskbar_rect,
    set_click_through,
    is_taskbar_autohide,
    make_overlay_capture_safe,
)


class TaskbarOverlayWindow(QWidget):
    """Floating transparent overlay displaying synced lyrics above the Windows taskbar."""

    offset_changed = pyqtSignal(float)
    reload_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, click_through: bool = False):
        super().__init__(None)
        self._click_through = click_through

        # Lyrics state
        self._current_text = "🎵 BarTify Ready"
        self._next_text = ""
        self._old_text = ""
        self._current_progress = 0.0

        # Animation state (Spotify vertical slide transition)
        self._anim_progress = 1.0  # 1.0 = idle, 0.0 -> 1.0 = in transition
        self._scroll_anim = QVariantAnimation(self)
        self._scroll_anim.setDuration(380)
        self._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._scroll_anim.valueChanged.connect(self._on_scroll_step)
        self._scroll_anim.finished.connect(self._on_scroll_finished)

        # Style defaults
        self._font_main = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self._font_next = QFont("Segoe UI", 8, QFont.Weight.Normal)
        self._color_main = QColor("#FFFFFF")
        self._color_next = QColor("#999999")
        self._color_progress = QColor("#1DB954")

        self._init_window_flags()
        self.reposition_to_taskbar()
        make_overlay_capture_safe(int(self.winId()))

    def _init_window_flags(self):
        """Sets frameless and top-most flags without ToolWindow so Snipping Tool captures it."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

    def changeEvent(self, event):
        """Prevents the overlay from remaining minimized during system state changes."""
        if event.type() == event.Type.WindowStateChange and self.isMinimized():
            self.showNormal()
        super().changeEvent(event)

    def reposition_to_taskbar(self, position: str = "left", width: int = 380, height: int = 48):
        """
        Positions the overlay directly ON the Windows taskbar surface.
        Defaults to 'left' (x = 16) to avoid colliding with centered Windows 11 icons.
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

        if position == "left":
            overlay_x = 16
        elif position == "right":
            overlay_x = sw - overlay_w - 240  # Just before system tray
        else:  # "center"
            overlay_x = (sw - overlay_w) // 2

        self.setGeometry(overlay_x, overlay_y, overlay_w, overlay_h)

    def apply_config(self, config: AppConfig):
        """Applies typography, color, and layout settings from AppConfig."""
        ov = config.overlay
        weight = QFont.Weight.Bold if ov.font_bold else QFont.Weight.Normal
        self._font_main = QFont(ov.font_family, ov.font_size, weight)

        next_size = max(7, int(ov.font_size * 0.82))
        self._font_next = QFont(ov.font_family, next_size, QFont.Weight.Normal)

        self._color_main = QColor(ov.text_color)
        self._color_next = QColor(ov.next_line_color)
        self._color_progress = QColor(ov.progress_color)

        self.reposition_to_taskbar(position=ov.position, width=ov.width, height=ov.height)
        self.update()

    def update_lyrics_display(
        self,
        current_text: str,
        next_text: str = "",
        progress: float = 0.0,
    ):
        """
        Updates lyrics and triggers Spotify-style vertical scrolling
        when moving to a new line.
        """
        clean_cur = (current_text or "♪").strip()
        clean_next = (next_text or "").strip()
        new_progress = max(0.0, min(1.0, progress))

        # Skip redraw if visual state has not noticeably changed (saves CPU & RAM churning)
        if (
            clean_cur == self._current_text
            and clean_next == self._next_text
            and abs(new_progress - self._current_progress) < 0.003
            and self._anim_progress >= 1.0
        ):
            return

        self._current_progress = new_progress

        if clean_cur != self._current_text:
            is_real_lyric = (
                not clean_cur.startswith("🎵")
                and not clean_cur.startswith("🔍")
                and not self._current_text.startswith("🎵")
                and not self._current_text.startswith("🔍")
            )
            if is_real_lyric and self._current_text:
                self._old_text = self._current_text
                self._current_text = clean_cur
                self._next_text = clean_next
                self._scroll_anim.stop()
                self._scroll_anim.setStartValue(0.0)
                self._scroll_anim.setEndValue(1.0)
                self._scroll_anim.start()
            else:
                self._old_text = ""
                self._current_text = clean_cur
                self._next_text = clean_next
                self._anim_progress = 1.0
                self.update()
        else:
            self._next_text = clean_next
            self.update()

    def _on_scroll_step(self, val: float):
        self._anim_progress = val
        self.update()

    def _on_scroll_finished(self):
        self._anim_progress = 1.0
        self._old_text = ""
        self.update()

    @staticmethod
    def _interpolate_color(c1: QColor, c2: QColor, t: float) -> QColor:
        t = max(0.0, min(1.0, t))
        r = int(c1.red() + (c2.red() - c1.red()) * t)
        g = int(c1.green() + (c2.green() - c1.green()) * t)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * t)
        a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * t)
        return QColor(r, g, b, a)

    def paintEvent(self, event):
        """Custom high-performance painter rendering lyrics, scroll animation, and progress bar."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        fm_main = QFontMetrics(self._font_main)
        fm_next = QFontMetrics(self._font_next)

        h_main = fm_main.height()
        h_next = fm_next.height()
        spacing = 3
        bar_h = 3
        total_h = h_main + spacing + h_next + 3 + bar_h
        y_start = (self.height() - total_h) // 2

        step_y = h_main + spacing
        shift = self._anim_progress * step_y if self._anim_progress < 1.0 else 0.0

        p.save()
        p.setClipRect(0, 0, self.width(), self.height() - bar_h - 2)

        x_margin = 8
        avail_w = self.width() - (x_margin * 2)

        if self._anim_progress < 1.0 and self._old_text:
            # 1. Old active line scrolling UP and fading out
            p.setFont(self._font_main)
            old_alpha = max(0.0, 1.0 - self._anim_progress)
            col_old = QColor(self._color_main)
            col_old.setAlpha(int(255 * old_alpha))
            p.setPen(col_old)
            old_y = int(y_start + fm_main.ascent() - shift)
            p.drawText(x_margin, old_y, self._old_text)

            # 2. New active line scrolling UP from next-line slot into main slot
            cur_col = self._interpolate_color(self._color_next, self._color_main, self._anim_progress)
            cur_y = int(y_start + step_y + fm_main.ascent() - shift)
            p.setFont(self._font_main if self._anim_progress > 0.4 else self._font_next)
            p.setPen(cur_col)
            p.drawText(x_margin, cur_y, self._current_text)

            # 3. Upcoming line scrolling UP into view from below
            if self._next_text:
                up_alpha = min(1.0, self._anim_progress)
                col_up = QColor(self._color_next)
                col_up.setAlpha(int(255 * up_alpha))
                p.setFont(self._font_next)
                p.setPen(col_up)
                up_y = int(y_start + step_y * 2 + fm_next.ascent() - shift)
                p.drawText(x_margin, up_y, self._next_text)
        else:
            # Steady idle state with horizontal autoscroll for wide lines
            text_w = fm_main.horizontalAdvance(self._current_text)
            scroll_x = 0
            if text_w > avail_w:
                overflow = text_w - avail_w
                scroll_x = -int(overflow * self._current_progress)

            p.setFont(self._font_main)
            p.setPen(self._color_main)
            p.drawText(x_margin + scroll_x, y_start + fm_main.ascent(), self._current_text)

            if self._next_text:
                p.setFont(self._font_next)
                p.setPen(self._color_next)
                p.drawText(x_margin, y_start + step_y + fm_next.ascent(), self._next_text)

        p.restore()

        # 4. Draw Karaoke Progress Bar
        bar_y = y_start + total_h - bar_h
        bar_w = self.width() - (x_margin * 2)

        # Background track
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 28))
        p.drawRoundedRect(x_margin, bar_y, bar_w, bar_h, 1.5, 1.5)

        # Active progress fill
        fill_w = int(bar_w * self._current_progress)
        if fill_w > 0:
            p.setBrush(self._color_progress)
            p.drawRoundedRect(x_margin, bar_y, fill_w, bar_h, 1.5, 1.5)

        p.end()

    def set_click_through_enabled(self, enable: bool):
        self._click_through = enable
        set_click_through(int(self.winId()), enable)

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

    def contextMenuEvent(self, event):
        """Context menu for quick controls."""
        if self._click_through:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #16161A;
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 14px;
                border-radius: 5px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #1DB954;
                color: #000000;
                font-weight: 600;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.08);
                margin: 4px 6px;
            }
        """)

        settings_act = menu.addAction(tr("menu_settings"))
        settings_act.triggered.connect(self.settings_requested.emit)

        reload_act = menu.addAction(tr("menu_reset"))
        reload_act.triggered.connect(self.reload_requested.emit)

        menu.addSeparator()
        quit_act = menu.addAction(tr("menu_exit"))
        quit_act.triggered.connect(QApplication.instance().quit)

        menu.exec(event.globalPos())
