"""
BarTify Modern Settings Interface.
Crafted with a clean, seamless Fluent/Spotify dark aesthetic.
Features live preview card, segmented controls, circular color swatches,
and responsive typography tuning.
"""

from typing import List, Tuple
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDialog,
    QFontComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..config import AppConfig, OverlayConfig, save_config
from ..core.i18n import get_language, set_language, tr


class TaskbarPreviewWidget(QWidget):
    """
    High-fidelity taskbar canvas preview.
    Uses QPainter directly (identical to TaskbarOverlayWindow) ensuring
    crystal-clear typography, full descenders ('g', 'y', 'p', 'q'), and zero clipping.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_text = "🎵 S'lalu ada yang bernyanyi dan berelegi"
        self.next_text = "Di balik awan hitam"
        self.font_family = "Segoe UI"
        self.font_size = 10
        self.is_bold = True
        self.color_main = QColor("#FFFFFF")
        self.color_next = QColor("#999999")
        self.color_progress = QColor("#1DB954")
        self.progress = 0.60
        self.setFixedHeight(68)

    def update_style(
        self,
        font_family: str,
        font_size: int,
        is_bold: bool,
        color_main: str,
        color_next: str,
        color_progress: str,
    ):
        self.font_family = font_family
        self.font_size = font_size
        self.is_bold = is_bold
        self.color_main = QColor(color_main)
        self.color_next = QColor(color_next)
        self.color_progress = QColor(color_progress)

        # Dynamic comfortable height based on font metrics
        f_main = QFont(font_family, font_size, QFont.Weight.Bold if is_bold else QFont.Weight.Normal)
        fm_main = QFontMetrics(f_main)
        next_size = max(7, int(font_size * 0.82))
        f_next = QFont(font_family, next_size, QFont.Weight.Normal)
        fm_next = QFontMetrics(f_next)

        h_main = fm_main.height()
        h_next = fm_next.height()
        spacing = 4
        bar_h = 3
        total_h = h_main + spacing + h_next + 6 + bar_h + 20
        self.setFixedHeight(max(70, total_h))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Draw card container
        card_rect = self.rect().adjusted(10, 0, -10, -6)
        p.setPen(QColor(255, 255, 255, 12))
        p.setBrush(QColor("#121316"))
        p.drawRoundedRect(card_rect, 8, 8)

        # Fonts
        f_main = QFont(self.font_family, self.font_size, QFont.Weight.Bold if self.is_bold else QFont.Weight.Normal)
        next_size = max(7, int(self.font_size * 0.82))
        f_next = QFont(self.font_family, next_size, QFont.Weight.Normal)

        fm_main = QFontMetrics(f_main)
        fm_next = QFontMetrics(f_next)

        h_main = fm_main.height()
        h_next = fm_next.height()
        spacing = 4
        bar_h = 3
        total_h = h_main + spacing + h_next + 6 + bar_h
        y_start = (self.height() - 6 - total_h) // 2

        x_margin = 24

        # 1. Main Lyric
        p.setFont(f_main)
        p.setPen(self.color_main)
        p.drawText(x_margin, y_start + fm_main.ascent(), self.main_text)

        # 2. Next Lyric
        p.setFont(f_next)
        p.setPen(self.color_next)
        p.drawText(x_margin, y_start + h_main + spacing + fm_next.ascent(), self.next_text)

        # 3. Karaoke Bar
        bar_y = y_start + total_h - bar_h
        bar_w = self.width() - (x_margin * 2)

        # Background track
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 28))
        p.drawRoundedRect(x_margin, bar_y, bar_w, bar_h, 1.5, 1.5)

        # Active fill
        fill_w = int(bar_w * self.progress)
        if fill_w > 0:
            p.setBrush(self.color_progress)
            p.drawRoundedRect(x_margin, bar_y, fill_w, bar_h, 1.5, 1.5)

        p.end()


class ColorSwatchButton(QWidget):
    """Minimalist circular color swatch with hex badge."""
    color_changed = pyqtSignal(str)

    def __init__(self, color_hex: str = "#FFFFFF", parent=None):
        super().__init__(parent)
        self._color_hex = color_hex
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.circle = QPushButton(self)
        self.circle.setFixedSize(22, 22)
        self.circle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.circle.clicked.connect(self._pick_color)

        self.label = QLabel(self._color_hex.upper(), self)
        self.label.setStyleSheet("color: #929298; font-size: 11px; font-weight: 500; font-family: 'Consolas', monospace;")

        layout.addWidget(self.circle)
        layout.addWidget(self.label)
        self._apply_style()

    @property
    def color_hex(self) -> str:
        return self._color_hex

    def set_color(self, hex_val: str):
        self._color_hex = hex_val
        self.label.setText(self._color_hex.upper())
        self._apply_style()

    def _apply_style(self):
        self.circle.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color_hex};
                border: 2px solid rgba(255, 255, 255, 0.18);
                border-radius: 11px;
            }}
            QPushButton:hover {{
                border: 2px solid #FFFFFF;
            }}
        """)

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color_hex), self, "Pilih Warna")
        if col.isValid():
            self.set_color(col.name())
            self.color_changed.emit(self._color_hex)


