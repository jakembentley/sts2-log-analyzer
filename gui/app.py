"""Root application window."""
from __future__ import annotations

import os
import json
import time
import customtkinter as ctk

from .constants import WIN_WIDTH, WIN_HEIGHT, WIN_MIN_WIDTH, WIN_MIN_HEIGHT, BG_DARK, BG_PANEL, FONT_SMALL, TEXT_DIM
from .file_panel import FilePanel, DEFAULT_LOGS_DIR

SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".sts2-analyzer.json")
LIVE_POLL_MS = 5000


class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__()

        self.title("STS2 Log Analyzer")
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.minsize(WIN_MIN_WIDTH, WIN_MIN_HEIGHT)

        self._settings = self._load_settings()
        self._logs_dir = self._settings.get("logs_dir", DEFAULT_LOGS_DIR)
        self._current_log_file = None
        self._selected_run = None
        self._last_mtime: dict[str, float] = {}

        self._build_layout()
        self._refresh()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)   # status bar
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # Left sidebar
        self._file_panel = FilePanel(
            self,
            on_file_selected=self._on_file_selected,
            on_refresh=self._refresh,
        )
        self._file_panel.grid(row=0, column=0, sticky="nsew")

        # Main content with tabs
        self._main = ctk.CTkFrame(self, fg_color=BG_DARK)
        self._main.grid(row=0, column=1, sticky="nsew")
        self._main.grid_rowconfigure(0, weight=1)
        self._main.grid_columnconfigure(0, weight=1)

        self._tabs = ctk.CTkTabview(self._main, fg_color=BG_PANEL)
        self._tabs.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        for name in ("Overview", "Cards", "Combat", "Rewards", "Events", "Timeline"):
            self._tabs.add(name)

        # Import and instantiate each tab
        from .tab_overview import OverviewTab
        from .tab_cards import CardsTab
        from .tab_combat import CombatTab
        from .tab_rewards import RewardsTab
        from .tab_events import EventsTab
        from .tab_timeline import TimelineTab

        tab_kwargs = dict(fg_color=BG_DARK)
        self._tab_overview  = OverviewTab(self._tabs.tab("Overview"),  on_run_select=self._on_run_select, **tab_kwargs)
        self._tab_cards     = CardsTab(self._tabs.tab("Cards"),    **tab_kwargs)
        self._tab_combat    = CombatTab(self._tabs.tab("Combat"),   **tab_kwargs)
        self._tab_rewards   = RewardsTab(self._tabs.tab("Rewards"),  **tab_kwargs)
        self._tab_events    = EventsTab(self._tabs.tab("Events"),   **tab_kwargs)
        self._tab_timeline  = TimelineTab(self._tabs.tab("Timeline"), **tab_kwargs)

        for tab in (self._tab_overview, self._tab_cards, self._tab_combat,
                    self._tab_rewards, self._tab_events, self._tab_timeline):
            tab.pack(fill="both", expand=True)

        # Status bar
        self._status_var = ctk.StringVar(value="Ready")
        ctk.CTkLabel(
            self, textvariable=self._status_var,
            font=FONT_SMALL, text_color=TEXT_DIM,
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=4)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        from analyzer.parser import LogParser
        from analyzer.aggregator import aggregate

        t0 = time.perf_counter()
        log_files = LogParser().parse_directory(self._logs_dir)
        elapsed = time.perf_counter() - t0

        self._log_files = log_files
        self._file_panel.populate(log_files)

        total_runs = sum(len(lf.runs) for lf in log_files)
        self._set_status(
            f"{self._logs_dir} | {len(log_files)} files | {total_runs} runs | parsed in {elapsed:.2f}s"
        )

        # Track mtimes for live reload
        for lf in log_files:
            try:
                self._last_mtime[lf.filename] = os.path.getmtime(lf.path)
            except OSError:
                pass

    def _on_file_selected(self, log_file) -> None:
        self._current_log_file = log_file
        self._selected_run = None

        from analyzer.aggregator import aggregate, aggregate_run
        stats = aggregate([log_file])

        run_summaries = [aggregate_run(run) for run in log_file.runs]

        self._tab_overview.load(run_summaries, stats)
        self._tab_cards.load(stats, log_file.runs)
        self._tab_combat.load(stats)
        self._tab_rewards.load(stats)
        self._tab_events.load(stats)
        self._tab_timeline.load(None)  # cleared until a run is selected

        self._set_status(
            f"{log_file.filename} | {len(log_file.runs)} runs | "
            f"{log_file.size_bytes // 1024} KB | {log_file.session_timestamp}"
        )

    def _on_run_select(self, run_summary: dict) -> None:
        """Called when user clicks a run row in Overview tab."""
        if self._current_log_file is None:
            return
        run_id = run_summary.get("run_id")
        for run in self._current_log_file.runs:
            if (run.run_id or "–") == run_id:
                self._selected_run = run
                self._tab_timeline.load(run)
                self._tabs.set("Timeline")
                break

    # ------------------------------------------------------------------
    # Live reload
    # ------------------------------------------------------------------

    def _schedule_live_check(self) -> None:
        self.after(LIVE_POLL_MS, self._check_live)

    def _check_live(self) -> None:
        if not self._file_panel.is_live:
            self._schedule_live_check()
            return

        if self._current_log_file is None:
            self._schedule_live_check()
            return

        lf = self._current_log_file
        try:
            mtime = os.path.getmtime(lf.path)
        except OSError:
            self._schedule_live_check()
            return

        if mtime != self._last_mtime.get(lf.filename):
            self._last_mtime[lf.filename] = mtime
            # Re-parse just this file
            from analyzer.parser import LogParser
            updated = LogParser().parse_file(lf.path)
            # Patch into log_files list
            for i, existing in enumerate(self._log_files):
                if existing.filename == lf.filename:
                    self._log_files[i] = updated
                    break
            self._on_file_selected(updated)

        self._schedule_live_check()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _load_settings(self) -> dict:
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_settings(self) -> None:
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
        except OSError:
            pass

    def _set_status(self, msg: str) -> None:
        self._status_var.set(msg)
