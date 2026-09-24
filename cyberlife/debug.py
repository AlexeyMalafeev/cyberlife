"""The debug menu (--debug): poke at game state and stage bar encounters on demand.

Everything here is a free action: it never spends an action point, and every change goes
through the same Player fields the game itself uses, so it autosaves like anything else.
"""
from . import data, events, romance
from .ui import say, dim, green, red, yellow, menu, ask_text

ENABLED = False    # set by `python3 -m cyberlife --debug`; adds "Debug" to the day menu

STATS = ["credits", "health", "stress", "humanity", "cred", "heat", "energy", "missed_rent", "day"]
CAST_FIELDS = ["affection", "times_met", "avoid_until"]


def enable(on=True):
    """Turn debug mode on (or off). Character sheets start shown; the menu toggles them."""
    global ENABLED
    ENABLED = on
    romance.SHOW_SHEETS = on


def _ask_int(label, current):
    raw = ask_text(f"{label}?", current)
    try:
        return int(raw)
    except (TypeError, ValueError):
        say(red(f"Not a number: {raw!r}"))
        return None


def _set_field(target, key, label=None):
    value = _ask_int(label or key, target[key] if isinstance(target, dict) else getattr(target, key))
    if value is None:
        return
    if isinstance(target, dict):
        target[key] = value
    else:
        setattr(target, key, value)
    say(green(f"{label or key} = {value}"))


def _cast_label(player, her):
    extra = f"met {her['times_met']}x, affection {her['affection']}"
    if her["avoid_until"] > player.day:
        extra += f", away until day {her['avoid_until']}"
    return f"{her['name']:<8} {dim(her['stage'].ljust(9))} {dim(extra)}"


def _pick_member(player, title):
    romance.ensure_cast(player)
    labels = [_cast_label(player, her) for her in player.cast]
    choice = menu(title, labels + [dim("Back")])
    return player.cast[choice] if choice < len(player.cast) else None


# -- the menu entries ------------------------------------------------------

def edit_stats(player):
    choice = menu("Set which stat?", [f"{s:<12} {dim(str(getattr(player, s)))}" for s in STATS]
                  + [dim("Back")])
    if choice < len(STATS):
        stat = STATS[choice]
        _set_field(player, stat)
        floor = 1 if stat == "day" else 0      # clamp() covers the rest, not these
        setattr(player, stat, max(floor, getattr(player, stat)))


def edit_skills(player):
    names = list(player.skills)
    choice = menu("Set which skill (base, before chrome)?",
                  [f"{s:<12} {dim(str(player.skills[s]))}" for s in names] + [dim("Back")])
    if choice < len(names):
        _set_field(player.skills, names[choice])
        player.skills[names[choice]] = max(0, player.skills[names[choice]])


def toggle_cyberware(player):
    labels = [f"{'[x]' if player.has(cw['id']) else '[ ]'} {cw['name']}" for cw in data.CYBERWARE]
    choice = menu("Install or remove:", labels + [dim("Back")])
    if choice == len(data.CYBERWARE):
        return
    cw_id = data.CYBERWARE[choice]["id"]
    if player.has(cw_id):
        player.cyberware.remove(cw_id)
        say(green(f"Removed {data.CYBERWARE[choice]['name']}."))
    else:
        player.cyberware.append(cw_id)
        say(green(f"Installed {data.CYBERWARE[choice]['name']}."))


def set_job(player):
    choice = menu("Job:", [job["name"] for job in data.JOBS] + [dim("Unemployed"), dim("Back")])
    if choice < len(data.JOBS):
        player.job_id = data.JOBS[choice]["id"]
    elif choice == len(data.JOBS):
        player.job_id = None
    else:
        return
    say(green(f"Job: {player.job['name'] if player.job else 'none'}."))


def test_encounter(player):
    """Seat one cast member at the bar, skipping the encounter roll and who's-in-tonight.
    The night counts: affection, meetings and stress change as they would in play."""
    her = _pick_member(player, "Who's at the bar?")
    if her is None:
        return
    if her["stage"] not in ("stranger", "met"):
        say(red(f"{her['name']} is {her['stage']}; set her stage to stranger or met first."))
        return
    stress = romance.meet(player, [her])
    say(dim(f"   (stress {stress:+d})"))


def edit_member(player):
    her = _pick_member(player, "Edit whom?")
    if her is None:
        return
    romance.sheet(her)
    fields = CAST_FIELDS + ["stage"]
    choice = menu(f"Set what for {her['name']}?",
                  [f"{f:<12} {dim(str(her[f]))}" for f in fields] + [dim("Back")])
    if choice < len(CAST_FIELDS):
        field = CAST_FIELDS[choice]
        _set_field(her, field)
        if field != "affection":
            her[field] = max(0, her[field])
        if her["times_met"] and her["last_outcome"] is None:
            her["last_outcome"] = 1     # a return scene needs a last night; call it lukewarm
    elif choice == len(CAST_FIELDS):
        _set_stage(player, her)


def _set_stage(player, her):
    stage = data.CAST_STAGES[menu("Stage:", list(data.CAST_STAGES))]
    if stage in data.PARTNER_STAGES:
        partner = player.partner
        if partner is not None and partner is not her:
            say(red(f"You're already with {partner['name']}; one partner at a time."))
            return
        if her["stage"] not in data.PARTNER_STAGES:
            romance.start_relationship(player, her)
    her["stage"] = stage
    say(green(f"{her['name']} is now {stage}."))


def new_cast(player):
    player.cast = []
    romance.ensure_cast(player)
    say(green("New cast: " + ", ".join(her["name"] for her in player.cast) + "."))


def run_event(player):
    labels = []
    for _, handler, ok in events.EVENTS:
        name = handler.__name__.replace("_", " ")
        labels.append(name if ok(player) else dim(f"{name}  (not eligible)"))
    choice = menu("Which night event?", labels + [dim("Back")])
    if choice == len(events.EVENTS):
        return
    _, handler, ok = events.EVENTS[choice]
    if not ok(player):
        say(red("Its conditions don't hold right now; change the state first."))
        return
    handler(player)


def toggle_sheets(player):
    romance.SHOW_SHEETS = not romance.SHOW_SHEETS
    say(green(f"Character sheets {'shown' if romance.SHOW_SHEETS else 'hidden'} before encounters."))


def debug_menu(player):
    """The day menu's "Debug" entry. Loops until Back; never spends an action point."""
    while True:
        entries = [
            ("Test an encounter with...", test_encounter),
            ("Edit a cast member", edit_member),
            (f"Character sheets: {yellow('on') if romance.SHOW_SHEETS else dim('off')}",
             toggle_sheets),
            ("Regenerate the cast", new_cast),
            ("Stats", edit_stats),
            ("Skills", edit_skills),
            ("Cyberware", toggle_cyberware),
            ("Job", set_job),
            ("Run a night event", run_event),
            (dim("Back"), None),
        ]
        choice = menu("Debug:", [label for label, _ in entries])
        handler = entries[choice][1]
        if handler is None:
            return False
        say()
        handler(player)
        player.clamp()
        say()
