"""Local log cache — copies live log files to ~/.sts2-analyzer-cache/ as backup."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

CACHE_DIR = Path.home() / ".sts2-analyzer-cache"


def cache_file(src_path: str) -> None:
    """Copy a log file to the local cache directory (silently skips on error)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / os.path.basename(src_path)
    try:
        shutil.copy2(src_path, dst)
    except OSError:
        pass


def cache_file_if_changed(src_path: str) -> bool:
    """Copy src to cache only if absent or newer than the cached copy. Returns True if copied."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    src = Path(src_path)
    dst = CACHE_DIR / src.name
    try:
        src_mtime = src.stat().st_mtime
        if dst.exists() and dst.stat().st_mtime >= src_mtime:
            return False
        shutil.copy2(src, dst)
        return True
    except OSError:
        return False


def cache_dir() -> str:
    """Return the cache directory path as a string, creating it if needed."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return str(CACHE_DIR)


def cache_count() -> int:
    """Return the number of .log files currently in the cache."""
    try:
        return sum(1 for f in CACHE_DIR.iterdir() if f.suffix == ".log")
    except OSError:
        return 0
