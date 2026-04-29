"""Cards tab: top-20 card play bar chart + per-run acquisition list."""
from __future__ import annotations

import customtkinter as ctk

from .constants import (
    BG_DARK, BG_PANEL, BG_CARD, FONT_BODY, FONT_SMALL,
    TEXT, TEXT_DIM, ACCENT2, MPL_BAR, MPL_BG, MPL_FG, MPL_GRID,
)
from .widgets import ChartFrame, SectionLabel


class CardsTab(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Left: chart
        left = ctk.CTkFrame(self, fg_color=BG_PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        SectionLabel(left, "Most Played Cards").grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")
        self._chart = ChartFrame(left, figsize=(5, 9))
        self._chart.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        # Right: per-run acquisition list
        right = ctk.CTkFrame(self, fg_color=BG_PANEL)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        SectionLabel(right, "Cards Acquired (per run)").grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")

        self._acq_list = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self._acq_list.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

    def load(self, stats, runs) -> None:
        self._draw_chart(stats)
        self._draw_acquisitions(runs)

    def _draw_chart(self, stats) -> None:
        top = stats.top_cards
        if not top:
            self._chart.clear()
            return

        cards = [c for c, _ in top]
        counts = [n for _, n in top]

        ax = self._chart.get_ax()
        bars = ax.barh(cards[::-1], counts[::-1], color=MPL_BAR, height=0.7)
        ax.set_xlabel("Times Played", color=MPL_FG)
        ax.set_title("Top 20 Cards", color=MPL_FG, pad=8)
        for bar, count in zip(bars, counts[::-1]):
            ax.text(
                bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", ha="left", color=MPL_FG, fontsize=8,
            )
        self._chart.fig.tight_layout()
        self._chart.redraw()

    def _draw_acquisitions(self, runs) -> None:
        for w in self._acq_list.winfo_children():
            w.destroy()

        for run in runs:
            if not run.cards_acquired:
                continue

            # Run header
            chars = ", ".join(run.character_names)
            outcome = run.outcome
            from .constants import OUTCOME_COLOR
            color = OUTCOME_COLOR.get(outcome, TEXT_DIM)
            ctk.CTkLabel(
                self._acq_list,
                text=f"{chars}  [{outcome}]",
                font=FONT_BODY, text_color=color,
            ).pack(anchor="w", padx=4, pady=(8, 2))

            cards_text = "  ".join(
                c.replace("CARD.", "") for c in run.cards_acquired
            )
            ctk.CTkLabel(
                self._acq_list, text=cards_text,
                font=FONT_SMALL, text_color=TEXT_DIM,
                wraplength=400, justify="left",
            ).pack(anchor="w", padx=12, pady=(0, 4))
