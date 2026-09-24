import random

from cyberlife import actions, data, romance


# -- work ---------------------------------------------------------------

def test_work_without_job_opens_job_board_and_never_mind_is_free(player, answers):
    answers(str(len(data.JOBS) + 1))   # "Never mind"
    assert not actions.work(player)
    assert player.job is None


def test_work_picks_job_then_earns_pay(player, answers, force_roll):
    force_roll(0.99)                    # no on-the-job skill gain
    answers("1")                        # noodle stand, no requirement
    before = player.credits
    assert actions.work(player)
    job = data.JOBS[0]
    assert player.job is job
    assert abs(player.credits - before - job["pay"]) <= 10
    assert player.stress == 20 + job["stress"]


def test_work_refuses_unqualified_job(player, answers):
    locked = next(i for i, j in enumerate(data.JOBS) if j["req"] and j["req"][1] > 5)
    answers(str(locked + 1))
    assert not actions.work(player)
    assert player.job is None


def test_quit_job_is_free(player):
    player.job_id = data.JOBS[0]["id"]
    assert not actions.quit_job(player)
    assert player.job is None


# -- gigs ---------------------------------------------------------------

def test_gig_success_pays_and_raises_cred_and_heat(player, answers, force_roll):
    force_roll(0.0)
    answers("1")
    g = data.GIGS[0]
    before = player.credits
    assert actions.gig(player)
    assert g["pay"][0] <= player.credits - before <= g["pay"][1]
    assert player.cred == g["cred"]
    assert player.heat == g["heat"]


def test_gig_failure_costs_health_credits_and_cred(player, answers, force_roll):
    force_roll(0.99)
    player.cred = 5
    answers("1")
    assert actions.gig(player)
    assert player.health < 100
    assert player.credits < 1000
    assert player.cred == 4


def test_gig_never_mind_is_free(player, answers):
    answers(str(len(data.GIGS) + 1))
    assert not actions.gig(player)
    assert player.heat == 0


def test_gig_chance_scales_with_skill_and_heat(player):
    g = data.GIGS[0]
    base = actions._gig_chance(player, g)
    player.skills[g["skill"]] += 2
    assert actions._gig_chance(player, g) > base
    player.heat = 5
    assert actions._gig_chance(player, g) < base + 0.14
    assert 0.05 <= actions._gig_chance(player, g) <= 0.95


# -- self-improvement ---------------------------------------------------

def test_train_success(player, answers, force_roll):
    force_roll(0.0)
    answers("1")
    assert actions.train(player)
    assert player.skills["hacking"] == 2
    assert player.stress == 24


def test_train_failure_still_costs_stress(player, answers, force_roll):
    force_roll(0.99)
    answers("1")
    assert actions.train(player)
    assert player.skills["hacking"] == 1
    assert player.stress == 24


def test_rest(player):
    player.health = 50
    player.stress = 60
    assert actions.rest(player)
    assert player.health == 62
    assert player.stress == 38


def test_bar_needs_credits(player):
    player.credits = 10
    assert not actions.bar(player)
    assert player.credits == 10


def test_bar_lowers_stress(player, force_roll):
    force_roll(0.99)   # no cred, no side-events
    player.stress = 50
    assert actions.bar(player)
    assert player.credits == 960
    assert player.stress == 38
    assert player.cred == 0


# -- shops --------------------------------------------------------------

def test_ripperdoc_install(player, answers):
    player.credits = 2000
    idx = next(i for i, cw in enumerate(data.CYBERWARE) if cw["id"] == "optics")
    answers(str(idx + 1), "y")
    assert actions.ripperdoc(player)
    assert "optics" in player.cyberware
    assert player.credits == 500
    assert player.humanity == 92


def test_ripperdoc_cannot_afford_then_leave(player, answers):
    player.credits = 10
    leave = len(data.CYBERWARE) + 2
    answers("1", str(leave))
    assert not actions.ripperdoc(player)
    assert player.cyberware == []


def test_ripperdoc_stimpack_is_free_action(player, answers):
    player.health = 40
    stim = len(data.CYBERWARE) + 1
    leave = stim + 1
    answers(str(stim), str(leave))
    assert not actions.ripperdoc(player)
    assert player.health == 70
    assert player.credits == 850


def test_fixer_visa_wins(player, answers):
    player.credits = data.VISA_COST
    answers("y")
    assert actions.fixer(player)
    assert player.won == "visa"
    assert player.credits == 0


def test_fixer_too_poor_is_free(player):
    assert not actions.fixer(player)
    assert player.won is None


def test_visa_for_two_takes_her_along(player, dating, answers):
    player.credits = data.VISA_FOR_TWO
    answers("y")
    assert actions.fixer(player)
    assert player.won == "visa" and dating["came_along"]
    assert player.credits == 0


def test_you_can_still_leave_without_her(player, dating, answers):
    player.credits = data.VISA_FOR_TWO
    answers("n", "y")
    assert actions.fixer(player)
    assert player.won == "visa" and not dating["came_along"]
    assert player.credits == data.VISA_FOR_TWO - data.VISA_COST


def test_one_visa_is_all_you_can_afford(player, dating, answers):
    player.credits = data.VISA_COST
    answers("y")                     # no two-visa question when you can't pay for it
    assert actions.fixer(player)
    assert not dating["came_along"]


# -- time with your partner ---------------------------------------------

def test_outing_with_your_partner(player, dating, answers):
    player.stress, player.humanity, player.day = 50, 60, 9
    before = dating["affection"]
    answers("1")                     # her first interest's outing
    assert actions.see_partner(player)
    fx = data.REL_OUTING
    assert player.credits == 1000 - fx["cost"]
    assert player.stress == 50 + fx["stress"]
    assert player.humanity == 60 + fx["humanity"]
    assert dating["affection"] == before + fx["affection"]
    assert dating["last_seen_day"] == 9


def test_outings_follow_her_interests(dating):
    labels = [label for label, _ in romance.outings(dating)]
    assert labels[:2] == [data.DATE_INTERESTS[i]["outing"] for i in dating["interests"]]
    assert labels[2] == data.REL_STAY_IN["label"]


def test_staying_in_is_free(player, dating, answers):
    answers("3")
    assert actions.see_partner(player)
    assert player.credits == 1000


def test_never_mind_and_no_money_are_free(player, dating, answers):
    answers("4")
    assert not actions.see_partner(player)
    player.credits = 0
    answers("1")
    assert not actions.see_partner(player)
    assert dating["last_seen_day"] == 1 and player.humanity == 100
