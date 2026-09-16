"""Things the player can spend action points on during the day."""
import random

from . import data
from .ui import say, dim, green, red, yellow, cyan, neon, bold, menu, ask_yes_no, header


def _delta(label, amount, good_when_positive=True):
    """Format a stat change, e.g. '+40¢' in green or '-10 HP' in red."""
    if amount == 0:
        return ""
    sign = "+" if amount > 0 else ""
    good = (amount > 0) == good_when_positive
    return (green if good else red)(f"{sign}{amount} {label}")


def _report(*parts):
    parts = [p for p in parts if p]
    if parts:
        say("   " + dim("→ ") + "  ".join(parts))


def _meets(player, req):
    return req is None or player.skill(req[0]) >= req[1]


# -- Work -------------------------------------------------------------

def work(player):
    if player.job is None:
        if not _pick_job(player):
            return False
    job = player.job
    say(random.choice(data.WORK_FLAVOR))
    pay = job["pay"] + random.randint(-10, 10)
    stress = job["stress"]
    player.credits += pay
    player.stress += stress
    _report(_delta("¢", pay), _delta("stress", stress, good_when_positive=False))
    if job["req"] and random.random() < 0.15:
        skill = job["req"][0]
        player.skills[skill] += 1
        say(dim(f"   You picked something up on the job.") + " " + _delta(skill, 1))
    return True


def _pick_job(player):
    say(dim("You scroll the job boards. Most of it is garbage."))
    options = []
    for job in data.JOBS:
        req = job["req"]
        req_txt = "" if req is None else dim(f"  (needs {req[0]} {req[1]})")
        label = f"{job['name']:<32} {yellow(str(job['pay']) + '¢')}/shift{req_txt}"
        if not _meets(player, req):
            label = dim(job["name"].ljust(32)) + dim(f" {job['pay']}¢/shift  (needs {req[0]} {req[1]})")
        options.append(label)
    options.append(dim("Never mind"))
    choice = menu("Take a job:", options)
    if choice == len(data.JOBS):
        return False
    job = data.JOBS[choice]
    if not _meets(player, job["req"]):
        say(red("You don't qualify. Yet."))
        return False
    player.job = job
    say(green(f"You're now working as: {job['name']}."))
    return True


def quit_job(player):
    """Free action: does not spend an action point."""
    if player.job:
        say(dim(f"You ghost {player.job['name']}. They won't miss you."))
        player.job = None


# -- Gigs -------------------------------------------------------------

def gig(player):
    say(dim("Your fixer, Marrow, pings you a list. No guarantees."))
    options = []
    for g in data.GIGS:
        chance = _gig_chance(player, g)
        lo, hi = g["pay"]
        options.append(
            f"{g['name']:<32} {yellow(f'{lo}-{hi}¢')}  "
            f"{dim(g['skill'])} {cyan(f'{int(chance * 100)}%')}  heat +{g['heat']}"
        )
    options.append(dim("Never mind"))
    choice = menu("Take a gig:", options)
    if choice == len(data.GIGS):
        return False
    g = data.GIGS[choice]
    say(dim("You take the job."))
    player.heat += g["heat"]
    if random.random() < _gig_chance(player, g):
        pay = random.randint(*g["pay"])
        player.credits += pay
        player.cred += g["cred"]
        player.stress += 6
        say(green("Clean. In and out."))
        _report(_delta("¢", pay), _delta("cred", g["cred"]), _delta("stress", 6, False))
        if random.random() < 0.25:
            player.skills[g["skill"]] += 1
            _report(_delta(g["skill"], 1))
    else:
        dmg = random.randint(8, 20) * g["heat"] // 2 + 5
        lost = min(player.credits, random.randint(50, 150) * g["heat"])
        player.health -= dmg
        player.credits -= lost
        player.stress += 12
        player.cred -= 1
        say(red(g["fail"]))
        _report(_delta("HP", -dmg), _delta("¢", -lost), _delta("stress", 12, False), _delta("cred", -1))
    return True


def _gig_chance(player, g):
    chance = g["base"] + 0.07 * player.skill(g["skill"]) - 0.03 * player.heat
    return max(0.05, min(0.95, chance))


# -- Self-improvement -------------------------------------------------

