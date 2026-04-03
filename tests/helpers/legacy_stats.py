import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dataclasses import dataclass

@dataclass
class Stats:
    """DEPRECATED: Legacy stats shim for test compatibility.
    
    This class has been moved from the core engine to test helpers to enforce
    Aspect-Oriented Architecture (AOA) boundaries. Modern code should use
    Aspects (Combat, Progression, etc.) directly.
    """
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
    xp_to_next: int = 100 # Added for test compatibility
    gold: int = 0 # Added for test compatibility
