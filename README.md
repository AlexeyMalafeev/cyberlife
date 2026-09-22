# CyberLife

**v0.1.0 "Altered Bourbon"** — a text-based cyberpunk life sim. Survive in Neo-Vasilisk long enough to buy your way off-world — or become a legend of the Sprawl.

## Run

```bash
python3 -m cyberlife
```

Requires Python 3.10+. No dependencies. Add `--seed N` for a repeatable run, `q` at any prompt to quit. Set `NO_COLOR=1` to disable ANSI colors.

See [CHANGELOG.md](CHANGELOG.md) for what's been built and [BACKLOG.md](BACKLOG.md) for what's planned.

## Develop

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```

## How it plays

Each day you get **3 action points** (more with the right chrome). Spend them on:

| Action        | Effect |
|---------------|--------|
| Work          | Steady credits, steady stress. Better jobs need skills. |
| Run a gig     | Skill-checked, risky. Big credits + street cred on success; HP, credits and cred lost on failure. Raises heat. |
| Train         | Chance to raise Hacking / Muscle / Charm (harder at higher levels). |
| Rest          | +HP, -stress. |
| Hit the bar   | -stress, chance of cred, chance of trouble. |
| Ripperdoc     | Buy cyberware (permanent bonuses, costs humanity) or stim-packs. |
| See the fixer | Buy the 15,000¢ forged orbital visa to win. |

**NPC dialog:** the people you deal with speak stock lines by default. On Apple Silicon you
can have a local model voice them instead, through [mlx-lm](https://github.com/ml-explore/mlx-lm)'s
server (installed wherever you like; the game itself still needs nothing but Python):

```bash
mlx_lm.server --model mlx-community/gemma-3-4b-it-4bit
```

```bash
python3 -m cyberlife --llm mlx
```

The model only talks — every outcome is decided by the game first — and if the server goes
away the game falls back to stock lines. `--llm-url` (default `http://localhost:8080`),
`--llm-model` and `--llm-timeout` (default 5s) tune it, or set `CYBERLIFE_LLM=mlx` and
friends in your environment.

**Saving:** five slots under `~/.cyberlife/saves` (override with `--save-dir DIR` or
`CYBERLIFE_SAVE_DIR`). The game autosaves each night and when you quit; "Save game" in the
day menu writes to any slot and costs no action point. Finishing a run — win or lose —
retires its slot.

At night: rent is auto-debited every 7 days, heat cools off, and a random event fires (some with choices). High heat attracts corpo sweeps.

**Win:** buy the visa, or reach 100 street cred.
**Lose:** health 0, humanity 0 (cyberpsychosis), stress 100 (burnout), or 3 missed rents (eviction).

## Layout

```
cyberlife/
  __main__.py   entry point / CLI args
  game.py       day/night loop, character creation, endings
  actions.py    what you can do with an action point
  events.py     weighted random night events
  data.py       all content: jobs, gigs, cyberware, backgrounds, flavor text
  player.py     Player state + derived stats (cyberware bonuses)
  ui.py         colors, menus, prompts
tests/          pytest suite (fixtures in conftest.py)
```

Tuning knobs (visa cost, legend cred, rent cadence) live at the top of `data.py`; adding a job, gig, or implant is a one-line entry in the same file.