def train(player):
    options = [f"{s.capitalize():<10} {dim('lvl')} {player.skill(s)}" for s in player.skills]
    options.append(dim("Never mind"))
    choice = menu("Train what?", options)
    if choice == len(player.skills):
        return False
    skill = list(player.skills)[choice]
    level = player.skills[skill]
    chance = max(0.2, 0.9 - 0.1 * level)
    player.stress += 4
    if random.random() < chance:
        player.skills[skill] += 1
        say(green(f"It clicks. {skill.capitalize()} is now {player.skill(skill)}."))
        _report(_delta(skill, 1), _delta("stress", 4, False))
    else:
        say(dim("You grind for hours and feel exactly the same."))
        _report(_delta("stress", 4, False))
    return True


def rest(player):
    say(dim("You pull the blackout curtain and let the city hum without you."))
    heal = 12
    calm = 22
    player.health += heal
    player.stress -= calm
    _report(_delta("HP", heal), _delta("stress", -calm, False))
    return True


def bar(player):
    cost = 40
    if player.credits < cost:
        say(red("You can't even afford a drink. That's a new low."))
        return False
    player.credits -= cost
    say(random.choice(data.BAR_FLAVOR))
    player.stress -= 12
    cred = 1 if random.random() < 0.3 else 0
    player.cred += cred
    _report(_delta("¢", -cost), _delta("stress", -12, False), _delta("cred", cred))
    roll = random.random()
    if roll < 0.15:
        say(cyan("A stranger buys you a round and talks. You listen. You learn."))
        player.skills["charm"] += 1
        _report(_delta("charm", 1))
    elif roll < 0.25:
        say(red("Someone doesn't like your face. Chairs get involved."))
        if player.skill("muscle") >= 3:
            say(green("You win. The room notices."))
            player.cred += 2
            _report(_delta("cred", 2))
        else:
            player.health -= 10
            _report(_delta("HP", -10))
    return True


# -- Shops ------------------------------------------------------------

def ripperdoc(player):
    header("Doc Saito's Chrome Clinic")
    say(dim("\"Sit. Don't touch anything. What do you want to lose today?\""))
    while True:
        options = []
        for cw in data.CYBERWARE:
            owned = player.has(cw["id"])
            bonus = ", ".join(f"+{v} {k.replace('max_', 'max ')}" for k, v in cw["bonus"].items())
            line = f"{cw['name']:<20} {yellow(str(cw['cost']) + '¢'):<14} {dim(bonus)}  {red(f'-{cw['humanity']} humanity')}"
            options.append(dim(cw["name"].ljust(20) + " (installed)") if owned else line)
        options.append(f"{'Stim-pack (+30 HP)':<20} {yellow('150¢')}")
        options.append(dim("Leave"))
        choice = menu(f"Credits: {player.credits}¢   Humanity: {player.humanity}", options)
        if choice == len(options) - 1:
            return False
        if choice == len(options) - 2:
            if player.credits < 150:
                say(red("Not enough credits."))
                continue
            player.credits -= 150
            player.health += 30
            _report(_delta("¢", -150), _delta("HP", 30))
            player.clamp()
            continue
        cw = data.CYBERWARE[choice]
        if player.has(cw["id"]):
            say(dim("Already installed."))
            continue
        if player.credits < cw["cost"]:
            say(red("Not enough credits."))
            continue
        say(dim(cw["blurb"]))
        if player.humanity - cw["humanity"] <= 20:
            say(red("Saito frowns. \"Any more chrome and I'm not sure who wakes up.\""))
        if not ask_yes_no(f"Install {cw['name']} for {cw['cost']}¢?"):
            continue
        player.credits -= cw["cost"]
        player.humanity -= cw["humanity"]
        player.cyberware.append(cw["id"])
        say(neon("The anesthetic tastes like copper. When you wake up, you're different."))
        _report(_delta("¢", -cw["cost"]), _delta("humanity", -cw["humanity"]))
        player.clamp()
        return True   # surgery costs an action point


def fixer(player):
    header("Marrow's Booth, back of the Neon Lotus")
    say(dim("\"You want out? Everybody wants out. Question is what you'll pay.\""))
    say(f"  Forged orbital visa: {yellow(str(data.VISA_COST) + '¢')}   (you have {player.credits}¢)")
    say(f"  Or make a name for yourself: street cred {player.cred}/{data.LEGEND_CRED}")
    say()
    if player.credits >= data.VISA_COST:
        if ask_yes_no("Buy the visa and leave the city for good?"):
            player.credits -= data.VISA_COST
            player.won = "visa"
            return True
    else:
        say(dim("Marrow laughs. \"Come back when you're serious.\""))
    return False
