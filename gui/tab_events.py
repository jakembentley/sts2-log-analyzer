"""Events tab: event encounter counts + choice distribution."""
from __future__ import annotations

import customtkinter as ctk

from .constants import (
    BG_PANEL, BG_CARD, FONT_BODY, FONT_SMALL,
    TEXT, TEXT_DIM, ACCENT2,
)
from .widgets import SectionLabel

_HDR = ("Event", "Times", "Top Choice", "Distribution")
_WIDTHS = (200, 60, 220, 260)


class EventsTab(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        SectionLabel(self, "Event Choices").grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")

        # Header
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=4)
        hdr.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 2))
        for i, (h, w) in enumerate(zip(_HDR, _WIDTHS)):
            ctk.CTkLabel(
                hdr, text=h, font=FONT_SMALL, text_color=TEXT_DIM,
                width=w, anchor="w",
            ).grid(row=0, column=i, padx=(8 if i == 0 else 4, 4), pady=4, sticky="w")

        self._list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)

    def load(self, stats) -> None:
        for w in self._list.winfo_children():
            w.destroy()

        if not stats.event_encounters:
            ctk.CTkLabel(
                self._list, text="No events recorded (singleplayer runs don't log EventSynchronizer).",
                font=FONT_BODY, text_color=TEXT_DIM,
            ).pack(pady=20)
            return

        for event_id, total in stats.event_encounters.most_common():
            choice_counter = stats.event_choices.get(event_id, {})
            top_choice = choice_counter.most_common(1)
            top_str = top_choice[0][0].split(".")[-1] if top_choice else "–"

            # Distribution string: "DIVE_IN: 3, LEAVE: 1"
            dist_parts = [f"{k.split('.')[-1]}: {v}" for k, v in choice_counter.most_common(3)]
            dist_str = "  |  ".join(dist_parts) if dist_parts else "–"

            row = ctk.CTkFrame(self._list, fg_color="transparent", corner_radius=4)
            row.pack(fill="x", pady=1)

            values = [
                (event_id.replace("_", " "), TEXT, _WIDTHS[0]),
                (str(total), TEXT_DIM, _WIDTHS[1]),
                (top_str.replace("_", " "), ACCENT2, _WIDTHS[2]),
                (dist_str, TEXT_DIM, _WIDTHS[3]),
            ]

            for i, (text, color, width) in enumerate(values):
                ctk.CTkLabel(
                    row, text=text, font=FONT_SMALL, text_color=color,
                    width=width, anchor="w",
                ).grid(row=0, column=i, padx=(8 if i == 0 else 4, 4), pady=3, sticky="w")
