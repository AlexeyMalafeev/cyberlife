"""The cast: women you meet at the bar, talk to over several nights, and maybe end up with.

Everything mechanical happens in Python first: who she is, what each round is about, how each
reply scores and in what order they're shown. The dialog model (if any) only writes words for
decisions already made, and every stock line is drawn from `random` whether or not a model is
on, so a --seed plays out the same either way.
"""
import random

from . import data, llm
from .ui import say, dim, cyan, green, red, neon, yellow, menu, ask_yes_no

KINDS = ("good", "bad", "neutral")               # replies to her talking about herself
ANSWERS = ("truth", "lie", "dodge")              # replies to her asking about you
FEEL = {1: "good", -1: "bad", 0: "neutral"}      # how a reply's score reads to her
SCENE_LIMIT = 420      # characters of model narration we'll print
REPLY_LIMIT = 160
SHOW_SHEETS = False    # print each woman's sheet() before her scene; the debug menu toggles it

# Topic kind -> (her field, table). "interest" is a list of two ids; everything else is one id.
TRAITS = {
    "occupation": ("occupation", data.DATE_OCCUPATIONS),
    "interest": ("interests", data.DATE_INTERESTS),
    "value": ("value", data.DATE_VALUES),
    "peeve": ("peeve", data.DATE_PEEVES),
    "chrome": ("chrome", data.DATE_CHROME),
    "corps": ("corps", data.DATE_CORPS),
    "vice": ("vice", data.DATE_VICES),
    "belief": ("belief", data.DATE_BELIEFS),
    "origin": ("origin", data.DATE_ORIGINS),
    "dream": ("dream", data.DATE_DREAMS),
    "family": ("family", data.DATE_FAMILIES),
    "wound": ("wound", data.DATE_WOUNDS),
}


# -- who she is ----------------------------------------------------------

def _pick(table):
    """Draw from a {id: {"weight": w, ...}} table or a [(weight, phrase), ...] list."""
    if isinstance(table, dict):
        ids = list(table)
        return random.choices(ids, [table[i]["weight"] for i in ids])[0]
    weights, phrases = zip(*table)
    return random.choices(phrases, weights)[0]


def _lean(table, lean):
    """A trait her job suggests: `lean` with DATE_LEAN_CHANCE, otherwise anything but."""
    if lean is None:
        return _pick(table)
    if random.random() < data.DATE_LEAN_CHANCE:
        return lean
    return _pick({k: v for k, v in table.items() if k != lean})


def fill_traits(her):
    """Draw any traits she's missing (all of them for a new woman; new ones for an old save)."""
    leans = data.DATE_OCCUPATIONS[her["occupation"]].get("leans", {})
    for kind, (field, table) in TRAITS.items():
        if field not in her:
            her[field] = _lean(table, leans.get(kind))
    return her


def generate(taken=()):
    """A new woman, as a JSON-safe dict: appearance phrases plus personality ids.

    `taken` names are skipped, so a cast never has two women with the same name.
    """
    first = _pick(data.DATE_INTERESTS)
    rest = {k: v for k, v in data.DATE_INTERESTS.items() if k != first}
    return fill_traits({
        "name": random.choice([n for n in data.DATE_NAMES if n not in taken]),
        "age": random.randint(*data.DATE_AGES),
        **{part: _pick(options) for part, options in data.DATE_LOOKS.items()},
        "temperament": _pick(data.DATE_TEMPERAMENTS),
        "occupation": _pick(data.DATE_OCCUPATIONS),
        "interests": [first, _pick(rest)],
    })


def relationship():
    """Fresh relationship state, carried by every cast member next to her profile.

    `discussed` holds [kind, id] topics from earlier nights, `asked` the questions you've
    answered, `lies` the ones you lied to and she hasn't caught yet.
    """
    return {"stage": "stranger", "times_met": 0, "affection": 0, "last_met_day": None,
            "last_outcome": None, "avoid_until": 0, "since_day": None, "last_seen_day": None,
            "came_along": False, "discussed": [], "asked": [], "lies": []}


def new_member(taken=()):
    return {**generate(taken), **relationship()}


