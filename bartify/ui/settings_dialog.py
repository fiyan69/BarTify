"""
BarTify Settings GUI Dialog.
Provides a user-friendly dark-themed settings panel with live preview,
font selection, color picker, layout presets, and config persistence.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFontComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ..config import AppConfig, OverlayConfig, save_config


class ColorPickerButton(QPushButton):
    """Button displaying a color preview swatch and opening QColorDialog on click."""
    color_changed = pyqtSignal(str)

    def __init__(self, initial_hex: str = "#FFFFFF", parent=None):
        super().__init__(parent)
        self._color_hex = initial_hex
        self.setFixedHeight(30)
        self.clicked.connect(self._pick_color)
        self._update_style()

    @property
    def color_hex(self) -> str:
        return self._color_hex

    def set_color(self, hex_val: str):
        self._color_hex = hex_val
        self._update_style()

    def _update_style(self):
        self.setText(self._color_hex.upper())
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color_hex};
                color: {'#000000' if QColor(self._color_hex).lightness() > 140 else '#FFFFFF'};
                font-weight: bold;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                border: 2px solid #1DB954;
            }}
        """)

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color_hex), self, "Pilih Warna")
        if color.isValid():
            self._color_hex = color.name()
            self._update_style()
            self.color_changed.emit(self._color_hex)


