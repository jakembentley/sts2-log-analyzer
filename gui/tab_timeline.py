"""Timeline tab: vertical narrative feed for a selected run."""
from __future__ import annotations

import customtkinter as ctk

from .constants import (
    BG_DARK, BG_PANEL, BG_CARD, FONT_BODY, FONT_SMALL,
    TEXT, TEXT_DIM, TEXT_WIN, TEXT_LOSS, TEXT_GOLD, ACCENT, ACCENT2,
    OUTCOME_COLOR,
)
from .widgets import SectionLabel

# Icon letters for each event type
_TYPE_ICONS = {
    "act":          ("◆", ACCENT2),
    "combat":       ("⚔", TEXT),
    "reward":       ("★", TEXT_GOLD),
    "event_start":  ("❓", ACCENT),
    "event_choice": ("✔", ACCENT2),
    "run_end":      ("🏁", TEXT_WIN),
}


class TimelineTab(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._header_lbl = SectionLabel(self, "Select a run in Overview to view its timeline.")
        self._header_lbl.grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

    def load(self, run) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

        if run is None:
            self._header_lbl.configure(text="Select a run in Overview to view its timeline.")
            return

        chars = ", ".join(run.character_names)
        outcome = run.outcome
        outcome_color = OUTCOME_COLOR.get(outcome, TEXT_DIM)
        self._header_lbl.configure(
            text=f"{chars}  •  {run.run_type}  •  A{run.ascension}  •  [{outcome}]",
            text_color=outcome_color,
        )

        # Filter timeline to meaningful events (skip raw reward lines that follow combat)
        for event in run.timeline:
            etype = event.get("type", "")
            self._add_event(etype, event)

    def _add_event(self, etype: str, event: dict) -> None:
        icon, icon_color = _TYPE_ICONS.get(etype, ("•", TEXT_DIM))

        card = ctk.CTkFrame(self._scroll, fg_color=BG_CARD, corner_radius=6)
        card.pack(fill="x", pady=2)
        card.grid_columnconfigure(1, weight=1)

        # Icon column
        ctk.CTkLabel(
            card, text=icon, font=("Segoe UI", 16), text_color=icon_color,
            width=32, anchor="center",
        ).grid(row=0, column=0, padx=(8, 4), pady=6)

        # Content column
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)

        if etype == "act":
            ctk.CTkLabel(
                content, text=f"Act: {event['act']}",
                font=FONT_BODY, text_color=ACCENT2,
            ).pack(anchor="w")

        elif etype == "combat":
            enc = event["encounter_id"].replace("_", " ")
            won = event["won"]
            color = TEXT_WIN if won else TEXT_LOSS
            result = "WON" if won else "LOST"
            ctk.CTkLabel(
                content, text=f"{enc}  —  {result}",
                font=FONT_BODY, text_color=color,
            ).pack(anchor="w")
            kills = event.get("kills", [])
            if kills:
                kill_str = ", ".join(k.replace("MONSTER.", "") for k in kills)
                ctk.CTkLabel(
                    content, text=f"Killed: {kill_str}",
                    font=FONT_SMALL, text_color=TEXT_DIM,
                ).pack(anchor="w")

        elif etype == "reward":
            rtype = event["reward_type"]
            if rtype == "gold":
                txt = f"+{event['gold_amount']} gold"
                ctk.CTkLabel(content, text=txt, font=FONT_SMALL, text_color=TEXT_GOLD).pack(anchor="w")
            else:
                item = (event.get("item_id") or "").replace("CARD.", "").replace("RELIC.", "").replace("POTION.", "")
                color = ACCENT2 if rtype == "relic" else (ACCENT if rtype == "potion" else TEXT)
                ctk.CTkLabel(
                    content, text=f"{rtype.title()}: {item}",
                    font=FONT_SMALL, text_color=color,
                ).pack(anchor="w")

        elif etype == "event_start":
            ctk.CTkLabel(
                content, text=f"Event: {event['event_id'].replace('_', ' ')}",
                font=FONT_BODY, text_color=ACCENT,
            ).pack(anchor="w")

        elif etype == "event_choice":
            choice = event["choice_key"].split(".")[-1].replace("_", " ")
            ctk.CTkLabel(
                content, text=f"Chose: {choice}",
                font=FONT_SMALL, text_color=ACCENT2,
            ).pack(anchor="w")

        elif etype == "run_end":
            outcome = event["outcome"]
            color = TEXT_WIN if outcome == "WIN" else TEXT_LOSS
            ctk.CTkLabel(
                content, text=f"Run {outcome}",
                font=("Segoe UI", 14, "bold"), text_color=color,
            ).pack(anchor="w")

            ancients = event.get("win_ancients", [])
            if ancients:
                ctk.CTkLabel(
                    content, text="Ancients: " + ", ".join(ancients),
                    font=FONT_SMALL, text_color=TEXT_WIN,
                ).pack(anchor="w")

            death_m = event.get("death_monster")
            death_e = event.get("death_encounter")
            if death_m:
                ctk.CTkLabel(
                    content, text=f"Killed by: {death_m.replace('MONSTER.', '')}",
                    font=FONT_SMALL, text_color=TEXT_LOSS,
                ).pack(anchor="w")
            if death_e:
                ctk.CTkLabel(
                    content, text=f"In: {death_e.replace('ENCOUNTER.', '').replace('_', ' ')}",
                    font=FONT_SMALL, text_color=TEXT_LOSS,
                ).pack(anchor="w")