def ensure_cast(player):
    """Top the cast up to data.CAST_SIZE. Character creation calls this; so do loads of saves
    from before the cast existed."""
    while len(player.cast) < data.CAST_SIZE:
        player.cast.append(new_member({c["name"] for c in player.cast}))
    return player.cast


# -- what you talk about --------------------------------------------------

def _entry(kind, key):
    return TRAITS[kind][1][key]


def _keys(her, kind):
    value = her[TRAITS[kind][0]]
    return value if kind == "interest" else [value]


def _recall(kind, key):
    """How you'd bring a topic up again, or None if it's not something you'd quote back."""
    entry = _entry(kind, key)
    return entry.get("recall") or (entry["label"] if kind == "interest" else None)


def _unlocked(her, kind):
    return her["times_met"] >= data.DATE_TOPIC_DEPTH.get(kind, 0)


def trait_topics(her):
    """Everything she'd talk about tonight. Deeper things wait until she knows you."""
    return [(kind, key) for kind in TRAITS if _unlocked(her, kind) for key in _keys(her, kind)
            if (kind, key) != ("chrome", "indifferent")]


def your_work(player):
    """How your work reads to her: "corpo", "legit", "runner" or "broke"."""
    if player.job:
        return "corpo" if player.job.get("corp") else "legit"
    return "runner" if player.cred >= data.DATE_RUNNER_CRED else "broke"


def questions(her, player):
    """What she might ask about you tonight: things you haven't answered yet."""
    asks = ["work"]
    if player.cyberware:
        asks.append("chrome")
    if player.heat >= data.DATE_TROUBLE_HEAT or player.cred >= data.DATE_TROUBLE_CRED:
        asks.append("trouble")
    return [q for q in asks if q not in her["asked"]]


def _callback(her):
    """A follow-up on something from an earlier night: ("callback", (kind, key, wrong key))."""
    told = [(k, key) for k, key in her["discussed"] if _recall(k, key)]
    kind, key = random.choice(told)
    mine = _keys(her, kind)
    wrong = random.choice([k for k in TRAITS[kind][1] if k not in mine and _recall(kind, k)])
    return ("callback", (kind, key, wrong))


def plan_topics(her, player):
    """What each round is about tonight, in order, with no topic twice.

    Things she hasn't told you yet come first; with more than a night's worth, some go unsaid.
    From the second meeting she may follow up on an earlier night, and any night she may ask
    about you. Everything's shuffled, so nothing has a fixed place in the conversation.
    """
    told = {tuple(t) for t in her["discussed"]}
    fresh = [t for t in trait_topics(her) if t not in told]
    old = [t for t in trait_topics(her) if t in told]
    random.shuffle(fresh)
    random.shuffle(old)
    extra = []
    if (any(_recall(*t) for t in told) and random.random() < data.DATE_CALLBACK_CHANCE):
        extra.append(_callback(her))
    asks = questions(her, player)
    if asks and random.random() < data.DATE_QUESTION_CHANCE:
        extra.append(("question", random.choice(asks)))
    topics = (fresh + old)[:data.DATE_ROUNDS - len(extra)] + extra
    random.shuffle(topics)
    return topics


def replies(topic):
    return ANSWERS if topic[0] == "question" else KINDS


def small_talk(her):
    """What a noncommittal reply scores with her: intense women hate it, guarded ones like it
    the first night."""
    temperament = data.DATE_TEMPERAMENTS[her["temperament"]]
    if her["times_met"] == 0 and "neutral_first" in temperament:
        return temperament["neutral_first"]
    return temperament.get("neutral", 0)


def truth_lands(her, player, question):
    """Whether telling her the truth wins her over. Depends on who she is and who you are."""
    if question == "work":
        return your_work(player) in data.DATE_CORPS[her["corps"]]["likes_work"]
    if question == "chrome":
        return data.DATE_CHROME[her["chrome"]]["likes_truth"]
    return data.DATE_VALUES[her["value"]]["likes_trouble"]


