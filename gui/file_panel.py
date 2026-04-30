"""Left sidebar: log file list, refresh button, live reload toggle."""
from __future__ import annotations

import os
import sys
import customtkinter as ctk

from .constants import (
    SIDEBAR_WIDTH, BG_PANEL, BG_CARD, BG_HOVER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, TEXT, TEXT_DIM, ACCENT, ACCENT2,
)


def _default_logs_dir() -> str:
    """Return the platform-appropriate default log directory for STS2."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
    return os.path.join(base, "SlayTheSpire2", "logs")


DEFAULT_LOGS_DIR = _default_logs_dir()


class FilePanel(ctk.CTkFrame):
    """
    Left sidebar listing parsed log files.
    Calls `on_file_selected(LogFile)` when the user picks a file.
    Calls `on_refresh()` when refresh is requested.
    """

    def __init__(self, parent, on_file_selected, on_refresh, on_view_cache=None, on_change_folder=None, **kwargs):
        kwargs.setdefault("fg_color", BG_PANEL)
        kwargs.setdefault("width", SIDEBAR_WIDTH)
        super().__init__(parent, **kwargs)

        self._on_file_selected = on_file_selected
        self._on_refresh = on_refresh
        self._on_view_cache = on_view_cache
        self._on_change_folder = on_change_folder
        self._log_files = []
        self._selected_filename = None
        self._row_frames: dict[str, ctk.CTkFrame] = {}
        self._viewing_cache = False

        self._build()

    def _build(self) -> None:
        self._source_label_var = ctk.StringVar(value="LOG FILES")
        ctk.CTkLabel(
            self, textvariable=self._source_label_var,
            font=FONT_HEADING, text_color=TEXT,
        ).pack(pady=(16, 8), padx=12, anchor="w")

        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", width=SIDEBAR_WIDTH - 20,
        )
        self._list_frame.pack(fill="both", expand=True, padx=6, pady=4)

        # Refresh button
        ctk.CTkButton(
            self, text="↺  Refresh",
            font=FONT_BODY, fg_color=BG_CARD, hover_color=BG_HOVER,
            command=self._on_refresh,
        ).pack(fill="x", padx=8, pady=(4, 2))

        # Change folder button
        ctk.CTkButton(
            self, text="📁  Change Folder",
            font=FONT_BODY, fg_color=BG_CARD, hover_color=BG_HOVER,
            command=self._on_change_folder_click,
        ).pack(fill="x", padx=8, pady=(2, 2))

        # Cache toggle button
        self._cache_btn = ctk.CTkButton(
            self, text="⬛  View Cache",
            font=FONT_BODY, fg_color=BG_CARD, hover_color=BG_HOVER,
            command=self._toggle_cache,
        )
        self._cache_btn.pack(fill="x", padx=8, pady=(2, 2))

        # Live toggle
        self._live_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self, text="Live reload",
            font=FONT_SMALL, text_color=TEXT_DIM,
            variable=self._live_var,
            checkmark_color=ACCENT2,
            fg_color=ACCENT2,
            command=self._on_live_toggle,
        ).pack(padx=12, pady=(2, 12), anchor="w")

    def _on_live_toggle(self) -> None:
        # App's watcher will read this via is_live property
        pass

    def _toggle_cache(self) -> None:
        if self._on_view_cache:
            self._on_view_cache()

    def _on_change_folder_click(self) -> None:
        from tkinter import filedialog
        chosen = filedialog.askdirectory(title="Select STS2 log folder")
        if chosen and self._on_change_folder:
            self._on_change_folder(chosen)

    def set_viewing_cache(self, viewing: bool) -> None:
        """Update button label and header to reflect the active source."""
        self._viewing_cache = viewing
        if viewing:
            self._source_label_var.set("CACHED LOGS")
            self._cache_btn.configure(text="⬛  View Live")
        else:
            self._source_label_var.set("LOG FILES")
            self._cache_btn.configure(text="⬛  View Cache")

    @property
    def is_live(self) -> bool:
        return self._live_var.get()

    def populate(self, log_files) -> None:
        """Replace the file list with a new set of LogFile objects."""
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._row_frames.clear()
        self._log_files = log_files

        for lf in log_files:
            self._add_row(lf)

        # Auto-select the first file
        if log_files and self._selected_filename is None:
            self._select(log_files[0].filename)
        elif self._selected_filename:
            self._select(self._selected_filename)

    def _add_row(self, lf) -> None:
        is_active = lf.is_active
        label = f"● {lf.filename}" if is_active else f"○ {lf.filename}"
        size_kb = lf.size_bytes // 1024
        sub = f"{len(lf.runs)} run{'s' if len(lf.runs) != 1 else ''}  {size_kb} KB"

        frame = ctk.CTkFrame(
            self._list_frame, fg_color="transparent", corner_radius=6,
        )
        frame.pack(fill="x", padx=2, pady=2)

        ctk.CTkLabel(
            frame, text=label, font=FONT_SMALL,
            text_color=ACCENT2 if is_active else TEXT,
            anchor="w", wraplength=SIDEBAR_WIDTH - 30,
        ).pack(fill="x", padx=6, pady=(4, 0))

        ctk.CTkLabel(
            frame, text=sub, font=("Segoe UI", 9),
            text_color=TEXT_DIM, anchor="w",
        ).pack(fill="x", padx=6, pady=(0, 4))

        frame.bind("<Button-1>", lambda e, f=lf: self._select(f.filename))
        for child in frame.winfo_children():
            child.bind("<Button-1>", lambda e, f=lf: self._select(f.filename))

        frame.bind("<Enter>", lambda e, fr=frame: fr.configure(fg_color=BG_CARD))
        frame.bind("<Leave>", lambda e, fr=frame, fn=lf.filename: fr.configure(
            fg_color=BG_HOVER if fn == self._selected_filename else "transparent"
        ))

        self._row_frames[lf.filename] = frame

    def _select(self, filename: str) -> None:
        # Deselect old
        if self._selected_filename and self._selected_filename in self._row_frames:
            self._row_frames[self._selected_filename].configure(fg_color="transparent")

        self._selected_filename = filename

        # Highlight new
        if filename in self._row_frames:
            self._row_frames[filename].configure(fg_color=BG_HOVER)

        # Notify app
        for lf in self._log_files:
            if lf.filename == filename:
                self._on_file_selected(lf)
                break
