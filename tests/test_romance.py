import json
import random
import re

import pytest

from cyberlife import actions, data, llm, romance, save


class Stub:
    """A dialog backend that hands out scripted replies in order (the last one repeats)."""
    name = "stub"

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, messages, max_tokens=None):
        self.calls.append(messages)
        reply = self.replies[min(len(self.calls), len(self.replies)) - 1]
        if isinstance(reply, Exception):
            raise reply
        return reply


def round_json(n=0):
    return json.dumps({"line": f"Model line {n}.", "good": f"Good reply {n}.",
                       "bad": f"Bad reply {n}.", "neutral": f"Neutral reply {n}."})


REAL_TEMPERAMENTS = data.DATE_TEMPERAMENTS
LIGHT = {"occupation", "interest", "value", "peeve", "chrome", "corps", "vice", "belief"}


@pytest.fixture(autouse=True)
def plain_rounds(monkeypatch):
    """Unless a test opts back in: no follow-ups, no questions about you, and small talk scores 0
    whatever her temperament, so steer("neutral") means exactly 0."""
    monkeypatch.setattr(data, "DATE_CALLBACK_CHANCE", 0.0)
    monkeypatch.setattr(data, "DATE_QUESTION_CHANCE", 0.0)
    monkeypatch.setattr(data, "DATE_TEMPERAMENTS", {
        k: {f: v for f, v in t.items() if f not in ("neutral", "neutral_first")}
        for k, t in REAL_TEMPERAMENTS.items()})


@pytest.fixture
def always(monkeypatch):
    """Every bar visit has an encounter, with a one-woman cast who's always there alone."""
    monkeypatch.setattr(data, "ENCOUNTER_CHANCE", 1.0)
    monkeypatch.setattr(data, "DATE_AT_BAR", (1,))
    monkeypatch.setattr(data, "CAST_SIZE", 1)


@pytest.fixture
def her(player, always):
    return romance.ensure_cast(player)[0]


@pytest.fixture
def steer(monkeypatch):
    """Answer each round's menu with the reply of the kind scripted, whatever order it's shown in.

    Replies are taken in order, per round type: a round about her takes the next of
    good/bad/neutral, a question about you the next of truth/lie/dodge, wherever it falls.
    accept=True/False answers the "Try your luck?" prompt first; None skips it (for chat() alone).
    Returns the input queue; steer.keys records every menu key it picked.
    """
    from cyberlife import ui
    real_sample = random.sample

    def _steer(*kinds, accept=True):
        queue = [] if accept is None else ["y" if accept else "n"]
        plan = list(kinds)

        def sample(population, k):
            order = real_sample(population, k)
            fits = [r for r in plan if r in population]
            if tuple(population) in (romance.KINDS, romance.ANSWERS) and fits:
                plan.remove(fits[0])
                key = str(order.index(fits[0]) + 1)
                queue.append(key)
                _steer.keys.append(key)
            return order

        def _read(prompt=""):
            if not queue:
                raise AssertionError(f"unexpected prompt with no scripted answer: {prompt!r}")
            return queue.pop(0)

        monkeypatch.setattr(random, "sample", sample)
        monkeypatch.setattr(ui, "_read", _read)
        return queue
    _steer.keys = []
    return _steer


# -- who she is ----------------------------------------------------------

def test_same_seed_same_woman():
    random.seed(11)
    first = romance.generate()
    random.seed(11)
    assert romance.generate() == first


def test_women_vary():
    random.seed(3)
    women = [romance.generate() for _ in range(300)]
    assert len({json.dumps(w, sort_keys=True) for w in women}) == 300
    for trait in ("name", "temperament", "occupation", "value", "peeve", "chrome", "hair", "eyes"):
        assert len({w[trait] for w in women}) >= 3, trait


def test_generated_traits_are_valid():
    random.seed(5)
    for _ in range(200):
        her = romance.generate()
        a, b = her["interests"]
        assert a != b and a in data.DATE_INTERESTS and b in data.DATE_INTERESTS
        assert data.DATE_AGES[0] <= her["age"] <= data.DATE_AGES[1]
        assert her["occupation"] in data.DATE_OCCUPATIONS and her["chrome"] in data.DATE_CHROME


def test_topics_fill_every_round_without_repeats(player):
    random.seed(2)
    for _ in range(100):
        her = romance.new_member()
        topics = romance.plan_topics(her, player)
        assert len(topics) == data.DATE_ROUNDS
        assert len(set(topics)) == len(topics)
        assert ("chrome", "indifferent") not in topics
        assert set(topics) <= set(romance.trait_topics(her))