def score(her, player, topic, reply):
    """+1, 0 or -1 for a reply. A lie always lands, for now."""
    if reply in ("neutral", "dodge"):
        return small_talk(her)
    if reply == "truth":
        return 1 if truth_lands(her, player, topic[1]) else -1
    return {"good": 1, "bad": -1, "lie": 1}[reply]


def catch_lies(her):
    """Each lie she hasn't caught might surface now. Costs double with someone who values honesty."""
    for question in list(her["lies"]):
        if random.random() < data.DATE_LIE_CAUGHT:
            her["lies"].remove(question)
            cost = data.DATE_LIE_COST * (2 if her["value"] == "honesty" else 1)
            her["affection"] -= cost
            say(red(data.DATE_QUESTIONS[question]["caught"].format(name=her["name"])))


# -- prompts -------------------------------------------------------------

def _situation(her, player):
    """Where you two stand, for the persona prompt."""
    if her["stage"] in data.PARTNER_STAGES:
        home = " and they live with you now" if her["stage"] == "serious" else ""
        return (f"You're together{home}. Their real name is {player.name}; on the street they "
                f"go by {player.handle}.\n")
    if her["times_met"] == 0:
        return (f"You're at the bar of the Neon Lotus. A stranger just took the stool next to "
                f"yours and you swapped names: they go by {player.handle}. Any reply that "
                f"gives the stranger's name uses {player.handle}.\n")
    times = "once" if her["times_met"] == 1 else f"{her['times_met']} times"
    memory = data.DATE_OUTCOMES[her["last_outcome"]]["memory"]
    return (f"You're at the bar of the Neon Lotus. You've talked with {player.handle} here "
            f"{times} before; last time {memory}. They just sat down next to you again. You "
            f"already know each other's names, so don't introduce yourselves.\n")


# How the persona names each trait. Deeper ones only appear once they're unlocked, so the model
# can't bring up her wound on the first night.
_PERSONA = [("corps", "On the corps"), ("vice", "Your guilty pleasure"),
            ("belief", "What you believe in"), ("origin", "Where you're from"),
            ("dream", "What you want from life"), ("family", "Your family"),
            ("wound", "What you carry, and only share with someone you trust")]


def _persona(her, player):
    chrome = [cw["name"] for cw in data.CYBERWARE if player.has(cw["id"])]
    interests = " and ".join(data.DATE_INTERESTS[i]["label"] for i in her["interests"])
    more = " ".join(f"{label}: {_entry(kind, her[TRAITS[kind][0]])['desc']}."
                    for kind, label in _PERSONA if _unlocked(her, kind))
    told = [_recall(k, key) or _entry(k, key).get("desc") for k, key in her["discussed"]]
    told = f"You've already told them about: {'; '.join(told)}.\n" if told else ""
    return (
        f"You are {her['name']}, {her['age']}, {data.DATE_OCCUPATIONS[her['occupation']]['desc']} "
        f"in {data.CITY}, 2087, a cyberpunk megacity. {_situation(her, player)}"
        f"Your look: {her['build']}, {her['hair']}, {her['eyes']}, {her['style']}, {her['feature']}.\n"
        f"Your manner: {data.DATE_TEMPERAMENTS[her['temperament']]['desc']}. "
        f"You love {interests}. What matters most to you: {data.DATE_VALUES[her['value']]['desc']}. "
        f"You can't stand {data.DATE_PEEVES[her['peeve']]['desc']}. "
        f"On cyberware: {data.DATE_CHROME[her['chrome']]['desc']}. {more}\n{told}"
        f"The stranger: background {player.background}; job: {llm.job_desc(player)}; "
        f"chrome: {', '.join(chrome) or 'none visible'}.\n"
        "Speak casually, like a real person in a bar. Short sentences. No stage directions, "
        "no quotation marks, no name prefixes."
    )


_SMALL_TALK = "noncommittal small talk"


