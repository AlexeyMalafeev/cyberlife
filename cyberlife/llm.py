"""NPC dialog: stock lines from data.NPCS, optionally voiced by a language model.

The model only ever narrates. Every mechanical outcome is decided in Python before a line is
requested, and the stock line is picked from `random` whichever backend is active, so a given
--seed plays out identically with the model on or off.
"""
import json
import os
import random
import re
import urllib.request

from . import data
from .ui import say, dim, cyan

MAX_LINE = 240        # characters of model output we'll print
MAX_TOKENS = 80
GIVE_UP_AFTER = 3     # consecutive failures before falling back to stock lines for the session


class CannedBackend:
    """No model: every line comes from the stock lines in data.NPCS."""
    name = "off"

    def complete(self, messages):
        return None


class ChatCompletionsBackend:
    """Any server speaking the OpenAI-style /v1/chat/completions API."""
    name = "chat"
    DEFAULT_TIMEOUT = 5.0

    def __init__(self, url, model=None, timeout=None, headers=None, post=None):
        self.url = url.rstrip("/") + "/v1/chat/completions"
        self.model = model
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.headers = headers or {}
        self._post = post or _post_json

    def complete(self, messages):
        payload = {"messages": messages, "max_tokens": MAX_TOKENS, "temperature": 0.8}
        if self.model:
            payload["model"] = self.model
        reply = self._post(self.url, payload, self.headers, self.timeout)
        return reply["choices"][0]["message"]["content"]


class MlxBackend(ChatCompletionsBackend):
    """A local `mlx_lm.server` (Apple Silicon). Start it with --model so nothing loads mid-game."""
    name = "mlx"
    DEFAULT_URL = "http://localhost:8080"

    def __init__(self, url=None, model=None, timeout=None, post=None):
        super().__init__(url or self.DEFAULT_URL, model=model, timeout=timeout, post=post)


class DeepSeekBackend(ChatCompletionsBackend):
    """DeepSeek's hosted API. The key comes from $DEEPSEEK_API_KEY and only ever goes in a header."""
    name = "deepseek"
    DEFAULT_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"
    DEFAULT_TIMEOUT = 10.0     # a round trip over the internet, not localhost

    def __init__(self, url=None, model=None, timeout=None, post=None, api_key=None):
        api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("--llm deepseek needs an API key in the DEEPSEEK_API_KEY environment variable")
        super().__init__(url or self.DEFAULT_URL, model=model or self.DEFAULT_MODEL, timeout=timeout,
                         headers={"Authorization": f"Bearer {api_key}"}, post=post)


BACKENDS = {"off": CannedBackend, "mlx": MlxBackend, "deepseek": DeepSeekBackend}


def make_backend(name, url=None, model=None, timeout=None):
    """Build a backend by CLI name. Raises ValueError for an unknown name or missing API key."""
    if name not in BACKENDS:
        raise ValueError(f"unknown dialog backend {name!r}; choose from {', '.join(BACKENDS)}")
    if name == "off":
        return CannedBackend()
    return BACKENDS[name](url=url, model=model, timeout=timeout)


def _post_json(url, payload, headers, timeout):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


# -- state ---------------------------------------------------------------

backend = CannedBackend()
_failures = 0


def use(new_backend):
    global backend, _failures
    backend = new_backend
    _failures = 0


# -- prompts -------------------------------------------------------------

def player_summary(player):
    chrome = [cw["name"] for cw in data.CYBERWARE if player.has(cw["id"])]
    job = player.job["name"] if player.job else "unemployed"
    return (f"{player.handle}, a {player.background} ({job}). Day {player.day}. "
            f"Street cred {player.cred}/{data.LEGEND_CRED}, heat {player.heat}, "
            f"humanity {player.humanity}/100, credits {player.credits}. "
            f"Chrome: {', '.join(chrome) or 'none'}.")


def build_messages(npc, player, situation, example):
    system = (
        f"You are {npc['name']}, {npc['role']} in {data.CITY}, 2087, a cyberpunk megacity. "
        f"Manner: {npc['disposition']}. About you: {' '.join(npc['facts'])}\n"
        f"You're talking to {player_summary(player)}\n"
        "Reply with ONE line of spoken dialog, under 30 words. No narration, no stage "
        "directions, no quotation marks, no name prefix. Don't offer money, items or deals "
        "beyond what the situation says. Never mention amounts, prices or other numbers; the "
        "game shows those itself."
    )
    user = f"Situation: {situation}\nFor tone only, don't reuse its wording: {example}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


# -- output hygiene ------------------------------------------------------

_THINK = re.compile(r"<think>.*?(</think>|$)", re.S | re.I)
_ANSI = re.compile(r"\x1b(\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(\x07|\x1b\\)?|.)?")


def sanitize(text, speaker=""):
    """Make model output safe and tidy to print: one plain line, capped, or '' if nothing usable."""
    if not isinstance(text, str):
        return ""
    text = _THINK.sub(" ", text)
    text = _ANSI.sub("", text)
    text = "".join(ch if ch.isprintable() else " " for ch in text)
    text = " ".join(text.split())
    if speaker and text.lower().startswith(speaker.lower() + ":"):
        text = text[len(speaker) + 1:].lstrip()
    text = text.strip("\"'“”*` ")
    if len(text) > MAX_LINE:
        cut = text[:MAX_LINE]
        end = max(cut.rfind(p) for p in ".!?")
        text = cut[:end + 1] if end >= MAX_LINE // 3 else cut[:cut.rfind(" ")].rstrip(",;:") + "…"
    return text


# "one" is left out: "no one", "the one" are everywhere and never a price.
_NUMBER = re.compile(
    r"\d|\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\w+teen|twenty|thirty|"
    r"forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|grand|dozen|half)\b", re.I)


def mentions_numbers(line):
    """Models get numbers wrong, and a wrong price reads as the game lying. The game shows real ones."""
    return bool(_NUMBER.search(line))


# -- the one entry point -------------------------------------------------

def respond(npc_id, player, situation, **context):
    """Return what `npc_id` says in `situation`. Never raises for backend trouble."""
    global _failures
    npc = data.NPCS[npc_id]
    sit = npc["situations"][situation]
    canned = random.choice(sit["canned"]).format(**context)   # always drawn: keeps --seed stable
    messages = build_messages(npc, player, sit["prompt"].format(**context), canned)
    try:
        text = backend.complete(messages)
    except Exception as exc:
        _failures += 1
        if _failures >= GIVE_UP_AFTER and not isinstance(backend, CannedBackend):
            reason = sanitize(str(exc) or type(exc).__name__)[:80]
            say(dim(f"(The {backend.name} dialog model isn't answering: {reason}. "
                    "Using stock lines for now.)"))
            use(CannedBackend())
        return canned
    if text is None:
        return canned
    _failures = 0
    line = sanitize(text, npc["name"])
    return canned if not line or mentions_numbers(line) else line


def speak(npc_id, player, situation, **context):
    say(f"{cyan(data.NPCS[npc_id]['name'])}: {dim(respond(npc_id, player, situation, **context))}")
