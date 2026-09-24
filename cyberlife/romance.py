"""The cast: women you meet at the bar, talk to over several nights, and maybe end up with.

Everything mechanical happens in Python first: who she is, what each round is about, which
reply is good/bad/neutral and in what order they're shown. The dialog model (if any) only
writes words for decisions already made, and every stock line is drawn from `random` whether
or not a model is on, so a --seed plays out the same either way.
"""
import random

from . import data, llm
from .ui import say, dim, cyan, green, red, neon, menu, ask_yes_no

KINDS = ("good", "bad", "neutral")
SCORE = {"good": 1, "bad": -1, "neutral": 0}
SCENE_LIMIT = 420      # characters of model narration we'll print
REPLY_LIMIT = 160


# -- who she is ----------------------------------------------------------

def _pick(table):
    """Draw from a {id: {"weight": w, ...}} table or a [(weight, phrase), ...] list."""
    if isinstance(table, dict):
        ids = list(table)
        return random.choices(ids, [table[i]["weight"] for i in ids])[0]
    weights, phrases = zip(*table)
    return random.choices(phrases, weights)[0]


def generate(taken=()):
    """A new woman, as a JSON-safe dict: appearance phrases plus personality ids.

    `taken` names are skipped, so a cast never has two women with the same name.
    """
    first = _pick(data.DATE_INTERESTS)
    rest = {k: v for k, v in data.DATE_INTERESTS.items() if k != first}
    return {
        "name": random.choice([n for n in data.DATE_NAMES if n not in taken]),
        "age": random.randint(*data.DATE_AGES),
        **{part: _pick(options) for part, options in data.DATE_LOOKS.items()},
        "temperament": _pick(data.DATE_TEMPERAMENTS),
        "occupation": _pick(data.DATE_OCCUPATIONS),
        "interests": [first, _pick(rest)],
        "value": _pick(data.DATE_VALUES),
        "peeve": _pick(data.DATE_PEEVES),
        "chrome": _pick(data.DATE_CHROME),
    }


# Relationship state every cast member carries next to her profile.
RELATIONSHIP = {"stage": "stranger", "times_met": 0, "affection": 0, "last_met_day": None,
                "last_outcome": None, "avoid_until": 0, "since_day": None,
                "last_seen_day": None, "came_along": False}


def new_member(taken=()):
    return {**generate(taken), **RELATIONSHIP}


def ensure_cast(player):
    """Top the cast up to data.CAST_SIZE. Character creation calls this; so do loads of saves
    from before the cast existed."""
    while len(player.cast) < data.CAST_SIZE:
        player.cast.append(new_member({c["name"] for c in player.cast}))
    return player.cast


def plan_topics(her):
    """What each round is about: a shuffled pick of everything there is to know about her.

    No topic comes up twice in one night. With more topics than rounds, some go unmentioned.
    """
    topics = [("occupation", her["occupation"]), ("value", her["value"]), ("peeve", her["peeve"])]
    topics += [("interest", i) for i in her["interests"]]
    if her["chrome"] != "indifferent":
        topics.append(("chrome", her["chrome"]))
    return random.sample(topics, data.DATE_ROUNDS)


def _topic_entry(kind, key):
    table = {"occupation": data.DATE_OCCUPATIONS, "interest": data.DATE_INTERESTS,
             "value": data.DATE_VALUES, "peeve": data.DATE_PEEVES, "chrome": data.DATE_CHROME}[kind]
    return table[key]


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


def _persona(her, player):
    chrome = [cw["name"] for cw in data.CYBERWARE if player.has(cw["id"])]
    interests = " and ".join(data.DATE_INTERESTS[i]["label"] for i in her["interests"])
    return (
        f"You are {her['name']}, {her['age']}, {data.DATE_OCCUPATIONS[her['occupation']]['desc']} "
        f"in {data.CITY}, 2087, a cyberpunk megacity. {_situation(her, player)}"
        f"Your look: {her['build']}, {her['hair']}, {her['eyes']}, {her['style']}, {her['feature']}.\n"
        f"Your manner: {data.DATE_TEMPERAMENTS[her['temperament']]['desc']}. "
        f"You love {interests}. What matters most to you: {data.DATE_VALUES[her['value']]['desc']}. "
        f"You can't stand {data.DATE_PEEVES[her['peeve']]['desc']}. "
        f"On cyberware: {data.DATE_CHROME[her['chrome']]['desc']}.\n"
        f"The stranger: background {player.background}; job: {llm.job_desc(player)}; "
        f"chrome: {', '.join(chrome) or 'none visible'}.\n"
        "Speak casually, like a real person in a bar. Short sentences. No stage directions, "
        "no quotation marks, no name prefixes."
    )


