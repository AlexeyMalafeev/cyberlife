# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CyberLife: a text-based cyberpunk life sim. Pure Python 3.10+ stdlib at runtime, no build step. pytest for tests. Optional NPC dialog talks HTTP to a model server (`--llm mlx` local, `--llm deepseek` hosted); the game never imports ML libraries.

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

**Every feature or behavior change ships with tests in the same commit.** New action → `tests/test_actions.py`; new event → `tests/test_events.py` (the parametrized `test_each_handler_runs_when_eligible` picks it up automatically, but add a targeted test for its choices/outcomes); loop/rent/ending changes → `tests/test_game.py`; new content tables → `tests/test_data.py` sanity checks; encounter/dialog-game/relationship changes → `tests/test_romance.py`.

Fixtures in `tests/conftest.py`:
- `isolated_saves` (autouse) — points the save directory at `tmp_path`. Tests must never
  touch the real `~/.cyberlife`; the fuzz test picks menu entries at random and will hit "Save game".
- `player` — a Street Kid with 1000¢ and default stats.
- `answers("1", "y", ...)` — scripts user input by replacing `ui._read` (the autouse `line_input` fixture turns off single-keypress mode so menus read through it too); raises if the code asks for more input than scripted, so it also asserts prompt count. Menu numbers are positional, and the day menu renumbers when "Quit job" disappears.
- `canned_dialog` (autouse) resets `llm.backend` to stock lines; `no_network` (autouse) makes
  any socket open fail the test. Test dialog backends with a stub backend or a fake `post=`.
- `force_roll(0.0 | 0.99)` — pins `random.random()` so success/failure branches are deterministic. `random.randint`/`random.choice` are unaffected (the autouse `seeded` fixture seeds them).

`test_random_play_always_reaches_an_ending` is the fuzz test: 40 seeds of random input through `game.run()`, asserting no crash and an ending. It's what caught `pause()` bypassing `_read`.

Releases are tagged `vX.Y.Z` and carry a **codename that riffs on what that release
introduced**, running **alphabetically**: the next one takes the letter after the newest
release heading in `CHANGELOG.md` (or `git tag -n1`), e.g. "Altered Bourbon" → "Blade
Rendezvous" → a C name. The house style is puns that *riff on* cyberpunk pop culture — never an
existing franchise's title as-is. To cut a release: rename the `## [Unreleased]` heading to
`## [X.Y.Z] — "Codename" — YYYY-MM-DD` with a one-line summary, open a fresh empty Unreleased
section, bump `version` in `pyproject.toml`, then `git tag -a vX.Y.Z` with the codename in the
tag message and `git push --tags`.

Bump the **minor** version for a batch of player-visible features, cut only after a playtest
says it's ready, not per feature or on a schedule. **Patch** releases are fixes only and take
no codename (heading `## [X.Y.Z] — YYYY-MM-DD`), which keeps the alphabet for real content.

**User-visible changes go in `CHANGELOG.md` under `## [Unreleased]`** in the same commit,
grouped Added / Changed / Fixed. Describe what a player or contributor notices, not the diff;
internal refactors only earn a line when they change how you work with the code (the
`Player.job` → `job_id` change did). Cutting a release turns that section into the
version's own (see above).

Planned work and its design notes live in `BACKLOG.md`. Check it before starting a feature — several items have ordering constraints (save/load before anything that adds `Player` fields, LLM dialog before the social systems).

## Architecture

Everything is a function that takes the `Player` dataclass and mutates it; there's no engine layer beyond `game.run()`.

