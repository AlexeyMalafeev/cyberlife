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