class SegmentedPillGroup(QWidget):
    """Modern segmented pill button selector for docking alignment."""
    selection_changed = pyqtSignal(str)

    def __init__(self, options: List[Tuple[str, str]], active_key: str = "left", parent=None):
        super().__init__(parent)
        self._options = options
        self._active_key = active_key
        self._buttons: dict[str, QPushButton] = {}
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        self.setStyleSheet("""
            QWidget#PillContainer {
                background-color: #16161A;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        self.setObjectName("PillContainer")

        for key, label in self._options:
            btn = QPushButton(label, self)
            btn.setFixedHeight(26)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self.set_active(k))
            self._buttons[key] = btn
            layout.addWidget(btn)

        self._refresh_styles()

    def set_active(self, key: str):
        if key in self._buttons and key != self._active_key:
            self._active_key = key
            self._refresh_styles()
            self.selection_changed.emit(self._active_key)

    def active_key(self) -> str:
        return self._active_key

    def update_labels(self, options: List[Tuple[str, str]]):
        self._options = options
        for key, label in options:
            if key in self._buttons:
                self._buttons[key].setText(label)

    def _refresh_styles(self):
        for key, btn in self._buttons.items():
            if key == self._active_key:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2D2D35;
                        color: #FFFFFF;
                        font-weight: 600;
                        font-size: 11px;
                        border: 1px solid rgba(255, 255, 255, 0.14);
                        border-radius: 6px;
                        padding: 0 12px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #7E7E86;
                        font-size: 11px;
                        border: none;
                        border-radius: 6px;
                        padding: 0 12px;
                    }
                    QPushButton:hover {
                        color: #D0D0D5;
                        background-color: rgba(255, 255, 255, 0.04);
                    }
                """)


class SliderWithBadge(QWidget):
    """Horizontal slider paired with an aesthetic value badge."""
    value_changed = pyqtSignal(float)

    def __init__(
        self,
        min_val: float,
        max_val: float,
        step: float = 1.0,
        initial_val: float = 10.0,
        unit: str = "",
        multiplier: int = 1,
        parent=None,
    ):
        super().__init__(parent)
        self._min = min_val
        self._max = max_val
        self._step = step
        self._unit = unit
        self._multiplier = multiplier

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(int(min_val * multiplier), int(max_val * multiplier))
        self.slider.setSingleStep(int(step * multiplier))
        self.slider.setValue(int(initial_val * multiplier))
        self.slider.setFixedWidth(130)

        self.badge = QLabel(self)
        self.badge.setFixedWidth(54)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.badge.setStyleSheet("color: #1DB954; font-size: 11px; font-weight: 600;")

        layout.addWidget(self.slider)
        layout.addWidget(self.badge)

        self.slider.valueChanged.connect(self._on_slider_moved)
        self._update_badge(initial_val)

    def _on_slider_moved(self, raw_val: int):
        val = raw_val / self._multiplier
        self._update_badge(val)
        self.value_changed.emit(val)

    def _update_badge(self, val: float):
        if self._multiplier > 1:
            sign = "+" if val > 0 else ""
            self.badge.setText(f"{sign}{val:.1f} {self._unit}".strip())
        else:
            self.badge.setText(f"{int(val)} {self._unit}".strip())

    def value(self) -> float:
        return self.slider.value() / self._multiplier

    def set_value(self, val: float):
        self.slider.setValue(int(val * self._multiplier))
        self._update_badge(val)


