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
              {k: v for k, v in data.DATE_CHROME.items() if k != "indifferent"}]
    for table in topics:
        for key, entry in table.items():
            assert entry["lines"], key
            assert len(entry["lines"]) == len(entry["good"]) == len(entry["bad"]), key
            assert entry["desc" if "desc" in entry else "label"], key


def test_encounter_sizes_and_outcomes():
    assert 0 < data.ENCOUNTER_CHANCE < 1
    assert len(data.DATE_INTERESTS) >= 2         # she always has two different ones
    assert len(data.DATE_OUTCOMES) == data.DATE_ROUNDS + 1
    # Enough topics for a full conversation even when she doesn't care about chrome.
    assert 1 + 2 + 1 + 1 >= data.DATE_ROUNDS
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
        text = template.format(hint="HINT", **looks)
        assert "HINT" in text and "{" not in text
