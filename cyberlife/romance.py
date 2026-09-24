"""Bar encounters: meet someone, talk, maybe start something.

Everything mechanical happens in Python first: who she is, what each round is about, which
reply is good/bad/neutral and in what order they're shown. The dialog model (if any) only
writes words for decisions already made, and every stock line is drawn from `random` whether
or not a model is on, so a --seed plays out the same either way.
"""
import random

from . import data, llm
from .ui import say, dim, cyan, green, neon, menu, ask_yes_no

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


def generate():
    """A new woman at the bar, as a JSON-safe dict: appearance phrases plus personality ids."""
    first = _pick(data.DATE_INTERESTS)
    rest = {k: v for k, v in data.DATE_INTERESTS.items() if k != first}
    return {
        "name": random.choice(data.DATE_NAMES),
        "age": random.randint(*data.DATE_AGES),
        **{part: _pick(options) for part, options in data.DATE_LOOKS.items()},
        "temperament": _pick(data.DATE_TEMPERAMENTS),
        "occupation": _pick(data.DATE_OCCUPATIONS),
        "interests": [first, _pick(rest)],
        "value": _pick(data.DATE_VALUES),
        "peeve": _pick(data.DATE_PEEVES),
        "chrome": _pick(data.DATE_CHROME),
    }


def plan_topics(her):
    """What each round is about: her work first, then a shuffled mix of the rest."""
    rest = [("interest", i) for i in her["interests"]]
    rest += [("value", her["value"]), ("peeve", her["peeve"])]
    if her["chrome"] != "indifferent":
        rest.append(("chrome", her["chrome"]))
    random.shuffle(rest)
    return [("occupation", her["occupation"])] + rest[:data.DATE_ROUNDS - 1]


def _topic_entry(kind, key):
    table = {"occupation": data.DATE_OCCUPATIONS, "interest": data.DATE_INTERESTS,
             "value": data.DATE_VALUES, "peeve": data.DATE_PEEVES, "chrome": data.DATE_CHROME}[kind]
    return table[key]


# -- prompts -------------------------------------------------------------

def _persona(her, player):
    chrome = [cw["name"] for cw in data.CYBERWARE if player.has(cw["id"])]
    interests = " and ".join(data.DATE_INTERESTS[i]["label"] for i in her["interests"])
    return (
        f"You are {her['name']}, {her['age']}, {data.DATE_OCCUPATIONS[her['occupation']]['desc']} "
        f"in {data.CITY}, 2087, a cyberpunk megacity. You're at the bar of the Neon Lotus, talking "
        f"to a stranger who sat down next to you.\n"
        f"Your look: {her['build']}, {her['hair']}, {her['eyes']}, {her['style']}, {her['feature']}.\n"
        f"Your manner: {data.DATE_TEMPERAMENTS[her['temperament']]['desc']}. "
        f"You love {interests}. What matters most to you: {data.DATE_VALUES[her['value']]['desc']}. "
        f"You can't stand {data.DATE_PEEVES[her['peeve']]['desc']}. "
        f"On cyberware: {data.DATE_CHROME[her['chrome']]['desc']}.\n"
        f"The stranger is a {player.background}; chrome: {', '.join(chrome) or 'none visible'}.\n"
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
    return ("an open question about the stranger",
            f"is the opposite of {entry['desc']}",
            f"is a perfect example of {entry['desc']}, the thing you can't stand")


def _transcript(history):
    lines = []
    for hers, yours in history:
        lines += [f"You: {hers}", f"Stranger: {yours}"]
    return "\n".join(lines) or "(nothing yet -- the stranger just sat down)"


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


def scene_messages(her, hint, example):
    occupation = data.DATE_OCCUPATIONS[her["occupation"]]["desc"]
    system = (f"You narrate a text game set in {data.CITY}, 2087, a cyberpunk megacity. "
              "Second person, present tense, terse and atmospheric.")
    user = (
        "In two or three short sentences (under 60 words), describe the player noticing a young "
        "woman at the bar of the Neon Lotus.\n"
        f"Her look: {her['build']}, {her['hair']}, {her['eyes']}, {her['style']}, {her['feature']}.\n"
        f"Maybe a visual clue to her work ({occupation}), nothing more.\n"
        f"End on this small detail, in your own words: {hint}\n"
        "Don't name her, don't describe her personality, no dialog, no numbers.\n"
        f"For tone only, don't reuse its wording: {example}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def closing_messages(her, player, history, outcome, example):
    user = (f"Conversation so far:\n{_transcript(history)}\n\n"
            f"The conversation is ending. {outcome['prompt']} One line, under 25 words, spoken "
            f"dialog only.\nFor tone only, don't reuse its wording: {example}")
    return [{"role": "system", "content": _persona(her, player)}, {"role": "user", "content": user}]


# -- words: stock first, then the model if it has something usable ------------------

def scene(her):
    """The opening description: her looks and one vague hint, never her personality."""
    hint = random.choice(data.DATE_TEMPERAMENTS[her["temperament"]]["hints"])
    canned = random.choice(data.DATE_SCENES).format(hint=hint, **her)
    text = llm.sanitize(llm.complete(scene_messages(her, hint, canned), max_tokens=160),
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


def closing(her, player, history, outcome):
    canned = random.choice(outcome["canned"])
    text = llm.complete(closing_messages(her, player, history, outcome, canned))
    return llm.sanitize(text, her["name"]) or canned


# -- the encounter -------------------------------------------------------

def _her_line(her, line):
    say(f"{cyan(her['name'])}: {dim(line)}")


def chat(player, her):
    """Play the conversation. Returns (score from 0 to DATE_ROUNDS, [(her line, your reply)])."""
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
        if net <= data.DATE_WALKOUT:
            break
    return max(0, net), history


def encounter(player):
    """Maybe meet someone at the bar. Returns None if nobody did, else the stress change to report."""
    if player.partner is not None or random.random() >= data.ENCOUNTER_CHANCE:
        return None
    her = generate()
    say()
    say(neon(scene(her)))
    if not ask_yes_no("Try your luck?"):
        say(dim("You let the moment pass. Probably for the best. Probably."))
        return 0
    say(dim(f"You slide onto the stool next to her. She tells you her name is {her['name']}."))
    score, history = chat(player, her)
    outcome = data.DATE_OUTCOMES[score]
    say()
    _her_line(her, closing(her, player, history, outcome))
    say(dim(outcome["narration"]))
    player.stress += outcome["stress"]
    if score == data.DATE_ROUNDS:
        player.partner = {**her, "since_day": player.day}
        say(green(f"You're seeing {her['name']} now."))
    return outcome["stress"]
