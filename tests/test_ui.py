import pytest

from cyberlife import ui


@pytest.fixture
def keys(monkeypatch):
    """Script raw keypresses: turn on single-key mode and feed ui._getkey from a queue."""
    queue = []

    def _getkey():
        if not queue:
            raise AssertionError("unexpected keypress read with no scripted key")
        return queue.pop(0)

    monkeypatch.setattr(ui, "RAW_KEYS", True)
    monkeypatch.setattr(ui, "_getkey", _getkey)

    def script(*items):
        queue.extend(items)
        return queue

    return script


def test_menu_keys_run_digits_then_zero_then_letters(answers, capsys):
    options = [f"opt{i}" for i in range(12)]
    answers("0")
    assert ui.menu("Pick", options) == 9
    out = capsys.readouterr().out
    assert "1. opt0" in out and "0. opt9" in out and "a. opt10" in out and "b. opt11" in out


def test_menu_keys_never_include_q():
    assert "q" not in ui.MENU_KEYS


def test_menu_reprompts_on_unlisted_key(answers, capsys):
    answers("7", "2")
    assert ui.menu("Pick", ["a", "b", "c"]) == 1
    assert "Press one of the keys shown" in capsys.readouterr().out


def test_menu_rejects_more_options_than_keys():
    with pytest.raises(ValueError):
        ui.menu("Pick", ["x"] * (len(ui.MENU_KEYS) + 1))


def test_menu_picks_on_a_single_keypress(keys):
    keys("3")
    assert ui.menu("Pick", ["a", "b", "c"]) == 2


def test_menu_letter_keys_ignore_case(keys):
    keys("A")
    assert ui.menu("Pick", [str(i) for i in range(11)]) == 10


def test_raw_menu_skips_ignored_keys(keys):
    keys("", "x", "1")   # escape sequence (read as ''), a stray letter, then a real pick
    assert ui.menu("Pick", ["a", "b"]) == 0


def test_yes_no_on_a_single_keypress(keys):
    keys("Y", "n")
    assert ui.ask_yes_no("Sure?") is True
    assert ui.ask_yes_no("Sure?") is False


def test_pause_takes_any_key(keys):
    keys("\r")
    ui.pause()
    keys("z")
    ui.pause()


@pytest.mark.parametrize("key", ["q", "Q", "\x04"])
def test_q_and_ctrl_d_quit_in_key_mode(keys, key):
    keys(key)
    with pytest.raises(ui.QuitGame):
        ui.menu("Pick", ["a"])


def test_ctrl_c_interrupts_in_key_mode(keys):
    keys("\x03")
    with pytest.raises(KeyboardInterrupt):
        ui.pause()


def test_text_prompts_still_read_whole_lines(keys, answers):
    answers("Molly")   # ask_text goes through _read, not _getkey
    assert ui.ask_text("Name?", "Kai") == "Molly"
