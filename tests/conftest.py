import random

import pytest

from cyberlife import save, ui
from cyberlife.player import Player


@pytest.fixture(autouse=True)
def isolated_saves(tmp_path, monkeypatch):
    """Never let a test touch the real ~/.cyberlife. Every test gets an empty save dir."""
    monkeypatch.delenv("CYBERLIFE_SAVE_DIR", raising=False)
    save.set_save_dir(tmp_path / "saves")
    yield tmp_path / "saves"
    save.set_save_dir(None)


@pytest.fixture(autouse=True)
def no_color(monkeypatch):
    monkeypatch.setattr(ui, "USE_COLOR", False)


@pytest.fixture(autouse=True)
def line_input(monkeypatch):
    """Route every prompt through ui._read (never raw keypresses), so `answers` can script them."""
    monkeypatch.setattr(ui, "RAW_KEYS", False)


@pytest.fixture(autouse=True)
def seeded():
    random.seed(0)


@pytest.fixture
def player():
    return Player(name="Kai", handle="Ghost", background="Street Kid", credits=1000)


@pytest.fixture
def answers(monkeypatch):
    """Script the player's input. Usage: answers("1", "y") — consumed in order."""
    queue = []

    def _read(prompt=""):
        if not queue:
            raise AssertionError(f"unexpected prompt with no scripted answer: {prompt!r}")
        return queue.pop(0)

    monkeypatch.setattr(ui, "_read", _read)

    def script(*items):
        queue.extend(items)
        return queue

    return script


@pytest.fixture
def force_roll(monkeypatch):
    """Pin random.random() to a fixed value (0.0 = always succeed, 0.99 = always fail)."""
    def _set(value):
        monkeypatch.setattr(random, "random", lambda: value)
    return _set
