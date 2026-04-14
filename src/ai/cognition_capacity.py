from __future__ import annotations
from typing import TYPE_CHECKING, Any
from src.core.models.base import SimulationModel

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

from src.core.models.cognition import CognitionCapacityProfile

def _clamp(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value

def _norm_attr(value: int, cap: int) -> float:
    if cap <= 1:
        return 0.0
    return _clamp((value - 1) / (cap - 1), 0.0, 1.0)

def _stamina_ratio(stamina: int, max_stamina: int) -> float:
    if max_stamina <= 0:
        return 1.0
    return _clamp(stamina / max_stamina, 0.0, 1.0)

def _fatigue_penalty(stamina_ratio: float) -> float:
    return 1.0 - stamina_ratio

class CognitionCapacityBuilder:
    """Deterministic builder for deriving CognitionCapacityProfile from entity state."""
    
    @staticmethod
    def build(entity: Entity, tick: int = 0) -> CognitionCapacityProfile:
        """Derive a profile from authoritative entity inputs.
        
        Purity Requirements:
        - Non-mutating
        - Independent of RNG
        - Purely deterministic based on input attributes and stamina
        """
        prog = entity.progression
        attrs = prog.attributes
        caps = prog.attribute_caps
        
        # Exact Fallbacks
        int_ = getattr(attrs, "int_", 1)
        wis = getattr(attrs, "wis", 1)
        per = getattr(attrs, "per", 1)
        cha = getattr(attrs, "cha", 1)
        
        int_cap = getattr(caps, "int_cap", 15)
        wis_cap = getattr(caps, "wis_cap", 15)
        per_cap = getattr(caps, "per_cap", 15)
        cha_cap = getattr(caps, "cha_cap", 15)
        
        stamina = getattr(prog, "stamina", 1)
        max_stamina = getattr(prog, "max_stamina", 1)
        
        # Computed Intermediate values
        n_int = _norm_attr(int_, int_cap)
        n_wis = _norm_attr(wis, wis_cap)
        n_per = _norm_attr(per, per_cap)
        n_cha = _norm_attr(cha, cha_cap)
        sr = _stamina_ratio(stamina, max_stamina)
        fatigue = _fatigue_penalty(sr)
        
        # Exact Formulas
        profile_data = {
            "planning_budget": int(round(_clamp(3.0 + 5.0 * n_int + 1.0 * n_wis, 3.0, 9.0))),
            "judgment_stability": round(_clamp(0.35 + 0.45 * n_wis + 0.10 * n_int - 0.20 * fatigue, 0.10, 0.95), 3),
            "evidence_quality": round(_clamp(0.30 + 0.50 * n_per + 0.10 * n_wis + 0.05 * n_int - 0.20 * fatigue, 0.10, 0.95), 3),
            "social_bandwidth": int(round(_clamp(2.0 + 4.0 * n_cha + 1.0 * n_wis, 2.0, 7.0))),
            "detour_depth_limit": int(round(_clamp(1.0 + 2.0 * n_int + 1.0 * n_wis, 1.0, 4.0))),
            "active_slice_limit": int(round(_clamp(3.0 + 4.0 * n_int + 2.0 * n_wis, 3.0, 9.0))),
            "concern_intake_limit": int(round(_clamp(2.0 + 2.0 * n_wis + 1.0 * n_int, 2.0, 5.0))),
            "lead_retention_limit": int(round(_clamp(2.0 + 3.0 * n_per + 2.0 * n_int, 2.0, 7.0))),
            "candidate_zone_limit": int(round(_clamp(1.0 + 3.0 * n_per + 1.0 * n_int, 1.0, 5.0))),
            "ally_evaluation_limit": int(round(_clamp(2.0 + 4.0 * n_cha + 1.0 * n_wis, 2.0, 7.0))),
            "blocker_resolution_patience": round(_clamp(0.30 + 0.35 * n_int + 0.25 * n_wis - 0.20 * fatigue, 0.10, 0.95), 3),
            "resume_reliability": round(_clamp(0.25 + 0.35 * n_int + 0.25 * n_wis + 0.10 * n_per - 0.20 * fatigue, 0.10, 0.95), 3),
            "interruption_resistance": round(_clamp(0.20 + 0.45 * n_wis + 0.15 * n_int - 0.15 * fatigue, 0.05, 0.95), 3),
            "abandonment_threshold_mod": round(_clamp(0.80 + 0.30 * n_wis - 0.10 * fatigue, 0.60, 1.20), 3),
            "contradiction_sensitivity": round(_clamp(0.20 + 0.50 * n_per + 0.10 * n_wis, 0.10, 0.90), 3),
            "source_trust_learning_rate": round(_clamp(0.10 + 0.35 * n_per + 0.20 * n_wis + 0.10 * n_cha, 0.05, 0.85), 3),
        }
        
        return CognitionCapacityProfile(**profile_data)
