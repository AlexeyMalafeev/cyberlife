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

# Legit work: steady credits, steady stress. req = (skill, level) or None. "desc" is how dialog
# prompts describe the job -- the menu label's "Role, Employer" comma reads like a name to a model.
JOBS = [
    {"id": "noodle",    "name": "Noodle stand shift",           "pay": 70,  "stress": 9,  "req": None,
     "desc": "a cook at a noodle stand"},
    {"id": "courier",   "name": "Courier for QuikDrop",         "pay": 100, "stress": 10, "req": ("muscle", 2),
     "desc": "a courier for QuikDrop, a delivery company"},
    {"id": "dataentry", "corp": True, "name": "Data-entry drone, Kiroshi",    "pay": 140, "stress": 12, "req": ("hacking", 3),
     "desc": "a data-entry clerk at Kiroshi, a corporation"},
    {"id": "promoter",  "name": "Club promoter, Neon Lotus",    "pay": 160, "stress": 11, "req": ("charm", 4),
     "desc": "a promoter for the Neon Lotus, a club and bar"},
    {"id": "security", "corp": True,  "name": "Security contractor, Vexcorp", "pay": 240, "stress": 14, "req": ("muscle", 5),
     "desc": "a security contractor for Vexcorp, a corporation"},
    {"id": "netrunner", "corp": True, "name": "Junior netrunner, Tessier",    "pay": 320, "stress": 16, "req": ("hacking", 6),
     "desc": "a junior netrunner at Tessier, a corporation"},
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


# -- Bar encounters ---------------------------------------------------
# Someone worth meeting at the Neon Lotus. Every trait is drawn from a weighted table, so a
# --seed reproduces her. Her personality decides which replies land; the player never sees it.

ENCOUNTER_CHANCE = 0.3   # per bar visit, while you're single
DATE_ROUNDS = 5          # exchanges in the conversation
DATE_WALKOUT = -3        # net score at which she leaves before the last round

# The cast: the same few women, generated at character creation, are the only ones you meet.
# Each conversation adds its net score to her affection. She'll start something only once
# you've talked enough times, she likes you enough, and the night itself goes well.
CAST_SIZE = 6
# Where each of them stands with you, in order. "gone" is someone who left you.
CAST_STAGES = ("stranger", "met", "dating", "serious", "gone")
PARTNER_STAGES = ("dating", "serious")
DATE_AT_BAR = (1, 2)            # how many of them are in when an encounter fires
DATE_MIN_MEETINGS = 3           # conversations (including tonight's) before she's your partner
DATE_PARTNER_AFFECTION = 10     # affection (including tonight's net) she needs to get there
DATE_PARTNER_NET = 3            # ...and tonight's net score
DATE_AVOID_NET = -2             # a night this bad, or a walkout, and she stays away...
DATE_AVOID_DAYS = 5             # ...for this many days
BAR_SPOTS = [
    "two stools down", "at the end of the bar", "in the corner booth", "by the jukebox",
    "under the flickering holo-sign", "at the window counter", "near the door",
]

DATE_NAMES = [
    "Mira", "Yuki", "Zara", "Nadia", "Rin", "Lena", "Ines", "Kaya", "Tamsin", "Oksana",
    "Suki", "Vesna", "Dalia", "Noor", "Ada", "Petra", "Jin", "Lux", "Marisol", "Freya",
    "Anouk", "Talia", "Ksenia", "Wren", "Ayla", "Isra", "Mei", "Sol", "Esme", "Dasha",
    "Nika", "Paz", "Rhea", "Selin", "Kira", "Lark", "Ottilie", "Zhen", "Farah", "Coco",
]
DATE_AGES = (21, 29)

# Appearance: (weight, phrase). Phrases slot mid-sentence into DATE_SCENES.
DATE_LOOKS = {
    "build": [(3, "slim"), (2, "wiry"), (2, "tall"), (2, "petite"), (1, "rangy"), (1, "curvy")],
    "hair": [
        (3, "a sharp black bob"), (2, "cropped silver hair"), (2, "long dark braids"),
        (2, "a messy auburn undercut"), (2, "neon-blue hair tied up with a chopstick"),
        (1, "a shaved head traced with circuit tattoos"), (2, "loose copper curls"),
        (1, "a pink fringe over one eye"), (2, "straight hair dyed the green of old monitors"),
        (1, "a white mohawk gone soft in the humidity"), (2, "dark hair pinned up in a hurry"),
        (1, "bleached hair with black roots"),
    ],
    "eyes": [
        (3, "dark eyes"), (2, "grey eyes"), (2, "green eyes"), (1, "one blue eye, one brown"),
        (2, "chrome optics ringed in gold"), (1, "Kiroshi optics that flicker amber"),
        (2, "tired hazel eyes"), (1, "violet-tinted contacts"), (1, "eyes lined in smudged kohl"),
        (1, "optics with slow-scrolling pupils"),
    ],
    "style": [
        (3, "a patched courier jacket"), (2, "a clinic smock under a rain shell"),
        (2, "an oversized band hoodie"), (2, "a sharp corpo blazer with the logo torn off"),
        (1, "a mesh top and a vinyl coat"), (2, "grease-stained mechanic's overalls"),
        (1, "a vintage silk dress two sizes too big"), (2, "a black turtleneck and fingerless gloves"),
        (1, "a glowing LED raincoat"), (1, "army-surplus everything"),
    ],
    "feature": [
        (2, "a neon koi tattoo curling up her neck"), (2, "a thin scar through one eyebrow"),
        (2, "a matte-black chrome forearm"), (2, "a row of silver rings along one ear"),
        (1, "freckles that the neon turns violet"), (1, "a data-jack behind her ear, capped in brass"),
        (2, "chipped black nail polish"), (1, "a barcode tattooed across her knuckles"),
        (1, "a laugh line that doesn't match her poker face"), (1, "a paper book in her coat pocket"),
        (1, "a bandage on her knuckles"), (1, "headphones older than she is"),
    ],
}

# Canned opening scene. Slots come from DATE_LOOKS, plus {spot} from BAR_SPOTS and {hint} from
# her temperament.
DATE_SCENES = [
    "A {build} woman sits {spot}: {hair}, {eyes}, {style}. You notice {feature}. {hint}",
    "There's a {build} woman {spot}, nursing a drink alone: {hair}, {eyes}, {style}. "
    "Hard to miss {feature}. {hint}",
    "A {build} woman in {style} has taken a seat {spot}. She has {hair}, {eyes} "
    "and {feature}. {hint}",
    "Through the smoke you catch a {build} woman {spot}, with {hair}, {eyes} and {feature}, "
    "in {style}. {hint}",
]

# Someone you've already met. {mood} is the "again" line of how your last night together ended.
DATE_AGAIN = [
    "{name} is {spot} again, in {style}. {mood}",
    "You spot {name} {spot}. {mood}",
    "{name}'s here tonight, {spot}. {mood}",
]

# Personality. Each id maps to a weight and a description a dialog model sees; the player
# only ever gets a temperament's vague "hint" in the opening scene.
DATE_TEMPERAMENTS = {
    "warm":     {"weight": 3, "desc": "warm and open, quick to laugh",
                 "hints": ["She's the only one in here smiling at the bartender.",
                           "She thanks the service drone like it's a person."]},
    "guarded":  {"weight": 3, "desc": "guarded, slow to trust, dry once she does",
                 "neutral_first": 1,
                 "hints": ["She keeps one eye on the door.",
                           "She's chosen the seat with her back to the wall."]},
    "playful":  {"weight": 2, "desc": "playful and teasing, bored by earnestness",
                 "hints": ["She's stacking bottle caps into a tower, grinning when it wobbles.",
                           "She's doodling on a napkin and hiding it whenever someone looks."]},
    "sardonic": {"weight": 2, "desc": "sardonic, sharp-tongued, secretly soft",
                 "hints": ["She watches a corpo hit on the waitress with open amusement.",
                           "She raises her glass to the holo-ad, deadpan."]},
    "intense":  {"weight": 2, "desc": "intense and direct, hates wasting time",
                 "neutral": -1,
                 "hints": ["She hasn't looked away from the news feed on the wall in minutes.",
                           "She's reading something on her wrist-screen like it owes her money."]},
    "dreamy":   {"weight": 2, "desc": "dreamy and distracted, full of odd questions",
                 "hints": ["She's watching the rain on the window like it's telling her something.",
                           "She's humming along to a song that isn't playing."]},
}

# Conversation topics. "lines" are hers; "good" replies fit her, "bad" ones sound reasonable
# but clash with who she is -- never rude, or the game would be too easy to read. The lists
# run in parallel: good[i] and bad[i] answer lines[i].
DATE_OCCUPATIONS = {
    "medtech": {"weight": 3, "desc": "a triage medic at a street clinic",
               "recall": "your shifts at the clinic on Ninth", "leans": {"chrome": "wary"},
                "lines": ["I patch people up at a clinic on Ninth. Mostly knife work, some chrome rejection.",
                          "Long shift. I stitched up three kids from the same gang tonight."],
                "good": ["Somebody has to put the city back together. Glad it's someone who cares.",
                         "Three in one night? Do you ever get to sit down?"],
                "bad": ["Clinics are a racket. Ripperdocs do the same job for half the fuss.",
                        "Sounds grim. Ever think about a desk job somewhere clean?"]},
    "netrunner": {"weight": 2, "desc": "a freelance netrunner",
                 "recall": "your runs in the Net", "leans": {"chrome": "loves"},
                  "lines": ["I run the Net for whoever pays. Tonight I'm just unplugged for once.",
                            "Spent six hours inside a Vexcorp subnet. Real air feels weird after."],
                  "good": ["Unplugged looks good on you. What does the Net feel like after that long?",
                           "Real air's overrated. What did you find in there?"],
                  "bad": ["Runners always burn out. I'd find something with a future.",
                          "Isn't that just typing in the dark for corpos?"]},
    "courier": {"weight": 3, "desc": "a motorbike courier who runs packages through the Sprawl",
               "recall": "your courier runs across the Sprawl", "leans": {"corps": "drifter"},
                "lines": ["I run packages across the Sprawl. Don't ask what's in them, I never do.",
                          "Got shot at on the Ninth Street overpass today. Delivered anyway."],
                "good": ["Nobody knows the city like a courier. Where's the best route nobody uses?",
                         "Delivered anyway. That's the whole job in two words, isn't it?"],
                "bad": ["You should get a bodyguard. Or a safer job.",
                        "Couriers are just drones with a pulse. Tech'll replace you soon."]},
    "mechanic": {"weight": 2, "desc": "a mechanic who rebuilds bikes and cheap drones",
                "recall": "the bikes you rebuild", "leans": {"chrome": "loves"},
                 "lines": ["I fix bikes. Drones too, if the owner doesn't mind a few extra parts.",
                           "Spent all day rebuilding a gearbox someone tried to fix with gum."],
                 "good": ["Gum? You should charge them extra for the insult.",
                          "I'd love to see your shop. I bet everything in it has a story."],
                 "bad": ["Why fix old junk? Everyone just prints new now.",
                         "I'd never let anyone else touch my ride."]},
    "musician": {"weight": 2, "desc": "a synth player in a band nobody's heard of yet",
                "recall": "your band", "leans": {"corps": "saboteur"},
                 "lines": ["I play synth in a band. We had a gig here last week. Four people came.",
                           "My band's between drummers. Again."],
                 "good": ["Four people who'll say they saw you first. When's the next one?",
                          "What do you sound like? And don't say 'hard to describe'."],
                 "bad": ["Music doesn't pay in this town. Got a backup plan?",
                         "I mostly listen to whatever the feed plays."]},
    "corpo": {"weight": 2, "desc": "a junior analyst at Tessier, a corporation",
             "recall": "your analyst job at the corp", "leans": {"corps": "saboteur"},
              "lines": ["I crunch numbers for Tessier. Don't hold it against me.",
                        "My manager's AI scheduled me a mandatory 'joy session' tomorrow."],
              "good": ["Everyone's got to eat. What would you do if you could walk out tomorrow?",
                       "Joy session? Please tell me you're going to sabotage it."],
              "bad": ["Tessier's solid. Stick it out and you'll make senior.",
                      "At least it's steady. Most people here would kill for that."]},
    "tattoo": {"weight": 2, "desc": "a tattoo artist who also inks glowing subdermal ink",
              "recall": "your tattoo work", "leans": {"chrome": "loves"},
               "lines": ["I do ink. The glowing kind, if you want the cops to see you in the dark.",
                         "Did a full back piece today. Nine hours. My hand's still shaking."],
               "good": ["What's the best one you've ever done?",
                        "Nine hours of steady hands. I'd trust you with my skin."],
               "bad": ["I never got the appeal. You'll just regret it at forty.",
                       "Couldn't a printer do that faster?"]},
    "noodles": {"weight": 2, "desc": "a cook at a noodle stall under the monorail",
               "recall": "your noodle stall under the monorail", "leans": {"corps": "drifter"},
                "lines": ["I cook noodles under the monorail. The trains shake the broth.",
                          "Every drunk in the Sprawl ends up at my stall eventually."],
                "good": ["Then I've probably eaten your cooking. Best thing I had that week.",
                         "Everyone ends up there because it's the best thing open. What's the secret?"],
                "bad": ["I mostly eat protein bars. Faster.",
                        "Must get old, cooking for drunks every night."]},
    "fixer": {"weight": 1, "desc": "a junior fixer building her own list of clients",
             "recall": "your list of clients", "leans": {"corps": "drifter"},
              "lines": ["I connect people who need things with people who have things. Small time, for now.",
                        "Half my job is knowing who's lying. The other half is pretending I don't."],
              "good": ["For now. I've got a feeling you'll have your own booth soon.",
                       "So which half am I getting tonight?"],
              "bad": ["Fixers are just middlemen. I'd rather go direct.",
                      "Sounds exhausting. Why not just take a steady job?"]},
    "dancer": {"weight": 2, "desc": "a dancer at a holo-club uptown",
              "recall": "dancing at the holo-club", "leans": {"chrome": "loves"},
               "lines": ["I dance at a holo-club uptown. They project dragons on me. It's a whole thing.",
                         "My feet are done. I came here to sit down and not be looked at."],
               "good": ["Dragons. Do you get to pick the dragon at least?",
                        "Then I'll look at the drinks list instead. Rough night?"],
               "bad": ["Must be nice, getting paid to have fun.",
                       "I've probably seen you. You're the one on the ads, right?"]},
}

DATE_INTERESTS = {
    "films": {"weight": 3, "label": "old flat films",
              "outing": "a reel screening under the old metro",
              "lines": ["There's a place under the old metro that still runs films off real reels.",
                        "I watched a black-and-white movie last night. Nobody even had chrome."],
              "good": ["Real reels? I'd sit in the dark with you for that.",
                       "No chrome and it still worked. What was it about?"],
              "bad": ["Why watch flat stuff when you can braindance it?",
                      "I can't sit still for anything longer than a feed clip."]},
    "synth": {"weight": 3, "label": "live synth music",
              "outing": "a synth set at a basement club",
              "lines": ["You hear that bassline? The trio's actually good tonight.",
                        "I'd kill to hear a real analog synth once. Not a sample. The real thing."],
              "good": ["They are. The one on the left plays like she's arguing with it.",
                       "My uncle had one. It hummed even when it was off."],
              "bad": ["Honestly I tune it out. It's just noise to drink to.",
                      "Real or sample, who can even tell anymore?"]},
    "racing": {"weight": 2, "label": "illegal street racing",
               "outing": "the ring road races, from the barrier",
               "lines": ["There's a race on the ring road Sunday. No rules, no cops, no brakes if you're brave.",
                         "Nothing beats the ring road at three in the morning with the throttle open."],
               "good": ["Save me a spot on the barrier. Or on the back of your bike.",
                        "Three a.m., empty road, nobody telling you to slow down. Yeah."],
               "bad": ["Those races kill somebody every week. Not my scene.",
                       "Sounds like a good way to end up in a clinic."]},
    "cooking": {"weight": 2, "label": "cooking real food",
                "outing": "cooking something real at her place",
                "lines": ["I found real garlic at the market. Actual garlic. I nearly cried.",
                          "Vat-meat's fine if you know what to do with it. Most people don't."],
                "good": ["Real garlic? What are you making with it?",
                         "So what do you do with it? Teach me something."],
                "bad": ["I just microwave whatever's in the machine.",
                        "Food's food. As long as it's cheap."]},
    "art": {"weight": 2, "label": "street art and murals",
            "outing": "a walk to find new murals",
            "lines": ["Someone painted a whale on the side of the Vexcorp stack. It's gone by morning, always.",
                      "I've been mapping every mural in the Sprawl before the corps paint over them."],
            "good": ["Gone by morning makes it better, somehow. Someone was brave for one night.",
                     "Show me your map sometime. I want to see the ones I've missed."],
            "bad": ["Vandalism, basically. The walls look cleaner blank.",
                    "Why bother? They'll just paint over it."]},
    "books": {"weight": 2, "label": "paper books",
              "outing": "the paper-book stalls in the Undercity",
              "lines": ["I collect paper books. They can't update them on you.",
                        "Found a paper book in a dumpster today. Poems, water-stained. Best thing all week."],
              "good": ["Can't hack paper. That's the whole appeal, isn't it?",
                       "Water-stained poems. Read me one?"],
              "bad": ["Paper? Everything's on the feed, and it's free.",
                      "I haven't read anything longer than a message in years."]},
    "animals": {"weight": 1, "label": "real animals",
                "outing": "feeding the pigeons at the old station",
                "lines": ["I feed a stray cat behind my building. A real one. No chrome, no subscription.",
                          "Did you know there are still real pigeons in the old station? I counted."],
                "good": ["A real cat. Does it have a name, or is it too proud for one?",
                         "Real pigeons. The city hasn't won everything yet."],
                "bad": ["Strays carry who knows what. I'd call pest control.",
                        "Robo-pets are cleaner. No mess."]},
    "stars": {"weight": 1, "label": "the stars above the smog",
              "outing": "her roof, looking for her three stars",
              "lines": ["On a clear night you can see three stars from my roof. I named them.",
                        "Sometimes I think about what the sky looked like before the smog."],
              "good": ["Show me which three sometime. I've never looked up long enough.",
                       "I bet it was loud with stars. We just forgot to listen."],
              "bad": ["Stars? You can see better ones on any holo-ad.",
                      "Nobody looks up here. There's nothing to see."]},
    "games": {"weight": 2, "label": "old arcade games",
              "outing": "the Undercity arcade, for a rematch",
              "lines": ["There's an arcade in the Undercity with cabinets older than my grandmother.",
                        "I hold the high score on a machine nobody else plays. Undefeated."],
              "good": ["Older than your grandmother and still running. Take me.",
                       "Undefeated? I want a rematch. Name the place."],
              "bad": ["Arcades? I thought those died with pay phones.",
                      "I don't really play games. Waste of time."]},
    "dance": {"weight": 2, "label": "dancing until sunrise",
              "outing": "a club with no name, until sunrise",
              "lines": ["The best clubs are the ones that don't have a name. You just follow the bass.",
                        "I haven't danced until sunrise in months. I miss it."],
              "good": ["Then let's find one with no name. I'll follow you.",
                       "The sun's still a few hours off, if you're asking."],
              "bad": ["I don't really dance. I hold up walls.",
                      "Clubs are too loud. I like somewhere I can hear myself think."]},
}

DATE_VALUES = {
    "freedom": {"weight": 3, "desc": "freedom -- nobody owns you",
               "likes_trouble": True,
                "lines": ["Sometimes I think about getting on a bike and riding out past the wall.",
                          "Everyone here's owned by something. A corp, a gang, a debt. Not me. Not yet."],
                "good": ["I'd ride out with you. Nobody out there owns anybody.",
                         "Not yet sounds like a promise. Keep it."],
                "bad": ["Out there? No clinics, no work. Crazy talk.",
                        "Everyone needs someone watching their back. Owned isn't always bad."]},
    "loyalty": {"weight": 3, "desc": "loyalty -- you stand by your people",
               "likes_trouble": False,
                "lines": ["My best friend sold me out for a promotion once. I'm still not over it.",
                          "I'd walk into fire for my crew. They'd do the same."],
                "good": ["That's the worst kind of cut. The people who stay are what count.",
                         "People like that are rarer than chrome. Hold on to them."],
                "bad": ["Can't blame her. Everyone looks out for number one in this city.",
                        "Crews come and go. I only really count on myself."]},
    "ambition": {"weight": 2, "desc": "ambition -- you're going to be somebody",
                "likes_trouble": False,
                 "lines": ["Five years from now I'm going to own a place like this. Watch me.",
                           "I didn't come this far to stay small."],
                 "good": ["I believe it. What's it going to be called?",
                          "Neither did I. What's your next move?"],
                 "bad": ["Why stress about it? Take it easy, enjoy the ride.",
                         "Big plans get people killed around here."]},
    "honesty": {"weight": 2, "desc": "honesty -- say what you mean",
               "likes_trouble": True,
                "lines": ["Everyone in this bar is lying about something. What's yours?",
                          "I'd rather hear something ugly and true than pretty and fake."],
                "good": ["Right now? That I'm not as calm as I look.",
                         "Then here's one: I sat here because of you, not the stool."],
                "bad": ["A little mystery never hurt anyone.",
                        "Everyone lies. The trick is doing it well."]},
    "thrill": {"weight": 2, "desc": "thrills -- you live for the rush",
              "likes_trouble": True,
               "lines": ["I jumped a gap between two stacks last month. Didn't look down once.",
                         "Safe is just another word for bored."],
               "good": ["Didn't look down? I'd have wanted to see your face on the landing.",
                        "Bored's worse than dead. What's next on your list?"],
               "bad": ["That's how people end up in the gutter. Be careful.",
                       "I'll take bored if it means I live to thirty."]},
}

DATE_CHROME = {
    "loves": {"weight": 2, "desc": "you love chrome -- it's who people choose to become",
             "likes_truth": True,
              "lines": ["My arm's the best thing I ever bought. Want to see what it can do?",
                        "People who fear chrome just don't know what they want to be yet."],
              "good": ["Show me. I want to see what you chose to become.",
                       "Chrome's just choosing yourself. I respect that."],
              "bad": ["I'd rather keep what I was born with, honestly.",
                      "Chrome freaks me out a little. No offence."]},
    "wary": {"weight": 2, "desc": "you're wary of chrome -- you've seen what it does to people",
            "likes_truth": False,
             "lines": ["A friend of mine went cyberpsycho. Too much chrome, too fast.",
                       "Every ripperdoc in this city is selling you a piece of yourself back."],
             "good": ["I'm sorry. The city sells you the chrome and never mentions the cost.",
                      "Somebody's got to stay human in this city. Might as well be us."],
             "bad": ["Chrome's just tools. It's the person who breaks.",
                     "I'd get more chrome in a heartbeat if I could afford it."]},
    "indifferent": {"weight": 2, "desc": "you don't care about chrome either way",
                    "likes_truth": True},
}

DATE_PEEVES = {
    "bragging": {"weight": 3, "desc": "bragging",
                "good_desc": "modest; turns the attention back to you",
                 "lines": ["So what's your story? Everyone in here has one.",
                           "You don't look like you're from around here. What do you do?"],
                 "good": ["Nothing worth bragging about. I'd rather hear yours.",
                          "Still figuring it out. Ask me again in a month."],
                 "bad": ["Let's just say half the fixers in this city know my name.",
                         "Stick around and you'll hear about me. Everyone does."]},
    "pushy": {"weight": 2, "desc": "pushiness",
                "good_desc": "easygoing; respects your time and your plans",
              "lines": ["I'm not staying long. Early shift.",
                        "I'm meeting a friend later. Maybe."],
              "good": ["Then I'm glad I caught you at all.",
                       "Then I'll take whatever's left of 'maybe'."],
              "bad": ["Skip it. Stay, have another -- I'm buying.",
                      "Cancel. Your friend won't mind."]},
    "corpo": {"weight": 2, "desc": "corpo talk and hustle-speak",
                "good_desc": "plain, heartfelt talk about what they actually want from life",
              "lines": ["What do you actually want out of this city?",
                        "If you could change one thing about your life, what would it be?"],
              "good": ["To live somewhere nobody owns me.",
                       "More nights like this. Fewer mornings like the last one."],
              "bad": ["Leverage. Build a network, climb, cash out.",
                      "Scale up. I'm working on a few verticals."]},
    "pity": {"weight": 2, "desc": "being pitied",
                "good_desc": "treats your hard past as strength, not as something to feel sorry about",
             "lines": ["I grew up in the Stacks. Worst block in the Sprawl.",
                       "I've been on my own since I was fourteen."],
             "good": ["So did half the people worth knowing.",
                      "Then you've been figuring the city out longer than most."],
             "bad": ["That must have been awful. You poor thing.",
                     "I'm so sorry. Nobody should have to go through that."]},
    "cynicism": {"weight": 2, "desc": "cynicism",
                "good_desc": "hopeful; notices the good things in the city",
                 "lines": ["Sometimes I think the city's getting better. Slowly.",
                           "I saw a kid give her umbrella to a stranger today. Made my week."],
                 "good": ["Yeah. You see it in small things, if you look.",
                          "That's the stuff that keeps this place running."],
                 "bad": ["Nothing changes here. Nothing ever will.",
                         "Give it a week. The city beats that out of everyone."]},
    "prying": {"weight": 2, "desc": "nosy questions",
                "good_desc": "gives you room; answers without digging into your private life",
               "lines": ["I don't usually talk to strangers.",
                         "You ask a lot of questions, don't you?"],
               "good": ["Then we'll keep it easy. No questions you don't want.",
                        "Only the ones you want to answer."],
               "bad": ["So what's your deal? Anyone waiting for you at home?",
                       "Where do you live, anyway? Near here?"]},
}

# -- Deeper traits ----------------------------------------------------
# Same shape as the topics above. Light ones (corps, vice, belief) can come up the first night;
# the rest wait until she knows you (DATE_TOPIC_DEPTH). "recall" is how you'd bring it up again
# on a later night, for her follow-up rounds.

# Corps and power. "likes_work" is which kinds of work she respects when she asks what you do
# (see DATE_QUESTIONS["work"]).
DATE_CORPS = {
    "saboteur": {"weight": 2, "desc": "the corps are the enemy, and you quietly work against them",
                 "likes_work": ["runner", "legit", "broke"],
                 "lines": ["Every Vexcorp logo in this district has a sticker over it. Guess whose.",
                           "The corps don't own the city. They just rent it from people too tired to fight."],
                 "good": ["Then I'll keep an eye out for your stickers. Want help with the next batch?",
                          "Too tired, sure. Not everyone, though."],
                 "bad": ["The corps keep the lights on. Somebody has to.",
                         "Stickers won't change anything. Might as well get paid by them."]},
    "drifter": {"weight": 3, "desc": "the corps are weather -- you keep your head down and get by",
                "likes_work": ["corpo", "legit", "runner", "broke"],
                "lines": ["Corps, gangs, landlords. They're all weather. You just carry an umbrella.",
                          "I don't pick fights with towers. I just try to eat twice a day."],
                "good": ["Good umbrella's worth more than a good speech.",
                         "Twice a day's a solid plan. Anything more is a bonus."],
                "bad": ["That's how they win, though. Everyone keeping their head down.",
                        "You should aim higher than getting by."]},
    "climber": {"weight": 2, "desc": "you want a tower job and you're not ashamed of it",
                "likes_work": ["corpo", "legit"],
                "lines": ["I've got an interview at Kiroshi next week. Third round.",
                          "One day I'll have a window on the ninetieth floor. Real glass."],
                "good": ["Third round means they want you. What's the role?",
                         "Real glass. I'll wave up at you from down here."],
                "bad": ["Kiroshi? They'll chew you up and bill you for it.",
                        "Tower people forget where they came from."]},
    "burned": {"weight": 2, "desc": "a corp chewed you up once and you're still bitter about it",
               "likes_work": ["runner", "legit", "broke"],
               "lines": ["I gave Vexcorp four years. They gave me a severance chip and a cough.",
                         "You know what a non-compete clause is? It's a leash with a signature on it."],
               "good": ["Four years for a cough. They owe you, and they know it.",
                        "Then I hope you chewed through it."],
               "bad": ["That's corporate life. You knew the deal going in.",
                       "Four years at a tower looks good on anyone's file, though."]},
}

# Guilty pleasures.
DATE_VICES = {
    "dramas": {"weight": 3, "desc": "trashy feed dramas you'd never admit to watching",
               "recall": "your feed dramas",
               "lines": ["Don't tell anyone, but I stay up for Tower of Hearts. The twins just swapped bodies.",
                         "I cried at a feed drama last night. The one with the clone and the lighthouse."],
               "good": ["Swapped bodies? Okay, I need to know how that happened.",
                        "The lighthouse one got me too. Nobody talks about that."],
               "bad": ["Those shows rot your brain, you know.",
                       "I don't watch the feeds. Too much noise."]},
    "gambling": {"weight": 2, "desc": "the pachinko dens -- just a little, just on payday",
                 "recall": "your pachinko nights",
                 "lines": ["I won eighty on the pachinko last night and lost it by ten past.",
                           "There's a machine on Sixth that pays out every full moon. I have a system."],
                 "good": ["Eighty for ten minutes of joy. Honestly not a bad rate.",
                          "A system. Show me. I'll bring the coins."],
                 "bad": ["The house always wins. You know that, right?",
                         "That's just a tax on people who can't do maths."]},
    "braindance": {"weight": 2, "desc": "braindance binges -- other people's lives, secondhand",
                   "recall": "your braindances",
                   "lines": ["I spent my whole day off in a braindance of someone climbing a mountain.",
                             "Best braindance I ever had was just a grandmother cooking. Forty minutes of it."],
                   "good": ["What did the top feel like? Secondhand still counts.",
                            "Forty minutes of someone's gran cooking. That sounds perfect."],
                   "bad": ["Why live someone else's life when you've got your own?",
                           "Braindances creep me out. Wearing a stranger's head."]},
    "synthcoffee": {"weight": 2, "desc": "sugar-bomb synth-coffee, four a day at least",
                    "recall": "your synth-coffee habit",
                    "lines": ["This is my fourth synth-coffee today. Triple caramel. Judge me.",
                              "I know the vending machine code for extra syrup. It's my one power."],
                    "good": ["Fourth? Amateur. Tell me the caramel one's good at least.",
                             "Extra syrup code. You're dangerous. Tell me it."],
                    "bad": ["That stuff'll kill you faster than a gang war.",
                            "I drink it black. Sugar just slows you down."]},
    "karaoke": {"weight": 2, "desc": "karaoke bars, the worse the better",
                "recall": "your karaoke nights",
                "lines": ["There's a karaoke box down the street with a mic that shocks you. I love it.",
                          "I know every word of every song from before the Collapse. Every one."],
                "good": ["A mic that bites back. Now I have to go.",
                         "Every one? Prove it. Pick a song."],
                "bad": ["Karaoke's just public embarrassment with a timer.",
                        "I can't sing. I don't see the point in trying."]},
}

# What she believes in.
DATE_BELIEFS = {
    "netghosts": {"weight": 2, "desc": "ghosts in the Net -- the dead still talk, if you listen",
                  "recall": "the ghosts in the Net",
                  "lines": ["My grandmother's still in the Net. She messages me on her birthday.",
                            "There are voices behind the old firewalls. Runners don't talk about it."],
                  "good": ["What does she say? Does she sound like herself?",
                           "Runners don't talk about it. So you've heard them too."],
                  "bad": ["That's probably just an old bot someone forgot to switch off.",
                          "Ghosts are for people who can't let go."]},
    "tarot": {"weight": 2, "desc": "tarot readings from a vending machine on Fourth",
              "recall": "your tarot machine",
              "lines": ["The tarot machine on Fourth gave me the Tower card this morning. So. Careful tonight.",
                        "I get a reading every Monday. The machine's never been wrong. Mostly."],
              "good": ["The Tower. Should I be worried or flattered I'm sitting next to you?",
                       "Mostly never wrong is better than most people I know."],
              "bad": ["It's a vending machine. It's got about six cards in it.",
                      "You don't strike me as someone who'd fall for that."]},
    "saints": {"weight": 2, "desc": "the old saints -- you light a candle every week, quietly",
               "recall": "your candles for the saints",
               "lines": ["I light a candle every Sunday at the old chapel under the flyover. Old habit.",
                         "My mother said a saint watches every street. I've never figured out who watches this one."],
               "good": ["Light one for me next time? I could use the help.",
                        "Someone patient, I'd guess. Whoever it is."],
               "bad": ["Nobody up there's watching this city. Look around.",
                       "Religion's just another corp with better branding."]},
    "nothing": {"weight": 3, "desc": "nothing -- no gods, no fate, no signs",
                "recall": "your nothing-at-all",
                "lines": ["No gods, no fate, no lucky numbers. Just us and the rain.",
                          "People ask what I believe in. I say rent."],
                "good": ["Just us and the rain. Honestly that's enough tonight.",
                         "Rent's real. Can't argue with rent."],
                "bad": ["Everyone believes in something. You just haven't found it.",
                        "Sounds lonely. There's got to be more than that."]},
    "luck": {"weight": 2, "desc": "luck -- lucky charms, lucky numbers, lucky stools",
             "recall": "your lucky charm",
             "lines": ["This is my lucky stool. You're sitting next to the luckiest seat in the Lotus.",
                       "I've carried the same bottle cap for six years. Never been shot. Coincidence?"],
             "good": ["Then some of it's rubbing off on me. Good.",
                      "Six years unshot. I'd keep carrying it."],
             "bad": ["Luck's just statistics people don't understand.",
                     "Pretty sure it's a coincidence."]},
}

# Where she's from (second meeting on).
DATE_ORIGINS = {
    "sprawl": {"weight": 3, "desc": "born and raised in the Sprawl",
               "recall": "growing up in the Sprawl",
               "lines": ["I grew up four blocks from here. Same pollution, same noodle stall.",
                         "Sprawl kid. I learned to read from gang tags."],
               "good": ["Four blocks. We probably fought over the same stall.",
                        "Gang tags are a real alphabet. Harder than the school one."],
               "bad": ["Must've been rough. You got out of the worst of it, at least.",
                       "Sprawl kids always have that edge. Hard to shake, I bet."]},
    "tower": {"weight": 2, "desc": "raised in a corp tower before your family fell out of it",
              "recall": "the tower you grew up in",
              "lines": ["I grew up on the sixtieth floor. Then my father lost his job and we lost the floor.",
                        "I had a real bedroom once. Windows and everything."],
              "good": ["That's a long way down. You landed on your feet, though.",
                       "Windows and everything. What did you see out of them?"],
              "bad": ["So you had money, then. Must've been nice while it lasted.",
                      "Tower kid. I should've guessed from the posture."]},
    "orbital": {"weight": 1, "desc": "born on an orbital and deported to the city",
                "recall": "the station you were born on",
                "lines": ["I was born up there. On the station. They sent me down when my visa lapsed.",
                          "Gravity still feels wrong some mornings. Too heavy."],
                "good": ["Down here with the rest of us. What do you miss about up there?",
                         "Too heavy. Yeah. I think I get that, in a different way."],
                "bad": ["Up there? Everyone wants to get up there. You must be dying to go back.",
                        "Orbital people always think they're better than us."]},
    "nomad": {"weight": 2, "desc": "from a nomad clan out in the badlands",
              "recall": "your clan in the badlands",
              "lines": ["My clan's out past the wall. Forty trucks and a lot of opinions.",
                        "I left the badlands for the city. Some nights I can't remember why."],
              "good": ["Forty trucks. What made you leave, and do you miss it?",
                       "Maybe for nights like this one. Maybe that's why."],
              "bad": ["Nomads, huh? Always wondered how they live out there with no clinics.",
                      "The city must be a big step up from sand."]},
    "coast": {"weight": 2, "desc": "a refugee from the drowned coast towns",
              "recall": "your town on the drowned coast",
              "lines": ["My hometown's underwater now. You can still see the church steeple at low tide.",
                        "I came up from the coast when the sea wall went. I was nine."],
              "good": ["Is there anything you still have from there?",
                       "Nine. That's young to start over. You did."],
              "bad": ["The whole coast was a lost cause. Better off here, right?",
                      "Lots of coast people came up then. The city took a lot of you in."]},
}

# What she wants from life (second meeting on).
DATE_DREAMS = {
    "orbit": {"weight": 2, "desc": "getting a visa and leaving for the orbital stations",
              "recall": "your plan to get up to the stations",
              "lines": ["Two more years of savings and I'm buying a visa. Orbital. Clean air.",
                        "I have a picture of the station on my wall. I look at it every morning."],
              "good": ["Two years. I'll help you count. What's the first thing you'll do up there?",
                       "Keep looking. You'll see it for real one day."],
              "bad": ["Visas are a scam. Half of them are forged anyway.",
                      "Up there you'd be nobody. Down here, people know you."]},
    "noodlebar": {"weight": 2, "desc": "opening a noodle bar of your own",
                  "recall": "the noodle bar you want to open",
                  "lines": ["One day I'm opening my own noodle bar. Six stools, one recipe, no menu.",
                            "I've already got a name for my place. I'm not telling you it yet."],
                  "good": ["Six stools and no menu. Save me one.",
                           "Not yet. Fine. I'll earn it."],
                  "bad": ["Restaurants fail all the time. It's a brutal business.",
                          "Six stools won't pay rent round here."]},
    "fame": {"weight": 2, "desc": "being famous on the feeds, just once",
             "recall": "your plan to get famous on the feeds",
             "lines": ["I want one clip. Just one. A million views and my name in the corner.",
                       "Someday someone in a bar like this will say 'I knew her before.'"],
             "good": ["What's the clip? Tell me and I'll be view number one.",
                      "I'll be the one saying it. Loudly."],
             "bad": ["Fame's poison. Look what it does to the feed stars.",
                     "A million views and a week later nobody remembers."]},
    "flat": {"weight": 2, "desc": "buying back your mother's old flat",
             "recall": "your mother's flat",
             "lines": ["There's a flat in the Stacks that used to be my mother's. I'm going to buy it back.",
                       "The landlord who took my mother's flat is getting old. I can wait."],
             "good": ["Buy it back and hang her picture where it used to be.",
                      "You can wait. I believe that."],
             "bad": ["It's just rooms. Why not start fresh somewhere better?",
                     "Holding onto the past like that must be heavy."]},
    "clinic": {"weight": 1, "desc": "running a free clinic in the Sprawl",
               "recall": "your free clinic",
               "lines": ["I want to run a clinic that doesn't take money. Just walk in and get fixed.",
                         "Free patching. Everyone laughs when I say it. You can laugh."],
               "good": ["I'm not laughing. Where would you put it?",
                        "Somebody has to be the one who doesn't charge. Why not you?"],
               "bad": ["Free? It'd be bankrupt in a month.",
                       "Nobody does anything for free here. They'd rob you blind."]},
}

# Her people (second meeting on).
DATE_FAMILIES = {
    "brother": {"weight": 2, "desc": "raising your little brother on your own",
                "recall": "your little brother",
                "lines": ["My little brother's fourteen. I'm his whole family. He thinks I'm strict.",
                          "I have to be home by two. My brother doesn't sleep until I'm back."],
                "good": ["Fourteen and he's got you. He's luckier than he knows.",
                         "Then I'll walk you to the train by one-thirty."],
                "bad": ["Fourteen's old enough to look after himself around here.",
                        "That's a lot to carry. Isn't there anyone else?"]},
    "estranged": {"weight": 2, "desc": "cut off from corpo parents who never forgave you for leaving",
                  "recall": "your parents in the tower",
                  "lines": ["My parents stopped calling when I quit their company. Their company. Literally.",
                            "My mother sent me a birthday message. It was a form letter."],
                  "good": ["Their loss. You chose yourself. That takes more than they'd understand.",
                           "A form letter. That's cold. I'm sorry."],
                  "bad": ["Maybe call them first? Parents are only around once.",
                          "They probably just want what's best for you."]},
    "clan": {"weight": 2, "desc": "a huge loud family -- forty cousins, all in your business",
             "recall": "your forty cousins",
             "lines": ["I have forty cousins. Forty. They all know I'm here right now, somehow.",
                       "Family dinner is sixty people and three fights. Every week."],
             "good": ["Forty. Tell me they're not all going to find out about me.",
                      "Three fights a week sounds like love, honestly."],
             "bad": ["Sounds exhausting. I'd move across the city.",
                     "I don't get big families. Too much noise."]},
    "alone": {"weight": 2, "desc": "nobody left -- it's been just you for years",
              "recall": "being on your own",
              "lines": ["No family. It's been just me since I was sixteen.",
                        "Holidays are easy when there's nobody to visit."],
              "good": ["Sixteen's young. You built all of this yourself.",
                       "Then maybe one holiday we're nobody together."],
              "bad": ["That must be lonely. I don't know how you do it.",
                      "Everyone has somebody somewhere. You should look."]},
    "gran": {"weight": 2, "desc": "living with your grandmother, who runs your life",
             "recall": "your gran",
             "lines": ["I live with my gran. She's ninety and she still rates every guy I mention.",
                       "My gran makes dumplings every Sunday and makes me swear I'll bring someone."],
             "good": ["Ninety and rating. How am I doing so far?",
                      "What do I have to do to get invited?"],
             "bad": ["You still live with your gran? You should get your own place.",
                     "Grans always want something. Careful."]},
}

# What she's carrying (third meeting on). Good replies listen; bad ones fix or joke.
DATE_WOUNDS = {
    "psycho": {"weight": 2, "desc": "the old crew's netrunner went cyberpsycho, and you were there",
               "lines": ["I was there the night our runner went cyberpsycho. I still hear it sometimes.",
                         "Someone I loved turned into something else. Chrome did it. I watched."],
               "good": ["You don't have to tell me more. I'm here if you want to.",
                        "That's a lot to still be carrying. Thank you for telling me."],
               "bad": ["You should see someone about that. There are chips for trauma now.",
                       "At least you got out okay. That's what matters."]},
    "debt": {"weight": 2, "desc": "you owe the Kestrels money and they don't forget",
             "lines": ["I owe some people. The kind with tattoos on their knuckles. It's handled. Mostly.",
                       "Some weeks every credit I make goes to someone I'm scared of."],
             "good": ["Mostly is still a lot. You don't have to handle it alone.",
                      "That's heavy. I'm glad you still come out some nights."],
             "bad": ["You should just pay them off and be done. How much is it?",
                     "Everyone owes somebody. Don't let it get to you."]},
    "erased": {"weight": 1, "desc": "a corp wiped your records -- officially, you don't exist",
               "lines": ["Officially I don't exist. A corp scrubbed my records after I saw something.",
                         "No ID, no bank, no history. Sometimes I wonder if I'm still here."],
               "good": ["You're here. I can see you. That counts for something.",
                        "Whatever you saw, I'm glad you're still around to not talk about it."],
               "bad": ["Wait, what did you see? You can't stop there.",
                       "Honestly sounds kind of freeing. No history, no debts."]},
    "tank": {"weight": 2, "desc": "your sister's been in a coma tank for two years",
             "lines": ["My sister's in a tank at the clinic. Two years. I visit Thursdays.",
                       "They say she can hear me. I talk to her about stupid things. The weather."],
             "good": ["Thursdays. I bet she knows it's you every time.",
                      "Stupid things are the best things to hear. She's lucky to have you."],
             "bad": ["Two years? Have they said anything about turning it off?",
                     "You should try to live your own life too, you know."]},
    "fire": {"weight": 2, "desc": "your building burned down in the Block Nine fire",
             "lines": ["I lived in Block Nine. The fire took everything but my jacket.",
                       "I can't sleep if I smell smoke. Even cigarettes."],
             "good": ["Everything but the jacket. I'm glad it's still with you. You too.",
                      "I'll keep the smokers away. Promise."],
             "bad": ["Didn't the insurance cover it? They're supposed to.",
                     "At least it was just stuff. Stuff can be replaced."]},
}

# Which kinds wait until you've met her a few times, as {kind: meetings before}.
DATE_TOPIC_DEPTH = {"origin": 1, "dream": 1, "family": 1, "wound": 2}

# From the second meeting, she may check whether you listened: one round each night with this
# chance recalls something she told you on an earlier night. Both replies use the same
# sentence; the good one fills {thing} with what she said (her trait's "recall", or an
# interest's label), the bad one confidently with something she didn't.
DATE_CALLBACK_CHANCE = 0.5
DATE_CALLBACK = {
    "lines": ["Okay, test. What do you actually remember about me?",
              "Last time I talked your ear off. Did any of it stick?",
              "Go on then. Tell me one thing I told you."],
    "replies": ["You told me about {thing}. I've been thinking about it.",
                "Of course. We talked about {thing}. I wanted to hear more.",
                "I remember you going on about {thing}. It stuck with me."],
}

# She asks about you, with this chance once a night if any question applies. Replies are the
# truth (which lands or doesn't, depending on her), a flattering lie (which always lands -- for
# now), or a dodge (small talk, see temperaments). Each lie she hasn't caught has
# DATE_LIE_CAUGHT chance to surface every time you meet again, and every night once you're
# together; it costs DATE_LIE_COST affection, double if she values honesty.
DATE_QUESTION_CHANCE = 0.5
DATE_LIE_CAUGHT = 0.3
DATE_LIE_COST = 3
DATE_QUESTIONS = {
    "work": {  # the truth depends on your work: see romance.your_work(); judged by her DATE_CORPS
        "about": "what the stranger does for a living",
        "lines": ["So what do you actually do? Don't say 'this and that'.",
                  "What pays your rent? Honestly."],
        "truth": {"corpo": ["I'm {job}. It's steady. I don't love it."],
                  "legit": ["I'm {job}. Nothing glamorous, but it's honest."],
                  "runner": ["I run jobs for a fixer. The kind you don't put on a résumé."],
                  "broke": ["Honestly? Nothing right now. I'm looking."]},
        "truth_brief": {"corpo": "they work for a corporation, as {job}",
                        "legit": "they work as {job}",
                        "runner": "they run illegal jobs for a fixer",
                        "broke": "they're out of work right now"},
        "lie": ["I'm in logistics. Very boring, very legal, very well paid.",
                "Consulting. For a tower. I can't really say which."],
        "lie_brief": "a respectable, well-paid, perfectly legal job",
        "caught": "{name} heard what you really do for a living. Not from you.",
    },
    "chrome": {  # only if you have cyberware; judged by her DATE_CHROME "likes_truth"
        "about": "the stranger's cyberware",
        "lines": ["Is that chrome? It's new, isn't it?",
                  "How much of you is still factory original?"],
        "truth": ["Yeah, I had some work done. {chrome}. Changes how the world feels."],
        "truth_brief": "yes, they have chrome: {chrome}",
        "lie_brief": "their chrome is just cosmetic, nothing real",
        "lie": ["That? Cosmetic. Nothing under the skin, I swear.",
                "All original. What you see is what you get."],
        "caught": "{name} saw the ripperdoc's name on your med-scan. She knows it wasn't cosmetic.",
    },
    "trouble": {  # only if you're hot or known; judged by her DATE_VALUES "likes_trouble"
        "about": "whether the stranger is trouble",
        "lines": ["You've got a look. Are you trouble?",
                  "People in here keep glancing at you. Should I be worried?"],
        "truth": ["Some days. I try to keep it outside."],
        "truth_brief": "yes, they get into trouble sometimes",
        "lie_brief": "they're harmless and quiet, nothing to worry about",
        "lie": ["Me? I'm the quietest person in this bar.",
                "They must be thinking of somebody else."],
        "caught": "{name} heard your name from someone who was scared of it.",
    },
}
DATE_TROUBLE_HEAT = 2      # "trouble" comes up at this much heat...
DATE_TROUBLE_CRED = 15     # ...or this much street cred
DATE_RUNNER_CRED = 10      # jobless with this much cred and you're a runner, not broke
DATE_DODGE = [
    "Long story. Better with another drink.",
    "Ask me again when I know you better.",
    "Let's talk about you instead. You're more interesting.",
]

# A job suggests things about her; with DATE_LEAN_CHANCE she's what you'd expect, otherwise
# she's anything but (see DATE_OCCUPATIONS "leans").
DATE_LEAN_CHANCE = 0.5

# Noncommittal replies: neither pleases nor bothers anyone.
DATE_NEUTRAL = [
    "Huh. Never really thought about it.",
    "Yeah? Fair enough.",
    "The drinks here are better than they look, at least.",
    "Could be. Hard to say.",
    "Funny, I was just thinking about the rain.",
    "I guess everybody's got something.",
    "Mm. It's been a long week.",
    "That's one way to look at it.",
    "Sounds about right for this town.",
    "I'll drink to that, I suppose.",
    "Hm. Want another round?",
    "Is it always this loud in here?",
]

# How she takes what you said. Shown after each reply.
DATE_REACTIONS = {
    "good": ["She laughs, surprised.", "Her eyes stay on you a moment longer.",
             "She leans in a little.", "Something in her shoulders relaxes."],
    "bad": ["Her smile cools a degree.", "She glances at the door.",
            "She stirs her drink and says nothing for a beat.", "She sits back."],
    "neutral": ["She shrugs.", "She nods, half listening.",
                "She sips her drink.", "The music fills the pause."],
}

# How the night ends, worst to best. The net score (+1 per good reply, -1 per bad, so
# -DATE_ROUNDS..DATE_ROUNDS) picks the best tier whose "min_net" it reaches; walking out always
# lands in the first. The last tier ("partner") is only open once she's ready (see
# DATE_MIN_MEETINGS), so a single perfect night tops out at the kiss. "prompt" tells a dialog
# model how she says goodbye; "canned" is her line without one. "memory" is how she remembers
# the night next time, "again" how she greets you. Stress relief is the only payoff (see the
# CLAUDE.md balance notes); the last tier also makes her your partner.
DATE_OUTCOMES = [
    {"prompt": "You've had enough of this person. End it coldly and leave.",
     "canned": ["I'm going to go. Don't follow me.", "Wow. Okay. Goodnight."],
     "min_net": -DATE_ROUNDS,
     "narration": "She slides off the stool and leaves her drink unfinished.", "stress": 5,
     "memory": "it went badly and you walked out on them",
     "again": "She sees you, and her face closes like a door."},
    {"prompt": "Make a polite excuse and leave. You're not interested.",
     "canned": ["Well. Nice meeting you. I should go.", "Early shift. Take care."],
     "min_net": -1,
     "narration": "She finishes her drink a little too quickly.", "stress": 0,
     "memory": "it was awkward and you made an excuse to leave",
     "again": "She notices you and gives a small, careful nod."},
    {"prompt": "Say a friendly goodbye. It was nice, but nothing more.",
     "canned": ["This was nice. Take care of yourself out there.", "Thanks for the company."],
     "min_net": 1,
     "narration": "You talk until the ice melts. Pleasant, but nothing sparks.", "stress": -3,
     "memory": "it was pleasant, but nothing sparked",
     "again": "She recognises you and lifts her glass an inch."},
    {"prompt": "You enjoyed this. Hint you might like to run into them here again.",
     "canned": ["If I'm here again, you can buy the next one.", "You're not the worst company in here."],
     "min_net": 2,
     "narration": "She laughs at your jokes and touches your arm once on the way out.", "stress": -5,
     "memory": "you enjoyed it and hoped to run into them again",
     "again": "She catches your eye and pats the empty stool beside her."},
    {"prompt": "You really like them, but you're not ready for more yet. Say goodnight warmly.",
     "canned": ["I like you. That's what worries me. Goodnight.", "Ask me again some other night."],
     "min_net": 4,
     "narration": "Outside, under the dripping neon, she kisses you. Then she's gone into the rain.",
     "stress": -8,
     "memory": "you kissed them goodnight in the rain",
     "again": "She sees you and smiles before she can stop herself."},
    {"prompt": "You want to keep seeing them, starting tonight. Ask them to walk you home.",
     "canned": ["Walk me home? And then tomorrow, too.", "I'm not letting you disappear. Walk with me."],
     "min_net": DATE_PARTNER_NET, "partner": True,
     "narration": "She walks out with you, and doesn't let go of your hand.", "stress": -10,
     "memory": "you asked them to walk you home",
     "again": "She's already waving you over."},
]

# -- Relationships ----------------------------------------------------
# Once she's your partner. Seeing her is the one reliable humanity source in the game, and it
# costs a whole action point you could have spent on rent. Neglect her, run too hot, or lose
# too much of yourself to chrome and she'll leave.

REL_NEGLECT_DAYS = 4          # nights apart before affection starts slipping, one a night
REL_WORRY_HEAT = 8            # heat at which she starts worrying about you...
REL_WORRY_HUMANITY = 35       # ...or humanity below which she does
REL_WORRY_COST = 2            # affection lost per worried night
REL_LEAVE_AFFECTION = 5       # below this she's gone
REL_LEAVE_STRESS = 20
REL_SERIOUS_AFFECTION = 25    # she moves in once affection reaches this...
REL_SERIOUS_DAYS = 14         # ...after this many days together
REL_ASK_COST = 200            # what she asks for when she's in trouble
REL_ASK_AFFECTION = 3         # won by helping, lost by refusing

# Time together. Her two interests each suggest an outing (DATE_INTERESTS "outing"); staying
# in is free and calmer but does less for her.
REL_OUTING = {"cost": 40, "stress": -10, "humanity": 3, "affection": 2}
REL_STAY_IN = {"label": "Stay in at your place", "cost": 0, "stress": -14, "humanity": 2,
               "affection": 1}
REL_TOGETHER = [
    "I needed this. I needed you, I think.",
    "Same time tomorrow? I'm only half joking.",
    "You're the only quiet thing in this whole city.",
    "Don't go getting yourself killed. I'm getting used to you.",
]

REL_NEGLECTED = [
    "{name} messages: \"Still alive?\" You don't answer in time.",
    "You haven't seen {name} in days. Her last message sits unread.",
]
REL_WORRIED = [
    "{name} traces the new scar on your hand and doesn't say anything. That's worse.",
    "{name} asks who you're turning into. You don't have a good answer.",
]
REL_LEAVES = "{name} leaves her key on the table. She doesn't leave a note."
REL_MOVES_IN = "{name} turns up with two bags and a plant. She's moving in. Rent's split now."
REL_ASKS = [
    "Her clinic bill came in and it's more than she has.",
    "Her landlord wants a deposit back by morning, or she's out.",
    "Her bike got impounded. She needs it for work tomorrow.",
]

# What happens to her in each ending. "visa" is for leaving without her; "visa_together" when
# you bought two.
REL_ENDINGS = {
    "flatlined": "{name} is the one who reports you missing. Nobody listens.",
    "cyberpsychosis": "{name} still keeps a light on for you. You don't remember her name.",
    "burnout": "{name} sits by the bed for a week, then has to go back to work.",
    "evicted": "{name} helps you carry the bag. Then she's gone too.",
    "visa": "{name} is still asleep when you leave. You meant to tell her.",
    "visa_together": "{name} falls asleep on your shoulder before the shuttle clears the smog.",
    "legend": "{name} stays. Somebody has to remember who you were before.",
}
VISA_FOR_TWO = 25_000
