# Backlog

Planned features, roughly in dependency order. Each entry notes where it lands in the
architecture described in `CLAUDE.md`. Nothing here is committed to a schedule; reorder freely.

Ground rules that apply to all of them:

- Every item ships with tests in the same commit (see the Testing section of `CLAUDE.md`).
- User-visible changes get a `CHANGELOG.md` entry under `## [Unreleased]` in that same commit.
- New content goes in `data.py` tables, not inline in logic.
- All input goes through `ui._read`; all randomness through `random` so `--seed` stays reproducible.
- The suite must run offline and take no real time — no network, no sleeps.

---

## 1. Save / load game state — ✅ done

Shipped: `cyberlife/save.py`, five slots, autosave each night, save-on-quit, manual
"Save game" (free action) to any slot, title screen with Continue / Load / New run.

Decisions made along the way:

- **Several slots** (`data.SAVE_SLOTS = 5`), not one. Permadeath becomes an opt-in
  difficulty setting instead — see item 6.
- Jobs got an `id` and `Player.job_id` replaced `Player.job` (now a derived property),
  which is what made the state JSON-safe.
- A finished run's slot is deleted by `game.finish()`. With autosave-only that already
  behaves like permadeath; item 6 is what makes it a choice.
- Saves are versioned (`SAVE_VERSION`), tolerate missing/unknown fields, drop content
  that no longer exists, and refuse anything newer than the build.
- A slot whose file exists but won't parse reads as *damaged*, not *empty*, so a new run
  never silently overwrites it.

---

## 2. LLM-driven NPC dialog (local model or DeepSeek API) — ✅ done

Shipped: `cyberlife/llm.py` with `respond()`/`speak()`, `CannedBackend` (default),
`MlxBackend` and `DeepSeekBackend`, five NPCs in `data.NPCS`, `--llm off|mlx|deepseek`.

Decisions made along the way:

- **MLX instead of Ollama** for the local backend (Ollama may come later). It talks to
  `mlx_lm.server` over HTTP rather than importing `mlx_lm`, so the game stays stdlib-only,
  timeouts are real, and the server can live in whatever venv has MLX in it.
- mlx_lm.server and DeepSeek both speak the OpenAI-style `/v1/chat/completions` API, so
  `ChatCompletionsBackend` holds the wire code and each backend is a few lines of defaults
  (URL, model, timeout, auth header). An Ollama backend would be the same shape.
- `DEEPSEEK_API_KEY` is read from the environment and only ever sent as a bearer header.
  `--llm deepseek` with no key is a usage error before the game starts.
- The stock line is **always** drawn from `random`, then offered to the model as a tone
  reference and used as the fallback. That keeps the RNG stream identical with the model on
  or off, so `--seed` reproduces mechanics regardless of backend.
- **NPCs never say numbers.** A 4B model quoted a 200¢ shakedown as "twenty credits"; a wrong
  price reads as the game lying. Prompts ask for no numbers, and any line containing digits or
  number words falls back to stock. Keep amounts out of situation prompts.
- Three consecutive backend failures switch to stock lines for the rest of the session, with
  one notice naming the error, so a dead server or bad key can't add a timeout to every line.
- No config file yet: CLI flags plus `CYBERLIFE_LLM`, `CYBERLIFE_LLM_URL`,
  `CYBERLIFE_LLM_MODEL` env vars.
- Test backends with a stub or a fake `post=` transport; the suite's `no_network` fixture
  fails any test that opens a socket.

---

## 3. Dating sim elements: encounters at the bar — ✅ first pass done

Shipped: `cyberlife/romance.py`. With `data.ENCOUNTER_CHANCE` (30%) per bar visit while
single, a procedurally generated woman appears: appearance, job, temperament, two interests, a
value, a pet peeve and an attitude to chrome, all from weighted tables in `data.py`. Accepting
starts a five-round conversation. Each round she says a line and you pick one of three shuffled
replies (good/bad/neutral against her hidden traits: +1/-1/0). She walks out at net -3.
`max(0, net)` indexes `data.DATE_OUTCOMES`; a perfect 5 stores her as `Player.partner`.

Decisions made along the way (these differ from the original sketch below):

- **Generated people, not a fixed `data.PEOPLE` cast**, for replay value. Nobody is persisted
  unless you end up together, so "met before" doesn't exist yet.
- **Choices, not skill checks.** Charm doesn't enter into it; you win by reading her. Stock
  "bad" replies are written to sound reasonable (a mismatch, not rudeness) so it isn't obvious.
- The model gets one JSON call per round that returns her line plus the three replies, with
  the good/bad/neutral intent of each already decided in Python. Malformed JSON falls back to
  stock for that round and doesn't count towards the dead-backend limit. Stock lines, shuffle
  order and reaction beats are always drawn from `random` first, as with NPC lines.
- The number filter doesn't apply to date dialog: no price or stat rides on it.
- The only reward is stress relief. No cred, no money, no humanity (that's item 4's to give).

Still open from the sketch: eligibility gates on who you can meet (heat, chrome), more venues,
and meeting someone again. The original notes follow.

