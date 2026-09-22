import contextlib
import io
import random
import re

import pytest

from cyberlife import data, game, save, ui
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
    answers("9")   # "End the day" (no job → no "Quit job" entry; 8 is "Save game")
    game.day_loop(player)
    assert player.energy == 2
    assert player.energy_penalty == 0


def test_day_loop_spends_energy_on_actions(player, answers):
    answers("4", "4", "4")   # rest ×3
    game.day_loop(player)
    assert player.energy == 0


def test_day_loop_menu_shows_quit_job_only_with_job(player, answers):
    player.job_id = data.JOBS[0]["id"]
    answers("8", "9")   # quit job (free); menu loses that entry, so end day is now 9
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
    monkeypatch.setattr(game, "title_screen", lambda: player)
    monkeypatch.setattr(game, "day_loop", lambda p: None)
    player.cred = data.LEGEND_CRED
    game.run()
    assert player.won == "legend"
    assert "YOU MADE IT" in capsys.readouterr().out


# -- saving / loading integration --------------------------------------

def test_night_autosaves(player, monkeypatch):
    monkeypatch.setattr(game.events, "night_event", lambda p: None)
    player.save_slot = 2
    player.day = 3
    game.night(player)
    assert save.describe(2)["day"] == 4


def test_night_without_slot_writes_nothing(player, monkeypatch):
    monkeypatch.setattr(game.events, "night_event", lambda p: None)
    player.save_slot = None
    game.night(player)
    assert save.list_slots() == [None] * data.SAVE_SLOTS


def test_autosave_failure_does_not_crash_the_run(player, monkeypatch, capsys):
    player.save_slot = 1
    monkeypatch.setattr(save, "write", lambda p, s: (_ for _ in ()).throw(OSError("disk full")))
    game.autosave(player)
    assert "Autosave failed" in capsys.readouterr().out


def test_finish_retires_the_slot(player, capsys):
    save.write(player, 1)
    game.finish(player, "flatlined")
    assert save.describe(1) is None
    assert player.save_slot is None
    assert "GAME OVER" in capsys.readouterr().out


def test_quit_saves_progress(player, monkeypatch, capsys):
    monkeypatch.setattr(game, "title_screen", lambda: player)
    player.save_slot = 3
    player.day = 9
    monkeypatch.setattr(game, "day_loop", lambda p: (_ for _ in ()).throw(ui.QuitGame))
    game.run()
    out = capsys.readouterr().out
    assert "Run saved to slot 3" in out
    assert save.describe(3)["day"] == 9


def test_quit_at_title_screen_saves_nothing(monkeypatch, capsys):
    monkeypatch.setattr(ui, "_read", lambda prompt="": (_ for _ in ()).throw(ui.QuitGame))
    game.run()
    assert "jack out" in capsys.readouterr().out
    assert save.list_slots() == [None] * data.SAVE_SLOTS


def test_title_screen_with_no_saves_creates_a_character(monkeypatch):
    made = Player(name="new", handle="New", background="Street Kid")
    monkeypatch.setattr(game, "create_character", lambda: made)
    assert game.title_screen() is made


def test_title_screen_continue_loads_latest(player, answers):
    player.day = 17
    player.handle = "Wraith"
    save.write(player, 2)
    answers("1", "")          # Continue, then the [enter] pause
    loaded = game.title_screen()
    assert loaded.handle == "Wraith" and loaded.day == 17 and loaded.save_slot == 2


def test_title_screen_load_picks_a_slot(player, answers, monkeypatch):
    save.write(Player(name="a", handle="Alpha", background="Street Kid"), 1)
    save.write(Player(name="b", handle="Beta", background="Netrunner"), 4)
    answers("2", "1", "")     # Load a run → first listed non-empty slot → pause
    loaded = game.title_screen()
    assert loaded.handle == "Alpha"


def test_title_screen_new_run_ignores_saves(player, answers, monkeypatch):
    save.write(player, 1)
    made = Player(name="new", handle="New", background="Street Kid")
    monkeypatch.setattr(game, "create_character", lambda: made)
    answers("3")
    assert game.title_screen() is made


def test_damaged_save_is_reported_and_does_not_end_the_session(answers, monkeypatch, capsys):
    save.write(Player(name="a", handle="Alpha", background="Street Kid"), 1)
    save.slot_path(1).write_text('{"version": 99, "player": {}}')
    made2 = Player(name="new", handle="New", background="Street Kid")
    monkeypatch.setattr(game, "create_character", lambda: made2)
    answers("1", "1", "2")    # Load a run → damaged slot → error → back to title → New run
    assert game.title_screen() is made2
    assert "newer version" in capsys.readouterr().out


def test_new_run_takes_first_empty_slot(player, answers):
    save.write(Player(name="a", handle="Alpha", background="Street Kid"), 1)
    game._assign_slot(player)
    assert player.save_slot == 2


def test_new_run_when_all_slots_full_prompts_to_overwrite(player, answers):
    for n in range(1, data.SAVE_SLOTS + 1):
        save.write(Player(name="n", handle=f"P{n}", background="x"), n)
    answers("3")              # overwrite slot 3
    game._assign_slot(player)
    assert player.save_slot == 3
    assert save.describe(3)["handle"] == player.handle


def test_save_game_is_a_free_action(player, answers):
    answers("4")
    assert game.save_game(player) is False
    assert save.describe(4)["handle"] == player.handle
    assert player.save_slot == 4


def test_save_game_can_be_cancelled(player, answers):
    answers(str(data.SAVE_SLOTS + 1))   # "Back"
    assert game.save_game(player) is False
    assert save.list_slots() == [None] * data.SAVE_SLOTS


def test_save_game_confirms_before_overwriting_another_run(player, answers):
    save.write(Player(name="a", handle="Alpha", background="Street Kid"), 1)
    player.save_slot = 2
    answers("1", "n")         # pick slot 1, decline the overwrite
    assert game.save_game(player) is False
    assert save.describe(1)["handle"] == "Alpha"


def test_save_game_overwrites_own_slot_without_asking(player, answers):
    save.write(player, 1)
    player.handle = "Renamed"
    answers("1")              # no confirmation prompt for your own slot
    game.save_game(player)
    assert save.describe(1)["handle"] == "Renamed"


def test_saved_run_resumes_with_same_state(player, monkeypatch):
    player.credits, player.cred, player.day = 4321, 9, 15
    player.cyberware = ["optics"]
    player.job_id = "courier"
    save.write(player, 1)
    resumed = save.read(1)
    assert (resumed.credits, resumed.cred, resumed.day) == (4321, 9, 15)
    assert resumed.job["id"] == "courier"
    assert resumed.skill("charm") == player.skill("charm")
