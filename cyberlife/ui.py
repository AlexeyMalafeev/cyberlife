"""Terminal I/O helpers: colors, menus, prompts."""
import os
import sys

try:
    import termios
    import tty
except ImportError:          # Windows
    termios = tty = None
try:
    import msvcrt
except ImportError:          # everything else
    msvcrt = None

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
# Single-keypress input needs a real terminal; otherwise (pipes, tests) fall back to _read lines.
RAW_KEYS = sys.stdin.isatty() and (termios is not None or msvcrt is not None)

# Menu keys, in order: 1-9, then 0 for a tenth entry, then letters (never q -- that quits).
MENU_KEYS = "1234567890abcdefghijklmnoprstuvwxyz"


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


def _read(prompt):
    try:
        raw = input(prompt).strip()
    except EOFError:
        raise QuitGame
    if raw.lower() in ("q", "quit", "exit"):
        raise QuitGame
    return raw


def _getkey():
    """Block for one keypress and return it; drops keys typed ahead so they can't pick the next menu."""
    if msvcrt is not None:
        while msvcrt.kbhit():
            msvcrt.getwch()
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):     # arrow/function key: second half of the pair
            msvcrt.getwch()
            return ""
        return ch
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)                # no echo, no line buffering; Ctrl-C still raises
        termios.tcflush(fd, termios.TCIFLUSH)
        raw = os.read(fd, 32).decode(errors="ignore")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return "" if raw.startswith("\x1b") else raw[:1]   # ignore escape sequences (arrows etc.)


def _read_key(prompt):
    """Like _read, but a single keypress with no Enter. Returns the key lowercased ('' for Enter)."""
    if not RAW_KEYS:
        return _read(prompt).lower()
    sys.stdout.write(prompt)
    sys.stdout.flush()
    ch = _getkey()
    if ch == "\x03":
        raise KeyboardInterrupt
    if ch in ("\x04", "\x1a"):          # Ctrl-D / Ctrl-Z: EOF
        print()
        raise QuitGame
    ch = "" if ch in ("\r", "\n") else ch.lower()
    print(ch if ch.isprintable() else "")
    if ch == "q":
        raise QuitGame
    return ch


def pause():
    _read_key(dim("[any key] "))


def bar(value, maximum, width=12, color=green):
    value = max(0, min(value, maximum))
    filled = round(width * value / maximum) if maximum else 0
    return color("█" * filled) + dim("░" * (width - filled))


def menu(title, options):
    """Show a menu keyed 1-9, 0, a-z; one keypress picks. Return the chosen index."""
    if len(options) > len(MENU_KEYS):
        raise ValueError(f"menu has {len(options)} options; at most {len(MENU_KEYS)} fit")
    keys = MENU_KEYS[:len(options)]
    print(bold(title))
    for key, opt in zip(keys, options):
        print(f"  {cyan(key)}. {opt}")
    while True:
        raw = _read_key(neon("> "))
        if len(raw) == 1 and raw in keys:
            return keys.index(raw)
        print(dim("Press one of the keys shown (or q to quit)."))


def ask_yes_no(prompt):
    while True:
        raw = _read_key(neon(f"{prompt} [y/n] "))
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False


def ask_text(prompt, default):
    raw = _read(neon(f"{prompt} [{default}] "))
    return raw or default
