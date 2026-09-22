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


# NPCs who talk. The persona card (role, disposition, facts) is what a dialog model sees;
# each situation carries a prompt describing what the code already decided, plus stock lines
# used when no model is configured or it fails. Both are str.format()ed with call-site context;
# keep amounts out of prompts -- model lines that mention numbers are thrown away (llm.py).
NPCS = {
    "marrow": {
        "name": "Marrow",
        "role": "a fixer who works out of a booth at the back of the Neon Lotus",
        "disposition": "dry, amused, transactional; respects results, not talk; calls everyone 'kid'",
        "facts": ["Sells forged orbital visas for 15,000 credits.",
                  "Nobody has ever seen Marrow stand up.",
                  "Keeps a paper ledger because paper can't be hacked."],
        "situations": {
            "booth_broke": {
                "prompt": "The player comes to your booth asking about a way out of the city, "
                          "but can't afford the visa yet. Brush them off.",
                "canned": ["You want out? Everybody wants out. Come back when you're serious, kid.",
                           "Fifteen grand, kid. I don't do layaway.",
                           "Nice to see you. Nicer to see your money. Neither's here yet."],
            },
            "booth_ready": {
                "prompt": "The player comes to your booth and has enough for the visa. "
                          "You're ready to sell if they are.",
                "canned": ["Well, look who's serious. The visa's real, kid. Mostly.",
                           "Money talks. Yours is saying 'goodbye, Neo-Vasilisk.'",
                           "You actually saved it. Most don't live that long."],
            },
            "gig_list": {
                "prompt": "You're sending the player today's list of gigs. "
                          "No guarantees about any of them.",
                "canned": ["Here's what's on the board. No guarantees, no refunds.",
                           "Fresh list. Try not to die on any of them, it's bad for business.",
                           "Pick one. Don't make me regret the referral."],
            },
            "night_ping": {
                "prompt": "It's 03:12. You're pinging the player about a quick ten-minute job "
                          "and need a yes or no right now.",
                "canned": ["Quick one. Ten minutes. Yes or no?",
                           "You up? Course you are. Ten minutes of work, now or never.",
                           "Job just fell in my lap. Ten minutes. Clock's running, kid."],
            },
        },
    },
    "saito": {
        "name": "Doc Saito",
        "role": "a back-alley ripperdoc who runs a cramped chrome clinic",
        "disposition": "curt, clinical, tired; privately worried about the people she cuts open",
        "facts": ["Lost her medical licence years ago and doesn't miss it.",
                  "Has seen too many customers go cyberpsycho.",
                  "Hums old pop songs while she operates."],
        "situations": {
            "greeting": {
                "prompt": "The player walks into your clinic. Greet them the way you greet "
                          "everyone who might want chrome.",
                "canned": ["Sit. Don't touch anything. What do you want to lose today?",
                           "Wipe your feet. You're tracking the street onto my floor.",
                           "Back again. Let's see what's left of you."],
            },
            "humanity_warning": {
                "prompt": "The player wants another implant, but it would take them dangerously "
                          "close to cyberpsychosis. Warn them. You'll still do it if they insist.",
                "canned": ["Any more chrome and I'm not sure who wakes up.",
                           "I can install it. I can't promise you'll recognise yourself after.",
                           "You're mostly machine already. Think hard about the rest."],
            },
        },
    },
    "juno": {
        "name": "Juno",
        "role": "the bartender at the Neon Lotus",
        "disposition": "warm but guarded; hears everything, repeats nothing",
        "facts": ["Has worked the Lotus bar for eleven years.",
                  "Waters down the drinks of anyone who's rude.",
                  "Owes Marrow a favour and won't say what for."],
        "situations": {
            "pour": {
                "prompt": "You're pouring the player a drink after a long day.",
                "canned": ["Rough one? This one's strong.",
                           "Same as always. Don't tell me about your day, I can see it.",
                           "Drink up. The city'll still be out there when you're done."],
            },
        },
    },
    "stranger": {
        "name": "Stranger",
        "role": "an old face-for-hire who drinks alone at the Neon Lotus",
        "disposition": "wry, generous with advice, cagey about their past",
        "facts": ["Used to talk for a living: negotiator, grifter, maybe both.",
                  "Buys drinks for people who remind them of themselves."],
        "situations": {
            "advice": {
                "prompt": "You've bought the player a round and are passing on one piece of "
                          "hard-won advice about reading people or talking your way through the city.",
                "canned": ["Never tell anyone what you want first. Let them guess wrong.",
                           "Everyone in this town is selling. Find out what they need to buy.",
                           "Smile with your eyes. Chrome ones count."],
            },
        },
    },
    "kestrels": {
        "name": "Kestrel",
        "role": "an enforcer for the Kestrels, the gang that taxes your block",
        "disposition": "bored, menacing, in no hurry",
        "facts": ["Works in pairs.",
                  "Considers the tax a public service."],
        "situations": {
            "shakedown": {
                "prompt": "You and your partner corner the player by the lift and demand "
                          "they pay the block 'tax'.",
                "canned": ["Tax time. {demand}¢, and nobody has to bleed.",
                           "Block tax. {demand}¢. We're not asking twice.",
                           "You're doing well, we hear. That's {demand}¢ well."],
            },
        },
    },
}

def job_by_id(job_id):
    """Look up a job dict by its id, or None."""
    return next((j for j in JOBS if j["id"] == job_id), None)
