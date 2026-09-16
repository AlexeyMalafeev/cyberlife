import contextlib
import io
import random
import re

import pytest

from cyberlife import data, game, ui
from cyberlife.player import Player


def test_night_debits_rent_on_rent_day(player, monkeypatch):
    monkeypatch.setattr(game.events, "night_event", lambda p: None)
    player.day = data.RENT_EVERY
    game.night(player)
    assert player.credits == 1000 - player.rent
    assert player.day == data.RENT_EVERY + 1
    assert player.missed_rent == 0


def test_night_missed_rent_strikes(player, monkeypatch):
    monkeypatch.setattr(game.events, "night_event", lambda p: None)
    player.credits = 0
    for n in range(1, data.MAX_MISSED_RENT + 1):
        player.day = data.RENT_EVERY * n
        game.night(player)
        assert player.missed_rent == n
    assert player.death_cause() == "evicted"


def test_night_passive_drift(player, monkeypatch):
    monkeypatch.setattr(game.events, "night_event", lambda p: None)
    player.stress, player.health, player.heat, player.day = 50, 80, 3, 2
    game.night(player)
    assert (player.stress, player.health, player.heat) == (44, 83, 2)


def test_day_loop_energy_penalty_and_end_day(player, answers):
    player.energy_penalty = 1
    answers("8")   # "End the day" (no job → no "Quit job" entry)
    game.day_loop(player)
    assert player.energy == 2
    assert player.energy_penalty == 0


def test_day_loop_spends_energy_on_actions(player, answers):
    answers("4", "4", "4")   # rest ×3
    game.day_loop(player)
    assert player.energy == 0


def test_day_loop_menu_shows_quit_job_only_with_job(player, answers):
    player.job = data.JOBS[0]
    answers("8", "8")   # quit job (free); menu renumbers, so end day is now 8
    game.day_loop(player)
    assert player.job is None
    assert player.energy == player.max_energy


@pytest.mark.parametrize("seed", range(40))
def test_random_play_always_reaches_an_ending(seed, monkeypatch):
    rng = random.Random(seed)

    def fake_read(prompt=""):
        if "[y/n]" in prompt:
            return rng.choice(["y", "n"])
        if "> " in prompt:
            return str(rng.randint(1, 9))
        return ""

    monkeypatch.setattr(ui, "_read", fake_read)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        random.seed(seed)
        game.run()
    text = out.getvalue()
    assert ("GAME OVER" in text) or ("YOU MADE IT" in text)
    assert re.search(r"Survived \d+ days", text)


def test_quit_at_any_prompt_exits_cleanly(monkeypatch, capsys):
    monkeypatch.setattr(ui, "_read", lambda prompt="": (_ for _ in ()).throw(ui.QuitGame))
    game.run()
    assert "You jack out" in capsys.readouterr().out


def test_legend_win(player, monkeypatch, capsys):
    monkeypatch.setattr(game, "create_character", lambda: player)
    monkeypatch.setattr(game, "day_loop", lambda p: None)
    player.cred = data.LEGEND_CRED
    game.run()
    assert player.won == "legend"
    assert "YOU MADE IT" in capsys.readouterr().out