def test_first_night_topics_come_in_any_order_and_some_get_skipped(player):
    """Her work isn't always the opener, and there's more to her than one night covers."""
    random.seed(6)
    her = romance.new_member()
    her["chrome"] = "wary"
    plans = [romance.plan_topics(her, player) for _ in range(300)]
    assert {plan[0][0] for plan in plans} == LIGHT
    assert {plan[-1][0] for plan in plans} == LIGHT
    for kind in LIGHT - {"interest"}:
        assert any(kind not in {k for k, _ in plan} for plan in plans), kind


def test_same_woman_different_night_different_order(player):
    random.seed(9)
    her = romance.new_member()
    assert len({tuple(romance.plan_topics(her, player)) for _ in range(20)}) > 1


@pytest.mark.parametrize("times_met, unlocked", [
    (0, set()), (1, {"origin", "dream", "family"}), (2, {"origin", "dream", "family", "wound"}),
])
def test_deeper_topics_wait_until_she_knows_you(times_met, unlocked):
    random.seed(3)
    her = romance.new_member()
    her["times_met"] = times_met
    kinds = {kind for kind, _ in romance.trait_topics(her)}
    assert kinds - LIGHT == unlocked


def test_things_she_hasnt_told_you_come_first(player):
    random.seed(4)
    her = romance.new_member()
    her["times_met"] = 1
    told = romance.trait_topics(her)[:6]
    her["discussed"] = [list(t) for t in told]
    for _ in range(50):
        plan = romance.plan_topics(her, player)
        assert not set(plan) & set(told)          # there are enough new things to fill a night


def test_topics_played_are_remembered(player, steer):
    random.seed(5)
    her = romance.new_member()
    steer(*["neutral"] * 5, accept=None)
    romance.chat(player, her)
    assert len(her["discussed"]) == data.DATE_ROUNDS
    assert all(tuple(t) in romance.trait_topics(her) for t in her["discussed"])


# -- who she is, deeper ---------------------------------------------------

def test_every_trait_is_drawn_and_valid():
    random.seed(7)
    for _ in range(200):
        her = romance.generate()
        for kind, (field, table) in romance.TRAITS.items():
            values = her[field] if kind == "interest" else [her[field]]
            assert all(v in table for v in values), kind


def test_her_job_suggests_but_doesnt_decide(monkeypatch):
    """A medic leans wary of chrome, but sometimes she's the opposite of what her job suggests."""
    random.seed(8)
    monkeypatch.setattr(data, "DATE_OCCUPATIONS", {"medtech": data.DATE_OCCUPATIONS["medtech"]})
    views = [romance.generate()["chrome"] for _ in range(400)]
    wary = views.count("wary") / len(views)
    assert 0.4 < wary < 0.7                      # the lean, about half the time...
    assert {"loves", "indifferent"} <= set(views)  # ...and the rest, anything but
    monkeypatch.setattr(data, "DATE_LEAN_CHANCE", 0.0)
    assert "wary" not in {romance.generate()["chrome"] for _ in range(100)}


def test_persona_holds_back_deeper_traits_until_unlocked(player):
    random.seed(9)
    her = romance.new_member()
    her["last_outcome"] = 2
    wound = data.DATE_WOUNDS[her["wound"]]["desc"]
    dream = data.DATE_DREAMS[her["dream"]]["desc"]
    first = romance._persona(her, player)
    assert data.DATE_VICES[her["vice"]]["desc"] in first
    assert dream not in first and wound not in first
    her["times_met"] = 2
    later = romance._persona(her, player)
    assert dream in later and wound in later


def test_persona_knows_what_shes_already_told_you(player):
    random.seed(9)
    her = romance.new_member()
    her["discussed"] = [["vice", her["vice"]]]
    assert data.DATE_VICES[her["vice"]]["recall"] in romance._persona(her, player)


# -- small talk and temperament ------------------------------------------

@pytest.mark.parametrize("temperament, times_met, points", [
    ("warm", 0, 0), ("intense", 0, -1), ("intense", 3, -1), ("guarded", 0, 1), ("guarded", 1, 0),
])
def test_small_talk_depends_on_her_temperament(monkeypatch, temperament, times_met, points):
    monkeypatch.setattr(data, "DATE_TEMPERAMENTS", REAL_TEMPERAMENTS)
    her = romance.new_member()
    her.update(temperament=temperament, times_met=times_met)
    assert romance.small_talk(her) == points


def test_small_talk_bores_an_intense_woman_all_night(player, steer, monkeypatch):
    monkeypatch.setattr(data, "DATE_TEMPERAMENTS", REAL_TEMPERAMENTS)
    her = romance.new_member()
    her["temperament"] = "intense"
    steer(*["neutral"] * 5, accept=None)
    net, walked_out, history = romance.chat(player, her)
    assert (net, walked_out, len(history)) == (-3, True, 3)


