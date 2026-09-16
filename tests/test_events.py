import pytest

from cyberlife import events


def test_every_event_has_a_handler_and_predicate():
    for weight, handler, ok in events.EVENTS:
        assert weight > 0 and callable(handler) and callable(ok)


def test_night_event_only_picks_eligible(player, monkeypatch):
    player.credits = 100          # too poor for the chip dealer
    expected = {h.__name__ for _, h, ok in events.EVENTS if ok(player)}
    assert "corpo_sweep" not in expected and "chrome_glitch" not in expected
    fired = []
    patched = [(w, lambda p, name=h.__name__: fired.append(name), ok) for w, h, ok in events.EVENTS]
    monkeypatch.setattr(events, "EVENTS", patched)
    for _ in range(300):
        events.night_event(player)
    assert set(fired) == expected


@pytest.mark.parametrize("handler", [h for _, h, _ in events.EVENTS])
def test_each_handler_runs_when_eligible(handler, player, answers, force_roll):
    player.credits = 1000
    player.cred = 10
    player.heat = 4
    player.day = 20
    player.cyberware.append("optics")
    player.humanity = 50
    force_roll(0.99)
    answers("y", "y")
    handler(player)
    player.clamp()
    assert player.death_cause() is None


def test_corpo_sweep_fines_scale_with_heat(player, force_roll):
    force_roll(0.99)
    player.heat = 4
    events.corpo_sweep(player)
    assert player.credits == 1000 - (150 + 80 * 4)
    assert player.heat == 2


def test_shakedown_pay(player, answers):
    answers("y")
    events.shakedown(player)
    assert player.credits == 800
    assert player.health == 100


def test_fixer_ping_decline(player, answers):
    answers("n")
    events.fixer_ping(player)
    assert player.credits == 1000 and player.health == 100
