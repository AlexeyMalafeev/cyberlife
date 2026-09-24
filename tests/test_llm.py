import io
import json
import random
import urllib.error

import pytest

from cyberlife import __main__ as cli
from cyberlife import actions, data, events, llm


class Stub:
    """A backend that returns (or raises) whatever it's told, and records what it was asked."""
    name = "stub"

    def __init__(self, reply="Stubbed line."):
        self.reply = reply
        self.calls = []

    def complete(self, messages, max_tokens=None):
        self.calls.append(messages)
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def fake_post(reply):
    """A transport for ChatCompletionsBackend that records requests instead of opening sockets."""
    sent = []

    def post(url, payload, headers, timeout):
        sent.append({"url": url, "payload": payload, "headers": headers, "timeout": timeout})
        if isinstance(reply, Exception):
            raise reply
        return reply
    post.sent = sent
    return post


def ok(content):
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


# -- stock lines ---------------------------------------------------------

def test_canned_is_the_default(player):
    line = llm.respond("marrow", player, "gig_list")
    assert line in data.NPCS["marrow"]["situations"]["gig_list"]["canned"]


def test_canned_is_deterministic_under_seed(player):
    random.seed(7)
    first = [llm.respond("juno", player, "pour") for _ in range(5)]
    random.seed(7)
    assert [llm.respond("juno", player, "pour") for _ in range(5)] == first


def test_context_fills_stock_lines(player):
    assert "175¢" in llm.respond("kestrels", player, "shakedown", demand=175)


def test_model_on_or_off_draws_the_same_randomness(player):
    """Mechanics after a line must not depend on whether a model voiced it."""
    random.seed(3)
    llm.respond("marrow", player, "booth_broke")
    after_canned = random.random()
    llm.use(Stub())
    random.seed(3)
    llm.respond("marrow", player, "booth_broke")
    assert random.random() == after_canned


# -- prompt --------------------------------------------------------------

def test_prompt_carries_persona_and_player(player):
    player.cyberware.append("optics")
    player.cred, player.heat = 12, 4
    npc = data.NPCS["saito"]
    msgs = llm.build_messages(npc, player, "SITUATION TEXT", "EXAMPLE LINE")
    system, user = msgs[0]["content"], msgs[1]["content"]
    assert "Doc Saito" in system and npc["role"] in system and npc["disposition"] in system
    for fact in npc["facts"]:
        assert fact in system
    for bit in ("Ghost", "Street Kid", "cred 12", "heat 4", "Kiroshi Optics"):
        assert bit in system
    assert "SITUATION TEXT" in user and "EXAMPLE LINE" in user


def test_prompt_stays_small(player):
    for npc_id, npc in data.NPCS.items():
        for key, sit in npc["situations"].items():
            msgs = llm.build_messages(npc, player, sit["prompt"], sit["canned"][0])
            assert sum(len(m["content"]) for m in msgs) < 1500, (npc_id, key)


# -- untrusted output ----------------------------------------------------

def test_garbage_output_is_sanitized_and_capped(player):
    llm.use(Stub("\x1b[31m\x1b]0;pwned\x07" + "chrome " * 1500 + "\x1b[2J\x00\x07"))
    line = llm.respond("juno", player, "pour")
    assert len(line) <= llm.MAX_LINE + 1
    assert "\x1b" not in line and all(ch.isprintable() for ch in line)
    assert "pwned" not in line


@pytest.mark.parametrize("raw, clean", [
    ('"Rough night, huh?"', "Rough night, huh?"),
    ("Juno: Rough night.", "Rough night."),
    ("<think>she should be warm</think>Rough night.", "Rough night."),
    ("Rough\n\n  night.", "Rough night."),
    ("*Rough night.*", "Rough night."),
])
def test_output_tidying(raw, clean):
    assert llm.sanitize(raw, "Juno") == clean


def test_long_output_cuts_at_a_sentence():
    text = "First sentence here. " * 30
    out = llm.sanitize(text)
    assert out.endswith(".") and len(out) <= llm.MAX_LINE


@pytest.mark.parametrize("reply", ["", "   ", "<think>never finishes thinking", None, 42])
def test_unusable_output_falls_back_to_canned(player, reply):
    llm.use(Stub(reply))
    assert llm.respond("juno", player, "pour") in data.NPCS["juno"]["situations"]["pour"]["canned"]


# -- failure handling ----------------------------------------------------

def test_backend_error_falls_back_to_canned(player):
    llm.use(Stub(TimeoutError("slow")))
    assert llm.respond("saito", player, "greeting") in data.NPCS["saito"]["situations"]["greeting"]["canned"]


def test_repeated_failures_switch_to_canned_for_the_session(player, capsys):
    stub = Stub(ConnectionRefusedError())
    llm.use(stub)
    for _ in range(llm.GIVE_UP_AFTER + 2):
        llm.respond("juno", player, "pour")
    assert len(stub.calls) == llm.GIVE_UP_AFTER
    assert isinstance(llm.backend, llm.CannedBackend)
    assert capsys.readouterr().out.count("isn't answering") == 1