# -- follow-ups ----------------------------------------------------------

@pytest.fixture
def followups(monkeypatch):
    monkeypatch.setattr(data, "DATE_CALLBACK_CHANCE", 1.0)


def test_no_follow_up_on_the_first_night(player, followups):
    her = romance.new_member()
    assert all(kind != "callback" for kind, _ in romance.plan_topics(her, player))


def test_follow_up_tests_your_memory(player, followups):
    random.seed(10)
    her = romance.new_member()
    her.update(times_met=1, discussed=[["vice", her["vice"]], ["value", her["value"]]])
    plan = romance.plan_topics(her, player)
    (callback,) = [t for t in plan if t[0] == "callback"]
    kind, right, wrong = callback[1]
    assert (kind, right) == ("vice", her["vice"])     # values aren't quoted back; vices are
    assert wrong != right and wrong in data.DATE_VICES
    stock = romance.stock_round(her, player, callback)
    assert data.DATE_VICES[right]["recall"] in stock["good"]
    assert data.DATE_VICES[wrong]["recall"] in stock["bad"]
    # Same sentence either way: only the detail tells them apart.
    assert stock["good"].replace(data.DATE_VICES[right]["recall"], "X") == \
           stock["bad"].replace(data.DATE_VICES[wrong]["recall"], "X")


def test_follow_up_scores_like_any_round(player, followups, steer):
    random.seed(11)
    her = romance.new_member()
    her.update(times_met=1, last_outcome=2, discussed=[["interest", her["interests"][0]]])
    steer(*["good"] * 5, accept=None)
    net, _, _ = romance.chat(player, her)
    assert net == 5
    assert ["interest", her["interests"][0]] in her["discussed"]
    assert all(t[0] != "callback" for t in her["discussed"])


# -- she asks about you ---------------------------------------------------

@pytest.fixture
def asking(monkeypatch):
    monkeypatch.setattr(data, "DATE_QUESTION_CHANCE", 1.0)


def test_which_questions_she_can_ask(player):
    her = romance.new_member()
    player.heat, player.cred = 0, 0
    assert romance.questions(her, player) == ["work"]
    player.cyberware = ["optics"]
    player.heat = data.DATE_TROUBLE_HEAT
    assert romance.questions(her, player) == ["work", "chrome", "trouble"]
    her["asked"] = ["work", "trouble"]
    assert romance.questions(her, player) == ["chrome"]


@pytest.mark.parametrize("job, cred, work", [
    ("netrunner", 0, "corpo"), ("courier", 50, "legit"), (None, data.DATE_RUNNER_CRED, "runner"),
    (None, 0, "broke"),
])
def test_your_work_as_she_sees_it(player, job, cred, work):
    player.job_id, player.cred = job, cred
    assert romance.your_work(player) == work


@pytest.mark.parametrize("corps, job, lands", [
    ("climber", "netrunner", True), ("climber", None, False),
    ("saboteur", "netrunner", False), ("saboteur", None, True),
    ("drifter", "netrunner", True), ("drifter", None, True),
])
def test_the_truth_about_your_work_depends_on_her(player, corps, job, lands):
    her = romance.new_member()
    her["corps"] = corps
    player.job_id, player.cred = job, 0
    assert romance.truth_lands(her, player, "work") is lands
    assert romance.score(her, player, ("question", "work"), "truth") == (1 if lands else -1)
    assert romance.score(her, player, ("question", "work"), "lie") == 1


def test_the_truth_about_your_chrome_and_trouble(player):
    her = romance.new_member()
    her.update(chrome="wary", value="loyalty")
    assert not romance.truth_lands(her, player, "chrome")
    assert not romance.truth_lands(her, player, "trouble")
    her.update(chrome="loves", value="thrill")
    assert romance.truth_lands(her, player, "chrome") and romance.truth_lands(her, player, "trouble")


def test_the_truth_uses_your_real_job(player):
    player.job_id = "courier"
    her = romance.new_member()
    stock = romance.stock_round(her, player, ("question", "work"))
    assert data.job_by_id("courier")["desc"] in stock["truth"]
    player.cyberware = ["optics"]
    stock = romance.stock_round(her, player, ("question", "chrome"))
    assert "Kiroshi Optics" in stock["truth"]