class ToggleSwitch(QWidget):
    """
    Windows 11 / Fluent styled toggle switch (dongle).
    Pill-shaped toggle with smooth Spotify green active state and crisp anti-aliased thumb.
    """
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(42, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self.update()
            self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self.update()
            self.toggled.emit(self._checked)
            event.accept()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track background
        bg_color = QColor("#1DB954") if self._checked else QColor("#28282E")
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg_color)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 11, 11)

        # Thumb
        thumb_x = self.width() - 19 if self._checked else 3
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(thumb_x, 3, 16, 16)
        p.end()


class SettingRow(QWidget):
    """Clean setting row with left-aligned title/desc and right-aligned control."""

    def __init__(self, title_key: str, desc_key: str = "", control: QWidget = None, parent=None):
        super().__init__(parent)
        self.title_key = title_key
        self.desc_key = desc_key
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.lbl_title = QLabel(tr(title_key) if title_key else "", self)
        self.lbl_title.setStyleSheet("color: #EEEEF0; font-size: 13px; font-weight: 500;")
        text_layout.addWidget(self.lbl_title)

        self.lbl_desc = None
        if desc_key:
            self.lbl_desc = QLabel(tr(desc_key), self)
            self.lbl_desc.setStyleSheet("color: #727278; font-size: 11px;")
            text_layout.addWidget(self.lbl_desc)

        layout.addLayout(text_layout)
        layout.addStretch()

        if control:
            layout.addWidget(control)

    def retranslate(self):
        if self.title_key:
            self.lbl_title.setText(tr(self.title_key))
        if self.desc_key and self.lbl_desc:
            self.lbl_desc.setText(tr(self.desc_key))


