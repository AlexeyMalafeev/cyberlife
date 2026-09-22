"""Static game content: backgrounds, jobs, gigs, cyberware, flavor text."""

CITY = "Neo-Vasilisk"
VISA_COST = 15_000
LEGEND_CRED = 100
RENT_EVERY = 7
MAX_MISSED_RENT = 3
SAVE_SLOTS = 5

BACKGROUNDS = {
    "Street Kid": {
        "blurb": "Grew up in the Sprawl. You know every alley and every knife.",
        "skills": {"hacking": 1, "muscle": 3, "charm": 2},
        "credits": 400, "cred": 8,
    },
    "Corpo Dropout": {
        "blurb": "Walked out of a tower job with a severance chip and a nice coat.",
        "skills": {"hacking": 2, "muscle": 1, "charm": 3},
        "credits": 1800, "cred": 0,
    },
    "Netrunner": {
        "blurb": "You've spent more hours in the Net than in your own skin.",
        "skills": {"hacking": 4, "muscle": 1, "charm": 1},
        "credits": 700, "cred": 3,
    },
}

# Legit work: steady credits, steady stress. req = (skill, level) or None.
JOBS = [
    {"id": "noodle",    "name": "Noodle stand shift",           "pay": 70,  "stress": 9,  "req": None},
    {"id": "courier",   "name": "Courier for QuikDrop",         "pay": 100, "stress": 10, "req": ("muscle", 2)},
    {"id": "dataentry", "name": "Data-entry drone, Kiroshi",    "pay": 140, "stress": 12, "req": ("hacking", 3)},
    {"id": "promoter",  "name": "Club promoter, Neon Lotus",    "pay": 160, "stress": 11, "req": ("charm", 4)},
    {"id": "security",  "name": "Security contractor, Vexcorp", "pay": 240, "stress": 14, "req": ("muscle", 5)},
    {"id": "netrunner", "name": "Junior netrunner, Tessier",    "pay": 320, "stress": 16, "req": ("hacking", 6)},
]

# Gigs: risky, skill-checked. chance = base + 0.07 * skill.
GIGS = [
    {"name": "Scrub a fixer's ledger",        "skill": "hacking", "base": 0.35,
     "pay": (250, 450), "cred": 2, "heat": 1, "fail": "The ICE bites back. Your nose bleeds for an hour."},
    {"name": "Bounce at a black-market club", "skill": "muscle",  "base": 0.40,
     "pay": (200, 380), "cred": 2, "heat": 1, "fail": "Some chromed-up gonk lays you out cold."},
    {"name": "Smuggle a chipped briefcase",   "skill": "charm",   "base": 0.40,
     "pay": (220, 420), "cred": 2, "heat": 1, "fail": "The checkpoint doesn't buy your story."},
    {"name": "Crack a Vexcorp data-vault",    "skill": "hacking", "base": 0.15,
     "pay": (900, 1600), "cred": 6, "heat": 3, "fail": "Black ICE. You wake up on the floor, hours gone."},
    {"name": "Collect a debt for the Kestrels","skill": "muscle", "base": 0.20,
     "pay": (700, 1200), "cred": 5, "heat": 3, "fail": "The debtor had friends. Lots of friends."},
    {"name": "Con a corpo out of a keycard",  "skill": "charm",   "base": 0.20,
     "pay": (800, 1400), "cred": 5, "heat": 3, "fail": "Security recognises the grift halfway through."},
]

# Cyberware: permanent bonuses at the cost of humanity.
CYBERWARE = [
    {"id": "optics",   "name": "Kiroshi Optics",      "cost": 1500, "humanity": 8,
     "bonus": {"hacking": 1, "charm": 1}, "blurb": "Zoom, low-light, and a HUD that never turns off."},
    {"id": "voice",    "name": "Voice Modulator",     "cost": 1200, "humanity": 8,
     "bonus": {"charm": 2}, "blurb": "Say it once, they'll believe it."},
    {"id": "lungs",    "name": "Synth-Lungs",         "cost": 1800, "humanity": 6,
     "bonus": {"max_energy": 1}, "blurb": "One more action every day. Smog-proof."},
    {"id": "dermal",   "name": "Subdermal Armor",     "cost": 2500, "humanity": 12,
     "bonus": {"muscle": 2, "max_health": 25}, "blurb": "Bullets bruise instead of kill."},
    {"id": "coproc",   "name": "Neural Coprocessor",  "cost": 4000, "humanity": 15,
     "bonus": {"hacking": 3}, "blurb": "Think in parallel. Sleep in binary."},
    {"id": "reflex",   "name": "Reflex Booster",      "cost": 6000, "humanity": 18,
     "bonus": {"muscle": 2, "hacking": 1, "max_energy": 1}, "blurb": "The world slows down. You don't."},
]

WORK_FLAVOR = [
    "The shift blurs past under flickering fluorescents.",
    "Your supervisor's optics track you the whole time.",
    "Rain hammers the window. Somewhere, a siren.",
    "You count the seconds until your neural clock says you're done.",
    "A coworker whispers about a gig. You pretend not to hear.",
]

BAR_FLAVOR = [
    "The Neon Lotus is loud enough to forget things.",
    "A synth-jazz trio plays to nobody in particular.",
    "The bartender pours something blue and doesn't ask questions.",
    "Holo-ads flicker across the sweat on the walls.",
]


def job_by_id(job_id):
    """Look up a job dict by its id, or None."""
    return next((j for j in JOBS if j["id"] == job_id), None)
