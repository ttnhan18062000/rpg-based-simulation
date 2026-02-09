"""CombatAction — validates and resolves attack proposals.

Damage calculation uses effective stats (base + equipment + status effects),
so territory debuffs and other effects are automatically applied without
any special-case code here.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.core.enums import ActionType, Domain

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.world_state import WorldState
    from src.systems.rng import DeterministicRNG

logger = logging.getLogger(__name__)


class CombatAction:
    """Stateless handler for ATTACK proposals."""

    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._rng = rng

    def validate(self, proposal: ActionProposal, world: WorldState) -> bool:
        if proposal.verb != ActionType.ATTACK:
            return False

        attacker = world.entities.get(proposal.actor_id)
        if attacker is None or not attacker.alive:
            return False

        target_id: int = proposal.target
        defender = world.entities.get(target_id)
        if defender is None or not defender.alive:
            logger.debug(
                "Entity %d attack on %s failed — target dead or missing",
                proposal.actor_id,
                target_id,
            )
            return False

        # Must be adjacent (Manhattan distance 1)
        if attacker.pos.manhattan(defender.pos) > 1:
            logger.debug("Entity %d attack on %d failed — out of range", proposal.actor_id, target_id)
            return False

        return True

    def apply(self, proposal: ActionProposal, world: WorldState) -> None:
        attacker = world.entities.get(proposal.actor_id)
        target_id: int = proposal.target
        defender = world.entities.get(target_id)
        if attacker is None or defender is None:
            return

        tick = world.tick
        cfg = self._config

        # --- Evasion check ---
        defender_evasion = defender.effective_evasion()
        luck_mod = attacker.stats.luck * 0.002
        effective_evasion = max(0.0, defender_evasion - luck_mod)
        if self._rng.next_bool(Domain.COMBAT, defender.id, tick + 3, effective_evasion):
            logger.info(
                "Tick %d: Entity %d (%s) attack EVADED by Entity %d (%s)",
                tick, attacker.id, attacker.kind, defender.id, defender.kind,
            )
            attacker.next_act_at += 1.0 / max(attacker.effective_spd(), 1)
            return

        # --- Damage calculation (attribute-enhanced) ---
        # effective_atk / effective_def already include equipment AND status effects
        atk_power = attacker.effective_atk()
        def_power = defender.effective_def()

        # Attribute multipliers (STR boosts attack, VIT boosts defense)
        str_mult = 1.0
        vit_mult = 1.0
        if attacker.attributes:
            str_mult = 1.0 + attacker.attributes.str_ * 0.02
        if defender.attributes:
            vit_mult = 1.0 + defender.attributes.vit * 0.01

        # Base damage = ATK * str_mult - DEF * vit_mult / 2 (min 1), with variance
        variance = self._rng.next_float(Domain.COMBAT, attacker.id, tick)
        raw_damage = int(atk_power * str_mult) - int(def_power * vit_mult) // 2
        raw_damage = max(raw_damage, 1)
        damage = int(raw_damage * (1.0 + cfg.damage_variance * (variance - 0.5)))
        damage = max(damage, 1)

        # --- Crit check ---
        crit_rate = attacker.effective_crit_rate()
        crit_rate += attacker.stats.luck * 0.003
        is_crit = self._rng.next_bool(Domain.COMBAT, attacker.id, tick + 1, min(crit_rate, 0.8))
        if is_crit:
            damage = int(damage * attacker.stats.crit_dmg)

        defender.stats.hp -= damage
        logger.info(
            "Tick %d: Entity %d (%s Lv%d) hits Entity %d (%s Lv%d) for %d%s damage [HP: %d/%d]",
            tick,
            attacker.id, attacker.kind, attacker.stats.level,
            defender.id, defender.kind, defender.stats.level,
            damage,
            " CRIT!" if is_crit else "",
            max(defender.stats.hp, 0),
            defender.stats.max_hp,
        )

        attacker.next_act_at += 1.0 / max(attacker.effective_spd(), 1)

        # --- Stamina cost for attacking ---
        attacker.stats.stamina = max(0, attacker.stats.stamina - 3)

        # --- Attribute training from combat ---
        if attacker.attributes and attacker.attribute_caps:
            from src.core.attributes import train_attributes
            train_attributes(attacker.attributes, attacker.attribute_caps, "attack")
        if defender.attributes and defender.attribute_caps and defender.alive:
            from src.core.attributes import train_attributes
            train_attributes(defender.attributes, defender.attribute_caps, "defend")

        # --- XP award on kill ---
        if not defender.alive:
            xp_gain = self._calculate_xp(attacker, defender, cfg)
            # Apply XP multiplier from INT/WIS
            if attacker.attributes:
                from src.core.attributes import derive_xp_multiplier
                xp_gain = int(xp_gain * derive_xp_multiplier(
                    attacker.attributes.int_, attacker.attributes.wis))
            attacker.stats.xp += xp_gain
            attacker.stats.gold += defender.stats.gold
            defender.stats.gold = 0
            logger.info(
                "Tick %d: Entity %d (%s) gained %d XP from killing Entity %d (%s) [XP: %d/%d]",
                tick, attacker.id, attacker.kind, xp_gain,
                defender.id, defender.kind,
                attacker.stats.xp, attacker.stats.xp_to_next,
            )
            # --- Quest progress: HUNT ---
            if attacker.quests:
                from src.core.quests import QuestType
                for q in attacker.quests:
                    if q.quest_type == QuestType.HUNT and not q.completed:
                        if q.target_kind == defender.kind:
                            just_done = q.advance()
                            if just_done:
                                attacker.stats.gold += q.gold_reward
                                attacker.stats.xp += q.xp_reward
                                logger.info(
                                    "Tick %d: Entity %d completed quest '%s' → +%d gold, +%d XP",
                                    tick, attacker.id, q.title,
                                    q.gold_reward, q.xp_reward,
                                )

    @staticmethod
    def _calculate_xp(attacker, defender, cfg) -> int:
        """XP = base * defender_level * scale, bonus for higher-tier enemies."""
        base = cfg.xp_per_kill_base
        level_mult = max(1, defender.stats.level)
        tier_bonus = 1.0 + defender.tier * 0.5
        xp = int(base * level_mult * tier_bonus)
        return max(xp, 1)
