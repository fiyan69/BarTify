"""
BarTify Configuration.
Centralized settings for overlay appearance, polling rates, and provider endpoints.
"""

from dataclasses import dataclass


@dataclass
class OverlayConfig:
    width_padding: int = 400
    height: int = 44
    font_family: str = "Segoe UI"
    font_size: int = 11
    next_line_font_size: int = 8
    accent_color: str = "#1DB954"
    text_color: str = "#FFFFFF"
    hover_opacity: float = 0.20


@dataclass
class PollingConfig:
    render_interval_ms: int = 50   # 20 FPS UI refresh
    media_poll_interval_ms: int = 1000  # Poll WinRT every 1 sec
    lyrics_request_timeout: float = 6.0


@dataclass
class AppConfig:
    target_media_app: str = "spotify"
    overlay: OverlayConfig = OverlayConfig()
    polling: PollingConfig = PollingConfig()


# Default singleton config instance
DEFAULT_CONFIG = AppConfig()