def test_a_lie_is_remembered_and_can_be_caught(player, asking, steer, force_roll, capsys):
    her = romance.new_member()
    her.update(corps="saboteur", value="freedom")
    player.job_id = "netrunner"                        # the truth wouldn't land with her
    steer("lie", *["neutral"] * 4, accept=None)
    net, _, _ = romance.chat(player, her)
    assert net == 1
    assert her["asked"] == ["work"] and her["lies"] == ["work"]
    assert "work" not in romance.questions(her, player)     # she won't ask twice
    before = her["affection"]
    force_roll(0.0)
    romance.catch_lies(her)
    assert her["lies"] == [] and her["affection"] == before - data.DATE_LIE_COST
    assert "really do for a living" in capsys.readouterr().out


def test_lying_to_someone_who_values_honesty_costs_double(player, force_roll):
    her = romance.new_member()
    her.update(value="honesty", lies=["chrome"])
    force_roll(0.0)
    romance.catch_lies(her)
    assert her["affection"] == -2 * data.DATE_LIE_COST


def test_uncaught_lies_stay_hidden(player, force_roll):
    her = romance.new_member()
    her["lies"] = ["work"]
    force_roll(0.99)
    romance.catch_lies(her)
    assert her["lies"] == ["work"] and her["affection"] == 0


def test_a_dodge_can_be_asked_again(player, asking, steer):
    her = romance.new_member()
    steer("dodge", *["neutral"] * 4, accept=None)
    net, _, _ = romance.chat(player, her)
    assert net == 0 and her["asked"] == [] and her["lies"] == []


def test_lies_come_out_when_you_meet_again(player, steer, her, force_roll):
    her.update(stage="met", times_met=1, last_outcome=2, lies=["work"])
    force_roll(0.0)
    steer(*["neutral"] * 5)
    romance.encounter(player)
    assert her["lies"] == [] and her["affection"] == -data.DATE_LIE_COST


def test_a_partner_can_catch_a_lie_at_night(player, dating, force_roll):
    dating["lies"] = ["trouble"]
    before = dating["affection"]
    force_roll(0.0)
    romance.night(player)
    assert dating["lies"] == [] and dating["affection"] == before - data.DATE_LIE_COST


def test_stock_scene_hides_her_personality():
    random.seed(8)
    for _ in range(100):
        her = romance.new_member()
        text = romance.scene(her, "by the jukebox").lower()
        secrets = [data.DATE_TEMPERAMENTS[her["temperament"]]["desc"],
                   data.DATE_VALUES[her["value"]]["desc"], data.DATE_PEEVES[her["peeve"]]["desc"],
                   her["name"]] + [data.DATE_INTERESTS[i]["label"] for i in her["interests"]]
        for secret in secrets:
            assert not re.search(rf"\b{re.escape(secret.lower())}\b", text), secret
        assert her["hair"] in text or her["hair"].lower() in text
        assert "by the jukebox" in text and "{" not in text


# -- the conversation ----------------------------------------------------

@pytest.mark.parametrize("kinds, net", [
    (["good"] * 5, 5),
    (["good"] * 4 + ["neutral"], 4),
    (["good", "good", "neutral", "bad", "good"], 2),
    (["neutral"] * 5, 0),
    (["bad", "good", "good", "good", "good"], 3),
    (["bad", "bad", "good", "good", "neutral"], 0),    # the playtest date that recovered
    (["bad", "bad", "neutral", "neutral", "neutral"], -2),
])
def test_net_score_is_good_minus_bad(player, steer, kinds, net):
    steer(*kinds, accept=None)
    got, walked_out, history = romance.chat(player, romance.new_member())
    assert (got, walked_out, len(history)) == (net, False, 5)


def test_she_walks_out_after_too_many_misses(player, steer):
    steer("bad", "bad", "bad", "good", "good", accept=None)
    net, walked_out, history = romance.chat(player, romance.new_member())
    assert (net, walked_out, len(history)) == (-3, True, 3)
    assert len(steer.keys) == 3      # the last two rounds never came up


def test_three_misses_in_the_last_round_is_not_a_walkout(player, steer):
    steer("neutral", "neutral", "bad", "bad", "bad", accept=None)
    net, walked_out, history = romance.chat(player, romance.new_member())
    assert (net, walked_out, len(history)) == (-3, False, 5)


def test_the_good_reply_moves_around(player, steer):
    for seed in range(10):
        random.seed(seed)
        steer(*["good"] * 5, accept=None)
        romance.chat(player, romance.new_member())
    assert set(steer.keys) == {"1", "2", "3"}


@pytest.mark.parametrize("net, walked_out, ready, tier", [
    (-5, False, False, 0), (-2, False, False, 0), (-3, True, False, 0), (-3, True, True, 0),
    (-1, False, False, 1), (0, False, False, 1),
    (1, False, False, 2),
    (2, False, False, 3), (3, False, False, 3),
    (4, False, False, 4),
    (5, False, False, 4),     # one perfect night tops out at the kiss
    (2, False, True, 3),      # ready, but tonight wasn't good enough
    (3, False, True, 5), (5, False, True, 5),
])
def test_net_score_picks_the_ending(net, walked_out, ready, tier):
    assert romance.outcome(net, walked_out, ready) is data.DATE_OUTCOMES[tier]


