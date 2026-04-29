"""Rewards tab: gold chart, relic badges, potion badges."""
from __future__ import annotations

import customtkinter as ctk

from .constants import (
    BG_DARK, BG_PANEL, BG_CARD, FONT_BODY, FONT_SMALL,
    TEXT, TEXT_DIM, TEXT_GOLD, ACCENT, ACCENT2, MPL_BAR, MPL_BG, MPL_FG,
)
from .widgets import ChartFrame, SectionLabel, BadgeLabel


class RewardsTab(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # Top-left: gold chart
        gold_frame = ctk.CTkFrame(self, fg_color=BG_PANEL)
        gold_frame.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=(8, 4))
        gold_frame.grid_rowconfigure(1, weight=1)
        gold_frame.grid_columnconfigure(0, weight=1)

        SectionLabel(gold_frame, "Gold per Run").grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")
        self._gold_chart = ChartFrame(gold_frame, figsize=(5, 3))
        self._gold_chart.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        # Bottom-left: relic badges
        relic_outer = ctk.CTkFrame(self, fg_color=BG_PANEL)
        relic_outer.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(4, 8))
        relic_outer.grid_rowconfigure(1, weight=1)
        relic_outer.grid_columnconfigure(0, weight=1)

        SectionLabel(relic_outer, "Relics Collected").grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")
        self._relic_scroll = ctk.CTkScrollableFrame(relic_outer, fg_color="transparent")
        self._relic_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        # Right: potion badges
        potion_outer = ctk.CTkFrame(self, fg_color=BG_PANEL)
        potion_outer.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(4, 8), pady=8)
        potion_outer.grid_rowconfigure(1, weight=1)
        potion_outer.grid_columnconfigure(0, weight=1)

        SectionLabel(potion_outer, "Potions Found").grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")
        self._potion_scroll = ctk.CTkScrollableFrame(potion_outer, fg_color="transparent")
        self._potion_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

    def load(self, stats) -> None:
        self._draw_gold(stats)
        self._draw_badges(self._relic_scroll, stats.relics_collected, ACCENT2)
        self._draw_badges(self._potion_scroll, stats.potions_collected, ACCENT)

    def _draw_gold(self, stats) -> None:
        if not stats.gold_per_run:
            self._gold_chart.clear()
            return

        labels = [f"R{i+1}" for i in range(len(stats.gold_per_run))]
        values = [g for _, g in stats.gold_per_run]

        ax = self._gold_chart.get_ax()
        bars = ax.bar(labels, values, color=TEXT_GOLD, width=0.6)
        ax.set_ylabel("Gold", color=MPL_FG)
        ax.set_title("Gold per Run", color=MPL_FG, pad=6)
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                str(val), ha="center", va="bottom", color=MPL_FG, fontsize=8,
            )
        self._gold_chart.fig.tight_layout()
        self._gold_chart.redraw()

    def _draw_badges(self, container, counter, color) -> None:
        for w in container.winfo_children():
            w.destroy()

        if not counter:
            ctk.CTkLabel(container, text="None", font=FONT_SMALL, text_color=TEXT_DIM).pack(pady=8)
            return

        flow = ctk.CTkFrame(container, fg_color="transparent")
        flow.pack(fill="both", expand=True)

        col_count = 3
        for i, (item, count) in enumerate(counter.most_common()):
            name = item.replace("_", " ")
            label = f"{name} ×{count}" if count > 1 else name
            badge = BadgeLabel(flow, text=label, color=color)
            badge.grid(row=i // col_count, column=i % col_count, padx=3, pady=3, sticky="ew")

        for c in range(col_count):
            flow.grid_columnconfigure(c, weight=1)
