"""
LRC Lyrics Parser and Synchronizer.
Parses standard .lrc format into timestamped lines with fast binary-search lookup.
"""

from bisect import bisect_right
from dataclasses import dataclass
import re
from typing import List, Optional


@dataclass
class LyricLine:
    """Represents a single timestamped line of lyrics."""
    timestamp: float  # In seconds
    text: str


class ParsedLyrics:
    """Container for parsed LRC lines with lookup and progress calculation."""

    def __init__(self, lines: List[LyricLine], offset: float = 0.0):
        self.lines = sorted(lines, key=lambda x: x.timestamp)
        self.offset = offset
        self._timestamps = [line.timestamp for line in self.lines]

    def __len__(self) -> int:
        return len(self.lines)

    def is_empty(self) -> bool:
        return len(self.lines) == 0

    def get_current_line_index(self, position_seconds: float) -> Optional[int]:
        """Finds the index of the active lyric line for the given position."""
        if not self.lines:
            return None

        adjusted_pos = position_seconds + self.offset
        idx = bisect_right(self._timestamps, adjusted_pos) - 1

        if idx < 0:
            return None
        return idx

    def get_current_line(self, position_seconds: float) -> Optional[LyricLine]:
        """Returns the currently active LyricLine."""
        idx = self.get_current_line_index(position_seconds)
        if idx is None or idx < 0 or idx >= len(self.lines):
            return None
        return self.lines[idx]

    def get_line_progress(self, position_seconds: float) -> float:
        """
        Calculates the progress of the current line from 0.0 to 1.0
        based on the gap between current line timestamp and next line timestamp.
        """
        idx = self.get_current_line_index(position_seconds)
        if idx is None or idx < 0 or idx >= len(self.lines):
            return 0.0

        current_line = self.lines[idx]
        adjusted_pos = position_seconds + self.offset

        # If it's the last line, default to 1.0 or fade over 5 seconds
        if idx + 1 >= len(self.lines):
            time_since_start = max(0.0, adjusted_pos - current_line.timestamp)
            return min(1.0, time_since_start / 5.0)

        next_line = self.lines[idx + 1]
        line_duration = next_line.timestamp - current_line.timestamp

        if line_duration <= 0.05:
            return 1.0

        progress = (adjusted_pos - current_line.timestamp) / line_duration
        return max(0.0, min(1.0, progress))


def parse_lrc(lrc_text: str) -> ParsedLyrics:
    """
    Parses a raw .lrc string into a ParsedLyrics object.
    Supports multi-timestamp lines, millisecond offsets, and metadata tags.
    """
    if not lrc_text or not lrc_text.strip():
        return ParsedLyrics([])

    tag_pattern = re.compile(r"\[([a-zA-Z]+):([^\]]*)\]")
    timestamp_pattern = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]")

    lines: List[LyricLine] = []
    global_offset = 0.0

    for raw_line in lrc_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Check for metadata tags like [offset:+/-500]
        meta_match = tag_pattern.match(line)
        if meta_match:
            tag_name, tag_val = meta_match.groups()
            if tag_name.lower() == "offset":
                try:
                    # Offset is typically in milliseconds (+/- ms)
                    global_offset = float(tag_val.strip()) / 1000.0
                except ValueError:
                    pass
            # Skip metadata lines
            if not timestamp_pattern.search(line):
                continue

        # Extract all timestamps on this line
        ts_matches = list(timestamp_pattern.finditer(line))
        if not ts_matches:
            continue

        # Extract text following the last timestamp
        last_match = ts_matches[-1]
        text = line[last_match.end():].strip()

        for match in ts_matches:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            fraction_str = match.group(3)

            fraction = 0.0
            if fraction_str:
                # Handle 2-digit (hundredths) or 3-digit (thousandths)
                fraction = float(f"0.{fraction_str}")

            total_seconds = (minutes * 60) + seconds + fraction
            lines.append(LyricLine(timestamp=total_seconds, text=text))

    return ParsedLyrics(lines=lines, offset=global_offset)