**Depends on:** item 1 (persisting who you've met). Better with item 2, fine without it.

**Shape**

- `actions.bar` grows an encounter branch: on some rolls you meet someone instead of getting
  the current stranger/brawl outcomes. Candidates come from a new `data.PEOPLE` table —
  name, archetype, where they hang out, what they like, an opening line.
- Who you can meet should be gated the way events are: an `eligibility` predicate over the
  player (the corpo fixer's sister doesn't sit down with someone carrying 8 heat; the
  netrunner notices your chrome). Reuse the `(weight, handler, predicate)` shape from
  `events.EVENTS` rather than inventing a second selection mechanism.
- An encounter is a short scene: a few dialog beats with 2-3 choices each, resolved against
  `charm` (and sometimes `hacking`/`muscle`/`humanity` — chrome can unsettle people).
  Outcome sets a starting `affection` and whether they'll see you again.
- Probably wants a second venue eventually so the bar isn't the only social surface —
  the ripperdoc's waiting room, a noodle stand, a netrunner den.

**Balance note:** the bar is currently a cheap stress dump. Encounters shouldn't also hand
out cred or money — see the Balance notes in `CLAUDE.md`. Their payoff is item 4.

**Tests:** encounter selection respects eligibility; each scene reaches an end state for any
choice path (parametrize over choices the way `test_each_handler_runs_when_eligible` does);
declining is free and costs no action point; an encounter with someone already met doesn't
restart the introduction.

---

## 4. Relationship development

**Depends on:** item 3. `Player.partner` already holds the full generated profile (ids into
the `data.DATE_*` tables plus `since_day`), so her interests and peeves can drive this item's
content. It's a single partner, not a dict of relationships yet.

**Shape**

- `Player.relationships: dict[str, Relationship]` keyed by person id. A `Relationship`
  dataclass holds `affection`, `trust`, `stage` (acquaintance → seeing each other → serious),
  `last_seen_day`, and flags for what they know about you.
- New action: **Spend time with someone** — one action point, options like a walk, a meal,
  staying in. Effects: `-stress`, `+humanity` (the one reliable humanity source in the game,
  which gives chrome a real cost), `+affection`.
- Relationships decay if neglected: `night()` drops `affection` after N days without contact.
  This is the pressure that makes the action-point economy interesting — a day spent on a
  person is a day not spent earning rent.
- Stage gates content: partners move in (rent split, but eviction hurts two people), give
  you gear or a fixer contact, or ask you to stop taking gigs. Heat and humanity should
  matter — a cyberpsycho-adjacent runner with 90 heat gets left.
- **Endings need to change.** `ending()` maps a single string to text today; it should also
  report who you left behind and whether they came with you. "Buy the visa" reads very
  differently when someone is waiting at the shuttle — that's the emotional payoff for the
  whole system. The visa could even cost more for two.

**Tests:** affection changes and stage transitions at thresholds; decay after neglect and
no decay when seen; relationship-gated content unlocks only at the right stage; a partner
leaves on a heat/humanity trigger; endings render with and without a partner; relationships
round-trip through save/load.

**Design caution:** keep people from reading as stat dispensers you farm for humanity. Their
asks should sometimes conflict with what's optimal.

---

## 5. Next phases: life after Neo-Vasilisk

**Depends on:** items 1 and 4. This is the biggest item by a wide margin — probably worth
splitting once the shape is clearer.

**Why:** both current endings are a fade to black about 60 days in. The visa ending in
particular sets up a place the player never sees.

**Shape**

- Winning becomes a **transition** instead of a terminal state: `ending()` stays for the
  loss paths, but `won` routes into a new chapter with its own location, economy, and
  win/lose conditions. `game.run` becomes a chapter loop over a list of chapter modules,
  each exposing `day_loop`/`night`/`ending`, with the `Player` carried across.
- The two win paths should lead somewhere genuinely different:
  - **Visa** → the orbital station. Clean, bright, and you're the poorest person there.
    Your street skills are worthless; your chrome is conspicuous; rent is replaced by
    citizenship review. The threat is being sent back down.
  - **Legend** → you stay and run the Sprawl. Territory, crew, rival fixers. A different
    game: you spend days on other people's problems and the resource is loyalty, not credits.
- Carry-over rules matter and should be decided early: chrome and humanity persist,
  credits convert at a brutal rate, cred means nothing upstairs (or everything downstairs),
  relationships come with you or don't depending on item 4.
- `data.py` will need splitting into per-chapter content modules at this point.

**Do first:** a one-page design note on the orbital chapter's core loop before writing code.
The Sprawl loop works because rent is a clock; the station needs its own clock, and that's
the part to figure out on paper.

**Tests:** chapter transition preserves the right fields and converts the rest; each chapter
reaches an ending under random play (extend the fuzz test to run through transitions);
chapter-specific loss conditions fire; a mid-chapter save loads into the right chapter.

---

## 6. Difficulty settings (incl. optional permadeath)

**Depends on:** item 1 (shipped).

**Why:** the save system deliberately left this open. Five slots and a manual save make the
game forgiving by default; some players want the original stakes back, and later chapters
(item 5) will want a way to skip the early grind for testing.

**Shape**

- A `Difficulty` record in `data.py` — not scattered `if hard:` branches — holding
  multipliers and flags the rest of the code reads: starting credits, rent scaling,
  gig success modifier, event severity, and `permadeath: bool`.
- Chosen at character creation, stored on `Player`, and persisted (it's just another field,
  which the save format already tolerates).
- **Permadeath on:** manual saving is disabled, the autosave slot is the only state, and
  `game.finish()` deletes it as it does today. The honest version also removes the
  quit-and-reload escape — save-on-quit should write and then refuse to load that slot
  twice, or simply delete on load.
- **Permadeath off (default):** manual saves and reloading stay as they are now.
- Worth considering: a `--dev` difficulty that starts on day 40 with credits and chrome,
  purely to reach late-game content without playing 40 days by hand. This is the cheapest
  way to make item 5 testable.

**Tests:** each difficulty's modifiers actually apply; permadeath blocks manual save and
clears the slot on death; difficulty round-trips through save/load; a save written before
difficulty existed loads at the default.
