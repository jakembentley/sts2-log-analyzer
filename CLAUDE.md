# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Commands

```bash
# Run the app
.venv/Scripts/python.exe main.py

# Install dependencies
.venv/Scripts/pip.exe install -r requirements.txt
```

All commands must be run from `sts2-log-analyzer/` as the working directory.

## Notes

- **Log directory** defaults to the platform-appropriate STS2 log path (Windows: `%APPDATA%`, macOS: `~/Library/Application Support`, Linux: `$XDG_DATA_HOME`); user can override via the "📁 Change Folder" button in the sidebar — persisted to `~/.sts2-analyzer.json`
- **User settings** are persisted to `~/.sts2-analyzer.json` (selected file, window geometry, live-reload state)
- **Log cache** copies every live `.log` file to `~/.sts2-analyzer-cache/` on each refresh; toggle via "View Cache" button in sidebar
- **Live reload** polls every 5 seconds (`LIVE_POLL_MS = 5000` in `gui/app.py`) — no filesystem watcher
- No test suite, lint config, or build step exists yet

## Architecture

| File / module | Purpose |
|---|---|
| `main.py` | Entry point — instantiates `App`, starts Tkinter mainloop |
| `gui/app.py` | Root window — tab manager, file panel, live-reload polling, settings persistence |
| `gui/file_panel.py` | Left sidebar — log file list, refresh button, live-reload toggle |
| `gui/tab_overview.py` | Overview tab — run summaries and aggregate stats |
| `gui/tab_cards.py` | Cards tab — card play counts and acquisition stats |
| `gui/tab_combat.py` | Combat tab — encounter win rates and kill stats |
| `gui/tab_rewards.py` | Rewards tab — gold, relics, and potions collected |
| `gui/tab_timeline.py` | Timeline tab — chronological event view for a selected run |
| `gui/tab_events.py` | Events tab — event encounters and player choices |
| `gui/widgets.py` | Reusable UI components and helpers |
| `gui/constants.py` | UI constants — colors, fonts, window dimensions (dark theme) |
| `analyzer/parser.py` | Core log parsing — regex extraction of runs, combats, rewards, events |
| `analyzer/models.py` | Dataclasses — `RunSession`, `LogFile`, `CombatEvent`, `RewardEvent`, `PlayerInfo` |
| `analyzer/aggregator.py` | Stats aggregation across runs — `AggregateStats`, `EncounterStats` |
| `analyzer/watcher.py` | File watching support for live reload |
| `analyzer/cache.py` | Local log cache — copies live files to `~/.sts2-analyzer-cache/` on every refresh |

## Commit convention

```
<type>(<scope>): <subject — ≤72 chars, imperative mood>

Why: <motivation>
What:
  - <key change 1>
  - <key change 2>

Files: <key files, comma-separated>
```

Types: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`
Scopes: `parser`, `gui`, `overview`, `cards`, `combat`, `rewards`, `timeline`, `events`, `models`, `aggregator`
