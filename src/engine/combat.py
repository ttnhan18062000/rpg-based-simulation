from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Tuple, Dict, Any
from dataclasses import replace, field
from src.core.updates import CombatUpdate, CombatIntent
from src.core.enums import EntityRole

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState

class CombatResolutionSystem:
    """
    Authoritative logic for combat interactions and outcomes.
    Matches legacy 'CombatInteractionService'.
    """
    
    # Rulebook Constants (Recovered from Legacy/Epic 17)
    HIGH_GROUND_BONUS = 0.20
    FLANKING_BONUS = 0.15
    COVER_REDUCTION = 0.30
    BOND_SYNERGY_BONUS = 0.10

    @staticmethod
    def calculate_damage(
        attacker: EntityState, 
        defender: EntityState,
        atk_mult: float = 1.0,
        def_mult: float = 1.0
    ) -> int:
        """
        Pillar 3: Fractional Armor Mitigation
        Formula: damage = (atk * atk_mult) * ((atk * atk_mult) / ((atk * atk_mult) + (def * def_mult) * 2.0 + 1.0))
        """
        atk = float(attacker.combat.atk) * atk_mult
        dfn = float(defender.combat.def_stat) * def_mult
        raw_damage = int(atk * (atk / (atk + dfn * 2.0 + 1.0)))
        return max(1, raw_damage)

    @staticmethod
    def resolve_attack(
        attacker: EntityState,
        defender: EntityState,
        state: AuthoritativeState,
        is_opportunity_attack: bool = False,
        is_lethal: bool = True
    ) -> CombatUpdate:
        """
        Core combat resolution logic with Tactical Modifiers.
        """
        from src.engine.legality import LegalityServiceV2
        
        # 0. Legality Check
        is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, defender, state, is_opportunity_attack=is_opportunity_attack)
        if not is_legal:
            return CombatUpdate(
                attacker_id=attacker.id,
                outcome_kind="REJECTED",
                failure_reason=reason
            )

        # 1. Evaluate Tactical Context
        atk_mult = 1.0
        def_mult = 1.0
        trace = {}
        
        if LegalityServiceV2.check_high_ground(attacker.position, defender.position, state):
            atk_mult += CombatResolutionSystem.HIGH_GROUND_BONUS
            trace["HIGH_GROUND"] = CombatResolutionSystem.HIGH_GROUND_BONUS
            
        if LegalityServiceV2.check_flanking(defender.id, state):
            atk_mult += CombatResolutionSystem.FLANKING_BONUS
            trace["FLANKING"] = CombatResolutionSystem.FLANKING_BONUS
            
        if LegalityServiceV2.check_cover(attacker.position, defender.position, state):
            def_mult += CombatResolutionSystem.COVER_REDUCTION
            trace["COVER_REDUCTION"] = CombatResolutionSystem.COVER_REDUCTION
            
        if defender.properties.get("status_frozen"):
            atk_mult *= 1.5
            trace["SHATTER"] = 1.5
            
        if attacker.biological.sleep_debt > 80.0:
            atk_mult *= 0.8
            trace["EXHAUSTION"] = 0.8
            
        for sid, bond in attacker.social.bonds.items():
            if bond.familiarity > 0.5:
                ally = state.entities.get(sid)
                if ally and ally.combat.alive and LegalityServiceV2.is_adjacent(attacker.position, ally.position):
                    atk_mult += CombatResolutionSystem.BOND_SYNERGY_BONUS
                    trace["BOND_SYNERGY"] = CombatResolutionSystem.BOND_SYNERGY_BONUS
                    break

        # 3. Calculate Damage
        damage = CombatResolutionSystem.calculate_damage(attacker, defender, atk_mult=atk_mult, def_mult=def_mult)
        trace["FINAL_ATK_MULT"] = atk_mult
        trace["FINAL_DEF_MULT"] = def_mult
        
        # 4. Determine Outcome
        new_hp = defender.combat.hp - damage
        outcome = "SURVIVE"
        alive = True
        xp_gain = 0
        gold_gain = 0
        gen_delta = 0
        perma_set = None
        
        if new_hp <= 0:
            outcome = "KILL" if is_lethal else "DEFEAT"
            alive = False
            
            if defender.identity.role == EntityRole.MONSTER:
                xp_gain = defender.identity.evolution_level * 10
                gold_gain = defender.identity.evolution_level * 5
            elif defender.identity.role == EntityRole.HERO:
                xp_gain = defender.identity.evolution_level * 20
                gold_gain = defender.identity.evolution_level * 50
                
                if defender.lifecycle.generation < 4:
                    gen_delta = 1
                    outcome = "REBIRTH"
                else:
                    perma_set = True
                    outcome = "PERMADEATH"

        return CombatUpdate(
            damage_taken=damage,
            hp_delta=-damage,
            attacker_id=attacker.id,
            is_opportunity_attack=is_opportunity_attack,
            alive_set=alive,
            outcome_kind=outcome,
            is_lethal=is_lethal,
            xp_gain=xp_gain,
            gold_gain=gold_gain,
            generation_delta=gen_delta,
            is_permadeath_set=perma_set,
            trace=trace
        )

    @staticmethod
    def resolve_opportunity_attack(
        attacker: EntityState,
        defender: EntityState,
        state: AuthoritativeState
    ) -> CombatUpdate:
        return CombatResolutionSystem.resolve_attack(
            attacker, defender, state, is_opportunity_attack=True, is_lethal=False
        )

    @staticmethod
    def resolve_multi_attack(
        attackers: List[EntityState],
        defender: EntityState,
        state: AuthoritativeState,
        is_opportunity_attack: bool = False,
        is_lethal: bool = True
    ) -> CombatUpdate:
        """
        Resolves multiple attackers hitting a single defender in the same tick.
        """
        from src.engine.legality import LegalityServiceV2
        
        intents = []
        total_damage = 0
        valid_attackers = []
        
        for attacker in attackers:
            # 0. Legality Check
            is_legal, _ = LegalityServiceV2.verify_attack_legality(attacker, defender, state, is_opportunity_attack=is_opportunity_attack)
            if not is_legal:
                continue
                
            damage = CombatResolutionSystem.calculate_damage(attacker, defender) 
            intents.append(CombatIntent(
                attacker_id=attacker.id,
                damage=damage,
                is_opportunity_attack=is_opportunity_attack,
                is_lethal=is_lethal
            ))
            total_damage += damage
            valid_attackers.append(attacker)

        if not intents:
            return CombatUpdate(
                outcome_kind="REJECTED",
                failure_reason="NO_LEGAL_ATTACKERS"
            )

        new_hp = defender.combat.hp - total_damage
        outcome = "SURVIVE"
        alive = True
        if new_hp <= 0:
            outcome = "KILL" if is_lethal else "DEFEAT"
            alive = False

        return CombatUpdate(
            damage_taken=total_damage,
            hp_delta=-total_damage,
            attacker_id=valid_attackers[0].id,
            is_opportunity_attack=is_opportunity_attack,
            alive_set=alive,
            outcome_kind=outcome,
            is_lethal=is_lethal,
            simultaneous_intents=intents
        )

    @staticmethod
    def resolve_aoe_attack(
        attacker: EntityState,
        target_pos: Tuple[float, float],
        radius: int,
        state: AuthoritativeState,
        defender: Optional[EntityState] = None,
        is_lethal: bool = True
    ) -> CombatUpdate:
        from src.core.updates import CombatIntent
        from src.engine.legality import LegalityServiceV2
        
        is_legal, reason = LegalityServiceV2.verify_aoe_legality(attacker, target_pos, state)
        if not is_legal:
            return CombatUpdate(
                attacker_id=attacker.id,
                outcome_kind="REJECTED",
                failure_reason=reason
            )
            
        damage = attacker.combat.atk
        hp_delta = 0
        if defender:
            is_def_legal, _ = LegalityServiceV2.verify_attack_legality(attacker, defender, state)
            if is_def_legal:
                atk_mult = 1.0
                if LegalityServiceV2.check_high_ground(attacker.position, defender.position, state):
                    atk_mult += CombatResolutionSystem.HIGH_GROUND_BONUS
                
                damage = CombatResolutionSystem.calculate_damage(attacker, defender, atk_mult=atk_mult)
                hp_delta = -damage
            else:
                defender = None
                hp_delta = 0
            
        return CombatUpdate(
            attacker_id=attacker.id,
            damage_taken=damage if defender else 0,
            hp_delta=hp_delta,
            outcome_kind="SURVIVE" if not defender or (defender.combat.hp + hp_delta > 0) else ("KILL" if is_lethal else "DEFEAT"),
            is_lethal=is_lethal,
            simultaneous_intents=[CombatIntent(
                attacker_id=attacker.id,
                damage=damage,
                is_lethal=is_lethal,
                splash_radius=radius,
                splash_damage=attacker.combat.atk // 2
            )]
        )