@pytest.mark.parametrize("kinds, tier", [
    (["bad", "bad", "bad"], 0),
    (["bad", "bad", "good", "good", "neutral"], 1),
    (["good", "neutral", "neutral", "neutral", "neutral"], 2),
    (["good", "good", "good", "neutral", "neutral"], 3),
    (["good", "good", "good", "good", "neutral"], 4),
    (["good"] * 5, 5),
])
def test_every_ending_plays_out(player, steer, her, kinds, tier, capsys):
    her.update(stage="met", times_met=data.DATE_MIN_MEETINGS - 1, last_outcome=3,
               affection=data.DATE_PARTNER_AFFECTION - 5)       # ready if tonight is perfect
    steer(*kinds)
    player.stress = 50
    change = romance.encounter(player)
    ending = data.DATE_OUTCOMES[tier]
    assert change == ending["stress"]
    assert player.stress == 50 + ending["stress"]
    assert ending["narration"] in capsys.readouterr().out
    assert (player.partner is not None) == (tier == len(data.DATE_OUTCOMES) - 1)


def test_one_perfect_night_is_not_enough(player, steer, her):
    steer(*["good"] * 5)
    romance.encounter(player)
    assert player.partner is None
    assert her["last_outcome"] == 4 and her["affection"] == 5 and her["times_met"] == 1


def test_perfect_nights_add_up_to_a_partner(player, steer, her, monkeypatch):
    """Two perfect nights reach the affection bar but not the meeting count; the third does."""
    for night in range(1, data.DATE_MIN_MEETINGS + 1):
        player.day = 10 * night
        steer(*["good"] * 5)
        romance.encounter(player)
        assert her["times_met"] == night and her["affection"] == 5 * night
        assert (player.partner is her) == (night == data.DATE_MIN_MEETINGS)
    assert her["stage"] == "dating" and her["since_day"] == 30 and her["last_seen_day"] == 30


def test_affection_accumulates_up_and_down(player, steer, her):
    steer("good", "good", "neutral", "neutral", "neutral")
    romance.encounter(player)
    steer("bad", "neutral", "neutral", "neutral", "neutral")
    romance.encounter(player)
    assert her["affection"] == 1 and her["times_met"] == 2


def test_no_encounters_while_you_have_a_partner(player, dating, monkeypatch):
    monkeypatch.setattr(data, "ENCOUNTER_CHANCE", 1.0)
    assert romance.encounter(player) is None


def test_declining_is_free(player, steer, her):
    steer(accept=False)
    player.stress = 30
    assert romance.encounter(player) == 0
    assert player.stress == 30 and player.partner is None
    assert her["times_met"] == 0 and her["stage"] == "stranger"


# -- the cast ------------------------------------------------------------

def test_a_cast_has_distinct_names():
    from cyberlife.player import Player
    random.seed(1)
    p = Player(name="Kai", handle="Ghost", background="Street Kid")
    romance.ensure_cast(p)
    assert len({c["name"] for c in p.cast}) == len(p.cast) == data.CAST_SIZE


def test_encounters_only_pick_one_or_two_cast_members(player, monkeypatch):
    monkeypatch.setattr(data, "ENCOUNTER_CHANCE", 1.0)
    romance.ensure_cast(player)
    seen = set()
    for _ in range(200):
        here = romance.present(player)
        assert 1 <= len(here) <= 2 and len({id(h) for h in here}) == len(here)
        assert all(any(h is c for c in player.cast) for h in here)
        seen.add(len(here))
    assert seen == {1, 2}


def test_who_is_never_at_the_bar(player):
    romance.ensure_cast(player)
    player.day = 10
    avoiding, ex, partner, *rest = player.cast
    avoiding.update(stage="met", avoid_until=11)
    ex["stage"] = "gone"
    partner["stage"] = "dating"
    for _ in range(100):
        here = romance.present(player)
        assert not any(h is avoiding or h is ex or h is partner for h in here)
    player.day = 11
    assert any(h is avoiding for _ in range(100) for h in romance.present(player))


def test_approaching_one_leaves_the_other_alone(player, monkeypatch, answers, force_roll):
    monkeypatch.setattr(data, "DATE_AT_BAR", (2,))
    romance.ensure_cast(player)
    force_roll(0.0)
    answers("2", *["1"] * data.DATE_ROUNDS)
    picked = []
    real = romance.chat
    monkeypatch.setattr(romance, "chat", lambda p, h: picked.append(h) or real(p, h))
    romance.encounter(player)
    assert len(picked) == 1
    met = [c for c in player.cast if c["times_met"]]
    assert met == picked
    assert all(c["stage"] == "stranger" and c["affection"] == 0
               for c in player.cast if c is not picked[0])


