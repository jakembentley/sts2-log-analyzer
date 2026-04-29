"""Reusable CTk widget building blocks."""
from __future__ import annotations

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .constants import (
    BG_CARD, BG_PANEL, FONT_HEADING, FONT_BODY, FONT_SMALL,
    TEXT, TEXT_DIM, ACCENT, MPL_BG, MPL_FG, MPL_GRID, MPL_BAR,
)


class StatCard(ctk.CTkFrame):
    """A small card showing a big number with a label beneath it."""

    def __init__(self, parent, title: str, value: str, color: str = TEXT, **kwargs):
        kwargs.setdefault("fg_color", BG_CARD)
        kwargs.setdefault("corner_radius", 8)
        super().__init__(parent, **kwargs)

        self._value_label = ctk.CTkLabel(
            self, text=value,
            font=("Segoe UI", 28, "bold"),
            text_color=color,
        )
        self._value_label.pack(padx=16, pady=(12, 0))

        self._title_label = ctk.CTkLabel(
            self, text=title,
            font=FONT_SMALL,
            text_color=TEXT_DIM,
        )
        self._title_label.pack(padx=16, pady=(2, 12))

    def update_value(self, value: str, color: str = TEXT) -> None:
        self._value_label.configure(text=value, text_color=color)


class BadgeLabel(ctk.CTkFrame):
    """A small pill-shaped badge with text."""

    def __init__(self, parent, text: str, color: str = ACCENT, **kwargs):
        kwargs.setdefault("fg_color", color)
        kwargs.setdefault("corner_radius", 12)
        super().__init__(parent, **kwargs)
        ctk.CTkLabel(
            self, text=text,
            font=FONT_SMALL,
            text_color=TEXT,
        ).pack(padx=8, pady=3)


class ChartFrame(ctk.CTkFrame):
    """A matplotlib Figure embedded in a CTk frame."""

    def __init__(self, parent, figsize=(8, 4), **kwargs):
        kwargs.setdefault("fg_color", BG_PANEL)
        super().__init__(parent, **kwargs)

        self.fig = Figure(figsize=figsize, facecolor=MPL_BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def clear(self) -> None:
        self.fig.clf()
        self.canvas.draw()

    def get_ax(self):
        self.fig.clf()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(MPL_BG)
        ax.tick_params(colors=MPL_FG)
        ax.xaxis.label.set_color(MPL_FG)
        ax.yaxis.label.set_color(MPL_FG)
        ax.title.set_color(MPL_FG)
        for spine in ax.spines.values():
            spine.set_edgecolor(MPL_GRID)
        ax.grid(color=MPL_GRID, linestyle="--", linewidth=0.5, alpha=0.7)
        return ax

    def redraw(self) -> None:
        self.canvas.draw()


class SectionLabel(ctk.CTkLabel):
    """A bolded section header label."""

    def __init__(self, parent, text: str, **kwargs):
        kwargs.setdefault("font", FONT_HEADING)
        kwargs.setdefault("text_color", TEXT)
        super().__init__(parent, text=text, **kwargs)


class RunRowFrame(ctk.CTkFrame):
    """A clickable row in the run list."""

    def __init__(self, parent, run_summary: dict, on_click=None, **kwargs):
        kwargs.setdefault("fg_color", BG_CARD)
        kwargs.setdefault("corner_radius", 6)
        super().__init__(parent, **kwargs)

        outcome = run_summary.get("outcome", "UNKNOWN")
        from .constants import OUTCOME_COLOR, TEXT_GOLD, FONT_MONO
        outcome_color = OUTCOME_COLOR.get(outcome, TEXT_DIM)

        # Layout: outcome badge | characters | type | acts | combats | gold
        cols = [
            (outcome, outcome_color, 60),
            (run_summary.get("characters", ""), TEXT, 200),
            (run_summary.get("run_type", ""), TEXT_DIM, 80),
            (f"A{run_summary.get('ascension', 0)}", TEXT_DIM, 40),
            (run_summary.get("acts", ""), TEXT_DIM, 200),
            (f"{run_summary.get('wins', 0)}/{run_summary.get('combats', 0)}", TEXT, 60),
            (f"{run_summary.get('gold', 0)}g", TEXT_GOLD, 60),
        ]

        for i, (text, color, width) in enumerate(cols):
            lbl = ctk.CTkLabel(
                self, text=text, font=FONT_BODY, text_color=color,
                width=width, anchor="w",
            )
            lbl.grid(row=0, column=i, padx=(8 if i == 0 else 4, 4), pady=6, sticky="w")

        if on_click:
            self.bind("<Button-1>", lambda e: on_click(run_summary))
            for widget in self.winfo_children():
                widget.bind("<Button-1>", lambda e: on_click(run_summary))

        self.bind("<Enter>", lambda e: self.configure(fg_color=BG_PANEL))
        self.bind("<Leave>", lambda e: self.configure(fg_color=BG_CARD))
