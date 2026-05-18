from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING
import hashlib

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState

class StateFingerprinter:
    """
    Produces deterministic, domain-specific fingerprints for authoritative state.
    Used for lightweight runtime stability guards and parity verification.
    """

    @staticmethod
    def get_fingerprint(state: AuthoritativeState) -> Dict[str, Any]:
        """
        Produce a deterministic fingerprint of the current state.
        Includes identity, spatial, resources, and world dynamics.
        """
        # 1. Identity & Spatial (Sorted by ID)
        # We use a summarized string for speed, but detailed enough to catch divergence.
        entity_parts = []
        for eid in sorted(state.entities.keys()):
            ent = state.entities[eid]
            # Include: ID, Kind, Position, HP, Gold, Current Project, Project Count, Skills Count
            entity_parts.append(
                f"{eid}:{ent.kind}:{ent.position}:{ent.combat.hp}:"
                f"{ent.inventory.gold}:{ent.strategic.current_project_id}:"
                f"{len(ent.strategic.projects)}:{len(ent.identity.learned_skills)}"
            )
        entity_ident = "|".join(entity_parts)
        
        # 2. Resources & Dynamics
        resource_ident = "|".join(f"{k}:{v}" for k, v in sorted(state.global_resources.items()))
        
        region_parts = []
        for rid in sorted(state.regions.keys()):
            r = state.regions[rid]
            region_parts.append(f"{rid}:{r.owner_faction_id}:{r.influence}:{r.hazard_level}")
        region_ident = "|".join(region_parts)
        
        scar_ident = "|".join(f"{sid}:{s.severity}" for sid, s in sorted(state.local_scars.items()))
        
        # 3. Macro state
        macro_ident = f"{state.maturity}:{state.last_calamity_tick}:{state.movement_count}"
        
        # 4. Combine into hash
        raw_data = f"{state.seed}|{entity_ident}|{resource_ident}|{region_ident}|{scar_ident}|{macro_ident}"
        state_hash = hashlib.md5(raw_data.encode()).hexdigest()
        
        return {
            "state_hash": state_hash,
            "tick": state.tick,
            "seed": state.seed,
            "entity_count": len(state.entities),
            "resource_count": len(state.global_resources),
            "maturity": state.maturity
        }