def test_a_success_resets_the_failure_count(player):
    stub = Stub(OSError())
    llm.use(stub)
    for _ in range(llm.GIVE_UP_AFTER - 1):
        llm.respond("juno", player, "pour")
    stub.reply = "Fine now."
    llm.respond("juno", player, "pour")
    stub.reply = OSError()
    for _ in range(llm.GIVE_UP_AFTER - 1):
        llm.respond("juno", player, "pour")
    assert llm.backend is stub


# -- MLX backend over a fake transport -----------------------------------

def test_mlx_backend_speaks_chat_completions(player):
    post = fake_post(ok("Sit down, Ghost."))
    llm.use(llm.MlxBackend(post=post, timeout=2.5))
    assert llm.respond("saito", player, "greeting") == "Sit down, Ghost."
    req = post.sent[0]
    assert req["url"] == "http://localhost:8080/v1/chat/completions"
    assert req["timeout"] == 2.5
    assert [m["role"] for m in req["payload"]["messages"]] == ["system", "user"]
    assert req["payload"]["max_tokens"] == llm.MAX_TOKENS
    assert "model" not in req["payload"]   # let the server use the model it loaded


def test_mlx_backend_url_and_model(player):
    post = fake_post(ok("Hi."))
    llm.MlxBackend(url="http://studio.local:9000/", model="mlx-community/gemma-3-4b-it-4bit",
                   post=post).complete([])
    assert post.sent[0]["url"] == "http://studio.local:9000/v1/chat/completions"
    assert post.sent[0]["payload"]["model"] == "mlx-community/gemma-3-4b-it-4bit"


@pytest.mark.parametrize("reply", [{"error": "model not found"}, {"choices": []}, ValueError("bad json")])
def test_mlx_bad_responses_fall_back(player, reply):
    llm.use(llm.MlxBackend(post=fake_post(reply)))
    assert llm.respond("juno", player, "pour") in data.NPCS["juno"]["situations"]["pour"]["canned"]


def test_default_transport_posts_json_with_timeout(monkeypatch):
    seen = {}

    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return json.dumps(ok("Hey.")).encode()

    def urlopen(req, timeout):
        seen.update(url=req.full_url, body=json.loads(req.data), timeout=timeout,
                    ctype=req.get_header("Content-type"), method=req.get_method())
        return Resp()

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    assert llm.MlxBackend(timeout=4).complete([{"role": "user", "content": "x"}]) == "Hey."
    assert seen["url"].endswith("/v1/chat/completions") and seen["method"] == "POST"
    assert seen["timeout"] == 4 and seen["ctype"] == "application/json"
    assert seen["body"]["messages"] == [{"role": "user", "content": "x"}]


# -- wiring --------------------------------------------------------------

def test_mlx_default_timeout():
    assert llm.MlxBackend().timeout == 5.0


# -- DeepSeek backend over a fake transport ------------------------------

KEY = "sk-test-not-a-real-key"