def _topic_brief(kind, key):
    """(what her line is about, what a good reply does, what a bad reply does) for the model."""
    entry = _topic_entry(kind, key)
    if kind == "occupation":
        return (f"your work as {entry['desc']}",
                "shows genuine curiosity about or respect for your work",
                "shrugs your work off or suggests you'd be better off doing something else")
    if kind == "interest":
        return (f"your love of {entry['label']}",
                f"shows the stranger gets or shares your love of {entry['label']}",
                f"dismisses {entry['label']} or prefers something else")
    if kind == "value":
        return (f"something that shows what you value most ({entry['desc']}), without naming it",
                "shows the stranger shares that value",
                "reveals the opposite priority")
    if kind == "chrome":
        return (f"cyberware ({entry['desc']})",
                "matches how you feel about chrome",
                "takes the opposite view of chrome")
    return (f"a question or remark that shows whether the stranger is given to {entry['desc']}",
            entry["good_desc"],
            f"is a clear case of {entry['desc']}, the thing you can't stand")


def _transcript(history):
    lines = []
    for hers, yours in history:
        lines += [f"You: {hers}", f"Stranger: {yours}"]
    return "\n".join(lines) or "(nothing yet -- you've only swapped names)"


def round_messages(her, player, topic, history, last):
    about, good, bad = _topic_brief(*topic)
    mood = {"good": "The stranger's last reply won you over a little.",
            "bad": "The stranger's last reply put you off a little.",
            "neutral": "The stranger's last reply was fine, if forgettable.",
            None: ""}[last]
    user = (
        f"Conversation so far:\n{_transcript(history)}\n{mood}\n\n"
        f"Write your next line (under 30 words), reacting naturally and steering to {about}. "
        "Then write three things the stranger could say back, in first person, each under 20 words:\n"
        f'- "good": {good}\n'
        f'- "bad": {bad}\n'
        '- "neutral": noncommittal small talk that neither pleases nor bothers you\n'
        "All three must sound natural and friendly on the surface: don't make the bad one rude, "
        "the good one flattering, or any of them name your traits.\n"
        'Answer with only a JSON object: {"line": "...", "good": "...", "bad": "...", "neutral": "..."}'
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


def stock_round(topic):
    entry = _topic_entry(*topic)
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
    voiced = {"line": llm.sanitize(reply.get("line"), her["name"])}
    voiced.update({k: llm.sanitize(reply.get(k), "You", limit=REPLY_LIMIT) for k in KINDS})
    replies = [voiced[k].lower() for k in KINDS]
    if not all(voiced.values()) or len(set(replies)) < len(KINDS):
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

    The net score is +1 per good reply and -1 per bad one, -DATE_ROUNDS..DATE_ROUNDS.
    """
    net, history, last = 0, [], None
    for topic in plan_topics(her):
        stock = stock_round(topic)                  # drawn every round: keeps --seed stable
        order = random.sample(KINDS, len(KINDS))
        reaction = {k: random.choice(data.DATE_REACTIONS[k]) for k in KINDS}
        beat = voice_round(her, player, topic, history, last) or stock
        say()
        _her_line(her, beat["line"])
        kind = order[menu("You say:", [beat[k] for k in order])]
        net += SCORE[kind]
        say(dim(reaction[kind]))
        history.append((beat["line"], beat[kind]))
        last = kind
        if net <= data.DATE_WALKOUT and len(history) < data.DATE_ROUNDS:
            return net, True, history
    return net, False, history


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
    spots = random.sample(data.BAR_SPOTS, len(here))
    for her, spot in zip(here, spots):
        say()
        say(neon(scene(her, spot)))
    her = _choose(here, spots)
    if her is None:
        say(dim("You let the moment pass. Probably for the best. Probably."))
        return 0
    if her["times_met"]:
        say(dim(f"You take the stool next to {her['name']}. She remembers your handle."))
    else:
        say(dim(f"You slide onto the stool next to her and trade names over the noise. "
                f"She's {her['name']}."))
    net, walked_out, history = chat(player, her)
    ready = (her["times_met"] + 1 >= data.DATE_MIN_MEETINGS
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
