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

## 2. LLM-driven NPC dialog (local model or DeepSeek API) — 🟡 local done, DeepSeek next

Shipped: `cyberlife/llm.py` with `respond()`/`speak()`, `CannedBackend` (default) and
`MlxBackend`, five NPCs in `data.NPCS`, `--llm off|mlx`.

Decisions made along the way:

- **MLX instead of Ollama** for the local backend (Ollama may come later). It talks to
  `mlx_lm.server` over HTTP rather than importing `mlx_lm`, so the game stays stdlib-only,
  timeouts are real, and the server can live in whatever venv has MLX in it.
- That server speaks the OpenAI-style `/v1/chat/completions` API, and so does DeepSeek:
  `ChatCompletionsBackend` holds the wire code. **`DeepSeekBackend` should be a small subclass**
  — base URL `https://api.deepseek.com`, `Authorization: Bearer $DEEPSEEK_API_KEY` in
  `headers`, a default `model` — plus a `BACKENDS` entry. An Ollama backend would be the same
  shape (it serves `/v1/chat/completions` too).
- The stock line is **always** drawn from `random`, then offered to the model as a tone
  reference and used as the fallback. That keeps the RNG stream identical with the model on
  or off, so `--seed` reproduces mechanics regardless of backend.
- **NPCs never say numbers.** A 4B model quoted a 200¢ shakedown as "twenty credits"; a wrong
  price reads as the game lying. Prompts ask for no numbers, and any line containing digits or
  number words falls back to stock. Keep amounts out of situation prompts.
- Three consecutive backend failures switch to stock lines for the rest of the session, with
  one notice, so a dead server can't add a timeout to every conversation.
- No config file yet: CLI flags plus `CYBERLIFE_LLM`, `CYBERLIFE_LLM_URL`,
  `CYBERLIFE_LLM_MODEL` env vars.

Original plan, for the DeepSeek half:

**Why:** the game's text is currently a fixed flavor table. Generated dialog is what makes
NPCs feel like people rather than stat vending machines — and it's the foundation for items 3 and 4.

**Shape**

- `cyberlife/llm.py` exposing one function, something like
  `respond(npc, player, situation) -> str`, plus a `Backend` protocol with three
  implementations: `OllamaBackend` (local, `http://localhost:11434`), `DeepSeekBackend`
  (reads `DEEPSEEK_API_KEY` from the environment — never from a file in the repo), and
  `CannedBackend` that returns lines from `data.py`.
- **`CannedBackend` is the default.** The game must stay fully playable, deterministic, and
  offline with no model configured. Select the backend with `--llm ollama|deepseek|off`
  or a config file written by item 1.
- Prompt construction lives in one place: a system prompt carrying the NPC's persona card
  (name, role, disposition toward the player, 2-3 memorable facts) plus a compact player
  summary (handle, background, cred, heat, notable chrome). Keep it small — this gets called
  a lot and local models have short attention spans.
- Treat model output as untrusted text: cap length, strip ANSI escapes before printing, and
  never let it decide stat changes. **Mechanics stay in Python** — the LLM narrates the
  outcome the code already chose. This keeps the game fair and the tests meaningful.
- Timeout hard (~5s) and fall back to canned lines on any error. A dead Ollama process
  should degrade the flavor text, not end the run.

**Tests:** `CannedBackend` is deterministic under `--seed`; a stub backend that raises falls
back to canned; a stub returning 10KB of ANSI garbage gets truncated and sanitized; prompt
builder includes persona and player facts. Real backends are tested against a fake HTTP
transport — the suite never opens a socket.

---

## 3. Dating sim elements: encounters at the bar

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

**Depends on:** item 3.

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
