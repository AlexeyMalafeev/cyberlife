"""Terminal I/O helpers: colors, menus, prompts."""
import os
import sys

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


class QuitGame(Exception):
    """Raised when the player types q/quit at any prompt."""


def _c(code, s):
    return f"\033[{code}m{s}\033[0m" if USE_COLOR else str(s)


def bold(s):   return _c("1", s)
def dim(s):    return _c("2", s)
def red(s):    return _c("91", s)
def green(s):  return _c("92", s)
def yellow(s): return _c("93", s)
def neon(s):   return _c("95", s)
def cyan(s):   return _c("96", s)


def say(s=""):
    print(s)


def hr():
    print(dim("─" * 62))


def header(title):
    hr()
    print(neon(bold(f" {title}")))
    hr()


def pause():
    try:
        input(dim("[enter] "))
    except EOFError:
        raise QuitGame


def _read(prompt):
    try:
        raw = input(prompt).strip()
    except EOFError:
        raise QuitGame
    if raw.lower() in ("q", "quit", "exit"):
        raise QuitGame
    return raw


def bar(value, maximum, width=12, color=green):
    value = max(0, min(value, maximum))
    filled = round(width * value / maximum) if maximum else 0
    return color("█" * filled) + dim("░" * (width - filled))


def menu(title, options):
    """Show a numbered menu; return the chosen index."""
    print(bold(title))
    for i, opt in enumerate(options, 1):
        print(f"  {cyan(i)}. {opt}")
    while True:
        raw = _read(neon("> "))
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(dim(f"Pick 1-{len(options)} (or q to quit)."))


def ask_yes_no(prompt):
    while True:
        raw = _read(neon(f"{prompt} [y/n] ")).lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False


def ask_text(prompt, default):
    raw = _read(neon(f"{prompt} [{default}] "))
    return raw or default
