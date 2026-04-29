from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class PlayerInfo:
    steam_id: str       # "76561198099480450" or "1"
    character: str      # "IRONCLAD", "DEFECT", etc.


@dataclass
class CombatEvent:
    encounter_id: str           # "SLUDGE_SPINNER_WEAK"
    won: bool
    kills: list[str] = field(default_factory=list)  # ["MONSTER.SLUDGE_SPINNER"]
    act: str = ""


@dataclass
class RewardEvent:
    reward_type: str            # "gold" | "card" | "relic" | "potion"
    item_id: str | None = None
    gold_amount: int = 0


@dataclass
class CardPlay:
    player_id: str
    card_id: str
    target: str | None = None


@dataclass
class EventChoice:
    event_id: str
    player_id: str
    choice_key: str
    option_index: int


@dataclass
class RunSession:
    source_file: str
    run_id: str | None = None
    session_timestamp: str = ""
    run_type: str = ""          # "DAILY", "CUSTOM", "singleplayer"
    players: list[PlayerInfo] = field(default_factory=list)
    ascension: int = 0
    seed: str = ""
    modifiers: list[str] = field(default_factory=list)
    acts_visited: list[str] = field(default_factory=list)
    outcome: str = "UNKNOWN"    # "WIN" | "LOSS" | "UNKNOWN"
    win_ancients: list[str] = field(default_factory=list)
    death_encounter: str | None = None
    death_monster: str | None = None
    combats: list[CombatEvent] = field(default_factory=list)
    rewards: list[RewardEvent] = field(default_factory=list)
    card_plays: list[CardPlay] = field(default_factory=list)
    event_choices: list[EventChoice] = field(default_factory=list)
    card_selections: list[tuple[str, list[str]]] = field(default_factory=list)

    # Timeline events — ordered list of dicts for the Timeline tab
    # Each dict has at minimum a "type" key: "combat", "event", "reward", "run_end"
    timeline: list[dict] = field(default_factory=list)

    @property
    def character_names(self) -> list[str]:
        return [p.character for p in self.players]

    @property
    def total_gold(self) -> int:
        return sum(r.gold_amount for r in self.rewards if r.reward_type == "gold")

    @property
    def relics(self) -> list[str]:
        return [r.item_id for r in self.rewards if r.reward_type == "relic" and r.item_id]

    @property
    def potions(self) -> list[str]:
        return [r.item_id for r in self.rewards if r.reward_type == "potion" and r.item_id]

    @property
    def cards_acquired(self) -> list[str]:
        return [r.item_id for r in self.rewards if r.reward_type == "card" and r.item_id]

    @property
    def encounters_won(self) -> int:
        return sum(1 for c in self.combats if c.won)

    @property
    def encounters_total(self) -> int:
        return len(self.combats)


@dataclass
class LogFile:
    path: str
    filename: str
    size_bytes: int
    session_timestamp: str
    runs: list[RunSession] = field(default_factory=list)
    is_active: bool = False     # True for godot.log
