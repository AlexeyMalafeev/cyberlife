# CyberLife

A text-based cyberpunk life sim. Survive in Neo-Vasilisk long enough to buy your way off-world — or become a legend of the Sprawl.

## Run

```bash
python3 -m cyberlife
```

Requires Python 3.10+. No dependencies. Add `--seed N` for a repeatable run, `q` at any prompt to quit. Set `NO_COLOR=1` to disable ANSI colors.

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
```

Tuning knobs (visa cost, legend cred, rent cadence) live at the top of `data.py`; adding a job, gig, or implant is a one-line entry in the same file.
