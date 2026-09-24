# Changelog

All notable changes to CyberLife are recorded here, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project aims to follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Every release carries a codename that riffs on what it introduced, and the codenames run
**alphabetically** — 0.1.0 is A, the next release is B, and so on.

## [Unreleased]

### Added

- The project is open source under the MIT license (see `LICENSE`).
- NPCs talk. Marrow, Doc Saito, Juno the bartender, a stranger at the bar and the Kestrels
  each have a persona and speak a line when you deal with them. By default the lines come from
  a stock table, so the game stays offline and `--seed` runs are unchanged.
- `--llm mlx` voices those lines with a local model through `mlx_lm.server` on Apple Silicon
  (`--llm-url`, `--llm-model`, `--llm-timeout`, or the matching `CYBERLIFE_LLM*` environment
  variables). The model only narrates: every outcome is rolled before it speaks, a line that
  mentions numbers or runs long is replaced by a stock one, and if the server stops answering
  the game says so once and carries on with stock lines. The same seed plays out the same way
  with the model on or off.
- `--llm deepseek` voices NPCs through DeepSeek's hosted API instead, using the key in
  `DEEPSEEK_API_KEY` (model `deepseek-chat` and a 10s timeout unless you say otherwise).
  Starting without a key is a usage error; a rejected key gets one notice naming the HTTP
  error, then stock lines.

- Someone to meet at the Neon Lotus. About one bar visit in three, a woman catches your eye:
  her looks, job, temperament, interests, values, pet peeve and view of chrome are drawn at
  random, so no two are alike. Take your chance and you get five exchanges. Each time she says
  something and you pick one of three replies in shuffled order: one suits her, one clashes,
  one does neither. Her personality is never shown; you read it from what she says. How well
  you do sets how the night ends, from a drink left unfinished to a kiss in the rain. A perfect
  conversation means you start seeing her, and she stays in your save and on your status panel.
  The only payoff is stress relief. Encounters stop while you're seeing someone.
- With `--llm` on, the model narrates the meeting and writes her lines and your three replies
  live, reacting to what you said last. It never decides which reply is good; the game does. If
  the model is off or sends something unusable, stock text fills in, and the same seed plays
  out the same either way.

### Changed

- Menus and yes/no prompts respond to a single keypress — no more Enter. Menu entries are keyed
  1–9, then 0 for a tenth entry (the day menu's "End the day" while you hold a job). "Press any
  key" replaces "press Enter" between screens. Keys typed ahead are dropped, so a held key can't
  spend your action points for you. Name and handle prompts still take a full line, and piped
  input (no terminal) still reads one line per prompt.
- Dialog backends now take a `max_tokens` argument: `complete(messages, max_tokens=None)`.
  Custom and stub backends need the extra parameter.

### Fixed

- The game and test suite run on Python 3.10 and 3.11 again. The ripperdoc menu had an f-string
  that only Python 3.12+ could parse, although `pyproject.toml` promises 3.10+.

## [0.1.0] — "Altered Bourbon" — 2026-09-23

First playable release: the full day-to-day loop, a save system that stores a life to disk and
restores it later, and a bar to drown the day in when the Sprawl gets to be too much.

### Added

**The game** — a text-based cyberpunk life sim set in Neo-Vasilisk, 2087. Each day gives you
three action points; spend them on work, gigs, training, rest, the bar, the ripperdoc, or the
fixer, then survive the night.

- Character creation with three backgrounds (Street Kid, Corpo Dropout, Netrunner), each with
  its own starting skills, credits, and street cred.
- Six jobs gated behind skill requirements, and six skill-checked gigs with visible success
  odds that trade heat and risk for credits and cred.
- Six pieces of cyberware that grant permanent bonuses — including extra action points and max
  health — at a permanent cost in humanity.
- Thirteen weighted night events with eligibility rules, so corpo sweeps only find you when
  you're hot, chrome only glitches if you have chrome, and the Kestrels only shake down someone
  worth shaking down. Several ask you to make a call.
- Rent every seven days, three strikes before eviction.
- Two ways to win (buy the 15,000¢ orbital visa, or reach 100 street cred) and four ways to
  lose (flatlined, cyberpsychosis, burnout, eviction), each with its own ending text.
- Status panel with health/stress/humanity bars, and a stat-change report after every action.
- ANSI color, disabled automatically when stdout isn't a tty or when `NO_COLOR` is set.
- `q` quits from any prompt.

**Save and load** — five slots of versioned JSON under `~/.cyberlife/saves`.

- Autosave each night, a save when you quit, and a manual "Save game" entry in the day menu
  that writes to any slot and costs no action point.
- Title screen offering Continue, Load a run, or New run, listing each slot with its handle,
  background, day, credits, and age.
- A new run takes the first empty slot, or asks which to overwrite when all five are full.
- Finishing a run — win or lose — retires its slot.
- The format tolerates schema drift: unknown fields are dropped, missing ones take their
  dataclass defaults, and content that no longer exists (a removed job or implant) is stripped
  on load. A save written by a newer `SAVE_VERSION` is refused with a clear message.
- Saves are written through a temp file and renamed, so an interrupted save can't corrupt an
  existing one.
- `--save-dir DIR` and `CYBERLIFE_SAVE_DIR` override the save location.

**Tests** — 132 pytest tests running in under a second, no network and no sleeps.

- Fixtures that script player input (`answers`), pin dice rolls (`force_roll`), and redirect
  saves to a temp directory (`isolated_saves`, autouse — the suite never touches the real
  `~/.cyberlife`).
- A fuzz test that plays 40 seeded runs of random input through `game.run()` and asserts every
  one reaches an ending without crashing.

**Docs and project setup** — `README.md`, `CLAUDE.md` (architecture and conventions for future
Claude Code sessions), `BACKLOG.md` (planned features with design notes), `pyproject.toml`, and
a virtualenv-based dev setup with pytest as the only dependency.

### Changed

- Hitting the bar now grants street cred on a 30% roll rather than every visit, and a failed
  gig costs a point of cred. Guaranteed cred made random play win roughly 15% of the time,
  which undercut the intended difficulty.
- The day menu is built from `(label, handler)` pairs rather than a fixed index chain, so
  entries can appear and disappear (like "Quit job") without renumbering bugs.
- Jobs carry an `id`, and `Player.job_id` replaced `Player.job`, which is now a derived
  property resolving through `data.job_by_id`. `player.job` previously held a `data.JOBS` dict
  by identity, which can't survive a round trip through JSON.

### Fixed

- `ui.pause()` called `input()` directly instead of going through `ui._read`, so `q` didn't
  quit at the `[enter]` prompt and the pause couldn't be scripted. Found by the fuzz test.
- A save file that existed but couldn't be parsed — corrupt, or written by a newer build —
  reported as an *empty* slot. It vanished from the title screen and the next new run would
  have silently overwritten it. Damaged saves now occupy their slot and display as such, and
  the title screen still opens when the only save is unreadable.
