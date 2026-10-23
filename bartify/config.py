"""
BarTify Configuration.
Centralized settings for overlay appearance, polling rates, and provider endpoints.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

CONFIG_FILE_PATH = Path(__file__).resolve().parent.parent / "config.json"


@dataclass
class OverlayConfig:
    font_family: str = "Segoe UI"
    font_size: int = 10
    font_bold: bool = True
    text_color: str = "#FFFFFF"
    next_line_color: str = "#999999"
    progress_color: str = "#1DB954"
    position: str = "left"  # "left", "center", "right"
    width: int = 380
    height: int = 48
    manual_offset: float = 0.0


@dataclass
class AppConfig:
    target_media_app: str = "spotify"
    overlay: OverlayConfig = field(default_factory=OverlayConfig)


def load_config() -> AppConfig:
    """Loads configuration from config.json, returning default if file doesn't exist."""
    if not CONFIG_FILE_PATH.exists():
        return AppConfig()

    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            overlay_data = data.get("overlay", {})
            valid_keys = OverlayConfig.__annotations__.keys()
            filtered_overlay = {k: v for k, v in overlay_data.items() if k in valid_keys}
            return AppConfig(
                target_media_app=data.get("target_media_app", "spotify"),
                overlay=OverlayConfig(**filtered_overlay),
            )
    except Exception:
        return AppConfig()


def save_config(config: AppConfig) -> bool:
    """Saves configuration to config.json."""
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(config), f, indent=2)
        return True
    except Exception:
        return False