- `game.run()` → `create_character()` → repeat `day_loop()` → `night()` until `player.death_cause()` or `player.won` is set → `ending()`.
- **`day_loop`** gives the player `max_energy` action points and shows a menu built from a list of `(label, handler)` pairs. Each handler in `actions.py` returns truthy if it **spent an action point**, falsy if it was cancelled/free (e.g. "Never mind", `quit_job`, the fixer when you can't afford the visa). Forgetting the return value is the most likely bug when adding an action.
- **`night`** applies passive drift (stress down, HP up, heat -1), debits rent every `RENT_EVERY` days, then fires one `events.night_event()`.
- **`events.EVENTS`** is a table of `(weight, handler, eligibility_predicate)`; selection is `random.choices` over the eligible subset. New events go in this table, not in the loop.
- **Win/lose is checked in `game.run`, not in actions.** Actions set `player.won = "visa"` (or `run` sets `"legend"` on cred ≥ `LEGEND_CRED`); `Player.death_cause()` returns the loss reason string. `ending()` maps those strings to text — add a key there if you add an ending.
- **`Player`** stores raw `skills`/`health` etc. Always read effective values through `player.skill(name)`, `player.max_health`, `player.max_energy` — they add cyberware bonuses computed from `data.CYBERWARE` by id. Call `player.clamp()` after mutating stats (the loop does it once per action; handlers that branch on the value mid-action need to call it themselves).
- **`data.py`** holds all content and tuning constants (`VISA_COST`, `LEGEND_CRED`, `RENT_EVERY`, `MAX_MISSED_RENT`, job/gig/cyberware tables). Jobs are referenced by the dict object itself (`player.job` is a `data.JOBS` entry); cyberware by `id` string.
- **`save.py`** keeps `data.SAVE_SLOTS` JSON slots under `~/.cyberlife/saves` (override with
  `--save-dir` or `CYBERLIFE_SAVE_DIR`). `game.night()` autosaves, quitting saves, and
  `game.finish()` deletes the slot so a finished run can't be continued. Saves are versioned:
  unknown fields are dropped, missing ones take dataclass defaults, content that no longer
  exists (a removed job or implant) is stripped, and a newer `SAVE_VERSION` is refused.
  `describe()` returns `None` only for a genuinely absent file — a present-but-unparseable
  save reports `unreadable` so nothing overwrites it. **Bump `SAVE_VERSION` when a field
  changes meaning**, not when one is merely added.
- **`Player.job_id`** is the stored field; `player.job` is a read-only property resolving it
  through `data.job_by_id`. Assign `job_id`, never `job`.
- **`llm.py`** voices NPCs. Call sites use `llm.speak(npc_id, player, situation, **ctx)`;
  personas and per-situation prompts + stock lines live in `data.NPCS`. Decide outcomes
  *before* speaking and describe them in the situation — the model narrates, never decides.
  `respond()` always draws the stock line from `random` first so seeds are backend-independent,
  and drops model lines that mention numbers. Backends implement `complete(messages,
  max_tokens=None) -> str | None`; call them through `llm.complete()`, which counts failures
  and never raises. `ChatCompletionsBackend` is the OpenAI-style HTTP base that `MlxBackend` and
  `DeepSeekBackend` subclass (register new ones in `llm.BACKENDS`).
- **`romance.py`** is the cast and the bar encounter (`actions.bar` calls `romance.encounter`).
  `Player.cast` is a list of JSON-safe dicts made at character creation by `ensure_cast`: a
  profile drawn from the `data.DATE_*` tables plus relationship state (`romance.RELATIONSHIP`:
  `stage`, `times_met`, `affection`, ...). `Player.partner` is a read-only property: the entry
  whose `stage` is in `data.PARTNER_STAGES`. Change her `stage`, never assign `partner`. Each
  conversation adds its net score to `affection`, and she only becomes a partner once
  `DATE_MIN_MEETINGS` and `DATE_PARTNER_AFFECTION` are met. `romance.night` handles neglect,
  worry, leaving and moving in. Each round Python picks the topic (a random draw with no
  repeats) and which reply is good/bad/neutral, and the model (one JSON call via
  `llm.parse_json`) only words it. Stock `lines`/`good`/`bad` lists are parallel: `good[i]`
  answers `lines[i]`. Tests steer choices by kind with the `steer` fixture in
  `tests/test_romance.py`. `always` there gives a one-woman cast who's always at the bar, and the
  shared `dating` fixture gives `player` a partner.
- **`ui.py`** owns all input. Text prompts go through `_read`, which raises `QuitGame` on `q`/EOF; `game.run` catches it. Menus, y/n and `pause()` go through `_read_key`, which reads one raw keypress on a real terminal (`RAW_KEYS`) and otherwise falls back to `_read`. Menu keys come from `MENU_KEYS` (1-9, 0, then letters without `q`). Don't call `input()` directly elsewhere or the fuzzer/quit handling breaks.

## Balance notes

Random play should mostly lose (eviction) and only win via legend after ~2 months. Bar cred is intentionally a 30% chance and failed gigs cost -1 cred — both were added because guaranteed cred made random play win 15% of the time. Keep that in mind before adding free cred sources.
