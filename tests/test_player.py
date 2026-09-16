import pytest

from cyberlife import data
from cyberlife.player import Player


def test_skill_includes_cyberware_bonus(player):
    player.skills["hacking"] = 2
    assert player.skill("hacking") == 2
    player.cyberware.append("coproc")   # +3 hacking
    assert player.skill("hacking") == 5
    assert player.skills["hacking"] == 2, "raw skill must not change"


def test_max_stats_from_cyberware(player):
    assert player.max_health == 100
    assert player.max_energy == 3
    player.cyberware += ["dermal", "lungs"]
    assert player.max_health == 125
    assert player.max_energy == 4


def test_clamp_bounds(player):
    player.health = 999
    player.stress = -5
    player.humanity = 150
    player.credits = -20
    player.heat = -1
    player.clamp()
    assert player.health == player.max_health
    assert player.stress == 0
    assert player.humanity == 100
    assert player.credits == 0
    assert player.heat == 0


@pytest.mark.parametrize("field,value,cause", [
    ("health", 0, "flatlined"),
    ("humanity", 0, "cyberpsychosis"),
    ("stress", 100, "burnout"),
    ("missed_rent", data.MAX_MISSED_RENT, "evicted"),
])
def test_death_causes(player, field, value, cause):
    assert player.death_cause() is None
    setattr(player, field, value)
    assert player.death_cause() == cause


def test_death_cause_clamps_first(player):
    player.health = -40
    assert player.death_cause() == "flatlined"
    assert player.health == 0
