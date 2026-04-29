from __future__ import annotations

import os
import re
from .models import (
    CardPlay, CombatEvent, EventChoice, LogFile, PlayerInfo, RewardEvent, RunSession
)

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

RE_TIMESTAMP     = re.compile(r'^Timestamp:\s+(.+)$')
RE_LOG_LINE      = re.compile(r'^\[(?:INFO|DEBUG|VERYDEBUG|WARN|ERROR)\]\s*(.*)')

RE_EMBARK_MULTI  = re.compile(
    r'Embarking on a (\w+) multiplayer run\. Players: (.+?)\. Ascension: (\d+) Seed: (\S*)'
    r'(?: Modifiers: (.+))?$'
)
RE_EMBARK_SOLO   = re.compile(
    r'Embarking on a singleplayer (\w+) run\. Ascension: (\d+) Seed: (\S*)'
)
RE_PLAYER_ENTRY  = re.compile(r'Player (\S+),\s*(\w+)')
RE_CHAR_LOAD     = re.compile(r"Preloading 'characters=([^']+)' assets")

RE_COMBAT_START  = re.compile(r'Creating NCombatRoom with mode=ActiveCombat encounter=(\w+)')
RE_COMBAT_WIN    = re.compile(r'CHARACTER\.(\w+) has won against encounter ENCOUNTER\.(\w+)\.')
RE_COMBAT_LOSS   = re.compile(r'CHARACTER\.(\w+) has lost to encounter ENCOUNTER\.(\w+)\.')
RE_KILL          = re.compile(r'CHARACTER\.(\w+) has killed a MONSTER\.(\w+)\.')

RE_RUN_WIN       = re.compile(r'CHARACTER\.(\w+) has won a run with ancient EVENT\.(\w+)\.')
RE_RUN_DEATH     = re.compile(r'CHARACTER\.(\w+) has died to a MONSTER\.(\w+)\.')
RE_RUN_SAVED     = re.compile(r'Saved run history: (\d+)\.run')

RE_GOLD          = re.compile(r'Obtained (\d+) gold from reward')
RE_CARD_REWARD   = re.compile(r'Obtained (CARD\.\w+) from card reward')
RE_RELIC_REWARD  = re.compile(r'Obtained (RELIC\.\w+) from relic reward')
RE_POTION_REWARD = re.compile(r'Obtained (POTION\.\w+) from potion reward')

RE_CARD_PLAY     = re.compile(
    r'Player (\S+) playing card (\w+) \((?:targeting (.+?) \(index \d+\)|no target)\)'
)
RE_CARD_SELECT   = re.compile(r'Player (\S+) chose cards \[([^\]]+)\]')

RE_EVENT_START   = re.compile(r'\[EventSynchronizer\] Beginning event EVENT\.(\w+)')
RE_EVENT_CHOICE  = re.compile(
    r'\[EventSynchronizer\] Option index (\d+) chosen for player (\S+) in event EVENT\.(\w+)\. Choice key: (\S+)'
)