class SettingCard(QFrame):
    """Minimalist surface card grouping related configuration options."""

    def __init__(self, title_key: str, parent=None):
        super().__init__(parent)
        self.title_key = title_key
        self.rows: List[SettingRow] = []
        self.setObjectName("SettingCard")
        self.setStyleSheet("""
            QFrame#SettingCard {
                background-color: #18181C;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 10px;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 8, 0, 8)
        self.layout.setSpacing(0)

        # Section header label
        self.lbl_section = QLabel(tr(title_key).upper() if title_key else "", self)
        self.lbl_section.setStyleSheet("""
            color: #1DB954;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.5px;
            padding: 4px 14px 6px 14px;
        """)
        self.layout.addWidget(self.lbl_section)

    def add_row(self, row: SettingRow):
        if self.layout.count() > 1:
            divider = QFrame(self)
            divider.setFixedHeight(1)
            divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.04);")
            self.layout.addWidget(divider)
        self.rows.append(row)
        self.layout.addWidget(row)

    def retranslate(self):
        if self.title_key:
            self.lbl_section.setText(tr(self.title_key).upper())
        for r in self.rows:
            r.retranslate()


class SettingsDialog(QDialog):
    """
    Modern Windows 11 Fluent / Spotify-dark styled settings dialog.
    Lightweight, uncluttered, and responsive.
    """
    config_saved = pyqtSignal(object)

    def __init__(self, current_config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = current_config
        set_language(self.config.general.language)
        self.setWindowTitle(tr("app_title"))
        self.setFixedSize(500, 620)
        self._init_styles()
        self._init_ui()
        self._load_values()
        self._update_preview()

    def _init_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0F0F12;
                color: #FFFFFF;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 3px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QFontComboBox {
                background-color: #16161A;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.09);
                border-radius: 6px;
                padding: 4px 8px;
                min-height: 24px;
                min-width: 140px;
                font-size: 12px;
            }
            QFontComboBox:hover {
                border-color: rgba(255, 255, 255, 0.2);
            }
            QFontComboBox:focus {
                border-color: #1DB954;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.12);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #1DB954;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                border: none;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #1ED760;
            }
            QCheckBox {
                color: #EEEEF0;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                background-color: #16161A;
            }
            QCheckBox::indicator:hover {
                border-color: rgba(255, 255, 255, 0.35);
            }
            QCheckBox::indicator:checked {
                background-color: #1DB954;
                border-color: #1DB954;
            }
        """)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(12)

        # Scrollable Settings Container
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 4, 0)
        content_layout.setSpacing(10)

        # 1. Preview Card (Uses Canvas Painting for 100% Crisp Typography & Full Descenders)
        card_preview = SettingCard("preview_heading", content)
        self.preview_canvas = TaskbarPreviewWidget(card_preview)
        card_preview.layout.addWidget(self.preview_canvas)
        content_layout.addWidget(card_preview)

        # 2. Typography Card
        card_typo = SettingCard("card_typography", content)

        self.font_combo = QFontComboBox(self)
        self.font_combo.currentFontChanged.connect(self._update_preview)
        card_typo.add_row(SettingRow("row_font", "row_font_desc", self.font_combo))

        self.size_slider = SliderWithBadge(8, 20, step=1, initial_val=10, unit="pt")
        self.size_slider.value_changed.connect(lambda _: self._update_preview())
        card_typo.add_row(SettingRow("row_size", "row_size_desc", self.size_slider))

        self.bold_check = QCheckBox(self)
        self.bold_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bold_check.toggled.connect(self._update_preview)
        card_typo.add_row(SettingRow("row_bold", "row_bold_desc", self.bold_check))

        content_layout.addWidget(card_typo)

        # 3. Colors Card
        card_colors = SettingCard("card_colors", content)

        self.main_color_btn = ColorSwatchButton("#FFFFFF", self)
        self.main_color_btn.color_changed.connect(lambda _: self._update_preview())
        card_colors.add_row(SettingRow("row_color_main", "row_color_main_desc", self.main_color_btn))

        self.next_color_btn = ColorSwatchButton("#999999", self)
        self.next_color_btn.color_changed.connect(lambda _: self._update_preview())
        card_colors.add_row(SettingRow("row_color_next", "row_color_next_desc", self.next_color_btn))

        self.progress_color_btn = ColorSwatchButton("#1DB954", self)
        self.progress_color_btn.color_changed.connect(lambda _: self._update_preview())
        card_colors.add_row(SettingRow("row_color_bar", "row_color_bar_desc", self.progress_color_btn))

        content_layout.addWidget(card_colors)

        # 4. Docking & Layout Card
        card_layout = SettingCard("card_layout", content)

        self.pos_pills = SegmentedPillGroup([("left", tr("pos_left")), ("center", tr("pos_center")), ("right", tr("pos_right"))], "left", self)
        card_layout.add_row(SettingRow("row_position", "row_position_desc", self.pos_pills))

        self.width_slider = SliderWithBadge(260, 680, step=20, initial_val=380, unit="px")
        card_layout.add_row(SettingRow("row_width", "row_width_desc", self.width_slider))

        self.offset_slider = SliderWithBadge(-3.0, 3.0, step=0.1, initial_val=0.0, unit="s", multiplier=10)
        card_layout.add_row(SettingRow("row_offset", "row_offset_desc", self.offset_slider))

        content_layout.addWidget(card_layout)

        # 5. System Integration Card
        card_system = SettingCard("card_system", content)

        self.lang_pills = SegmentedPillGroup([("en", "English"), ("id", "Bahasa Indonesia")], self.config.general.language, self)
        self.lang_pills.selection_changed.connect(self._on_language_changed)
        card_system.add_row(SettingRow("row_language", "row_language_desc", self.lang_pills))

        self.autostart_toggle = ToggleSwitch(self.config.general.auto_start_with_spotify, self)
        card_system.add_row(SettingRow(
            "row_autostart",
            "row_autostart_desc",
            self.autostart_toggle,
        ))

        self.autohide_toggle = ToggleSwitch(self.config.general.auto_hide_when_idle, self)
        card_system.add_row(SettingRow(
            "row_autohide",
            "row_autohide_desc",
            self.autohide_toggle,
        ))

        content_layout.addWidget(card_system)

        self._cards = [card_preview, card_typo, card_colors, card_layout, card_system]

        scroll.setWidget(content)
        root_layout.addWidget(scroll)

        # 6. Modern Bottom Action Bar
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 6, 4, 2)

        self.reset_btn = QPushButton(tr("btn_reset"), self)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7A7A80;
                font-size: 12px;
                font-weight: 500;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 7px;
                padding: 7px 14px;
            }
            QPushButton:hover {
                color: #FFFFFF;
                background-color: rgba(255, 255, 255, 0.05);
                border-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(self.reset_btn)

        btn_layout.addStretch()

        self.cancel_btn = QPushButton(tr("btn_cancel"), self)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #A0A0A5;
                font-size: 12px;
                font-weight: 500;
                border: none;
                border-radius: 7px;
                padding: 7px 14px;
            }
            QPushButton:hover {
                color: #FFFFFF;
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton(tr("btn_save"), self)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: #000000;
                font-size: 12px;
                font-weight: 700;
                border: none;
                border-radius: 7px;
                padding: 7px 18px;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
        """)
        self.save_btn.clicked.connect(self._save_and_apply)
        btn_layout.addWidget(self.save_btn)

        root_layout.addLayout(btn_layout)

    def _on_language_changed(self, lang_key: str):
        set_language(lang_key)
        self._retranslate_ui()

    def _retranslate_ui(self):
        self.setWindowTitle(tr("app_title"))
        for card in self._cards:
            card.retranslate()
        self.reset_btn.setText(tr("btn_reset"))
        self.cancel_btn.setText(tr("btn_cancel"))
        self.save_btn.setText(tr("btn_save"))
        self.pos_pills.update_labels([
            ("left", tr("pos_left")),
            ("center", tr("pos_center")),
            ("right", tr("pos_right")),
        ])

    def _load_values(self):
        ov = self.config.overlay
        self.font_combo.setCurrentFont(QFont(ov.font_family))
        self.size_slider.set_value(ov.font_size)
        self.bold_check.setChecked(ov.font_bold)

        self.main_color_btn.set_color(ov.text_color)
        self.next_color_btn.set_color(ov.next_line_color)
        self.progress_color_btn.set_color(ov.progress_color)

        self.pos_pills.set_active(ov.position if ov.position in ["left", "center", "right"] else "left")
        self.width_slider.set_value(ov.width)
        self.offset_slider.set_value(ov.manual_offset)

        # System Integration & Language
        gen = self.config.general
        self.lang_pills.set_active(gen.language)
        self.autostart_toggle.setChecked(gen.auto_start_with_spotify)
        self.autohide_toggle.setChecked(gen.auto_hide_when_idle)

    def _update_preview(self):
        font_family = self.font_combo.currentFont().family()
        font_size = int(self.size_slider.value())
        is_bold = self.bold_check.isChecked()

        main_color = self.main_color_btn.color_hex
        next_color = self.next_color_btn.color_hex
        progress_color = self.progress_color_btn.color_hex

        self.preview_canvas.update_style(
            font_family=font_family,
            font_size=font_size,
            is_bold=is_bold,
            color_main=main_color,
            color_next=next_color,
            color_progress=progress_color,
        )

    def _reset_defaults(self):
        default = OverlayConfig()
        self.font_combo.setCurrentFont(QFont(default.font_family))
        self.size_slider.set_value(default.font_size)
        self.bold_check.setChecked(default.font_bold)
        self.main_color_btn.set_color(default.text_color)
        self.next_color_btn.set_color(default.next_line_color)
        self.progress_color_btn.set_color(default.progress_color)
        self.pos_pills.set_active("left")
        self.width_slider.set_value(default.width)
        self.offset_slider.set_value(default.manual_offset)
        self.autostart_toggle.setChecked(False)
        self.autohide_toggle.setChecked(True)
        self.lang_pills.set_active("en")
        set_language("en")
        self._retranslate_ui()
        self._update_preview()

    def _save_and_apply(self):
        new_overlay = OverlayConfig(
            font_family=self.font_combo.currentFont().family(),
            font_size=int(self.size_slider.value()),
            font_bold=self.bold_check.isChecked(),
            text_color=self.main_color_btn.color_hex,
            next_line_color=self.next_color_btn.color_hex,
            progress_color=self.progress_color_btn.color_hex,
            position=self.pos_pills.active_key(),
            width=int(self.width_slider.value()),
            manual_offset=self.offset_slider.value(),
        )
        self.config.overlay = new_overlay
        self.config.general.language = self.lang_pills.active_key()
        self.config.general.auto_start_with_spotify = self.autostart_toggle.isChecked()
        self.config.general.auto_hide_when_idle = self.autohide_toggle.isChecked()
        save_config(self.config)
        self.config_saved.emit(self.config)
        self.accept()
