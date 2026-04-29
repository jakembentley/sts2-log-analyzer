from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .models import LogFile, RunSession


@dataclass
class EncounterStats:
    encounter_id: str
    times_faced: int = 0
    wins: int = 0
    losses: int = 0
    kills: Counter = field(default_factory=Counter)

    @property
    def win_rate(self) -> float:
        return self.wins / self.times_faced if self.times_faced else 0.0


@dataclass
class AggregateStats:
    total_runs: int = 0
    wins: int = 0
    losses: int = 0
    unknown: int = 0

    characters_played: Counter = field(default_factory=Counter)
    run_types: Counter = field(default_factory=Counter)

    # Card plays across all runs
    card_play_counts: Counter = field(default_factory=Counter)
    # Cards acquired via rewards
    cards_acquired: Counter = field(default_factory=Counter)

    # Combat
    encounter_stats: dict[str, EncounterStats] = field(default_factory=dict)
    total_kills: Counter = field(default_factory=Counter)

    # Rewards
    total_gold: int = 0
    gold_per_run: list[tuple[str, int]] = field(default_factory=list)  # (run_label, gold)
    relics_collected: Counter = field(default_factory=Counter)
    potions_collected: Counter = field(default_factory=Counter)

    # Events
    event_encounters: Counter = field(default_factory=Counter)
    event_choices: dict[str, Counter] = field(default_factory=dict)  # event_id -> choice_key Counter

    @property
    def win_rate(self) -> float:
        decided = self.wins + self.losses
        return self.wins / decided if decided else 0.0

    @property
    def top_cards(self) -> list[tuple[str, int]]:
        return self.card_play_counts.most_common(20)

    @property
    def sorted_encounters(self) -> list[EncounterStats]:
        return sorted(self.encounter_stats.values(), key=lambda e: e.times_faced, reverse=True)


def aggregate(log_files: list[LogFile]) -> AggregateStats:
    stats = AggregateStats()
    for lf in log_files:
        for run in lf.runs:
            _add_run(stats, run)
    return stats


def aggregate_run(run: RunSession) -> dict:
    """Return a flat summary dict for display in the overview table."""
    return {
        "source_file": run.source_file,
        "run_id": run.run_id or "–",
        "session_timestamp": run.session_timestamp,
        "run_type": run.run_type,
        "characters": ", ".join(run.character_names),
        "ascension": run.ascension,
        "seed": run.seed,
        "modifiers": ", ".join(m.replace("MODIFIER.", "") for m in run.modifiers),
        "outcome": run.outcome,
        "acts": " → ".join(run.acts_visited),
        "combats": run.encounters_total,
        "wins": run.encounters_won,
        "gold": run.total_gold,
        "relics": len(run.relics),
        "cards": len(run.cards_acquired),
        "death_monster": (run.death_monster or "").replace("MONSTER.", ""),
        "death_encounter": (run.death_encounter or "").replace("ENCOUNTER.", ""),
    }


def _add_run(stats: AggregateStats, run: RunSession) -> None:
    stats.total_runs += 1

    if run.outcome == "WIN":
        stats.wins += 1
    elif run.outcome == "LOSS":
        stats.losses += 1
    else:
        stats.unknown += 1

    for p in run.players:
        stats.characters_played[p.character] += 1
    stats.run_types[run.run_type] += 1

    # Card plays
    for cp in run.card_plays:
        stats.card_play_counts[cp.card_id] += 1

    # Cards acquired
    for item in run.cards_acquired:
        card_name = item.replace("CARD.", "")
        stats.cards_acquired[card_name] += 1

    # Combat
    for combat in run.combats:
        eid = combat.encounter_id
        if eid not in stats.encounter_stats:
            stats.encounter_stats[eid] = EncounterStats(encounter_id=eid)
        es = stats.encounter_stats[eid]
        es.times_faced += 1
        if combat.won:
            es.wins += 1
        else:
            es.losses += 1
        for kill in combat.kills:
            monster = kill.replace("MONSTER.", "")
            es.kills[monster] += 1
            stats.total_kills[monster] += 1

    # Rewards
    run_gold = run.total_gold
    stats.total_gold += run_gold
    label = f"{run.source_file[:12]}…" if len(run.source_file) > 12 else run.source_file
    label = f"{label} #{run.run_id or '?'}"
    stats.gold_per_run.append((label, run_gold))

    for relic in run.relics:
        stats.relics_collected[relic.replace("RELIC.", "")] += 1
    for potion in run.potions:
        stats.potions_collected[potion.replace("POTION.", "")] += 1

    # Events
    for ec in run.event_choices:
        stats.event_encounters[ec.event_id] += 1
        if ec.event_id not in stats.event_choices:
            stats.event_choices[ec.event_id] = Counter()
        stats.event_choices[ec.event_id][ec.choice_key] += 1
