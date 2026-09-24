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


@pytest.fixture
def always(monkeypatch):
    monkeypatch.setattr(data, "ENCOUNTER_CHANCE", 1.0)


@pytest.fixture
def steer(monkeypatch):
    """Answer each round's menu with the reply of the kind scripted, whatever order it's shown in.

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
            if tuple(population) == romance.KINDS and plan:
                key = str(order.index(plan.pop(0)) + 1)
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


def test_topics_open_with_her_work_and_fill_every_round():
    random.seed(2)
    for _ in range(100):
        her = romance.generate()
        topics = romance.plan_topics(her)
        assert len(topics) == data.DATE_ROUNDS
        assert topics[0] == ("occupation", her["occupation"])
        assert len(set(topics)) == len(topics)
        assert ("chrome", "indifferent") not in topics


def test_stock_scene_hides_her_personality():
    random.seed(8)
    for _ in range(100):
        her = romance.generate()
        text = romance.scene(her).lower()
        secrets = [data.DATE_TEMPERAMENTS[her["temperament"]]["desc"],
                   data.DATE_VALUES[her["value"]]["desc"], data.DATE_PEEVES[her["peeve"]]["desc"],
                   her["name"]] + [data.DATE_INTERESTS[i]["label"] for i in her["interests"]]
        for secret in secrets:
            assert not re.search(rf"\b{re.escape(secret.lower())}\b", text), secret
        assert her["hair"] in text or her["hair"].lower() in text
        assert "{" not in text


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
    her = romance.generate()
    got, walked_out, history = romance.chat(player, her)
    assert (got, walked_out, len(history)) == (net, False, 5)


def test_she_walks_out_after_too_many_misses(player, steer):
    steer("bad", "bad", "bad", "good", "good", accept=None)
    her = romance.generate()
    net, walked_out, history = romance.chat(player, her)
    assert (net, walked_out, len(history)) == (-3, True, 3)
    assert len(steer.keys) == 3      # the last two rounds never came up


def test_three_misses_in_the_last_round_is_not_a_walkout(player, steer):
    steer("neutral", "neutral", "bad", "bad", "bad", accept=None)
    net, walked_out, history = romance.chat(player, romance.generate())
    assert (net, walked_out, len(history)) == (-3, False, 5)


def test_the_good_reply_moves_around(player, steer):
    for seed in range(10):
        random.seed(seed)
        steer(*["good"] * 5, accept=None)
        romance.chat(player, romance.generate())
    assert set(steer.keys) == {"1", "2", "3"}


@pytest.mark.parametrize("net, walked_out, tier", [
    (-5, False, 0), (-2, False, 0), (-3, True, 0),
    (-1, False, 1), (0, False, 1),
    (1, False, 2),
    (2, False, 3), (3, False, 3),
    (4, False, 4),
    (5, False, 5),
])
def test_net_score_picks_the_ending(net, walked_out, tier):
    assert romance.outcome(net, walked_out) is data.DATE_OUTCOMES[tier]


@pytest.mark.parametrize("kinds, tier", [
    (["bad", "bad", "bad"], 0),
    (["bad", "bad", "good", "good", "neutral"], 1),
    (["good", "neutral", "neutral", "neutral", "neutral"], 2),
    (["good", "good", "good", "neutral", "neutral"], 3),
    (["good", "good", "good", "good", "neutral"], 4),
    (["good"] * 5, 5),
])
def test_every_ending_plays_out(player, steer, always, kinds, tier, capsys):
    steer(*kinds)
    player.stress = 50
    change = romance.encounter(player)
    ending = data.DATE_OUTCOMES[tier]
    assert change == ending["stress"]
    assert player.stress == 50 + ending["stress"]
    assert ending["narration"] in capsys.readouterr().out
    assert (player.partner is not None) == (tier == len(data.DATE_OUTCOMES) - 1)


def test_perfect_date_makes_her_your_partner(player, steer, always):
    steer(*["good"] * 5)
    player.day = 12
    romance.encounter(player)
    assert player.partner["since_day"] == 12
    assert player.partner["name"] in data.DATE_NAMES
    assert player.partner["occupation"] in data.DATE_OCCUPATIONS


def test_no_encounters_while_you_have_a_partner(player, always):
    player.partner = {"name": "Mira"}
    assert romance.encounter(player) is None


def test_declining_is_free(player, steer, always):
    steer(accept=False)
    player.stress = 30
    assert romance.encounter(player) == 0
    assert player.stress == 30 and player.partner is None


# -- the bar -------------------------------------------------------------

def test_bar_encounter_replaces_the_side_events(player, answers, force_roll):
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
    assert player.partner is not None      # the model's words don't change the score


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
    her = romance.generate()
    topic = romance.plan_topics(her)[0]
    assert romance.voice_round(her, player, topic, [], None) is None


def test_json_wrapped_in_chatter_is_accepted(player):
    llm.use(Stub("Sure! Here you go:\n```json\n" + round_json(3) + "\n```"))
    random.seed(4)
    her = romance.generate()
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
    assert (canned.stress, canned.credits, canned.cred, canned.partner) == \
           (voiced.stress, voiced.credits, voiced.cred, voiced.partner)


def test_dead_backend_gives_up_and_the_date_goes_on(player, steer, always, capsys):
    llm.use(Stub(TimeoutError("no route")))
    steer(*["good"] * 5)
    romance.encounter(player)
    assert "isn't answering" in capsys.readouterr().out
    assert isinstance(llm.backend, llm.CannedBackend)
    assert player.partner is not None


# -- saving --------------------------------------------------------------

def test_partner_survives_save_and_load(player, steer, always):
    steer(*["good"] * 5)
    romance.encounter(player)
    save.write(player, 1)
    assert save.read(1).partner == player.partner


@pytest.mark.parametrize("stored", [None, "Mira", {"age": 24}, {"name": 7}])
def test_bad_or_missing_partner_loads_as_single(player, stored):
    player.partner = stored
    save.write(player, 1)
    assert save.read(1).partner is None


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


def test_peeve_rounds_brief_the_good_reply(player):
    random.seed(1)
    her = romance.generate()
    messages = romance.round_messages(her, player, ("peeve", "prying"), [], None)
    assert data.DATE_PEEVES["prying"]["good_desc"] in messages[1]["content"]
