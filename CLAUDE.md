# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CyberLife: a text-based cyberpunk life sim. Pure Python 3.10+ stdlib, no dependencies, no build step, no test suite yet.

## Commands

```bash
python3 -m cyberlife              # play
python3 -m cyberlife --seed 7     # repeatable RNG for reproducing a bug
NO_COLOR=1 python3 -m cyberlife   # plain output (colors also auto-disable when stdout isn't a tty)
```

Scripted playthrough (menus are numbered; blank line = the `[enter]` pause):

```bash
printf 'Kai\nGhost\n1\n\n1\n1\n4\n9\n\n' | python3 -m cyberlife --seed 7
```

There are no unit tests. The way the loop has been verified so far is a random-input fuzzer: monkeypatch `builtins.input` (answer `y`/`n` when the prompt contains `[y/n]`, a digit 1-9 when it contains `> `, else `""`), set `cyberlife.ui.USE_COLOR = False`, call `cyberlife.game.run()` a few hundred times under `contextlib.redirect_stdout`, and assert no exceptions and that every run prints an ending. Re-run something like that after touching the loop or adding actions/events.

## Architecture

Everything is a function that takes the `Player` dataclass and mutates it; there's no engine layer beyond `game.run()`.

- `game.run()` → `create_character()` → repeat `day_loop()` → `night()` until `player.death_cause()` or `player.won` is set → `ending()`.
- **`day_loop`** gives the player `max_energy` action points and shows a menu built from a list of `(label, handler)` pairs. Each handler in `actions.py` returns truthy if it **spent an action point**, falsy if it was cancelled/free (e.g. "Never mind", `quit_job`, the fixer when you can't afford the visa). Forgetting the return value is the most likely bug when adding an action.
- **`night`** applies passive drift (stress down, HP up, heat -1), debits rent every `RENT_EVERY` days, then fires one `events.night_event()`.
- **`events.EVENTS`** is a table of `(weight, handler, eligibility_predicate)`; selection is `random.choices` over the eligible subset. New events go in this table, not in the loop.
- **Win/lose is checked in `game.run`, not in actions.** Actions set `player.won = "visa"` (or `run` sets `"legend"` on cred ≥ `LEGEND_CRED`); `Player.death_cause()` returns the loss reason string. `ending()` maps those strings to text — add a key there if you add an ending.
- **`Player`** stores raw `skills`/`health` etc. Always read effective values through `player.skill(name)`, `player.max_health`, `player.max_energy` — they add cyberware bonuses computed from `data.CYBERWARE` by id. Call `player.clamp()` after mutating stats (the loop does it once per action; handlers that branch on the value mid-action need to call it themselves).
- **`data.py`** holds all content and tuning constants (`VISA_COST`, `LEGEND_CRED`, `RENT_EVERY`, `MAX_MISSED_RENT`, job/gig/cyberware tables). Jobs are referenced by the dict object itself (`player.job` is a `data.JOBS` entry); cyberware by `id` string.
- **`ui.py`** owns all input. Every prompt goes through `_read`, which raises `QuitGame` on `q`/EOF; `game.run` catches it. Don't call `input()` directly elsewhere or the fuzzer/quit handling breaks.

## Balance notes

Random play should mostly lose (eviction) and only win via legend after ~2 months. Bar cred is intentionally a 30% chance and failed gigs cost -1 cred — both were added because guaranteed cred made random play win 15% of the time. Keep that in mind before adding free cred sources.
