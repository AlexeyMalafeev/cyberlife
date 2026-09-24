import contextlib
import io
import random
import re

import pytest

from cyberlife import __main__ as cli
from cyberlife import data, debug, events, game, romance, ui


def test_day_menu_has_no_debug_entry_by_default(player, answers, capsys):
    answers("9")        # "End the day"
    game.day_loop(player)
    assert "Debug" not in capsys.readouterr().out


def test_debug_menu_is_a_free_action(player, answers):
    debug.enable()
    answers("9", "0", "0")      # Debug, Back, End the day
    game.day_loop(player)
    assert player.energy == player.max_energy


def test_cli_flag_turns_debug_on(monkeypatch):
    monkeypatch.setattr(cli, "run", lambda **kw: None)
    cli.main(["--debug"])
    assert debug.ENABLED and romance.SHOW_SHEETS
    cli.main([])
    assert not debug.ENABLED and not romance.SHOW_SHEETS


def test_set_a_stat(player, answers):
    answers(str(debug.STATS.index("credits") + 1), "12345")
    debug.edit_stats(player)
    assert player.credits == 12345


def test_blank_or_bad_number_keeps_the_value(player, answers, capsys):
    answers("1", "", "1", "lots")
    debug.edit_stats(player)
    debug.edit_stats(player)
    assert player.credits == 1000
    assert "Not a number" in capsys.readouterr().out


def test_set_a_skill(player, answers):
    answers("2", "7")               # muscle
    debug.edit_skills(player)
    assert player.skills["muscle"] == 7


def test_cyberware_toggles(player, answers):
    first = data.CYBERWARE[0]["id"]
    answers("1", "1")
    debug.toggle_cyberware(player)
    assert player.has(first)
    debug.toggle_cyberware(player)
    assert not player.has(first)


def test_set_and_clear_job(player, answers):
    answers("2", str(len(data.JOBS) + 1))
    debug.set_job(player)
    assert player.job_id == data.JOBS[1]["id"]
    debug.set_job(player)
    assert player.job_id is None


def test_edit_cast_member(player, answers):
    romance.ensure_cast(player)
    answers("2", str(debug.CAST_FIELDS.index("affection") + 1), "9")
    debug.edit_member(player)
    assert player.cast[1]["affection"] == 9


def test_make_her_your_partner(player, answers):
    romance.ensure_cast(player)
    stage = str(data.CAST_STAGES.index("dating") + 1)
    answers("1", str(len(debug.CAST_FIELDS) + 1), stage)
    debug.edit_member(player)
    assert player.partner is player.cast[0] and player.cast[0]["since_day"] == player.day


def test_only_one_partner_at_a_time(player, dating, answers, capsys):
    stage = str(data.CAST_STAGES.index("dating") + 1)
    answers("2", str(len(debug.CAST_FIELDS) + 1), stage)
    debug.edit_member(player)
    assert player.cast[1]["stage"] == "stranger" and player.partner is dating
    assert "one partner at a time" in capsys.readouterr().out


def test_regenerate_cast(player):
    romance.ensure_cast(player)
    before = [dict(c) for c in player.cast]
    debug.new_cast(player)
    assert len(player.cast) == data.CAST_SIZE and player.cast != before


def test_run_a_night_event(player, answers, monkeypatch):
    ran = []
    monkeypatch.setattr(events, "EVENTS", [(1, lambda p: ran.append("yes"), lambda p: True),
                                           (1, lambda p: ran.append("no"), lambda p: False)])
    answers("1", "2")
    debug.run_event(player)
    debug.run_event(player)
    assert ran == ["yes"]


def test_toggle_sheets(player):
    debug.enable()
    debug.toggle_sheets(player)
    assert not romance.SHOW_SHEETS
    debug.toggle_sheets(player)
    assert romance.SHOW_SHEETS


@pytest.mark.parametrize("seed", range(10))
def test_random_play_with_debug_on_reaches_an_ending(seed, monkeypatch):
    rng = random.Random(seed)

    def fake_read(prompt=""):
        if "[y/n]" in prompt:
            return rng.choice(["y", "n"])
        if "> " in prompt:
            return str(rng.randint(0, 9))
        return rng.choice(["", "0", "5", "x"])

    monkeypatch.setattr(ui, "_read", fake_read)
    debug.enable()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        random.seed(seed)
        game.run()
    text = out.getvalue()
    assert ("GAME OVER" in text) or ("YOU MADE IT" in text)
    assert re.search(r"Survived \d+ days", text)


def test_stats_the_game_never_clamps_have_floors(player, answers):
    answers(str(debug.STATS.index("day") + 1), "0", str(debug.STATS.index("energy") + 1), "-3")
    debug.edit_stats(player)
    debug.edit_stats(player)
    assert player.day == 1 and player.energy == 0