def test_neither_is_free(player, monkeypatch, answers, force_roll):
    monkeypatch.setattr(data, "DATE_AT_BAR", (2,))
    romance.ensure_cast(player)
    force_roll(0.0)
    answers("3")
    assert romance.encounter(player) == 0
    assert all(c["times_met"] == 0 for c in player.cast)


def test_someone_you_met_is_not_reintroduced(player, steer, her, capsys):
    stub = Stub("Scene.", *[round_json(n) for n in range(5)], "Bye.")
    llm.use(stub)
    steer(*["neutral"] * 5)
    romance.encounter(player)
    first = capsys.readouterr().out
    assert "trade names" in first and "Scene." in first
    steer(*["neutral"] * 5)
    romance.encounter(player)
    second = capsys.readouterr().out
    assert "trade names" not in second and "Scene." not in second
    assert data.DATE_OUTCOMES[1]["again"] in second       # how last time ended shows
    system = stub.calls[-1][0]["content"]
    assert "once before" in system and data.DATE_OUTCOMES[1]["memory"] in system
    assert "stranger just took the stool" not in system


def test_a_walkout_keeps_her_away_for_a_while(player, steer, her):
    player.day = 4
    steer("bad", "bad", "bad")
    romance.encounter(player)
    assert her["avoid_until"] == 4 + data.DATE_AVOID_DAYS
    assert romance.encounter(player) is None                 # nobody else in a one-woman cast
    player.day = 4 + data.DATE_AVOID_DAYS
    assert romance.present(player) == [her]


def test_a_decent_night_doesnt_keep_her_away(player, steer, her):
    steer("bad", "neutral", "neutral", "neutral", "neutral")
    romance.encounter(player)
    assert her["avoid_until"] == 0


# -- the bar -------------------------------------------------------------

def test_bar_encounter_replaces_the_side_events(player, answers, force_roll, always):
    force_roll(0.0)          # encounter fires; stranger would too if the bar got that far
    answers("n")
    charm = player.skills["charm"]
    assert actions.bar(player)
    assert player.skills["charm"] == charm


def test_bar_without_encounter_is_unchanged(player, force_roll):
    force_roll(0.99)
    assert actions.bar(player)
    assert player.partner is None


# -- the dialog model ----------------------------------------------------

def test_model_voices_every_beat(player, steer, always, capsys):
    stub = Stub("You see her at the bar, all neon and rain.",
                *[round_json(n) for n in range(5)], "Walk me home.")
    llm.use(stub)
    steer(*["good"] * 5)
    romance.encounter(player)
    out = capsys.readouterr().out
    assert "You see her at the bar, all neon and rain." in out
    for n in range(5):
        assert f"Model line {n}." in out and f"Good reply {n}." in out
    assert "Walk me home." in out
    assert len(stub.calls) == 7
    assert player.cast[0]["affection"] == 5      # the model's words don't change the score


def test_model_gets_the_trait_rules_and_the_transcript(player, steer, always):
    stub = Stub("Scene.", *[round_json(n) for n in range(5)], "Bye.")
    llm.use(stub)
    steer("good", "bad", "neutral", "good", "good")
    romance.encounter(player)
    first_round, second_round, third_round = stub.calls[1:4]
    system = first_round[0]["content"]
    assert "You can't stand" in system and "Your manner" in system
    assert f"they go by {player.handle}" in system and player.name not in system
    assert "Stranger: Good reply 0." in second_round[1]["content"]
    assert "won you over" in second_round[1]["content"]
    assert "Stranger: Bad reply 1." in third_round[1]["content"]
    assert "put you off" in third_round[1]["content"]


@pytest.mark.parametrize("reply", [
    "not json at all",
    '{"line": "Hi.", "good": "A.", "bad": "B."}',                          # missing a reply
    '{"line": "Hi.", "good": "Same.", "bad": "same.", "neutral": "C."}',   # indistinguishable
    '{"line": "", "good": "A.", "bad": "B.", "neutral": "C."}',
    '["line", "good"]',
    TimeoutError("slow"),
])
def test_unusable_rounds_fall_back_to_stock(player, reply):
    llm.use(Stub(reply))
    random.seed(4)
    her = romance.new_member()
    topic = romance.plan_topics(her, player)[0]
    assert romance.voice_round(her, player, topic, [], None) is None