RE_MAP_ACT       = re.compile(r"Preloading 'Act=(\w+)' assets")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class LogParser:
    """Parse one or all STS2 log files into structured LogFile objects."""

    def parse_directory(self, dir_path: str) -> list[LogFile]:
        log_files: list[LogFile] = []
        try:
            entries = sorted(os.listdir(dir_path))
        except OSError:
            return []

        for name in entries:
            if not name.endswith('.log'):
                continue
            log_files.append(self.parse_file(os.path.join(dir_path, name)))

        # godot.log (active) sorted first; timestamped files newest-first
        log_files.sort(key=lambda lf: (not lf.is_active, lf.filename), reverse=False)
        # Reverse timestamped ones so newest appears first after active
        active = [lf for lf in log_files if lf.is_active]
        others = sorted(
            [lf for lf in log_files if not lf.is_active],
            key=lambda lf: lf.filename,
            reverse=True,
        )
        return active + others

    def parse_file(self, path: str) -> LogFile:
        filename = os.path.basename(path)
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0

        log_file = LogFile(
            path=path,
            filename=filename,
            size_bytes=size,
            session_timestamp="",
            is_active=(filename == "godot.log"),
        )

        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError:
            return log_file

        session_ts = ""
        current_run: RunSession | None = None
        current_combat: CombatEvent | None = None
        current_act = ""
        resolve_random = False

        def store_combat(run: RunSession, combat: CombatEvent) -> None:
            run.combats.append(combat)
            run.timeline.append({
                "type": "combat",
                "encounter_id": combat.encounter_id,
                "won": combat.won,
                "kills": list(combat.kills),
                "act": combat.act,
            })

        def finalise_run(run: RunSession) -> None:
            nonlocal current_combat
            if current_combat is not None:
                store_combat(run, current_combat)
                current_combat = None
            log_file.runs.append(run)

        for raw_line in lines:
            line = raw_line.rstrip('\r\n')

            # Session-level timestamp in the header block
            if not session_ts:
                m = RE_TIMESTAMP.match(line)
                if m:
                    session_ts = m.group(1).strip()
                    log_file.session_timestamp = session_ts
                    continue

            # Strip log level prefix
            m = RE_LOG_LINE.match(line)
            if not m:
                continue
            content = m.group(1)

            # ----------------------------------------------------------
            # Run start — multiplayer
            # ----------------------------------------------------------
            m = RE_EMBARK_MULTI.search(content)
            if m:
                if current_run is not None:
                    finalise_run(current_run)
                run_type, players_str, asc, seed, mods_str = m.groups()
                players = [
                    PlayerInfo(steam_id=pm.group(1), character=pm.group(2))
                    for pm in RE_PLAYER_ENTRY.finditer(players_str)
                ]
                modifiers = [x.strip() for x in mods_str.split(',')] if mods_str else []
                current_run = RunSession(
                    source_file=filename,
                    session_timestamp=session_ts,
                    run_type=run_type,
                    players=players,
                    ascension=int(asc),
                    seed=seed,
                    modifiers=modifiers,
                )
                current_combat = None
                current_act = ""
                resolve_random = any(p.character == "RANDOM_CHARACTER" for p in players)
                continue

            # ----------------------------------------------------------
            # Run start — singleplayer
            # ----------------------------------------------------------
            m = RE_EMBARK_SOLO.search(content)
            if m:
                if current_run is not None:
                    finalise_run(current_run)
                run_type, asc, seed = m.groups()
                # Character name will be resolved from CHAR_LOAD below
                current_run = RunSession(
                    source_file=filename,
                    session_timestamp=session_ts,
                    run_type=run_type,
                    players=[PlayerInfo(steam_id="1", character="RANDOM_CHARACTER")],
                    ascension=int(asc),
                    seed=seed,
                )
                current_combat = None
                current_act = ""
                resolve_random = True
                continue

            if current_run is None:
                continue

            # ----------------------------------------------------------
            # RANDOM_CHARACTER resolution
            # ----------------------------------------------------------
            if resolve_random:
                m = RE_CHAR_LOAD.search(content)
                if m:
                    char_name = m.group(1)
                    for p in current_run.players:
                        if p.character == "RANDOM_CHARACTER":
                            p.character = char_name
                            break
                    if not any(p.character == "RANDOM_CHARACTER" for p in current_run.players):
                        resolve_random = False
                    continue

            # ----------------------------------------------------------
            # Act tracking
            # ----------------------------------------------------------
            m = RE_MAP_ACT.search(content)
            if m:
                act = m.group(1)
                if act not in current_run.acts_visited:
                    current_run.acts_visited.append(act)
                    current_run.timeline.append({"type": "act", "act": act})
                current_act = act
                continue

            # ----------------------------------------------------------
            # Combat start
            # ----------------------------------------------------------
            m = RE_COMBAT_START.search(content)
            if m:
                # If a previous combat was never closed (shouldn't happen), store it
                if current_combat is not None:
                    store_combat(current_run, current_combat)
                current_combat = CombatEvent(
                    encounter_id=m.group(1), won=False, act=current_act
                )
                continue

            # ----------------------------------------------------------
            # Combat kills
            # ----------------------------------------------------------
            m = RE_KILL.search(content)
            if m and current_combat is not None:
                current_combat.kills.append(f"MONSTER.{m.group(2)}")
                continue

            # ----------------------------------------------------------
            # Combat win — finalize
            # ----------------------------------------------------------
            m = RE_COMBAT_WIN.search(content)
            if m:
                if current_combat is not None:
                    current_combat.won = True
                    store_combat(current_run, current_combat)
                    current_combat = None
                continue

            # ----------------------------------------------------------
            # Combat loss — finalize, also record death encounter on run
            # ----------------------------------------------------------
            m = RE_COMBAT_LOSS.search(content)
            if m:
                current_run.death_encounter = f"ENCOUNTER.{m.group(2)}"
                if current_combat is not None:
                    current_combat.won = False
                    store_combat(current_run, current_combat)
                    current_combat = None
                continue

            # ----------------------------------------------------------
            # Rewards
            # ----------------------------------------------------------
            m = RE_GOLD.search(content)
            if m:
                amount = int(m.group(1))
                current_run.rewards.append(RewardEvent(reward_type="gold", gold_amount=amount))
                current_run.timeline.append({"type": "reward", "reward_type": "gold", "gold_amount": amount})
                continue

            m = RE_CARD_REWARD.search(content)
            if m:
                item = m.group(1)
                current_run.rewards.append(RewardEvent(reward_type="card", item_id=item))
                current_run.timeline.append({"type": "reward", "reward_type": "card", "item_id": item})
                continue

            m = RE_RELIC_REWARD.search(content)
            if m:
                item = m.group(1)
                current_run.rewards.append(RewardEvent(reward_type="relic", item_id=item))
                current_run.timeline.append({"type": "reward", "reward_type": "relic", "item_id": item})
                continue

            m = RE_POTION_REWARD.search(content)
            if m:
                item = m.group(1)
                current_run.rewards.append(RewardEvent(reward_type="potion", item_id=item))
                current_run.timeline.append({"type": "reward", "reward_type": "potion", "item_id": item})
                continue

            # ----------------------------------------------------------
            # Card plays & selections
            # ----------------------------------------------------------
            m = RE_CARD_PLAY.search(content)
            if m:
                pid, card_id, target = m.groups()
                current_run.card_plays.append(CardPlay(player_id=pid, card_id=card_id, target=target))
                continue

            m = RE_CARD_SELECT.search(content)
            if m:
                pid = m.group(1)
                cards = [c.strip() for c in m.group(2).split(',')]
                current_run.card_selections.append((pid, cards))
                continue

            # ----------------------------------------------------------
            # Events
            # ----------------------------------------------------------
            m = RE_EVENT_START.search(content)
            if m:
                event_id = m.group(1)
                current_run.timeline.append({"type": "event_start", "event_id": event_id})
                continue

            m = RE_EVENT_CHOICE.search(content)
            if m:
                idx, pid, event_id, choice_key = m.groups()
                current_run.event_choices.append(EventChoice(
                    event_id=event_id,
                    player_id=pid,
                    choice_key=choice_key,
                    option_index=int(idx),
                ))
                current_run.timeline.append({
                    "type": "event_choice",
                    "event_id": event_id,
                    "player_id": pid,
                    "choice_key": choice_key,
                })
                continue

            # ----------------------------------------------------------
            # Run outcome
            # ----------------------------------------------------------
            m = RE_RUN_WIN.search(content)
            if m:
                current_run.win_ancients.append(m.group(2))
                current_run.outcome = "WIN"
                continue

            m = RE_RUN_DEATH.search(content)
            if m:
                current_run.death_monster = f"MONSTER.{m.group(2)}"
                current_run.outcome = "LOSS"
                continue

            m = RE_RUN_SAVED.search(content)
            if m:
                current_run.run_id = m.group(1)
                current_run.timeline.append({
                    "type": "run_end",
                    "outcome": current_run.outcome,
                    "win_ancients": list(current_run.win_ancients),
                    "death_monster": current_run.death_monster,
                    "death_encounter": current_run.death_encounter,
                })
                finalise_run(current_run)
                current_run = None
                current_combat = None
                current_act = ""
                continue

        # EOF — finalise any open run (godot.log mid-session)
        if current_run is not None:
            if current_combat is not None:
                store_combat(current_run, current_combat)
                current_combat = None
            log_file.runs.append(current_run)

        return log_file
