"""Combat tab: encounter win-rate table + kill leaderboard."""
from __future__ import annotations

import customtkinter as ctk

from .constants import (
    BG_DARK, BG_PANEL, BG_CARD, FONT_BODY, FONT_SMALL,
    TEXT, TEXT_DIM, TEXT_WIN, TEXT_LOSS,
)
from .widgets import SectionLabel

_HDR = ("Encounter", "Faced", "Wins", "Loss", "Win%", "Top Kill")
_WIDTHS = (220, 50, 50, 50, 60, 180)


class CombatTab(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # ---- Left: encounter table ----
        left = ctk.CTkFrame(self, fg_color=BG_PANEL)
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(8, 4), pady=8)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        SectionLabel(left, "Encounter Win Rates").grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")

        # Header row
        hdr_frame = ctk.CTkFrame(left, fg_color=BG_CARD, corner_radius=4)
        hdr_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 2))
        for i, (h, w) in enumerate(zip(_HDR, _WIDTHS)):
            ctk.CTkLabel(
                hdr_frame, text=h, font=FONT_SMALL, text_color=TEXT_DIM,
                width=w, anchor="w",
            ).grid(row=0, column=i, padx=(8 if i == 0 else 4, 4), pady=4, sticky="w")

        self._enc_list = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._enc_list.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)

        # ---- Right: kill leaderboard ----
        right = ctk.CTkFrame(self, fg_color=BG_PANEL)
        right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(4, 8), pady=8)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        SectionLabel(right, "Monster Kill Count").grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")

        self._kill_list = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self._kill_list.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

    def load(self, stats) -> None:
        self._draw_encounters(stats)
        self._draw_kills(stats)

    def _draw_encounters(self, stats) -> None:
        for w in self._enc_list.winfo_children():
            w.destroy()

        for es in stats.sorted_encounters:
            wr = es.win_rate
            wr_color = TEXT_WIN if wr >= 0.75 else (TEXT_LOSS if wr < 0.5 else TEXT)
            top_kill = es.kills.most_common(1)
            top_kill_str = top_kill[0][0] if top_kill else "–"

            row = ctk.CTkFrame(self._enc_list, fg_color="transparent", corner_radius=4)
            row.pack(fill="x", pady=1)

            values = [
                (es.encounter_id.replace("_", " "), TEXT, _WIDTHS[0]),
                (str(es.times_faced), TEXT_DIM, _WIDTHS[1]),
                (str(es.wins), TEXT_WIN, _WIDTHS[2]),
                (str(es.losses), TEXT_LOSS if es.losses else TEXT_DIM, _WIDTHS[3]),
                (f"{wr:.0%}", wr_color, _WIDTHS[4]),
                (top_kill_str, TEXT_DIM, _WIDTHS[5]),
            ]

            for i, (text, color, width) in enumerate(values):
                ctk.CTkLabel(
                    row, text=text, font=FONT_SMALL, text_color=color,
                    width=width, anchor="w",
                ).grid(row=0, column=i, padx=(8 if i == 0 else 4, 4), pady=3, sticky="w")

    def _draw_kills(self, stats) -> None:
        for w in self._kill_list.winfo_children():
            w.destroy()

        max_kills = max(stats.total_kills.values(), default=1)

        for monster, count in stats.total_kills.most_common(30):
            row = ctk.CTkFrame(self._kill_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row, text=monster.replace("_", " "),
                font=FONT_SMALL, text_color=TEXT, anchor="w", width=160,
            ).grid(row=0, column=0, padx=(4, 8), sticky="w")

            ctk.CTkProgressBar(
                row, progress_color=TEXT_WIN,
                height=8,
            ).grid(row=0, column=1, sticky="ew", padx=(0, 8))
            # Set value after packing
            prog = row.winfo_children()[-1]
            prog.set(count / max_kills)

            ctk.CTkLabel(
                row, text=str(count),
                font=FONT_SMALL, text_color=TEXT_DIM, width=40,
            ).grid(row=0, column=2, padx=4, sticky="e")
