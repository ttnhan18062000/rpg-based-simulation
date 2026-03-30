from dataclasses import dataclass

@dataclass
class Stats:
    """DEPRECATED: Legacy stats shim for test compatibility."""
    level: int = 1
    xp: int = 0
    hp: int = 100
    max_hp: int = 100
    atk: int = 10
    def_: int = 5
    spd: int = 5
    stamina: int = 50
    max_stamina: int = 50
    luck: int = 0
    crit_rate: float = 0.05
    crit_dmg: float = 1.5
    evasion: float = 0.02
    vision: int = 6
    matk: int = 0
    mdef: int = 0
