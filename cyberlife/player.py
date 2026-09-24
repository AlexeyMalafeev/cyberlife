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
    job_id: str | None = None                      # key into data.JOBS; see .job
    rent: int = 600
    missed_rent: int = 0
    energy_penalty: int = 0   # applied at the start of the next day
    won: str | None = None
    save_slot: int | None = None   # which slot this run autosaves to
    cast: list = field(default_factory=list)   # the women you can meet; see romance.new_member()

    # -- derived stats -------------------------------------------------

    def _bonus(self, key):
        total = 0
        for cw in data.CYBERWARE:
            if cw["id"] in self.cyberware:
                total += cw["bonus"].get(key, 0)
        return total

    @property
    def job(self):
        """The current job's data dict, or None. Set via job_id so state stays JSON-safe."""
        return data.job_by_id(self.job_id) if self.job_id else None

    @property
    def partner(self):
        """The cast member you're seeing, or None. Set her "stage" to change it."""
        return next((c for c in self.cast if c["stage"] in data.PARTNER_STAGES), None)

    @property
    def rent_due(self):
        """Rent actually charged: split once she's moved in."""
        partner = self.partner
        return self.rent // 2 if partner and partner["stage"] == "serious" else self.rent

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
