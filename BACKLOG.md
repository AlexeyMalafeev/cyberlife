# Backlog

Planned features, roughly in dependency order. Each entry notes where it lands in the
architecture described in `CLAUDE.md`. Nothing here is committed to a schedule; reorder freely.

Ground rules that apply to all of them:

- Every item ships with tests in the same commit (see the Testing section of `CLAUDE.md`).
- New content goes in `data.py` tables, not inline in logic.
- All input goes through `ui._read`; all randomness through `random` so `--seed` stays reproducible.
- The suite must run offline and take no real time — no network, no sleeps.

---

## 1. Save / load game state

**Why first:** everything below adds fields to `Player`, and a save format written after the
fact has to migrate them. Doing it now means later features only add a key.

**Shape**

- `cyberlife/save.py` with `save(player, path)` / `load(path) -> Player`, JSON via
  `dataclasses.asdict`. Default location `~/.cyberlife/save.json`, overridable with `--save PATH`.
- `player.job` currently holds a `data.JOBS` dict *by identity*. That doesn't round-trip —
  give jobs an `id` field like cyberware has, store the id, and resolve on load. This is the
  one real refactor in this item; `actions.work` and `game.show_status` touch it.
- Add a `SAVE_VERSION` int. `load` rejects a newer version with a clear message and
  fills in missing keys from `Player`'s defaults so old saves keep working.
- Autosave at the end of `night()`; offer "Continue" on the title screen when a save exists.
- On an ending, delete the save (or move it to `save.dead.json` for a post-mortem screen).

**Tests:** round-trip a player with cyberware/job/relationships and assert field equality;
load a save missing a key added later; reject a future version; autosave writes after night;
ending clears the save. Use pytest's `tmp_path`, never the real home directory.

**Open question:** one save slot or several? One is simpler and fits the
permadeath tone; several is friendlier for testing later-game content.

---

## 2. LLM-driven NPC dialog (local model or DeepSeek API)

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
