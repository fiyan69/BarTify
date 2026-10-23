"""
BarTify Internationalization (i18n) Module.
Provides localization support with English as default and Bahasa Indonesia option.
"""

from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # App & Window
        "app_title": "BarTify Settings",
        "preview_heading": "PREVIEW",
        "preview_main": "🎵 S'lalu ada yang bernyanyi dan berelegi",
        "preview_next": "Di balik awan hitam",

        # Typography
        "card_typography": "Typography & Scale",
        "row_font": "Font Family",
        "row_font_desc": "Select typeface installed on your system",
        "row_size": "Text Size",
        "row_size_desc": "Lyric scale on the Windows taskbar",
        "row_bold": "Bold Text",
        "row_bold_desc": "Embolden font for higher contrast",

        # Colors
        "card_colors": "Color Palette",
        "row_color_main": "Active Lyric",
        "row_color_main_desc": "Color of the line currently sung",
        "row_color_next": "Next Line",
        "row_color_next_desc": "Upcoming line preview text color",
        "row_color_bar": "Karaoke Bar",
        "row_color_bar_desc": "Progress bar tracker below the lyrics",

        # Layout & Timing
        "card_layout": "Layout & Timing",
        "row_position": "Taskbar Docking",
        "row_position_desc": "Docking alignment along Windows taskbar",
        "pos_left": "Left",
        "pos_center": "Center",
        "pos_right": "Right",
        "row_width": "Maximum Width",
        "row_width_desc": "Horizontal bounds of the lyrics area",
        "row_offset": "Sync Offset",
        "row_offset_desc": "Fine-tune timing (earlier or later)",

        # System Integration
        "card_system": "System & Language",
        "row_language": "Language",
        "row_language_desc": "Select application display language",
        "row_autostart": "Auto-Start with Spotify",
        "row_autostart_desc": "Run BarTify automatically on Windows startup",
        "row_autohide": "Auto-Hide when Idle",
        "row_autohide_desc": "Hide overlay when Spotify is paused or closed",

        # Buttons
        "btn_reset": "Reset Defaults",
        "btn_cancel": "Cancel",
        "btn_save": "Save Changes",

        # Context Menu & Tray
        "menu_settings": "⚙️ Settings",
        "menu_reset": "🔄 Reset Lyric",
        "menu_exit": "❌ Exit",
        "tray_toggle": "Show / Hide Lyrics",
        "tray_center": "Center on Taskbar",
        "tray_settings": "⚙️ Settings...",
        "tray_exit": "❌ Exit",

        # Overlay Statuses
        "status_waiting": "🎵 BarTify - Waiting for Spotify",
        "status_searching": "🔍 Searching lyrics: {title}...",
        "status_no_lyrics": "(No synced lyrics found)",
    },
    "id": {
        # App & Window
        "app_title": "Pengaturan BarTify",
        "preview_heading": "PREVIEW",
        "preview_main": "🎵 S'lalu ada yang bernyanyi dan berelegi",
        "preview_next": "Di balik awan hitam",

        # Typography
        "card_typography": "Tipografi & Skala",
        "row_font": "Jenis Font",
        "row_font_desc": "Pilih jenis huruf yang terpasang di Windows",
        "row_size": "Ukuran Teks",
        "row_size_desc": "Skala keterbacaan lirik di taskbar",
        "row_bold": "Teks Tebal (Bold)",
        "row_bold_desc": "Menebalkan font agar lebih kontras",

        # Colors
        "card_colors": "Palet Warna",
        "row_color_main": "Lirik Utama",
        "row_color_main_desc": "Warna baris yang sedang dinyanyikan",
        "row_color_next": "Baris Berikutnya",
        "row_color_next_desc": "Warna teks pratinjau bait selanjutnya",
        "row_color_bar": "Bilah Karaoke",
        "row_color_bar_desc": "Warna progress bar linier di bawah teks",

        # Layout & Timing
        "card_layout": "Tata Letak & Waktu",
        "row_position": "Posisi Taskbar",
        "row_position_desc": "Area berlabuh lirik di taskbar Windows",
        "pos_left": "Kiri",
        "pos_center": "Tengah",
        "pos_right": "Kanan",
        "row_width": "Lebar Maksimal",
        "row_width_desc": "Batas bentang horizontal teks",
        "row_offset": "Sinkronisasi Detik",
        "row_offset_desc": "Kompensasi waktu cepat/lambat lirik",

        # System Integration
        "card_system": "Sistem & Bahasa",
        "row_language": "Bahasa Antarmuka",
        "row_language_desc": "Pilih bahasa tampilan aplikasi BarTify",
        "row_autostart": "Buka Otomatis saat Spotify Dibuka",
        "row_autostart_desc": "Jalankan BarTify otomatis di latar belakang saat Windows menyala",
        "row_autohide": "Sembunyikan jika Spotify Tutup",
        "row_autohide_desc": "Sembunyikan bilah taskbar otomatis jika Spotify tidak memutar musik",

        # Buttons
        "btn_reset": "Reset Default",
        "btn_cancel": "Batal",
        "btn_save": "Simpan Pengaturan",

        # Context Menu & Tray
        "menu_settings": "⚙️ Pengaturan",
        "menu_reset": "🔄 Reset Lyric",
        "menu_exit": "❌ Keluar",
        "tray_toggle": "Tampilkan / Sembunyikan Lirik",
        "tray_center": "Posisikan ke Tengah",
        "tray_settings": "⚙️ Pengaturan...",
        "tray_exit": "❌ Keluar",

        # Overlay Statuses
        "status_waiting": "🎵 BarTify - Menunggu Spotify",
        "status_searching": "🔍 Mencari lirik: {title}...",
        "status_no_lyrics": "(Lirik sinkron tidak ditemukan)",
    },
}


_CURRENT_LANG = "en"


def set_language(lang: str):
    """Sets active language globally ('en' or 'id')."""
    global _CURRENT_LANG
    _CURRENT_LANG = lang if lang in TRANSLATIONS else "en"


def get_language() -> str:
    """Returns currently active language code."""
    return _CURRENT_LANG


def tr(key: str, **kwargs) -> str:
    """
    Translates key for the active language.
    Falls back to English if key missing in target language.
    Supports kwargs formatting e.g. tr('status_searching', title='Song')
    """
    lang_dict = TRANSLATIONS.get(_CURRENT_LANG, TRANSLATIONS["en"])
    text = lang_dict.get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text
