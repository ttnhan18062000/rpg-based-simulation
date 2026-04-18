from __future__ import annotations
from typing import Dict
from src.core.models.base import SimulationModel
from src.core.models.enums import ConsequenceKindSer

class Consequence(SimulationModel):
    """A persistent combat outcome impacting performance. [Milestone 5]"""
    id: str
    kind: ConsequenceKindSer
    tag: str                  # Human-readable name (e.g., "Serrated Gash")
    
    # Stat Multipliers (1.0 = neutral)
    atk_mult: float = 1.0
    def_mult: float = 1.0
    spd_mult: float = 1.0
    max_stamina_mult: float = 1.0
    
    severity: int = 1         # 1-5 scale (affects healing time)
    remaining_ticks: int = -1 # -1 = permanent (scar), > 0 = temporary (wound)
    
    def is_permanent(self) -> bool:
        return self.remaining_ticks == -1

    def tick(self) -> None:
        if self.remaining_ticks > 0:
            self.remaining_ticks -= 1

    @property
    def expired(self) -> bool:
        return self.remaining_ticks == 0