class SettingsDialog(QDialog):
    """Settings dialog for user-friendly configuration of fonts, colors, and layout."""

    config_saved = pyqtSignal(object)  # Emits AppConfig

    def __init__(self, current_config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = current_config
        self.setWindowTitle("BarTify - Pengaturan Tampilan & Lirik")
        self.setFixedSize(520, 620)
        self._init_window()
        self._init_ui()
        self._load_values()
        self._update_preview()

    def _init_window(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                border: 1px solid #282828;
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 14px;
                font-weight: bold;
                color: #1DB954;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 12px;
            }
            QComboBox, QFontComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #242424;
                color: #FFFFFF;
                border: 1px solid #3E3E3E;
                border-radius: 5px;
                padding: 5px 8px;
                min-height: 22px;
            }
            QComboBox:focus, QFontComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #1DB954;
            }
            QCheckBox {
                color: #E0E0E0;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #555555;
                background-color: #242424;
            }
            QCheckBox::indicator:checked {
                background-color: #1DB954;
                border-color: #1DB954;
            }
            QPushButton#SaveBtn {
                background-color: #1DB954;
                color: #000000;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton#SaveBtn:hover {
                background-color: #1ed760;
            }
            QPushButton#ResetBtn {
                background-color: #282828;
                color: #E0E0E0;
                border: 1px solid #3E3E3E;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton#ResetBtn:hover {
                background-color: #333333;
            }
        """)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # 1. Live Preview Panel
        preview_group = QGroupBox("Pratinjau Langsung (Live Preview)", self)
        p_layout = QVBoxLayout(preview_group)

        self.preview_box = QFrame(self)
        self.preview_box.setStyleSheet("background-color: #181818; border-radius: 8px; border: 1px solid #333333;")
        self.preview_box.setFixedHeight(54)
        pb_layout = QVBoxLayout(self.preview_box)
        pb_layout.setContentsMargins(12, 4, 12, 4)
        pb_layout.setSpacing(2)
        pb_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.preview_main_label = QLabel("Look at the stars, look how they shine for you", self.preview_box)
        self.preview_next_label = QLabel("And everything you do", self.preview_box)
        self.preview_bar = QProgressBar(self.preview_box)
        self.preview_bar.setFixedHeight(3)
        self.preview_bar.setTextVisible(False)
        self.preview_bar.setRange(0, 100)
        self.preview_bar.setValue(55)

        pb_layout.addWidget(self.preview_main_label)
        pb_layout.addWidget(self.preview_next_label)
        pb_layout.addWidget(self.preview_bar)

        p_layout.addWidget(self.preview_box)
        main_layout.addWidget(preview_group)

        # 2. Typography Group
        font_group = QGroupBox("Tipografi & Ukuran Teks", self)
        f_layout = QGridLayout(font_group)
        f_layout.setSpacing(10)

        f_layout.addWidget(QLabel("Jenis Font:"), 0, 0)
        self.font_combo = QFontComboBox(self)
        self.font_combo.currentFontChanged.connect(self._update_preview)
        f_layout.addWidget(self.font_combo, 0, 1)

        f_layout.addWidget(QLabel("Ukuran Font (pt):"), 1, 0)
        self.size_spin = QSpinBox(self)
        self.size_spin.setRange(8, 22)
        self.size_spin.valueChanged.connect(self._update_preview)
        f_layout.addWidget(self.size_spin, 1, 1)

        self.bold_check = QCheckBox("Gunakan Teks Tebal (Bold)", self)
        self.bold_check.toggled.connect(self._update_preview)
        f_layout.addWidget(self.bold_check, 2, 0, 1, 2)

        main_layout.addWidget(font_group)

        # 3. Colors Group
        color_group = QGroupBox("Kustomisasi Warna", self)
        c_layout = QGridLayout(color_group)
        c_layout.setSpacing(10)

        c_layout.addWidget(QLabel("Warna Lirik Aktif:"), 0, 0)
        self.main_color_btn = ColorPickerButton("#FFFFFF", self)
        self.main_color_btn.color_changed.connect(lambda _: self._update_preview())
        c_layout.addWidget(self.main_color_btn, 0, 1)

        c_layout.addWidget(QLabel("Warna Baris Berikutnya:"), 1, 0)
        self.next_color_btn = ColorPickerButton("#999999", self)
        self.next_color_btn.color_changed.connect(lambda _: self._update_preview())
        c_layout.addWidget(self.next_color_btn, 1, 1)

        c_layout.addWidget(QLabel("Warna Karaoke Bar:"), 2, 0)
        self.progress_color_btn = ColorPickerButton("#1DB954", self)
        self.progress_color_btn.color_changed.connect(lambda _: self._update_preview())
        c_layout.addWidget(self.progress_color_btn, 2, 1)

        main_layout.addWidget(color_group)

        # 4. Layout & Position Group
        layout_group = QGroupBox("Tata Letak Taskbar & Sinkronisasi", self)
        l_layout = QGridLayout(layout_group)
        l_layout.setSpacing(10)

        l_layout.addWidget(QLabel("Posisi Taskbar:"), 0, 0)
        self.pos_combo = QComboBox(self)
        self.pos_combo.addItems(["Left (Samping Kiri)", "Center (Tengah)", "Right (Samping Kanan)"])
        l_layout.addWidget(self.pos_combo, 0, 1)

        l_layout.addWidget(QLabel("Lebar Maksimal (px):"), 1, 0)
        self.width_spin = QSpinBox(self)
        self.width_spin.setRange(250, 900)
        self.width_spin.setSingleStep(20)
        l_layout.addWidget(self.width_spin, 1, 1)

        l_layout.addWidget(QLabel("Timing Offset (detik):"), 2, 0)
        self.offset_spin = QDoubleSpinBox(self)
        self.offset_spin.setRange(-5.0, 5.0)
        self.offset_spin.setSingleStep(0.1)
        self.offset_spin.setDecimals(1)
        l_layout.addWidget(self.offset_spin, 2, 1)

        main_layout.addWidget(layout_group)

        # 5. Bottom Buttons
        btn_layout = QHBoxLayout()
        self.reset_btn = QPushButton("🔄 Reset Default", self)
        self.reset_btn.setObjectName("ResetBtn")
        self.reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(self.reset_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton("💾 Simpan Pengaturan", self)
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.clicked.connect(self._save_and_apply)
        btn_layout.addWidget(self.save_btn)

        main_layout.addLayout(btn_layout)

    def _load_values(self):
        ov = self.config.overlay
        self.font_combo.setCurrentFont(QFont(ov.font_family))
        self.size_spin.setValue(ov.font_size)
        self.bold_check.setChecked(ov.font_bold)

        self.main_color_btn.set_color(ov.text_color)
        self.next_color_btn.set_color(ov.next_line_color)
        self.progress_color_btn.set_color(ov.progress_color)

        pos_map = {"left": 0, "center": 1, "right": 2}
        self.pos_combo.setCurrentIndex(pos_map.get(ov.position, 0))
        self.width_spin.setValue(ov.width)
        self.offset_spin.setValue(ov.manual_offset)

    def _update_preview(self):
        font_family = self.font_combo.currentFont().family()
        font_size = self.size_spin.value()
        is_bold = self.bold_check.isChecked()

        main_color = self.main_color_btn.color_hex
        next_color = self.next_color_btn.color_hex
        progress_color = self.progress_color_btn.color_hex

        # Update Main Label
        font = QFont(font_family, font_size, QFont.Weight.Bold if is_bold else QFont.Weight.Normal)
        self.preview_main_label.setFont(font)
        self.preview_main_label.setStyleSheet(f"color: {main_color}; background: transparent;")

        # Update Next Label
        next_size = max(7, int(font_size * 0.82))
        next_font = QFont(font_family, next_size, QFont.Weight.Normal)
        self.preview_next_label.setFont(next_font)
        self.preview_next_label.setStyleSheet(f"color: {next_color}; background: transparent;")

        # Proportional tight heights
        fm_main = QFontMetrics(font)
        fm_next = QFontMetrics(next_font)
        self.preview_main_label.setFixedHeight(fm_main.height())
        self.preview_next_label.setFixedHeight(fm_next.height())

        # Update Progress Bar
        self.preview_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255, 255, 255, 0.12);
                border: none;
                border-radius: 1px;
            }}
            QProgressBar::chunk {{
                background-color: {progress_color};
                border-radius: 1px;
            }}
        """)

    def _reset_defaults(self):
        default = OverlayConfig()
        self.font_combo.setCurrentFont(QFont(default.font_family))
        self.size_spin.setValue(default.font_size)
        self.bold_check.setChecked(default.font_bold)
        self.main_color_btn.set_color(default.text_color)
        self.next_color_btn.set_color(default.next_line_color)
        self.progress_color_btn.set_color(default.progress_color)
        self.pos_combo.setCurrentIndex(0)
        self.width_spin.setValue(default.width)
        self.offset_spin.setValue(default.manual_offset)
        self._update_preview()

    def _save_and_apply(self):
        pos_list = ["left", "center", "right"]
        selected_pos = pos_list[self.pos_combo.currentIndex()]

        new_overlay = OverlayConfig(
            font_family=self.font_combo.currentFont().family(),
            font_size=self.size_spin.value(),
            font_bold=self.bold_check.isChecked(),
            text_color=self.main_color_btn.color_hex,
            next_line_color=self.next_color_btn.color_hex,
            progress_color=self.progress_color_btn.color_hex,
            position=selected_pos,
            width=self.width_spin.value(),
            manual_offset=self.offset_spin.value(),
        )
        self.config.overlay = new_overlay
        save_config(self.config)
        self.config_saved.emit(self.config)
        self.accept()