def _brief(player, topic):
    """(what her line does, {reply: what it does}) for the model."""
    kind, key = topic
    if kind == "callback":
        was, _, wrong = key
        return ("checking, lightly, whether the stranger remembers something you told them on "
                "an earlier night",
                {"good": f"correctly recalls {_recall(was, key[1])}",
                 "bad": f"confidently misremembers it as {_recall(was, wrong)}",
                 "neutral": _SMALL_TALK})
    if kind == "question":
        q = data.DATE_QUESTIONS[key]
        return (f"asking about {q['about']}",
                {"truth": f"answers honestly: {_truth_fact(player, key)}",
                 "lie": f"a smooth lie: {q['lie_brief']}",
                 "dodge": "politely dodges the question"})
    entry = _entry(kind, key)
    if kind == "occupation":
        return (f"steering to your work as {entry['desc']}",
                {"good": "shows genuine curiosity about or respect for your work",
                 "bad": "shrugs your work off or suggests you'd be better off doing something else",
                 "neutral": _SMALL_TALK})
    if kind == "interest":
        return (f"steering to your love of {entry['label']}",
                {"good": f"shows the stranger gets or shares your love of {entry['label']}",
                 "bad": f"dismisses {entry['label']} or prefers something else",
                 "neutral": _SMALL_TALK})
    if kind == "value":
        return (f"steering to something that shows what you value most ({entry['desc']}), "
                "without naming it",
                {"good": "shows the stranger shares that value", "bad": "reveals the opposite priority",
                 "neutral": _SMALL_TALK})
    if kind == "chrome":
        return (f"steering to cyberware ({entry['desc']})",
                {"good": "matches how you feel about chrome", "bad": "takes the opposite view of chrome",
                 "neutral": _SMALL_TALK})
    if kind == "peeve":
        return (f"a question or remark that shows whether the stranger is given to {entry['desc']}",
                {"good": entry["good_desc"],
                 "bad": f"is a clear case of {entry['desc']}, the thing you can't stand",
                 "neutral": _SMALL_TALK})
    if kind == "wound":
        return (f"opening up a little about something painful ({entry['desc']})",
                {"good": "listens and makes room, without trying to fix it",
                 "bad": "tries to fix it, pries for details, or brushes it off",
                 "neutral": _SMALL_TALK})
    return (f"steering to {entry['desc']}",
            {"good": "shows genuine interest in it or sympathy with it",
             "bad": "dismisses it or pushes the opposite view",
             "neutral": _SMALL_TALK})


def _transcript(history):
    lines = []
    for hers, yours in history:
        lines += [f"You: {hers}", f"Stranger: {yours}"]
    return "\n".join(lines) or "(nothing yet -- you've only swapped names)"


def round_messages(her, player, topic, history, last):
    about, briefs = _brief(player, topic)
    mood = {"good": "The stranger's last reply won you over a little.",
            "bad": "The stranger's last reply put you off a little.",
            "neutral": "The stranger's last reply was fine, if forgettable.",
            None: ""}[last]
    shape = ", ".join(f'"{k}": "..."' for k in ("line", *briefs))
    user = (
        f"Conversation so far:\n{_transcript(history)}\n{mood}\n\n"
        f"Write your next line (under 30 words), reacting naturally and {about}. "
        "Then write three things the stranger could say back, in first person, each under 20 words:\n"
        + "".join(f'- "{k}": {brief}\n' for k, brief in briefs.items()) +
        "All three must sound natural and friendly on the surface: don't make the bad one rude, "
        "the good one flattering, or any of them name your traits.\n"
        f"Answer with only a JSON object: {{{shape}}}"
    )
    return [{"role": "system", "content": _persona(her, player)}, {"role": "user", "content": user}]


