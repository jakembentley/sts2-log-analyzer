"""Overview tab: stat cards + scrollable run list."""
from __future__ import annotations

import customtkinter as ctk

from .constants import (
    BG_DARK, BG_PANEL, BG_CARD, FONT_HEADING, FONT_BODY, FONT_SMALL,
    TEXT, TEXT_DIM, TEXT_WIN, TEXT_LOSS, TEXT_GOLD, ACCENT2, OUTCOME_COLOR,
)
from .widgets import StatCard, SectionLabel


class OverviewTab(ctk.CTkFrame):
    def __init__(self, parent, on_run_select, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_run_select = on_run_select
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # Stat cards row
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        for i in range(5):
            cards_frame.grid_columnconfigure(i, weight=1)

        self._card_runs    = StatCard(cards_frame, "Total Runs", "–")
        self._card_wins    = StatCard(cards_frame, "Wins", "–", color=TEXT_WIN)
        self._card_winrate = StatCard(cards_frame, "Win Rate", "–%")
        self._card_gold    = StatCard(cards_frame, "Total Gold", "–", color=TEXT_GOLD)
        self._card_chars   = StatCard(cards_frame, "Characters", "–")

        for i, card in enumerate((self._card_runs, self._card_wins, self._card_winrate,
                                   self._card_gold, self._card_chars)):
            card.grid(row=0, column=i, padx=4, sticky="ew")

        # Column headers
        header = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=6)
        header.grid(row=1, column=0, sticky="new", padx=12, pady=(0, 2))
        headers = [
            ("Outcome", 60), ("Characters", 200), ("Type", 80),
            ("Asc", 40), ("Acts", 200), ("W/T", 60), ("Gold", 60),
        ]
        for i, (h, w) in enumerate(headers):
            ctk.CTkLabel(
                header, text=h, font=FONT_SMALL, text_color=TEXT_DIM,
                width=w, anchor="w",
            ).grid(row=0, column=i, padx=(8 if i == 0 else 4, 4), pady=4, sticky="w")

        self.grid_rowconfigure(2, weight=1)

        # Scrollable run list
        self._run_list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._run_list.grid(row=2, column=0, sticky="nsew", padx=12, pady=4)

    def load(self, run_summaries: list[dict], stats) -> None:
        # Update stat cards
        total = stats.total_runs
        self._card_runs.update_value(str(total))
        self._card_wins.update_value(str(stats.wins), color=TEXT_WIN)
        wr = f"{stats.win_rate:.0%}" if total else "–%"
        self._card_winrate.update_value(wr)
        self._card_gold.update_value(f"{stats.total_gold:,}", color=TEXT_GOLD)
        top_chars = ", ".join(c for c, _ in stats.characters_played.most_common(3))
        self._card_chars.update_value(top_chars or "–")

        # Clear run list
        for w in self._run_list.winfo_children():
            w.destroy()

        if not run_summaries:
            ctk.CTkLabel(
                self._run_list, text="No runs found in this file.",
                font=FONT_BODY, text_color=TEXT_DIM,
            ).pack(pady=20)
            return

        for rs in run_summaries:
            row = _RunRow(self._run_list, rs, on_click=self._on_run_select)
            row.pack(fill="x", pady=2)


class _RunRow(ctk.CTkFrame):
    def __init__(self, parent, run_summary: dict, on_click=None, **kwargs):
        kwargs.setdefault("fg_color", BG_CARD)
        kwargs.setdefault("corner_radius", 6)
        super().__init__(parent, **kwargs)

        outcome = run_summary.get("outcome", "UNKNOWN")
        outcome_color = OUTCOME_COLOR.get(outcome, TEXT_DIM)

        cols = [
            (outcome, outcome_color, 60),
            (run_summary.get("characters", ""), TEXT, 200),
            (run_summary.get("run_type", ""), TEXT_DIM, 80),
            (f"A{run_summary.get('ascension', 0)}", TEXT_DIM, 40),
            (run_summary.get("acts", ""), TEXT_DIM, 200),
            (f"{run_summary.get('wins', 0)}/{run_summary.get('combats', 0)}", TEXT, 60),
            (f"{run_summary.get('gold', 0):,}g", TEXT_GOLD, 60),
        ]

        for i in range(len(cols)):
            self.grid_columnconfigure(i, weight=0)

        for i, (text, color, width) in enumerate(cols):
            lbl = ctk.CTkLabel(
                self, text=text, font=FONT_BODY, text_color=color,
                width=width, anchor="w",
            )
            lbl.grid(row=0, column=i, padx=(8 if i == 0 else 4, 4), pady=6, sticky="w")

        # Death info if applicable
        death = run_summary.get("death_monster") or run_summary.get("death_encounter")
        if death:
            ctk.CTkLabel(
                self, text=f"† {death}", font=FONT_SMALL, text_color=TEXT_LOSS,
                anchor="w",
            ).grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 4), sticky="w")

        if on_click:
            def _click(e, rs=run_summary):
                on_click(rs)
            self.bind("<Button-1>", _click)
            for w in self.winfo_children():
                w.bind("<Button-1>", _click)

        self.bind("<Enter>", lambda e: self.configure(fg_color=BG_PANEL))
        self.bind("<Leave>", lambda e: self.configure(fg_color=BG_CARD))
