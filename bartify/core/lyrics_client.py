"""
LRCLIB Lyrics API Client.
Fetches synchronized .lrc lyrics with caching and search fallbacks.
"""

import logging
import re
from typing import Dict, Optional
import requests

from .lrc_parser import ParsedLyrics, parse_lrc

logger = logging.getLogger("BarTify.LyricsClient")


class LyricsClient:
    """Client for fetching synchronized lyrics from LRCLIB."""

    BASE_URL = "https://lrclib.net/api"
    USER_AGENT = "BarTify/0.1.0 (https://github.com/fiyan69/BarTify)"

    def __init__(self, timeout: float = 6.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})
        # Simple in-memory cache: (artist.lower(), title.lower()) -> Optional[ParsedLyrics]
        self._cache: Dict[str, Optional[ParsedLyrics]] = {}

    @staticmethod
    def clean_title(title: str) -> str:
        """Strips common suffixes and noise from track titles (e.g. remastered, feat)."""
        # Remove (feat. ...), (with ...), [feat. ...]
        title = re.sub(r"[\(\[](feat\.|ft\.|with).*?[\)\]]", "", title, flags=re.IGNORECASE)
        # Remove - Remastered..., - Live...
        title = re.sub(r"-\s*(remastered|live|mono|stereo|deluxe|bonus).*?$", "", title, flags=re.IGNORECASE)
        # Remove trailing parentheses with year or remaster info
        title = re.sub(r"[\(\[]\d{4}\s*remaster[\)\]]", "", title, flags=re.IGNORECASE)
        return title.strip()

    def _cache_key(self, artist: str, title: str) -> str:
        return f"{artist.strip().lower()}:::{title.strip().lower()}"

    def get_lyrics(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None,
        duration: Optional[float] = None,
    ) -> Optional[ParsedLyrics]:
        """
        Retrieves parsed synchronized lyrics for the given track.
        Uses in-memory cache, exact match, and search fallback.
        """
        if not title:
            return None

        key = self._cache_key(artist, title)
        if key in self._cache:
            return self._cache[key]

        cleaned_title = self.clean_title(title)
        lyrics = self._fetch_exact(cleaned_title, artist, album, duration)

        if not lyrics and cleaned_title != title:
            lyrics = self._fetch_exact(title, artist, album, duration)

        if not lyrics:
            # Fallback to fuzzy search
            lyrics = self._fetch_search(cleaned_title, artist)

        self._cache[key] = lyrics
        return lyrics

    def _fetch_exact(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None,
        duration: Optional[float] = None,
    ) -> Optional[ParsedLyrics]:
        """Attempts an exact match lookup via /api/get."""
        params = {
            "track_name": title,
            "artist_name": artist,
        }
        if album:
            params["album_name"] = album
        if duration and duration > 0:
            params["duration"] = int(duration)

        try:
            resp = self.session.get(
                f"{self.BASE_URL}/get", params=params, timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                synced_lrc = data.get("syncedLyrics")
                if synced_lrc:
                    parsed = parse_lrc(synced_lrc)
                    if not parsed.is_empty():
                        return parsed
        except Exception as e:
            logger.debug(f"Exact fetch failed: {e}")

        return None

    def _fetch_search(self, title: str, artist: str) -> Optional[ParsedLyrics]:
        """Fallback search query via /api/search."""
        query = f"{title} {artist}".strip()
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/search",
                params={"q": query},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                results = resp.json()
                if isinstance(results, list):
                    for item in results:
                        synced = item.get("syncedLyrics")
                        if synced:
                            parsed = parse_lrc(synced)
                            if not parsed.is_empty():
                                return parsed
        except Exception as e:
            logger.debug(f"Search fetch failed: {e}")

        return None
