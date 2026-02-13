"""WorldLoop — the authoritative 4-phase tick engine.

Phase cycle:
  1. Scheduling — identify ready entities, dispatch to workers
  2. Wait & Collect — drain the action queue
  3. Conflict Resolution & Application — validate + apply proposals
  4. Cleanup & Advancement — remove dead, territory effects, advance tick
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from src.core.effects import EffectType, territory_debuff
from src.core.enums import AIState, ActionType, Domain
from src.core.faction import Faction, FactionRegistry
from src.core.items import ITEM_REGISTRY
from src.core.snapshot import Snapshot
from src.engine.action_queue import ActionQueue
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.systems.generator import EntityGenerator

if TYPE_CHECKING:
    from src.actions.base import ActionProposal
    from src.config import SimulationConfig
    from src.core.world_state import WorldState
    from src.systems.rng import DeterministicRNG
    from src.utils.replay import ReplayRecorder

logger = logging.getLogger(__name__)


class WorldLoop:
    """The heartbeat of the simulation.

    Single-threaded mutation of WorldState through a 4-phase cycle:
      1. Scheduling — identify ready entities, dispatch to workers
      2. Wait & Collect — drain the action queue
      3. Conflict Resolution & Application — validate + apply proposals
      4. Cleanup & Advancement — remove dead, territory effects, advance tick
    """

    __slots__ = (
        "_config",
        "_world",
        "_action_queue",
        "_worker_pool",
        "_conflict_resolver",
        "_generator",
        "_recorder",
        "_last_applied",
        "_tick_events",
        "_faction_reg",
        "_rng",
    )

    def __init__(
        self,
        config: SimulationConfig,
        world: WorldState,
        worker_pool: WorkerPool,
        conflict_resolver: ConflictResolver,
        generator: EntityGenerator,
        recorder: ReplayRecorder | None = None,
        faction_reg: FactionRegistry | None = None,
        rng: DeterministicRNG | None = None,
    ) -> None:
        self._config = config
        self._world = world
        self._action_queue = ActionQueue()
        self._worker_pool = worker_pool
        self._conflict_resolver = conflict_resolver
        self._generator = generator
        self._recorder = recorder
        self._last_applied: list[ActionProposal] = []
        self._tick_events: list = []
        self._faction_reg = faction_reg or FactionRegistry.default()
        self._rng = rng

    @property
    def world(self) -> WorldState:
        return self._world

    @property
    def last_applied(self) -> list[ActionProposal]:
        """Actions applied during the most recent tick."""
        return self._last_applied

    @property
    def tick_events(self) -> list:
        """Enriched events emitted during the most recent tick."""
        return self._tick_events

    def _emit(self, category: str, message: str,
              entity_ids: tuple[int, ...] = (), metadata: dict | None = None) -> None:
        from src.utils.event_log import SimEvent
        self._tick_events.append(SimEvent(
            tick=self._world.tick,
            category=category,
            message=message,
            entity_ids=entity_ids,
            metadata=metadata,
        ))

    def tick_once(self) -> bool:
        """Execute a single tick. Returns False if simulation should stop."""
        tick = self._world.tick
        alive_count = sum(1 for e in self._world.entities.values() if e.alive and e.kind != "generator")

        if alive_count == 0 and tick > 0:
            logger.info("Tick %d: No entities alive — simulation ended.", tick)
            return False

        if tick >= self._config.max_ticks:
            logger.info("Tick %d: Max ticks reached.", tick)
            return False

        self._step()
        self._world.tick += 1
        return True

    def create_snapshot(self) -> Snapshot:
        """Create an immutable snapshot of the current world state."""
        return Snapshot.from_world(self._world)

    def run(self) -> None:
        """Execute the simulation until max_ticks or no entities remain."""
        logger.info("=== Simulation started (seed=%d) ===", self._world.seed)

        self._world.tick = 0
        while self._world.tick < self._config.max_ticks:
            if not self.tick_once():
                break

            if self._world.tick % 50 == 0:
                alive_count = sum(1 for e in self._world.entities.values() if e.alive and e.kind != "generator")
                logger.info(
                    "Tick %d: %d entities alive",
                    self._world.tick,
                    alive_count,
                )

        logger.info("=== Simulation finished at tick %d ===", self._world.tick)
        if self._recorder:
            self._recorder.flush()

    def _step(self) -> None:
        """Execute one complete tick cycle.

        Two phases:
        1. **Action phase** — only when entities are ready (schedule → collect → resolve → apply)
        2. **Subsystem phase** — always runs, with configurable rate divisors (design-02)
        """
        self._tick_events = []
        tick = self._world.tick
        t0 = time.perf_counter()

        # --- Phase 1: Scheduling ---
        self._phase_generators()
        ready_entities = self._phase_scheduling()

        applied: list = []
        t1 = t2 = t3 = t0

        if ready_entities:
            t1 = time.perf_counter()

            # --- Phase 2: Wait & Collect ---
            snapshot = Snapshot.from_world(self._world)
            self._worker_pool.dispatch(ready_entities, snapshot, self._action_queue)
            proposals = self._action_queue.drain()

            t2 = time.perf_counter()

            # --- Phase 3: Conflict Resolution & Application ---
            # Capture positions before resolution for opportunity attack detection
            pre_positions = {e.id: (e.pos.x, e.pos.y) for e in self._world.entities.values()}
            applied = self._conflict_resolver.resolve(proposals, self._world)
            self._last_applied = applied

            # Opportunity attacks on melee disengage (epic-05)
            self._process_opportunity_attacks(applied, pre_positions)

            # SPD-based chase closing (epic-05)
            self._process_chase_closing()

            # Emit base events for all applied actions
            _cat_map = {
                "REST": "rest", "MOVE": "movement", "ATTACK": "combat",
                "USE_ITEM": "item", "LOOT": "loot", "HARVEST": "harvest",
                "USE_SKILL": "skill",
            }
            for action in applied:
                involved: list[int] = [action.actor_id]
                if isinstance(action.target, int):
                    involved.append(action.target)
                cat = _cat_map.get(action.verb.name, action.verb.name.lower())
                meta: dict = {"verb": action.verb.name, "actor_id": action.actor_id}
                if isinstance(action.target, int):
                    meta["target_id"] = action.target
                self._emit(
                    cat,
                    f"Entity {action.actor_id}: {action.verb.name} → {action.reason}",
                    entity_ids=tuple(involved),
                    metadata=meta,
                )

            # Update combat_target_id for visualization
            self._update_combat_targets(applied)

            # Update AI states from worker results
            self._update_ai_states(applied)

            # Process USE_ITEM and LOOT actions (state mutations on world loop thread)
            self._process_item_actions(applied)

            t3 = time.perf_counter()

        # --- Subsystem phase: always runs (design-02) ---
        self._tick_subsystems(tick)

        t4 = time.perf_counter()

        if ready_entities:
            logger.debug(
                "Tick %d: schedule=%.4fs collect=%.4fs resolve=%.4fs subsys=%.4fs total=%.4fs entities=%d applied=%d",
                tick,
                t1 - t0, t2 - t1, t3 - t2, t4 - t3, t4 - t0,
                len(ready_entities), len(applied),
            )

        if self._recorder and applied:
            self._recorder.record_tick(tick, applied, self._world)

    def _tick_subsystems(self, tick: int) -> None:
        """Run world subsystems with configurable rate divisors (design-02).

        Groups:
        - **core** (rate=1): cleanup, effects, stamina, cooldowns, engagement
        - **environment** (rate=2): territory, memory, goals
        - **economy** (rate=5): resources, chests, healing, quests, level-ups
        """
        cfg = self._config

        # Core subsystems — every N ticks (default: every tick)
        if tick % cfg.subsystem_rate_core == 0:
            self._phase_cleanup()
            self._tick_effects()
            self._tick_stamina_and_skills()
            self._tick_engagement()
            self._tick_threat_decay()

        # Environment subsystems — every N ticks (default: every 2nd tick)
        if tick % cfg.subsystem_rate_environment == 0:
            self._process_territory_effects()
            self._update_entity_memory()
            self._update_entity_goals()
            self._track_region_transitions()

        # Economy subsystems — every N ticks (default: every 5th tick)
        if tick % cfg.subsystem_rate_economy == 0:
            self._tick_resource_nodes()
            self._tick_treasure_chests()
            self._heal_home_entities()
            self._tick_quests()
            self._check_level_ups()

    def _phase_generators(self) -> None:
        """Run generator entities (immediate, no worker dispatch)."""
        if self._generator.should_spawn(self._world):
            entity = self._generator.spawn(self._world)
            self._world.add_entity(entity)
            logger.info("Tick %d: Spawned %s #%d at %s", self._world.tick, entity.kind, entity.id, entity.pos)

    def _phase_scheduling(self) -> list:
        """Identify entities ready to act this tick."""
        current_time = float(self._world.tick)
        ready = [
            e
            for e in self._world.entities.values()
            if e.alive and e.kind != "generator" and e.next_act_at <= current_time
        ]
        # Deterministic order: next_act_at, then entity ID
        ready.sort(key=lambda e: (e.next_act_at, e.id))
        return ready

    def _has_adjacent_hostile(self, entity) -> bool:
        """Return True if any hostile entity is adjacent (Manhattan dist 1)."""
        reg = self._faction_reg
        for other in self._world.entities.values():
            if other.id == entity.id or not other.alive or other.kind == "generator":
                continue
            if entity.pos.manhattan(other.pos) <= 1 and reg.is_hostile(entity.faction, other.faction):
                return True
        return False

    def _heal_home_entities(self) -> None:
        """Heal entities on home territory + apply town aura damage to hostiles."""
        cfg = self._config
        reg = self._faction_reg

        for entity in self._world.entities.values():
            if not entity.alive or entity.kind == "generator":
                continue

            on_town = self._world.grid.is_town(entity.pos)
            on_camp = self._world.grid.is_camp(entity.pos)

            # --- Town aura: hostile entities in town take gradual damage ---
            if on_town and reg.is_hostile(entity.faction, Faction.HERO_GUILD):
                entity.stats.hp -= cfg.town_aura_damage
                logger.debug(
                    "Tick %d: Entity #%d (%s) takes %d town aura damage [HP: %d/%d]",
                    self._world.tick, entity.id, entity.kind,
                    cfg.town_aura_damage, max(entity.stats.hp, 0), entity.stats.max_hp,
                )
                continue

            if entity.stats.hp >= entity.stats.max_hp:
                continue

            # --- Hero in town: passive heal (even while fighting) UNLESS adjacent hostile ---
            if (
                entity.faction == Faction.HERO_GUILD
                and on_town
            ):
                in_combat = self._has_adjacent_hostile(entity)
                if not in_combat:
                    # Full resting heal if in RESTING_IN_TOWN, otherwise passive heal
                    if entity.ai_state == AIState.RESTING_IN_TOWN:
                        heal = min(cfg.hero_heal_per_tick, entity.stats.max_hp - entity.stats.hp)
                    else:
                        heal = min(cfg.town_passive_heal, entity.stats.max_hp - entity.stats.hp)
                    entity.stats.hp += heal
                    logger.debug(
                        "Tick %d: Entity #%d healed %d HP in town (%d/%d)%s",
                        self._world.tick, entity.id, heal, entity.stats.hp, entity.stats.max_hp,
                        " (passive)" if entity.ai_state != AIState.RESTING_IN_TOWN else "",
                    )
                continue

            # --- Goblins guarding camp heal slowly ---
            if (
                entity.faction == Faction.GOBLIN_HORDE
                and entity.ai_state == AIState.GUARD_CAMP
                and on_camp
            ):
                heal = min(1, entity.stats.max_hp - entity.stats.hp)
                entity.stats.hp += heal

    def _process_item_actions(self, applied: list[ActionProposal]) -> None:
        """Handle USE_ITEM and LOOT proposals on the world loop thread."""
        for proposal in applied:
            entity = self._world.entities.get(proposal.actor_id)
            if entity is None or not entity.alive:
                continue

            if proposal.verb == ActionType.USE_ITEM and proposal.target:
                # Use a consumable item
                item_id: str = proposal.target
                if entity.inventory and entity.inventory.remove_item(item_id):
                    template = ITEM_REGISTRY.get(item_id)
                    if template and template.heal_amount > 0:
                        old_hp = entity.stats.hp
                        entity.stats.hp = min(
                            entity.stats.hp + template.heal_amount,
                            entity.effective_max_hp(),
                        )
                        healed = entity.stats.hp - old_hp
                        logger.info(
                            "Tick %d: Entity %d (%s) used %s → healed %d HP [HP: %d/%d]",
                            self._world.tick, entity.id, entity.kind,
                            template.name, healed, entity.stats.hp, entity.stats.max_hp,
                        )
                        self._emit("item", f"{entity.kind} #{entity.id} used {template.name} → healed {healed} HP",
                                   entity_ids=(entity.id,),
                                   metadata={"item_id": item_id, "item_name": template.name,
                                             "healed": healed, "hp_after": entity.stats.hp,
                                             "max_hp": entity.stats.max_hp})
                    from src.core.attributes import speed_delay
                    entity.next_act_at += speed_delay(entity.effective_spd(), "use_item", entity.stats.interaction_speed)

            elif proposal.verb == ActionType.LOOT and proposal.target:
                # Pick up ground loot
                from src.core.models import Vector2
                pos = proposal.target
                if isinstance(pos, Vector2):
                    items = self._world.pickup_items(pos)
                    if items and entity.inventory:
                        picked = []
                        for iid in items:
                            if entity.inventory.add_item(iid):
                                picked.append(iid)
                                # Auto-equip only if better than current gear
                                entity.inventory.auto_equip_best(iid)
                            else:
                                # Can't carry — drop back
                                self._world.drop_items(pos, [iid])
                        if picked:
                            logger.info(
                                "Tick %d: Entity %d (%s) looted %d items at %s",
                                self._world.tick, entity.id, entity.kind, len(picked), pos,
                            )
                            self._emit("loot", f"{entity.kind} #{entity.id} looted {len(picked)} items",
                                       entity_ids=(entity.id,),
                                       metadata={"items": picked, "count": len(picked),
                                                 "source": "ground", "x": pos.x, "y": pos.y})
                            # Quest progress: GATHER
                            if entity.quests:
                                from src.core.quests import QuestType
                                for iid_picked in picked:
                                    for q in entity.quests:
                                        if q.quest_type == QuestType.GATHER and not q.completed:
                                            if q.target_kind == iid_picked:
                                                just_done = q.advance()
                                                if just_done:
                                                    entity.stats.gold += q.gold_reward
                                                    entity.stats.xp += q.xp_reward
                                                    logger.info(
                                                        "Tick %d: Entity %d completed quest '%s' → +%d gold, +%d XP",
                                                        self._world.tick, entity.id, q.title,
                                                        q.gold_reward, q.xp_reward,
                                                    )
                    elif items:
                        # Entity has no inventory, leave items on ground
                        self._world.drop_items(pos, items)
                    # Check for treasure chests at this position
                    self._try_loot_chest(entity, pos)
                    from src.core.attributes import speed_delay as _sd
                    entity.next_act_at += _sd(entity.effective_spd(), "loot", entity.stats.interaction_speed)
                    # Attribute training from looting
                    if entity.attributes and entity.attribute_caps:
                        from src.core.attributes import train_attributes
                        train_attributes(entity.attributes, entity.attribute_caps, "loot", stats=entity.stats)

            elif proposal.verb == ActionType.USE_SKILL and proposal.target:
                # Use a skill on a target
                from src.core.classes import SKILL_DEFS, SkillTarget
                from src.core.effects import skill_effect
                from src.actions.damage import get_damage_calculator
                skill_id: str = proposal.target if isinstance(proposal.target, str) else ""
                # Find the skill instance on the entity
                skill_inst = None
                for si in entity.skills:
                    if si.skill_id == skill_id:
                        skill_inst = si
                        break
                if skill_inst and skill_inst.is_ready():
                    sdef = SKILL_DEFS.get(skill_id)
                    if sdef:
                        stamina_cost = skill_inst.effective_stamina_cost(sdef.stamina_cost)
                        if entity.stats.stamina >= stamina_cost:
                            entity.stats.stamina -= stamina_cost
                            cooldown = skill_inst.effective_cooldown(sdef.cooldown)
                            skill_inst.use(base_cooldown=cooldown)
                            power = skill_inst.effective_power(sdef.power)
                            skill_range = getattr(sdef, 'range', 1) or 1
                            has_mods = any([sdef.atk_mod, sdef.def_mod, sdef.spd_mod,
                                            sdef.crit_mod, sdef.evasion_mod])

                            if sdef.target in (SkillTarget.SINGLE_ENEMY, SkillTarget.AREA_ENEMIES):
                                # Resolve damage via DamageCalculator (design-01)
                                calculator = get_damage_calculator(sdef.damage_type)
                                aoe_radius = getattr(sdef, 'radius', 0) or 0
                                aoe_falloff = getattr(sdef, 'aoe_falloff', 0.15)

                                # Determine impact point for AoE skills
                                # For AoE: find nearest hostile within cast range as impact center
                                impact_pos = entity.pos
                                if sdef.target == SkillTarget.AREA_ENEMIES and aoe_radius > 0:
                                    best_dist = 999
                                    for eid_scan, e_scan in self._world.entities.items():
                                        if eid_scan == entity.id or not e_scan.alive:
                                            continue
                                        if not self._faction_reg.is_hostile(entity.faction, e_scan.faction):
                                            continue
                                        d = entity.pos.manhattan(e_scan.pos)
                                        if d <= skill_range and d < best_dist:
                                            best_dist = d
                                            impact_pos = e_scan.pos

                                # Collect targets within effective area
                                targets: list[tuple[int, Entity, int]] = []  # (eid, entity, dist_from_impact)
                                for eid, other in self._world.entities.items():
                                    if eid == entity.id or not other.alive:
                                        continue
                                    if not self._faction_reg.is_hostile(entity.faction, other.faction):
                                        continue
                                    if aoe_radius > 0:
                                        # AoE: check distance from impact point
                                        dist_impact = impact_pos.manhattan(other.pos)
                                        if dist_impact > aoe_radius:
                                            continue
                                        targets.append((eid, other, dist_impact))
                                    else:
                                        # Single-target or range-only: check distance from caster
                                        if entity.pos.manhattan(other.pos) > skill_range:
                                            continue
                                        targets.append((eid, other, 0))

                                hit_count = 0
                                for eid, other, dist_from_center in targets:
                                    # Evasion check
                                    defender_evasion = other.effective_evasion()
                                    luck_mod = entity.stats.luck * 0.002
                                    eff_evasion = max(0.0, defender_evasion - luck_mod)
                                    if self._rng and self._rng.next_bool(
                                            Domain.COMBAT, other.id, self._world.tick + 7, eff_evasion):
                                        logger.info("Tick %d: Entity %d's %s EVADED by %d",
                                                    self._world.tick, entity.id, sdef.name, eid)
                                        if sdef.target == SkillTarget.SINGLE_ENEMY:
                                            break
                                        continue

                                    # Damage calculation using correct stat pair
                                    if power > 0:
                                        dmg_ctx = calculator.resolve(entity, other)
                                        raw_dmg = int(dmg_ctx.atk_power * dmg_ctx.atk_mult * power)
                                        raw_dmg = max(raw_dmg - int(dmg_ctx.def_power * dmg_ctx.def_mult) // 2, 1)

                                        # AoE falloff: reduce damage by distance from center
                                        if dist_from_center > 0 and aoe_falloff > 0:
                                            falloff_mult = max(0.0, 1.0 - dist_from_center * aoe_falloff)
                                            raw_dmg = max(1, int(raw_dmg * falloff_mult))

                                        # Variance
                                        if self._rng:
                                            variance = self._rng.next_float(
                                                Domain.COMBAT, entity.id, self._world.tick + 5 + eid)
                                            raw_dmg = max(1, int(raw_dmg * (1.0 + self._config.damage_variance * (variance - 0.5))))

                                        # Crit check (only for center target in AoE)
                                        is_crit = False
                                        if dist_from_center == 0:
                                            crit_rate = entity.effective_crit_rate()
                                            crit_rate += entity.stats.luck * 0.003
                                            if self._rng and self._rng.next_bool(
                                                    Domain.COMBAT, entity.id, self._world.tick + 6, min(crit_rate, 0.8)):
                                                raw_dmg = int(raw_dmg * entity.stats.crit_dmg)
                                                is_crit = True

                                        dmg = max(raw_dmg, 1)
                                        other.stats.hp -= dmg
                                        hit_count += 1
                                        # Threat from skill damage (epic-05 F3)
                                        sk_threat = dmg * self._config.threat_damage_mult
                                        from src.core.classes import HeroClass as _HC
                                        if entity.hero_class in (_HC.WARRIOR, _HC.CHAMPION):
                                            sk_threat *= self._config.threat_tank_class_mult
                                        other.threat_table[entity.id] = other.threat_table.get(entity.id, 0.0) + sk_threat
                                        aoe_tag = f" (AoE d={dist_from_center})" if aoe_radius > 0 else ""
                                        logger.info(
                                            "Tick %d: Entity %d used %s on %d → %d dmg%s%s [HP: %d/%d]",
                                            self._world.tick, entity.id, sdef.name,
                                            eid, dmg, " CRIT!" if is_crit else "", aoe_tag,
                                            max(other.stats.hp, 0), other.stats.max_hp,
                                        )
                                        self._emit("skill", f"{entity.kind} #{entity.id} used {sdef.name} on #{eid} → {dmg} dmg{aoe_tag}",
                                                   entity_ids=(entity.id, eid),
                                                   metadata={"skill_id": skill_id, "skill_name": sdef.name,
                                                             "damage": dmg, "target_id": eid,
                                                             "crit": is_crit, "aoe": aoe_radius > 0,
                                                             "dist_from_center": dist_from_center,
                                                             "target_hp_after": other.stats.hp,
                                                             "target_max_hp": other.stats.max_hp})
                                    # Apply debuff if skill has duration + mods
                                    if sdef.duration > 0 and has_mods:
                                        other.effects.append(skill_effect(
                                            atk_mod=sdef.atk_mod, def_mod=sdef.def_mod,
                                            spd_mod=sdef.spd_mod, crit_mod=sdef.crit_mod,
                                            evasion_mod=sdef.evasion_mod,
                                            duration=sdef.duration, source=sdef.name,
                                            is_debuff=True,
                                        ))
                                        logger.info(
                                            "Tick %d: Entity %d debuffed by %s for %d ticks",
                                            self._world.tick, eid, sdef.name, sdef.duration,
                                        )
                                    if sdef.target == SkillTarget.SINGLE_ENEMY:
                                        break

                            elif sdef.target == SkillTarget.SELF:
                                # Self-buff: instant heal + buff effect
                                hp_mod = getattr(sdef, 'hp_mod', 0.0) or 0.0
                                if hp_mod > 0:
                                    heal = int(entity.stats.max_hp * hp_mod)
                                    entity.stats.hp = min(entity.stats.hp + heal, entity.stats.max_hp)
                                    logger.info(
                                        "Tick %d: Entity %d used %s (self) → healed %d HP",
                                        self._world.tick, entity.id, sdef.name, heal,
                                    )
                                # Apply self-buff if skill has duration + mods
                                if sdef.duration > 0 and has_mods:
                                    entity.effects.append(skill_effect(
                                        atk_mod=sdef.atk_mod, def_mod=sdef.def_mod,
                                        spd_mod=sdef.spd_mod, crit_mod=sdef.crit_mod,
                                        evasion_mod=sdef.evasion_mod,
                                        duration=sdef.duration, source=sdef.name,
                                    ))
                                    logger.info(
                                        "Tick %d: Entity %d buffed by %s for %d ticks",
                                        self._world.tick, entity.id, sdef.name, sdef.duration,
                                    )

                            elif sdef.target == SkillTarget.AREA_ALLIES:
                                # Buff nearby allies within range
                                for eid, other in self._world.entities.items():
                                    if not other.alive:
                                        continue
                                    if entity.pos.manhattan(other.pos) > skill_range:
                                        continue
                                    if other.faction != entity.faction:
                                        continue
                                    if sdef.duration > 0 and has_mods:
                                        other.effects.append(skill_effect(
                                            atk_mod=sdef.atk_mod, def_mod=sdef.def_mod,
                                            spd_mod=sdef.spd_mod, crit_mod=sdef.crit_mod,
                                            evasion_mod=sdef.evasion_mod,
                                            duration=sdef.duration, source=sdef.name,
                                        ))
                                logger.info(
                                    "Tick %d: Entity %d used %s (allies) in range %d",
                                    self._world.tick, entity.id, sdef.name, skill_range,
                                )

                            from src.core.attributes import speed_delay as _sd2
                            entity.next_act_at += _sd2(entity.effective_spd(), "skill")
                            # Attribute training from skill use
                            if entity.attributes and entity.attribute_caps:
                                from src.core.attributes import train_attributes
                                train_attributes(entity.attributes, entity.attribute_caps, "skill", stats=entity.stats)

            elif proposal.verb == ActionType.HARVEST and proposal.target:
                # Harvest a resource node
                from src.core.models import Vector2
                pos = proposal.target
                if isinstance(pos, Vector2):
                    node = self._world.resource_at(pos)
                    if node and node.is_available and entity.inventory:
                        item_id = node.harvest()
                        if item_id and entity.inventory.add_item(item_id):
                            logger.info(
                                "Tick %d: Entity %d (%s) harvested %s from %s at %s",
                                self._world.tick, entity.id, entity.kind,
                                item_id, node.name, pos,
                            )
                            # Quest progress: GATHER from harvest
                            if entity.quests:
                                from src.core.quests import QuestType
                                for q in entity.quests:
                                    if q.quest_type == QuestType.GATHER and not q.completed:
                                        if q.target_kind == item_id:
                                            just_done = q.advance()
                                            if just_done:
                                                entity.stats.gold += q.gold_reward
                                                entity.stats.xp += q.xp_reward
                                                logger.info(
                                                    "Tick %d: Entity %d completed quest '%s' → +%d gold, +%d XP",
                                                    self._world.tick, entity.id, q.title,
                                                    q.gold_reward, q.xp_reward,
                                                )
                        elif item_id:
                            # Can't carry — drop on ground
                            self._world.drop_items(pos, [item_id])
                    from src.core.attributes import speed_delay as _sd3
                    entity.next_act_at += _sd3(entity.effective_spd(), "harvest", entity.stats.interaction_speed)
                    entity.stats.stamina = max(0, entity.stats.stamina - 2)
                    # Attribute training from harvesting
                    if entity.attributes and entity.attribute_caps:
                        from src.core.attributes import train_attributes
                        train_attributes(entity.attributes, entity.attribute_caps, "harvest", stats=entity.stats)

    def _check_level_ups(self) -> None:
        """Check and apply level-ups for all entities."""
        cfg = self._config
        for entity in self._world.entities.values():
            if not entity.alive or entity.kind == "generator":
                continue
            while (
                entity.stats.xp >= entity.stats.xp_to_next
                and entity.stats.level < cfg.max_level
            ):
                entity.stats.xp -= entity.stats.xp_to_next
                entity.stats.level += 1
                # Stat growth
                entity.stats.max_hp += cfg.stat_growth_hp
                entity.stats.hp = min(entity.stats.hp + cfg.stat_growth_hp, entity.stats.max_hp)
                entity.stats.atk += cfg.stat_growth_atk
                entity.stats.matk += cfg.stat_growth_matk
                entity.stats.def_ += cfg.stat_growth_def
                entity.stats.spd += cfg.stat_growth_spd
                # XP curve: each level needs more XP
                entity.stats.xp_to_next = int(entity.stats.xp_to_next * cfg.xp_per_level_scale)
                # Attribute level-up gains
                if entity.attributes and entity.attribute_caps:
                    from src.core.attributes import level_up_attributes, recalc_derived_stats
                    old_attrs = entity.attributes.copy()
                    level_up_attributes(entity.attributes, entity.attribute_caps)
                    recalc_derived_stats(entity.stats, entity.attributes, old_attrs=old_attrs)
                logger.info(
                    "Tick %d: Entity %d (%s) leveled up to Lv%d! [HP: %d/%d ATK: %d DEF: %d SPD: %d]",
                    self._world.tick, entity.id, entity.kind, entity.stats.level,
                    entity.stats.hp, entity.stats.max_hp,
                    entity.stats.atk, entity.stats.def_, entity.stats.spd,
                )
                self._emit("level_up", f"{entity.kind} #{entity.id} reached Lv{entity.stats.level}!",
                           entity_ids=(entity.id,),
                           metadata={"entity_id": entity.id, "new_level": entity.stats.level,
                                     "max_hp": entity.stats.max_hp, "atk": entity.stats.atk,
                                     "def": entity.stats.def_, "spd": entity.stats.spd})

    def _tick_stamina_and_skills(self) -> None:
        """Regenerate stamina and tick skill cooldowns for all entities."""
        for entity in self._world.entities.values():
            if not entity.alive or entity.kind == "generator":
                continue
            # Stamina regen: faster when resting, slower otherwise
            if entity.ai_state in (AIState.RESTING_IN_TOWN, AIState.IDLE):
                regen = 5
            elif entity.ai_state in (AIState.VISIT_SHOP, AIState.VISIT_BLACKSMITH,
                                     AIState.VISIT_GUILD, AIState.VISIT_CLASS_HALL,
                                     AIState.VISIT_INN):
                regen = 4
            else:
                regen = 1
            entity.stats.stamina = min(entity.stats.stamina + regen, entity.stats.max_stamina)
            # Tick skill cooldowns
            for skill in entity.skills:
                skill.tick()

    def _update_entity_memory(self) -> None:
        """Update terrain_memory and entity_memory for all alive entities based on vision."""
        grid = self._world.grid
        spatial = self._world.spatial_index
        entities = self._world.entities
        tick = self._world.tick
        grid_w = grid.width
        grid_h = grid.height
        tiles = grid._tiles  # direct array access — skip method + enum overhead

        for entity in entities.values():
            if not entity.alive or entity.kind == "generator":
                continue
            vr = entity.stats.vision_range
            ex, ey = entity.pos.x, entity.pos.y
            tmem = entity.terrain_memory

            # Record visible tiles — direct array access, no method/enum overhead
            for dy in range(-vr, vr + 1):
                ty = ey + dy
                if ty < 0 or ty >= grid_h:
                    continue
                remaining = vr - abs(dy)
                x_lo = max(0, ex - remaining)
                x_hi = min(grid_w - 1, ex + remaining)
                row_base = ty * grid_w
                for tx in range(x_lo, x_hi + 1):
                    tmem[(tx, ty)] = tiles[row_base + tx].value

            # Record visible entities — use spatial hash instead of full scan
            nearby_ids = spatial.query_radius(entity.pos, vr)
            nearby_ids.discard(entity.id)
            seen_ids: set[int] = set()

            # Build dict index of existing memory for O(1) lookup
            mem_index: dict[int, dict] = {}
            for em in entity.entity_memory:
                mem_index[em["id"]] = em

            for oid in nearby_ids:
                other = entities.get(oid)
                if other is None or not other.alive or other.kind == "generator":
                    continue
                if abs(ex - other.pos.x) + abs(ey - other.pos.y) > vr:
                    continue  # spatial hash is coarse — verify exact distance
                seen_ids.add(oid)
                existing = mem_index.get(oid)
                if existing is not None:
                    existing["x"] = other.pos.x
                    existing["y"] = other.pos.y
                    existing["kind"] = other.kind
                    existing["hp"] = other.stats.hp
                    existing["max_hp"] = other.stats.max_hp
                    existing["atk"] = other.effective_atk()
                    existing["level"] = other.stats.level
                    existing["tick"] = tick
                    existing["visible"] = True
                else:
                    new_em = {
                        "id": oid, "x": other.pos.x, "y": other.pos.y,
                        "kind": other.kind, "hp": other.stats.hp,
                        "max_hp": other.stats.max_hp, "atk": other.effective_atk(),
                        "level": other.stats.level, "tick": tick, "visible": True,
                    }
                    entity.entity_memory.append(new_em)
                    mem_index[oid] = new_em

            # Mark unseen as not visible, prune dead/removed + old (>200 ticks)
            pruned = []
            for em in entity.entity_memory:
                eid = em["id"]
                if eid not in entities or not entities[eid].alive:
                    continue
                if eid not in seen_ids:
                    em["visible"] = False
                if tick - em["tick"] < 200:
                    pruned.append(em)
            entity.entity_memory = pruned

    def _process_territory_effects(self) -> None:
        """Apply debuffs to entities on hostile territory and alert defenders."""
        reg = self._faction_reg
        cfg = self._config
        tick = self._world.tick

        for entity in self._world.entities.values():
            if not entity.alive or entity.kind == "generator":
                continue
            mat = self._world.grid.get(entity.pos)
            tile_owner = reg.tile_owner(mat)

            if tile_owner is None or tile_owner == entity.faction:
                # On neutral or home territory — remove territory debuff if present
                entity.remove_effects_by_type(EffectType.TERRITORY_DEBUFF)
                continue

            if not reg.is_hostile(entity.faction, tile_owner):
                continue

            # --- Intruder on hostile territory ---
            territory_info = reg.territory_for(tile_owner)
            if territory_info is None:
                continue

            # Apply / refresh territory debuff on the intruder
            entity.remove_effects_by_type(EffectType.TERRITORY_DEBUFF)
            entity.effects.append(territory_debuff(
                atk_mult=territory_info.atk_debuff,
                def_mult=territory_info.def_debuff,
                spd_mult=territory_info.spd_debuff,
                duration=cfg.territory_debuff_duration,
                source=f"{tile_owner.name}_territory",
            ))

            # Alert nearby defenders: switch them to ALERT state
            alert_r = territory_info.alert_radius
            for defender in self._world.entities.values():
                if (
                    defender.alive
                    and defender.faction == tile_owner
                    and defender.id != entity.id
                    and entity.pos.manhattan(defender.pos) <= alert_r
                    and defender.ai_state not in (AIState.COMBAT, AIState.HUNT, AIState.ALERT, AIState.FLEE)
                ):
                    defender.ai_state = AIState.ALERT
                    logger.debug(
                        "Tick %d: Entity %d (%s) alerted by intruder %d (%s) on %s territory",
                        tick, defender.id, defender.kind, entity.id, entity.kind, tile_owner.name,
                    )

    def _track_region_transitions(self) -> None:
        """Check entity positions against regions and emit enter/leave events for heroes."""
        from src.core.regions import find_region_at

        regions = self._world.regions
        if not regions:
            return

        for entity in self._world.entities.values():
            if not entity.alive or entity.kind == "generator":
                continue

            # Determine which region entity is currently in (Voronoi nearest-center)
            region = find_region_at(entity.pos, regions)
            new_region_id = region.region_id if region else ""
            new_region_name = region.name if region else ""
            new_difficulty = region.difficulty if region else 0

            old_region_id = entity.current_region_id
            if new_region_id == old_region_id:
                continue

            entity.current_region_id = new_region_id

            # Only emit events for heroes
            if entity.faction != Faction.HERO_GUILD:
                continue

            if old_region_id:
                self._emit("region_leave",
                           f"Hero #{entity.id} left region",
                           entity_ids=(entity.id,),
                           metadata={"entity_id": entity.id, "region_id": old_region_id})

            if new_region_id:
                self._emit("region_enter",
                           f"Hero #{entity.id} entered {new_region_name} (tier {new_difficulty})",
                           entity_ids=(entity.id,),
                           metadata={"entity_id": entity.id, "region_id": new_region_id,
                                     "region_name": new_region_name, "difficulty": new_difficulty})

    def _tick_engagement(self) -> None:
        """Track how many ticks each entity has been adjacent to a hostile.

        Used by the Engagement Lock mechanic: when engaged_ticks >= 2,
        fleeing (moving away) costs double action delay.
        """
        reg = self._faction_reg
        spatial = self._world.spatial_index
        entities = self._world.entities
        for entity in entities.values():
            if not entity.alive or entity.kind == "generator":
                continue
            adjacent_hostile = False
            ex, ey = entity.pos.x, entity.pos.y
            for oid in spatial.query_radius(entity.pos, 1):
                if oid == entity.id:
                    continue
                other = entities.get(oid)
                if other is None or not other.alive or other.kind == "generator":
                    continue
                if abs(ex - other.pos.x) + abs(ey - other.pos.y) <= 1 and reg.is_hostile(entity.faction, other.faction):
                    adjacent_hostile = True
                    break
            if adjacent_hostile:
                entity.engaged_ticks = min(entity.engaged_ticks + 1, 10)
            else:
                entity.engaged_ticks = 0

    def _tick_threat_decay(self) -> None:
        """Decay threat values over time (epic-05 F3).

        Each tick, all threat entries decay by threat_decay_rate %.
        Entries below 1.0 are pruned to keep tables clean.
        Dead attacker entries are also removed.
        """
        decay = 1.0 - self._config.threat_decay_rate
        entities = self._world.entities
        for entity in entities.values():
            if not entity.alive or not entity.threat_table:
                continue
            to_remove: list[int] = []
            for attacker_id, threat in entity.threat_table.items():
                # Remove threat from dead/removed attackers
                attacker = entities.get(attacker_id)
                if attacker is None or not attacker.alive:
                    to_remove.append(attacker_id)
                    continue
                new_threat = threat * decay
                if new_threat < 1.0:
                    to_remove.append(attacker_id)
                else:
                    entity.threat_table[attacker_id] = new_threat
            for aid in to_remove:
                del entity.threat_table[aid]

    def _tick_resource_nodes(self) -> None:
        """Tick cooldowns on depleted resource nodes so they respawn."""
        for node in self._world.resource_nodes.values():
            node.tick_cooldown()

    def _tick_treasure_chests(self) -> None:
        """Respawn looted treasure chests and their guards."""
        tick = self._world.tick
        for chest in self._world.treasure_chests.values():
            if chest.try_respawn(tick):
                # Respawn guard if it was killed
                if chest.guard_entity_id is not None:
                    guard = self._world.entities.get(chest.guard_entity_id)
                    if guard is None or not guard.alive:
                        self._spawn_chest_guard(chest)
                logger.info("Tick %d: Treasure chest %d respawned at %s (tier %d)",
                            tick, chest.chest_id, chest.pos, chest.tier)

    def _try_loot_chest(self, entity, pos) -> None:
        """If there's an available treasure chest at pos, loot it."""
        from src.core.items import CHEST_LOOT_TABLES
        from src.core.enums import Domain
        for chest in self._world.treasure_chests.values():
            if chest.pos == pos and chest.is_available:
                # Check if guard is still alive — must defeat guard first
                if chest.guard_entity_id is not None:
                    guard = self._world.entities.get(chest.guard_entity_id)
                    if guard and guard.alive:
                        continue  # Guard still alive, can't loot
                # Generate loot from chest loot table
                loot_table = CHEST_LOOT_TABLES.get(chest.tier, [])
                loot_items: list[str] = []
                for item_id, chance, min_c, max_c in loot_table:
                    roll = self._rng.next_float(Domain.LOOT, entity.id, self._world.tick + chest.chest_id)
                    if roll < chance:
                        count = self._rng.next_int(
                            Domain.LOOT, entity.id, self._world.tick + chest.chest_id + 100,
                            min_c, max_c)
                        loot_items.extend([item_id] * count)
                # Drop loot on the ground at chest position
                if loot_items:
                    self._world.drop_items(pos, loot_items)
                # Mark chest as looted
                chest.loot(self._world.tick, respawn_ticks=150 + chest.tier * 50)
                logger.info(
                    "Tick %d: Entity %d looted tier-%d chest #%d at %s → %d items",
                    self._world.tick, entity.id, chest.tier, chest.chest_id, pos, len(loot_items))
                break  # Only loot one chest per action

    def _spawn_chest_guard(self, chest) -> None:
        """Spawn an elite guard entity next to a treasure chest."""
        from src.core.enums import EnemyTier
        from src.core.items import TERRAIN_RACE
        # Determine race from terrain at chest position
        mat = self._world.grid.material_at(chest.pos.x, chest.pos.y)
        race = TERRAIN_RACE.get(mat, "goblin")
        tier = min(chest.tier + 1, EnemyTier.ELITE)  # Chest tier 1→WARRIOR, 2→ELITE, 3→ELITE
        entity = self._generator.spawn_race(
            self._world, race=race, tier=tier, near_pos=chest.pos)
        self._world.add_entity(entity)
        chest.guard_entity_id = entity.id
        logger.info("Tick %d: Spawned chest guard %s #%d at %s (tier %d)",
                    self._world.tick, entity.kind, entity.id, entity.pos, tier)

    def _tick_quests(self) -> None:
        """Check EXPLORE quest completion and prune finished quests."""
        from src.core.quests import QuestType
        tick = self._world.tick
        for entity in self._world.entities.values():
            if not entity.alive or entity.kind == "generator" or not entity.quests:
                continue
            for q in entity.quests:
                if q.completed:
                    continue
                # EXPLORE: complete when hero is within 2 tiles of target
                if q.quest_type == QuestType.EXPLORE and q.target_pos is not None:
                    if entity.pos.manhattan(q.target_pos) <= 2:
                        q.advance()
                        entity.stats.gold += q.gold_reward
                        entity.stats.xp += q.xp_reward
                        logger.info(
                            "Tick %d: Entity %d completed quest '%s' → +%d gold, +%d XP",
                            tick, entity.id, q.title, q.gold_reward, q.xp_reward,
                        )
            # Prune completed quests older than 50 ticks (keep for display briefly)
            entity.quests = [q for q in entity.quests if not q.completed or tick % 50 != 0]

    def _tick_effects(self) -> None:
        """Tick down status effect durations, apply hp_per_tick, and remove expired."""
        for entity in self._world.entities.values():
            if not entity.alive or entity.kind == "generator":
                continue
            if not entity.effects:
                continue
            for eff in entity.effects:
                # Apply hp_per_tick (positive = regen, negative = DoT)
                if eff.hp_per_tick != 0 and not eff.expired:
                    entity.stats.hp = max(0, min(
                        entity.stats.hp + eff.hp_per_tick,
                        entity.effective_max_hp(),
                    ))
                eff.tick()
            entity.effects = [e for e in entity.effects if not e.expired]

    def _update_entity_goals(self) -> None:
        """Derive behavioral goals for each entity based on state and context."""
        reg = self._faction_reg
        for entity in self._world.entities.values():
            if not entity.alive or entity.kind == "generator":
                continue
            goals: list[str] = []
            hp_ratio = entity.stats.hp_ratio
            stamina_ratio = entity.stats.stamina_ratio
            is_hero = entity.faction == Faction.HERO_GUILD
            st = entity.ai_state

            # --- Current action (from last AI decision reason) ---
            if entity.last_reason:
                goals.append(f"[Action] {entity.last_reason}")

            # --- Territory awareness ---
            mat = self._world.grid.get(entity.pos)
            on_enemy_territory = reg.is_enemy_territory(entity.faction, mat)
            if on_enemy_territory:
                goals.append("[Warning] Trespassing on enemy territory — stat debuff active!")
            if entity.has_effect(EffectType.TERRITORY_DEBUFF):
                goals.append("[Debuff] Weakened by hostile territory")

            # --- State-specific context ---
            if is_hero:
                # HP status
                if hp_ratio < 0.3:
                    goals.append("[Urgent] HP critical — find safety and heal!")
                elif hp_ratio < 0.6:
                    goals.append("[Concern] Low HP — consider potions or retreating to town")
                # Stamina status
                if stamina_ratio < 0.2:
                    goals.append("[Stamina] Exhausted — need rest soon")
                elif stamina_ratio < 0.4:
                    goals.append("[Stamina] Running low — conserve energy")

                # Long-term goals
                if entity.stats.level < 5:
                    goals.append("[Goal] Grow stronger — gain XP from enemies")
                elif entity.stats.level < 10:
                    goals.append("[Goal] Reach high level to raid enemy camps")
                else:
                    goals.append("[Goal] Dominate the battlefield")

                # Equipment needs
                if entity.inventory:
                    inv = entity.inventory
                    if not inv.weapon:
                        goals.append("[Need] No weapon equipped — find or buy one")
                    if not inv.armor:
                        goals.append("[Need] No armor equipped — find or buy one")
                    slots_used = inv.used_slots
                    slots_max = inv.max_slots
                    if slots_used > slots_max * 0.8:
                        goals.append(f"[Inventory] Nearly full ({slots_used}/{slots_max}) — sell or store items")
                    elif slots_used < slots_max * 0.3:
                        goals.append(f"[Inventory] Plenty of space ({slots_used}/{slots_max}) — collect loot")

                # Exploration
                explored = len(entity.terrain_memory)
                total_tiles = self._world.grid.width * self._world.grid.height
                pct = explored * 100 // total_tiles
                if pct < 30:
                    goals.append(f"[Explore] {pct}% mapped — much to discover")
                elif pct < 70:
                    goals.append(f"[Explore] {pct}% mapped — continue exploration")
                else:
                    goals.append(f"[Explore] {pct}% mapped — well-traveled")

                # Craft awareness
                if entity.craft_target:
                    goals.append(f"[Craft] Working toward: {entity.craft_target}")

                # State-specific
                if st == AIState.COMBAT:
                    goals.append("[Focus] Defeat the current enemy!")
                elif st == AIState.LOOTING:
                    goals.append("[Focus] Picking up nearby items")
                elif st == AIState.RESTING_IN_TOWN:
                    goals.append(f"[Town] Resting — HP {entity.stats.hp}/{entity.stats.max_hp}")
                elif st == AIState.HARVESTING:
                    goals.append("[Focus] Harvesting a resource node")
                elif st == AIState.VISIT_SHOP:
                    goals.append("[Town] Shopping — buying supplies or selling loot")
                elif st == AIState.VISIT_BLACKSMITH:
                    goals.append("[Town] At the Blacksmith — crafting gear")
                elif st == AIState.VISIT_GUILD:
                    goals.append("[Town] At the Guild — gathering intel")
                elif st == AIState.VISIT_CLASS_HALL:
                    goals.append("[Town] At Class Hall — training skills")
                elif st == AIState.VISIT_INN:
                    goals.append(f"[Town] Resting at Inn — STA {entity.stats.stamina}/{entity.stats.max_stamina}")
                elif st == AIState.VISIT_HOME:
                    goals.append("[Town] At home — managing storage")
                elif st == AIState.FLEE:
                    goals.append("[Urgent] Fleeing from danger!")
                elif st == AIState.HUNT:
                    goals.append("[Focus] Hunting a target")
            else:
                # Non-hero entities
                if st == AIState.GUARD_CAMP:
                    goals.append("[Duty] Guarding camp — watching for intruders")
                elif st == AIState.ALERT:
                    goals.append("[Alert] Intruder detected! Engaging the threat!")
                elif st == AIState.RETURN_TO_CAMP:
                    goals.append("[Movement] Returning to camp")
                elif st == AIState.HUNT:
                    goals.append("[Hunt] Pursuing a target")
                elif st == AIState.COMBAT:
                    goals.append("[Combat] Fighting an enemy")
                elif st == AIState.FLEE:
                    goals.append("[Flee] Too wounded to fight — retreating!")
                elif st == AIState.WANDER:
                    goals.append("[Patrol] Wandering and searching for prey")
                elif st == AIState.RESTING_IN_TOWN:
                    goals.append(f"[Rest] Recovering HP ({entity.stats.hp}/{entity.stats.max_hp})")

                if hp_ratio < 0.3:
                    goals.append("[Urgent] Desperate — need to escape!")
                elif hp_ratio < 0.6:
                    goals.append("[Caution] Wounded — being cautious")
                else:
                    goals.append("[Status] Healthy and ready")

                if entity.home_pos:
                    dist_home = entity.pos.manhattan(entity.home_pos)
                    if dist_home > 8:
                        goals.append(f"[Range] Far from camp ({dist_home} tiles)")

            entity.goals = goals

    def _process_opportunity_attacks(
        self, applied: list[ActionProposal], pre_positions: dict[int, tuple[int, int]]
    ) -> None:
        """Free hit from adjacent hostiles when an entity moves away (epic-05).

        For each applied MOVE, check if the entity was at Manhattan distance 1
        from any hostile before moving. If the move increased distance (disengaging),
        each such hostile deals a reduced-damage hit.
        """
        cfg = self._config
        reg = self._faction_reg
        entities = self._world.entities
        mult = cfg.opportunity_attack_damage_mult
        tick = self._world.tick

        for proposal in applied:
            if proposal.verb != ActionType.MOVE:
                continue
            mover = entities.get(proposal.actor_id)
            if mover is None or not mover.alive:
                continue
            old_pos = pre_positions.get(proposal.actor_id)
            if old_pos is None:
                continue
            ox, oy = old_pos
            new_pos = mover.pos  # already moved

            # Find hostiles that were adjacent (dist=1) to old position
            for eid, ent in entities.items():
                if eid == mover.id or not ent.alive or ent.kind == "generator":
                    continue
                if not reg.is_hostile(mover.faction, ent.faction):
                    continue
                # Was this hostile adjacent to mover's OLD position?
                old_dist = abs(ent.pos.x - ox) + abs(ent.pos.y - oy)
                if old_dist != 1:
                    continue
                # Did the move INCREASE distance from this hostile?
                new_dist = abs(ent.pos.x - new_pos.x) + abs(ent.pos.y - new_pos.y)
                if new_dist <= old_dist:
                    continue
                # Opportunity attack: simplified damage (no crit, no evasion)
                atk = ent.effective_atk()
                def_ = mover.effective_def()
                raw = max(1, int(atk * mult) - def_ // 2)
                mover.stats.hp -= raw
                # Threat from opportunity attack (epic-05 F3)
                oa_threat = raw * cfg.threat_damage_mult
                mover.threat_table[ent.id] = mover.threat_table.get(ent.id, 0.0) + oa_threat
                logger.info(
                    "Tick %d: Entity %d (%s) opportunity attack on %d (%s) for %d damage [HP: %d/%d]",
                    tick, ent.id, ent.kind, mover.id, mover.kind,
                    raw, max(mover.stats.hp, 0), mover.stats.max_hp,
                )
                self._emit(
                    "combat",
                    f"Entity {ent.id} opportunity attack → {mover.id} for {raw} damage",
                    entity_ids=(ent.id, mover.id),
                    metadata={"verb": "OPPORTUNITY_ATTACK", "actor_id": ent.id,
                              "target_id": mover.id, "damage": raw},
                )

    def _process_chase_closing(self) -> None:
        """SPD-based chase closing: faster hunters periodically gain a bonus tile (epic-05).

        When a HUNT entity has higher SPD than its chase target, it periodically
        gets moved 1 bonus tile closer — closing the gap over time.
        """
        import math
        cfg = self._config
        reg = self._faction_reg
        entities = self._world.entities
        spatial = self._world.spatial_index

        for entity in list(entities.values()):
            if not entity.alive or entity.ai_state != AIState.HUNT:
                continue
            if entity.chase_ticks < 2:
                continue

            # Find chase target: nearest visible hostile
            hunter_spd = entity.effective_spd()
            ex, ey = entity.pos.x, entity.pos.y
            best_target = None
            best_dist = 999
            for oid in spatial.query_radius(entity.pos, entity.stats.vision_range):
                if oid == entity.id:
                    continue
                other = entities.get(oid)
                if other is None or not other.alive or other.kind == "generator":
                    continue
                if not reg.is_hostile(entity.faction, other.faction):
                    continue
                d = abs(ex - other.pos.x) + abs(ey - other.pos.y)
                if d < best_dist:
                    best_dist = d
                    best_target = other
            if best_target is None:
                continue

            target_spd = best_target.effective_spd()
            if hunter_spd <= target_spd:
                continue

            # Closing interval: lower = more frequent bonus moves
            interval = max(1, math.ceil(cfg.chase_spd_closing_base * target_spd / hunter_spd))
            if entity.chase_ticks % interval != 0:
                continue

            # Bonus move: 1 tile closer to target
            from src.ai.perception import Perception
            direction = Perception.direction_toward(entity.pos, best_target.pos)
            new_pos = entity.pos + direction
            # Check passability (walkable + not occupied)
            if not self._world.grid.is_walkable(new_pos):
                continue
            occupied = any(
                e.id != entity.id and e.pos.x == new_pos.x and e.pos.y == new_pos.y
                for e in entities.values() if e.alive
            )
            if occupied:
                continue

            self._world.move_entity(entity.id, new_pos)
            logger.info(
                "Tick %d: Entity %d (%s) sprint-closes on %d (%s) (SPD %d vs %d, chase_ticks=%d)",
                self._world.tick, entity.id, entity.kind,
                best_target.id, best_target.kind,
                hunter_spd, target_spd, entity.chase_ticks,
            )
            self._emit(
                "movement",
                f"Entity {entity.id} sprints closer to {best_target.id} (SPD advantage)",
                entity_ids=(entity.id,),
                metadata={"verb": "CHASE_SPRINT", "actor_id": entity.id,
                          "target_id": best_target.id},
            )

    def _update_combat_targets(self, applied: list[ActionProposal]) -> None:
        """Set combat_target_id on entities for frontend visualization."""
        acted: set[int] = set()
        for proposal in applied:
            entity = self._world.entities.get(proposal.actor_id)
            if entity is None:
                continue
            acted.add(proposal.actor_id)
            if proposal.verb in (ActionType.ATTACK, ActionType.USE_SKILL) and isinstance(proposal.target, int):
                entity.combat_target_id = proposal.target
            else:
                entity.combat_target_id = None
        # Clear target for entities that didn't act this tick but are no longer in combat
        for entity in self._world.entities.values():
            if entity.id not in acted and entity.ai_state not in (AIState.COMBAT, AIState.HUNT):
                entity.combat_target_id = None

    def _update_ai_states(self, applied: list[ActionProposal]) -> None:
        """Propagate new AI states from brain decisions after action resolution."""
        for proposal in applied:
            entity = self._world.entities.get(proposal.actor_id)
            if entity is None:
                continue
            if proposal.new_ai_state is not None:
                entity.ai_state = AIState(proposal.new_ai_state)
            if proposal.reason:
                entity.last_reason = proposal.reason

    def _phase_cleanup(self) -> None:
        """Remove dead entities, respawn heroes at town, drop loot, rebuild spatial index."""
        dead_ids = [eid for eid, e in self._world.entities.items() if not e.alive]
        for eid in dead_ids:
            entity = self._world.entities.get(eid)
            if entity is None:
                continue

            # Drop all inventory + equipment as ground loot
            if entity.inventory:
                dropped = entity.inventory.get_all_item_ids()
                if dropped:
                    self._world.drop_items(entity.pos, dropped)
                    logger.info(
                        "Tick %d: Entity %d (%s) dropped %d items at %s",
                        self._world.tick, eid, entity.kind, len(dropped), entity.pos,
                    )

            if entity.faction == Faction.HERO_GUILD and entity.home_pos is not None:
                # Hero respawn: restore HP, teleport home, cooldown
                entity.stats.hp = entity.stats.max_hp
                old_pos = entity.pos
                entity.pos = entity.home_pos
                entity.ai_state = AIState.RESTING_IN_TOWN
                entity.next_act_at = float(self._world.tick + self._config.hero_respawn_ticks)
                entity.memory.clear()
                entity.effects.clear()
                # Reset inventory (hero loses carried items on death, keeps equipment)
                if entity.inventory:
                    entity.inventory.items.clear()
                self._world.spatial_index.move(eid, old_pos, entity.home_pos)
                logger.info(
                    "Tick %d: Hero #%d died → respawning at home %s in %d ticks.",
                    self._world.tick, eid, entity.home_pos, self._config.hero_respawn_ticks,
                )
                self._emit("death", f"Hero #{eid} died → respawning in {self._config.hero_respawn_ticks} ticks",
                           entity_ids=(eid,),
                           metadata={"entity_id": eid, "kind": entity.kind,
                                     "level": entity.stats.level,
                                     "x": old_pos.x, "y": old_pos.y,
                                     "respawn": True})
            else:
                removed = self._world.remove_entity(eid)
                if removed:
                    logger.info("Tick %d: Entity %d (%s Lv%d) died.", self._world.tick, eid, removed.kind, removed.stats.level)
                    self._emit("death", f"{removed.kind} #{eid} Lv{removed.stats.level} died",
                               entity_ids=(eid,),
                               metadata={"entity_id": eid, "kind": removed.kind,
                                         "level": removed.stats.level,
                                         "x": removed.pos.x, "y": removed.pos.y,
                                         "respawn": False})
