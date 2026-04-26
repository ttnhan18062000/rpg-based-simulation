from typing import TYPE_CHECKING
from src_legacy.api.schemas import StatBreakdownSchema, StatSourceSchema

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity

class StatBreakdownService:
    """Explains how combat stats are derived from base, attributes, and effects."""

    @staticmethod
    def get_breakdown(entity: "Entity", stat_name: str) -> StatBreakdownSchema:
        combat = entity.combat
        prog = entity.progression
        attrs = prog.attributes
        
        # Hardcoded True Bases (from EntityBuilder defaults)
        # In a real system, these would come from a Kind Template Registry
        TRUE_BASES = {
            "atk": 5,
            "def": 0,
            "spd": 10,
            "luck": 0,
            "crit_rate": 0.05,
            "evasion": 0.0,
            "max_hp": 20,
            "matk": 5,
            "mdef": 0
        }
        
        base = TRUE_BASES.get(stat_name, 0)
        sources = []
        
        # 1. Attribute Contribution
        if attrs:
            from src_legacy.core.gameplay.attributes import (
                derive_atk, derive_def, derive_spd, derive_crit_rate, 
                derive_evasion, derive_luck, derive_max_hp, derive_matk, derive_mdef
            )
            
            attr_val = 0
            if stat_name == "atk": attr_val = derive_atk(0, attrs.str_)
            elif stat_name == "def": attr_val = derive_def(0, attrs.vit)
            elif stat_name == "spd": attr_val = derive_spd(0, attrs.agi)
            elif stat_name == "crit_rate": attr_val = derive_crit_rate(0.0, attrs.agi, attrs.wis)
            elif stat_name == "evasion": attr_val = derive_evasion(0.0, attrs.agi)
            elif stat_name == "luck": attr_val = derive_luck(0, attrs.wis)
            elif stat_name == "max_hp": attr_val = derive_max_hp(0, attrs.vit, attrs.end)
            elif stat_name == "matk": attr_val = derive_matk(0, attrs.spi, attrs.int_)
            elif stat_name == "mdef": attr_val = derive_mdef(0, attrs.wis, attrs.spi)
            
            if attr_val > 0:
                sources.append(StatSourceSchema(source_name="Attributes", flat_bonus=int(attr_val)))

        # 2. Trait Milestones (e.g. str_25)
        traits = entity.identity.traits
        trait_mult = 1.0
        if stat_name == "atk" and ("str_25" in traits): trait_mult = 1.1
        if stat_name == "max_hp" and ("vit_25" in traits): trait_mult = 1.1
        if stat_name == "spd" and ("agi_25" in traits): trait_mult = 1.1
        
        if trait_mult > 1.0:
            sources.append(StatSourceSchema(source_name="Traits", mult_bonus=trait_mult))

        # 3. Active Effects
        effect_mult = 1.0
        for eff in combat.effects:
            m = 1.0
            if stat_name == "atk": m = getattr(eff, "atk_mult", 1.0)
            elif stat_name == "def": m = getattr(eff, "def_mult", 1.0)
            elif stat_name == "spd": m = getattr(eff, "spd_mult", 1.0)
            elif stat_name == "crit_rate": m = getattr(eff, "crit_mult", 1.0)
            elif stat_name == "evasion": m = getattr(eff, "evasion_mult", 1.0)
            
            if m != 1.0:
                effect_mult *= m
                sources.append(StatSourceSchema(source_name=f"Effect: {eff.source}", mult_bonus=m))

        # Final calculated value
        final = getattr(combat, stat_name if stat_name != "def" else "def_")
        
        return StatBreakdownSchema(
            stat_name=stat_name,
            final_value=float(final),
            base_value=float(base),
            sources=sources
        )

    @staticmethod
    def get_all_breakdowns(entity: "Entity") -> dict[str, StatBreakdownSchema]:
        stats = ["atk", "def", "spd", "luck", "crit_rate", "evasion", "max_hp", "matk", "mdef"]
        return {s: StatBreakdownService.get_breakdown(entity, s) for s in stats}
