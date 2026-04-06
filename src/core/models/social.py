from typing import Any
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel

class SocialBond(SimulationModel):
    """A directed social bond between two entities. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    source_id: int
    target_id: int
    
    # Bond dimensions (-1.0 to 1.0)
    trust: float = Field(default=0.0, ge=-1.0, le=1.0)
    fear: float = Field(default=0.0, ge=-1.0, le=1.0)
    rivalry: float = Field(default=0.0, ge=-1.0, le=1.0)
    familiarity: float = Field(default=0.0, ge=0.0, le=1.0) # [PHASE 1]
    
    # Metadata
    last_interaction_tick: int = 0
    interaction_count: int = 0

class SocialRegistry(SimulationModel):
    """Authoritative global registry for directed social bonds. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    # Keyed by f"{source_id}:{target_id}"
    bonds: dict[str, SocialBond] = Field(default_factory=dict)
    # Global standing: Keyed by Entity ID string
    reputation: dict[str, float] = Field(default_factory=dict)
    max_bonds_per_source: int = 20
    
    def get_bond(self, source_id: int, target_id: int) -> SocialBond:
        key = f"{source_id}:{target_id}"
        if key not in self.bonds:
            self._ensure_bond_capacity(source_id)
            self.bonds[key] = SocialBond(source_id=source_id, target_id=target_id)
        return self.bonds[key]

    def _ensure_bond_capacity(self, source_id: int):
        """Prunes least relevant bonds if over limit."""
        prefix = f"{source_id}:"
        source_bonds = [(k, b) for k, b in self.bonds.items() if k.startswith(prefix)]
        if len(source_bonds) >= self.max_bonds_per_source:
            # Sort by last_interaction_tick ascending (oldest first)
            source_bonds.sort(key=lambda x: x[1].last_interaction_tick)
            del self.bonds[source_bonds[0][0]]

    def update_bond(self, source_id: int, target_id: int, trust_delta: float = 0.0, fear_delta: float = 0.0, rivalry_delta: float = 0.0, familiarity_delta: float = 0.0, tick: int = 0) -> tuple[dict[str, float], dict[str, float]]:
        """Update emotional stance and last interaction tick."""
        bond = self.get_bond(source_id, target_id)
        
        old_vals = {
            "trust": bond.trust,
            "fear": bond.fear,
            "rivalry": bond.rivalry,
            "familiarity": bond.familiarity
        }
        
        bond.trust = max(-1.0, min(1.0, bond.trust + trust_delta))
        bond.fear = max(0.0, min(1.0, bond.fear + fear_delta))
        bond.rivalry = max(0.0, min(1.0, bond.rivalry + rivalry_delta))
        bond.familiarity = max(0.0, min(1.0, bond.familiarity + familiarity_delta))
        bond.last_interaction_tick = tick
        bond.interaction_count += 1
        
        new_vals = {
            "trust": bond.trust,
            "fear": bond.fear,
            "rivalry": bond.rivalry,
            "familiarity": bond.familiarity
        }
        return old_vals, new_vals

    def get_reputation(self, entity_id: int) -> float:
        return self.reputation.get(str(entity_id), 0.0)

    def update_reputation(self, entity_id: int, delta: float):
        eid_str = str(entity_id)
        curr = self.reputation.get(eid_str, 0.0)
        self.reputation[eid_str] = max(-100.0, min(100.0, curr + delta))

    def copy(self) -> "SocialRegistry":
        """Manual deep copy for snapshotting."""
        new_registry = SocialRegistry(
            bonds={k: b.model_copy(deep=True) for k, b in self.bonds.items()},
            reputation=dict(self.reputation),
            max_bonds_per_source=self.max_bonds_per_source
        )
        return new_registry
