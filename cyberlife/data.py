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
    {"id": "dataentry", "name": "Data-entry drone, Kiroshi",    "pay": 140, "stress": 12, "req": ("hacking", 3),
     "desc": "a data-entry clerk at Kiroshi, a corporation"},
    {"id": "promoter",  "name": "Club promoter, Neon Lotus",    "pay": 160, "stress": 11, "req": ("charm", 4),
     "desc": "a promoter for the Neon Lotus, a club and bar"},
    {"id": "security",  "name": "Security contractor, Vexcorp", "pay": 240, "stress": 14, "req": ("muscle", 5),
     "desc": "a security contractor for Vexcorp, a corporation"},
    {"id": "netrunner", "name": "Junior netrunner, Tessier",    "pay": 320, "stress": 16, "req": ("hacking", 6),
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

# Canned opening scene. Slots come from DATE_LOOKS, plus {hint} from her temperament.
DATE_SCENES = [
    "Two stools down sits a {build} woman with {hair} and {eyes}, wearing {style}. "
    "You notice {feature}. {hint}",
    "A {build} woman at the end of the bar is nursing a drink alone: {hair}, {eyes}, {style}. "
    "Hard to miss {feature}. {hint}",
    "The seat next to yours is taken by a {build} woman in {style}. She has {hair}, {eyes} "
    "and {feature}. {hint}",
    "Through the smoke you catch a {build} woman with {hair}, {eyes} and {feature}, "
    "in {style}. {hint}",
]

# Personality. Each id maps to a weight and a description a dialog model sees; the player
# only ever gets a temperament's vague "hint" in the opening scene.
DATE_TEMPERAMENTS = {
    "warm":     {"weight": 3, "desc": "warm and open, quick to laugh",
                 "hints": ["She's the only one in here smiling at the bartender.",
                           "She thanks the service drone like it's a person."]},
    "guarded":  {"weight": 3, "desc": "guarded, slow to trust, dry once she does",
                 "hints": ["She keeps one eye on the door.",
                           "She's chosen the seat with her back to the wall."]},
    "playful":  {"weight": 2, "desc": "playful and teasing, bored by earnestness",
                 "hints": ["She's stacking bottle caps into a tower, grinning when it wobbles.",
                           "She's doodling on a napkin and hiding it whenever someone looks."]},
    "sardonic": {"weight": 2, "desc": "sardonic, sharp-tongued, secretly soft",
                 "hints": ["She watches a corpo hit on the waitress with open amusement.",
                           "She raises her glass to the holo-ad, deadpan."]},
    "intense":  {"weight": 2, "desc": "intense and direct, hates wasting time",
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
                "lines": ["I patch people up at a clinic on Ninth. Mostly knife work, some chrome rejection.",
                          "Long shift. I stitched up three kids from the same gang tonight."],
                "good": ["Somebody has to put the city back together. Glad it's someone who cares.",
                         "Three in one night? Do you ever get to sit down?"],
                "bad": ["Clinics are a racket. Ripperdocs do the same job for half the fuss.",
                        "Sounds grim. Ever think about a desk job somewhere clean?"]},
    "netrunner": {"weight": 2, "desc": "a freelance netrunner",
                  "lines": ["I run the Net for whoever pays. Tonight I'm just unplugged for once.",
                            "Spent six hours inside a Vexcorp subnet. Real air feels weird after."],
                  "good": ["Unplugged looks good on you. What does the Net feel like after that long?",
                           "Real air's overrated. What did you find in there?"],
                  "bad": ["Runners always burn out. I'd find something with a future.",
                          "Isn't that just typing in the dark for corpos?"]},
    "courier": {"weight": 3, "desc": "a motorbike courier who runs packages through the Sprawl",
                "lines": ["I run packages across the Sprawl. Don't ask what's in them, I never do.",
                          "Got shot at on the Ninth Street overpass today. Delivered anyway."],
                "good": ["Nobody knows the city like a courier. Where's the best route nobody uses?",
                         "Delivered anyway. That's the whole job in two words, isn't it?"],
                "bad": ["You should get a bodyguard. Or a safer job.",
                        "Couriers are just drones with a pulse. Tech'll replace you soon."]},
    "mechanic": {"weight": 2, "desc": "a mechanic who rebuilds bikes and cheap drones",
                 "lines": ["I fix bikes. Drones too, if the owner doesn't mind a few extra parts.",
                           "Spent all day rebuilding a gearbox someone tried to fix with gum."],
                 "good": ["Gum? You should charge them extra for the insult.",
                          "I'd love to see your shop. I bet everything in it has a story."],
                 "bad": ["Why fix old junk? Everyone just prints new now.",
                         "I'd never let anyone else touch my ride."]},
    "musician": {"weight": 2, "desc": "a synth player in a band nobody's heard of yet",
                 "lines": ["I play synth in a band. We had a gig here last week. Four people came.",
                           "My band's between drummers. Again."],
                 "good": ["Four people who'll say they saw you first. When's the next one?",
                          "What do you sound like? And don't say 'hard to describe'."],
                 "bad": ["Music doesn't pay in this town. Got a backup plan?",
                         "I mostly listen to whatever the feed plays."]},
    "corpo": {"weight": 2, "desc": "a junior analyst at a corp she quietly hates",
              "lines": ["I crunch numbers for Tessier. Don't hold it against me.",
                        "My manager's AI scheduled me a mandatory 'joy session' tomorrow."],
              "good": ["Everyone's got to eat. What would you do if you could walk out tomorrow?",
                       "Joy session? Please tell me you're going to sabotage it."],
              "bad": ["Tessier's solid. Stick it out and you'll make senior.",
                      "At least it's steady. Most people here would kill for that."]},
    "tattoo": {"weight": 2, "desc": "a tattoo artist who also inks glowing subdermal ink",
               "lines": ["I do ink. The glowing kind, if you want the cops to see you in the dark.",
                         "Did a full back piece today. Nine hours. My hand's still shaking."],
               "good": ["What's the best one you've ever done?",
                        "Nine hours of steady hands. I'd trust you with my skin."],
               "bad": ["I never got the appeal. You'll just regret it at forty.",
                       "Couldn't a printer do that faster?"]},
    "noodles": {"weight": 2, "desc": "a cook at a noodle stall under the monorail",
                "lines": ["I cook noodles under the monorail. The trains shake the broth.",
                          "Every drunk in the Sprawl ends up at my stall eventually."],
                "good": ["Then I've probably eaten your cooking. Best thing I had that week.",
                         "Everyone ends up there because it's the best thing open. What's the secret?"],
                "bad": ["I mostly eat protein bars. Faster.",
                        "Must get old, cooking for drunks every night."]},
    "fixer": {"weight": 1, "desc": "a junior fixer building her own list of clients",
              "lines": ["I connect people who need things with people who have things. Small time, for now.",
                        "Half my job is knowing who's lying. The other half is pretending I don't."],
              "good": ["For now. I've got a feeling you'll have your own booth soon.",
                       "So which half am I getting tonight?"],
              "bad": ["Fixers are just middlemen. I'd rather go direct.",
                      "Sounds exhausting. Why not just take a steady job?"]},
    "dancer": {"weight": 2, "desc": "a dancer at a holo-club uptown",
               "lines": ["I dance at a holo-club uptown. They project dragons on me. It's a whole thing.",
                         "My feet are done. I came here to sit down and not be looked at."],
               "good": ["Dragons. Do you get to pick the dragon at least?",
                        "Then I'll look at the drinks list instead. Rough night?"],
               "bad": ["Must be nice, getting paid to have fun.",
                       "I've probably seen you. You're the one on the ads, right?"]},
}

DATE_INTERESTS = {
    "films": {"weight": 3, "label": "old flat films",
              "lines": ["There's a place under the old metro that still runs films off real reels.",
                        "I watched a black-and-white movie last night. Nobody even had chrome."],
              "good": ["Real reels? I'd sit in the dark with you for that.",
                       "No chrome and it still worked. What was it about?"],
              "bad": ["Why watch flat stuff when you can braindance it?",
                      "I can't sit still for anything longer than a feed clip."]},
    "synth": {"weight": 3, "label": "live synth music",
              "lines": ["You hear that bassline? The trio's actually good tonight.",
                        "I'd kill to hear a real analog synth once. Not a sample. The real thing."],
              "good": ["They are. The one on the left plays like she's arguing with it.",
                       "My uncle had one. It hummed even when it was off."],
              "bad": ["Honestly I tune it out. It's just noise to drink to.",
                      "Real or sample, who can even tell anymore?"]},
    "racing": {"weight": 2, "label": "illegal street racing",
               "lines": ["There's a race on the ring road Sunday. No rules, no cops, no brakes if you're brave.",
                         "Nothing beats the ring road at three in the morning with the throttle open."],
               "good": ["Save me a spot on the barrier. Or on the back of your bike.",
                        "Three a.m., empty road, nobody telling you to slow down. Yeah."],
               "bad": ["Those races kill somebody every week. Not my scene.",
                       "Sounds like a good way to end up in a clinic."]},
    "cooking": {"weight": 2, "label": "cooking real food",
                "lines": ["I found real garlic at the market. Actual garlic. I nearly cried.",
                          "Vat-meat's fine if you know what to do with it. Most people don't."],
                "good": ["Real garlic? What are you making with it?",
                         "So what do you do with it? Teach me something."],
                "bad": ["I just microwave whatever's in the machine.",
                        "Food's food. As long as it's cheap."]},
    "art": {"weight": 2, "label": "street art and murals",
            "lines": ["Someone painted a whale on the side of the Vexcorp stack. It's gone by morning, always.",
                      "I've been mapping every mural in the Sprawl before the corps paint over them."],
            "good": ["Gone by morning makes it better, somehow. Someone was brave for one night.",
                     "Show me your map sometime. I want to see the ones I've missed."],
            "bad": ["Vandalism, basically. The walls look cleaner blank.",
                    "Why bother? They'll just paint over it."]},
    "books": {"weight": 2, "label": "paper books",
              "lines": ["I collect paper books. They can't update them on you.",
                        "Found a paper book in a dumpster today. Poems, water-stained. Best thing all week."],
              "good": ["Can't hack paper. That's the whole appeal, isn't it?",
                       "Water-stained poems. Read me one?"],
              "bad": ["Paper? Everything's on the feed, and it's free.",
                      "I haven't read anything longer than a message in years."]},
    "animals": {"weight": 1, "label": "real animals",
                "lines": ["I feed a stray cat behind my building. A real one. No chrome, no subscription.",
                          "Did you know there are still real pigeons in the old station? I counted."],
                "good": ["A real cat. Does it have a name, or is it too proud for one?",
                         "Real pigeons. The city hasn't won everything yet."],
                "bad": ["Strays carry who knows what. I'd call pest control.",
                        "Robo-pets are cleaner. No mess."]},
    "stars": {"weight": 1, "label": "the stars above the smog",
              "lines": ["On a clear night you can see three stars from my roof. I named them.",
                        "Sometimes I think about what the sky looked like before the smog."],
              "good": ["Show me which three sometime. I've never looked up long enough.",
                       "I bet it was loud with stars. We just forgot to listen."],
              "bad": ["Stars? You can see better ones on any holo-ad.",
                      "Nobody looks up here. There's nothing to see."]},
    "games": {"weight": 2, "label": "old arcade games",
              "lines": ["There's an arcade in the Undercity with cabinets older than my grandmother.",
                        "I hold the high score on a machine nobody else plays. Undefeated."],
              "good": ["Older than your grandmother and still running. Take me.",
                       "Undefeated? I want a rematch. Name the place."],
              "bad": ["Arcades? I thought those died with pay phones.",
                      "I don't really play games. Waste of time."]},
    "dance": {"weight": 2, "label": "dancing until sunrise",
              "lines": ["The best clubs are the ones that don't have a name. You just follow the bass.",
                        "I haven't danced until sunrise in months. I miss it."],
              "good": ["Then let's find one with no name. I'll follow you.",
                       "The sun's still a few hours off, if you're asking."],
              "bad": ["I don't really dance. I hold up walls.",
                      "Clubs are too loud. I like somewhere I can hear myself think."]},
}

DATE_VALUES = {
    "freedom": {"weight": 3, "desc": "freedom -- nobody owns you",
                "lines": ["Sometimes I think about getting on a bike and riding out past the wall.",
                          "Everyone here's owned by something. A corp, a gang, a debt. Not me. Not yet."],
                "good": ["I'd ride out with you. Nobody out there owns anybody.",
                         "Not yet sounds like a promise. Keep it."],
                "bad": ["Out there? No clinics, no work. Crazy talk.",
                        "Everyone needs someone watching their back. Owned isn't always bad."]},
    "loyalty": {"weight": 3, "desc": "loyalty -- you stand by your people",
                "lines": ["My best friend sold me out for a promotion once. I'm still not over it.",
                          "I'd walk into fire for my crew. They'd do the same."],
                "good": ["That's the worst kind of cut. The people who stay are what count.",
                         "People like that are rarer than chrome. Hold on to them."],
                "bad": ["Can't blame her. Everyone looks out for number one in this city.",
                        "Crews come and go. I only really count on myself."]},
    "ambition": {"weight": 2, "desc": "ambition -- you're going to be somebody",
                 "lines": ["Five years from now I'm going to own a place like this. Watch me.",
                           "I didn't come this far to stay small."],
                 "good": ["I believe it. What's it going to be called?",
                          "Neither did I. What's your next move?"],
                 "bad": ["Why stress about it? Take it easy, enjoy the ride.",
                         "Big plans get people killed around here."]},
    "honesty": {"weight": 2, "desc": "honesty -- say what you mean",
                "lines": ["Everyone in this bar is lying about something. What's yours?",
                          "I'd rather hear something ugly and true than pretty and fake."],
                "good": ["Right now? That I'm not as calm as I look.",
                         "Then here's one: I sat here because of you, not the stool."],
                "bad": ["A little mystery never hurt anyone.",
                        "Everyone lies. The trick is doing it well."]},
    "thrill": {"weight": 2, "desc": "thrills -- you live for the rush",
               "lines": ["I jumped a gap between two stacks last month. Didn't look down once.",
                         "Safe is just another word for bored."],
               "good": ["Didn't look down? I'd have wanted to see your face on the landing.",
                        "Bored's worse than dead. What's next on your list?"],
               "bad": ["That's how people end up in the gutter. Be careful.",
                       "I'll take bored if it means I live to thirty."]},
}

DATE_CHROME = {
    "loves": {"weight": 2, "desc": "you love chrome -- it's who people choose to become",
              "lines": ["My arm's the best thing I ever bought. Want to see what it can do?",
                        "People who fear chrome just don't know what they want to be yet."],
              "good": ["Show me. I want to see what you chose to become.",
                       "Chrome's just choosing yourself. I respect that."],
              "bad": ["I'd rather keep what I was born with, honestly.",
                      "Chrome freaks me out a little. No offence."]},
    "wary": {"weight": 2, "desc": "you're wary of chrome -- you've seen what it does to people",
             "lines": ["My brother went cyberpsycho. Too much chrome, too fast.",
                       "Every ripperdoc in this city is selling you a piece of yourself back."],
             "good": ["I'm sorry. The city sells you the chrome and never mentions the cost.",
                      "Somebody's got to stay human in this city. Might as well be us."],
             "bad": ["Chrome's just tools. It's the person who breaks.",
                     "I'd get more chrome in a heartbeat if I could afford it."]},
    "indifferent": {"weight": 2, "desc": "you don't care about chrome either way"},
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
# lands in the first. "prompt" tells a dialog model how she says goodbye; "canned" is her line
# without one. Stress relief is the only payoff (see CLAUDE.md balance notes); the top tier
# also makes her your partner.
DATE_OUTCOMES = [
    {"prompt": "You've had enough of this person. End it coldly and leave.",
     "canned": ["I'm going to go. Don't follow me.", "Wow. Okay. Goodnight."],
     "min_net": -DATE_ROUNDS,
     "narration": "She slides off the stool and leaves her drink unfinished.", "stress": 5},
    {"prompt": "Make a polite excuse and leave. You're not interested.",
     "canned": ["Well. Nice meeting you. I should go.", "Early shift. Take care."],
     "min_net": -1,
     "narration": "She finishes her drink a little too quickly.", "stress": 0},
    {"prompt": "Say a friendly goodbye. It was nice, but nothing more.",
     "canned": ["This was nice. Take care of yourself out there.", "Thanks for the company."],
     "min_net": 1,
     "narration": "You talk until the ice melts. Pleasant, but nothing sparks.", "stress": -3},
    {"prompt": "You enjoyed this. Hint you might like to run into them here again.",
     "canned": ["If I'm here again, you can buy the next one.", "You're not the worst company in here."],
     "min_net": 2,
     "narration": "She laughs at your jokes and touches your arm once on the way out.", "stress": -5},
    {"prompt": "You really like them, but you're not ready for more yet. Say goodnight warmly.",
     "canned": ["I like you. That's what worries me. Goodnight.", "Ask me again some other night."],
     "min_net": 4,
     "narration": "Outside, under the dripping neon, she kisses you. Then she's gone into the rain.",
     "stress": -8},
    {"prompt": "You want to keep seeing them, starting tonight. Ask them to walk you home.",
     "canned": ["Walk me home? And then tomorrow, too.", "I'm not letting you disappear. Walk with me."],
     "min_net": 5,
     "narration": "She walks out with you, and doesn't let go of your hand.", "stress": -10},
]