def scene_messages(her, spot, hint, example):
    occupation = data.DATE_OCCUPATIONS[her["occupation"]]["desc"]
    system = (f"You narrate a text game set in {data.CITY}, 2087, a cyberpunk megacity. "
              "Second person, present tense, terse and atmospheric.")
    user = (
        "In two or three short sentences (under 60 words), describe the player noticing a young "
        f"woman at the Neon Lotus. She's {spot}.\n"
        f"Her look: {her['build']}, {her['hair']}, {her['eyes']}, {her['style']}, {her['feature']}.\n"
        f"Maybe a visual clue to her work ({occupation}), nothing more.\n"
        f"End on this small detail, in your own words: {hint}\n"
        "Don't name her, don't describe her personality, no dialog, no numbers.\n"
        f"For tone only, don't reuse its wording: {example}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def closing_messages(her, player, history, ending, example):
    user = (f"Conversation so far:\n{_transcript(history)}\n\n"
            f"The conversation is ending. {ending['prompt']} One line, under 25 words, spoken "
            f"dialog only.\nFor tone only, don't reuse its wording: {example}")
    return [{"role": "system", "content": _persona(her, player)}, {"role": "user", "content": user}]


# -- words: stock first, then the model if it has something usable ------------------

def scene(her, spot):
    """How you notice her tonight.

    A stranger gets her looks and one vague hint, never her personality. Someone you've met
    gets a line that shows how your last night together went.
    """
    if her["times_met"]:
        mood = data.DATE_OUTCOMES[her["last_outcome"]]["again"]
        return random.choice(data.DATE_AGAIN).format(spot=spot, mood=mood, **her)
    hint = random.choice(data.DATE_TEMPERAMENTS[her["temperament"]]["hints"])
    canned = random.choice(data.DATE_SCENES).format(spot=spot, hint=hint, **her)
    text = llm.sanitize(llm.complete(scene_messages(her, spot, hint, canned), max_tokens=160),
                        limit=SCENE_LIMIT)
    return text or canned


def _chrome_names(player):
    return ", ".join(cw["name"] for cw in data.CYBERWARE if player.has(cw["id"]))


def _truth_fact(player, question):
    q = data.DATE_QUESTIONS[question]
    if question == "work":
        return q["truth_brief"][your_work(player)].format(job=llm.job_desc(player))
    return q["truth_brief"].format(chrome=_chrome_names(player))


def stock_round(her, player, topic):
    """Her line and every reply, from the tables. Always drawn, model or not."""
    kind, key = topic
    if kind == "callback":
        was, right, wrong = key
        reply = random.choice(data.DATE_CALLBACK["replies"])     # same sentence, different detail
        return {"line": random.choice(data.DATE_CALLBACK["lines"]),
                "good": reply.format(thing=_recall(was, right)),
                "bad": reply.format(thing=_recall(was, wrong)),
                "neutral": random.choice(data.DATE_NEUTRAL)}
    if kind == "question":
        q = data.DATE_QUESTIONS[key]
        truths = q["truth"][your_work(player)] if key == "work" else q["truth"]
        job = player.job["desc"] if player.job else ""
        return {"line": random.choice(q["lines"]),
                "truth": random.choice(truths).format(job=job, chrome=_chrome_names(player)),
                "lie": random.choice(q["lie"]),
                "dodge": random.choice(data.DATE_DODGE)}
    entry = _entry(kind, key)
    i = random.randrange(len(entry["lines"]))     # good[i] and bad[i] answer lines[i]
    return {"line": entry["lines"][i], "good": entry["good"][i], "bad": entry["bad"][i],
            "neutral": random.choice(data.DATE_NEUTRAL)}


def voice_round(her, player, topic, history, last):
    """The model's version of a round, or None if it gave nothing usable.

    Numbers are allowed here, unlike NPC lines: no prices or stats ride on this dialog.
    """
    reply = llm.parse_json(llm.complete(round_messages(her, player, topic, history, last),
                                        max_tokens=300))
    if reply is None:
        return None
    names = replies(topic)
    voiced = {"line": llm.sanitize(reply.get("line"), her["name"])}
    voiced.update({k: llm.sanitize(reply.get(k), "You", limit=REPLY_LIMIT) for k in names})
    said = [voiced[k].lower() for k in names]
    if not all(voiced.values()) or len(set(said)) < len(names):
        return None
    return voiced


def closing(her, player, history, ending):
    canned = random.choice(ending["canned"])
    text = llm.complete(closing_messages(her, player, history, ending, canned))
    return llm.sanitize(text, her["name"]) or canned


# -- the encounter -------------------------------------------------------

def _her_line(her, line):
    say(f"{cyan(her['name'])}: {dim(line)}")


def outcome(net, walked_out, ready=False):
    """The DATE_OUTCOMES entry for a finished conversation. `ready`: she could become your partner."""
    if walked_out:
        return data.DATE_OUTCOMES[0]
    return [o for o in data.DATE_OUTCOMES
            if net >= o["min_net"] and (ready or not o.get("partner"))][-1]


def chat(player, her):
    """Play the conversation. Returns (net score, walked out?, [(her line, your reply)]).

    Each reply scores +1, 0 or -1 (see score()), so the net is -DATE_ROUNDS..DATE_ROUNDS.
    Afterwards she remembers what she told you, which questions you answered, and your lies.
    """
    net, history, last = 0, [], None
    for topic in plan_topics(her, player):
        names = replies(topic)
        stock = stock_round(her, player, topic)     # drawn every round: keeps --seed stable
        order = random.sample(names, len(names))
        reaction = {k: random.choice(data.DATE_REACTIONS[k]) for k in KINDS}
        beat = voice_round(her, player, topic, history, last) or stock
        say()
        _her_line(her, beat["line"])
        reply = order[menu("You say:", [beat[k] for k in order])]
        points = score(her, player, topic, reply)
        net += points
        last = FEEL[points]
        say(dim(reaction[last]))
        history.append((beat["line"], beat[reply]))
        _remember(her, topic, reply)
        if net <= data.DATE_WALKOUT and len(history) < data.DATE_ROUNDS:
            return net, True, history
    return net, False, history


def _remember(her, topic, reply):
    kind, key = topic
    if kind == "question":
        if reply != "dodge":
            her["asked"].append(key)
        if reply == "lie":
            her["lies"].append(key)
    elif kind != "callback" and [kind, key] not in her["discussed"]:
        her["discussed"].append([kind, key])


def present(player):
    """Who's at the bar tonight: one or two cast members willing to talk to you."""
    pool = [c for c in player.cast
            if c["stage"] in ("stranger", "met") and c["avoid_until"] <= player.day]
    count = min(len(pool), random.choice(data.DATE_AT_BAR))
    return random.sample(pool, count)


def _choose(here, spots):
    """Which of them you approach, or None."""
    if len(here) == 1:
        her = here[0]
        return her if ask_yes_no("Try your luck?" if not her["times_met"]
                                 else f"Join {her['name']}?") else None
    labels = [f"{her['name']}, {spot}" if her["times_met"] else f"The woman {spot}"
              for her, spot in zip(here, spots)]
    choice = menu("Who do you approach?", labels + [dim("Neither")])
    return here[choice] if choice < len(here) else None


def encounter(player):
    """Maybe someone from the cast is at the bar. Returns None if nobody is, else the stress
    change to report."""
    if player.partner is not None or random.random() >= data.ENCOUNTER_CHANCE:
        return None
    ensure_cast(player)
    here = present(player)
    if not here:
        return None
    return meet(player, here)


def meet(player, here):
    """Seat `here` (one or two cast members) at the bar and play the night out. Returns the
    stress change to report. The debug menu calls this directly to skip the dice."""
    spots = random.sample(data.BAR_SPOTS, len(here))
    for her, spot in zip(here, spots):
        say()
        if SHOW_SHEETS:
            sheet(her)
        say(neon(scene(her, spot)))
    her = _choose(here, spots)
    if her is None:
        say(dim("You let the moment pass. Probably for the best. Probably."))
        return 0
    if her["times_met"]:
        say(dim(f"You take the stool next to {her['name']}. She remembers your handle."))
        catch_lies(her)
    else:
        say(dim(f"You slide onto the stool next to her and trade names over the noise. "
                f"She's {her['name']}."))
    net, walked_out, history = chat(player, her)
    ready = (player.partner is None and her["times_met"] + 1 >= data.DATE_MIN_MEETINGS
             and her["affection"] + net >= data.DATE_PARTNER_AFFECTION)
    ending = outcome(net, walked_out, ready)
    say()
    _her_line(her, closing(her, player, history, ending))   # she still remembers the old night
    say(dim(ending["narration"]))
    her.update(stage="met", times_met=her["times_met"] + 1, affection=her["affection"] + net,
               last_met_day=player.day, last_outcome=data.DATE_OUTCOMES.index(ending))
    if walked_out or net <= data.DATE_AVOID_NET:
        her["avoid_until"] = player.day + data.DATE_AVOID_DAYS
    player.stress += ending["stress"]
    if ending.get("partner"):
        start_relationship(player, her)
        say(green(f"You're seeing {her['name']} now."))
    return ending["stress"]


def sheet(her):
    """Print her hidden profile and where she stands with you. Debug only: in play, reading
    her is the whole game."""
    rows = [
        ("Look", f"{her['build']}, {her['hair']}, {her['eyes']}, {her['style']}, {her['feature']}"),
        ("Manner", f"{her['temperament']}: {data.DATE_TEMPERAMENTS[her['temperament']]['desc']}"),
    ]
    for kind, (field, table) in TRAITS.items():     # every trait, so new ones show up here too
        ids = her[field] if isinstance(her[field], list) else [her[field]]
        text = " and ".join(table[i].get("desc") or table[i]["label"] for i in ids)
        rows.append((kind.capitalize(), f"{', '.join(ids)}: {text}"))
    status = f"{her['stage']}, met {her['times_met']}x, affection {her['affection']}"
    if her["last_outcome"] is not None:
        status += f"; last time {data.DATE_OUTCOMES[her['last_outcome']]['memory']}"
    if her["avoid_until"]:
        status += f"; avoiding you until day {her['avoid_until']}"
    rows.append(("Status", status))
    if her["discussed"]:
        rows.append(("Told you", ", ".join(f"{k} {i}" for k, i in her["discussed"])))
    if her["lies"]:
        rows.append(("Your lies", ", ".join(map(str, her["lies"]))))
    say(yellow(f"-- {her['name']}, {her['age']} " + "-" * 30))
    for label, text in rows:
        say(f"   {dim(label.ljust(12))}{text}")


# -- together ------------------------------------------------------------

def start_relationship(player, her):
    her.update(stage="dating", since_day=player.day, last_seen_day=player.day)


def outings(her):
    """[(label, effects)] for time together: her interests' outings, then staying in."""
    options = [(data.DATE_INTERESTS[i]["outing"], data.REL_OUTING) for i in her["interests"]]
    return options + [(data.REL_STAY_IN["label"], data.REL_STAY_IN)]


def together_messages(her, player, activity, example):
    user = (f"You and {player.handle} just spent the evening together: {activity}. Say one "
            "thing to them as it winds down. One line, under 25 words, spoken dialog only.\n"
            f"For tone only, don't reuse its wording: {example}")
    return [{"role": "system", "content": _persona(her, player)}, {"role": "user", "content": user}]


def together_line(her, player, activity):
    canned = random.choice(data.REL_TOGETHER)
    text = llm.complete(together_messages(her, player, activity, canned))
    return llm.sanitize(text, her["name"]) or canned


def night(player):
    """Nightly drift for your partner: neglect and worry cost affection; too little and she
    leaves, enough for long enough and she moves in."""
    her = player.partner
    if her is None:
        return
    name = her["name"]
    catch_lies(her)
    if player.day - her["last_seen_day"] >= data.REL_NEGLECT_DAYS:
        her["affection"] -= 1
        say(dim(random.choice(data.REL_NEGLECTED).format(name=name)))
    if player.heat >= data.REL_WORRY_HEAT or player.humanity < data.REL_WORRY_HUMANITY:
        her["affection"] -= data.REL_WORRY_COST
        say(dim(random.choice(data.REL_WORRIED).format(name=name)))
    if her["affection"] < data.REL_LEAVE_AFFECTION:
        her["stage"] = "gone"
        player.stress += data.REL_LEAVE_STRESS
        say(red(data.REL_LEAVES.format(name=name)))
    elif (her["stage"] == "dating" and her["affection"] >= data.REL_SERIOUS_AFFECTION
          and player.day - her["since_day"] >= data.REL_SERIOUS_DAYS):
        her["stage"] = "serious"
        say(green(data.REL_MOVES_IN.format(name=name)))
