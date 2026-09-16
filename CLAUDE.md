# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CyberLife: a text-based cyberpunk life sim. Pure Python 3.10+ stdlib at runtime, no build step. pytest for tests.

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'   # one-time setup (pytest is the only dev dep)
.venv/bin/pytest                                # full suite (~0.2s)
.venv/bin/pytest tests/test_actions.py          # one file
.venv/bin/pytest -k "gig"                       # by name
.venv/bin/pytest -k "not random_play"           # skip the 40-seed fuzz
python3 -m cyberlife                            # play (stdlib only, no venv needed)
python3 -m cyberlife --seed 7                   # repeatable RNG for reproducing a bug
NO_COLOR=1 python3 -m cyberlife                 # plain output (also auto when stdout isn't a tty)
```

## Testing

**Every feature or behavior change ships with tests in the same commit.** New action → `tests/test_actions.py`; new event → `tests/test_events.py` (the parametrized `test_each_handler_runs_when_eligible` picks it up automatically, but add a targeted test for its choices/outcomes); loop/rent/ending changes → `tests/test_game.py`; new content tables → `tests/test_data.py` sanity checks.

Fixtures in `tests/conftest.py`:
- `player` — a Street Kid with 1000¢ and default stats.
- `answers("1", "y", ...)` — scripts user input by replacing `ui._read`; raises if the code asks for more input than scripted, so it also asserts prompt count. Menu numbers are positional, and the day menu renumbers when "Quit job" disappears.
- `force_roll(0.0 | 0.99)` — pins `random.random()` so success/failure branches are deterministic. `random.randint`/`random.choice` are unaffected (the autouse `seeded` fixture seeds them).

`test_random_play_always_reaches_an_ending` is the fuzz test: 40 seeds of random input through `game.run()`, asserting no crash and an ending. It's what caught `pause()` bypassing `_read`.

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