def test_json_wrapped_in_chatter_is_accepted(player):
    llm.use(Stub("Sure! Here you go:\n```json\n" + round_json(3) + "\n```"))
    random.seed(4)
    her = romance.new_member()
    beat = romance.voice_round(her, player, ("occupation", her["occupation"]), [], None)
    assert beat == {"line": "Model line 3.", "good": "Good reply 3.",
                    "bad": "Bad reply 3.", "neutral": "Neutral reply 3."}


def test_model_on_or_off_plays_out_the_same(player, steer, always):
    """Same seed, same input: same woman, same score, same stats with or without a model."""
    from cyberlife.player import Player

    def play(backend):
        llm.use(backend)
        random.seed(99)
        p = Player(name="Kai", handle="Ghost", background="Street Kid", credits=1000)
        steer("good", "neutral", "good", "good", "good")
        actions.bar(p)
        return p

    canned = play(llm.CannedBackend())
    voiced = play(Stub("Scene.", *[round_json(n) for n in range(5)], "Bye."))
    assert (canned.stress, canned.credits, canned.cred, canned.cast) == \
           (voiced.stress, voiced.credits, voiced.cred, voiced.cast)


def test_dead_backend_gives_up_and_the_date_goes_on(player, steer, always, capsys):
    llm.use(Stub(TimeoutError("no route")))
    steer(*["good"] * 5)
    romance.encounter(player)
    assert "isn't answering" in capsys.readouterr().out
    assert isinstance(llm.backend, llm.CannedBackend)
    assert player.cast[0]["affection"] == 5


# -- saving --------------------------------------------------------------

def test_cast_survives_save_and_load(player, steer, her):
    steer(*["good"] * 5)
    romance.encounter(player)
    save.write(player, 1)
    assert save.read(1).cast == player.cast


