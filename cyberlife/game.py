"""Main game loop."""
import random

import time

from . import actions, data, events, save
from .player import Player
from .ui import (QuitGame, say, hr, header, bar, bold, dim, red, green,
                 yellow, cyan, neon, menu, ask_text, ask_yes_no, pause)


def _slot_label(info, n):
    if info is None:
        return dim(f"Slot {n}  -  empty")
    if info["unreadable"]:
        return dim(f"Slot {n}  -  damaged save")
    ago = max(0, int((time.time() - info["saved_at"]) / 60))
    when = "just now" if ago < 1 else (f"{ago}m ago" if ago < 60 else f"{ago // 60}h ago")
    day, creds = info["day"], info["credits"]
    stale = dim("  (older save)") if info["stale"] else ""
    return (f"Slot {n}  {bold(info['handle'])} the {info['background']}  "
            f"{dim(f'day {day}')}  {yellow(f'{creds}c')}  {dim(when)}{stale}")


def pick_slot(prompt, slots, allow_empty=True, allow_cancel=True):
    """Return a slot number, or None if cancelled."""
    options, numbers = [], []
    for i, info in enumerate(slots, 1):
        if info is None and not allow_empty:
            continue
        options.append(_slot_label(info, i))
        numbers.append(i)
    if not options:
        return None
    if allow_cancel:
        options.append(dim("Back"))
    choice = menu(prompt, options)
    if allow_cancel and choice == len(options) - 1:
        return None
    return numbers[choice]


def title_screen():
    """Return a Player: either loaded from a slot or freshly created."""
    header(f"C Y B E R L I F E   ·   {data.CITY}, 2087")
    slots = save.list_slots()
    if not any(slots):
        return create_character()
    recent = save.latest(slots)
    options, kinds = [], []
    if recent is not None:
        info = slots[recent - 1]
        options.append(f"Continue  {bold(info['handle'])}, day {info['day']}")
        kinds.append("continue")
    options += ["Load a run", "New run"]
    kinds += ["load", "new"]
    kind = kinds[menu("", options)]
    if kind == "new":
        return create_character()
    slot = recent if kind == "continue" else pick_slot("Load which run?", slots, allow_empty=False)
    if slot is None:
        return title_screen()
    return _load_or_none(slot) or title_screen()


def _load_or_none(slot):
    try:
        player = save.read(slot)
    except save.SaveError as exc:
        say(red(str(exc)))
        return None
    say(green(f"Jacking back in as {player.handle}, day {player.day}."))
    pause()
    return player


def _assign_slot(player):
    """Give a new run a slot, asking which to overwrite if all are full."""
    slots = save.list_slots()
    slot = save.first_empty(slots)
    if slot is None:
        say(dim("All save slots are full."))
        slot = pick_slot("Overwrite which slot?", slots, allow_empty=False, allow_cancel=False)
    save.write(player, slot)
    say(dim(f"Autosaving to slot {slot} each night."))


def create_character():
    header(f"{data.CITY}, 2087")
    say(dim("Rent is due, the air is poison, and everybody's selling something."))
    say(dim("You're going to get out of here. Somehow."))
    say()
    name = ask_text("Your name?", "Kai")
    handle = ask_text("Your street handle?", "Ghost")
    names = list(data.BACKGROUNDS)
    choice = menu("Where'd you come from?", [
        f"{bold(n):<24} {dim(data.BACKGROUNDS[n]['blurb'])}" for n in names
    ])
    bg = names[choice]
    info = data.BACKGROUNDS[bg]
    player = Player(name=name, handle=handle, background=bg,
                    credits=info["credits"], cred=info["cred"],
                    skills=dict(info["skills"]))
    say()
    say(neon(f"Welcome to the Sprawl, {handle}."))
    _assign_slot(player)
    pause()
    return player


def show_status(player):
    hr()
    rent_in = data.RENT_EVERY - (player.day - 1) % data.RENT_EVERY
    say(f" {bold(player.handle)} {dim('·')} {player.background} {dim('·')} "
        f"Day {yellow(player.day)} {dim('·')} rent {player.rent}¢ due in {rent_in}d")
    say(f" Credits {yellow(f'{player.credits}¢'):<16} Actions {cyan('◆' * player.energy)}{dim('◇' * (player.max_energy - player.energy))}")
    say(f" Health   {bar(player.health, player.max_health)} {player.health:>3}/{player.max_health}"
        f"   Stress   {bar(player.stress, 100, color=red)} {player.stress:>3}/100")
    say(f" Humanity {bar(player.humanity, 100, color=neon)} {player.humanity:>3}/100"
        f"   Cred {green(player.cred):<6} Heat {red(player.heat)}")
    sk = "  ".join(f"{s.capitalize()} {player.skill(s)}" for s in player.skills)
    job = player.job["name"] if player.job else dim("unemployed")
    partner = f"   {dim('Seeing:')} {neon(player.partner['name'])}" if player.partner else ""
    say(f" {dim(sk)}   {dim('Job:')} {job}{partner}")
    hr()


