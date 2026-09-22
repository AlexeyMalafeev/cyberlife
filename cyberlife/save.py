"""Save/load: JSON slots on disk, versioned and tolerant of schema drift."""
import dataclasses
import json
import os
import time
from pathlib import Path

from . import data
from .player import Player

SAVE_VERSION = 1

_save_dir = None


class SaveError(Exception):
    """A save file is missing, unreadable, or too new to load."""


def save_dir():
    """Where slots live. Honors --save-dir, then CYBERLIFE_SAVE_DIR, then ~/.cyberlife/saves."""
    if _save_dir is not None:
        return _save_dir
    env = os.environ.get("CYBERLIFE_SAVE_DIR")
    return Path(env) if env else Path.home() / ".cyberlife" / "saves"


def set_save_dir(path):
    global _save_dir
    _save_dir = Path(path) if path is not None else None


def slot_path(slot):
    return save_dir() / f"slot-{slot}.json"


def write(player, slot):
    """Write the run to a slot. Returns the path."""
    player.save_slot = slot
    payload = {
        "version": SAVE_VERSION,
        "saved_at": time.time(),
        "player": dataclasses.asdict(player),
    }
    path = slot_path(slot)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write via a temp file so an interrupted save can't corrupt an existing one.
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=1))
    tmp.replace(path)
    return path


def _payload(slot):
    path = slot_path(slot)
    if not path.exists():
        raise SaveError(f"Slot {slot} is empty.")
    try:
        payload = json.loads(path.read_text())
        version = int(payload["version"])
        fields = payload["player"]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise SaveError(f"Slot {slot} is corrupt ({exc}).") from exc
    if version > SAVE_VERSION:
        raise SaveError(
            f"Slot {slot} was written by a newer version of the game "
            f"(save v{version}, this build reads v{SAVE_VERSION})."
        )
    return payload, version, fields


def read(slot):
    """Load a slot into a Player. Raises SaveError if unusable."""
    payload, version, fields = _payload(slot)
    known = {f.name for f in dataclasses.fields(Player)}
    # Drop fields this build no longer has; anything new keeps its dataclass default.
    kept = {k: v for k, v in fields.items() if k in known}
    missing = known - set(kept)
    try:
        player = Player(**kept)
    except TypeError as exc:
        raise SaveError(f"Slot {slot} is missing required data ({exc}).") from exc
    if player.job_id and data.job_by_id(player.job_id) is None:
        player.job_id = None   # job was removed from the game since this save
    player.cyberware = [c for c in player.cyberware if any(cw["id"] == c for cw in data.CYBERWARE)]
    player.skills = {k: player.skills.get(k, 1) for k in Player(name="", handle="", background="").skills}
    player.save_slot = slot
    player.clamp()
    _ = missing   # tolerated by design: older saves simply take current defaults
    return player


def describe(slot):
    """Metadata for the slot menus.

    None means the slot is genuinely empty. A file that exists but can't be read comes
    back with an ``unreadable`` message instead, so the menu can show it and nothing
    silently overwrites a damaged-but-present save.
    """
    if not slot_path(slot).exists():
        return None
    try:
        payload, version, fields = _payload(slot)
    except SaveError as exc:
        return {"slot": slot, "unreadable": str(exc)}
    return {
        "unreadable": None,
        "slot": slot,
        "handle": fields.get("handle", "?"),
        "background": fields.get("background", "?"),
        "day": fields.get("day", 0),
        "credits": fields.get("credits", 0),
        "cred": fields.get("cred", 0),
        "saved_at": payload.get("saved_at", 0),
        "version": version,
        "stale": version < SAVE_VERSION,
    }


def list_slots():
    """[describe(1), ..., describe(SAVE_SLOTS)] with None for empty slots."""
    return [describe(n) for n in range(1, data.SAVE_SLOTS + 1)]


def first_empty(slots=None):
    """Lowest slot with no file at all. A damaged save still occupies its slot."""
    slots = list_slots() if slots is None else slots
    return next((i + 1 for i, s in enumerate(slots) if s is None), None)


def latest(slots=None):
    """Slot number of the most recently saved readable run, or None."""
    slots = list_slots() if slots is None else slots
    used = [s for s in slots if s and not s["unreadable"]]
    return max(used, key=lambda s: s["saved_at"])["slot"] if used else None


def delete(slot):
    slot_path(slot).unlink(missing_ok=True)