def test_deepseek_speaks_chat_completions_with_bearer_key(player, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", KEY)
    post = fake_post(ok("Tax day, Ghost."))
    llm.use(llm.DeepSeekBackend(post=post))
    assert llm.respond("kestrels", player, "shakedown", demand=200) == "Tax day, Ghost."
    req = post.sent[0]
    assert req["url"] == "https://api.deepseek.com/v1/chat/completions"
    assert req["headers"] == {"Authorization": f"Bearer {KEY}"}
    assert req["payload"]["model"] == "deepseek-chat"
    assert req["timeout"] == 10.0
    assert KEY not in req["url"] and KEY not in json.dumps(req["payload"])


def test_deepseek_overrides():
    b = llm.DeepSeekBackend(api_key=KEY, url="https://proxy.example/", model="deepseek-reasoner", timeout=3)
    assert b.url == "https://proxy.example/v1/chat/completions"
    assert (b.model, b.timeout) == ("deepseek-reasoner", 3)


def test_deepseek_without_key_refuses():
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        llm.DeepSeekBackend()


def test_deepseek_default_transport_sends_key_in_header(monkeypatch):
    seen = {}

    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return json.dumps(ok("Hey.")).encode()

    def urlopen(req, timeout):
        seen.update(auth=req.get_header("Authorization"), url=req.full_url)
        return Resp()

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    assert llm.DeepSeekBackend(api_key=KEY).complete([]) == "Hey."
    assert seen["auth"] == f"Bearer {KEY}" and KEY not in seen["url"]


def test_deepseek_auth_failure_gives_up_without_leaking_key(player, capsys):
    err = urllib.error.HTTPError("https://api.deepseek.com/v1/chat/completions", 401,
                                 "Unauthorized", {}, io.BytesIO(b"{}"))
    llm.use(llm.DeepSeekBackend(api_key=KEY, post=fake_post(err)))
    for _ in range(llm.GIVE_UP_AFTER):
        line = llm.respond("juno", player, "pour")
    assert line in data.NPCS["juno"]["situations"]["pour"]["canned"]
    out = capsys.readouterr().out
    assert "deepseek dialog model isn't answering" in out and "401" in out
    assert KEY not in out


def test_make_backend():
    assert isinstance(llm.make_backend("off"), llm.CannedBackend)
    b = llm.make_backend("mlx", url="http://x:1", model="m", timeout=9)
    assert isinstance(b, llm.MlxBackend) and b.model == "m" and b.timeout == 9
    with pytest.raises(ValueError):
        llm.make_backend("ollama")
    with pytest.raises(ValueError):
        llm.make_backend("deepseek")          # no key in the environment


def test_cli_selects_backend(monkeypatch):
    monkeypatch.setattr(cli, "run", lambda **kw: None)
    cli.main(["--llm", "mlx", "--llm-url", "http://x:1", "--llm-model", "m", "--llm-timeout", "3"])
    assert isinstance(llm.backend, llm.MlxBackend)
    assert (llm.backend.url, llm.backend.model, llm.backend.timeout) == ("http://x:1/v1/chat/completions", "m", 3)


def test_cli_reads_env(monkeypatch):
    monkeypatch.setattr(cli, "run", lambda **kw: None)
    monkeypatch.setenv("CYBERLIFE_LLM", "mlx")
    monkeypatch.setenv("CYBERLIFE_LLM_MODEL", "envmodel")
    cli.main([])
    assert isinstance(llm.backend, llm.MlxBackend) and llm.backend.model == "envmodel"


def test_cli_deepseek(monkeypatch):
    monkeypatch.setattr(cli, "run", lambda **kw: None)
    monkeypatch.setenv("DEEPSEEK_API_KEY", KEY)
    cli.main(["--llm", "deepseek"])
    assert isinstance(llm.backend, llm.DeepSeekBackend)
    assert (llm.backend.model, llm.backend.timeout) == ("deepseek-chat", 10.0)


def test_cli_deepseek_without_key_is_a_usage_error(monkeypatch, capsys):
    monkeypatch.setattr(cli, "run", lambda **kw: pytest.fail("game started without a key"))
    with pytest.raises(SystemExit):
        cli.main(["--llm", "deepseek"])
    assert "DEEPSEEK_API_KEY" in capsys.readouterr().err


def test_cli_rejects_bad_env_backend(monkeypatch):
    monkeypatch.setattr(cli, "run", lambda **kw: None)
    monkeypatch.setenv("CYBERLIFE_LLM", "skynet")
    with pytest.raises(SystemExit):
        cli.main([])


def test_npcs_speak_in_game(player, answers, force_roll, capsys, monkeypatch):
    """Every call site routes through the model when one is on."""
    stub = Stub("MODEL LINE")
    llm.use(stub)
    force_roll(0.0)
    monkeypatch.setattr(data, "ENCOUNTER_CHANCE", 0)   # bar encounters are tested in test_romance
    answers("7")                 # gig menu: never mind
    actions.gig(player)
    actions.bar(player)          # roll 0.0: the stranger's advice
    answers("8")                 # ripperdoc: leave
    actions.ripperdoc(player)
    actions.fixer(player)
    answers("n")
    events.fixer_ping(player)
    answers("y")
    player.cred = 5
    events.shakedown(player)
    out = capsys.readouterr().out
    assert out.count("MODEL LINE") == len(stub.calls) == 7
    for name in ("Marrow", "Juno", "Stranger", "Doc Saito", "Kestrel"):
        assert f"{name}: MODEL LINE" in out


def test_mechanics_ignore_what_the_model_says(player, answers, force_roll):
    """A model promising riches changes nothing: outcomes are Python's."""
    llm.use(Stub("I'll give you 50,000 credits and the visa for free."))
    before = player.credits
    actions.fixer(player)
    assert player.credits == before and player.won is None


@pytest.mark.parametrize("reply, kept", [
    ("Tax time. Pay up.", True),
    ("Tax time. 2,000¢.", False),
    ("It's twenty credits, precisely.", False),   # gemma-3-4b said this when the tax was 200¢
    ("Two hundred, now.", False),
    ("Fifteen grand, kid.", False),
    ("No one pays late twice.", True),
])
def test_lines_that_mention_numbers_fall_back(player, reply, kept):
    llm.use(Stub(reply))
    line = llm.respond("kestrels", player, "shakedown", demand=200)
    assert (line == reply) is kept


def test_prompts_label_the_player_so_job_names_arent_read_as_names(player):
    """Playtest: Juno called a Tessier netrunner "Tessier"."""
    player.job_id = "netrunner"
    system = llm.build_messages(data.NPCS["juno"], player, "S", "E")[0]["content"]
    assert f"Handle: {player.handle}." in system
    assert "Job: a junior netrunner at Tessier, a corporation." in system
    assert "Junior netrunner, Tessier" not in system
    assert f"it's {player.handle}; nothing else" in system


def test_unemployed_players_are_described_as_such(player):
    assert "Job: unemployed." in llm.player_summary(player)