def autosave(player):
    if player.save_slot is None:
        return
    try:
        save.write(player, player.save_slot)
    except OSError as exc:
        say(red(f"Autosave failed: {exc}"))


def save_game(player):
    """Free action: write the run to a slot of the player's choosing."""
    slots = save.list_slots()
    slot = pick_slot("Save to which slot?", slots)
    if slot is None:
        return False
    info = slots[slot - 1]
    if info and info["slot"] != player.save_slot:
        if not ask_yes_no(f"Overwrite {info['handle']}, day {info['day']}?"):
            return False
    try:
        save.write(player, slot)
        say(green(f"Saved to slot {slot}."))
    except OSError as exc:
        say(red(f"Could not save: {exc}"))
    return False


def day_loop(player):
    player.energy = max(1, player.max_energy - player.energy_penalty)
    player.energy_penalty = 0
    while player.energy > 0 and not player.won:
        show_status(player)
        options = [
            ("Work" + (dim(f"  ({player.job['name']})") if player.job else dim("  (find a job)")), actions.work),
            ("Run a gig" + dim("  (risky, pays)"), actions.gig),
            ("Train a skill", actions.train),
            ("Rest" + dim("  (+HP, -stress)"), actions.rest),
            ("Hit the bar" + dim("  (40¢, -stress)"), actions.bar),
            ("Ripperdoc" + dim("  (cyberware, meds)"), actions.ripperdoc),
            ("See the fixer" + dim("  (the way out)"), actions.fixer),
        ]
        if player.job:
            options.append((dim("Quit job"), actions.quit_job))
        options.append((dim("Save game"), save_game))
        options.append((dim("End the day"), None))
        choice = menu("What now?", [label for label, _ in options])
        say()
        handler = options[choice][1]
        if handler is None:
            break
        spent = handler(player)
        if spent:
            player.energy -= 1
        player.clamp()
        if player.death_cause():
            return
        say()


def night(player):
    header(f"Night {player.day}")
    # Passive drift: sleep helps a little, heat cools, chrome itches.
    player.stress -= 6
    player.health += 3
    player.heat = max(0, player.heat - 1)
    if player.day % data.RENT_EVERY == 0:
        if player.credits >= player.rent:
            player.credits -= player.rent
            say(dim(f"Rent auto-debited: -{player.rent}¢."))
        else:
            player.missed_rent += 1
            left = data.MAX_MISSED_RENT - player.missed_rent
            say(red(f"You can't make rent. Strike {player.missed_rent}/{data.MAX_MISSED_RENT}."))
            if left > 0:
                say(red(f"{left} more and the landlord's drones change the locks."))
    say()
    events.night_event(player)
    say()
    player.day += 1
    autosave(player)


def ending(player, cause):
    header("GAME OVER" if cause else "YOU MADE IT")
    text = {
        "flatlined": "Your body is found three days later. Nobody claims it.",
        "cyberpsychosis": "The chrome wins. What's left of you walks off into the neon and never looks back.",
        "burnout": "One morning you just don't get up. The city doesn't notice.",
        "evicted": "The locks change. Everything you own fits in a bag. The Sprawl swallows you.",
        "visa": f"The shuttle lifts off and {data.CITY} shrinks to a smear of light. You don't look back. You're free.",
        "legend": f"Every fixer in {data.CITY} knows your name. You don't need a way out. You own the way in.",
    }
    say(text.get(cause or player.won, ""))
    say()
    say(dim(f"Survived {player.day - 1} days · {player.credits}¢ · cred {player.cred} · {len(player.cyberware)} pieces of chrome"))
    hr()


def run(seed=None, save_dir=None):
    if seed is not None:
        random.seed(seed)
    if save_dir is not None:
        save.set_save_dir(save_dir)
    player = None
    try:
        player = title_screen()
        while True:
            header(f"Day {player.day}")
            day_loop(player)
            cause = player.death_cause()
            if cause:
                finish(player, cause)
                return
            if player.cred >= data.LEGEND_CRED and not player.won:
                player.won = "legend"
            if player.won:
                finish(player, None)
                return
            night(player)
            cause = player.death_cause()
            if cause:
                finish(player, cause)
                return
            pause()
    except (QuitGame, KeyboardInterrupt):
        say()
        if player is not None and player.save_slot is not None:
            autosave(player)
            say(dim(f"Run saved to slot {player.save_slot}."))
        say(dim("You jack out. The city keeps running without you."))


def finish(player, cause):
    """Show the ending and retire the slot -- a finished run can't be continued."""
    if player.save_slot is not None:
        save.delete(player.save_slot)
        player.save_slot = None
    ending(player, cause)
