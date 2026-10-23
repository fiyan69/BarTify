"""
Windows GSMTC (Global System Media Transport Controls) Media Listener.
Reads playback metadata and timeline directly from Windows WinRT API.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Optional

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)


@dataclass
class MediaTrack:
    """Represents a media track state snapshot."""
    title: str
    artist: str
    album: str
    duration_seconds: float
    position_seconds: float
    is_playing: bool
    sampled_at: float

    @property
    def current_position(self) -> float:
        """Returns the time-interpolated playback position in seconds."""
        if not self.is_playing:
            return self.position_seconds
        elapsed = time.time() - self.sampled_at
        interpolated = self.position_seconds + elapsed
        return min(interpolated, self.duration_seconds) if self.duration_seconds > 0 else interpolated


class WindowsMediaListener:
    """Manages listening to Windows System Media Transport Controls sessions."""

    def __init__(self, target_app_keyword: str = "spotify"):
        self.target_app_keyword = target_app_keyword.lower()
        self._manager: Optional[MediaManager] = None

    async def _ensure_manager(self) -> Optional[MediaManager]:
        """Lazily initialize and cache the MediaManager."""
        if self._manager is None:
            try:
                self._manager = await MediaManager.request_async()
            except Exception:
                self._manager = None
        return self._manager

    async def get_active_session(self):
        """Finds the target media session (defaults to Spotify)."""
        manager = await self._ensure_manager()
        if not manager:
            return None

        try:
            sessions = manager.get_sessions()
            # First priority: matching target app keyword
            for session in sessions:
                app_id = (session.source_app_user_model_id or "").lower()
                if self.target_app_keyword in app_id:
                    return session

            # Second priority: current active session if any
            return manager.get_current_session()
        except Exception:
            return None

    async def get_current_track(self) -> Optional[MediaTrack]:
        """Polls current track metadata and timeline from the active session."""
        session = await self.get_active_session()
        if not session:
            return None

        try:
            info = await session.try_get_media_properties_async()
            if not info or not info.title:
                return None

            playback = session.get_playback_info()
            timeline = session.get_timeline_properties()

            is_playing = (
                playback.playback_status == PlaybackStatus.PLAYING
                if playback
                else False
            )

            position_sec = 0.0
            duration_sec = 0.0

            if timeline:
                if timeline.position is not None:
                    base_sec = timeline.position.total_seconds()
                    # WinRT timeline position can be several seconds older than current time.
                    # Use last_updated_time to calculate true realtime position without lag.
                    if timeline.last_updated_time is not None and is_playing:
                        try:
                            now_utc = datetime.now(timezone.utc)
                            lag = (now_utc - timeline.last_updated_time).total_seconds()
                            if 0 <= lag < 15:
                                position_sec = base_sec + lag
                            else:
                                position_sec = base_sec
                        except Exception:
                            position_sec = base_sec
                    else:
                        position_sec = base_sec

                if timeline.end_time is not None:
                    duration_sec = timeline.end_time.total_seconds()

            return MediaTrack(
                title=info.title.strip(),
                artist=info.artist.strip() if info.artist else "",
                album=info.album_title.strip() if info.album_title else "",
                duration_seconds=duration_sec,
                position_seconds=position_sec,
                is_playing=is_playing,
                sampled_at=time.time(),
            )
        except Exception:
            return None
