"""File mtime watcher for live reload of godot.log."""
from __future__ import annotations

import os


class FileWatcher:
    """Track whether a file's mtime has changed since last check."""

    def __init__(self, path: str):
        self.path = path
        self._last_mtime = self._get_mtime()

    def _get_mtime(self) -> float:
        try:
            return os.path.getmtime(self.path)
        except OSError:
            return 0.0

    def has_changed(self) -> bool:
        """Return True if the file changed since last call, and update the baseline."""
        current = self._get_mtime()
        if current != self._last_mtime:
            self._last_mtime = current
            return True
        return False

    def reset(self) -> None:
        self._last_mtime = self._get_mtime()
