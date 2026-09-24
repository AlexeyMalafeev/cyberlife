from cyberlife import data
from cyberlife.player import Player

SKILLS = set(Player(name="a", handle="b", background="c").skills)


def test_cyberware_ids_unique_and_bonus_keys_valid():
    ids = [cw["id"] for cw in data.CYBERWARE]
    assert len(ids) == len(set(ids))
    for cw in data.CYBERWARE:
        for key in cw["bonus"]:
            assert key in SKILLS | {"max_health", "max_energy"}, (cw["id"], key)
        assert cw["humanity"] > 0 and cw["cost"] > 0


def test_jobs_reference_real_skills():
    for job in data.JOBS:
        if job["req"] is not None:
            skill, level = job["req"]
            assert skill in SKILLS and level >= 1


def test_gigs_well_formed():
    for g in data.GIGS:
        assert g["skill"] in SKILLS
        lo, hi = g["pay"]
        assert 0 < lo <= hi
        assert 0 < g["base"] < 1


def test_backgrounds_cover_every_skill():
    for bg in data.BACKGROUNDS.values():
        assert set(bg["skills"]) == SKILLS


def test_npcs_well_formed():
    for npc_id, npc in data.NPCS.items():
        assert npc["name"] and npc["role"] and npc["disposition"], npc_id
        assert 2 <= len(npc["facts"]) <= 3, npc_id
        assert npc["situations"], npc_id
        for key, sit in npc["situations"].items():
            assert sit["prompt"], (npc_id, key)
            assert len(sit["canned"]) >= 2, (npc_id, key)


def _weighted_tables():
    yield from data.DATE_LOOKS.items()
    for name in ("DATE_TEMPERAMENTS", "DATE_OCCUPATIONS", "DATE_INTERESTS", "DATE_VALUES",
                 "DATE_PEEVES", "DATE_CHROME"):
        table = getattr(data, name)
        yield name, [(entry["weight"], key) for key, entry in table.items()]


def test_encounter_tables_have_positive_weights():
    for name, table in _weighted_tables():
        assert table, name
        assert all(w > 0 for w, _ in table), name


def test_every_topic_has_paired_stock_lines():
    """Stock rounds pick lines[i] with good[i] and bad[i], so the lists must line up."""
    topics = [data.DATE_OCCUPATIONS, data.DATE_INTERESTS, data.DATE_VALUES, data.DATE_PEEVES,
              {k: v for k, v in data.DATE_CHROME.items() if k != "indifferent"},
              data.DATE_CORPS, data.DATE_VICES, data.DATE_BELIEFS, data.DATE_ORIGINS,
              data.DATE_DREAMS, data.DATE_FAMILIES, data.DATE_WOUNDS]
    for table in topics:
        for key, entry in table.items():
            assert entry["lines"], key
            assert len(entry["lines"]) == len(entry["good"]) == len(entry["bad"]), key
            assert entry["desc" if "desc" in entry else "label"], key
    for key, entry in data.DATE_PEEVES.items():
        assert entry["good_desc"], key


def test_encounter_sizes_and_outcomes():
    assert 0 < data.ENCOUNTER_CHANCE < 1
    assert len(data.DATE_INTERESTS) >= 2         # she always has two different ones
    *tiers, top = data.DATE_OUTCOMES
    floors = [o["min_net"] for o in tiers]
    assert floors == sorted(set(floors))                  # one tier per threshold, worst first
    assert floors[0] == -data.DATE_ROUNDS                 # every score lands somewhere
    assert top["partner"] and not any(o.get("partner") for o in tiers)
    assert 0 < top["min_net"] <= data.DATE_ROUNDS
    # Enough topics for a full conversation even when she doesn't care about chrome.
    assert 1 + 2 + 1 + 1 >= data.DATE_ROUNDS
    assert data.DATE_MIN_MEETINGS >= 2                    # one night is never enough
    assert data.DATE_PARTNER_AFFECTION > data.DATE_ROUNDS
    assert data.CAST_SIZE <= len(data.DATE_NAMES)
    assert max(data.DATE_AT_BAR) <= len(data.BAR_SPOTS)
    for outcome in data.DATE_OUTCOMES:
        assert outcome["memory"] and outcome["again"]
    assert -data.DATE_ROUNDS < data.DATE_WALKOUT < 0
    for outcome in data.DATE_OUTCOMES:
        assert outcome["canned"] and outcome["prompt"] and outcome["narration"]
    stresses = [o["stress"] for o in data.DATE_OUTCOMES]
    assert stresses == sorted(stresses, reverse=True)     # better dates never feel worse
    assert set(data.DATE_REACTIONS) == {"good", "bad", "neutral"}
    assert len(set(data.DATE_NAMES)) == len(data.DATE_NAMES)


