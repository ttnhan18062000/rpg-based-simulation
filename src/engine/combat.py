from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Tuple, Dict, Any
from dataclasses import replace, field
from src.core.updates import CombatUpdate, CombatIntent, EquipmentUpdate
import logging

logger = logging.getLogger(__name__)
from src.core.enums import EntityRole, ReasonCode
from src.core.state import EquipSlot

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState

class CombatResolutionSystem:
    """
    Authoritative logic for combat interactions and outcomes.
    Matches legacy 'CombatInteractionService'.
    VERIFIED v2: combat
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
        VERIFIED v2: legacy_damage_parity
        """
        atk = float(attacker.combat.atk) * atk_mult
        dfn = float(defender.combat.def_stat) * def_mult
        raw_damage = int(atk * (atk / (atk + dfn * 2.0 + 1.0)))
        return max(1, raw_damage)

    @staticmethod
    def _get_tactical_multipliers(
        attacker: EntityState,
        defender: EntityState,
        state: AuthoritativeState,
        is_opportunity_attack: bool = False
    ) -> Tuple[float, float, Dict[str, float]]:
        """
        Calculates all tactical multipliers for an attack.
        Consolidated from resolve_attack for reuse.
        """
        from src.engine.legality import LegalityServiceV2
        
        atk_mult = 1.0
        def_mult = 1.0
        trace = {}
        
        if LegalityServiceV2.check_high_ground(attacker.navigation.position, defender.navigation.position, state):
            atk_mult += CombatResolutionSystem.HIGH_GROUND_BONUS
            trace["HIGH_GROUND"] = CombatResolutionSystem.HIGH_GROUND_BONUS
            
        is_flanked, is_surrounded = LegalityServiceV2.check_flanking(defender.id, state)
        if is_flanked:
            atk_mult += CombatResolutionSystem.FLANKING_BONUS
            trace["FLANKING"] = CombatResolutionSystem.FLANKING_BONUS
            
        if is_surrounded:
            # VERIFIED v2: RPG-COMBAT-200
            atk_mult += 0.25
            trace["SURROUNDED"] = 0.25
            
        if LegalityServiceV2.check_cover(attacker.navigation.position, defender.navigation.position, state):
            def_mult += CombatResolutionSystem.COVER_REDUCTION
            trace["COVER_REDUCTION"] = CombatResolutionSystem.COVER_REDUCTION
            
        if defender.identity.properties.get("status_frozen"):
            atk_mult *= 1.5
            trace["SHATTER"] = 1.5
            
        if attacker.biological.sleep_debt > 80.0:
            atk_mult *= 0.8
            trace["EXHAUSTION"] = 0.8
            
        # Stamina exhaustion penalty
        from src.engine.rpg_depth import StaminaService
        exhaust_mult = StaminaService.get_exhaustion_multiplier(attacker.stamina)
        if exhaust_mult < 1.0:
            atk_mult *= exhaust_mult
            trace["STAMINA_EXHAUSTION"] = exhaust_mult
            
        for sid, bond in attacker.social.bonds.items():
            if bond.familiarity > 0.5:
                ally = state.entities.get(sid)
                if ally and ally.combat.alive and LegalityServiceV2.is_adjacent(attacker.navigation.position, ally.navigation.position):
                    atk_mult += CombatResolutionSystem.BOND_SYNERGY_BONUS
                    trace["BOND_SYNERGY"] = CombatResolutionSystem.BOND_SYNERGY_BONUS
                    break
        
        return atk_mult, def_mult, trace

    @staticmethod
    def _get_durability_decay(attacker: EntityState, defender: EntityState) -> Tuple[Optional[EquipmentUpdate], Optional[EquipmentUpdate]]:
        """Phase 8: Calculate durability loss for attacker and defender."""
        attacker_equip_upd = None
        if attacker.equipment.slots.get(EquipSlot.MAIN_HAND):
            attacker_equip_upd = EquipmentUpdate(
                durability_delta={EquipSlot.MAIN_HAND: -1.0}
            )
            
        defender_equip_upd = None
        def_dur_deltas = {}
        for slot in (EquipSlot.TORSO, EquipSlot.LEGS, EquipSlot.HEAD):
            if defender.equipment.slots.get(slot):
                def_dur_deltas[slot] = -0.5
        if def_dur_deltas:
            defender_equip_upd = EquipmentUpdate(durability_delta=def_dur_deltas)
            
        return attacker_equip_upd, defender_equip_upd

    @staticmethod
    def resolve_attack(
        attacker: EntityState,
        defender: EntityState,
        state: AuthoritativeState,
        is_opportunity_attack: bool = False,
        is_lethal: bool = True
    ) -> CombatUpdate:
        is_lethal = is_lethal and (defender.identity.role != EntityRole.HERO)
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
        atk_mult, def_mult, trace = CombatResolutionSystem._get_tactical_multipliers(
            attacker, defender, state, is_opportunity_attack=is_opportunity_attack
        )

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
 
        # 5. Durability Decay (Phase 8)
        attacker_equip_upd, defender_equip_upd = CombatResolutionSystem._get_durability_decay(attacker, defender)

        # 6. Wound Infliction
        wound_upd = CombatResolutionSystem._get_wound_infliction(attacker, defender, damage, state.tick, alive)
        if wound_upd:
            trace["WOUND_INFLICTED"] = 1.0

        # 7. Social Consequences
        from src.core.updates import SocialUpdate, SocialBondUpdate
        social_upd = SocialUpdate(
            bond_updates=[SocialBondUpdate(target_id=attacker.id, sentiment_delta=-0.1, familiarity_delta=0.05)],
            grudge_delta={attacker.id: damage / defender.combat.max_hp}
        )

        # 8. Generate Resource Intents
        from src.core.updates import ResourceTransferIntent
        resource_transfers = []
        if not alive and defender.combat.alive:
             resource_transfers.append(ResourceTransferIntent(
                 source_id=defender.id, source_kind="COMBAT",
                 xp_reward=xp_gain,
                 transfer_kind="KILL_REWARD",
                 is_group_required=False
             ))
             if gold_gain > 0:
                 resource_transfers.append(ResourceTransferIntent(
                     source_id=defender.id, source_kind="COMBAT",
                     gold_delta=gold_gain,
                     transfer_kind="KILL_REWARD",
                     is_group_required=True
                 ))

        return CombatUpdate(
            damage_taken=damage,
            hp_delta=-damage,
            attacker_id=attacker.id,
            is_opportunity_attack=is_opportunity_attack,
            alive_set=alive,
            outcome_kind=outcome,
            is_lethal=is_lethal,
            generation_delta=gen_delta,
            is_permadeath_set=perma_set,
            equipment_upd=defender_equip_upd,
            attacker_equipment_upd=attacker_equip_upd,
            wound_update=wound_upd,
            social_upd=social_upd,
            resource_transfers=resource_transfers,
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
    def resolve_skill_usage(
        attacker: EntityState,
        defender: EntityState,
        state: AuthoritativeState,
        damage: int,
        is_lethal: bool = True
    ) -> CombatUpdate:
        from src.engine.legality import LegalityServiceV2
        
        is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, defender, state)
        if not is_legal:
            return CombatUpdate(outcome_kind="REJECTED", failure_reason=reason)

        new_hp = defender.combat.hp - damage
        outcome = "SURVIVE"
        alive = True
        if new_hp <= 0:
            outcome = "KILL" if is_lethal else "DEFEAT"
            alive = False
            
        xp_gain = 0
        gold_gain = 0
        if not alive:
            if defender.identity.role == EntityRole.MONSTER:
                xp_gain = 10 * defender.identity.evolution_level
                gold_gain = 5 * defender.identity.evolution_level

        attacker_equip_upd, defender_equip_upd = CombatResolutionSystem._get_durability_decay(attacker, defender)
        wound_upd = CombatResolutionSystem._get_wound_infliction(attacker, defender, damage, state.tick, alive)

        from src.core.updates import SocialUpdate, SocialBondUpdate
        social_upd = SocialUpdate(
            bond_updates=[SocialBondUpdate(target_id=attacker.id, sentiment_delta=-0.1, familiarity_delta=0.05)],
            grudge_delta={attacker.id: damage / defender.combat.max_hp}
        )

        from src.core.updates import ResourceTransferIntent
        resource_transfers = []
        if not alive and defender.combat.alive:
              resource_transfers.append(ResourceTransferIntent(
                  source_id=defender.id, source_kind="COMBAT",
                  xp_reward=xp_gain,
                  transfer_kind="KILL_REWARD",
                  is_group_required=False
              ))
              if gold_gain > 0:
                  resource_transfers.append(ResourceTransferIntent(
                      source_id=defender.id, source_kind="COMBAT",
                      gold_delta=gold_gain,
                      transfer_kind="KILL_REWARD",
                      is_group_required=True
                  ))

        return CombatUpdate(
            damage_taken=damage,
            hp_delta=-damage,
            attacker_id=attacker.id,
            outcome_kind=outcome,
            alive_set=alive,
            equipment_upd=defender_equip_upd,
            attacker_equipment_upd=attacker_equip_upd,
            wound_update=wound_upd,
            social_upd=social_upd,
            resource_transfers=resource_transfers
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
        Now correctly incorporates tactical bonuses for each attacker.
        """
        from src.engine.legality import LegalityServiceV2
        
        intents = []
        total_damage = 0
        valid_attackers = []
        full_trace = {}
        
        for attacker in attackers:
            # 0. Legality Check
            is_legal, _ = LegalityServiceV2.verify_attack_legality(attacker, defender, state, is_opportunity_attack=is_opportunity_attack)
            if not is_legal:
                continue
                
            # 1. Tactical Multipliers
            atk_mult, def_mult, trace = CombatResolutionSystem._get_tactical_multipliers(
                attacker, defender, state, is_opportunity_attack=is_opportunity_attack
            )
            
            # 2. Damage Calculation
            damage = CombatResolutionSystem.calculate_damage(attacker, defender, atk_mult=atk_mult, def_mult=def_mult)
            
            intents.append(CombatIntent(
                attacker_id=attacker.id,
                damage=damage,
                is_opportunity_attack=is_opportunity_attack,
                is_lethal=is_lethal
            ))
            total_damage += damage
            valid_attackers.append(attacker)
            
            # Aggregate traces
            for k, v in trace.items():
                full_trace[f"{attacker.id}_{k}"] = v

        if not intents:
            return CombatUpdate(
                outcome_kind="REJECTED",
                failure_reason=ReasonCode.TARGET_INVALID
            )

        new_hp = defender.combat.hp - total_damage
        outcome = "SURVIVE"
        alive = True
        if new_hp <= 0:
            outcome = "KILL" if is_lethal else "DEFEAT"
            alive = False

        xp_gain = 0
        gold_gain = 0
        resource_transfers = []
        if not alive and defender.combat.alive:
             if defender.identity.role == EntityRole.MONSTER:
                xp_gain = defender.identity.evolution_level * 10
                gold_gain = defender.identity.evolution_level * 5
             elif defender.identity.role == EntityRole.HERO:
                xp_gain = defender.identity.evolution_level * 20
                gold_gain = defender.identity.evolution_level * 50
                
             from src.core.updates import ResourceTransferIntent
             resource_transfers.append(ResourceTransferIntent(
                 source_id=defender.id, source_kind="COMBAT",
                 xp_reward=xp_gain,
                 transfer_kind="KILL_REWARD",
                 is_group_required=False
             ))
             if gold_gain > 0:
                 resource_transfers.append(ResourceTransferIntent(
                     source_id=defender.id, source_kind="COMBAT",
                     gold_delta=gold_gain,
                     transfer_kind="KILL_REWARD",
                     is_group_required=True
                 ))

        # Social Consequences (Multi-attacker)
        from src.core.updates import SocialUpdate, SocialBondUpdate
        bond_ups = []
        grudges = {}
        for attacker in valid_attackers:
            bond_ups.append(SocialBondUpdate(target_id=attacker.id, sentiment_delta=-0.1, familiarity_delta=0.05))
            grudges[attacker.id] = (total_damage / len(valid_attackers)) / defender.combat.max_hp
            
        social_upd = SocialUpdate(bond_updates=bond_ups, grudge_delta=grudges)

        return CombatUpdate(
            damage_taken=total_damage,
            hp_delta=-total_damage,
            attacker_id=valid_attackers[0].id,
            is_opportunity_attack=is_opportunity_attack,
            alive_set=alive,
            outcome_kind=outcome,
            is_lethal=is_lethal,
            simultaneous_intents=intents,
            social_upd=social_upd,
            resource_transfers=resource_transfers,
            trace=full_trace
        )

    @staticmethod
    def resolve_aoe_attack(
        attacker: EntityState,
        target_pos: Tuple[float, float],
        radius: int,
        state: AuthoritativeState,
        defender: Optional[EntityState] = None,
        is_lethal: bool = True
    ) -> Dict[int, CombatUpdate]:
        from src.core.updates import CombatIntent, ResourceTransferIntent, SocialUpdate, SocialBondUpdate
        from src.engine.legality import LegalityServiceV2
        
        is_legal, reason = LegalityServiceV2.verify_aoe_legality(attacker, target_pos, state)
        if not is_legal:
            return {attacker.id: CombatUpdate(
                attacker_id=attacker.id,
                outcome_kind="REJECTED",
                failure_reason=reason
            )}
            
        updates: Dict[int, CombatUpdate] = {}
        all_transfers = []
        
        # 1. Primary Target
        primary_damage = 0
        if defender:
            is_def_legal, _ = LegalityServiceV2.verify_attack_legality(attacker, defender, state)
            if is_def_legal:
                primary_damage = CombatResolutionSystem.calculate_damage(attacker, defender)
                new_hp = defender.combat.hp - primary_damage
                is_kill = new_hp <= 0
                
                att_dur, def_dur = CombatResolutionSystem._get_durability_decay(attacker, defender)
                
                social_up = SocialUpdate(
                    bond_updates=[SocialBondUpdate(target_id=attacker.id, sentiment_delta=-0.1, familiarity_delta=0.05)],
                    grudge_delta={attacker.id: primary_damage / defender.combat.max_hp}
                )

                updates[defender.id] = CombatUpdate(
                    attacker_id=attacker.id,
                    damage_taken=primary_damage,
                    hp_delta=-primary_damage,
                    alive_set=not is_kill,
                    outcome_kind="KILL" if is_kill and is_lethal else ("DEFEAT" if is_kill else "SURVIVE"),
                    is_lethal=is_lethal,
                    equipment_upd=def_dur,
                    social_upd=social_up,
                    wound_update=CombatResolutionSystem._get_wound_infliction(attacker, defender, primary_damage, state.tick, not is_kill)
                )
                
                if is_kill:
                    all_transfers.append(ResourceTransferIntent(
                        source_id=defender.id, source_kind="COMBAT",
                        xp_reward=defender.identity.evolution_level * 10,
                        transfer_kind="KILL_REWARD",
                        is_group_required=False
                    ))
                    all_transfers.append(ResourceTransferIntent(
                        source_id=defender.id, source_kind="COMBAT",
                        gold_delta=defender.identity.evolution_level * 5,
                        transfer_kind="KILL_REWARD",
                        is_group_required=True
                    ))
            else:
                defender = None

        # 2. Splash Victims
        splash_damage = attacker.combat.atk // 2
        splash_intents = []
        
        victim_ids = sorted(list(state.entities.keys()))
        for other_id in victim_ids:
            other_ent = state.entities[other_id]
            if other_id == attacker.id: continue
            if defender and other_id == defender.id: continue
            
            dist = LegalityServiceV2.get_manhattan_dist(target_pos, other_ent.navigation.position)
            if dist <= radius:
                if attacker.identity.faction == other_ent.identity.faction:
                    continue

                if LegalityServiceV2.has_line_of_sight(target_pos, other_ent.navigation.position, state):
                    v_damage = max(1, splash_damage)
                    new_hp = other_ent.combat.hp - v_damage
                    is_kill = new_hp <= 0
                    
                    _, def_dur = CombatResolutionSystem._get_durability_decay(attacker, other_ent)

                    social_up = SocialUpdate(
                        bond_updates=[SocialBondUpdate(target_id=attacker.id, sentiment_delta=-0.05, familiarity_delta=0.02)],
                        grudge_delta={attacker.id: v_damage / other_ent.combat.max_hp}
                    )

                    updates[other_id] = CombatUpdate(
                        attacker_id=attacker.id,
                        damage_taken=v_damage,
                        hp_delta=-v_damage,
                        alive_set=not is_kill,
                        outcome_kind="KILL" if is_kill and is_lethal else ("DEFEAT" if is_kill else "SURVIVE"),
                        is_lethal=is_lethal,
                        equipment_upd=def_dur,
                        social_upd=social_up,
                        wound_update=CombatResolutionSystem._get_wound_infliction(attacker, other_ent, v_damage, state.tick, not is_kill)
                    )
                    
                    splash_intents.append(CombatIntent(
                        attacker_id=attacker.id,
                        damage=v_damage,
                        is_lethal=is_lethal,
                        impact_pos=other_ent.navigation.position
                    ))
                    
                    if is_kill and other_ent.combat.alive:
                        all_transfers.append(ResourceTransferIntent(
                            source_id=other_id, source_kind="COMBAT",
                            xp_reward=other_ent.identity.evolution_level * 10,
                            transfer_kind="KILL_REWARD",
                            is_group_required=False
                        ))
                        all_transfers.append(ResourceTransferIntent(
                            source_id=other_id, source_kind="COMBAT",
                            gold_delta=other_ent.identity.evolution_level * 5,
                            transfer_kind="KILL_REWARD",
                            is_group_required=True
                        ))

        # 3. Attacker Update
        updates[attacker.id] = CombatUpdate(
            attacker_id=attacker.id,
            outcome_kind="SUCCESS",
            simultaneous_intents=[CombatIntent(
                attacker_id=attacker.id,
                damage=primary_damage,
                is_lethal=is_lethal,
                splash_radius=radius,
                splash_damage=splash_damage,
                impact_pos=target_pos
            )] + splash_intents,
            attacker_equipment_upd=CombatResolutionSystem._get_durability_decay(attacker, attacker)[0],
            resource_transfers=all_transfers
        )
        
        return updates

    @staticmethod
    def _get_wound_infliction(attacker: EntityState, defender: EntityState, damage: float, tick: int, alive: bool) -> Optional[WoundUpdate]:
        """Calculates and returns a WoundUpdate if damage is sufficient."""
        if damage > defender.combat.max_hp * 0.25 and alive:
            from src.core.state import WoundState
            from src.core.updates import WoundUpdate
            from src.core.enums import EntityRole
            w_id = f"w_{attacker.id}_{defender.id}_{tick}"
            penalty = 5.0
            wound = WoundState(
                id=w_id,
                kind="SLASH" if attacker.identity.role == EntityRole.HERO else "CRUSH",
                severity=damage / defender.combat.max_hp,
                tick_inflicted=tick,
                atk_penalty=penalty,
                def_penalty=penalty
            )
            return WoundUpdate(wounds_add=[wound])
        return None
