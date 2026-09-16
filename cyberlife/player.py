"""Player state and derived stats."""
from dataclasses import dataclass, field

from . import data


@dataclass
class Player:
    name: str
    handle: str
    background: str
    day: int = 1
    credits: int = 500
    health: int = 100
    energy: int = 3
    stress: int = 20
    humanity: int = 100
    cred: int = 0
    heat: int = 0
    skills: dict = field(default_factory=lambda: {"hacking": 1, "muscle": 1, "charm": 1})
    cyberware: list = field(default_factory=list)   # list of cyberware ids
    job: dict | None = None
    rent: int = 600
    missed_rent: int = 0
    energy_penalty: int = 0   # applied at the start of the next day
    won: str | None = None

    # -- derived stats -------------------------------------------------

    def _bonus(self, key):
        total = 0
        for cw in data.CYBERWARE:
            if cw["id"] in self.cyberware:
                total += cw["bonus"].get(key, 0)
        return total

    def skill(self, name):
        return self.skills[name] + self._bonus(name)

    @property
    def max_health(self):
        return 100 + self._bonus("max_health")

    @property
    def max_energy(self):
        return 3 + self._bonus("max_energy")

    def has(self, cyber_id):
        return cyber_id in self.cyberware

    # -- mutation helpers ----------------------------------------------

    def clamp(self):
        self.health = max(0, min(self.health, self.max_health))
        self.stress = max(0, min(self.stress, 100))
        self.humanity = max(0, min(self.humanity, 100))
        self.cred = max(0, self.cred)
        self.heat = max(0, self.heat)
        self.credits = max(0, self.credits)

    def death_cause(self):
        """Return a game-over reason, or None if still in the game."""
        self.clamp()
        if self.health <= 0:
            return "flatlined"
        if self.humanity <= 0:
            return "cyberpsychosis"
        if self.stress >= 100:
            return "burnout"
        if self.missed_rent >= data.MAX_MISSED_RENT:
            return "evicted"
        return None