def test_stock_scenes_fill_from_looks_and_hint():
    looks = {part: options[0][1] for part, options in data.DATE_LOOKS.items()}
    for template in data.DATE_SCENES:
        text = template.format(hint="HINT", spot="SPOT", **looks)
        assert "HINT" in text and "SPOT" in text and "{" not in text
    for template in data.DATE_AGAIN:
        text = template.format(name="NAME", spot="SPOT", mood="MOOD", **looks)
        assert "NAME" in text and "MOOD" in text and "{" not in text


def test_relationship_tables():
    for entry in data.DATE_INTERESTS.values():
        assert entry["outing"]
    assert data.REL_LEAVE_AFFECTION < data.DATE_PARTNER_AFFECTION < data.REL_SERIOUS_AFFECTION
    for fx in (data.REL_OUTING, data.REL_STAY_IN):
        assert fx["stress"] < 0 and fx["humanity"] > 0 and fx["affection"] > 0
    assert data.VISA_FOR_TWO > data.VISA_COST
    endings = {"flatlined", "cyberpsychosis", "burnout", "evicted", "visa", "legend"}
    assert set(data.REL_ENDINGS) == endings | {"visa_together"}
    for text in [*data.REL_ENDINGS.values(), *data.REL_NEGLECTED, *data.REL_WORRIED,
                 data.REL_LEAVES, data.REL_MOVES_IN]:
        assert "NAME" in text.format(name="NAME")


def test_jobs_have_a_prompt_description():
    for job in data.JOBS:
        assert job["desc"] and job["desc"] != job["name"], job["id"]


def test_deeper_trait_tables():
    from cyberlife import romance
    assert set(data.DATE_TOPIC_DEPTH) <= set(romance.TRAITS)
    # Follow-ups quote these back, and need at least one wrong answer to offer.
    for table in (data.DATE_OCCUPATIONS, data.DATE_VICES, data.DATE_BELIEFS, data.DATE_ORIGINS,
                  data.DATE_DREAMS, data.DATE_FAMILIES):
        assert len(table) >= 3
        for key, entry in table.items():
            assert entry["recall"], key
    for key, entry in data.DATE_OCCUPATIONS.items():
        for kind, lean in entry.get("leans", {}).items():
            assert lean in romance.TRAITS[kind][1], key
    for entry in data.DATE_CORPS.values():
        assert set(entry["likes_work"]) <= {"corpo", "legit", "runner", "broke"}
    assert all(isinstance(v["likes_trouble"], bool) for v in data.DATE_VALUES.values())
    assert all(isinstance(v["likes_truth"], bool) for v in data.DATE_CHROME.values())
    for t in data.DATE_TEMPERAMENTS.values():
        assert t.get("neutral", 0) in (-1, 0, 1) and t.get("neutral_first", 0) in (-1, 0, 1)
    assert 0 < data.DATE_LEAN_CHANCE < 1
    assert any(job.get("corp") for job in data.JOBS)


def test_callback_and_question_tables():
    for reply in data.DATE_CALLBACK["replies"]:
        assert "THING" in reply.format(thing="THING") and not reply.startswith("{")
    assert data.DATE_CALLBACK["lines"] and data.DATE_DODGE
    assert set(data.DATE_QUESTIONS) == {"work", "chrome", "trouble"}
    for qid, q in data.DATE_QUESTIONS.items():
        assert q["lines"] and q["lie"] and q["about"] and q["lie_brief"], qid
        assert "NAME" in q["caught"].format(name="NAME"), qid
    work = data.DATE_QUESTIONS["work"]
    assert set(work["truth"]) == set(work["truth_brief"]) == {"corpo", "legit", "runner", "broke"}
    for n in (data.DATE_CALLBACK_CHANCE, data.DATE_QUESTION_CHANCE, data.DATE_LIE_CAUGHT):
        assert 0 < n <= 1
