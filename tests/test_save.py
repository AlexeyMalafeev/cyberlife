import dataclasses
import json

import pytest

from cyberlife import data, romance, save
from cyberlife.player import Player


def _rich_player():
    p = Player(name="Kai", handle="Ghost", background="Netrunner", day=12, credits=2431)
    p.skills = {"hacking": 5, "muscle": 2, "charm": 3}
    p.cyberware = ["optics", "coproc"]
    p.job_id = "dataentry"
    p.cred, p.heat, p.stress, p.humanity, p.health = 14, 2, 41, 63, 77
    p.rent, p.missed_rent, p.energy, p.energy_penalty = 650, 1, 2, 1
    romance.ensure_cast(p)
    romance.start_relationship(p, p.cast[2])
    p.cast[0].update(stage="met", times_met=2, affection=4, last_outcome=3, avoid_until=14)
    return p


def test_round_trip_preserves_every_field():
    original = _rich_player()
    save.write(original, 1)
    loaded = save.read(1)
    before = dataclasses.asdict(original)
    after = dataclasses.asdict(loaded)
    assert after == before


def test_round_trip_preserves_derived_state():
    save.write(_rich_player(), 1)
    loaded = save.read(1)
    assert loaded.job["name"] == "Data-entry drone, Kiroshi"
    assert loaded.skill("hacking") == 5 + 1 + 3   # +optics +coproc
    assert loaded.max_energy == 3


def test_write_sets_slot_and_is_atomic(isolated_saves):
    p = _rich_player()
    save.write(p, 3)
    assert p.save_slot == 3
    assert save.slot_path(3).exists()
    assert not list(isolated_saves.glob("*.tmp"))


def test_slots_are_independent():
    a = Player(name="A", handle="Alpha", background="Street Kid", credits=100)
    b = Player(name="B", handle="Beta", background="Corpo Dropout", credits=900)
    save.write(a, 1)
    save.write(b, 2)
    assert save.read(1).handle == "Alpha"
    assert save.read(2).handle == "Beta"


# -- schema drift -------------------------------------------------------

def test_missing_field_falls_back_to_default():
    save.write(_rich_player(), 1)
    payload = json.loads(save.slot_path(1).read_text())
    del payload["player"]["heat"]          # a field added after this save was written
    save.slot_path(1).write_text(json.dumps(payload))
    assert save.read(1).heat == 0


def test_unknown_field_is_ignored():
    save.write(_rich_player(), 1)
    payload = json.loads(save.slot_path(1).read_text())
    payload["player"]["karma"] = 99        # a field this build no longer has
    save.slot_path(1).write_text(json.dumps(payload))
    assert save.read(1).handle == "Ghost"


def test_removed_job_and_cyberware_are_dropped():
    p = _rich_player()
    p.job_id = "bartender_that_no_longer_exists"
    p.cyberware = ["optics", "wings"]
    save.write(p, 1)
    loaded = save.read(1)
    assert loaded.job_id is None and loaded.job is None
    assert loaded.cyberware == ["optics"]


def test_newer_version_is_refused():
    save.write(_rich_player(), 1)
    payload = json.loads(save.slot_path(1).read_text())
    payload["version"] = save.SAVE_VERSION + 1
    save.slot_path(1).write_text(json.dumps(payload))
    with pytest.raises(save.SaveError, match="newer version"):
        save.read(1)


def test_corrupt_and_empty_slots_raise_save_error():
    with pytest.raises(save.SaveError, match="empty"):
        save.read(1)
    save.slot_path(2).parent.mkdir(parents=True, exist_ok=True)
    save.slot_path(2).write_text("{not json")
    with pytest.raises(save.SaveError, match="corrupt"):
        save.read(2)


# -- slot listing -------------------------------------------------------

def test_list_describe_first_empty_and_latest():
    assert save.list_slots() == [None] * data.SAVE_SLOTS
    assert save.first_empty() == 1
    assert save.latest() is None

    save.write(_rich_player(), 2)
    slots = save.list_slots()
    info = slots[1]
    assert info["slot"] == 2 and info["handle"] == "Ghost" and info["day"] == 12
    assert info["stale"] is False
    assert save.first_empty() == 1
    assert save.latest() == 2


def test_latest_prefers_most_recent(monkeypatch):
    times = iter([100.0, 200.0])
    monkeypatch.setattr(save.time, "time", lambda: next(times))
    save.write(Player(name="a", handle="Old", background="x"), 1)
    save.write(Player(name="b", handle="New", background="x"), 4)
    assert save.latest() == 4


def test_describe_returns_none_only_for_a_missing_file():
    assert save.describe(1) is None
    assert save.list_slots()[0] is None


def test_all_slots_full_has_no_empty():
    for n in range(1, data.SAVE_SLOTS + 1):
        save.write(Player(name="n", handle=f"P{n}", background="x"), n)
    assert save.first_empty() is None


def test_delete_is_idempotent():
    save.write(_rich_player(), 1)
    save.delete(1)
    save.delete(1)
    assert save.describe(1) is None


# -- save directory resolution -----------------------------------------

def test_env_var_is_used_when_no_explicit_dir(tmp_path, monkeypatch):
    save.set_save_dir(None)
    monkeypatch.setenv("CYBERLIFE_SAVE_DIR", str(tmp_path / "env"))
    assert save.save_dir() == tmp_path / "env"
    save.set_save_dir(tmp_path / "explicit")
    assert save.save_dir() == tmp_path / "explicit"


def test_default_dir_is_under_home(monkeypatch, tmp_path):
    save.set_save_dir(None)
    monkeypatch.delenv("CYBERLIFE_SAVE_DIR", raising=False)
    monkeypatch.setattr(save.Path, "home", classmethod(lambda cls: tmp_path))
    assert save.save_dir() == tmp_path / ".cyberlife" / "saves"


# -- damaged saves occupy their slot -----------------------------------

def test_damaged_slot_is_not_reported_as_empty():
    save.write(_rich_player(), 1)
    save.slot_path(1).write_text("{ not json")
    info = save.describe(1)
    assert info is not None and info["unreadable"]
    assert save.first_empty() == 2, "a damaged save must not be handed to a new run"
    assert save.latest() is None, "a damaged save is not a continuable run"


def test_readable_slot_reports_no_error():
    save.write(_rich_player(), 1)
    assert save.describe(1)["unreadable"] is None
