"""Random night-time events. Each handler mutates the player and narrates."""
import random

from . import data
from .ui import say, dim, red, green, cyan, yellow, neon, ask_yes_no


def _r(*parts):
    say("   " + dim("→ ") + "  ".join(p for p in parts if p))


# --- handlers ----------------------------------------------------------

def rain(p):
    say("Acid rain all night. The city sounds almost gentle through the window.")
    p.stress -= 4
    _r(green("-4 stress"))


def blackout(p):
    say("A grid blackout hits the block. No lights, no Net, no sleep.")
    p.energy_penalty = 1
    _r(red("-1 action tomorrow"))


def corpo_sweep(p):
    say(red("Vexcorp security sweeps the building. Your name is on a list."))
    if p.skill("charm") >= 4 and random.random() < 0.5:
        say(green("You talk your way out of it. Barely."))
        p.heat = 0
        return
    fine = min(p.credits, 150 + 80 * p.heat)
    p.credits -= fine
    p.heat = max(0, p.heat - 2)
    _r(red(f"-{fine}¢"), green("-2 heat"))


def fixer_ping(p):
    say("03:12. Marrow pings: \"Quick one. Ten minutes. Yes or no?\"")
    if not ask_yes_no("Take it?"):
        say(dim("You roll over. The city can wait."))
        return
    if random.random() < 0.4 + 0.07 * p.skill("hacking"):
        pay = random.randint(200, 400)
        p.credits += pay
        p.cred += 1
        say(green("Done before the coffee's cold."))
        _r(green(f"+{pay}¢"), green("+1 cred"))
    else:
        p.health -= 10
        p.heat += 2
        say(red("It goes sideways. You leave in a hurry."))
        _r(red("-10 HP"), red("+2 heat"))


def chip_dealer(p):
    say("A kid in the stairwell sells skill-chips out of a lunchbox. 300¢, no refunds.")
    if p.credits < 300 or not ask_yes_no("Buy one?"):
        return
    p.credits -= 300
    if random.random() < 0.55:
        skill = random.choice(list(p.skills))
        p.skills[skill] += 1
        say(green(f"It's legit. {skill.capitalize()} +1."))
        _r(red("-300¢"), green(f"+1 {skill}"))
    else:
        p.stress += 15
        say(red("Malware. Your vision strobes for hours."))
        _r(red("-300¢"), red("+15 stress"))


def landlord(p):
    say("A note under the door: \"Market adjustment.\" Rent goes up 50¢.")
    p.rent += 50
    _r(red(f"rent now {p.rent}¢"))


def old_friend(p):
    say("Someone from before all this calls. You talk until the sky goes grey.")
    p.stress -= 10
    p.humanity += 3
    _r(green("-10 stress"), green("+3 humanity"))


def bad_noodles(p):
    say("The noodle stand's 'chicken' was not chicken.")
    p.health -= 8
    _r(red("-8 HP"))


def chrome_glitch(p):
    say(neon("Your chrome glitches. For a second, your hands aren't yours."))
    p.humanity -= 4
    p.stress += 6
    _r(red("-4 humanity"), red("+6 stress"))


def lucky_find(p):
    amt = random.randint(80, 300)
    say(f"A dead drop nobody came back for. {amt}¢ in a cred-stick.")
    p.credits += amt
    _r(green(f"+{amt}¢"))


def shakedown(p):
    say(red("Two Kestrels corner you by the lift. \"Tax time.\""))
    demand = min(p.credits, 200)
    if ask_yes_no(f"Pay them {demand}¢?"):
        p.credits -= demand
        _r(red(f"-{demand}¢"))
        return
    if random.random() < 0.15 + 0.1 * p.skill("muscle"):
        say(green("You put one down. The other runs."))
        p.cred += 3
        _r(green("+3 cred"))
    else:
        p.health -= 18
        p.credits -= demand
        say(red("They take the money and leave you a reminder."))
        _r(red("-18 HP"), red(f"-{demand}¢"))


def quiet_dream(p):
    say("You dream of a place with no ads. You almost remember your own face.")
    p.humanity += 4
    _r(green("+4 humanity"))


def quiet_night(p):
    say(dim("Nothing happens. In this city, that's a gift."))


# --- table: (weight, handler, eligibility) ----------------------------

EVENTS = [
    (10, quiet_night,   lambda p: True),
    (6,  rain,          lambda p: True),
    (4,  blackout,      lambda p: True),
    (8,  corpo_sweep,   lambda p: p.heat >= 3),
    (5,  fixer_ping,    lambda p: p.cred >= 3),
    (3,  chip_dealer,   lambda p: p.credits >= 300),
    (3,  landlord,      lambda p: p.day >= 14),
    (4,  old_friend,    lambda p: True),
    (4,  bad_noodles,   lambda p: True),
    (5,  chrome_glitch, lambda p: len(p.cyberware) >= 1),
    (4,  lucky_find,    lambda p: True),
    (4,  shakedown,     lambda p: p.cred >= 5),
    (4,  quiet_dream,   lambda p: p.humanity < 70),
]


def night_event(player):
    pool = [(w, h) for w, h, ok in EVENTS if ok(player)]
    weights = [w for w, _ in pool]
    handler = random.choices([h for _, h in pool], weights=weights)[0]
    handler(player)
    player.clamp()