def _write_v1(player, partner):
    """A save from before the cast existed: `partner` field, no `cast`."""
    import dataclasses
    fields = dataclasses.asdict(player)
    del fields["cast"]
    fields["partner"] = partner
    path = save.slot_path(1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": 1, "saved_at": 0, "player": fields}))


def test_old_partner_migrates_into_the_cast(player):
    random.seed(2)
    old = {**romance.generate(), "since_day": 7}
    player.day = 20
    _write_v1(player, old)
    loaded = save.read(1)
    assert len(loaded.cast) == data.CAST_SIZE
    partner = loaded.partner
    assert partner["name"] == old["name"] and partner["occupation"] == old["occupation"]
    assert partner["stage"] == "dating" and partner["since_day"] == 7
    assert partner["last_seen_day"] == 20              # no neglect penalty for upgrading
    assert partner["times_met"] >= data.DATE_MIN_MEETINGS
    assert len({c["name"] for c in loaded.cast}) == data.CAST_SIZE


@pytest.mark.parametrize("stored", [None, "Mira", {"age": 24}, {"name": 7},
                                    {"name": "Mira", "occupation": "astronaut"}])
def test_bad_or_missing_old_partner_loads_as_single(player, stored):
    _write_v1(player, stored)
    loaded = save.read(1)
    assert loaded.partner is None
    assert len(loaded.cast) == data.CAST_SIZE
    assert all(c["stage"] == "stranger" for c in loaded.cast)


def test_older_cast_entries_get_the_new_traits(player):
    """A woman saved before she had a dream or a family keeps who she was and gains the rest."""
    romance.ensure_cast(player)
    kept = dict(player.cast[0])
    for field in ("dream", "family", "wound", "corps", "vice", "belief", "origin",
                  "discussed", "asked", "lies"):
        del player.cast[0][field]
    save.write(player, 1)
    loaded = save.read(1).cast[0]
    assert loaded["name"] == kept["name"] and loaded["occupation"] == kept["occupation"]
    assert loaded["dream"] in data.DATE_DREAMS and loaded["wound"] in data.DATE_WOUNDS
    assert loaded["discussed"] == [] and loaded["lies"] == []


def test_forgotten_topics_and_questions_are_dropped_on_load(player):
    romance.ensure_cast(player)
    her = player.cast[0]
    her["discussed"] = [["vice", her["vice"]], ["vice", "gone-from-the-game"], "junk"]
    her["lies"] = ["work", "gone"]
    save.write(player, 1)
    loaded = save.read(1).cast[0]
    assert loaded["discussed"] == [["vice", her["vice"]]] and loaded["lies"] == ["work"]


def test_damaged_cast_entries_are_replaced(player):
    romance.ensure_cast(player)
    player.cast[1]["peeve"] = "no-longer-in-the-game"
    player.cast[2] = "junk"
    del player.cast[3]["avoid_until"]                  # older entry, missing a field
    save.write(player, 1)
    loaded = save.read(1)
    assert len(loaded.cast) == data.CAST_SIZE
    assert loaded.cast[0] == player.cast[0]
    assert loaded.cast[1]["avoid_until"] == 0          # the one missing a field, filled in


def test_only_one_partner_survives_a_load(player):
    romance.ensure_cast(player)
    player.cast[0]["stage"] = "dating"
    player.cast[1]["stage"] = "serious"
    save.write(player, 1)
    loaded = save.read(1)
    assert [c["stage"] for c in loaded.cast[:2]] == ["dating", "met"]


# -- together ------------------------------------------------------------

def test_neglect_costs_affection_and_seeing_her_doesnt(player, dating):
    before = dating["affection"]
    player.day = dating["last_seen_day"] + data.REL_NEGLECT_DAYS - 1
    romance.night(player)
    assert dating["affection"] == before
    player.day += 1
    romance.night(player)
    assert dating["affection"] == before - 1


@pytest.mark.parametrize("heat, humanity, worried", [
    (0, 100, False), (data.REL_WORRY_HEAT, 100, True), (0, data.REL_WORRY_HUMANITY - 1, True),
])
def test_heat_and_chrome_worry_her(player, dating, heat, humanity, worried):
    player.heat, player.humanity = heat, humanity
    before = dating["affection"]
    romance.night(player)
    assert dating["affection"] == before - (data.REL_WORRY_COST if worried else 0)


def test_she_leaves_when_affection_runs_out(player, dating, capsys):
    player.stress = 30
    dating["affection"] = data.REL_LEAVE_AFFECTION
    player.heat = data.REL_WORRY_HEAT
    romance.night(player)
    assert dating["stage"] == "gone" and player.partner is None
    assert player.stress == 30 + data.REL_LEAVE_STRESS
    assert data.REL_LEAVES.format(name=dating["name"]) in capsys.readouterr().out
    assert all(h is not dating for _ in range(50) for h in romance.present(player))


def test_she_moves_in_with_enough_affection_and_time(player, dating):
    dating["affection"] = data.REL_SERIOUS_AFFECTION
    player.day = dating["since_day"] + data.REL_SERIOUS_DAYS - 1
    dating["last_seen_day"] = player.day
    romance.night(player)
    assert dating["stage"] == "dating"                  # not long enough yet
    player.day += 1
    dating["last_seen_day"] = player.day
    romance.night(player)
    assert dating["stage"] == "serious"
    assert player.rent_due == player.rent // 2


def test_a_partner_knows_your_real_name(player, dating):
    messages = romance.together_messages(dating, player, "a walk", "Nice.")
    assert player.name in messages[0]["content"] and "together" in messages[0]["content"]


def test_she_knows_your_handle_and_your_job(player, steer, always):
    """Playtest: without the handle the model invented a name ("Name's Kestrel")."""
    stub = Stub("Scene.", *[round_json(n) for n in range(5)], "Bye.")
    llm.use(stub)
    player.job_id = "netrunner"
    steer(*["good"] * 5)
    romance.encounter(player)
    for messages in stub.calls[1:]:
        system = messages[0]["content"]
        assert f"uses {player.handle}" in system
        assert "junior netrunner at Tessier, a corporation" in system
        assert "Junior netrunner, Tessier" not in system


def test_model_voices_a_question_with_its_own_replies(player):
    llm.use(Stub(json.dumps({"line": "So what do you do?", "truth": "I run gigs.",
                             "lie": "Logistics.", "dodge": "Long story."})))
    player.job_id = None
    her = romance.new_member()
    topic = ("question", "work")
    messages = romance.round_messages(her, player, topic, [], None)
    prompt = messages[1]["content"]
    assert '"truth"' in prompt and '"lie"' in prompt and '"dodge"' in prompt
    assert '"good"' not in prompt
    beat = romance.voice_round(her, player, topic, [], None)
    assert beat == {"line": "So what do you do?", "truth": "I run gigs.", "lie": "Logistics.",
                    "dodge": "Long story."}


def test_model_follow_up_brief_names_the_right_and_wrong_memory(player):
    her = romance.new_member()
    topic = ("callback", ("vice", "karaoke", "gambling"))
    prompt = romance.round_messages(her, player, topic, [], None)[1]["content"]
    assert data.DATE_VICES["karaoke"]["recall"] in prompt
    assert data.DATE_VICES["gambling"]["recall"] in prompt


def test_peeve_rounds_brief_the_good_reply(player):
    random.seed(1)
    her = romance.new_member()
    messages = romance.round_messages(her, player, ("peeve", "prying"), [], None)
    assert data.DATE_PEEVES["prying"]["good_desc"] in messages[1]["content"]
