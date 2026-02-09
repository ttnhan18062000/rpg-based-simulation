"""WorldLoop — the authoritative 4-phase tick engine.

Phase cycle:
  1. Scheduling — identify ready entities, dispatch to workers
  2. Wait & Collect — drain the action queue
  3. Conflict Resolution & Application — validate + apply proposals
  4. Cleanup & Advancement — remove dead, territory effects, advance tick
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.effects import EffectType, territory_debuff
from src.core.enums import AIState, ActionType
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
        "_faction_reg",
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
    ) -> None:
        self._config = config
        self._world = world
        self._action_queue = ActionQueue()
        self._worker_pool = worker_pool
        self._conflict_resolver = conflict_resolver
        self._generator = generator
        self._recorder = recorder
        self._last_applied: list[ActionProposal] = []
        self._faction_reg = faction_reg or FactionRegistry.default()

    @property
    def world(self) -> WorldState:
        return self._world

    @property
    def last_applied(self) -> list[ActionProposal]:
        """Actions applied during the most recent tick."""
        return self._last_applied

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
        """Execute one complete tick cycle."""
        tick = self._world.tick

        # --- Phase 1: Scheduling ---
        self._phase_generators()
        ready_entities = self._phase_scheduling()

        if not ready_entities:
            return

        # --- Phase 2: Wait & Collect ---
        snapshot = Snapshot.from_world(self._world)
        self._worker_pool.dispatch(ready_entities, snapshot, self._action_queue)
        proposals = self._action_queue.drain()

        # --- Phase 3: Conflict Resolution & Application ---
        applied = self._conflict_resolver.resolve(proposals, self._world)
        self._last_applied = applied

        # Update AI states from worker results
        self._update_ai_states(applied)

        # Process USE_ITEM and LOOT actions (state mutations on world loop thread)
        self._process_item_actions(applied)

        # Heal heroes resting in town / camp
        self._heal_home_entities()

        # --- Phase 4: Cleanup & Advancement ---
        self._phase_cleanup()

        # Territory intrusion: apply debuffs and trigger alerts
        self._process_territory_effects()

        # Tick down status effects and remove expired ones
        self._tick_effects()

        # Tick resource node cooldowns (respawn depleted nodes)
        self._tick_resource_nodes()

        # Level-up checks
        self._check_level_ups()

        # Stamina regen and skill cooldown ticking
        self._tick_stamina_and_skills()

        # Update entity perception memory and goals
        self._update_entity_memory()
        self._tick_quests()
        self._update_entity_goals()

        if self._recorder:
            self._recorder.record_tick(tick, applied, self._world)

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
                    entity.next_act_at += 0.5  # small action delay

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
                                # Auto-equip if slot is empty
                                t = ITEM_REGISTRY.get(iid)
                                if t and t.item_type.value <= 2:  # WEAPON/ARMOR/ACCESSORY
                                    entity.inventory.equip(iid)
                            else:
                                # Can't carry — drop back
                                self._world.drop_items(pos, [iid])
                        if picked:
                            logger.info(
                                "Tick %d: Entity %d (%s) looted %d items at %s",
                                self._world.tick, entity.id, entity.kind, len(picked), pos,
                            )
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
                    entity.next_act_at += 0.5
                    # Attribute training from looting
                    if entity.attributes and entity.attribute_caps:
                        from src.core.attributes import train_attributes
                        train_attributes(entity.attributes, entity.attribute_caps, "loot")

            elif proposal.verb == ActionType.USE_SKILL and proposal.target:
                # Use a skill on a target
                from src.core.classes import SKILL_DEFS, SkillTarget
                from src.core.effects import skill_effect
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
                                # Deal damage + apply debuff to enemies in range
                                for eid, other in self._world.entities.items():
                                    if eid == entity.id or not other.alive:
                                        continue
                                    if entity.pos.manhattan(other.pos) > skill_range:
                                        continue
                                    if not self._faction_reg.is_hostile(entity.faction, other.faction):
                                        continue
                                    # Damage
                                    if power > 0:
                                        raw_dmg = int(entity.effective_atk() * power)
                                        dmg = max(raw_dmg - other.effective_def() // 2, 1)
                                        other.stats.hp -= dmg
                                        logger.info(
                                            "Tick %d: Entity %d used %s on %d → %d dmg [HP: %d/%d]",
                                            self._world.tick, entity.id, sdef.name,
                                            eid, dmg, other.stats.hp, other.stats.max_hp,
                                        )
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

                            entity.next_act_at += 1.0 / max(entity.effective_spd(), 1)
                            # Attribute training from skill use
                            if entity.attributes and entity.attribute_caps:
                                from src.core.attributes import train_attributes
                                train_attributes(entity.attributes, entity.attribute_caps, "cast")

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
                    entity.next_act_at += 0.5
                    entity.stats.stamina = max(0, entity.stats.stamina - 2)
                    # Attribute training from harvesting
                    if entity.attributes and entity.attribute_caps:
                        from src.core.attributes import train_attributes
                        train_attributes(entity.attributes, entity.attribute_caps, "harvest")

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
                entity.stats.def_ += cfg.stat_growth_def
                entity.stats.spd += cfg.stat_growth_spd
                # XP curve: each level needs more XP
                entity.stats.xp_to_next = int(entity.stats.xp_to_next * cfg.xp_per_level_scale)
                # Attribute level-up gains
                if entity.attributes and entity.attribute_caps:
                    from src.core.attributes import level_up_attributes
                    level_up_attributes(entity.attributes, entity.attribute_caps)
                logger.info(
                    "Tick %d: Entity %d (%s) leveled up to Lv%d! [HP: %d/%d ATK: %d DEF: %d SPD: %d]",
                    self._world.tick, entity.id, entity.kind, entity.stats.level,
                    entity.stats.hp, entity.stats.max_hp,
                    entity.stats.atk, entity.stats.def_, entity.stats.spd,
                )

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
        vr = self._config.vision_range
        grid = self._world.grid
        tick = self._world.tick
        for entity in self._world.entities.values():
            if not entity.alive or entity.kind == "generator":
                continue
            ex, ey = entity.pos.x, entity.pos.y
            # Record visible tiles into terrain_memory
            from src.core.models import Vector2
            for dy in range(-vr, vr + 1):
                for dx in range(-vr, vr + 1):
                    if abs(dx) + abs(dy) > vr:
                        continue
                    tx, ty = ex + dx, ey + dy
                    tp = Vector2(tx, ty)
                    if grid.in_bounds(tp):
                        entity.terrain_memory[(tx, ty)] = grid.get(tp).value
            # Record visible entities into entity_memory (keep latest per id)
            seen_ids = set()
            for other in self._world.entities.values():
                if other.id == entity.id or not other.alive or other.kind == "generator":
                    continue
                if entity.pos.manhattan(other.pos) <= vr:
                    seen_ids.add(other.id)
                    # Update or add memory entry
                    found = False
                    for em in entity.entity_memory:
                        if em["id"] == other.id:
                            em["x"] = other.pos.x
                            em["y"] = other.pos.y
                            em["kind"] = other.kind
                            em["hp"] = other.stats.hp
                            em["max_hp"] = other.stats.max_hp
                            em["atk"] = other.effective_atk()
                            em["level"] = other.stats.level
                            em["tick"] = tick
                            em["visible"] = True
                            found = True
                            break
                    if not found:
                        entity.entity_memory.append({
                            "id": other.id, "x": other.pos.x, "y": other.pos.y,
                            "kind": other.kind, "hp": other.stats.hp,
                            "max_hp": other.stats.max_hp, "atk": other.effective_atk(),
                            "level": other.stats.level, "tick": tick, "visible": True,
                        })
            # Mark unseen entities as not visible, prune dead/removed + very old (>200 ticks)
            pruned = []
            for em in entity.entity_memory:
                eid = em["id"]
                # Remove entries for entities that no longer exist (defeated/removed)
                if eid not in self._world.entities or not self._world.entities[eid].alive:
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

    def _tick_resource_nodes(self) -> None:
        """Tick cooldowns on depleted resource nodes so they respawn."""
        for node in self._world.resource_nodes.values():
            node.tick_cooldown()

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
            is_hero = entity.faction == Faction.HERO_GUILD

            # Territory awareness
            mat = self._world.grid.get(entity.pos)
            on_enemy_territory = reg.is_enemy_territory(entity.faction, mat)
            if on_enemy_territory:
                goals.append("Trespassing on enemy territory — stat debuff active!")

            # Active effects awareness
            if entity.has_effect(EffectType.TERRITORY_DEBUFF):
                goals.append("Weakened by hostile territory")

            if is_hero:
                if hp_ratio < 0.3:
                    goals.append("Survive — find safety and heal")
                elif hp_ratio < 0.6:
                    goals.append("Find potions or return to town to heal")
                if entity.stats.level < 5:
                    goals.append("Grow stronger — gain XP from enemies")
                elif entity.stats.level < 10:
                    goals.append("Become powerful enough to raid goblin camps")
                else:
                    goals.append("Dominate the battlefield")
                if entity.inventory and entity.inventory.used_slots > entity.inventory.max_slots * 0.8:
                    goals.append("Inventory nearly full — prioritize upgrades")
                elif entity.inventory and entity.inventory.used_slots < entity.inventory.max_slots * 0.3:
                    goals.append("Collect more loot and equipment")
                if entity.inventory and not entity.inventory.weapon:
                    goals.append("Find a weapon")
                if entity.inventory and not entity.inventory.armor:
                    goals.append("Find armor")
                explored = len(entity.terrain_memory)
                total_tiles = self._world.grid.width * self._world.grid.height
                if explored < total_tiles * 0.3:
                    goals.append("Explore unknown territory")
                elif explored < total_tiles * 0.7:
                    goals.append("Continue mapping the world")
                else:
                    goals.append("Most of the world has been explored")
                if entity.ai_state == AIState.COMBAT:
                    goals.append("Defeat the current enemy")
                elif entity.ai_state == AIState.LOOTING:
                    goals.append("Pick up nearby loot")
                elif entity.ai_state == AIState.RESTING_IN_TOWN:
                    goals.append("Rest and recover in town")
                elif entity.ai_state == AIState.HARVESTING:
                    goals.append("Harvest nearby resources")
            else:
                if entity.ai_state == AIState.GUARD_CAMP:
                    goals.append("Guard the camp from intruders")
                    goals.append("Patrol the perimeter")
                elif entity.ai_state == AIState.ALERT:
                    goals.append("Intruder detected! Engage the threat!")
                elif entity.ai_state == AIState.RETURN_TO_CAMP:
                    goals.append("Return to the safety of camp")
                elif entity.ai_state == AIState.HUNT:
                    goals.append("Hunt down a nearby target")
                elif entity.ai_state == AIState.COMBAT:
                    goals.append("Fight to the death")
                elif entity.ai_state == AIState.FLEE:
                    goals.append("Flee — too wounded to fight")
                elif entity.ai_state == AIState.WANDER:
                    goals.append("Wander and search for prey")
                if hp_ratio < 0.3:
                    goals.append("Desperate — need to escape")
                elif hp_ratio < 0.6:
                    goals.append("Wounded — be cautious")
                else:
                    goals.append("Feeling strong")

            entity.goals = goals

    def _update_ai_states(self, applied: list[ActionProposal]) -> None:
        """Propagate new AI states from brain decisions after action resolution."""
        for proposal in applied:
            entity = self._world.entities.get(proposal.actor_id)
            if entity is None:
                continue
            if proposal.new_ai_state is not None:
                entity.ai_state = AIState(proposal.new_ai_state)

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
            else:
                removed = self._world.remove_entity(eid)
                if removed:
                    logger.info("Tick %d: Entity %d (%s Lv%d) died.", self._world.tick, eid, removed.kind, removed.stats.level)
