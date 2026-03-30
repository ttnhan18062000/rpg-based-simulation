# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/__init__.py
"""Deterministic Concurrent RPG Engine."""

__version__ = "0.1.0"

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/__main__.py
"""Entry point: ``python -m src``.

Supports two modes:
  - ``python -m src``            → Launch FastAPI server with live visualization
  - ``python -m src cli``        → Headless CLI simulation (original mode)
"""

from __future__ import annotations

import argparse
import logging

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic Concurrent RPG Engine")
    sub = parser.add_subparsers(dest="command")

    # --- Server mode (default) ---
    srv = sub.add_parser("serve", help="Start the FastAPI visualization server (default)")
    srv.add_argument("--host", type=str, default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8000)
    srv.add_argument("--seed", type=int, default=42)
    srv.add_argument("--entities", type=int, default=10)
    srv.add_argument("--workers", type=int, default=4)
    srv.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING"])

    # --- Headless CLI mode ---
    cli = sub.add_parser("cli", help="Run headless CLI simulation")
    cli.add_argument("--seed", type=int, default=42)
    cli.add_argument("--ticks", type=int, default=200)
    cli.add_argument("--entities", type=int, default=10)
    cli.add_argument("--workers", type=int, default=4)
    cli.add_argument("--replay", type=str, default="replay.json")
    cli.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING"])

    return parser


def _run_server(args: argparse.Namespace) -> None:
    import uvicorn

    from src.api.app import create_app
    from src.config import SimulationConfig

    config = SimulationConfig(
        world_seed=args.seed,
        initial_entity_count=args.entities,
        num_workers=args.workers,
        log_level=args.log_level,
    )
    app = create_app(config)
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level.lower())


def _run_cli(args: argparse.Namespace) -> None:
    from src.ai.brain import AIBrain
    from src.config import SimulationConfig
    from src.core.models.enums import AIState, Domain, EnemyTier, EntityRole, Material
    from src.core.gameplay.faction import Faction, FactionRegistry
    from src.core.world.grid import Grid
    from src.core.entities.entity import Entity, Stats, Vector2, Inventory
    from src.core.models.world_state import WorldState
    from src.engine.conflict_resolver import ConflictResolver
    from src.engine.worker_pool import WorkerPool
    from src.engine.world_loop import WorldLoop
    from src.systems.world.generator import EntityGenerator
    from src.platform.rng import DeterministicRNG
    from src.platform.spatial_hash import SpatialHash
    from src.utils.logging import setup_logging
    from src.utils.replay import ReplayRecorder
    
    setup_logging(args.log_level)

    config = SimulationConfig(
        world_seed=args.seed,
        max_ticks=args.ticks,
        initial_entity_count=args.entities,
        num_workers=args.workers,
        replay_file=args.replay,
        log_level=args.log_level,
    )

    setup_logging(config.log_level)

    from src.core.registry.registry_loader import load_all_registries
    load_all_registries()

    rng = DeterministicRNG(config.world_seed)
    grid = Grid(config.grid_width, config.grid_height)
    spatial = SpatialHash(config.spatial_cell_size)
    world = WorldState(seed=config.world_seed, grid=grid, spatial_index=spatial)

    town_center = Vector2(config.town_center_x, config.town_center_y)

    # Place town tiles
    for ty in range(config.town_center_y - config.town_radius, config.town_center_y + config.town_radius + 1):
        for tx in range(config.town_center_x - config.town_radius, config.town_center_x + config.town_radius + 1):
            pos = Vector2(tx, ty)
            if grid.in_bounds(pos):
                grid.set(pos, Material.TOWN)

    # Place sanctuary tiles
    for sy in range(config.town_center_y - config.sanctuary_radius, config.town_center_y + config.sanctuary_radius + 1):
        for sx in range(config.town_center_x - config.sanctuary_radius, config.town_center_x + config.sanctuary_radius + 1):
            pos = Vector2(sx, sy)
            if grid.in_bounds(pos) and grid.get(pos) == Material.FLOOR:
                grid.set(pos, Material.SANCTUARY)

    # Place goblin camps
    generator = EntityGenerator(config, rng)
    camp_positions: list[Vector2] = []
    for camp_idx in range(config.num_camps):
        for attempt in range(50):
            cx = rng.next_int(Domain.SPAWN, 9000 + camp_idx, attempt, 0, config.grid_width - 1)
            cy = rng.next_int(Domain.SPAWN, 9000 + camp_idx, attempt + 100, 0, config.grid_height - 1)
            camp_pos = Vector2(cx, cy)
            if camp_pos.manhattan(town_center) < config.camp_min_distance_from_town:
                continue
            too_close = any(camp_pos.manhattan(e) < config.camp_radius * 4 for e in camp_positions)
            if too_close or not grid.in_bounds(camp_pos):
                continue
            for cty in range(cy - config.camp_radius, cy + config.camp_radius + 1):
                for ctx in range(cx - config.camp_radius, cx + config.camp_radius + 1):
                    cp = Vector2(ctx, cty)
                    if grid.in_bounds(cp) and grid.get(cp) == Material.FLOOR:
                        grid.set(cp, Material.CAMP)
            camp_positions.append(camp_pos)
            world.camps.append(camp_pos)
            logger.info("Placed goblin camp at %s", camp_pos)
            break

    # Spawn heroes via EntityBuilder
    from src.core.gameplay.classes import HeroClass, HERO_STARTING_GEAR
    from src.core.entities.entity_builder import EntityBuilder
    from src.core.data.hero_names import generate_hero_name
    from src.core.gameplay.buildings import Building

    class_choices = [HeroClass.WARRIOR, HeroClass.RANGER, HeroClass.MAGE, HeroClass.ROGUE]
    
    for h_idx in range(config.hero_count):
        hero_eid = world.allocate_entity_id()
        # Round-robin class selection
        hero_class = class_choices[h_idx % len(class_choices)]
        
        gear = HERO_STARTING_GEAR.get(hero_class, {})
        
        builder = (
            EntityBuilder(rng, hero_eid, tick=0)
            .kind("hero")
            .at(Vector2(config.town_center_x, config.town_center_y))
            .home(town_center)
            .faction(Faction.HERO_GUILD)
            .role(EntityRole.HERO)
        )
        # Assign traits first to generate name
        builder.with_traits(race_prefix="hero")
        hero_name = generate_hero_name(rng, hero_eid, 0, builder._traits)
        
        hero = (
            builder
            .with_identity(display_name=hero_name, generation=1)
            .with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3,
                             crit_rate=0.08, crit_dmg=1.8, evasion=0.03, gold=50)
            .with_randomized_stats()
            .with_hero_class(hero_class)
            .with_race_skills("hero")
            .with_class_skills(hero_class, level=1)
            .with_inventory(max_slots=config.hero_inventory_slots,
                            max_weight=config.hero_inventory_weight,
                            weapon=gear.get("weapon", "iron_sword"),
                            armor=gear.get("armor", "leather_vest"),
                            accessory=gear.get("accessory"))
            .with_starting_items(["small_hp_potion"] * 3)
            .with_home_storage()
            .with_talents(race="hero")
            .build()
        )
        world.add_entity(hero)

        # Register hero house as a building
        # Offset house positions to avoid stacking
        off_x = (h_idx % 3) - 1
        off_y = (h_idx // 3)
        hero_house_pos = Vector2(config.town_center_x + off_x, config.town_center_y + off_y + 1)
        world.buildings.append(Building(
            building_id=f"hero_house_{hero_eid}",
            name=f"{hero_name}'s House",
            pos=hero_house_pos,
            building_type="hero_house",
        ))

    # Spawn initial goblins (tiered)
    for i in range(1, config.initial_entity_count):
        entity = generator.spawn(world)
        world.add_entity(entity)

    # Spawn camp guards
    for camp_pos in camp_positions:
        chief = generator.spawn(world, tier=EnemyTier.ELITE, near_pos=camp_pos)
        world.add_entity(chief)
        for g in range(min(config.camp_max_guards, 3)):
            guard = generator.spawn(world, tier=EnemyTier.WARRIOR, near_pos=camp_pos)
            world.add_entity(guard)

    faction_reg = FactionRegistry.default()
    brain = AIBrain(config, rng, faction_reg)
    worker_pool = WorkerPool(config, brain, rng)
    conflict_resolver = ConflictResolver(config, rng)
    recorder = ReplayRecorder(config.replay_file, config.world_seed)

    loop = WorldLoop(
        config=config, world=world, worker_pool=worker_pool,
        conflict_resolver=conflict_resolver, generator=generator, recorder=recorder,
        rng=rng,
    )

    try:
        loop.run()
    except Exception as e:
        from src.utils.metrics import SIM_ERRORS_TOTAL
        SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="cli_main").inc()
        logger.exception("CLI Simulation crashed", extra={'component': 'cli_main'})
        raise
    finally:
        worker_pool.shutdown()

    logger.info("Done. Replay written to %s", config.replay_file)


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Default to serve mode if no subcommand given
    if args.command is None or args.command == "serve":
        if args.command is None:
            # Re-parse with serve defaults
            args = parser.parse_args(["serve"])
        _run_server(args)
    elif args.command == "cli":
        _run_cli(args)


if __name__ == "__main__":
    main()

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/actions/__init__.py
"""Action system: proposals, validation, and execution."""

from src.actions.base import ActionProposal
from src.actions.move import MoveAction
from src.actions.rest import RestAction
from src.actions.combat import CombatAction

__all__ = ["ActionProposal", "CombatAction", "MoveAction", "RestAction"]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/actions/base.py
"""Base action proposal — the universal currency between AI and World."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.models.enums import ActionType


@dataclass(frozen=True, slots=True)
class ActionProposal:
    """An intent produced by a worker thread.

    The WorldLoop validates and applies (or rejects) each proposal.
    """

    actor_id: int
    verb: ActionType
    target: Any = None
    reason: str = ""
    new_ai_state: int | None = None

    def __repr__(self) -> str:
        return f"Proposal(entity={self.actor_id}, {self.verb.name}, target={self.target}, reason={self.reason!r})"

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/actions/combat.py
"""CombatAction — validates and resolves attack proposals.

Damage calculation supports dual damage types (Physical / Magical) with
elemental tags.  The weapon’s damage_type determines which stat pair is
used (ATK/DEF vs MATK/MDEF).  Elemental tags on weapons apply a
vulnerability multiplier from the defender’s elem_vuln table.

Effective stats (base + equipment + status effects) are used throughout,
so territory debuffs and other effects are automatically applied.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.actions.damage import get_damage_calculator
from src.core.models.enums import ActionType, DamageType, Domain, Element
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.gameplay.items.item_registry import ITEM_REGISTRY

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG

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
        if attacker is None or not attacker.combat.alive:
            return False

        if isinstance(proposal.target, str) and proposal.target.startswith("BUILDING:"):
            bid = proposal.target.split(":")[1]
            target_b = next((b for b in world.buildings if b.building_id == bid), None)
            if not target_b or not target_b.is_functional:
                return False
            # Range check
            dist = attacker.spatial.pos.manhattan(target_b.spatial.pos)
            if dist > self._get_weapon_range(attacker):
                return False
            return True

        target_id: int = proposal.target
        defender = world.entities.get(target_id)
        if defender is None or not defender.combat.alive:
            logger.debug(
                "Entity %d attack on %s failed — target dead or missing",
                proposal.actor_id,
                target_id,
            )
            return False

        # Range check — use weapon range (default 1 for melee)
        weapon_range = self._get_weapon_range(attacker)
        dist = attacker.spatial.pos.manhattan(defender.spatial.pos)
        if dist > weapon_range:
            logger.debug("Entity %d attack on %d failed — out of range (%d > %d)",
                         proposal.actor_id, target_id, dist, weapon_range)
            return False

        # Line-of-sight check for ranged attacks (distance > 1)
        if dist > 1 and not world.grid.has_line_of_sight(
                attacker.spatial.pos.x, attacker.spatial.pos.y, defender.spatial.pos.x, defender.spatial.pos.y):
            logger.debug("Entity %d ranged attack on %d blocked — no line of sight",
                         proposal.actor_id, target_id)
            return False

        return True

    def apply(self, proposal: ActionProposal, world: WorldState) -> None:
        attacker = world.entities.get(proposal.actor_id)
        if attacker is None:
            return

        if isinstance(proposal.target, str) and proposal.target.startswith("BUILDING:"):
            bid = proposal.target.split(":")[1]
            target_b = next((b for b in world.buildings if b.building_id == bid), None)
            if target_b:
                # Buildings take 50% damage from basic attacks
                if attacker.identity.hero_class != 0:
                    dmg = attacker.combat.atk * 0.5
                    target_b.take_damage(dmg)
                    logger.info(f"Tick {world.tick}: {attacker.kind} #{attacker.id} damaged {target_b.name} for {dmg:.1f}")
                    attacker.progression.stamina = max(0, attacker.progression.stamina - 5)
                    from src.core.gameplay.attributes import speed_delay
                    attacker.next_act_at += speed_delay(attacker.combat.spd, "attack")
            return

        target_id: int = proposal.target
        defender = world.entities.get(target_id)
        if defender is None:
            return

        tick = world.tick
        cfg = self._config
        dist = attacker.spatial.pos.manhattan(defender.spatial.pos)

        # --- Evasion check ---
        defender_evasion = defender.combat.evasion
        
        # Agility impact: hit chance
        luck_mod = attacker.combat.luck * 0.002
        effective_evasion = max(0.0, defender_evasion - luck_mod)
        if self._rng.next_bool(Domain.COMBAT, defender.id, tick + 3, effective_evasion):
            logger.info(
                "Tick %d: Entity %d (%s) attack EVADED by Entity %d (%s)",
                tick, attacker.id, attacker.kind, defender.id, defender.kind,
            )
            if hasattr(world, "event_bus") and world.event_bus:
                from src.core.data.events import CombatEvent
                world.event_bus.publish(CombatEvent(
                    attacker_id=attacker.id,
                    defender_id=defender.id,
                    damage=0,
                    is_crit=False,
                    is_evasion=True,
                    skill_used="attack",
                    attacker_hp=attacker.combat.hp,
                    defender_hp=defender.combat.hp
                ))
            from src.core.gameplay.attributes import speed_delay
            attacker.next_act_at += speed_delay(attacker.combat.spd, "attack")
            return

        # --- Determine damage type and element from weapon ---
        dmg_type = DamageType.PHYSICAL
        element = Element.NONE
        if attacker.inventory and attacker.inventory.weapon:
            weapon_tmpl = ITEM_REGISTRY.get(attacker.inventory.weapon)
            if weapon_tmpl:
                dmg_type = weapon_tmpl.damage_type
                element = weapon_tmpl.element

        # --- Damage calculation (strategy pattern) ---
        calculator = get_damage_calculator(dmg_type)
        dmg_ctx = calculator.resolve(attacker, defender)

        # Pillar 3: Fractional Armor Mitigation
        # Formula: dmg = raw_atk * (raw_atk / (raw_atk + def*2))
        # This ensures high-defense entities are chipped but not instantly slaughtered.
        atk_final = int(dmg_ctx.atk_power * dmg_ctx.atk_mult)
        def_final = int(dmg_ctx.def_power * dmg_ctx.def_mult)
        
        raw_damage = int(atk_final * (atk_final / (atk_final + def_final * 2.0 + 1.0)))
        raw_damage = max(raw_damage, 1)
        variance = self._rng.next_float(Domain.COMBAT, attacker.id, tick + 2)
        damage = int(raw_damage * (1.0 + cfg.damage_variance * (variance - 0.5)))
        damage = max(damage, 1)

        # --- Metrics: Combat Event ---
        from src.utils.metrics import SIM_COMBAT_EVENTS
        SIM_COMBAT_EVENTS.labels(
            attacker_faction=Faction(attacker.identity.faction).name.lower(),
            defender_faction=Faction(defender.identity.faction).name.lower()
        ).inc()

        # --- Elemental vulnerability modifier ---
        if element != Element.NONE:
            elem_mult = defender.elemental_vulnerability(element)
            damage = max(1, int(damage * elem_mult))

        # --- Crit check ---
        crit_rate = attacker.combat.crit_rate
        crit_rate += attacker.combat.luck * 0.003
        is_crit = self._rng.next_bool(Domain.COMBAT, attacker.id, tick + 1, min(crit_rate, 0.8))
        if is_crit:
            damage = int(damage * attacker.combat.crit_dmg)
            
        defender.combat.hp -= damage
        # Build damage descriptor
        dmg_label = "MAG" if dmg_type == DamageType.MAGICAL else "PHY"
        elem_label = ""
        if element != Element.NONE:
            elem_label = f" [{Element(element).name}]"
        logger.info(
            "TICK_ACTION_COMBAT: [%s]%s(L%s) hit [%s]%s(L%s) for %s dmg. Def HP: %s/%s",
            attacker.id, attacker.kind, attacker.progression.level,
            defender.id, defender.kind, defender.progression.level,
            damage,
            max(defender.combat.hp, 0),
            defender.combat.max_hp,
        )
        
        if hasattr(world, "event_bus") and world.event_bus:
            from src.core.data.events import CombatEvent
            world.event_bus.publish(CombatEvent(
                attacker_id=attacker.id,
                defender_id=defender.id,
                damage=damage,
                is_crit=is_crit,
                is_evasion=False,
                skill_used="attack",
                attacker_hp=attacker.combat.hp,
                defender_hp=defender.combat.hp
            ))

        # --- Nemesis System: Grudge tracking ---
        if hasattr(defender, "mind"):
            # Every hit increases the grudge proportional to % of max HP lost
            hp_lost_ratio = damage / defender.combat.max_hp
            grudge_gain = hp_lost_ratio * 50.0
            defender.mind.grudges[attacker.id] = defender.mind.grudges.get(attacker.id, 0.0) + grudge_gain
            # Small mood drop when taking damage (fear/despair)
            defender.mind.mood = max(0.0, defender.mind.mood - hp_lost_ratio * 0.2)
            
            # --- Narrative Memory: TRAUMA ---
            if hp_lost_ratio > 0.15: # Significant hit
                defender.mind.memory_log.append({
                    "tick": tick,
                    "type": "TRAUMA",
                    "desc": f"Took massive damage ({damage}) from {attacker.kind} #{attacker.id}",
                    "impact": -hp_lost_ratio * 100.0,
                    "source_id": attacker.id
                })
        
        if hasattr(attacker, "mind") and hp_lost_ratio > 0.2:
            # --- Narrative Memory: TRIUMPH ---
            attacker.mind.memory_log.append({
                "tick": tick,
                "type": "TRIUMPH",
                "desc": f"Dealt massive damage ({damage}) to {defender.kind} #{defender.id}",
                "impact": hp_lost_ratio * 50.0,
                "target_id": defender.id
            })

        # --- Threat generation (epic-05 F3) ---
        threat = damage * cfg.threat_damage_mult
        from src.core.gameplay.classes import HeroClass
        if attacker.progression.hero_class in (HeroClass.WARRIOR, HeroClass.CHAMPION):
            threat *= cfg.threat_tank_class_mult
        defender.mind.threat_table[attacker.id] = defender.mind.threat_table.get(attacker.id, 0.0) + threat
        # LOGGING: Milestone 8 - Trace threat generation
        import logging
        logging.getLogger("combat").debug("Threat generated: Entity %d -> Entity %d, +%.2f", attacker.id, defender.id, threat)

        from src.core.gameplay.attributes import speed_delay
        attacker.next_act_at += speed_delay(attacker.combat.spd, "attack")

        # Stamina cost
        attacker.progression.stamina = max(0, attacker.progression.stamina - 3)

        # --- Attribute training from combat ---
        if attacker.attributes and attacker.attribute_caps:
            from src.core.gameplay.attributes import train_attributes
            train_attributes(attacker.attributes, attacker.attribute_caps, dmg_ctx.train_action, stats=attacker.stats, race=attacker.kind, talents=attacker.talents, weakness=attacker.weakness)
        if defender.attributes and defender.attribute_caps and defender.combat.alive:
            from src.core.gameplay.attributes import train_attributes
            train_attributes(defender.attributes, defender.attribute_caps, "defend", stats=defender.stats, race=defender.kind, talents=defender.talents, weakness=defender.weakness)

        # --- Veterancy (epic-18 F1) ---
        from src.core.models.enums import VeterancyRank

        def check_veterancy_rank_up(entity, world_ref) -> None:
            """Check and apply veterancy rank ups."""
            old_rank = entity.veterancy_rank
            new_rank = old_rank
            pts = entity.veterancy_points
            
            if pts >= 500: new_rank = VeterancyRank.LEGEND
            elif pts >= 200: new_rank = VeterancyRank.ELITE
            elif pts >= 80: new_rank = VeterancyRank.VETERAN
            elif pts >= 25: new_rank = VeterancyRank.BLOODED
            
            if new_rank > old_rank:
                entity.veterancy_rank = new_rank
                rank_name = VeterancyRank(new_rank).name.title()
                logger.info("Tick %s: Entity %s (%s) promoted to %s!", tick, entity.id, entity.kind, rank_name)

        # +1 pt per hit dealt
        attacker.veterancy_points += 1
        check_veterancy_rank_up(attacker, world)
        
        # +1 pt per hit taken and survived
        if defender.combat.alive:
            defender.veterancy_points += 1
            # Near death survival +3 pt
            if defender.combat.hp_ratio < 0.25:
                defender.mind.memory_log.append({"tick": tick, "type": "SURVIVAL", "impact": 1.5})
                
            if defender.combat.hp_ratio < 0.15:
                defender.combat.max_hp += 1
                logger.info("TICK_ACTION_COMBAT: [%s] %s (%s) survived near-death, MaxHP increased to %s",
                            tick, defender.id, defender.kind, defender.combat.max_hp)
                
            check_veterancy_rank_up(defender, world)

        # --- XP award on kill ---
        if not defender.combat.alive:
            # --- Nemesis System: Bad Memories ---
            if hasattr(defender, "mind"):
                # Record the region where death occurred
                from src.core.world.regions import find_region_at
                region = find_region_at(defender.spatial.pos, world.regions)
                region_id = region.region_id if region else None
                if region_id:
                    # Mark this region as dangerous (-0.5 sentiment)
                    defender.mind.memory_locations[region_id] = defender.mind.memory_locations.get(region_id, 0.0) - 0.5
                # Record the killer in memory for a massive grudge after respawn
                defender.mind.memory["last_killer_id"] = attacker.id
                defender.mind.mood = 0.2 # Respawns in a fearful state
            
            # +5 points for a kill (+10 if higher level)
            xp_gain = 5
            if defender.progression.level > attacker.progression.level:
                xp_gain = 10
            
            # Application of RPG rules
            from src.core.models.enums import TraitType
            if TraitType.TACTICAL in attacker.identity.traits:
                xp_gain = int(xp_gain * 1.2)
                
            # xp_gain = int(xp_gain * attacker.progression.xp_mult)
            attacker.progression.xp += xp_gain
            attacker.veterancy_points += xp_gain
            # --- Milestone 11: Track death for regional control ---
            from src.core.world.regions import find_region_at
            region = find_region_at(defender.spatial.pos, world.regions)
            if region:
                key = (int(defender.identity.faction), region.region_id)
                world.faction_deaths_per_region[key] = world.faction_deaths_per_region.get(key, 0) + 1

            # --- Pillar 4: Corpse Node (Continuity) ---
            from src.core.models import CorpseNode
            if hasattr(world, "corpse_nodes") and (defender.identity.role == "hero" or defender.identity.is_world_boss):
                node_id = world._next_corpse_id
                world._next_corpse_id += 1
                
                # 80% Gold retention in corpse, 20% to killer
                corpse_gold = int(defender.progression.gold * 0.8)
                looted_gold = defender.progression.gold - corpse_gold
                attacker.progression.gold += looted_gold
                
                # Drop non-equipped inventory
                corpse_items = []
                if defender.inventory:
                    corpse_items = list(defender.inventory.items)
                    defender.inventory.items = [] # Wipe hero inventory
                
                node = CorpseNode(
                    node_id=node_id,
                    entity_id=defender.id,
                    pos=defender.spatial.pos,
                    items=corpse_items,
                    gold=corpse_gold,
                    created_tick=tick
                )
                world.corpse_nodes[node_id] = node
                logger.info("Tick %s: Entity %s died -> Created CorpseNode #%s at %s", tick, defender.id, node_id, defender.spatial.pos)
            else:
                # Normal loot for non-heroes
                attacker.progression.gold += defender.progression.gold
                defender.progression.gold = 0

            # --- Pillar 5: Nemesis Evolution ---
            from src.systems.lifecycle.evolution_system import EvolutionSystem
            EvolutionSystem.on_hero_slain(attacker, defender, world)

            logger.info(
                "Tick %s: Entity %s (%s) gained %s XP from killing Entity %s (%s) [XP: %s/%s]",
                tick, attacker.id, attacker.kind, xp_gain,
                defender.id, defender.kind,
                attacker.progression.xp, attacker.progression.xp_to_next,
            )
            # --- Quest progress: HUNT ---
            if attacker.quests:
                from src.core.gameplay.quests import QuestType
                for q in attacker.quests:
                    if q.quest_type == QuestType.HUNT and not q.completed:
                        if q.target_kind == defender.kind:
                            just_done = q.advance()
                            if just_done:
                                from src.utils.metrics import SIM_QUEST_STATUS_TOTAL
                                SIM_QUEST_STATUS_TOTAL.labels(type=q.quest_type.name.lower(), status="completed").inc()
                                attacker.progression.gold += q.gold_reward
                                attacker.progression.xp += q.xp_reward
                                logger.info(
                                    "Tick %s: Entity %s completed quest '%s' → +%s gold, +%s XP",
                                    tick, attacker.id, q.title,
                                    q.gold_reward, q.xp_reward,
                                )
                                if hasattr(world, "event_bus") and world.event_bus:
                                    from src.core.data.events import QuestEvent
                                    world.event_bus.publish(QuestEvent(
                                        entity_id=attacker.id,
                                        quest_title=q.title,
                                        quest_type=q.quest_type.name,
                                        status="completed",
                                        gold_reward=q.gold_reward,
                                        xp_reward=q.xp_reward
                                    ))
                    elif q.quest_type.name == "BOUNTY" and not q.completed:
                        # Bounty completion check: kind matches boss display name or kind
                        if defender.identity.is_world_boss and (q.target_kind == defender.identity.display_name or q.target_kind == defender.kind):
                            just_done = q.advance()
                            if just_done:
                                from src.utils.metrics import SIM_QUEST_STATUS_TOTAL
                                SIM_QUEST_STATUS_TOTAL.labels(type="bounty", status="completed").inc()
                                attacker.progression.gold += q.gold_reward
                                attacker.progression.xp += q.xp_reward
                                attacker.progression.fame += 100
                                logger.info(
                                    "Tick %s: Entity %s completed BOUNTY '%s' → +%s gold, +%s XP, +100 Fame",
                                    tick, attacker.id, q.title,
                                    q.gold_reward, q.xp_reward,
                                )
                                if hasattr(world, "event_bus") and world.event_bus:
                                    from src.core.data.events import QuestEvent
                                    world.event_bus.publish(QuestEvent(
                                        entity_id=attacker.id,
                                        quest_title=q.title,
                                        quest_type="BOUNTY",
                                        status="completed",
                                        gold_reward=q.gold_reward,
                                        xp_reward=q.xp_reward
                                    ))

            # --- Calamity-Specific Rewards (Titles) ---
            if defender.identity.is_world_boss:
                title = f"Slayer of {defender.identity.display_name}"
                if title not in attacker.titles:
                    attacker.titles.append(title)
                    # Titles grant a permanent 5% ATK boost (simplified as flat addition for now)
                    # In a property-based architecture, this would be computed in StatsProxy
                    attacker.stats.combat.atk = int(attacker.stats.combat.atk * 1.05)
                    logger.info("Tick %s: Hero %s earned Title: %s! Permanent +5%% ATK bonus applied.",
                                tick, attacker.id, title)
                    # Note: World events for titles are handled in WorldLoop or via logging

    @staticmethod
    def _get_weapon_range(entity) -> int:
        """Return the weapon range of the entity's equipped weapon (default 1 = melee)."""
        if entity.inventory and entity.inventory.weapon:
            weapon_tmpl = ITEM_REGISTRY.get(entity.inventory.weapon)
            if weapon_tmpl:
                return weapon_tmpl.weapon_range
        return 1

    @staticmethod
    def _calculate_xp(attacker, defender, cfg) -> int:
        """XP = base * defender_level * scale, bonus for higher-tier enemies.
        Mobs learn at half the rate of heroes."""
        base = cfg.xp_per_kill_base
        level_mult = max(1, defender.progression.level)
        tier_bonus = 1.0 + defender.identity.tier * 0.5
        xp = int(base * level_mult * tier_bonus)
        
        from src.core.models.enums import EntityRole
        if attacker.identity.role == EntityRole.MOB:
            xp = int(xp * 0.5)
            
        return max(xp, 1)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/actions/damage.py
"""Damage calculation strategy pattern.

Abstract DamageCalculator with concrete subclasses for each damage type.
To add a new damage type (e.g. TRUE, HYBRID):
  1. Create a new DamageCalculator subclass.
  2. Register it in DAMAGE_CALCULATORS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.models.enums import DamageType

if TYPE_CHECKING:
    from src.core.entities.entity import Entity


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class DamageContext:
    """Resolved damage parameters from a calculator."""
    atk_power: int
    def_power: int
    atk_mult: float
    def_mult: float
    train_action: str


# ---------------------------------------------------------------------------
# Abstract calculator
# ---------------------------------------------------------------------------

class DamageCalculator(ABC):
    """Base class for damage type calculators.

    Subclass and implement:
      - damage_type: the DamageType enum value this handles
      - resolve(): extract atk/def power and attribute multipliers
    """

    @property
    @abstractmethod
    def damage_type(self) -> int:
        """The DamageType this calculator handles."""

    @abstractmethod
    def resolve(self, attacker: Entity, defender: Entity) -> DamageContext:
        """Resolve attack/defense power and multipliers for this damage type."""


# ---------------------------------------------------------------------------
# Physical damage
# ---------------------------------------------------------------------------

class PhysicalDamageCalculator(DamageCalculator):

    @property
    def damage_type(self) -> int:
        return DamageType.PHYSICAL

    def resolve(self, attacker: Entity, defender: Entity) -> DamageContext:
        atk_power = attacker.stats.combat.atk
        def_power = defender.stats.combat.def_

        atk_mult = 1.0
        def_mult = 1.0
        
        # Flanking check (1.3x damage)
        diff = attacker.spatial.pos - defender.spatial.pos
        # Note: dot product < 0 means attacker is in the 180-degree arc BEHIND the defender's facing
        facing = defender.spatial.facing
        if (diff.x * facing.x + diff.y * facing.y) < 0:
            atk_mult *= 1.3
            # We could emit a "Flank!" event here, but resolve() is usually pure.
            # We'll let the system handle the log/emit.

        if attacker.attributes:
            atk_mult *= (1.0 + attacker.attributes.str_ * 0.02)
        if defender.attributes:
            def_mult *= (1.0 + defender.attributes.vit * 0.01)

        return DamageContext(
            atk_power=atk_power,
            def_power=def_power,
            atk_mult=atk_mult,
            def_mult=def_mult,
            train_action="attack",
        )


# ---------------------------------------------------------------------------
# Magical damage
# ---------------------------------------------------------------------------

class MagicalDamageCalculator(DamageCalculator):

    @property
    def damage_type(self) -> int:
        return DamageType.MAGICAL

    def resolve(self, attacker: Entity, defender: Entity) -> DamageContext:
        atk_power = attacker.stats.combat.matk
        def_power = defender.stats.combat.mdef

        atk_mult = 1.0
        def_mult = 1.0
        if attacker.attributes:
            atk_mult = 1.0 + attacker.attributes.spi * 0.02
        if defender.attributes:
            def_mult = 1.0 + defender.attributes.wis * 0.01

        return DamageContext(
            atk_power=atk_power,
            def_power=def_power,
            atk_mult=atk_mult,
            def_mult=def_mult,
            train_action="magic_attack",
        )


# ---------------------------------------------------------------------------
# Registry — maps DamageType -> calculator instance
# ---------------------------------------------------------------------------

DAMAGE_CALCULATORS: dict[int, DamageCalculator] = {}

_physical = PhysicalDamageCalculator()
_magical = MagicalDamageCalculator()

DAMAGE_CALCULATORS[DamageType.PHYSICAL] = _physical
DAMAGE_CALCULATORS[DamageType.MAGICAL] = _magical

# Fallback for unknown types
DEFAULT_CALCULATOR: DamageCalculator = _physical


def get_damage_calculator(damage_type: int) -> DamageCalculator:
    """Look up the calculator for a damage type, falling back to physical."""
    return DAMAGE_CALCULATORS.get(damage_type, DEFAULT_CALCULATOR)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/actions/move.py
"""MoveAction — validates and applies movement proposals.

Territory tiles (TOWN, CAMP) are now passable for all factions.
The consequence of entering enemy territory (debuff + alert) is handled
by the WorldLoop after the move is applied.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.core.models.enums import ActionType
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)


class MoveAction:
    """Stateless handler for MOVE proposals."""

    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState, occupied: set[tuple[int, int]]) -> bool:
        if proposal.verb != ActionType.MOVE:
            return False

        entity = world.entities.get(proposal.actor_id)
        if entity is None or not entity.combat.alive:
            return False

        target: Vector2 = proposal.target
        if not world.grid.is_walkable(target):
            logger.debug("Entity %d blocked by terrain at %s", proposal.actor_id, target)
            return False

        if (target.x, target.y) in occupied:
            logger.debug("Entity %d blocked by occupant at %s", proposal.actor_id, target)
            return False

        return True

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        target: Vector2 = proposal.target
        old_pos = world.entities[proposal.actor_id].spatial.pos if proposal.actor_id in world.entities else None
        world.move_entity(proposal.actor_id, target)
        entity = world.entities.get(proposal.actor_id)
        if entity is not None:
            from src.core.gameplay.attributes import speed_delay
            spd = entity.stats.combat.spd
            # Road tiles grant a speed bonus
            if world.grid.is_road(target) or world.grid.is_bridge(target):
                spd = max(spd, int(spd * 1.3))
            delay = speed_delay(spd, "move", entity.stats.interaction_speed)
            # Engagement Lock: fleeing from adjacent hostiles costs double delay
            if entity.engaged_ticks >= 2:
                delay *= 2.0
                entity.engaged_ticks = 0  # reset after paying the penalty
            entity.next_act_at += delay
            # Stamina cost for moving
            entity.stats.progression.stamina = max(0, entity.stats.progression.stamina - 1)
            # Attribute training from movement
            if entity.attributes and entity.attribute_caps:
                from src.core.gameplay.attributes import train_attributes
                train_attributes(entity.attributes, entity.attribute_caps, "move", stats=entity.stats)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/actions/raid.py
"""RAID AI logic for faction aggression and building sabotage."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.actions.base import ActionProposal
from src.core.models.enums import ActionType, AIState, EntityRole

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.entities.entity import Entity

logger = logging.getLogger(__name__)

class RaidAI:
    """Specialized AI for faction raids targeting the town."""

    @staticmethod
    def propose(entity: Entity, world: WorldState) -> ActionProposal | None:
        """Propose a raid-related action (attack building or hero)."""
        # 1. Target heroes first if very close
        targets = world.spatial_index.query_radius(entity.spatial.pos, radius=5)
        heroes = [world.entities[tid] for tid in targets 
                  if tid in world.entities and world.entities[tid].identity.role == EntityRole.HERO]
        
        if heroes:
            # Target closest hero
            heroes.sort(key=lambda h: h.spatial.pos.manhattan(entity.spatial.pos))
            target_h = heroes[0]
            if entity.spatial.pos.manhattan(target_h.spatial.pos) <= 1:
                return ActionProposal(entity.id, ActionType.ATTACK, target=target_h.id, reason="Raid: Attack hero")
            else:
                return ActionProposal(entity.id, ActionType.MOVE, target=target_h.spatial.pos, reason="Raid: Move to hero")

        # 2. If no heroes near, target buildings
        if world.buildings:
            functional = [b for b in world.buildings if b.is_functional]
            if functional:
                functional.sort(key=lambda b: b.spatial.pos.manhattan(entity.spatial.pos))
                target_b = functional[0]
                
                if entity.spatial.pos.manhattan(target_b.spatial.pos) <= 1:
                    return ActionProposal(entity.id, ActionType.ATTACK, target=f"BUILDING:{target_b.building_id}", reason="Raid: Sabotage building")
                else:
                    return ActionProposal(entity.id, ActionType.MOVE, target=target_b.spatial.pos, reason="Raid: Move to building")

        return None

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/actions/repair.py
"""Stateless handler for repair."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.actions.base import ActionProposal

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class RepairAction:
    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState) -> bool:
        actor = world.entities.get(proposal.actor_id)
        if not actor or not actor.combat.alive: return False
        if actor.stats.progression.gold < 10.0: return False
        target_b = next((b for b in world.buildings if b.building_id == proposal.target), None)
        if not target_b: return False
        if actor.spatial.pos.manhattan(target_b.spatial.pos) > 1: return False
        return True

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        actor = world.entities.get(proposal.actor_id)
        target_b = next((b for b in world.buildings if b.building_id == proposal.target), None)
        if actor and target_b:
            actor.stats.progression.gold -= 10.0
            target_b.repair(50.0)
            logger.info(f"Tick {world.tick}: {actor.kind} #{actor.id} repaired {target_b.name}")
            actor.stats.progression.stamina = max(0, actor.stats.progression.stamina - 5)
            from src.core.gameplay.attributes import speed_delay
            actor.next_act_at += speed_delay(actor.stats.combat.spd, "building")

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/actions/rest.py
"""RestAction — entity idles and recovers slightly."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.core.models.enums import AIState, ActionType

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)


class RestAction:
    """Stateless handler for REST proposals."""

    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState) -> bool:
        if proposal.verb != ActionType.REST:
            return False
        entity = world.entities.get(proposal.actor_id)
        return entity is not None and entity.combat.alive

    # AI states that represent building interactions (higher delay)
    _BUILDING_STATES = frozenset({
        AIState.VISIT_SHOP, AIState.VISIT_BLACKSMITH, AIState.VISIT_GUILD,
        AIState.VISIT_CLASS_HALL, AIState.VISIT_INN, AIState.VISIT_HOME,
    })

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        entity = world.entities.get(proposal.actor_id)
        if entity is None:
            return
        # Minor HP recovery on rest
        if entity.stats.combat.hp < entity.stats.combat.max_hp:
            entity.stats.combat.hp = min(entity.stats.combat.hp + 1, entity.stats.combat.max_hp)
        from src.core.gameplay.attributes import speed_delay
        action_type = "building" if entity.mind.ai_state in RestAction._BUILDING_STATES else "rest"
        entity.next_act_at += speed_delay(entity.stats.combat.spd, action_type, entity.stats.interaction_speed)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/__init__.py
"""AI layer: perception, state machines, and decision-making."""

from src.ai.brain import AIBrain
from src.ai.perception import Perception

__all__ = ["AIBrain", "Perception"]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/brain.py
"""AIBrain — stateless decision engine with Utility AI goal selection.

Hybrid architecture:
  1. For "decision" states (IDLE, WANDER, RESTING_IN_TOWN, GUARD_CAMP),
     the GoalEvaluator scores all viable goals and picks one via weighted
     random.  The selected goal sets the AIState, then the state handler
     executes it.
  2. For "execution" states (HUNT, COMBAT, FLEE, LOOTING, VISIT_*, etc.),
     the state handler runs directly — the entity is already committed to
     an action and shouldn’t re-evaluate every tick.

Uses the STATE_HANDLERS registry from ``ai.states`` and the FactionRegistry
for faction-aware enemy/ally detection.
"""

from __future__ import annotations
from dataclasses import replace
from typing import Any, Protocol, TypeVar, runtime_checkable, TYPE_CHECKING

from src.core.models.enums import AIState, ActionType, Domain
from src.actions.base import ActionProposal
from src.ai.goals import GoalEvaluator
from src.ai.perception import Perception
from src.ai.states import AIContext, STATE_HANDLERS, IdleHandler
from src.core.gameplay.faction import FactionRegistry

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.entities.entity import Entity
    from src.core.models.snapshot import Snapshot
    from src.platform.rng import DeterministicRNG

_FALLBACK = IdleHandler()


class AIBrain:
    """Dispatches entity AI decisions based on their current state.

    Fully stateless — safe to call from any thread.
    """

    __slots__ = ("_config", "_rng", "_faction_reg", "_goal_evaluator")

    def __init__(
        self,
        config: SimulationConfig,
        rng: DeterministicRNG,
        faction_reg: FactionRegistry | None = None,
    ) -> None:
        self._config = config
        self._rng = rng
        self._faction_reg = faction_reg or FactionRegistry.default()
        self._goal_evaluator = GoalEvaluator()

    # States where the goal evaluator runs before the handler
    _DECISION_STATES = frozenset({
        AIState.IDLE, AIState.WANDER,
        AIState.HUNT, AIState.COMBAT, AIState.FLEE,
        AIState.RESTING_IN_TOWN, AIState.GUARD_CAMP,
    })

    def decide(self, actor: Entity, snapshot: Snapshot) -> tuple[AIState, ActionProposal]:
        """Run the AI Cognitive Pipeline for *actor*."""
        # --- Phase 1: Input (Sensory & Perception) ---
        ctx = self._sensory_perception_phase(actor, snapshot) # Steps 1 & 2
        
        # --- Phase 2: Internal State (Memory & Appraisal) ---
        self._memory_appraisal_phase(ctx) # Steps 3 & 4
        
        # --- Phase 3: Deliberation (Planning) ---
        selected_state = self._deliberation_tactical_phase(ctx) # Steps 5 & 6
        
        # --- Phase 4: Output (Proposal) ---
        return self._finalization_phase(ctx, selected_state) # Step 7

    def _sensory_perception_phase(self, actor: Entity, snapshot: Snapshot) -> AIContext:
        """Phase 1: Input. Gather raw data and apply selective attention."""
        ctx = AIContext(
            actor=actor,
            snapshot=snapshot,
            config=self._config,
            rng=self._rng,
            faction_reg=self._faction_reg,
        )
        
        # Step 1: Sensory (Gather data - handled by ctx.visible)
        
        # Step 2: Selective Attention (Filter saliency)
        # 1. Update Position History (Stuck Detection)
        actor.mind.pos_history.append(actor.spatial.pos)
        if len(actor.mind.pos_history) > 5:
            actor.mind.pos_history.pop(0)
            
        # 2. Rank by saliency: (Distance, Faction, Rarity)
        visible = ctx.visible
        def get_saliency(e):
            dist = actor.spatial.pos.manhattan(e.spatial.pos)
            is_hostile = self._faction_reg.is_hostile(actor.identity.faction, e.identity.faction)
            # Hostile/Rare entities have higher weight
            weight = 2.0 if is_hostile else 1.0
            rarity = getattr(e, 'rarity', 0)
            if isinstance(rarity, (int, float)) and rarity > 0:
                weight *= 2.0 # More importance to rare targets
            return weight / (dist + 1)
            
        ranked = sorted(visible, key=get_saliency, reverse=True)
        # Pillar 1: Selective Attention slots
        actor.mind.attention_pool = [e.id for e in ranked[:actor.mind.max_attention_slots]]
        
        # Actually filter ctx.visible for the rest of this tick's cognitive pipeline
        # (Decision Scorers and State Handlers will only see these entities)
        attention_set = set(actor.mind.attention_pool)
        ctx._visible = [e for e in visible if e.id in attention_set]
                
        return ctx

    def _memory_appraisal_phase(self, ctx: AIContext) -> None:
        """Phase 2: Internal State. Retrieve context and evaluate emotions."""
        actor = ctx.actor
        snapshot = ctx.snapshot
        
        # Step 3: Memory Recall (Retrieve Context)
        # 1. Remember visible hostile entities
        for e in ctx.visible:
            if self._faction_reg.is_hostile(actor.identity.faction, e.identity.faction):
                actor.mind.memory[e.id] = e.spatial.pos
        
        # 2. Fatigue Decay (Anti-loop)
        for rid in list(actor.mind.region_fatigue.keys()):
            val = actor.mind.region_fatigue[rid]
            actor.mind.region_fatigue[rid] = max(0.0, val - 0.005) # Slow decay

        # Step 4: Appraisal (Subjective Emotions)
        # 1. Boredom recovery & Emotional decay
        for gname in list(actor.mind.boredom_multipliers.keys()):
            val = actor.mind.boredom_multipliers[gname]
            if val < 1.0:
                actor.mind.boredom_multipliers[gname] = min(1.0, val + 0.02)
        
        for eme in list(actor.mind.emotional_state.keys()):
            val = actor.mind.emotional_state[eme]
            if val > 0:
                actor.mind.emotional_state[eme] = max(0.0, val - 0.01)

        # 3. Trigger Emotions & Mood (Pillar 1: Soul)
        # Influence mood from recent memory events
        recent_memories = [m for m in actor.mind.memory_log if (snapshot.tick - m.get("tick", 0)) < 100]
        for m in recent_memories:
            impact = m.get("impact", 0.0)
            if impact > 0:
                actor.mind.mood = min(1.0, actor.mind.mood + (impact * 0.02))
            else:
                actor.mind.mood = max(0.0, actor.mind.mood + (impact * 0.05)) # Trauma hits harder
                
        # 4. Physical Maintenance (Aging)
        if hasattr(actor, 'progression'):
            actor.progression.age_ticks += 1
            if actor.progression.age_ticks >= actor.progression.longevity_limit:
                actor.stats.combat.hp = 0
                return
            
        # 5. Narrative Memory: Discovery events
        region_id = getattr(actor, 'current_region_id', None)
        if region_id:
            # First-time DISCOVERY
            if region_id not in actor.mind.memory_locations:
                actor.mind.memory_locations[region_id] = 0.0  # neutral initial sentiment
                actor.mind.memory_log.append({
                    "tick": snapshot.tick,
                    "type": "DISCOVERY",
                    "desc": f"Discovered region {region_id}",
                    "impact": 2.0,
                })

        # 6. Specific Emotion Triggers
        if actor.stats.combat.hp_ratio < 0.3:
            current_panic = actor.mind.emotional_state.get("panic", 0.0)
            actor.mind.emotional_state["panic"] = min(1.0, current_panic + 0.1)

        # 6. Environmental Dread (Sentiment)
        region_id = getattr(actor, 'current_region_id', None)
        if region_id:
            sentiment = actor.mind.memory_locations.get(region_id, 0.0)
            if sentiment < -0.1: # Threshold for dread
                current_panic = actor.mind.emotional_state.get("panic", 0.0)
                actor.mind.emotional_state["panic"] = min(1.0, current_panic + 0.05)
            
        if len(actor.mind.pos_history) >= 5 and all(p == actor.mind.pos_history[0] for p in actor.mind.pos_history):
            actor.mind.emotional_state["stuck"] = 1.0
        else:
            actor.mind.emotional_state.pop("stuck", None)

        # 7. Relationship & Familiarity (Pillar 4: Social)
        # If we see a very high-familiarity hero, mood slightly improves
        for v in ctx.visible:
            fam = actor.identity.hero_familiarity.get(v.id, 0.0)
            if fam > 0.8:
                actor.mind.mood = min(1.0, actor.mind.mood + 0.005)

        # 8. Memory Decay: prune oldest low-impact memories
        actor.mind.prune_memories(max_entries=50)

    def _deliberation_tactical_phase(self, ctx: AIContext) -> AIState:
        """Phase 3: Deliberation. Choose the next state and plan 'how' (Tactical Intent)."""
        actor = ctx.actor
        
        # Step 5: Goal Deliberation (Goal scoring)
        if actor.mind.ai_state not in self._DECISION_STATES:
            return actor.mind.ai_state

        # Layer 1: Goal Lock — skip re-evaluation if committed
        from src.core.models.enums import EntityRole
        # Heroes and Elites/Bosses have sophisticated locking
        if actor.identity.role == EntityRole.HERO or (actor.identity.role == EntityRole.MOB and actor.identity.tier >= 1):
            if self._goal_evaluator.is_goal_locked(ctx):
                # Refresh tactical hints even if locked
                self._generate_tactical_hints(ctx, actor.mind.ai_state)
                return actor.mind.ai_state

        goal_scores = self._goal_evaluator.evaluate(ctx)
        if not goal_scores:
            return actor.mind.ai_state
            
        # Step 6: Selection with Temperature (Softmax)
        rng_val = self._rng.next_float(
            Domain.AI_DECISION, actor.id, ctx.snapshot.tick + 50)
        
        # Openness drives creativity/randomness
        temp = 0.05 + actor.identity.openness * 0.3
        selected = self._goal_evaluator.select(goal_scores, rng_val, temperature=temp)
        
        if selected:
            old_goal = actor.mind.last_goal

            # Layer 2: Record switch and apply commitment
            if old_goal and old_goal != selected.goal:
                cooldown_ticks = getattr(self._config, 'goal_cooldown_ticks', 5)
                actor.mind.goal_cooldowns[old_goal] = ctx.snapshot.tick + cooldown_ticks
                actor.mind.goal_switch_count += 1
                actor.mind.goal_committed_at = ctx.snapshot.tick

            actor.mind.ai_state = selected.target_state
            actor.mind.last_goal = selected.goal

            # Apply boredom penalty
            current = actor.mind.boredom_multipliers.get(selected.goal, 1.0)
            actor.mind.boredom_multipliers[selected.goal] = max(0.1, current * 0.8)
            
            # 3. Generate Tactical Hints (The "How" - Pillar 3)
            self._generate_tactical_hints(ctx, selected.target_state)
            
        return actor.mind.ai_state

    def _generate_tactical_hints(self, ctx: AIContext, state: AIState) -> None:
        """Pillar 3: Attach tactical guidance to the context."""
        actor = ctx.actor
        hints = ctx.tactical_hints
        
        # Example 1: Kiting for Ranged
        from src.core.models.enums import HeroClass
        ranged_classes = (HeroClass.RANGER, HeroClass.MAGE, HeroClass.SHARPSHOOTER, HeroClass.ARCHMAGE, HeroClass.CASTER)
        if actor.progression.hero_class in ranged_classes:
            hints["skirmish"] = True
            hints["min_dist"] = 3
        
        # Example 2: Flanking / Backstabbing (Melee High-Agi)
        if actor.progression.hero_class in (HeroClass.ROGUE, HeroClass.ASSASSIN):
            if any(v for v in ctx.visible if v.identity.faction == actor.identity.faction):
                hints["flanking"] = True

        # Example 3: Support Logic (Generous Thinking)
        if actor.identity.agreeableness > 0.7:
             # Look for low HP allies
             low_hp_ally = next((a for a in ctx.visible if a.identity.faction == actor.identity.faction and a.stats.combat.hp_ratio < 0.6), None)
             if low_hp_ally:
                 hints["support_target_id"] = low_hp_ally.id


    def _finalization_phase(self, ctx: AIContext, state: AIState) -> tuple[AIState, ActionProposal]:
        """Phase 4: Output. Proposal generation."""
        actor = ctx.actor
        handler = STATE_HANDLERS.get(state, _FALLBACK)
            
        # Step 7: Proposal Construction
        try:
            new_state, proposal = handler.handle(ctx)
            
            # Pillar 3: Hysteresis Force (Grounded)
            # If the evaluator decided to lock, we MUST respect it even if the 
            # handler wants to deviate (unless it's a critical HP override).
            if self._goal_evaluator.is_goal_locked(ctx):
                new_state = state # force back to selected state
                
            # Finalize proposal AI state
            proposal = replace(proposal, new_ai_state=int(new_state))
                
        except Exception as e:
            from src.utils.metrics import SIM_ERRORS_TOTAL
            SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component=f"ai_handler_{state.name.lower()}").inc()
            new_state = AIState.IDLE
            proposal = ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason=f"Handler {state.name} failed")

        # Apply Stance / Action Style
        style = getattr(actor.mind, 'action_style', 'balanced')
        if style != "balanced":
            proposal = replace(proposal, reason=f"[{style}] {proposal.reason}")
            
        # Update heuristics
        if proposal.verb == ActionType.REST:
            actor.consecutive_idle_ticks += 1
        else:
            actor.consecutive_idle_ticks = 0

        return new_state, proposal

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/flow_fields.py
"""Vector Flow Fields (Dijkstra Maps) for global navigation.

A Flow Field is a grid of vectors pointing toward a specific target location.
It allows O(1) pathfinding for many entities targeting the same destination
(e.g., all heroes returning to town).

Performance:
- Calculation: O(N log N) or O(N) using Breadth-First Search (Dijkstra).
- Lookup: O(1) per entity.
- Memory: 512x512 grid = 262,144 vectors (approx 2MB as float16).
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING
from src.core.models import Vector2, FloatVector2
from src.ai.pathfinding import tile_cost

if TYPE_CHECKING:
    from src.core.models.snapshot import SnapshotGrid

class FlowField:
    """A pre-calculated grid of direction vectors toward a single target."""
    
    __slots__ = ("target", "vectors", "width", "height", "created_at")
    
    def __init__(self, target: Vector2, width: int, height: int, tick: int = 0):
        self.target = target
        self.width = width
        self.height = height
        self.created_at = tick
        # Store as a flat list for performance: idx = y * width + x
        # Each element is a tuple (dx, dy) or None if unreachable
        self.vectors: list[tuple[int, int] | None] = [None] * (width * height)

    def get_vector(self, pos: Vector2 | FloatVector2) -> FloatVector2 | None:
        """Get the direction vector at the given position using bilinear interpolation for smoothing."""
        if not (0 <= pos.x < self.width - 1 and 0 <= pos.y < self.height - 1):
            # Fallback for boundaries
            x, y = int(max(0, min(self.width-1, pos.x))), int(max(0, min(self.height-1, pos.y)))
            v = self.vectors[y * self.width + x]
            return FloatVector2(v[0], v[1]).normalize() if v else None
            
        x0, y0 = int(pos.x), int(pos.y)
        x1, y1 = x0 + 1, y0 + 1
        fx, fy = pos.x - x0, pos.y - y0
        
        # Get vectors at the 4 corners
        v00 = self.vectors[y0 * self.width + x0]
        v10 = self.vectors[y0 * self.width + x1]
        v01 = self.vectors[y1 * self.width + x0]
        v11 = self.vectors[y1 * self.width + x1]
        
        # Interpolation weights
        w00 = (1 - fx) * (1 - fy)
        w10 = fx * (1 - fy)
        w01 = (1 - fx) * fy
        w11 = fx * fy
        
        vx, vy = 0.0, 0.0
        total_w = 0.0
        
        for v, w in [(v00, w00), (v10, w10), (v01, w01), (v11, w11)]:
            if v:
                vx += v[0] * w
                vy += v[1] * w
                total_w += w
        
        if total_w < 0.01:
            return None
            
        return FloatVector2(vx / total_w, vy / total_w).normalize()


class FlowFieldManager:
    """Manages creation and caching of flow fields for static locations."""
    
    _instance: FlowFieldManager | None = None
    
    def __init__(self):
        # target_pos_tuple -> FlowField
        self._cache: dict[tuple[int, int], FlowField] = {}
        self.default_ttl = 5

    @classmethod
    def get_instance(cls) -> FlowFieldManager:
        if cls._instance is None:
            cls._instance = FlowFieldManager()
        return cls._instance

    def get_flow_field(self, target: Vector2, grid: SnapshotGrid, current_tick: int = 0) -> FlowField:
        """Returns a cached flow field for the target, or generates a new one."""
        key = (target.x, target.y)
        if key in self._cache:
            ff = self._cache[key]
            if self._is_static_target(target, grid) or (current_tick - ff.created_at < self.default_ttl):
                return ff
            
        field = self._generate_dijkstra_map(target, grid, current_tick)
        self._cache[key] = field
        return field

    def _is_static_target(self, target: Vector2, grid: SnapshotGrid) -> bool:
        """Returns True if the target is a permanent location (Town/Camp)."""
        # Towns and Camps are static and never expire from cache
        if hasattr(grid, 'is_town') and grid.is_town(target):
            return True
        if hasattr(grid, 'is_camp') and grid.is_camp(target):
            return True
        return False

    def _generate_dijkstra_map(self, target: Vector2, grid: SnapshotGrid, tick: int = 0) -> FlowField:
        """Generate a Dijkstra Map using Breadth-First Search."""
        width, height = grid.width, grid.height
        field = FlowField(target, width, height, tick)
        
        # 1. Distances grid (infinity default)
        distances = [float('inf')] * (width * height)
        distances[target.y * width + target.x] = 0
        
        # 2. Priority Queue (Dijkstra)
        import heapq
        queue = [(0.0, target.x, target.y)]
        
        # 3. Fill distances
        while queue:
            d, cx, cy = heapq.heappop(queue)
            
            if d > distances[cy * width + cx]:
                continue
            
            # Check 8 neighbors
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0: continue
                    nx, ny = cx + dx, cy + dy
                    
                    if 0 <= nx < width and 0 <= ny < height:
                        npos = Vector2(nx, ny)
                        if not grid.is_walkable(npos):
                            continue
                        
                        # Use tile_cost (terrain awareness)
                        t_cost = tile_cost(grid, npos)
                        
                        # Diagonal multiplier
                        move_cost = t_cost * (1.414 if dx != 0 and dy != 0 else 1.0)
                        new_dist = d + move_cost
                        
                        idx = ny * width + nx
                        if new_dist < distances[idx]:
                            distances[idx] = new_dist
                            heapq.heappush(queue, (new_dist, nx, ny))

        # 4. Generate vectors from distances (gradient descent)
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                if distances[idx] == float('inf') or (x == target.x and y == target.y):
                    continue
                
                # Look for neighbor with lowest distance
                best_v = None
                min_d = distances[idx]
                
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            nd = distances[ny * width + nx]
                            if nd < min_d:
                                min_d = nd
                                best_v = (dx, dy)
                
                field.vectors[idx] = best_v
                
        return field

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/goal_evaluator.py
"""Backward-compatibility shim — re-exports from ``src.ai.goals``.

The monolithic goal evaluator has been refactored into a plugin-based
system under ``src/ai/goals/``.  This module re-exports the key symbols
so any existing imports continue to work.

Prefer importing from ``src.ai.goals`` directly in new code.
"""

from src.ai.goals.base import GoalScore, GoalEvaluator, GOAL_REGISTRY  # noqa: F401

__all__ = ["GoalScore", "GoalEvaluator", "GOAL_REGISTRY"]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/goals/__init__.py
"""AI Goal scoring plugin system.

Each goal is a GoalScorer subclass registered in GOAL_REGISTRY.
The GoalEvaluator iterates all registered scorers to produce ranked goals.
"""

from src.ai.goals.base import GoalScorer, GoalScore, GoalEvaluator, GOAL_REGISTRY
from src.ai.goals.registry import register_all_goals

# Auto-register all built-in goals on import
register_all_goals()

__all__ = [
    "GoalScorer",
    "GoalScore",
    "GoalEvaluator",
    "GOAL_REGISTRY",
]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/goals/base.py
"""Base classes for the Goal scoring plugin system.

GoalScorer   — Abstract base class; subclass and implement `score()`.
GoalScore    — A (goal_name, score, target_state) tuple for selection.
GoalEvaluator— Iterates registered scorers, filters, sorts, selects.
GOAL_REGISTRY— Module-level list where scorers are registered.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.models.enums import AIState

if TYPE_CHECKING:
    from src.ai.states import AIContext


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class GoalScore:
    """A scored goal ready for selection."""
    goal: str
    score: float
    target_state: AIState


# ---------------------------------------------------------------------------
# Abstract scorer
# ---------------------------------------------------------------------------

class GoalScorer(ABC):
    """Base class for all goal scorers.

    Subclass this and implement:
      - name:         unique goal identifier string
      - target_state: AIState the entity transitions to if this goal wins
      - score(ctx):   return a float utility score (<=0 means non-viable)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique goal identifier (e.g. 'combat', 'flee')."""

    @property
    @abstractmethod
    def target_state(self) -> AIState:
        """AIState to transition to when this goal is selected."""

    @abstractmethod
    def score(self, ctx: AIContext) -> float:
        """Score this goal for the given entity context.

        Returns a float where higher = more desirable.
        Scores <= 0.0 are filtered out as non-viable.
        """

    def evaluate(self, ctx: AIContext) -> GoalScore:
        """Convenience: score and wrap into GoalScore."""
        return GoalScore(
            goal=self.name,
            score=self.score(ctx),
            target_state=self.target_state,
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GOAL_REGISTRY: list[GoalScorer] = []


def register_goal(scorer: GoalScorer) -> GoalScorer:
    """Register a GoalScorer instance in the global registry."""
    GOAL_REGISTRY.append(scorer)
    return scorer


# ---------------------------------------------------------------------------
# Modifiers (Biases)
# ---------------------------------------------------------------------------

class ScoreModifier(ABC):
    """Interface for modifying a GoalScore based on external factors."""
    @abstractmethod
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        """Apply modification to the score object in-place."""

class BoredomModifier(ScoreModifier):
    """Applies actor's boredom multipliers to current scores."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        multiplier = ctx.actor.boredom_multipliers.get(score.goal, 1.0)
        score.score *= multiplier

class LifeStageModifier(ScoreModifier):
    """Heuristic based on level brackets to differentiate progression focus."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        level = ctx.actor.progression.level
        goal = score.goal
        
        # Early Stage (1-10)
        if level <= 10:
            if goal in ("explore", "rest"): score.score *= 1.3
            if goal in ("trade", "combat"): score.score *= 0.8
        # Mid Stage (11-20)
        elif level <= 20:
            if goal in ("combat", "loot"): score.score *= 1.2
            if goal == "rest": score.score *= 0.9
        # Late Stage (21+)
        else:
            if goal in ("social", "trade", "craft"): score.score *= 1.4
            if goal == "explore": score.score *= 0.7

class PersonalityModifier(ScoreModifier):
    """Biases scores based on OCEAN personality traits."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        identity = ctx.actor.identity
        goal = score.goal
        
        if goal == "explore":
            score.score *= (0.5 + identity.openness)
        elif goal in ("rest", "craft"):
            score.score *= (0.5 + identity.conscientiousness)
        elif goal == "social":
            score.score *= (0.5 + identity.extraversion)
        elif goal == "trade":
            # Agreeableness might affect likelihood to visit shops (better deals or social interaction)
            score.score *= (0.5 + identity.agreeableness)
        elif score.goal == "flee":
            score.score *= (0.5 + identity.neuroticism)
        elif goal == "combat":
            # Anxious entities are less aggressive
            score.score *= (1.2 - identity.neuroticism)

class StuckModifier(ScoreModifier):
    """Encourages resting/idling if the entity is stuck (emotional state)."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        if ctx.actor.mind.emotional_state.get("stuck", 0.0) > 0:
            if score.goal in ("rest", "social"):
                score.score *= 2.0
            if score.goal in ("explore", "combat", "loot"):
                score.score *= 0.5

class HysteresisModifier(ScoreModifier):
    """Provides a boost to the currently active goal to prevent jitter.
    
    Boost scales with commitment duration:
      base=1.25 + 0.05 * min(ticks_held, 10) → up to 1.75x after 10 ticks.
    """
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        if ctx.actor.mind.last_goal == score.goal:
            ticks_held = max(0, ctx.snapshot.tick - ctx.actor.mind.goal_committed_at)
            boost = 1.25 + 0.05 * min(ticks_held, 10)
            score.score *= boost


class CooldownModifier(ScoreModifier):
    """Penalizes recently abandoned goals to prevent flip-flopping.
    
    If the goal is on cooldown (tick < expiry), multiply score by
    config.goal_cooldown_penalty (default 0.5).
    """
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        cooldowns = ctx.actor.mind.goal_cooldowns
        expiry = cooldowns.get(score.goal)
        if expiry is not None and ctx.snapshot.tick < expiry:
            penalty = getattr(ctx.config, 'goal_cooldown_penalty', 0.5)
            score.score *= penalty


class MemoryModifier(ScoreModifier):
    """Biases scores based on accumulated narrative memories.

    - High glory  → stronger combat preference
    - High trauma → stronger flee preference
    - Discoveries → stronger explore preference
    """
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        mind = ctx.actor.mind
        goal = score.goal

        if goal == "combat":
            glory = mind.total_glory()
            if glory > 0:
                score.score *= 1.0 + glory / 100.0
            
            # Nemesis fear: discourage fighting a high-grudge rival directly
            enemy = ctx.nearest_enemy()
            if enemy and mind.grudges.get(enemy.id, 0.0) > 30.0:
                score.score *= 0.1
        elif goal == "flee":
            trauma = mind.total_trauma()
            if trauma < 0:
                score.score *= 1.0 + abs(trauma) / 100.0
            
            # Nemesis bias: if a known nemesis is visible, further boost flee
            enemy = ctx.nearest_enemy()
            if enemy and mind.grudges.get(enemy.id, 0.0) > 30.0:
                score.score *= 1.5
        elif goal == "explore":
            discoveries = sum(
                1 for e in mind.memory_log if e.get("type") == "DISCOVERY"
            )
            if discoveries > 0:
                score.score *= 1.0 + discoveries / 20.0


class EmotionalModifier(ScoreModifier):
    """Biases scores based on short-term emotional states (Panic, etc.)."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        emotions = ctx.actor.mind.emotional_state
        goal = score.goal
        
        panic = emotions.get("panic", 0.0)
        if panic > 0:
            if goal == "flee":
                score.score *= (1.0 + panic * 5.0)
            if goal in ("combat", "loot", "trade"):
                score.score *= max(0.0, 1.0 - panic)

class SkirmishModifier(ScoreModifier):
    """Biases ranged entities towards kiting / maintaining distance."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        from src.core.models.enums import HeroClass
        ranged_classes = (HeroClass.RANGER, HeroClass.MAGE, HeroClass.SHARPSHOOTER, HeroClass.ARCHMAGE, HeroClass.CASTER)
        
        if ctx.actor.progression.hero_class in ranged_classes:
            goal = score.goal
            # If a hostile is adjacent, boost flee or move_away
            if goal in ("flee", "move"):
                target_id = ctx.actor.mind.combat_target_id
                if target_id:
                    target_pos = ctx.actor.mind.memory.get(target_id)
                    if target_pos:
                        dist = ctx.actor.spatial.pos.manhattan(target_pos)
                        if dist <= 3:
                            score.score *= 2.0


class AmbitionModifier(ScoreModifier):
    """Biases scores based on the actor's Life Directive (Obsession)."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        directive = getattr(ctx.actor.identity, "life_directive", None)
        if not directive:
            return
            
        goal = score.goal
        # Pillar 6: Narrative Biases
        if directive == "DRAGON_SLAYER":
            if goal == "combat": score.score *= 1.5
            if goal == "explore": score.score *= 1.2
        elif directive == "CRAFTER":
            if goal == "craft": score.score *= 1.7
            if goal == "loot": score.score *= 1.3
        elif directive == "MERCHANT":
            if goal == "trade": score.score *= 1.6
            if goal == "social": score.score *= 1.3
        elif directive == "COLLECTOR":
            if goal == "loot": score.score *= 1.7
            if goal == "explore": score.score *= 1.2
        elif directive == "EXPLORATION":
            if goal == "explore": score.score *= 1.6
            if goal == "loot": score.score *= 1.2

class FatigueModifier(ScoreModifier):
    """Penalty for goals that stay in the same region too long (Anti-Loop)."""
    def modify(self, score: GoalScore, ctx: AIContext) -> None:
        rid = ctx.actor.current_region_id
        if not rid:
            return
            
        fatigue = ctx.actor.mind.region_fatigue.get(rid, 0.0)
        if fatigue > 0:
            # Penalize the goals that keep us in the current region
            if score.goal in ("explore", "combat", "loot"):
                score.score *= (1.0 - fatigue * 0.5)

# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class GoalEvaluator:
    """Scores all registered goals and selects one via weighted random.

    Usage::

        evaluator = GoalEvaluator()
        scores = evaluator.evaluate(ctx)
        goal = evaluator.select(scores, rng_value)
    """

    def __init__(self, modifiers: list[ScoreModifier] | None = None) -> None:
        self.modifiers = modifiers if modifiers is not None else [
            BoredomModifier(),
            LifeStageModifier(),
            PersonalityModifier(),
            EmotionalModifier(),
            HysteresisModifier(),
            CooldownModifier(),
            MemoryModifier(),
            StuckModifier(),
            SkirmishModifier(),
            AmbitionModifier(),
            FatigueModifier(),
        ]

    def evaluate(self, ctx: AIContext) -> list[GoalScore]:
        """Score all registered goals, filter non-viable, sort descending."""
        scores = [scorer.evaluate(ctx) for scorer in GOAL_REGISTRY]
        
        # Apply modifiers (Boredom, Personality, Life-Cycle, etc.)
        for s in scores:
            for modifier in self.modifiers:
                modifier.modify(s, ctx)
        
        scores = [s for s in scores if s.score > 0.0]
        scores.sort(key=lambda g: g.score, reverse=True)
        return scores

    def is_goal_locked(self, ctx: AIContext) -> bool:
        min_ticks = getattr(ctx.config, 'min_commitment_ticks', 3)
        committed_at = ctx.actor.mind.goal_committed_at
        ticks_held = ctx.snapshot.tick - committed_at

        # print(f"DEBUG_LOCK: actor={ctx.actor.id} tick={ctx.snapshot.tick} committed_at={committed_at} ticks_held={ticks_held} min_ticks={min_ticks} hp={ctx.actor.stats.combat.hp_ratio}")

        if ticks_held < min_ticks:
            # Soul/Personality override: fear breaks the lock early
            panic = ctx.actor.mind.emotional_state.get("panic", 0.0)
            if ctx.actor.stats.combat.hp_ratio < 0.5 and (ctx.actor.identity.neuroticism > 0.5 or panic > 0.5):
                return False
            # Critical override for all: near death breaks the lock
            if ctx.actor.stats.combat.hp_ratio < 0.15:
                return False
            return True
        return False

    @staticmethod
    def select(
        scores: list[GoalScore],
        rng_value: float,
        top_n: int = 3,
        temperature: float = 0.2,
    ) -> GoalScore | None:
        """Select a goal via Softmax weighted random from top N candidates.

        Args:
            scores: Sorted list of GoalScore (descending).
            rng_value: Random float [0, 1) for selection.
            top_n: How many top goals to consider.
            temperature: Softmax smoothing factor (higher = more random).

        Returns:
            Selected GoalScore, or None if no viable goals.
        """
        if not scores:
            return None

        candidates = scores[:top_n]
        if len(candidates) == 1:
            return candidates[0]

        # Softmax: w_i = exp(score / temperature)
        # Shift by max_score for numerical stability
        max_score = candidates[0].score
        import math
        weights = [math.exp((c.score - max_score) / temperature) for c in candidates]
        total = sum(weights)

        # Weighted selection
        target = rng_value * total
        cumulative = 0.0
        for i, w in enumerate(weights):
            cumulative += w
            if target <= cumulative:
                return candidates[i]

        return candidates[-1]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/goals/registry.py
"""Goal scorer registration.

Call ``register_all_goals()`` once at import time to populate GOAL_REGISTRY.
To add a custom goal, either append to this function or call
``register_goal()`` directly from your own module.
"""

from __future__ import annotations

from src.ai.goals.base import register_goal
from src.ai.goals.scorers import (
    CombatGoal,
    FleeGoal,
    ExploreGoal,
    LootGoal,
    TradeGoal,
    RestGoal,
    CraftGoal,
    SocialGoal,
    GuardGoal,
    CorpseScorer,
)

_registered = False


def register_all_goals() -> None:
    """Register all built-in goal scorers (idempotent)."""
    global _registered
    if _registered:
        return
    _registered = True

    register_goal(CombatGoal())
    register_goal(FleeGoal())
    register_goal(ExploreGoal())
    register_goal(LootGoal())
    register_goal(TradeGoal())
    register_goal(RestGoal())
    register_goal(CraftGoal())
    register_goal(SocialGoal())
    register_goal(GuardGoal())
    register_goal(CorpseScorer())

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/goals/scorers.py
"""Built-in GoalScorer implementations.

Each class is a self-contained scoring unit.  To add a new goal:
  1. Create a new GoalScorer subclass here (or in a separate file).
  2. Register it in ``registry.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.ai.goals.base import GoalScorer
from src.core.models.enums import AIState
from src.core.gameplay.faction import Faction
from src.core.entities.traits import aggregate_trait_stats, aggregate_trait_utility

if TYPE_CHECKING:
    from src.ai.states import AIContext


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _trait_utility(ctx: AIContext):
    return aggregate_trait_utility(ctx.actor.identity.traits)


def _trait_stats(ctx: AIContext):
    return aggregate_trait_stats(ctx.actor.identity.traits)


def _is_hero(ctx: AIContext) -> bool:
    return ctx.actor.identity.faction == Faction.HERO_GUILD


def _current_region_difficulty(ctx: AIContext) -> int:
    """Return difficulty tier of the region the actor is currently standing in (0 if none)."""
    rid = ctx.actor.current_region_id
    if not rid:
        return 0
    for r in ctx.snapshot.regions:
        if r.region_id == rid:
            return r.difficulty
    return 0


def _region_danger_penalty(ctx: AIContext) -> float:
    """Penalty when hero is in a region too dangerous for their level.

    Rule: region is dangerous when difficulty * 3 > hero_level + 3.
    Returns a value >= 0 (0 = no penalty, higher = more dangerous).
    """
    diff = _current_region_difficulty(ctx)
    if diff <= 0:
        return 0.0
    level = ctx.actor.progression.level
    danger_threshold = diff * 3
    comfort_ceiling = level + 3
    if danger_threshold <= comfort_ceiling:
        return 0.0
    return min((danger_threshold - comfort_ceiling) * 0.05, 0.4)


# ---------------------------------------------------------------------------
# Combat — seek and fight enemies
# ---------------------------------------------------------------------------

class CombatGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "combat"

    @property
    def target_state(self) -> AIState:
        return AIState.HUNT

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.combat.hp_ratio
        # Heroes start less aggressive (0.1) than wild mobs (0.3)
        base = 0.1 if _is_hero(ctx) else 0.3

        enemy = ctx.nearest_enemy()
        if enemy is not None:
            dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
            base += 0.5 * max(0, 1.0 - dist / 10.0)
            enemy_power = enemy.combat.atk + enemy.combat.matk
            my_power = actor.combat.atk + actor.combat.matk
            if my_power > enemy_power * 1.2:
                base += 0.2
            elif enemy_power > my_power * 1.5:
                base -= 0.3
        else:
            base -= 0.2

        # Milestone 7: Hero Renown Factor (Flee from legends!)
        if enemy is not None and enemy.identity.faction == Faction.HERO_GUILD:
            fame = getattr(enemy.progression, "fame", 0)
            if fame > 100:
                base -= 0.6  # Legendary hero: very scary
            elif fame > 50:
                base -= 0.3  # Well-known hero: intimidating
            elif fame > 20:
                base -= 0.1  # Rising star

        # Base aggression boosted for melee distance
        if enemy is not None:
            dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
            if dist <= 1:
                base += 0.4  # Melee "stickiness"

        if hp_ratio < 0.3:
            base -= 0.6 * (1.0 - hp_ratio)
        elif hp_ratio < 0.6:
            base -= 0.2 * (1.0 - hp_ratio)

        # Brave heroes are significantly more aggressive
        bravery = actor.mind.emotional_state.get("bravery", 0.5)
        neuroticism = getattr(actor.identity, "neuroticism", 0.5)
        # Check for BRAVE trait explicitly since emotional_state might be default
        from src.core.entities.traits import TraitType
        if TraitType.BRAVE in actor.identity.traits:
            base += 0.8  # Aggressively stay in the fight!
        
        # Neuroticism impact (Directly in scorer to override modifiers if needed)
        base += (0.5 - neuroticism) * 0.6
        base += (bravery - 0.5) * 0.4

        # Mobs are more aggressive when defending home territory
        if not _is_hero(ctx):
            from src.ai.states import is_on_home_territory
            if is_on_home_territory(ctx):
                base += 0.3  # territorial aggression bonus
            if enemy is not None:
                base += 0.15  # mobs always eager to fight intruders
        else:
            # Heroes are less eager to fight in regions above their level
            base -= _region_danger_penalty(ctx)

        base += _trait_utility(ctx).combat
        # Hero urgency boost: if an enemy is close, combat is mandatory
        if _is_hero(ctx) and enemy is not None and dist <= 3:
            base += 1.0 # Significant boost to override town activities
        return base


# ---------------------------------------------------------------------------
# Flee — retreat to safety
# ---------------------------------------------------------------------------

class FleeGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "flee"

    @property
    def target_state(self) -> AIState:
        return AIState.FLEE

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.stats.combat.hp_ratio

        # Layer 3: Threshold Deadband — use different thresholds for
        # entering vs exiting flee to prevent healing oscillation.
        currently_fleeing = actor.mind.ai_state == AIState.FLEE
        flee_exit = getattr(ctx.config, 'flee_exit_threshold', 0.5)

        # If currently fleeing and HP is still below exit threshold, stay fleeing
        if currently_fleeing and hp_ratio <= flee_exit:
            # Strong base to maintain flee commitment
            base = 0.8 + (flee_exit - hp_ratio) * 1.5
            base += _trait_utility(ctx).flee
            return base

        # If currently fleeing but HP is above exit threshold, allow stopping
        if currently_fleeing and hp_ratio > flee_exit:
            # Low score — let other goals win
            base = 0.1
            base += _trait_utility(ctx).flee
            return base

        # Soul Pillar (Memory): Nemesis panic
        enemy = ctx.nearest_enemy()
        if enemy and actor.mind.grudges.get(enemy.id, 0.0) > 30.0 and hp_ratio < 0.6:
            # Immediate panic response
            return 2.0 + _trait_utility(ctx).flee
        
        # Normal enter-flee logic (not currently fleeing)
        flee_threshold = ctx.config.flee_hp_threshold
        flee_threshold += _trait_stats(ctx).flee_threshold_mod
        # Heroes flee earlier in regions above their comfort zone (epic-15 F8)
        if _is_hero(ctx):
            diff = _current_region_difficulty(ctx)
            if diff > 0:
                comfort = actor.progression.level + 3
                excess = max(diff * 3 - comfort, 0)
                flee_threshold += excess * 0.03  # +3% per excess danger point
        flee_threshold = max(0.05, min(0.8, flee_threshold))

        # Milestone 6: Bravery influence
        bravery = actor.mind.emotional_state.get("bravery", 0.5)
        flee_threshold += (0.5 - bravery) * 0.4
        flee_threshold = max(0.05, min(0.9, flee_threshold))

        base = 0.0
        # Smooth escalation from 60% HP down to critical
        if hp_ratio <= flee_threshold:
            # Urgent flee: score 0.8 to 2.8+ as HP drops below threshold
            base = 0.8 + (flee_threshold - hp_ratio) * 2.0
        elif hp_ratio < 0.6:
            # Cautious flee: score 0.1 to 0.4 as HP drops from 60% to threshold
            # This allows modifiers (Nemesis, Trauma, Neuroticism) to tip the scale
            base = 0.4 * (0.6 - hp_ratio) / (0.6 - flee_threshold) if (0.6 - flee_threshold) > 0 else 0.1
        
        # Trait specific penalty
        from src.core.entities.traits import TraitType
        if TraitType.BRAVE in actor.identity.traits:
            base -= 0.6
        
        # Neuroticism impact on flee
        neuroticism = getattr(actor.identity, "neuroticism", 0.5)
        base += (neuroticism - 0.5) * 0.8

        # Proximity bonus: increase urge to flee if an enemy is actually nearby
        if ctx.nearest_enemy() is not None and hp_ratio < 0.6:
            base += 0.2

        # Mobs are less willing to flee on home territory
        if not _is_hero(ctx):
            from src.ai.states import is_on_home_territory
            if is_on_home_territory(ctx):
                base *= 0.5  # halve flee desire on home turf

        base += _trait_utility(ctx).flee
        return base



# ---------------------------------------------------------------------------
# Explore — discover unknown territory
# ---------------------------------------------------------------------------

class ExploreGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "explore"

    @property
    def target_state(self) -> AIState:
        return AIState.WANDER

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.combat.hp_ratio
        stamina_ratio = actor.progression.stamina_ratio

        base = 0.2
        if hp_ratio > 0.7 and stamina_ratio > 0.4:
            base += 0.2
        if ctx.nearest_enemy() is None:
            base += 0.15

        # Heroes prefer exploring regions near their power level (epic-15 F8)
        if _is_hero(ctx):
            penalty = _region_danger_penalty(ctx)
            base -= penalty
            # Slight bonus for being in a region that matches hero level
            diff = _current_region_difficulty(ctx)
            if diff > 0:
                level = actor.progression.level
                if diff * 3 <= level + 3:  # comfortable
                    base += 0.1

        base += _trait_utility(ctx).explore
        return base


# ---------------------------------------------------------------------------
# Loot — pick up ground items / harvest resources
# ---------------------------------------------------------------------------

class LootGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "loot"

    @property
    def target_state(self) -> AIState:
        return AIState.LOOTING

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        base = 0.0

        if _is_hero(ctx):
            # Don't loot if inventory is full (slots or weight)
            if actor.inventory and actor.inventory.is_effectively_full:
                return 0.0
            from src.ai.perception import Perception
            loot_pos = Perception.ground_loot_nearby(actor, ctx.snapshot, radius=5)
            if loot_pos is not None:
                base = 0.5
                if actor.spatial.pos.manhattan(loot_pos) <= 2:
                    base = 0.7
            # Reduce desire when bag is nearly full (slots or weight)
            if actor.inventory:
                free = actor.inventory.max_slots - actor.inventory.used_slots
                nearly_full = free <= 2 or actor.inventory.weight_ratio >= 0.9
                if nearly_full:
                    base *= 0.3  # strongly discourage looting with nearly-full bag
                elif free > 2:
                    base += 0.1

        base += _trait_utility(ctx).loot
        return base


# ---------------------------------------------------------------------------
# Trade — visit shops to buy/sell
# ---------------------------------------------------------------------------

class TradeGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "trade"

    @property
    def target_state(self) -> AIState:
        return AIState.VISIT_SHOP

    def score(self, ctx: AIContext) -> float:
        base = 0.0
        if _is_hero(ctx):
            from src.ai.states import hero_has_sellable_items, hero_wants_to_buy
            if hero_has_sellable_items(ctx.actor):
                base += 0.4
            if hero_wants_to_buy(ctx.actor):
                base += 0.3
            # Urgently sell when bag is nearly full (slots or weight)
            inv = ctx.actor.inventory
            if inv and (inv.used_slots >= inv.max_slots - 2 or inv.weight_ratio >= 0.9):
                base += 0.4

        # Suppress during combat
        if _is_hero(ctx) and ctx.nearest_enemy() is not None:
            return 0.05
        base += _trait_utility(ctx).trade
        return base


# ---------------------------------------------------------------------------
# Rest — heal and recover
# ---------------------------------------------------------------------------

class RestGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "rest"

    @property
    def target_state(self) -> AIState:
        return AIState.RESTING_IN_TOWN

    def score(self, ctx: AIContext) -> float:
        actor = ctx.actor
        hp_ratio = actor.combat.hp_ratio
        stamina_ratio = actor.progression.stamina_ratio

        base = 0.0
        if hp_ratio < 0.8:
            base = 0.3 * (1.0 - hp_ratio)
        if stamina_ratio < 0.3:
            base += 0.3
        if _is_hero(ctx) and actor.home_pos:
            base += 0.05

        # Suppress during combat
        if ctx.nearest_enemy() is not None:
            return -1.0  # HARD BLOCK: Never rest when enemies are visible
        base += _trait_utility(ctx).rest
        return base


# ---------------------------------------------------------------------------
# Craft — visit blacksmith, gather materials
# ---------------------------------------------------------------------------

class CraftGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "craft"

    @property
    def target_state(self) -> AIState:
        return AIState.VISIT_BLACKSMITH

    def score(self, ctx: AIContext) -> float:
        base = 0.0
        if _is_hero(ctx):
            from src.ai.states import hero_should_visit_blacksmith
            if hero_should_visit_blacksmith(ctx.actor):
                base = 0.4

        # Suppress during combat
        if _is_hero(ctx) and ctx.nearest_enemy() is not None:
            return 0.05
        base += _trait_utility(ctx).craft
        return base


# ---------------------------------------------------------------------------
# Social — visit guild, interact with NPCs
# ---------------------------------------------------------------------------

class SocialGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "social"

    @property
    def target_state(self) -> AIState:
        return AIState.VISIT_GUILD

    def score(self, ctx: AIContext) -> float:
        base = 0.0
        if _is_hero(ctx):
            from src.ai.states import hero_should_visit_guild, hero_should_visit_class_hall
            if hero_should_visit_guild(ctx.actor):
                base = 0.35
            if hero_should_visit_class_hall(ctx.actor):
                base += 0.3

        # Suppress during combat
        if _is_hero(ctx) and ctx.nearest_enemy() is not None:
            return 0.05
        base += _trait_utility(ctx).social
        return base


# ---------------------------------------------------------------------------
# Guard — patrol and protect territory (enemies only)
# ---------------------------------------------------------------------------

class GuardGoal(GoalScorer):

    @property
    def name(self) -> str:
        return "guard"

    @property
    def target_state(self) -> AIState:
        return AIState.GUARD_CAMP

    def score(self, ctx: AIContext) -> float:
        if _is_hero(ctx):
            return 0.0

        actor = ctx.actor
        base = 0.0

        from src.ai.states import is_on_home_territory
        if is_on_home_territory(ctx):
            base = 0.4
            # Spike urgency if an enemy is visible on our turf
            if ctx.nearest_enemy() is not None:
                base = 0.8
        elif actor.home_pos:
            dist_home = actor.spatial.pos.manhattan(actor.home_pos)
        return base


# ---------------------------------------------------------------------------
# Corpse Run — recover items after death
# ---------------------------------------------------------------------------

class CorpseScorer(GoalScorer):

    @property
    def name(self) -> str:
        return "corpse_run"

    @property
    def target_state(self) -> AIState:
        return AIState.RECOVER_CORPSE

    def score(self, ctx: AIContext) -> float:
        if not _is_hero(ctx):
            return 0.0
            
        # Check if we have a corpse node in the world
        nodes = getattr(ctx.snapshot, "corpse_nodes", {})
        for node_id, node in nodes.items():
            if node.entity_id == ctx.actor.id:
                # Urgent priority to get items back
                return 5.0
                
        return 0.0

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/pathfinding.py
"""A* Pathfinding with terrain cost awareness (epic-09).

Provides a `Pathfinder` class that computes optimal paths through the grid,
respecting walkability, terrain movement costs, and an occupied-tile set.

Usage:
    pf = Pathfinder(grid)
    path = pf.find_path(start, goal)          # list[Vector2] or None
    next_step = pf.next_step(start, goal)     # Vector2 or None
"""

from __future__ import annotations

import heapq
from typing import TYPE_CHECKING

from src.core.models.enums import Material
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.core.world.grid import Grid

# ---------------------------------------------------------------------------
# Terrain movement cost registry (F2)
# ---------------------------------------------------------------------------
# Cost 1.0 = baseline.  Lower = faster (roads).  Higher = slower.
# Impassable tiles (WALL, WATER, LAVA) are handled by Grid.is_walkable().

TERRAIN_MOVE_COST: dict[Material, float] = {
    Material.FLOOR:             1.0,
    Material.TOWN:              1.0,
    Material.CAMP:              1.0,
    Material.SANCTUARY:         1.0,
    Material.RUINS:             1.0,
    Material.DUNGEON_ENTRANCE:  1.0,
    Material.ROAD:              0.7,
    Material.BRIDGE:            0.7,
    Material.FOREST:            1.3,
    Material.DESERT:            1.2,
    Material.SWAMP:             1.5,
    Material.MOUNTAIN:          1.4,
    Material.GRASSLAND:         0.9,
    Material.SNOW:              1.4,
    Material.JUNGLE:            1.6,
    Material.SHALLOW_WATER:     1.5,
    Material.FARMLAND:          0.9,
    Material.CAVE:              1.1,
    Material.VOLCANIC:          1.3,
    Material.GRAVEYARD:         1.1,
}

# Cardinal directions (no diagonals — Manhattan grid)
_DIRS = (Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1))


def tile_cost(grid: Grid, pos: Vector2) -> float:
    """Return the movement cost for stepping onto *pos*."""
    mat = grid.get(pos)
    return TERRAIN_MOVE_COST.get(mat, 1.0)


# ---------------------------------------------------------------------------
# A* Pathfinder
# ---------------------------------------------------------------------------

class Pathfinder:
    """A* pathfinder operating on the simulation Grid.

    Thread-safe: reads only from the immutable snapshot grid.
    Performance-bounded: explores at most `max_nodes` before giving up.
    """

    __slots__ = ("_grid", "_max_nodes")

    def __init__(self, grid: Grid, max_nodes: int = 200) -> None:
        self._grid = grid
        self._max_nodes = max_nodes

    def find_path(
        self,
        start: Vector2,
        goal: Vector2,
        occupied: frozenset[tuple[int, int]] | set[tuple[int, int]] | None = None,
        exclude_goal_from_occupied: bool = True,
    ) -> list[Vector2] | None:
        """Compute an A* path from *start* to *goal*.

        Returns a list of Vector2 positions (excluding *start*, including *goal*),
        or None if no path exists within the node budget.

        *occupied* is a set of (x, y) tuples that are blocked by other entities.
        The *goal* tile is always considered reachable even if occupied (the
        entity intends to move *toward* it, not necessarily onto it).
        """
        if start == goal:
            return []

        grid = self._grid
        if not grid.is_walkable(goal):
            return None

        occ = occupied or set()

        # A* open set: (f_score, counter, x, y)
        counter = 0
        open_heap: list[tuple[float, int, int, int]] = []
        heapq.heappush(open_heap, (0.0, counter, start.x, start.y))

        g_score: dict[tuple[int, int], float] = {(start.x, start.y): 0.0}
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        closed: set[tuple[int, int]] = set()
        nodes_explored = 0

        gx, gy = goal.x, goal.y

        while open_heap and nodes_explored < self._max_nodes:
            _, _, cx, cy = heapq.heappop(open_heap)
            ckey = (cx, cy)

            if cx == gx and cy == gy:
                # Reconstruct path
                return self._reconstruct(came_from, ckey)

            if ckey in closed:
                continue
            closed.add(ckey)
            nodes_explored += 1

            current_g = g_score[ckey]

            for d in _DIRS:
                nx, ny = cx + d.x, cy + d.y
                nkey = (nx, ny)

                if nkey in closed:
                    continue

                npos = Vector2(nx, ny)
                if not grid.is_walkable(npos):
                    continue

                # Occupied check (skip goal tile)
                if nkey in occ and not (exclude_goal_from_occupied and nx == gx and ny == gy):
                    continue

                step_cost = tile_cost(grid, npos)
                tentative_g = current_g + step_cost

                if tentative_g < g_score.get(nkey, float("inf")):
                    g_score[nkey] = tentative_g
                    came_from[nkey] = ckey
                    h = abs(nx - gx) + abs(ny - gy)  # Manhattan heuristic
                    f = tentative_g + h
                    counter += 1
                    heapq.heappush(open_heap, (f, counter, nx, ny))

        return None  # No path found within budget

    def next_step(
        self,
        start: Vector2,
        goal: Vector2,
        occupied: frozenset[tuple[int, int]] | set[tuple[int, int]] | None = None,
    ) -> Vector2 | None:
        """Return the first step of the A* path, or None if no path exists."""
        path = self.find_path(start, goal, occupied)
        if path and len(path) > 0:
            return path[0]
        return None

    @staticmethod
    def _reconstruct(
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
    ) -> list[Vector2]:
        """Walk back through came_from to build the path."""
        path: list[Vector2] = []
        while current in came_from:
            path.append(Vector2(current[0], current[1]))
            current = came_from[current]
        path.reverse()
        return path

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/perception.py
"""Perception system — what an entity can see and remember.

All methods are stateless and operate on immutable snapshots.
Enemy/ally detection uses the faction system instead of string comparisons,
so adding new factions or changing alliances requires zero changes here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.gameplay.faction import FactionRegistry
from src.core.entities.entity import Entity, Vector2

if TYPE_CHECKING:
    from src.core.models.snapshot import Snapshot


class Perception:
    """Stateless perception utilities operating on immutable snapshots."""

    __slots__ = ()

    # ------------------------------------------------------------------
    # Vision
    # ------------------------------------------------------------------

    @staticmethod
    def visible_entities(
        actor: Entity,
        snapshot: Snapshot,
        vision_range: int,
    ) -> list[Entity]:
        """Return entities within Manhattan distance *vision_range* of *actor*."""
        ax, ay = actor.spatial.pos.x, actor.spatial.pos.y
        aid = actor.id
        vr = vision_range
        entities = snapshot.entities
        result: list[Entity] = []
        nearby = snapshot.nearby_entity_ids(ax, ay, vr)
        for eid in nearby:
            if eid == aid:
                continue
            e = entities[eid]
            
            # Pillar 7: PER-based Hidden Discovery
            if getattr(e, "is_hidden", False):
                # Hidden entities (traps, caches, stealthed units) 
                # require PER >= 20 to see at all
                if getattr(actor.stats, "per", 0) < 20:
                    continue
            
            result.append(e)
        
        return result

    # ------------------------------------------------------------------
    # Faction-aware target selection
    # ------------------------------------------------------------------

    @staticmethod
    def nearest_enemy(
        actor: Entity,
        visible: list[Entity],
        faction_reg: FactionRegistry | None = None,
    ) -> Entity | None:
        """Return the closest visible hostile entity, tie-broken by lowest ID.

        Uses the FactionRegistry when provided; falls back to faction != actor.identity.faction.
        """
        if faction_reg is not None:
            enemies = [
                e for e in visible
                if e.combat.alive and faction_reg.is_hostile(actor.identity.faction, e.identity.faction)
            ]
        else:
            enemies = [e for e in visible if e.combat.alive and e.identity.faction != actor.identity.faction]
        
        if not enemies:
            return None
        return min(enemies, key=lambda e: (actor.spatial.pos.manhattan(e.spatial.pos), e.id))

    @staticmethod
    def highest_threat_enemy(
        actor: Entity,
        visible: list[Entity],
        faction_reg: FactionRegistry | None = None,
    ) -> Entity | None:
        """Return the visible hostile with the highest threat score on *actor*.

        Falls back to nearest enemy if no threat data exists.
        Tie-broken by distance then lowest ID.
        """
        if faction_reg is not None:
            enemies = [
                e for e in visible
                if e.combat.alive and faction_reg.is_hostile(actor.identity.faction, e.identity.faction)
            ]
        else:
            enemies = [e for e in visible if e.combat.alive and e.identity.faction != actor.identity.faction]
        if not enemies:
            return None
        # Check threat table for entries
        if actor.mind.threat_table:
            # Filter to visible enemies that have threat entries
            threatened = [e for e in enemies if e.id in actor.mind.threat_table]
            if threatened:
                return max(threatened, key=lambda e: (
                    actor.mind.threat_table[e.id], -actor.spatial.pos.manhattan(e.spatial.pos), -e.id))
        # Fallback: nearest enemy
        return min(enemies, key=lambda e: (actor.spatial.pos.manhattan(e.spatial.pos), e.id))

    @staticmethod
    def nearest_ally(
        actor: Entity,
        visible: list[Entity],
        faction_reg: FactionRegistry | None = None,
    ) -> Entity | None:
        """Return the closest visible allied entity, tie-broken by lowest ID."""
        if faction_reg is not None:
            allies = [
                e for e in visible
                if e.combat.alive and e.id != actor.id and faction_reg.is_allied(actor.identity.faction, e.identity.faction)
            ]
        else:
            allies = [
                e for e in visible
                if e.combat.alive and e.id != actor.id and e.identity.faction == actor.identity.faction
            ]
        if not allies:
            return None
        return min(allies, key=lambda e: (actor.spatial.pos.manhattan(e.spatial.pos), e.id))

    @staticmethod
    def count_nearby_allies(
        actor: Entity,
        visible: list[Entity],
        faction_reg: FactionRegistry | None = None,
    ) -> int:
        """Count visible allies (same faction, excluding self)."""
        if faction_reg is not None:
            return sum(
                1 for e in visible
                if e.combat.alive and e.id != actor.id and faction_reg.is_allied(actor.identity.faction, e.identity.faction)
            )
        return sum(
            1 for e in visible
            if e.combat.alive and e.id != actor.id and e.identity.faction == actor.identity.faction
        )

    # ------------------------------------------------------------------
    # Direction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def direction_away_from(origin: Vector2, threat: Vector2) -> Vector2:
        """Return a unit-step Vector2 moving *origin* away from *threat*."""
        dx = origin.x - threat.x
        dy = origin.y - threat.y
        if abs(dx) >= abs(dy):
            return Vector2(1 if dx >= 0 else -1, 0)
        return Vector2(0, 1 if dy >= 0 else -1)

    @staticmethod
    def direction_toward(origin: Vector2, target: Vector2) -> Vector2:
        """Return a unit-step Vector2 moving *origin* toward *target*."""
        dx = target.x - origin.x
        dy = target.y - origin.y
        if dx == 0 and dy == 0:
            return Vector2(0, 0)
        if abs(dx) >= abs(dy):
            return Vector2(1 if dx > 0 else -1, 0)
        return Vector2(0, 1 if dy > 0 else -1)

    # ------------------------------------------------------------------
    # Tile queries
    # ------------------------------------------------------------------

    @staticmethod
    def is_in_town(actor: Entity, snapshot: Snapshot) -> bool:
        """Return True if the actor is standing on a TOWN tile."""
        return snapshot.grid.is_town(actor.spatial.pos)

    @staticmethod
    def is_in_sanctuary(actor: Entity, snapshot: Snapshot) -> bool:
        """Return True if the actor is standing on a SANCTUARY tile."""
        return snapshot.grid.is_sanctuary(actor.spatial.pos)

    @staticmethod
    def is_in_camp(actor: Entity, snapshot: Snapshot) -> bool:
        """Return True if the actor is standing on a CAMP tile."""
        return snapshot.grid.is_camp(actor.spatial.pos)

    @staticmethod
    def is_on_home_territory(
        actor: Entity,
        snapshot: Snapshot,
        faction_reg: FactionRegistry,
    ) -> bool:
        """Return True if the actor is standing on its own faction's territory."""
        mat = snapshot.grid.get(actor.spatial.pos)
        return faction_reg.is_home_territory(actor.identity.faction, mat)

    @staticmethod
    def is_on_enemy_territory(
        actor: Entity,
        snapshot: Snapshot,
        faction_reg: FactionRegistry,
    ) -> bool:
        """Return True if the actor is standing on a hostile faction's territory."""
        mat = snapshot.grid.get(actor.spatial.pos)
        return faction_reg.is_enemy_territory(actor.identity.faction, mat)

    # ------------------------------------------------------------------
    # Loot & camps
    # ------------------------------------------------------------------

    @staticmethod
    def ground_loot_nearby(actor: Entity, snapshot: Snapshot, radius: int = 3) -> Vector2 | None:
        """Return the position of the nearest ground loot pile within radius, or None.
        
        Optimized: uses spatial index for O(1) cell lookup.
        """
        best_pos: Vector2 | None = None
        best_dist = radius + 1
        ax, ay = actor.spatial.pos.x, actor.spatial.pos.y
        
        # Use spatial index to only check nearby cells
        for gx, gy in snapshot.nearby_ground_positions(ax, ay, radius):
            items = snapshot.ground_items.get((gx, gy))
            if not items:
                continue
            dist = abs(ax - gx) + abs(ay - gy)
            if dist <= radius and dist < best_dist:
                best_dist = dist
                best_pos = Vector2(gx, gy)
        return best_pos

    @staticmethod
    def find_frontier_target(
        actor: Entity,
        snapshot: Snapshot,
        rng_val: int,
    ) -> Vector2 | None:
        """Find an unexplored tile on the frontier (adjacent to explored tiles).

        Returns a walkable unexplored tile near the actor, biased by *rng_val*
        to avoid all entities converging on the same spot.

        Optimized: only scans a bounded neighborhood around the actor instead
        of iterating all explored tiles (which grows with the map).
        """
        explored = actor.terrain_memory
        grid = snapshot.grid
        ax, ay = actor.spatial.pos.x, actor.spatial.pos.y
        # Search in expanding rings up to a max scan radius
        # Heroes scan further, others scan less to save CPU
        max_r = 40 if actor.kind == "hero" else 15
        scan_radius = min(actor.stats.vision_range * 4, max_r)
        frontier: list[tuple[int, Vector2]] = []  # (distance, pos)

        grid_w, grid_h = grid.width, grid.height
        for dy in range(-scan_radius, scan_radius + 1):
            ty = ay + dy
            if ty < 0 or ty >= grid_h:
                continue
            remaining = scan_radius - abs(dy)
            for dx in range(-remaining, remaining + 1):
                tx = ax + dx
                if tx < 0 or tx >= grid_w:
                    continue
                if (tx, ty) in explored:
                    continue
                # Check if adjacent to an explored tile (frontier condition)
                is_frontier = (
                    (tx - 1, ty) in explored or (tx + 1, ty) in explored
                    or (tx, ty - 1) in explored or (tx, ty + 1) in explored
                )
                if not is_frontier:
                    continue
                candidate = Vector2(tx, ty)
                if grid.is_walkable(candidate):
                    dist = abs(dx) + abs(dy)
                    frontier.append((dist, candidate))
                    if len(frontier) >= 32:
                        break
            if len(frontier) >= 32:
                break

        if not frontier:
            return None
            
        # Nemesis System: Penalize regions with bad sentiment
        if hasattr(actor, "mind") and actor.mind.memory_locations:
            from src.core.world.regions import find_region_at
            sentiment_frontier = []
            for dist, pos in frontier:
                region = find_region_at(pos, snapshot.regions)
                region_id = region.region_id if region else None
                sentiment = actor.mind.memory_locations.get(region_id, 0.0) if region_id else 0.0
                # If sentiment is negative, increase the effective distance (make it less attractive)
                # sentiment -1.0 adds 100 to distance
                effective_dist = dist + (abs(min(0, sentiment)) * 100)
                sentiment_frontier.append((effective_dist, pos))
            frontier = sentiment_frontier

        # Sort by distance, pick from closest candidates with randomness
        frontier.sort(key=lambda t: t[0])
        pool = [p for _, p in frontier[:min(8, len(frontier))]]
        return pool[rng_val % len(pool)]

    @staticmethod
    def remembered_enemy_strength(actor: Entity, target_id: int) -> dict | None:
        """Return the remembered entity_memory entry for a specific entity, or None."""
        for em in actor.entity_memory:
            if em["id"] == target_id:
                return em
        return None

    @staticmethod
    def strongest_remembered_enemy(actor: Entity) -> dict | None:
        """Return the remembered enemy with the highest ATK, or None."""
        enemies = [em for em in actor.entity_memory if em.get("atk", 0) > 0]
        if not enemies:
            return None
        return max(enemies, key=lambda em: em.get("atk", 0))

    @staticmethod
    def nearest_camp(actor: Entity, snapshot: Snapshot) -> Vector2 | None:
        """Return the nearest camp center from the snapshot."""
        if not snapshot.camps:
            return None
        best: tuple[int, int] | None = None
        best_dist = 9999
        for cx, cy in snapshot.camps:
            d = abs(actor.spatial.pos.x - cx) + abs(actor.spatial.pos.y - cy)
            if d < best_dist:
                best_dist = d
                best = (cx, cy)
        return Vector2(best[0], best[1]) if best else None

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/states/__init__.py
from src.core.models.enums import AIState
from src.ai.states.base import AIContext, StateHandler
from src.ai.states.navigation import (
    IdleHandler, WanderHandler, ReturnToTownHandler, 
    ReturnToCampHandler, GuardCampHandler, ExhaustedHandler
)
from src.ai.states.combat import (
    HuntHandler, CombatHandler, FleeHandler, AlertHandler
)
from src.ai.states.interaction import (
    LootingHandler, HarvestingHandler, CorpseRunHandler
)
from src.ai.states.town import (
    RestingInTownHandler, VisitShopHandler, VisitBlacksmithHandler,
    VisitGuildHandler, VisitClassHallHandler, VisitInnHandler,
    VisitHomeHandler
)

STATE_HANDLERS: dict[AIState, StateHandler] = {
    AIState.IDLE: IdleHandler(),
    AIState.WANDER: WanderHandler(),
    AIState.HUNT: HuntHandler(),
    AIState.COMBAT: CombatHandler(),
    AIState.FLEE: FleeHandler(),
    AIState.RETURN_TO_TOWN: ReturnToTownHandler(),
    AIState.RESTING_IN_TOWN: RestingInTownHandler(),
    AIState.RETURN_TO_CAMP: ReturnToCampHandler(),
    AIState.GUARD_CAMP: GuardCampHandler(),
    AIState.LOOTING: LootingHandler(),
    AIState.ALERT: AlertHandler(),
    AIState.VISIT_SHOP: VisitShopHandler(),
    AIState.VISIT_BLACKSMITH: VisitBlacksmithHandler(),
    AIState.VISIT_GUILD: VisitGuildHandler(),
    AIState.HARVESTING: HarvestingHandler(),
    AIState.VISIT_CLASS_HALL: VisitClassHallHandler(),
    AIState.VISIT_INN: VisitInnHandler(),
    AIState.VISIT_HOME: VisitHomeHandler(),
    AIState.EXHAUSTED: ExhaustedHandler(),
    AIState.RECOVER_CORPSE: CorpseRunHandler(),
}

__all__ = [
    # Core types
    "AIContext",
    "StateHandler",
    "STATE_HANDLERS",
    
    # Handlers
    "IdleHandler",
    "WanderHandler",
    "HuntHandler",
    "CombatHandler",
    "FleeHandler",
    "ReturnToTownHandler",
    "RestingInTownHandler",
    "ReturnToCampHandler",
    "GuardCampHandler",
    "LootingHandler",
    "AlertHandler",
    "VisitShopHandler",
    "VisitBlacksmithHandler",
    "VisitGuildHandler",
    "HarvestingHandler",
    "VisitClassHallHandler",
    "VisitInnHandler",
    "VisitHomeHandler",
    "ExhaustedHandler",
    "CorpseRunHandler",
    
    # Shared Helpers (from base.py)
    "is_tile_passable",
    "propose_move_toward",
    "propose_move_away",
    "propose_retreat_home",
    "clear_dead_from_memory",
    "beyond_leash",
    "should_flee",
    "is_in_hostile_town",
    "is_on_home_territory",
    "is_on_enemy_territory",
    
    # Navigation/Combat Specific Helpers
    "get_weapon_range",
    "best_ready_skill",
    "can_use_potion",
    
    # Town/Interaction Helpers
    "find_building",
    "can_use_buildings",
    "hero_wants_to_buy",
    "hero_has_sellable_items",
    "hero_should_visit_blacksmith",
    "hero_should_visit_guild",
    "hero_should_visit_class_hall",
    "hero_should_visit_inn",
    "hero_should_visit_home",
    "find_nearby_resource",
]

# Re-export key helpers for backward compatibility
from src.ai.states.base import (
    is_tile_passable,
    propose_move_toward,
    propose_move_away,
    propose_retreat_home,
    clear_dead_from_memory,
    beyond_leash,
    should_flee,
    is_in_hostile_town,
    is_on_home_territory,
    is_on_enemy_territory,
)

from src.ai.states.combat import (
    get_weapon_range,
    best_ready_skill,
    can_use_potion,
)

from src.ai.states.town import (
    find_building,
    can_use_buildings,
    hero_wants_to_buy,
    hero_has_sellable_items,
    hero_should_visit_blacksmith,
    hero_should_visit_guild,
    hero_should_visit_class_hall,
    hero_should_visit_inn,
    hero_should_visit_home,
)

from src.ai.states.interaction import (
    find_nearby_resource,
)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/states/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.ai.perception import Perception
from src.core.models.enums import AIState, ActionType, Domain
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.entities.entity import Entity, Vector2

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.snapshot import Snapshot
    from src.platform.rng import DeterministicRNG


@dataclass(slots=True)
class AIContext:
    """All data a state handler might need.  Extend this to add weather,
    quests, etc. without changing handler signatures."""

    actor: Entity
    snapshot: Snapshot
    config: SimulationConfig
    rng: DeterministicRNG
    faction_reg: FactionRegistry
    
    # Pillar 3: Tactical Intent (Decoupled hints from Brain -> Handler)
    tactical_hints: dict[str, Any] = field(default_factory=dict)

    # -- cached helpers (lazily populated) --

    _visible: list[Entity] | None = None

    @property
    def visible(self) -> list[Entity]:
        if self._visible is None:
            self._visible = Perception.visible_entities(
                self.actor, self.snapshot, self.actor.combat.vision_range)
        return self._visible

    def nearest_enemy(self) -> Entity | None:
        """Return best combat target."""
        if hasattr(self.actor, "mind") and self.actor.mind.grudges:
            visible_targets = [v for v in self.visible if self.faction_reg.is_hostile(self.actor.identity.faction, v.identity.faction)]
            nemesis = None
            max_grudge = 0.0
            for v in visible_targets:
                g = self.actor.mind.grudges.get(v.id, 0.0)
                if g > max_grudge and g > 50.0:
                    max_grudge = g
                    nemesis = v
            if nemesis:
                return nemesis

        if self.actor.identity.faction != Faction.HERO_GUILD and self.actor.mind.threat_table:
            return Perception.highest_threat_enemy(self.actor, self.visible, self.faction_reg)
        return Perception.nearest_enemy(self.actor, self.visible, self.faction_reg)

    def nearest_ally(self) -> Entity | None:
        return Perception.nearest_ally(self.actor, self.visible, self.faction_reg)


class StateHandler(ABC):
    """Abstract base for AI state handlers."""

    @abstractmethod
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        ...


def is_tile_passable(actor: Entity, pos: Vector2, snapshot: Snapshot) -> bool:
    return snapshot.grid.is_walkable(pos)


def _greedy_move_toward(actor: Entity, target_pos: Vector2, snapshot: Snapshot, reason: str) -> ActionProposal:
    direction = Perception.direction_toward(actor.spatial.pos, target_pos)
    dest = actor.spatial.pos + direction
    if is_tile_passable(actor, dest, snapshot):
        return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=dest, reason=reason)
    dx = target_pos.x - actor.spatial.pos.x
    dy = target_pos.y - actor.spatial.pos.y
    alternates = [Vector2(0, 1), Vector2(0, -1)] if abs(dx) >= abs(dy) else [Vector2(1, 0), Vector2(-1, 0)]
    for alt in alternates:
        alt_dest = actor.spatial.pos + alt
        if is_tile_passable(actor, alt_dest, snapshot):
            return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=alt_dest, reason=f"{reason} (detour)")
    return ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (path blocked)")


def propose_move_toward(actor: Entity, target_pos: Vector2, snapshot: Snapshot, reason: str) -> ActionProposal:
    dist = actor.spatial.pos.manhattan(target_pos)
    if dist <= 2:
        return _greedy_move_toward(actor, target_pos, snapshot, reason)

    if dist > 8:
        is_shared_target = (snapshot.grid.is_town(target_pos) or snapshot.grid.is_camp(target_pos))
        
        # Check for World Boss (Calamity) at target position
        if not is_shared_target:
            from src.core.models.enums import EntityRole
            # Use spatial index to quickly check entities at target_pos
            nearby_ids = snapshot.nearby_entity_ids(target_pos.x, target_pos.y, 1)
            for eid in nearby_ids:
                e = snapshot.entities.get(eid)
                if e and e.spatial.pos == target_pos and e.identity.role == EntityRole.WORLD_BOSS:
                    is_shared_target = True
                    break
        
        if is_shared_target:
            from src.ai.flow_fields import FlowFieldManager
            ff = FlowFieldManager.get_instance().get_flow_field(target_pos, snapshot.grid, snapshot.tick)
            fvec = ff.get_vector(actor.spatial.pos)
            if fvec:
                # Optimized step selection: pick the cardinal/diagonal step that aligns best with the flow
                from src.core.models.vectors import DIRECTION_OFFSETS
                best_step = None
                max_dot = -1.0
                for step in DIRECTION_OFFSETS.values():
                    dot = step.x * fvec.x + step.y * fvec.y
                    if dot > max_dot:
                        dest = actor.spatial.pos + step
                        if is_tile_passable(actor, dest, snapshot):
                            max_dot = dot
                            best_step = step
                
                if best_step:
                    return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, 
                                          target=actor.spatial.pos + best_step, 
                                          reason=f"{reason} (Flow Field)")

    cached = getattr(actor, 'cached_path', None)
    cached_target = getattr(actor, 'cached_path_target', None)
    if (cached and cached_target
            and cached_target == target_pos
            and len(cached) > 0
            and cached[0] == actor.spatial.pos):
        cached.pop(0)
        if cached and is_tile_passable(actor, cached[0], snapshot):
            return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE,
                                  target=cached[0], reason=f"{reason} (A* cached)")

    from src.ai.pathfinding import Pathfinder
    pf = Pathfinder(snapshot.grid)
    path = pf.find_path(actor.spatial.pos, target_pos)

    if path:
        actor.cached_path = path
        actor.cached_path_target = target_pos
        step = path[0]
        if is_tile_passable(actor, step, snapshot):
            return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE,
                                  target=step, reason=f"{reason} (A*)")

    return _greedy_move_toward(actor, target_pos, snapshot, reason)


def propose_move_away(actor: Entity, threat_pos: Vector2, snapshot: Snapshot, reason: str) -> ActionProposal:
    direction = Perception.direction_away_from(actor.spatial.pos, threat_pos)
    dest = actor.spatial.pos + direction
    if is_tile_passable(actor, dest, snapshot):
        return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=dest, reason=reason)
    perps = [Vector2(-direction.y, direction.x), Vector2(direction.y, -direction.x)]
    for p in perps:
        alt = actor.spatial.pos + p
        if is_tile_passable(actor, alt, snapshot):
            return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=alt, reason=f"{reason} (side step)")
    return ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (flee blocked)")


def propose_retreat_home(ctx: AIContext, reason: str) -> tuple[AIState, ActionProposal]:
    actor = ctx.actor
    if actor.identity.faction == Faction.HERO_GUILD and actor.home_pos:
        return AIState.RETURN_TO_TOWN, propose_move_toward(
            actor, actor.home_pos, ctx.snapshot, reason)
    camp = Perception.nearest_camp(actor, ctx.snapshot)
    if camp:
        return AIState.RETURN_TO_CAMP, propose_move_toward(
            actor, camp, ctx.snapshot, reason)
    enemy = ctx.nearest_enemy()
    if enemy:
        return AIState.FLEE, propose_move_away(actor, enemy.spatial.pos, ctx.snapshot, reason)
    return AIState.WANDER, ActionProposal(
        actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (nowhere to go)")


def clear_dead_from_memory(actor: Entity, snapshot: Snapshot) -> None:
    dead_ids = [eid for eid in actor.mind.memory if eid not in snapshot.entities or not snapshot.entities[eid].combat.alive]
    for eid in dead_ids:
        del actor.mind.memory[eid]


def beyond_leash(actor: Entity, multiplier: float = 1.0) -> bool:
    """Return True if the entity is beyond its leash range from home."""
    if not actor.home_pos or actor.leash_radius <= 0:
        return False
    dist = actor.spatial.pos.manhattan(actor.home_pos)
    return dist > actor.leash_radius * multiplier


def is_in_hostile_town(ctx: AIContext) -> bool:
    """Return True if the entity is in a town hostile to its faction."""
    if not ctx.snapshot.grid.is_town(ctx.actor.spatial.pos):
        return False
    # Simplified: for now, all towns are assumed hostile to 'mob' factions
    # or we could check a town faction registry if it existed.
    # In WorldLoop, monsters are generally burned by town auras.
    return ctx.actor.identity.faction not in (Faction.HERO_GUILD, Faction.TOWN_GUARD)


def should_flee(actor: Entity, config: SimulationConfig) -> bool:
    """Return True if the entity's HP is below its flee threshold.
    
    Adjusted by mood: Despair (0.0) causes earlier fleeing, 
    Fury (1.0) causes staying longer.
    """
    base_threshold = config.flee_hp_threshold
    
    # Mood modifier: (0.5 - mood) * weight. 
    # If mood=0.0 (Despair), mod = +0.1. threshold = 0.2 + 0.1 = 0.3 (flee earlier)
    # If mood=1.0 (Fury), mod = -0.1. threshold = 0.2 - 0.1 = 0.1 (stay longer)
    mood = getattr(actor.mind, "mood", 0.5) if hasattr(actor, "mind") else 0.5
    threshold_mod = (0.5 - mood) * 0.2
    
    threshold = base_threshold + threshold_mod
    
    # Heroes might have different base thresholds if not provided by config
    if actor.identity.faction == Faction.HERO_GUILD and base_threshold <= 0:
        threshold = 0.2 + threshold_mod
        
    return actor.combat.hp_ratio < threshold


def is_on_home_territory(ctx: AIContext) -> bool:
    """Return True if the entity is within its camp or town area."""
    if ctx.actor.identity.faction == Faction.HERO_GUILD:
        return ctx.snapshot.grid.is_town(ctx.actor.spatial.pos)
    camp = Perception.nearest_camp(ctx.actor, ctx.snapshot)
    if camp:
        return ctx.actor.spatial.pos.manhattan(camp) <= ctx.config.camp_radius + 2
    return False


def is_on_enemy_territory(ctx: AIContext) -> bool:
    """Return True if the entity is in a hostile territory."""
    if ctx.actor.identity.faction == Faction.HERO_GUILD:
        camp = Perception.nearest_camp(ctx.actor, ctx.snapshot)
        if camp:
            return ctx.actor.spatial.pos.manhattan(camp) <= ctx.config.camp_radius + 5
    else:
        return ctx.snapshot.grid.is_town(ctx.actor.spatial.pos)
    return False

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/states/combat.py
from __future__ import annotations

from src.actions.base import ActionType, ActionProposal
from src.ai.perception import Perception
from src.core.models.enums import AIState
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.entities.entity import Entity
from src.ai.states.base import (
    AIContext, StateHandler, clear_dead_from_memory, 
    propose_move_toward, propose_move_away, propose_retreat_home,
    is_in_hostile_town, should_flee
)


def get_weapon_range(actor: Entity) -> int:
    """Return the weapon range of the entity's equipped weapon (default 1 = melee)."""
    if actor.inventory and actor.inventory.weapon:
        weapon_tmpl = ITEM_REGISTRY.get(actor.inventory.weapon)
        if weapon_tmpl:
            return weapon_tmpl.weapon_range
    return 1


def best_ready_skill(actor: Entity, dist_to_enemy: int = 1, nearby_enemies: int = 1) -> str | None:
    """Return the skill_id of the best ready active combat skill, or None."""
    from src.core.gameplay.classes import SKILL_DEFS, SkillTarget, SkillType
    import logging
    logger = logging.getLogger(__name__)
    
    best_id = None
    best_score = 0.0
    # print(f"DEBUG_SKILL: Entity {actor.id} checking {len(actor.progression.skills)} skills. Dist={dist_to_enemy}, Nearby={nearby_enemies}")
    for si in actor.progression.skills:
        sdef = SKILL_DEFS.get(si.skill_id)
        if sdef is None:
            # print(f"  Skill {si.skill_id} NOT FOUND in SKILL_DEFS")
            continue
        if not sdef: continue
        
        if not si.is_ready(): continue
        if sdef.skill_type != SkillType.ACTIVE:
            continue
        
        # Range check
        skill_range = sdef.range or 1
        if skill_range < dist_to_enemy: continue
        
        # Resource check
        cost = si.effective_stamina_cost(sdef.stamina_cost)
        if actor.progression.stamina < cost:
            continue
        
        # Scoring
        power = si.effective_power(sdef.power)
        aoe_radius = getattr(sdef, 'radius', 0) or 0
        score = power * (nearby_enemies if aoe_radius > 0 and nearby_enemies > 1 else 1)
        # print(f"  Skill {si.skill_id} SCORE={score} (power={power}, aoe={aoe_radius})")
            
        if score > best_score:
            best_score = score
            best_id = si.skill_id
            
    if best_id:
        print(f"DEBUG_SKILL_PICK: Entity {actor.id} picked {best_id} (score={best_score})")
    return best_id


def can_use_potion(actor: Entity) -> str | None:
    """Return the best potion item_id the actor can use, or None."""
    if actor.inventory is None:
        return None
    for pid in ("large_hp_potion", "medium_hp_potion", "small_hp_potion"):
        if actor.inventory.has_consumable(pid):
            t = ITEM_REGISTRY.get(pid)
            if t and t.heal_amount > 0:
                return pid
    return None


class HuntHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)

        # Leash enforcement
        from src.ai.states.base import beyond_leash
        if beyond_leash(actor, config.mob_leash_chase_multiplier):
            actor.chase_ticks = 0
            return propose_retreat_home(ctx, "Chase leash exceeded → returning home")

        if actor.leash_radius > 0 and actor.chase_ticks >= config.mob_chase_give_up_ticks:
            actor.chase_ticks = 0
            return propose_retreat_home(ctx, "Chase timed out → returning home")

        if is_in_hostile_town(ctx) and actor.stats.combat.hp_ratio < 0.6:
            return propose_retreat_home(ctx, "Town aura burning → aborting hunt")

        # Note: High-level brain (GoalEvaluator) already handles state transitions
        # We only keep critical overrides like Leash here.

        enemy = ctx.nearest_enemy()

        if enemy is None:
            actor.chase_ticks = 0
            if actor.mind.memory:
                last_seen_id = min(actor.mind.memory.keys())
                target_pos = actor.mind.memory[last_seen_id]
                if actor.spatial.pos.manhattan(target_pos) <= 1:
                    del actor.mind.memory[last_seen_id]
                    return AIState.WANDER, ActionProposal(
                        actor_id=actor.id, verb=ActionType.REST,
                        reason="Reached last known position, target gone → wander")
                return AIState.HUNT, propose_move_toward(
                    actor, target_pos, snapshot, "Hunting from memory")
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Lost target → back to wander")

        weapon_rng = get_weapon_range(actor)
        dist = actor.spatial.pos.manhattan(enemy.spatial.pos)

        # 1. Action Preference: Skill > Attack
        nearby_count = sum(
            1 for v in ctx.visible if ctx.faction_reg.is_hostile(actor.identity.faction, v.identity.faction)
            and v.combat.alive and actor.spatial.pos.manhattan(v.spatial.pos) <= 4
        )
        skill_id = best_ready_skill(actor, dist, nearby_count)
        if skill_id:
            actor.chase_ticks = 0
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.USE_SKILL, target=(skill_id, enemy.id),
                reason=f"Using skill {skill_id} on enemy {enemy.id} (dist={dist})")

        # 2. Basic Attack
        if dist <= weapon_rng:
            actor.chase_ticks = 0
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                reason=f"In range of enemy {enemy.id} (dist={dist}, range={weapon_rng}) → attacking")

        # 3. Handle deadlocks (yielding)
        if (dist == 2
                and enemy.mind.ai_state in (AIState.HUNT, AIState.COMBAT)
                and actor.id > enemy.id):
            return AIState.HUNT, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Yielding to let enemy {enemy.id} close gap (anti-deadlock)")

        # 4. Tactical Intent: Skirmish (Kiting)
        if ctx.tactical_hints.get("skirmish") and dist < ctx.tactical_hints.get("min_dist", 3):
            return AIState.HUNT, propose_move_away(actor, enemy.spatial.pos, snapshot, "Skirmishing (kiting) to maintain distance")

        # 5. Move closer
        actor.chase_ticks += 1
        return AIState.HUNT, propose_move_toward(
            actor, enemy.spatial.pos, snapshot, f"Hunting enemy {enemy.id}")


class CombatHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)

        if is_in_hostile_town(ctx) and actor.combat.hp_ratio < 0.5:
            return propose_retreat_home(ctx, "Town aura burning → disengaging from combat")

        if actor.combat.hp_ratio < 0.5:
            potion_id = can_use_potion(actor)
            if potion_id:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.USE_ITEM, target=potion_id,
                    reason=f"Low HP → using {potion_id}")

        # Note: Brain handles state transitions

        enemy = ctx.nearest_enemy()
        if enemy is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Enemy vanished → returning to wander")

        dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
        weapon_rng = get_weapon_range(actor)

        # 1. Action Preference: Skill > Attack
        nearby_count = sum(
            1 for v in ctx.visible if ctx.faction_reg.is_hostile(actor.identity.faction, v.identity.faction)
            and v.combat.alive and actor.spatial.pos.manhattan(v.spatial.pos) <= 4
        )
        skill_id = best_ready_skill(actor, dist, nearby_count)
        if skill_id:
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.USE_SKILL, target=(skill_id, enemy.id),
                reason=f"Using skill {skill_id} on enemy {enemy.id} (dist={dist})")

        # 2. Tactical Intent: Support / Healing
        support_id = ctx.tactical_hints.get("support_target_id")
        if support_id:
            target = snapshot.entities.get(support_id)
            if target and target.combat.alive:
                # Prioritize support skill or move toward ally
                support_skill = best_ready_skill(actor, actor.spatial.pos.manhattan(target.spatial.pos), 0)
                if support_skill:
                    return AIState.COMBAT, ActionProposal(
                        actor_id=actor.id, verb=ActionType.USE_SKILL, target=(support_skill, target.id),
                        reason=f"Supporting ally {target.id}")
                return AIState.COMBAT, propose_move_toward(actor, target.spatial.pos, snapshot, f"Moving to support {target.id}")

        # 3. Distance-based decision
        if dist <= weapon_rng:
            # Skirmish check: if too close, reposition
            if ctx.tactical_hints.get("skirmish") and dist < ctx.tactical_hints.get("min_dist", 1):
                return AIState.COMBAT, propose_move_away(actor, enemy.spatial.pos, snapshot, "Skirmishing (kiting) for breathing room")
                
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                reason=f"Attacking enemy {enemy.id} (dist={dist}, range={weapon_rng})")

        return AIState.HUNT, propose_move_toward(
            actor, enemy.spatial.pos, snapshot, f"Enemy {enemy.id} out of range ({dist} > {weapon_rng}) → closing distance")


class FleeHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        clear_dead_from_memory(actor, snapshot)
        enemy = ctx.nearest_enemy()

        if enemy is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Safe or recovered → stop fleeing")

        return AIState.FLEE, propose_move_away(
            actor, enemy.spatial.pos, snapshot, f"Fleeing from enemy {enemy.id}")


class AlertHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        clear_dead_from_memory(actor, snapshot)
        enemy = ctx.nearest_enemy()

        if enemy is not None:
            if actor.spatial.pos.manhattan(enemy.spatial.pos) <= 1:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                    reason=f"Alert! Attacking intruder {enemy.id}")
            return AIState.HUNT, propose_move_toward(
                actor, enemy.spatial.pos, snapshot, f"Alert! Chasing intruder {enemy.id}")

        from src.ai.states.base import is_on_home_territory
        if is_on_home_territory(ctx):
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Alert over → resuming guard duty")
        return propose_retreat_home(ctx, "Alert over → heading home")

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/states/interaction.py
from __future__ import annotations

from src.actions.base import ActionType, ActionProposal
from src.ai.perception import Perception
from src.core.models.enums import AIState
from src.core.entities.entity import Entity, Vector2
from src.ai.states.base import (
    AIContext, StateHandler, clear_dead_from_memory, 
    propose_move_toward, should_flee, propose_retreat_home
)


def find_nearby_resource(actor: Entity, snapshot, radius: int = 6):
    """Find the nearest available resource node within radius."""
    best = None
    best_dist = radius + 1
    for node in snapshot.resource_nodes:
        if not node.is_available:
            continue
        dist = actor.spatial.pos.manhattan(node.spatial.pos)
        if dist < best_dist:
            best_dist = dist
            best = node
    return best


class LootingHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)

        if actor.inventory and actor.inventory.is_effectively_full:
            actor.loot_progress = 0
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Bag full → abandoning loot")

        key = (actor.spatial.pos.x, actor.spatial.pos.y)
        if key in snapshot.ground_items and snapshot.ground_items[key]:
            if actor.loot_progress < config.loot_duration:
                actor.loot_progress += 1
                return AIState.LOOTING, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Looting... ({actor.loot_progress}/{config.loot_duration})")
            actor.loot_progress = 0
            return AIState.LOOTING, ActionProposal(
                actor_id=actor.id, verb=ActionType.LOOT, target=actor.spatial.pos,
                reason="Picking up loot")

        actor.loot_progress = 0
        loot_pos = Perception.ground_loot_nearby(actor, snapshot, radius=4)
        if loot_pos is not None:
            return AIState.LOOTING, propose_move_toward(
                actor, loot_pos, snapshot, "Moving to loot")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No more loot → wander")


class HarvestingHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot

        if should_flee(actor, ctx.config):
            actor.loot_progress = 0
            return propose_retreat_home(ctx, "Low HP → abandoning harvest")

        enemy = ctx.nearest_enemy()
        if enemy and actor.spatial.pos.manhattan(enemy.spatial.pos) <= 3:
            actor.loot_progress = 0
            return AIState.HUNT, propose_move_toward(
                actor, enemy.spatial.pos, snapshot, "Enemy nearby → abandoning harvest")

        res = None
        for node in snapshot.resource_nodes:
            if node.spatial.pos == actor.spatial.pos and node.is_available:
                res = node
                break

        if res is None:
            res = find_nearby_resource(actor, snapshot, radius=8)
            if res is None:
                actor.loot_progress = 0
                return AIState.WANDER, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason="No resources available → wander")
            return AIState.HARVESTING, propose_move_toward(
                actor, res.spatial.pos, snapshot, f"Moving to {res.name}")

        actor.loot_progress += 1
        if actor.loot_progress >= res.harvest_ticks:
            actor.loot_progress = 0
            return AIState.HARVESTING, ActionProposal(
                actor_id=actor.id, verb=ActionType.HARVEST, target=res.spatial.pos,
                reason=f"Harvested {res.name} → got {res.yields_item}")
        return AIState.HARVESTING, ActionProposal(
            actor_id=actor.id, verb=ActionType.HARVEST, target=res.spatial.pos,
            reason=f"Harvesting {res.name} ({actor.loot_progress}/{res.harvest_ticks})")


class CorpseRunHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        my_node = None
        nodes = getattr(snapshot, "corpse_nodes", {})
        for node in nodes.values():
            if node.entity_id == actor.id:
                my_node = node
                break
        
        if not my_node:
            return AIState.WANDER, ActionProposal(actor.id, ActionType.REST, "Corpse gone")
            
        if actor.spatial.pos.manhattan(my_node.spatial.pos) == 0:
            actor.stats.progression.gold += my_node.gold
            if actor.inventory:
                for iid in my_node.items:
                    actor.inventory.add_item(iid)
            
            if hasattr(snapshot, "corpse_nodes"):
                snapshot.corpse_nodes.pop(my_node.node_id, None)
            
            return AIState.IDLE, ActionProposal(actor.id, ActionType.LOOT, f"Recovered corpse #{my_node.node_id}")

        return AIState.RECOVER_CORPSE, propose_move_toward(actor, my_node.spatial.pos, snapshot, f"Running to corpse at {my_node.spatial.pos}")

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/states/navigation.py
from __future__ import annotations

from src.actions.base import ActionType, ActionProposal
from src.ai.perception import Perception
from src.core.models.enums import AIState, Domain
from src.core.gameplay.faction import Faction
from src.core.models import DIRECTION_OFFSETS, Vector2
from src.ai.states.base import (
    AIContext, StateHandler, clear_dead_from_memory, 
    propose_move_toward, beyond_leash, propose_retreat_home,
    is_in_hostile_town, is_on_enemy_territory, is_tile_passable,
    should_flee
)


class IdleHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        clear_dead_from_memory(ctx.actor, ctx.snapshot)
        return AIState.WANDER, ActionProposal(
            actor_id=ctx.actor.id, verb=ActionType.REST,
            reason="Idle → transitioning to wander")


class WanderHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config, rng = ctx.actor, ctx.snapshot, ctx.config, ctx.rng
        clear_dead_from_memory(actor, snapshot)
        enemy = ctx.nearest_enemy()

        if beyond_leash(actor):
            actor.chase_ticks = 0
            return propose_retreat_home(ctx, "Beyond leash range → returning home")

        if is_in_hostile_town(ctx):
            if actor.stats.combat.hp_ratio < 0.6 or enemy is None:
                return propose_retreat_home(ctx, "Town aura burning → retreating")

        if is_on_enemy_territory(ctx) and actor.stats.combat.hp_ratio < 0.8:
            return propose_retreat_home(ctx, "On enemy territory while weakened → retreating")

        if actor.home_pos and actor.stats.combat.hp_ratio < 0.7:
            return propose_retreat_home(ctx, "Wounded → retreating home to heal")

        if actor.identity.faction == Faction.HERO_GUILD:
            loot_pos = Perception.ground_loot_nearby(actor, snapshot, radius=4)
            if loot_pos is not None:
                if actor.spatial.pos.manhattan(loot_pos) == 0:
                    return AIState.LOOTING, ActionProposal(
                        actor_id=actor.id, verb=ActionType.LOOT, target=loot_pos,
                        reason="Standing on loot → picking up")
                return AIState.LOOTING, propose_move_toward(
                    actor, loot_pos, snapshot, "Loot nearby → moving to pick up")

            if actor.inventory and actor.inventory.used_slots < actor.inventory.max_slots - 1:
                # find_nearby_resource is in town.py (or shared)
                # For now, I'll keep it as a local import or move to a common place
                from src.ai.states.interaction import find_nearby_resource
                res = find_nearby_resource(actor, snapshot, radius=5)
                if res is not None:
                    if actor.spatial.pos == res.spatial.pos:
                        actor.loot_progress = 0
                        return AIState.HARVESTING, ActionProposal(
                            actor_id=actor.id, verb=ActionType.HARVEST,
                            target=res.spatial.pos,
                            reason=f"Harvesting {res.name}")
                    return AIState.HARVESTING, propose_move_toward(
                        actor, res.spatial.pos, snapshot,
                        f"Resource nearby → moving to {res.name}")

        if enemy is not None:
            if should_flee(actor, config):
                return propose_retreat_home(ctx, "Low HP → retreating")
            
            mem = Perception.remembered_enemy_strength(actor, enemy.id)
            if mem and mem.get("atk", 0) > actor.stats.combat.atk * 1.5 and actor.stats.combat.hp_ratio < 0.7:
                return propose_retreat_home(ctx, "Enemy too strong from memory → retreating")
            
            dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
            # get_weapon_range in combat.py
            from src.ai.states.combat import get_weapon_range
            weapon_rng = get_weapon_range(actor)
            
            if dist <= weapon_rng:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                    reason=f"Engaging enemy {enemy.id} in range {dist}")

            return AIState.HUNT, propose_move_toward(
                actor, enemy.spatial.pos, snapshot, "Spotted enemy → hunting")

        if actor.identity.faction == Faction.HERO_GUILD and actor.stats.progression.level >= 3:
            for em in actor.entity_memory:
                if not em.get("visible", False) and em.get("kind", "").startswith("goblin"):
                    remembered_pos = Vector2(em["x"], em["y"])
                    if actor.spatial.pos.manhattan(remembered_pos) > 3:
                        em_atk = em.get("atk", 0)
                        if em_atk > 0 and actor.stats.combat.atk > em_atk * 1.2:
                            return AIState.HUNT, propose_move_toward(
                                actor, remembered_pos, snapshot,
                                f"Returning to fight remembered enemy #{em['id']}")

        rng_val = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 999)
        frontier = Perception.find_frontier_target(actor, snapshot, rng_val)
        if frontier is not None:
            return AIState.WANDER, propose_move_toward(
                actor, frontier, snapshot, "Exploring unknown territory")

        direction_idx = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 3)
        offset = DIRECTION_OFFSETS[direction_idx]
        target = actor.spatial.pos + offset
        if is_tile_passable(actor, target, snapshot):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.MOVE, target=target,
                reason="Wandering randomly")
        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Wander blocked → resting")


class ReturnToTownHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        clear_dead_from_memory(actor, snapshot)

        if Perception.is_in_town(actor, snapshot):
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Arrived at town → resting")

        if actor.home_pos:
            return AIState.RETURN_TO_TOWN, propose_move_toward(
                actor, actor.home_pos, snapshot, "Heading to town")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No town to return to → wander")


class ReturnToCampHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)

        if actor.stats.combat.hp < actor.stats.combat.max_hp and config.mob_return_heal_rate > 0:
            heal = max(1, int(actor.stats.combat.max_hp * config.mob_return_heal_rate))
            actor.stats.combat.hp = min(actor.stats.combat.max_hp, actor.stats.combat.hp + heal)

        if Perception.is_in_camp(actor, snapshot):
            actor.chase_ticks = 0
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Arrived at camp → guarding")

        camp = Perception.nearest_camp(actor, snapshot)
        if camp:
            return AIState.RETURN_TO_CAMP, propose_move_toward(
                actor, camp, snapshot, "Heading to camp")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No camp to return to → wander")


class GuardCampHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config, rng = ctx.actor, ctx.snapshot, ctx.config, ctx.rng
        clear_dead_from_memory(actor, snapshot)
        enemy = ctx.nearest_enemy()

        if enemy is not None:
            if actor.spatial.pos.manhattan(enemy.spatial.pos) <= 1:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                    reason=f"Camp guard attacking intruder {enemy.id}")
            chase_range = max(4, actor.stats.vision_range)
            if actor.spatial.pos.manhattan(enemy.spatial.pos) <= chase_range:
                return AIState.HUNT, propose_move_toward(
                    actor, enemy.spatial.pos, snapshot, f"Camp guard chasing intruder {enemy.id}")

        camp = Perception.nearest_camp(actor, snapshot)
        if camp:
            dist_to_camp = actor.spatial.pos.manhattan(camp)
            if dist_to_camp > config.camp_radius + 1:
                return AIState.GUARD_CAMP, propose_move_toward(
                    actor, camp, snapshot, "Patrol → returning closer to camp")

        direction_idx = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 3)
        offset = DIRECTION_OFFSETS[direction_idx]
        target = actor.spatial.pos + offset
        if is_tile_passable(actor, target, snapshot):
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.MOVE, target=target,
                reason="Patrolling camp")
        return AIState.GUARD_CAMP, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Camp patrol blocked → resting")


class ExhaustedHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        return AIState.EXHAUSTED, ActionProposal(
            actor_id=ctx.actor.id,
            verb=ActionType.REST,
            reason="EXHAUSTED: Recovering stamina..."
        )

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/ai/states/town.py
from __future__ import annotations

from src.actions.base import ActionType, ActionProposal
from src.core.gameplay.buildings import (
    Building, RECIPES, RECIPE_MAP, SHOP_INVENTORY,
    can_craft, item_sell_price, shop_buy_price,
)
from src.core.models.enums import AIState, EntityRole
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.entities.entity import Entity
from src.core.gameplay.items.items import ItemType, _item_power
from src.ai.states.base import (
    AIContext, StateHandler, clear_dead_from_memory, 
    propose_move_toward
)


def find_building(snapshot, building_type: str) -> Building | None:
    """Find a building of the given type in the snapshot."""
    for b in snapshot.buildings:
        if b.building_type == building_type:
            return b
    return None


def can_use_buildings(actor: Entity) -> bool:
    """Return True if the entity's role permits using town buildings."""
    return actor.identity.role in (EntityRole.HERO, EntityRole.NPC)


def _get_equipped_for_type(actor: Entity, item_type: int) -> str | None:
    """Get the equipped item_id for a given ItemType."""
    if not actor.inventory:
        return None
    if item_type == ItemType.WEAPON:
        return actor.inventory.weapon
    elif item_type == ItemType.ARMOR:
        return actor.inventory.armor
    elif item_type == ItemType.ACCESSORY:
        return actor.inventory.accessory
    return None




def hero_has_sellable_items(actor: Entity) -> bool:
    """Return True if the hero has items they would want to sell at a shop."""
    inv = actor.inventory
    if not inv or not inv.items:
        return False

    for iid in inv.items:
        t = ITEM_REGISTRY.get(iid)
        if t is None:
            continue
        
        # Direct gold value items
        if t.gold_value > 0:
            return True
            
        # Materials (unless needed for current craft target)
        if t.item_type == ItemType.MATERIAL:
            if actor.craft_target:
                recipe = RECIPE_MAP.get(actor.craft_target)
                if recipe and iid in recipe.materials:
                    needed = recipe.materials[iid]
                    if inv.items.count(iid) <= needed:
                        continue
            return True
            
        # Inferior equipment
        if t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
            equipped = _get_equipped_for_type(actor, t.item_type)
            if equipped:
                eq_t = ITEM_REGISTRY.get(equipped)
                if eq_t and _item_power(t) < _item_power(eq_t):
                    return True
    return False


def hero_wants_to_buy(actor: Entity) -> str | None:
    """Check if hero wants to buy something from the shop."""
    if not actor.inventory:
        return None
    gold = actor.progression.gold
    inv = actor.inventory

    heal_potions = [
        ("large_hp_potion", 80), ("medium_hp_potion", 40), ("small_hp_potion", 15),
    ]
    total_heals = sum(inv.count_item(pid) for pid, _ in heal_potions)
    if total_heals < 2:
        for pid, price in heal_potions:
            if gold >= price and inv.can_add(pid):
                return pid

    best_upgrade = None
    best_upgrade_gain = 0
    for iid, price in SHOP_INVENTORY:
        if gold < price:
            continue
        t = ITEM_REGISTRY.get(iid)
        if t is None:
            continue
        if t.item_type not in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
            continue
        equipped = _get_equipped_for_type(actor, t.item_type)
        new_power = _item_power(t)
        cur_power = 0
        if equipped:
            eq_t = ITEM_REGISTRY.get(equipped)
            if eq_t:
                cur_power = _item_power(eq_t)
        gain = new_power - cur_power
        if gain > best_upgrade_gain:
            best_upgrade_gain = gain
            best_upgrade = iid
    if best_upgrade:
        return best_upgrade

    buff_ids = ["atk_potion", "def_potion", "spd_potion"]
    for bid in buff_ids:
        if inv.count_item(bid) == 0:
            price = shop_buy_price(bid)
            if price and gold >= price and inv.can_add(bid):
                return bid

    if actor.craft_target:
        recipe = RECIPE_MAP.get(actor.craft_target)
        if recipe:
            for mat_id, needed in recipe.materials.items():
                have = inv.items.count(mat_id)
                if have < needed:
                    price = shop_buy_price(mat_id)
                    if price and gold >= price and inv.can_add(mat_id):
                        return mat_id

    return None


def hero_should_visit_blacksmith(actor: Entity) -> bool:
    if not actor.inventory:
        return False
    if not actor.known_recipes:
        return True
    if actor.craft_target:
        recipe = RECIPE_MAP.get(actor.craft_target)
        if recipe and can_craft(recipe, actor.progression.gold, actor.inventory.items):
            return True
    return False


def hero_should_visit_guild(actor: Entity) -> bool:
    if not actor.entity_memory:
        return True
    known_prefixes = {"goblin", "wolf", "bandit", "skeleton", "zombie", "lich", "orc"}
    known_kinds = {em.get("kind", "") for em in actor.entity_memory}
    has_any_enemy_knowledge = any(
        any(k.startswith(prefix) for prefix in known_prefixes)
        for k in known_kinds
    )
    return not has_any_enemy_knowledge


def hero_should_visit_class_hall(actor: Entity) -> bool:
    from src.core.gameplay.classes import (
        HeroClass, available_class_skills, can_breakthrough, SKILL_DEFS,
    )
    try:
        hero_class = HeroClass(actor.progression.hero_class)
    except (ValueError, KeyError):
        return False
    if hero_class == HeroClass.NONE:
        return False
    known_ids = {s.skill_id for s in actor.progression.skills}
    available = available_class_skills(hero_class, actor.progression.level)
    for sid in available:
        if sid not in known_ids:
            sdef = SKILL_DEFS.get(sid)
            if sdef and actor.progression.gold >= sdef.gold_cost:
                return True
    if actor.attributes and can_breakthrough(hero_class, actor.progression.level, actor.attributes):
        return True
    return False


def hero_should_visit_inn(actor: Entity) -> bool:
    if actor.progression.max_stamina <= 0:
        return False
    return actor.progression.stamina < actor.progression.max_stamina * 0.4


def hero_should_visit_home(actor: Entity) -> bool:
    if not actor.home_storage or not actor.inventory:
        return False
    if actor.inventory.used_slots >= actor.inventory.max_slots - 2:
        if not actor.home_storage.is_full:
            return True
    cost = actor.home_storage.upgrade_cost()
    if cost is not None and actor.progression.gold >= cost:
        return True
    return False


class RestingInTownHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        clear_dead_from_memory(actor, snapshot)

        if actor.combat.hp < actor.combat.max_hp:
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Resting in town (healing)")

        want_buy = hero_wants_to_buy(actor)
        if want_buy:
            store = find_building(snapshot, "store")
            if store:
                return AIState.VISIT_SHOP, propose_move_toward(
                    actor, store.spatial.pos, snapshot, f"Heading to store to buy {want_buy}")

        if hero_should_visit_blacksmith(actor):
            bs = find_building(snapshot, "blacksmith")
            if bs:
                return AIState.VISIT_BLACKSMITH, propose_move_toward(
                    actor, bs.spatial.pos, snapshot, "Heading to blacksmith")

        if hero_should_visit_guild(actor):
            guild = find_building(snapshot, "guild")
            if guild:
                return AIState.VISIT_GUILD, propose_move_toward(
                    actor, guild.spatial.pos, snapshot, "Heading to guild for intel")

        if hero_should_visit_class_hall(actor):
            ch = find_building(snapshot, "class_hall")
            if ch:
                return AIState.VISIT_CLASS_HALL, propose_move_toward(
                    actor, ch.spatial.pos, snapshot, "Heading to class hall")

        if hero_should_visit_home(actor):
            if actor.home_pos:
                return AIState.VISIT_HOME, propose_move_toward(
                    actor, actor.home_pos, snapshot, "Heading home to manage storage")

        if hero_should_visit_inn(actor):
            inn = find_building(snapshot, "inn")
            if inn:
                return AIState.VISIT_INN, propose_move_toward(
                    actor, inn.spatial.pos, snapshot, "Heading to inn to recover stamina")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Fully healed → leaving town to explore")


class VisitShopHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        store = find_building(snapshot, "store")
        if store is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No store found")

        if actor.spatial.pos.manhattan(store.spatial.pos) > 0:
            return AIState.VISIT_SHOP, propose_move_toward(
                actor, store.spatial.pos, snapshot, "Walking to store")

        inv = actor.inventory
        if inv is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inventory")

        sold_any = False
        items_to_sell = []
        for iid in list(inv.items):
            t = ITEM_REGISTRY.get(iid)
            if t is None:
                continue
            should_sell = False
            if t.gold_value > 0:
                should_sell = True
            elif t.item_type == ItemType.MATERIAL:
                if actor.craft_target:
                    recipe = RECIPE_MAP.get(actor.craft_target)
                    if recipe and iid in recipe.materials:
                        needed = recipe.materials[iid]
                        have = inv.items.count(iid) - len([x for x in items_to_sell if x == iid])
                        if have <= needed:
                            continue
                should_sell = True
            elif t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                equipped = _get_equipped_for_type(actor, t.item_type)
                if equipped:
                    eq_t = ITEM_REGISTRY.get(equipped)
                    if eq_t and _item_power(t) < _item_power(eq_t):
                        should_sell = True
            if should_sell:
                items_to_sell.append(iid)

        total_gold = 0
        for iid in items_to_sell:
            if inv.remove_item(iid):
                price = item_sell_price(iid, actor.identity.reputation)
                actor.progression.gold += price
                total_gold += price
                sold_any = True

        if sold_any:
            from src.utils.metrics import SIM_SHOP_TRANSACTIONS_TOTAL
            for iid in items_to_sell:
                SIM_SHOP_TRANSACTIONS_TOTAL.labels(type="sell", item_id=iid).inc()
            return AIState.VISIT_SHOP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Sold items for {total_gold}g (total gold: {actor.progression.gold})")

        want = hero_wants_to_buy(actor)
        if want:
            price = shop_buy_price(want, actor.identity.reputation)
            if price and actor.progression.gold >= price and inv.can_add(want):
                actor.progression.gold -= price
                tax = int(price * 0.1)
                if hasattr(snapshot, 'town_treasury'):
                    snapshot.town_treasury += tax
                inv.add_item(want)
                from src.utils.metrics import SIM_SHOP_TRANSACTIONS_TOTAL
                SIM_SHOP_TRANSACTIONS_TOTAL.labels(type="buy", item_id=want).inc()
                inv.auto_equip_best(want)
                return AIState.VISIT_SHOP, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Bought {want} for {price}g")

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Done shopping → checking other activities")


class VisitBlacksmithHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        bs = find_building(snapshot, "blacksmith")
        if bs is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No blacksmith found")

        if actor.spatial.pos.manhattan(bs.spatial.pos) > 0:
            return AIState.VISIT_BLACKSMITH, propose_move_toward(
                actor, bs.spatial.pos, snapshot, "Walking to blacksmith")

        inv = actor.inventory
        if inv is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inventory")

        if not actor.known_recipes:
            actor.known_recipes = [r.recipe_id for r in RECIPES]
            best_recipe = None
            best_power = -1
            for r in RECIPES:
                t = ITEM_REGISTRY.get(r.output_item)
                if t is None:
                    continue
                power = _item_power(t)
                equipped = _get_equipped_for_type(actor, t.item_type)
                if equipped:
                    eq_t = ITEM_REGISTRY.get(equipped)
                    if eq_t and power <= _item_power(eq_t):
                        continue
                if power > best_power:
                    best_power = power
                    best_recipe = r.recipe_id
            if best_recipe:
                actor.craft_target = best_recipe
            return AIState.VISIT_BLACKSMITH, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Learned {len(RECIPES)} recipes from blacksmith! Target: {actor.craft_target}")

        if actor.craft_target:
            recipe = RECIPE_MAP.get(actor.craft_target)
            if recipe and can_craft(recipe, actor.progression.gold, inv.items):
                for mat_id, qty in recipe.materials.items():
                    for _ in range(qty):
                        inv.remove_item(mat_id)
                actor.progression.gold -= recipe.gold_cost
                if inv.can_add(recipe.output_item):
                    inv.add_item(recipe.output_item)
                    t = ITEM_REGISTRY.get(recipe.output_item)
                    if t and t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                        inv.equip(recipe.output_item)
                
                from src.utils.metrics import SIM_ITEMS_CRAFTED_TOTAL
                tier = "T1"
                if "t2" in recipe.output_item.lower(): tier = "T2"
                elif "t3" in recipe.output_item.lower(): tier = "T3"
                SIM_ITEMS_CRAFTED_TOTAL.labels(item_id=recipe.output_item, tier=tier).inc()
                
                actor.craft_target = None
                return AIState.VISIT_BLACKSMITH, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Crafted {recipe.output_item}!")

        if actor.craft_target:
            recipe = RECIPE_MAP.get(actor.craft_target)
            if recipe:
                missing = []
                for mat_id, qty in recipe.materials.items():
                    have = inv.items.count(mat_id)
                    if have < qty:
                        missing.append(f"{mat_id} ({have}/{qty})")
                gold_needed = max(0, recipe.gold_cost - actor.progression.gold)
                reason = f"Need: {', '.join(missing)}"
                if gold_needed > 0:
                    reason += f" + {gold_needed}g"
                return AIState.WANDER, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Left blacksmith to gather materials — {reason}")

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Nothing to craft → checking other activities")


class VisitGuildHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        guild = find_building(snapshot, "guild")
        if guild is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No guild found")

        if actor.spatial.pos.manhattan(guild.spatial.pos) > 0:
            return AIState.VISIT_GUILD, propose_move_toward(
                actor, guild.spatial.pos, snapshot, "Walking to guild hall")

        intel_added = False
        for cx, cy in snapshot.camps:
            camp_key = (cx, cy)
            if camp_key not in actor.terrain_memory:
                actor.terrain_memory[camp_key] = 4
                intel_added = True
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    k = (cx + dx, cy + dy)
                    if k not in actor.terrain_memory:
                        actor.terrain_memory[k] = 0

        regions_revealed = 0
        for node in snapshot.resource_nodes:
            nk = (node.spatial.pos.x, node.spatial.pos.y)
            if nk not in actor.terrain_memory:
                actor.terrain_memory[nk] = node.terrain.value if hasattr(node.terrain, 'value') else int(node.terrain)
                intel_added = True
                regions_revealed += 1

        if intel_added:
            parts = []
            if snapshot.camps:
                parts.append(f"{len(snapshot.camps)} camp locations")
            if regions_revealed:
                parts.append(f"{regions_revealed} resource nodes")
            return AIState.VISIT_GUILD, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Guild revealed {', '.join(parts)}!")

        from src.core.gameplay.quests import generate_quest, MAX_ACTIVE_QUESTS
        active_quests = [q for q in actor.quests if not q.completed]
        if len(active_quests) < MAX_ACTIVE_QUESTS:
            existing_ids = {q.quest_id for q in actor.quests}
            new_quest = generate_quest(
                hero_level=actor.progression.level,
                existing_quest_ids=existing_ids,
                rng=ctx.rng,
                entity_id=actor.id,
                tick=snapshot.tick,
                grid_width=snapshot.grid.width if hasattr(snapshot, 'grid') else 100,
                grid_height=snapshot.grid.height if hasattr(snapshot, 'grid') else 100,
                world=snapshot,
            )
            if new_quest:
                actor.quests.append(new_quest)
                return AIState.VISIT_GUILD, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Accepted quest: {new_quest.title}")

        from src.core.gameplay.buildings import MATERIAL_HINTS
        if actor.craft_target:
            recipe = RECIPE_MAP.get(actor.craft_target)
            if recipe:
                for mat_id in recipe.materials:
                    hint = MATERIAL_HINTS.get(mat_id)
                    if hint and hint not in actor.mind.goals:
                        actor.mind.goals.append(f"Guild tip: {mat_id} — {hint}")

        terrain_tips = [
            "Forests (green) host wolves — wolf pelts and fangs drop there.",
            "Deserts (tan) host bandits — fiber and raw gems found there.",
            "Swamps (purple) host undead — bone shards and ectoplasm drop there.",
            "Mountains (grey) host orcs — stone blocks and iron ore found there.",
        ]
        for tip in terrain_tips:
            if tip not in actor.mind.goals:
                actor.mind.goals.append(f"Guild tip: {tip}")

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Got intel from guild → planning next move")


class VisitClassHallHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        ch = find_building(snapshot, "class_hall")
        if ch is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No class hall found")

        if actor.spatial.pos.manhattan(ch.spatial.pos) > 0:
            return AIState.VISIT_CLASS_HALL, propose_move_toward(
                actor, ch.spatial.pos, snapshot, "Walking to class hall")

        from src.core.gameplay.classes import (
            HeroClass, available_class_skills, can_breakthrough, can_learn_skill,
            SKILL_DEFS, BREAKTHROUGHS, CLASS_DEFS, SkillInstance,
        )
        try:
            hero_class = HeroClass(actor.progression.hero_class)
        except (ValueError, KeyError, TypeError, AttributeError):
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No class → switching")

        from src.systems.lifecycle.progression_system import available_class_skills, can_learn_skill
        from src.core.gameplay.classes import SkillInstance
        
        known_ids = {s.skill_id for s in actor.progression.skills}
        available = available_class_skills(hero_class, actor.progression.level)
        for sid in available:
            if sid not in known_ids:
                sdef = SKILL_DEFS.get(sid)
                if sdef and actor.progression.gold >= sdef.gold_cost:
                    can_learn, _ = can_learn_skill(
                        sdef, actor.progression.level, actor.progression.skills, actor.progression.class_mastery)
                    if not can_learn:
                        continue
                    actor.progression.gold -= sdef.gold_cost
                    actor.progression.skills.append(SkillInstance(skill_id=sid))
                    return AIState.VISIT_CLASS_HALL, ActionProposal(
                        actor_id=actor.id, verb=ActionType.REST, 
                        reason=f"Learned skill: {sdef.name} (cost {sdef.gold_cost}g)")

        if actor.attributes and can_breakthrough(hero_class, actor.progression.level, actor.attributes):
            bt = BREAKTHROUGHS.get(hero_class)
            if bt:
                actor.progression.hero_class = int(bt.to_class)
                new_cdef = CLASS_DEFS.get(bt.to_class)
                if new_cdef and actor.attribute_caps:
                    actor.attribute_caps.str_cap += new_cdef.str_cap_bonus
                    actor.attribute_caps.agi_cap += new_cdef.agi_cap_bonus
                    actor.attribute_caps.vit_cap += new_cdef.vit_cap_bonus
                    actor.attribute_caps.int_cap += new_cdef.int_cap_bonus
                    actor.attribute_caps.spi_cap += new_cdef.spi_cap_bonus
                    actor.attribute_caps.wis_cap += new_cdef.wis_cap_bonus
                    actor.attribute_caps.end_cap += new_cdef.end_cap_bonus
                    actor.attribute_caps.per_cap += new_cdef.per_cap_bonus
                    actor.attribute_caps.cha_cap += new_cdef.cha_cap_bonus
                return AIState.VISIT_CLASS_HALL, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"CLASS BREAKTHROUGH! → {bt.to_class.name} (Talent: {bt.talent})")

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Done at class hall → checking other activities")


class VisitInnHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        inn = find_building(snapshot, "inn")
        if inn is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inn found")

        if actor.spatial.pos.manhattan(inn.spatial.pos) > 0:
            return AIState.VISIT_INN, propose_move_toward(
                actor, inn.spatial.pos, snapshot, "Walking to inn")

        healed = False
        if actor.combat.hp < actor.combat.max_hp:
            actor.combat.hp = min(actor.combat.hp + 10, actor.combat.max_hp)
            healed = True
        if actor.progression.stamina < actor.progression.max_stamina:
            actor.progression.stamina = min(actor.progression.stamina + 10, actor.progression.max_stamina)
            healed = True
        if actor.attributes and actor.attribute_caps:
            from src.core.gameplay.attributes import train_attributes
            train_attributes(actor.attributes, actor.attribute_caps, "rest", stats=actor.stats)

        if healed:
            return AIState.VISIT_INN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Resting at inn (HP: {actor.combat.hp}/{actor.combat.max_hp}, "
                       f"STA: {actor.progression.stamina}/{actor.progression.max_stamina})")

        from src.core.gameplay.effects import EffectType, well_rested_effect
        actor.remove_effects_by_type(EffectType.RESTED)
        actor.effects.append(well_rested_effect())

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Fully recovered at inn + Well-Rested! → checking other activities")


class VisitHomeHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        if actor.home_pos is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No home set")

        if actor.spatial.pos.manhattan(actor.home_pos) > 0:
            return AIState.VISIT_HOME, propose_move_toward(
                actor, actor.home_pos, snapshot, "Walking home")

        inv = actor.inventory
        storage = actor.home_storage
        if inv is None or storage is None:
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inventory/storage")

        cost = storage.upgrade_cost()
        if cost is not None and actor.stats.progression.gold >= cost:
            actor.stats.progression.gold -= cost
            old_max = storage.max_slots
            storage.upgrade()
            return AIState.VISIT_HOME, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Upgraded home storage {old_max}→{storage.max_slots} slots (-{cost}g)")

        stored = []
        for iid in list(inv.items):
            if storage.is_full:
                break
            t = ITEM_REGISTRY.get(iid)
            if t is None:
                continue
            should_store = False
            if t.item_type == ItemType.MATERIAL:
                if actor.craft_target:
                    recipe = RECIPE_MAP.get(actor.craft_target)
                    if recipe and iid in recipe.materials:
                        needed = recipe.materials[iid]
                        have = inv.items.count(iid) - len([x for x in stored if x == iid])
                        if have <= needed:
                            continue
                should_store = True
            elif t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                equipped = _get_equipped_for_type(actor, t.item_type)
                if equipped:
                    eq_t = ITEM_REGISTRY.get(equipped)
                    if eq_t and _item_power(t) < _item_power(eq_t):
                        should_store = True
            elif t.item_type == ItemType.CONSUMABLE and t.heal_amount > 0:
                count_in_inv = inv.items.count(iid) - len([x for x in stored if x == iid])
                if count_in_inv > 2:
                    should_store = True

            if should_store:
                if inv.remove_item(iid) and storage.add_item(iid):
                    stored.append(iid)

        if stored:
            return AIState.VISIT_HOME, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Stored {len(stored)} items at home ({storage.used_slots}/{storage.max_slots})")

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Done at home → checking other activities")

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/__init__.py
"""API layer: FastAPI web server wrapping the simulation engine."""

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/app.py
"""FastAPI application factory with lifespan management."""

from __future__ import annotations

import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from src.api.dependencies import set_engine_manager
from src.api.engine_manager import EngineManager
from src.api.routes import api_router
from src.config import SimulationConfig
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
STATIC_DIR = FRONTEND_DIR / "dist"


def create_app(config: SimulationConfig | None = None) -> FastAPI:
    """Build and return the fully-configured FastAPI application."""
    if config is None:
        config = SimulationConfig()

    _config = config

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        from src.core.registry.registry_loader import load_all_registries
        setup_logging(_config.log_level)
        load_all_registries()
        manager = EngineManager(_config)
        set_engine_manager(manager)
        manager.start()
        logger.info("API server started — simulation running.")
        yield
        manager.stop()
        logger.info("API server shutting down.")


    app = FastAPI(
        title="RPG Simulation Engine",
        description=(
            "Deterministic Concurrent RPG Engine — Real-Time Visualization API.\n\n"
            "## API Groups\n\n"
            "- **State** — Live simulation state: entities, events, buildings, ground items\n"
            "- **Map** — Static grid data (fetch once at startup)\n"
            "- **Control** — Simulation lifecycle: start, pause, resume, step, reset\n"
            "- **Config** — Read-only simulation configuration\n"
            "- **Metadata** — Game definitions (items, classes, traits, skills, etc.) — single source of truth\n"
        ),
        version="0.1.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "State", "description": "Live simulation state polled by the frontend: entities, events, buildings, ground items, resource nodes."},
            {"name": "Map", "description": "Static grid/map data. Fetched once at startup — the tile layout does not change during a run."},
            {"name": "Control", "description": "Simulation lifecycle controls: start, pause, resume, single-step, and reset."},
            {"name": "Config", "description": "Read-only simulation configuration parameters (world size, tick rate, hero settings, etc.)."},
            {"name": "Metadata", "description": "All game definitions — items, classes, skills, traits, attributes, buildings, resources, recipes, enums. These are pydantic dataclasses from src/core/ serialized directly — the single source of truth for both engine and frontend."},
        ],
    )

    # CORS — allow any origin in dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Compress JSON responses (target: reduced 1.3kb payload)
    # But exempt /metrics which Prometheus might struggle with if gzipped
    class ConditionalGZipMiddleware(GZipMiddleware):
        async def __call__(self, scope, receive, send) -> None:
            if scope["type"] == "http" and scope["path"].startswith("/metrics"):
                await self.app(scope, receive, send)
                return
            await super().__call__(scope, receive, send)

    app.add_middleware(ConditionalGZipMiddleware, minimum_size=512)

    from src.utils.metrics import API_REQUEST_DURATION

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            
            # We don't want to track the intense /stream or /metrics polling endpoint itself as heavily
            path = request.url.path
            if path not in ("/metrics", "/api/v1/stream"):
                from src.utils.metrics import API_REQUEST_DURATION
                API_REQUEST_DURATION.labels(method=request.method, endpoint=path).observe(duration)
                
            return response
        except Exception as e:
            from src.utils.metrics import SIM_ERRORS_TOTAL
            SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="api_middleware").inc()
            logger.exception("Unhandled API error: %s", e)
            raise

    # Mount Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # API routes
    from src.api.routes import (
        state, map, control, metadata, 
        config, stream, stream_ws
    )
    app.include_router(state.router, prefix="/api/v1")
    app.include_router(map.router, prefix="/api/v1")
    app.include_router(control.router, prefix="/api/v1/control")
    app.include_router(metadata.router, prefix="/api/v1")
    app.include_router(config.router, prefix="/api/v1")
    app.include_router(stream.router, prefix="/api/v1/stream")
    app.include_router(stream_ws.router, prefix="/api/v1")

    @app.get("/health", tags=["Control"])
    async def health_check():
        """Basic health check for orchestration and monitoring."""
        return {"status": "ok", "timestamp": time.time()}

    # Serve frontend static files
    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")

    return app

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/dependencies.py
"""FastAPI dependency injection — provides the EngineManager singleton."""

from __future__ import annotations

from src.api.engine_manager import EngineManager

_engine_manager: EngineManager | None = None


def set_engine_manager(manager: EngineManager) -> None:
    global _engine_manager
    _engine_manager = manager


def get_engine_manager() -> EngineManager:
    if _engine_manager is None:
        raise RuntimeError("EngineManager not initialized — server not started correctly.")
    return _engine_manager

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/encoder.py
from __future__ import annotations
from typing import Any, TYPE_CHECKING
import msgpack
import json

if TYPE_CHECKING:
    from src.core.models.snapshot import Snapshot
    from src.core.entities.entity import Entity
    from src.core.data.events import Event

# --- Constants for Compact Protocol ---

# Order must match exactly in both backend and frontend
ENTITY_KEY_MAP = [
    "id", "x", "y", "hp", "state_id", "target_id", "loot_progress"
]

STATE_ENUM_MAP = {
    "IDLE": 0,
    "MOVE": 1,
    "COMBAT": 2,
    "LOOT": 3,
    "HARVEST": 4,
    "CRAFT": 5,
    "REST": 6,
    "DEAD": 7,
    "FLEE": 8,
    "WANDER": 9
}

class WorldStateEncoder:
    """Serializes simulation state into Rich (Dict) or Compact (List) formats."""

    @staticmethod
    def encode_entity(entity: Entity, mode: str = "rich") -> dict[str, Any] | list[Any]:
        """Encodes a single entity."""
        if mode == "compact":
            # [id, x, y, hp, state_id, target_id, loot_progress]
            state_name = entity.mind.ai_state.name.upper() if hasattr(entity, 'ai_state') else "IDLE"
            state_id = STATE_ENUM_MAP.get(state_name, 0)
            return [
                entity.id,
                int(entity.spatial.pos.x),
                int(entity.spatial.pos.y),
                entity.stats.combat.hp,
                state_id,
                entity.combat_target_id,
                entity.loot_progress
            ]
        else:
            # Traditional Rich Dict (matches EntitySlimSchema partially)
            return {
                "id": entity.id,
                "kind": entity.kind,
                "display_name": entity.identity.display_name,
                "x": int(entity.spatial.pos.x),
                "y": int(entity.spatial.pos.y),
                "hp": entity.stats.combat.hp,
                "max_hp": entity.stats.combat.max_hp,
                "state": entity.mind.ai_state.name.lower() if hasattr(entity, 'ai_state') else "idle",
                "level": entity.stats.progression.level,
                "faction": entity.identity.faction.name.lower() if hasattr(entity.identity.faction, 'name') else str(entity.identity.faction),
                "combat_target_id": entity.combat_target_id
            }

    @staticmethod
    def encode_event(event: Event, mode: str = "rich") -> dict[str, Any] | list[Any]:
        """Encodes a single domain event."""
        if mode == "compact":
            # [tick, category, message, entity_ids]
            return [
                event.tick,
                event.category,
                event.message,
                list(event.entity_ids)
            ]
        else:
            return {
                "tick": event.tick,
                "category": event.category,
                "message": event.message,
                "entity_ids": list(event.entity_ids),
                "metadata": event.metadata
            }

    @classmethod
    def encode_tick(cls, snapshot: Snapshot, events: list[Event], mode: str = "compact") -> Any:
        """Encodes an entire tick state."""
        entities = [
            cls.encode_entity(e, mode)
            for e in snapshot.entities.values()
            if e.combat.alive
        ]
        encoded_events = [
            cls.encode_event(ev, mode)
            for ev in events
        ]
        
        if mode == "compact":
            # [tick, entities, events]
            return [snapshot.tick, entities, encoded_events]
        else:
            return {
                "tick": snapshot.tick,
                "entities": entities,
                "events": encoded_events,
                "alive_count": len(entities)
            }

    @classmethod
    def serialize(cls, data: Any, format: str = "msgpack") -> bytes | str:
        """Final serialization to wire format."""
        if format == "msgpack":
            return msgpack.packb(data, use_bin_type=True)
        else:
            return json.dumps(data)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/engine_manager.py
"""EngineManager — singleton wrapper that runs the WorldLoop on a background thread.

The API reads from an atomically-swapped immutable Snapshot; the WorldLoop
mutates WorldState exclusively on its own thread (Single-Writer preserved).
"""

from __future__ import annotations

import logging
import threading
import time
import typing
from typing import TYPE_CHECKING

from src.ai.brain import AIBrain
from src.core.gameplay.buildings import Building
from src.core.models.enums import AIState, Domain, EnemyTier, EntityRole, Material
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.world.grid import Grid
from src.core.entities.entity import Entity, Stats, Vector2, Inventory
from src.core.world.regions import Region, Location
from src.core.world.resource_nodes import ResourceNode
from src.core.models.snapshot import Snapshot
from src.core.models.world_state import WorldState
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.engine.world_loop import WorldLoop
from src.systems.world.generator import EntityGenerator
from src.platform.rng import DeterministicRNG
from src.platform.spatial_hash import SpatialHash
from src.utils.event_log import EventLog, SimEvent
from src.core.world.world_generator import WorldGenerator

if TYPE_CHECKING:
    from src.config import SimulationConfig

logger = logging.getLogger(__name__)


class EngineManager:
    """Manages the simulation lifecycle on a background thread.

    Provides thread-safe access to:
      - latest snapshot (atomic reference swap)
      - event log (lock-guarded ring buffer)
      - control commands (start / pause / resume / step / reset)
    """

    def __init__(self, config: SimulationConfig) -> None:
        self._config = config
        self.config = config
        self._tick_rate: float = 0.05  # seconds between ticks (20 tps default)

        # Simulation components (built in _build)
        self._rng: DeterministicRNG | None = None
        self._loop: WorldLoop | None = None
        self._worker_pool: WorkerPool | None = None

        # Thread-safe shared state
        self._snapshot_lock = threading.Lock()
        self._latest_snapshot: Snapshot | None = None
        self._event_log = EventLog()

        # Counters
        self._total_spawned: int = 0
        self._total_deaths: int = 0

        # Control
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self._paused = threading.Event()
        self._step_requested = threading.Event()
        self._stop_requested = threading.Event()

        self._build()
        
        # Wrapped logger (Phase L3 Logging)
        from src.utils.logging import RobustLoggerAdapter
        self._logger = RobustLoggerAdapter(logger, {'component': 'engine_manager', 'tick': -1})

    # -- public properties --

    @property
    def running(self) -> bool:
        return self._running.is_set()

    @property
    def paused(self) -> bool:
        return self._paused.is_set()

    @property
    def tick_rate(self) -> float:
        return self._tick_rate

    @tick_rate.setter
    def tick_rate(self, value: float) -> None:
        self._tick_rate = max(0.01, min(value, 2.0))

    @property
    def event_log(self) -> EventLog:
        return self._event_log

    @property
    def total_spawned(self) -> int:
        return self._total_spawned

    @property
    def total_deaths(self) -> int:
        return self._total_deaths

    # -- listeners --

    def add_tick_listener(self, cb: typing.Callable[[Snapshot, list[SimEvent]], None]) -> None:
        with self._listeners_lock:
            if cb not in self._listeners:
                self._listeners.append(cb)

    def remove_tick_listener(self, cb: typing.Callable[[Snapshot, list[SimEvent]], None]) -> None:
        with self._listeners_lock:
            if cb in self._listeners:
                self._listeners.remove(cb)

    # -- snapshot access --

    def get_snapshot(self) -> Snapshot | None:
        with self._snapshot_lock:
            return self._latest_snapshot

    def get_grid(self) -> Grid | None:
        """Return the grid from the latest snapshot (static data)."""
        snap = self.get_snapshot()
        return snap.grid if snap else None

    # -- lifecycle --

    def start(self) -> None:
        if self._running.is_set():
            return
        self._stop_requested.clear()
        self._paused.clear()
        self._running.set()
        self._thread = threading.Thread(target=self._run_loop, name="engine-loop", daemon=True)
        self._thread.start()
        # Start resource metrics collector
        try:
            from src.utils.resource_collector import start_resource_collector
            start_resource_collector()
        except Exception:
            self._logger.debug("Resource collector not started", exc_info=True)
        self._logger.info("EngineManager started (tick_rate=%.3fs)", self._tick_rate)

    def pause(self) -> None:
        self._paused.set()
        logger.info("EngineManager paused at tick %d", self._current_tick())

    def resume(self) -> None:
        self._paused.clear()
        logger.info("EngineManager resumed at tick %d", self._current_tick())

    def step(self) -> None:
        """Execute exactly one tick (must be paused)."""
        if not self._paused.is_set():
            self.pause()
        self._step_requested.set()

    def stop(self) -> None:
        self._stop_requested.set()
        self._paused.clear()
        self._running.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        if self._worker_pool:
            self._worker_pool.shutdown()
        self._logger.info("EngineManager stopped.")

    def reset(self) -> None:
        """Stop, rebuild, and leave in paused state ready to start."""
        self.stop()
        self._event_log.clear()
        self._total_spawned = 0
        self._total_deaths = 0
        self._build()
        # Take initial snapshot
        if self._loop:
            snap = self._loop.create_snapshot()
            with self._snapshot_lock:
                self._latest_snapshot = snap
        logger.info("EngineManager reset.")

    # -- internals --

    def _build(self) -> None:
        """Construct all simulation components from config."""
        cfg = self._config
        self._rng = DeterministicRNG(cfg.world_seed)
        
        # --- KAFKA RECOVERY ---
        world = self._try_recover_world(cfg)
        if world is not None:
            generator = EntityGenerator(cfg, self._rng)
            self._finalize_build(world, cfg, generator)
            return
            
        # --- GENERATE NEW WORLD (epic-05 EngineManager decomposition) ---
        generator_service = WorldGenerator(cfg, self._rng)
        world, generator = generator_service.generate()
        self._total_spawned = generator_service.total_spawned
        self._finalize_build(world, cfg, generator)

    def _finalize_build(self, world: WorldState, cfg: SimulationConfig, generator: EntityGenerator) -> None:
        """Finalize engine setup: create loop, brain, worker pool, and initial snapshot."""
        faction_reg = FactionRegistry.default()
        brain = AIBrain(cfg, self._rng, faction_reg)
        assert self._rng is not None
        self._worker_pool = WorkerPool(cfg, brain, self._rng)
        conflict_resolver = ConflictResolver(cfg, self._rng)

        self._loop = WorldLoop(
            config=cfg, world=world, worker_pool=self._worker_pool,
            conflict_resolver=conflict_resolver, generator=generator,
            faction_reg=faction_reg, rng=self._rng,
        )

        # Initial snapshot
        snap = self._loop.create_snapshot()
        with self._snapshot_lock:
            self._latest_snapshot = snap

    def _try_recover_world(self, cfg: SimulationConfig) -> WorldState | None:
        """Attempt to recover the simulation state from Kafka."""
        import pickle
        import uuid
        from src.api.kafka_client import create_kafka_consumer, KAFKA_TOPIC_SNAPSHOTS, KAFKA_TOPIC_EVENTS
        from confluent_kafka import TopicPartition, OFFSET_BEGINNING
        
        # Unique consumer group for startup so it doesn't mess with other readers
        consumer = create_kafka_consumer(f"sim_startup_{uuid.uuid4().hex}")
        if not consumer:
            return None
            
        try:
            # 1. Recover latest Compacted Snapshot
            consumer.assign([TopicPartition(KAFKA_TOPIC_SNAPSHOTS, 0)])
            consumer.seek(TopicPartition(KAFKA_TOPIC_SNAPSHOTS, 0, OFFSET_BEGINNING))
            
            latest_snap = None
            timeout_strikes = 0
            # Read until we hit EOF for the partition
            while timeout_strikes < 3:
                msg = consumer.poll(0.5)
                if msg is None:
                    timeout_strikes += 1
                    continue
                timeout_strikes = 0  # reset on active read
                
                if msg.error():
                    break
                    
                try:
                    obj = pickle.loads(msg.value())
                    if obj and hasattr(obj, 'tick'):
                        latest_snap = obj
                except Exception as e:
                    logger.debug("Failed to deserialize snapshot: %s", e)
                    
            if not latest_snap:
                logger.debug("Kafka Setup: No snapshot found on sim.snapshots")
                return None
                
            logger.info("Kafka Setup: Recovered snapshot at tick %d", latest_snap.tick)
            
            spatial = SpatialHash(cfg.spatial_cell_size)
            world = WorldState.from_snapshot(latest_snap, spatial)
            
            # 2. Replay subsequent Events
            consumer.assign([TopicPartition(KAFKA_TOPIC_EVENTS, 0)])
            consumer.seek(TopicPartition(KAFKA_TOPIC_EVENTS, 0, OFFSET_BEGINNING))
            
            resolver = ConflictResolver(cfg, DeterministicRNG(cfg.world_seed))
            replayed_ticks = 0
            timeout_strikes = 0
            
            while timeout_strikes < 3:
                msg = consumer.poll(0.5)
                if msg is None:
                    timeout_strikes += 1
                    continue
                timeout_strikes = 0
                
                if msg.error():
                    break
                    
                try:
                    payload = pickle.loads(msg.value())
                    tick = payload.get("tick")
                    proposals = payload.get("proposals", [])
                    
                    # Log compaction guarantees ordered snapshots, but we must strictly ensure
                    # we only apply events that happened AFTER this snapshot's tick
                    if tick and tick > world.tick:
                        resolver.resolve(proposals, world)
                        world.tick = tick
                        replayed_ticks += 1
                except Exception as e:
                    logger.debug("Failed to deserialize event: %s", e)
                    
            if replayed_ticks > 0:
                logger.info("Kafka Setup: Replayed %d ticks of events. Current synchronized tick: %d", 
                            replayed_ticks, world.tick)
                            
            return world
            
        except Exception as e:
            # Downgrade to debug if it's a state error (e.g. empty topics during E2E start)
            if "Erroneous state" in str(e) or "_STATE" in str(e):
                logger.debug("Kafka recovery skipped (topic likely empty): %s", e)
            else:
                logger.error("Failed to recover world from Kafka: %s", e)
            return None
        finally:
            consumer.close()

    def _run_loop(self) -> None:
        """Background thread main loop."""
        logger.info("Engine thread started.")
        assert self._loop is not None

        while not self._stop_requested.is_set():
            # Handle pause
            if self._paused.is_set() and not self._step_requested.is_set():
                time.sleep(0.01)
                continue

            single_step = self._step_requested.is_set()
            if single_step:
                self._step_requested.clear()

            # Execute one tick
            _tick_start = time.perf_counter()
            alive_before = set(self._loop.world.entities.keys())
            can_continue = self._loop.tick_once()

            if not can_continue:
                self._publish_snapshot_and_events()
                logger.info("Simulation ended at tick %d.", self._loop.world.tick)
                break

            # Track spawns / deaths
            alive_after = set(self._loop.world.entities.keys())
            new_ids = alive_after - alive_before
            dead_ids = alive_before - alive_after
            self._total_spawned += len(new_ids)
            self._total_deaths += len(dead_ids)

            from src.utils.metrics import (
                ACTIVE_ENTITIES, TOTAL_SPAWNS, TOTAL_DEATHS,
                SIM_CURRENT_TICK, SIM_TICKS_PER_SECOND,
            )

            current_tick = self._loop.world.tick
            ACTIVE_ENTITIES.set(len(alive_after))
            SIM_CURRENT_TICK.set(current_tick)
            if new_ids:
                TOTAL_SPAWNS.inc(len(new_ids))
            if dead_ids:
                TOTAL_DEATHS.inc(len(dead_ids))

            # Throughput
            tick_elapsed = time.perf_counter() - _tick_start
            if tick_elapsed > 0:
                SIM_TICKS_PER_SECOND.set(1.0 / tick_elapsed)

            self._publish_snapshot_and_events()

            # Rate limiting
            if not single_step:
                time.sleep(self._tick_rate)

        self._running.clear()
        logger.info("Engine thread exited.")

    def _publish_snapshot_and_events(self) -> None:
        """Swap snapshot + push events to Redis Stream."""
        assert self._loop is not None
        snap = self._loop.create_snapshot()
        with self._snapshot_lock:
            self._latest_snapshot = snap

        events: list[SimEvent] = self._loop.tick_events
        if events:
            self._event_log.append_many(events)

        # Publish the state delta to Redis Streams (infra-07)
        try:
            from src.api.redis_client import get_sync_redis
            from src.api.routes.stream import compute_delta, _snapshot_to_slim_dict
            from src.utils.metrics import SIM_REDIS_PUBLISH_DURATION
            r = get_sync_redis()

            _t0 = time.perf_counter()

            # Convert snapshots to slim entity dicts for diffing
            loot_duration = self.config.loot_duration
            new_slim = _snapshot_to_slim_dict(snap, loot_duration)
            old_slim = getattr(self, "_last_published_slim", {})

            payload_json = compute_delta(old_slim, new_slim, snap.tick, events)

            if payload_json:
                r.xadd("sim:stream", {"payload": payload_json})

            duration = time.perf_counter() - _t0
            SIM_REDIS_PUBLISH_DURATION.observe(duration)
            from src.utils.metrics import SIM_REDIS_LATENCY
            SIM_REDIS_LATENCY.labels(op="stream_publish").observe(duration)

            # Save slim dict for the NEXT tick's diff
            self._last_published_slim = new_slim

        except Exception:
            logger.exception("Failed to publish tick %d to Redis", self._loop.world.tick)

    def _current_tick(self) -> int:
        if self._loop:
            return self._loop.world.tick
        return 0

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/kafka_client.py
"""Kafka Client for persistent event sourcing and epoch snapshots."""

import logging
import os
from typing import Any

from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient, NewTopic

logger = logging.getLogger(__name__)

# Kafka topics
KAFKA_TOPIC_EVENTS = "sim.events"
KAFKA_TOPIC_SNAPSHOTS = "sim.snapshots"

_PRODUCER_INSTANCE: Producer | None = None

def get_kafka_url() -> str:
    """Return the configured Kafka bootstrap servers."""
    return os.environ.get("KAFKA_URL", "127.0.0.1:9092")

def is_kafka_disabled() -> bool:
    """Return True if Kafka integration is explicitly disabled."""
    return os.environ.get("DISABLE_KAFKA", "0").lower() in ("1", "true", "yes")

def init_kafka_topics() -> None:
    """Idempotently create exactly the required topics with appropriate configurations."""
    if is_kafka_disabled():
        logger.info("Kafka integration disabled via environment variable.")
        return
        
    admin_client = AdminClient({"bootstrap.servers": get_kafka_url()})
    
    # 1. Events Topic: We want this to be an immutable append-only log of deltas,
    # but practically we don't need infinite history locally, standard deletion is fine.
    # We'll use default retention (7 days usually) for safety.
    topic_events = NewTopic(KAFKA_TOPIC_EVENTS, num_partitions=1, replication_factor=1)
    
    # 2. Snapshots Topic: We only care about the relatively recent snapshots.
    # We use log compaction so we can aggressively prune old snapshots while keeping the newest.
    # The key will be "latest" so compaction automatically drops old snapshots.
    topic_snapshots = NewTopic(
        KAFKA_TOPIC_SNAPSHOTS, 
        num_partitions=1, 
        replication_factor=1,
        config={"cleanup.policy": "compact"}
    )
    
    to_create = [topic_events, topic_snapshots]
    
    try:
        # Create topics async
        futures = admin_client.create_topics(to_create)
        for topic, future in futures.items():
            try:
                future.result()  # blocking call to wait for creation
                logger.info("Kafka topic '%s' created successfully.", topic)
            except Exception as e:
                # 36 is topic_already_exists in confluent-kafka Error Codes
                if getattr(e, "args", [None])[0] and "TopicExists" in str(e):
                    logger.debug("Kafka topic '%s' already exists.", topic)
                else:
                    logger.warning("Failed to create topic '%s': %s", topic, e)
    except Exception as e:
        logger.error("Failed to connect to Kafka AdminClient: %s", e)


def get_kafka_producer() -> Producer | None:
    """Return a singleton, highly-durable Kafka Producer."""
    global _PRODUCER_INSTANCE
    
    if is_kafka_disabled():
        return None
        
    if _PRODUCER_INSTANCE is not None:
        return _PRODUCER_INSTANCE
        
    bootstrap_servers = get_kafka_url()
    
    import time
    for i in range(40): # Increased to 40 attempts (120s) for slow Docker bootstrap on Windows
        try:
            conf = {
                'bootstrap.servers': bootstrap_servers,
                'client.id': 'sim-engine-producer',
                'message.max.bytes': 10000000, # 10MB to match broker
                'acks': 'all',
                'retries': 5,
                'retry.backoff.ms': 500
            }
            _PRODUCER_INSTANCE = Producer(conf)
            # Confirm connectivity by fetching metadata
            _PRODUCER_INSTANCE.list_topics(timeout=2.0)
            logger.info("Successfully connected to Kafka producer at %s", bootstrap_servers)
            return _PRODUCER_INSTANCE
        except Exception as e:
            if i == 39:
                from src.utils.metrics import SIM_ERRORS_TOTAL
                SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="kafka_producer_init").inc()
                logger.error("Final attempt (40) failed to connect to Kafka at %s: %s", bootstrap_servers, e)
                raise # Re-raise the exception on final failure
            logger.warning("Attempt %d/40: Kafka not ready at %s, retrying in 3s...", i+1, bootstrap_servers)
            time.sleep(3)
    
    return None

def flush_producer() -> None:
    """Wait for all messages in the Producer queue to be delivered."""
    global _PRODUCER_INSTANCE
    if _PRODUCER_INSTANCE:
        _PRODUCER_INSTANCE.flush(timeout=5.0)

def create_kafka_consumer(group_id: str = "sim_engine_recovery") -> Consumer | None:
    """Return a new Kafka Consumer configured for reading from the beginning."""
    if is_kafka_disabled():
        return None
        
    bootstrap_servers = get_kafka_url()
    try:
        conf = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            # We explicitly don't want to auto-commit during recovery until we successfully rehydrate
            'enable.auto.commit': False,
        }
        consumer = Consumer(conf)
        logger.info("Kafka Consumer initialized at %s", bootstrap_servers)
        return consumer
    except Exception as e:
        from src.utils.metrics import SIM_ERRORS_TOTAL
        SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="kafka_consumer_init").inc()
        logger.error("Failed to initialize Kafka Consumer: %s", e)
        return None

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/rabbitmq_client.py
import os
import pika
import logging

logger = logging.getLogger(__name__)

# Track a global connection for simple synchronous workers/clients 
# (e.g., the EngineManager loop or the ai_worker thread).
_connection: pika.BlockingConnection | None = None


def is_rabbitmq_disabled() -> bool:
    """Return True if RabbitMQ integration is explicitly disabled."""
    return os.environ.get("DISABLE_RABBITMQ", "0").lower() in ("1", "true", "yes")

def get_rabbitmq() -> pika.BlockingConnection | None:
    """Get or create a synchronous RabbitMQ connection with retry logic."""
    if is_rabbitmq_disabled():
        return None
        
    global _connection
    if _connection is None or _connection.is_closed:
        url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/")
        parameters = pika.URLParameters(url)
        # Increase the heartbeat timeout to prevent connection drops during long simulation ticks (e.g. 100% CPU lock under GIL)
        parameters.heartbeat = 600
        parameters.blocked_connection_timeout = 300
        
        import time
        for i in range(40): # Increased to 40 attempts (120s) for slow Docker bootstrap on Windows
            try:
                _connection = pika.BlockingConnection(parameters)
                logger.info("Successfully connected to RabbitMQ at %s", url)
                return _connection
            except Exception as e:
                if i == 39:
                    from src.utils.metrics import SIM_ERRORS_TOTAL
                    SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="rabbitmq_client").inc()
                    logger.error("Final attempt (40) failed to connect to RabbitMQ at %s: %s", url, e)
                    raise
                logger.warning("Attempt %d/40: RabbitMQ not ready at %s, retrying in 3s...", i+1, url)
                time.sleep(3)
    
    return _connection


def close_rabbitmq():
    """Close the global RabbitMQ connection if it exists."""
    global _connection
    if _connection and not _connection.is_closed:
        try:
            _connection.close()
        except Exception:
            pass
        _connection = None

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/redis_client.py
import os
import logging
from typing import Optional
import redis.asyncio as aioredis
import redis as syncredis

logger = logging.getLogger(__name__)

# Singletons for reusing connection pools
_async_redis_client: Optional[aioredis.Redis] = None
_sync_redis_client: Optional[syncredis.Redis] = None

def get_redis_url() -> str:
    """Get the Redis connection URL from the environment, defaulting to localhost."""
    return os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

def get_async_redis() -> aioredis.Redis:
    """Get or create the global async Redis client."""
    global _async_redis_client
    if _async_redis_client is None:
        url = get_redis_url()
        logger.info(f"Connecting to async Redis at {url}")
        _async_redis_client = aioredis.from_url(url, decode_responses=True)
    return _async_redis_client

def get_sync_redis() -> syncredis.Redis:
    """Get or create the global sync Redis client. 
    Useful for background threads that don't have an active asyncio loop.
    """
    global _sync_redis_client
    if _sync_redis_client is None:
        url = get_redis_url()
        logger.info(f"Connecting to sync Redis at {url}")
        _sync_redis_client = syncredis.from_url(url, decode_responses=True)
    return _sync_redis_client

async def close_redis_connections():
    """Gracefully close all connection pools during app shutdown."""
    global _async_redis_client, _sync_redis_client
    if _async_redis_client:
        await _async_redis_client.aclose()
        _async_redis_client = None
    if _sync_redis_client:
        _sync_redis_client.close()
        _sync_redis_client = None

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/routes/__init__.py
"""Versioned API route modules."""

from fastapi import APIRouter

from src.api.routes.control import router as control_router
from src.api.routes.map import router as map_router
from src.api.routes.state import router as state_router
from src.api.routes.config import router as config_router
from src.api.routes.metadata import router as metadata_router
from src.api.routes.stream import router as stream_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(map_router, tags=["Map"])
api_router.include_router(stream_router, prefix="/stream", tags=["Stream"])
api_router.include_router(state_router, tags=["State"])
api_router.include_router(control_router, tags=["Control"])
api_router.include_router(config_router, tags=["Config"])
api_router.include_router(metadata_router)

__all__ = ["api_router"]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/routes/config.py
"""GET /api/v1/config — expose simulation configuration."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import SimulationConfigResponse

router = APIRouter()


@router.get("/config", response_model=SimulationConfigResponse)
def get_config(
    manager: EngineManager = Depends(get_engine_manager),
) -> SimulationConfigResponse:
    cfg = manager._config
    return SimulationConfigResponse(
        world_seed=cfg.world_seed,
        grid_width=cfg.grid_width,
        grid_height=cfg.grid_height,
        max_ticks=cfg.max_ticks,
        num_workers=cfg.num_workers,
        initial_entity_count=cfg.initial_entity_count,
        generator_spawn_interval=cfg.generator_spawn_interval,
        generator_max_entities=cfg.generator_max_entities,
        vision_range=cfg.vision_range,
        flee_hp_threshold=cfg.flee_hp_threshold,
        tick_rate=manager.tick_rate,
    )

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/routes/control.py
"""POST /api/v1/control/{action} — simulation lifecycle controls."""

from __future__ import annotations

import logging
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import ControlResponse

router = APIRouter()
logger = logging.getLogger(__name__)


class ControlAction(str, Enum):
    start = "start"
    pause = "pause"
    resume = "resume"
    step = "step"
    reset = "reset"


@router.post("/control/{action}", response_model=ControlResponse)
def control(
    action: ControlAction,
    manager: EngineManager = Depends(get_engine_manager),
) -> ControlResponse:
    snapshot = manager.get_snapshot()
    tick = snapshot.tick if snapshot else 0

    match action:
        case ControlAction.start:
            if manager.running:
                return ControlResponse(status="noop", message="Already running.", tick=tick)
            manager.start()
            return ControlResponse(status="ok", message="Simulation started.", tick=tick)

        case ControlAction.pause:
            if not manager.running:
                return ControlResponse(status="error", message="Not running.", tick=tick)
            manager.pause()
            return ControlResponse(status="ok", message="Simulation paused.", tick=tick)

        case ControlAction.resume:
            if not manager.running:
                return ControlResponse(status="error", message="Not running.", tick=tick)
            manager.resume()
            return ControlResponse(status="ok", message="Simulation resumed.", tick=tick)

        case ControlAction.step:
            if not manager.running:
                manager.start()
                manager.pause()
            manager.step()
            return ControlResponse(status="ok", message="Single tick executed.", tick=tick)

        case ControlAction.reset:
            manager.reset()
            snapshot = manager.get_snapshot()
            new_tick = snapshot.tick if snapshot else 0
            return ControlResponse(status="ok", message="Simulation reset.", tick=new_tick)


@router.post("/speed")
def set_speed(
    tps: float = Query(20.0, gt=0.5, le=100.0, description="Ticks per second"),
    manager: EngineManager = Depends(get_engine_manager),
) -> ControlResponse:
    manager.tick_rate = 1.0 / tps
    snapshot = manager.get_snapshot()
    tick = snapshot.tick if snapshot else 0
    return ControlResponse(status="ok", message=f"Speed set to {tps:.1f} tps.", tick=tick)


@router.post("/debug/log")
async def debug_log(data: dict):
    """Explicitly emit a log message for E2E trace verification."""
    msg = data.get("message", "No message provided")
    logger.info("E2E-TRACE: %s", msg)
    return {"status": "ok", "emitted": msg}

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/routes/map.py
"""GET /api/v1/map — static grid data (fetch once)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import MapResponse

router = APIRouter()


@router.get("/map", response_model=MapResponse)
def get_map(manager: EngineManager = Depends(get_engine_manager)) -> MapResponse:
    grid = manager.get_grid()
    if grid is None:
        raise HTTPException(status_code=503, detail="Simulation not initialized yet.")

    # RLE encode: [value, count, value, count, ...]
    tiles = grid._tiles
    total = grid.width * grid.height
    rle: list[int] = []
    if total > 0:
        cur_val = int(tiles[0])
        cur_count = 1
        for i in range(1, total):
            v = int(tiles[i])
            if v == cur_val:
                cur_count += 1
            else:
                rle.append(cur_val)
                rle.append(cur_count)
                cur_val = v
                cur_count = 1
        rle.append(cur_val)
        rle.append(cur_count)

    return MapResponse(width=grid.width, height=grid.height, grid=rle)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/routes/metadata.py
"""Metadata endpoints — expose all game definitions so the frontend has zero hardcoded data.

Core models (ItemTemplate, SkillDef, ClassDef, BreakthroughDef, TraitDef) are pydantic
dataclasses defined in src/core/.  They are the single source of truth used by both the
game engine and the API.  This module adds only thin aggregate response wrappers and
the handful of definitions (enums, attributes, buildings) that live nowhere else.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from fastapi import APIRouter
from src.api.encoder import ENTITY_KEY_MAP, STATE_ENUM_MAP

from src.core.models.enums import (
    AIState, DamageType, Element, EnemyTier, EntityRole,
    ItemType, Material, Rarity,
)
from src.core.gameplay.faction import Faction, FactionRelation, FactionRegistry
from src.core.gameplay.items.item_registry import ITEM_REGISTRY, ItemTemplate
from src.core.gameplay.classes import (
    CLASS_DEFS, CLASS_SKILLS, BREAKTHROUGHS, SKILL_DEFS, RACE_SKILLS,
    SCALING_GRADES, SCALING_MULTIPLIER,
    HeroClass, SkillDef, ClassDef, BreakthroughDef,
    SkillTarget,
)
from src.core.entities.traits import TRAIT_DEFS, TraitDef
from src.core.gameplay.buildings import RECIPES
from src.core.world.resource_nodes import TERRAIN_RESOURCES

router = APIRouter(prefix="/metadata", tags=["Metadata"])


# ---------------------------------------------------------------------------
# Pydantic response schemas — only for data NOT already in core models
# ---------------------------------------------------------------------------

# -- /enums helpers --

class EnumEntry(BaseModel):
    id: int
    name: str
    description: str = ""


class MaterialEntry(BaseModel):
    id: int
    name: str
    walkable: bool


class FactionEntry(BaseModel):
    id: int
    name: str


class FactionRelationEntry(BaseModel):
    faction_a: int
    faction_b: int
    relation: str


class EntityKindEntry(BaseModel):
    kind: str
    faction: str


class EnumsResponse(BaseModel):
    materials: list[MaterialEntry]
    ai_states: list[EnumEntry]
    tiers: list[EnumEntry]
    rarities: list[EnumEntry]
    item_types: list[EnumEntry]
    damage_types: list[EnumEntry]
    elements: list[EnumEntry]
    entity_roles: list[EnumEntry]
    factions: list[FactionEntry]
    faction_relations: list[FactionRelationEntry]
    entity_kinds: list[EntityKindEntry]


# -- /classes helpers (thin wrappers for grouped attribute view) --

class AttrBonuses(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    str_: int = Field(0, alias="str")
    agi: int = 0
    vit: int = 0
    int_: int = Field(0, alias="int")
    spi: int = 0
    wis: int = 0
    end: int = 0
    per: int = 0
    cha: int = 0


class AttrScaling(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    str_: str = Field("E", alias="str")
    agi: str = "E"
    vit: str = "E"
    int_: str = Field("E", alias="int")
    spi: str = "E"
    wis: str = "E"
    end: str = "E"
    per: str = "E"
    cha: str = "E"


class BreakthroughView(BaseModel):
    """Thin view that restructures flat BreakthroughDef fields for the frontend."""
    from_class: str
    to_class: str
    level_req: int
    attr_req: str
    attr_threshold: int
    talent: str
    bonuses: AttrBonuses
    cap_bonuses: AttrBonuses


class ClassView(BaseModel):
    """Thin view that restructures flat ClassDef fields for the frontend."""
    id: str
    name: str
    description: str
    tier: int = 1
    role: str = ""
    lore: str = ""
    playstyle: str = ""
    attr_bonuses: AttrBonuses
    cap_bonuses: AttrBonuses
    scaling: AttrScaling
    skill_ids: list[str] = []
    breakthrough: BreakthroughView | None = None


class ScalingGradeEntry(BaseModel):
    grade: str
    multiplier: float


class MasteryTierEntry(BaseModel):
    name: str
    min_mastery: float
    power_bonus: str
    stamina_reduction: str
    cooldown_reduction: str


class ClassesResponse(BaseModel):
    classes: list[ClassView]
    skills: list[dict]           # Serialized SkillDef (core model)
    race_skills: dict[str, list[str]]
    scaling_grades: list[ScalingGradeEntry]
    mastery_tiers: list[MasteryTierEntry]
    skill_targets: list[EnumEntry]


# -- /attributes & /buildings (no core model exists for these) --

class AttributeDefEntry(BaseModel):
    key: str
    label: str
    description: str


class AttributesResponse(BaseModel):
    attributes: list[AttributeDefEntry]


class BuildingTypeEntry(BaseModel):
    building_type: str
    name: str
    description: str


class BuildingsResponse(BaseModel):
    building_types: list[BuildingTypeEntry]


# -- /resources --

class ResourceTypeEntry(BaseModel):
    resource_type: str
    name: str
    terrain: str
    yields_item: str
    max_harvests: int
    respawn_cooldown: int
    harvest_ticks: int


class ResourcesResponse(BaseModel):
    resource_types: list[ResourceTypeEntry]


# -- /recipes --

class RecipeEntry(BaseModel):
    recipe_id: str
    output_item: str
    output_name: str
    gold_cost: int
    materials: dict[str, int]


class RecipesResponse(BaseModel):
    recipes: list[RecipeEntry]


# ---------------------------------------------------------------------------
# TypeAdapters for core models — serialize pydantic dataclasses to dicts
# ---------------------------------------------------------------------------

_item_ta = TypeAdapter(ItemTemplate)
_skill_ta = TypeAdapter(SkillDef)
_classdef_ta = TypeAdapter(ClassDef)
_breakthroughdef_ta = TypeAdapter(BreakthroughDef)
_traitdef_ta = TypeAdapter(TraitDef)


# ---------------------------------------------------------------------------
# Helper data (enums, attribute defs, building defs — no core model for these)
# ---------------------------------------------------------------------------

_NON_WALKABLE = {Material.WALL, Material.WATER, Material.LAVA}

_AI_STATE_DESCRIPTIONS: dict[str, str] = {
    "IDLE": "Idle — waiting for the AI evaluator to pick a new goal.",
    "WANDER": "Exploring and moving toward unexplored tiles to map the world.",
    "HUNT": "Seeking and chasing enemies to engage in combat.",
    "COMBAT": "Engaged in melee combat with an adjacent enemy.",
    "FLEE": "Retreating from danger toward safety.",
    "RETURN_TO_TOWN": "Navigating back to town for rest and resupply.",
    "RESTING_IN_TOWN": "Healing at town. Will visit buildings when fully healed.",
    "RETURN_TO_CAMP": "Enemy returning to its home camp.",
    "GUARD_CAMP": "Patrolling camp territory and watching for intruders.",
    "LOOTING": "Picking up items from the ground.",
    "ALERT": "Responding to a territory intrusion — seeking the intruder.",
    "VISIT_SHOP": "At the General Store — buying or selling items.",
    "VISIT_BLACKSMITH": "At the Blacksmith — learning recipes or crafting equipment.",
    "VISIT_GUILD": "At the Adventurer's Guild — gathering intel and accepting quests.",
    "HARVESTING": "Channeling a harvest action on a nearby resource node.",
    "VISIT_CLASS_HALL": "At the Class Hall — learning skills or attempting a class breakthrough.",
    "VISIT_INN": "Resting at the Inn for rapid HP and stamina recovery.",
    "VISIT_HOME": "At home — storing items or upgrading home storage.",
}

_ATTR_DEFS = [
    ("str", "STR", "Physical ATK scaling (+2%/pt), carry weight."),
    ("agi", "AGI", "SPD +0.4/pt, Crit +0.4%/pt, Evasion +0.3%/pt."),
    ("vit", "VIT", "Max HP +2/pt, physical DEF +0.3/pt."),
    ("int", "INT", "XP gain +1%/pt, MATK +0.2/pt, cooldown reduction."),
    ("spi", "SPI", "MATK +0.6/pt, MDEF +0.15/pt — primary magic offense."),
    ("wis", "WIS", "MDEF +0.4/pt, Luck +0.3/pt, XP gain +0.5%/pt."),
    ("end", "END", "Max stamina +2/pt, Max HP +0.5/pt, HP regen."),
    ("per", "PER", "Vision range +0.3/pt, loot quality, detection."),
    ("cha", "CHA", "Trade prices +1%/pt, interaction speed, social influence."),
]

_BUILDING_TYPES = [
    ("store", "General Store", "Buy and sell items. Heroes sell loot and purchase potions, equipment, and crafting materials."),
    ("blacksmith", "Blacksmith", "Learn recipes and craft equipment. Heroes bring materials and gold to forge upgrades."),
    ("guild", "Adventurer's Guild", "Gather intel on camps and resources. Accept quests and receive material hints."),
    ("class_hall", "Class Hall", "Learn class skills and attempt breakthroughs. The hall of heroes."),
    ("inn", "Traveler's Inn", "Rapid HP and stamina recovery. A safe haven within town walls."),
    ("hero_house", "Hero's House", "Personal dwelling. Store and retrieve items safely between adventures."),
]

_MATERIAL_NAMES = {
    Material.FLOOR: "Floor",
    Material.WALL: "Wall",
    Material.WATER: "Water",
    Material.TOWN: "Town",
    Material.CAMP: "Camp",
    Material.SANCTUARY: "Sanctuary",
    Material.FOREST: "Forest",
    Material.DESERT: "Desert",
    Material.SWAMP: "Swamp",
    Material.MOUNTAIN: "Mountain",
    Material.ROAD: "Road",
    Material.BRIDGE: "Bridge",
    Material.RUINS: "Ruins",
    Material.DUNGEON_ENTRANCE: "Dungeon Entrance",
    Material.LAVA: "Lava",
}

_SKILL_TARGET_NAMES = {
    SkillTarget.SELF: "self",
    SkillTarget.SINGLE_ENEMY: "single_enemy",
    SkillTarget.AREA_ENEMIES: "area_enemies",
    SkillTarget.SINGLE_ALLY: "single_ally",
    SkillTarget.AREA_ALLIES: "area_allies",
}


# ---------------------------------------------------------------------------
# Class view helpers — restructure flat ClassDef/BreakthroughDef into grouped views
# ---------------------------------------------------------------------------

def _attr_bonuses(obj) -> AttrBonuses:
    return AttrBonuses(**{
        "str": obj.str_bonus, "agi": obj.agi_bonus, "vit": obj.vit_bonus,
        "int": obj.int_bonus, "spi": obj.spi_bonus, "wis": obj.wis_bonus,
        "end": obj.end_bonus, "per": obj.per_bonus, "cha": obj.cha_bonus,
    })


def _cap_bonuses(obj) -> AttrBonuses:
    return AttrBonuses(**{
        "str": obj.str_cap_bonus, "agi": obj.agi_cap_bonus, "vit": obj.vit_cap_bonus,
        "int": obj.int_cap_bonus, "spi": obj.spi_cap_bonus, "wis": obj.wis_cap_bonus,
        "end": obj.end_cap_bonus, "per": obj.per_cap_bonus, "cha": obj.cha_cap_bonus,
    })


def _scaling(cd: ClassDef) -> AttrScaling:
    return AttrScaling(**{
        "str": cd.str_scaling, "agi": cd.agi_scaling, "vit": cd.vit_scaling,
        "int": cd.int_scaling, "spi": cd.spi_scaling, "wis": cd.wis_scaling,
        "end": cd.end_scaling, "per": cd.per_scaling, "cha": cd.cha_scaling,
    })


def _class_key(hc: HeroClass) -> str:
    return hc.name.lower()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/enums", response_model=EnumsResponse)
def get_enums() -> EnumsResponse:
    """All enum-like definitions: materials, AI states, tiers, rarities, factions, entity kinds."""

    materials = [
        MaterialEntry(
            id=m.value,
            name=_MATERIAL_NAMES.get(m, m.name.replace("_", " ").title()),
            walkable=m not in _NON_WALKABLE,
        )
        for m in Material
    ]

    ai_states = [
        EnumEntry(id=s.value, name=s.name, description=_AI_STATE_DESCRIPTIONS.get(s.name, ""))
        for s in AIState
    ]

    tiers = [EnumEntry(id=t.value, name=t.name.title()) for t in EnemyTier]
    rarities = [EnumEntry(id=r.value, name=r.name.lower()) for r in Rarity]
    item_types = [EnumEntry(id=it.value, name=it.name.lower()) for it in ItemType]
    damage_types = [EnumEntry(id=dt.value, name=dt.name.lower()) for dt in DamageType]
    elements = [EnumEntry(id=e.value, name=e.name.lower()) for e in Element]
    entity_roles = [EnumEntry(id=er.value, name=er.name.lower()) for er in EntityRole]
    factions = [FactionEntry(id=f.value, name=f.name.replace("_", " ").title()) for f in Faction]

    reg = FactionRegistry.default()
    faction_relations: list[FactionRelationEntry] = []
    for fa in Faction:
        for fb in Faction:
            if fa.value < fb.value:
                rel = reg.relation(fa, fb)
                faction_relations.append(FactionRelationEntry(
                    faction_a=fa.value, faction_b=fb.value,
                    relation=FactionRelation(rel).name.lower(),
                ))

    entity_kinds: list[EntityKindEntry] = []
    for kind_str, faction_val in reg._kind_map.items():
        entity_kinds.append(EntityKindEntry(
            kind=kind_str,
            faction=Faction(faction_val).name.replace("_", " ").title(),
        ))

    return EnumsResponse(
        materials=materials, ai_states=ai_states, tiers=tiers, rarities=rarities,
        item_types=item_types, damage_types=damage_types, elements=elements,
        entity_roles=entity_roles, factions=factions,
        faction_relations=faction_relations, entity_kinds=entity_kinds,
    )


@router.get("/items")
def get_items() -> dict:
    """Full item registry — returns core ItemTemplate models directly."""
    items = [_item_ta.dump_python(t, mode="json") for t in ITEM_REGISTRY.values()]
    return {"items": items}


@router.get("/classes", response_model=ClassesResponse)
def get_classes() -> ClassesResponse:
    """Class definitions, skills, breakthroughs, scaling grades, and mastery tiers."""

    classes: list[ClassView] = []
    for hc, cd in CLASS_DEFS.items():
        bt_view: BreakthroughView | None = None
        bt = BREAKTHROUGHS.get(hc)
        if bt:
            bt_view = BreakthroughView(
                from_class=_class_key(bt.from_class),
                to_class=_class_key(bt.to_class),
                level_req=bt.level_req,
                attr_req=bt.attr_req,
                attr_threshold=bt.attr_threshold,
                talent=bt.talent,
                bonuses=_attr_bonuses(bt),
                cap_bonuses=_cap_bonuses(bt),
            )

        classes.append(ClassView(
            id=_class_key(hc),
            name=cd.name,
            description=cd.description,
            tier=cd.tier,
            role=cd.role,
            lore=cd.lore,
            playstyle=cd.playstyle,
            attr_bonuses=_attr_bonuses(cd),
            cap_bonuses=_cap_bonuses(cd),
            scaling=_scaling(cd),
            skill_ids=CLASS_SKILLS.get(hc, []),
            breakthrough=bt_view,
        ))

    # Serialize core SkillDef models directly
    skills = [_skill_ta.dump_python(sdef, mode="json") for sdef in SKILL_DEFS.values()]

    scaling_grades = [
        ScalingGradeEntry(grade=g, multiplier=SCALING_MULTIPLIER[g])
        for g in SCALING_GRADES
    ]

    mastery_tiers = [
        MasteryTierEntry(name="Novice",      min_mastery=0,   power_bonus="—",    stamina_reduction="—",    cooldown_reduction="—"),
        MasteryTierEntry(name="Apprentice",   min_mastery=25,  power_bonus="—",    stamina_reduction="−10%", cooldown_reduction="—"),
        MasteryTierEntry(name="Adept",        min_mastery=50,  power_bonus="+20%", stamina_reduction="−10%", cooldown_reduction="—"),
        MasteryTierEntry(name="Expert",       min_mastery=75,  power_bonus="+20%", stamina_reduction="−20%", cooldown_reduction="−1 tick"),
        MasteryTierEntry(name="Master",       min_mastery=100, power_bonus="+35%", stamina_reduction="−25%", cooldown_reduction="−1 tick"),
    ]

    skill_targets = [
        EnumEntry(id=st.value, name=_SKILL_TARGET_NAMES.get(st, st.name.lower()))
        for st in SkillTarget
    ]

    return ClassesResponse(
        classes=classes, skills=skills, race_skills=RACE_SKILLS,
        scaling_grades=scaling_grades, mastery_tiers=mastery_tiers,
        skill_targets=skill_targets,
    )


@router.get("/traits")
def get_traits() -> dict:
    """All personality trait definitions — returns core TraitDef models directly."""
    traits = [_traitdef_ta.dump_python(tdef, mode="json") for tdef in TRAIT_DEFS.values()]
    return {"traits": traits}


@router.get("/attributes", response_model=AttributesResponse)
def get_attributes() -> AttributesResponse:
    """The 9 primary attribute definitions with effect descriptions."""
    return AttributesResponse(
        attributes=[AttributeDefEntry(key=k, label=l, description=d) for k, l, d in _ATTR_DEFS]
    )


@router.get("/buildings", response_model=BuildingsResponse)
def get_buildings() -> BuildingsResponse:
    """All building type definitions."""
    return BuildingsResponse(
        building_types=[BuildingTypeEntry(building_type=bt, name=n, description=d) for bt, n, d in _BUILDING_TYPES]
    )


@router.get("/resources", response_model=ResourcesResponse)
def get_resources() -> ResourcesResponse:
    """All resource node type definitions."""
    entries: list[ResourceTypeEntry] = []
    for terrain_mat, res_list in TERRAIN_RESOURCES.items():
        terrain_name = _MATERIAL_NAMES.get(Material(terrain_mat), str(terrain_mat))
        for res_type, res_name, yields, max_h, respawn, h_ticks in res_list:
            entries.append(ResourceTypeEntry(
                resource_type=res_type, name=res_name, terrain=terrain_name,
                yields_item=yields, max_harvests=max_h,
                respawn_cooldown=respawn, harvest_ticks=h_ticks,
            ))
    return ResourcesResponse(resource_types=entries)


@router.get("/recipes", response_model=RecipesResponse)
def get_recipes() -> RecipesResponse:
    """All crafting recipe definitions."""
    entries: list[RecipeEntry] = []
    for recipe in RECIPES:
        item = ITEM_REGISTRY.get(recipe.output_item)
        entries.append(RecipeEntry(
            recipe_id=recipe.recipe_id,
            output_item=recipe.output_item,
            output_name=item.name if item else recipe.output_item,
            gold_cost=recipe.gold_cost,
            materials=dict(recipe.materials),
        ))
    return RecipesResponse(recipes=entries)


@router.get("/protocol")
def get_protocol_metadata() -> dict:
    """Metadata for the High-Performance Binary WebSocket Protocol (BWS)."""
    return {
        "entity_key_map": ENTITY_KEY_MAP,
        "state_enum_map": STATE_ENUM_MAP
    }

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/routes/state.py
"""GET /api/v1/state — dynamic entity & event data (polled by UI)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import (
    AttributeCapSchema,
    AttributeSchema,
    BuildingSchema,
    BuildingStateSchema,
    EffectSchema,
    EntitySchema,
    EntitySlimSchema,
    EventSchema,
    GroundItemSchema,
    LocationSchema,
    QuestSchema,
    RegionSchema,
    ResourceNodeSchema,
    ResourceNodeStateSchema,
    SimulationStats,
    SkillSchema,
    StaticDataResponse,
    TreasureChestSchema,
    TreasureChestStateSchema,
    WorldStateResponse,
)

router = APIRouter()



# --- Standardized serialization logic moved to src.core.models.Entity (epic-05) ---




@router.get("/state", response_model=WorldStateResponse)
def get_state(
    since_tick: int = Query(0, ge=0, description="Only return events since this tick"),
    selected: int = Query(-1, description="Entity ID to get full details for (-1 = none)"),
    manager: EngineManager = Depends(get_engine_manager),
) -> WorldStateResponse:
    snapshot = manager.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="No snapshot available yet.")

    loot_dur = manager.config.loot_duration
    slim_entities: list[EntitySlimSchema] = []
    selected_entity: EntitySchema | None = None

    for e in snapshot.entities.values():
        if not e.combat.alive:
            continue
        
        # Standardized serialization (epic-05 api refactor)
        slim_entities.append(e.to_slim_schema(loot_duration=loot_dur))
        
        if e.id == selected:
            selected_entity = e.to_full_schema(loot_duration=loot_dur)

    events = [
        EventSchema(tick=ev.tick, category=ev.category, message=ev.message,
                    entity_ids=list(ev.entity_ids), metadata=ev.metadata)
        for ev in manager.event_log.since_tick(since_tick)
    ]

    ground_items = [
        GroundItemSchema(x=x, y=y, items=list(items))
        for (x, y), items in snapshot.ground_items.items()
        if items
    ]

    # Dynamic world objects (Audit Point 3)
    res_nodes: list[ResourceNodeStateSchema] = [
        ResourceNodeStateSchema(node_id=n.node_id, remaining=n.remaining, is_available=n.is_available)
        for n in snapshot.resource_nodes
    ]
    chests: list[TreasureChestStateSchema] = []
    if hasattr(snapshot, 'treasure_chests'):
        chests = [
            TreasureChestStateSchema(chest_id=c.chest_id, looted=c.looted, guard_entity_id=c.guard_entity_id)
            for c in snapshot.treasure_chests
        ]
    
    building_states: list[BuildingStateSchema] = []
    for b in snapshot.buildings:
        if b.building_type == "hero_house":
            try:
                owner_id = int(b.building_id.split("_")[-1])
                owner = snapshot.entities.get(owner_id)
                if owner and owner.inventory_aspect.home_storage:
                    hs = owner.inventory_aspect.home_storage
                    building_states.append(BuildingStateSchema(
                        building_id=b.building_id,
                        storage_items=list(hs.items),
                        storage_used=hs.used_slots,
                        storage_max=hs.max_slots,
                        storage_level=hs.level,
                    ))
            except (ValueError, IndexError):
                pass

    return WorldStateResponse(
        tick=snapshot.tick,
        alive_count=len(slim_entities),
        entities=slim_entities,
        selected_entity=selected_entity,
        events=events,
        ground_items=ground_items,
        resource_nodes=res_nodes,
        treasure_chests=chests,
        buildings=building_states,
        war_status={str(f_id): status for f_id, status in snapshot.war_status.items()},
        faction_aggression={str(f_id): agg for f_id, agg in snapshot.faction_aggression.items()},
    )

@router.get("/static", response_model=StaticDataResponse)
def get_static(
    manager: EngineManager = Depends(get_engine_manager),
) -> StaticDataResponse:
    """Static world data — buildings, resource nodes, regions, chests. Fetch once."""
    snapshot = manager.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="No snapshot available yet.")

    buildings = [
        BuildingSchema(
            building_id=b.building_id, name=b.name,
            x=b.pos.x, y=b.pos.y, building_type=b.building_type,
            owner_entity_id=int(b.building_id.split("_")[-1]) if b.building_type == "hero_house" else None
        )
        for b in snapshot.buildings
    ]

    resource_nodes = [
        ResourceNodeSchema(
            node_id=n.node_id, resource_type=n.resource_type, name=n.name,
            x=n.pos.x, y=n.pos.y, terrain=int(n.terrain),
            yields_item=n.yields_item,
            max_harvests=n.max_harvests,
            respawn_cooldown=n.respawn_cooldown,
            harvest_ticks=n.harvest_ticks,
        )
        for n in snapshot.resource_nodes
    ]

    treasure_chests = []
    if hasattr(snapshot, 'treasure_chests'):
        treasure_chests = [
            TreasureChestSchema(
                chest_id=c.chest_id, x=c.pos.x, y=c.pos.y,
                tier=c.tier,
            )
            for c in snapshot.treasure_chests
        ]

    regions = []
    if hasattr(snapshot, 'regions'):
        regions = [
            RegionSchema(
                region_id=r.region_id, name=r.name, terrain=int(r.terrain),
                center_x=r.center.x, center_y=r.center.y, radius=r.radius,
                difficulty=r.difficulty,
                owner_faction=r.owner_faction.name.lower() if r.owner_faction else None,
                influence=snapshot.region_control.get(r.region_id, 0.0),
                locations=[
                    LocationSchema(
                        location_id=loc.location_id, name=loc.name,
                        location_type=loc.location_type, x=loc.pos.x, y=loc.pos.y,
                        region_id=loc.region_id
                    ) for loc in r.locations
                ]
            )
            for r in snapshot.regions
        ]

    return StaticDataResponse(
        buildings=buildings,
        resource_nodes=resource_nodes,
        treasure_chests=treasure_chests,
        regions=regions,
    )
@router.post("/clear_events")
def clear_events(
    manager: EngineManager = Depends(get_engine_manager),
) -> dict:
    """Clear all stored events."""
    manager.event_log.clear()
    return {"status": "ok"}


@router.get("/stats", response_model=SimulationStats)
def get_stats(
    manager: EngineManager = Depends(get_engine_manager),
) -> SimulationStats:
    snapshot = manager.get_snapshot()
    tick = snapshot.tick if snapshot else 0
    alive = sum(1 for e in snapshot.entities.values() if e.combat.alive) if snapshot else 0

    return SimulationStats(
        tick=tick,
        world_day=tick // 100,
        alive_count=alive,
        total_spawned=manager.total_spawned,
        total_deaths=manager.total_deaths,
        running=manager.running,
        paused=manager.paused,
    )

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/routes/stream.py
"""GET /api/v1/stream — Server-Sent Events (SSE) state streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import EntitySlimSchema, EventSchema
from src.core.models.snapshot import Snapshot
from src.utils.event_log import SimEvent

router = APIRouter()
logger = logging.getLogger(__name__)


def _snapshot_to_slim_dict(snapshot: Snapshot, loot_duration: int) -> dict[int, EntitySlimSchema]:
    """Convert snapshot entities to a dict of fast serializable SlimSchemas."""
    res = {}
    for eid, e in snapshot.entities.items():
        if not e.combat.alive:
            continue
        res[eid] = e.to_slim_schema(loot_duration=loot_duration)
    return res


def compute_delta(
    old_slim: dict[int, EntitySlimSchema],
    new_slim: dict[int, EntitySlimSchema],
    tick: int,
    events: list[SimEvent],
) -> str | None:
    """Compute diff between two snapshots. Returns JSON string of delta, or None if empty."""
    changed = []
    removed = []

    # Find changed & new
    for eid, e in new_slim.items():
        old_e = old_slim.get(eid)
        if old_e is None or old_e != e:
            changed.append(e.model_dump())

    # Find removed (died)
    for eid in old_slim:
        if eid not in new_slim:
            removed.append(eid)

    # Convert events
    serialized_events = [
        EventSchema(tick=ev.tick, category=ev.category, message=ev.message,
                    entity_ids=list(ev.entity_ids), metadata=ev.metadata).model_dump()
        for ev in events
    ]

    # Don't send empty updates to save bandwidth (unless tick is divisible by 20 to heartbeat)
    if not changed and not removed and not serialized_events and tick % 20 != 0:
        return None

    delta = {
        "tick": tick,
        "changed": changed,
        "removed": removed,
        "events": serialized_events,
    }
    
    # We output strict JSON to encode properly in Server-Sent Events
    return json.dumps(delta)


async def _stream_generator(request: Request, manager: EngineManager) -> AsyncGenerator[dict, None]:
    """Yields SSE events from the Redis stream."""
    import time
    from src.api.redis_client import get_async_redis

    # Start by capturing the initial state and dropping a full dump
    initial_snap = manager.get_snapshot()
    if not initial_snap:
        yield {"data": json.dumps({"error": "Engine not ready"})}
        return
        
    loot_duration = manager.config.loot_duration
    prev_slim = _snapshot_to_slim_dict(initial_snap, loot_duration)

    # We send the very first full snapshot so the frontend can populate its maps initially
    initial_delta = {
        "tick": initial_snap.tick,
        "changed": [e.model_dump() for e in prev_slim.values()],
        "removed": [],
        "events": [],
    }
    yield {"data": json.dumps(initial_delta)}

    r = get_async_redis()
    # We want to start reading from the exact moment we grabbed the snapshot.
    # "$" means "only messages appended to the stream from now on"
    last_id = "$"

    while True:
        if await request.is_disconnected():
            break

        try:
            # Block and wait for a single new tick to hit the stream
            # The structure returned by xread is:
            # [[stream_name, [(msg_id, {field: value}), ...]], ...]
            response = await r.xread({"sim:stream": last_id}, count=1, block=1000)
            
            if response:
                stream_name, messages = response[0]
                msg_id, msg_data = messages[0]
                
                # Advance the pointer
                last_id = msg_id
                
                # Extract the pre-computed JSON delta from EngineManager
                payload_json = msg_data.get("payload")
                
                if payload_json:
                    yield {"data": payload_json}
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            await asyncio.sleep(1)


@router.get("", response_class=EventSourceResponse)
async def stream_state(
    request: Request,
    manager: EngineManager = Depends(get_engine_manager)
) -> EventSourceResponse:
    """Connect to a Server-Sent Events stream for realtime entity deltas."""
    if manager.get_snapshot() is None:
        raise HTTPException(status_code=503, detail="No snapshot available yet.")
        
    return EventSourceResponse(_stream_generator(request, manager))

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/routes/stream_ws.py
"""WebSocket streaming — High-performance binary state synchronization."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.encoder import WorldStateEncoder
from src.api.redis_client import get_async_redis
from src.core.models.snapshot import Snapshot
from src.utils.event_log import SimEvent

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def stream_ws(
    websocket: WebSocket,
    manager: EngineManager = Depends(get_engine_manager)
):
    """
    WebSocket endpoint for real-time world state.
    Supports JSON and MessagePack (BWS protocol).
    """
    await websocket.accept()
    
    # 1. Protocol Negotiation (Handshake)
    try:
        # Expected: {"type": "handshake", "format": "json" | "msgpack"}
        handshake = await websocket.receive_json()
        if handshake.get("type") != "handshake":
            await websocket.close(code=1003, reason="Missing handshake")
            return
            
        fmt = handshake.get("format", "json")
        mode = "compact" if fmt == "msgpack" else "rich"
        logger.info(f"WebSocket client connected (format={fmt}, mode={mode})")
        
    except Exception as e:
        logger.error(f"WebSocket handshake failed: {e}")
        await websocket.close(code=1003)
        return

    # 2. Redis Subscription Loop
    r = get_async_redis()
    # "$" means "only messages started after this moment"
    # However, for a fresh connection, we might want the CURRENT state first.
    last_id = "$"
    
    # Send initial full state (Rich/Compact based on mode)
    initial_snap = manager.get_snapshot()
    if initial_snap:
        # We don't have events for the initial dump, or we could fetch them.
        # For simplicity, just send the entities.
        initial_payload = WorldStateEncoder.encode_tick(initial_snap, [], mode=mode)
        serialized = WorldStateEncoder.serialize(initial_payload, format=fmt)
        if fmt == "msgpack":
            await websocket.send_bytes(serialized)
        else:
            await websocket.send_text(serialized)

    try:
        while True:
            # Block wait for new tick in Redis
            response = await r.xread({"sim:stream": last_id}, count=1, block=1000)
            
            if response:
                stream_name, messages = response[0]
                msg_id, msg_data = messages[0]
                last_id = msg_id
                
                # We could use the payload_json pre-computed in EngineManager,
                # but if the client wants MSGPack or Compact mode, we re-encode here.
                # In a high-scale production env, we'd pre-publish both to Redis.
                
                # For now, we rebuild from the latest snapshot in EngineManager
                # because the Redis payload is just a JSON string of a delta.
                snap = manager.get_snapshot()
                if snap and snap.tick > initial_snap.tick:
                    # We need the events for this tick too.
                    # EngineManager.event_log contains recent events.
                    events = manager.event_log.since_tick(snap.tick)
                    
                    payload = WorldStateEncoder.encode_tick(snap, events, mode=mode)
                    serialized = WorldStateEncoder.serialize(payload, format=fmt)
                    
                    if fmt == "msgpack":
                        await websocket.send_bytes(serialized)
                    else:
                        await websocket.send_text(serialized)
                        
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket stream error: {e}")
        await websocket.close(code=1011)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/api/schemas.py
"""Pydantic response models for the REST API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Entity ---

class AttributeSchema(BaseModel):
    str_: int = Field(5, alias="str")
    agi: int = 5
    vit: int = 5
    int_: int = Field(5, alias="int")
    spi: int = 5
    wis: int = 5
    end: int = 5
    per: int = 5
    cha: int = 5
    # Training progression (0.0 to 1.0 fractional toward next point)
    str_frac: float = 0.0
    agi_frac: float = 0.0
    vit_frac: float = 0.0
    int_frac: float = 0.0
    spi_frac: float = 0.0
    wis_frac: float = 0.0
    end_frac: float = 0.0
    per_frac: float = 0.0
    cha_frac: float = 0.0

    model_config = {
        "populate_by_name": True
    }


class AttributeCapSchema(BaseModel):
    str_cap: int = 15
    agi_cap: int = 15
    vit_cap: int = 15
    int_cap: int = 15
    spi_cap: int = 15
    wis_cap: int = 15
    end_cap: int = 15
    per_cap: int = 15
    cha_cap: int = 15


class SkillSchema(BaseModel):
    skill_id: str
    name: str = ""
    cooldown_remaining: int = 0
    mastery: float = 0.0
    times_used: int = 0
    skill_type: str = "active"
    target: str = "self"
    stamina_cost: int = 0
    cooldown: int = 0
    power: float = 1.0
    description: str = ""
    damage_type: str = "physical"   # "physical" | "magical"
    element: str = "none"           # "none" | "fire" | "ice" | "lightning" | "dark" | "holy"


class EffectSchema(BaseModel):
    effect_type: str
    source: str = ""
    remaining_ticks: int = 0
    atk_mult: float = 1.0
    def_mult: float = 1.0
    spd_mult: float = 1.0
    crit_mult: float = 1.0
    evasion_mult: float = 1.0
    hp_per_tick: int = 0


class QuestSchema(BaseModel):
    quest_id: str
    quest_type: str
    title: str
    description: str = ""
    target_kind: str = ""
    target_x: int | None = None
    target_y: int | None = None
    target_count: int = 1
    progress: int = 0
    completed: bool = False
    gold_reward: int = 0
    xp_reward: int = 0


class EntitySlimSchema(BaseModel):
    """Minimal entity data for rendering (non-selected entities)."""
    id: int
    kind: str
    display_name: str = ""
    x: int
    y: int
    hp: int
    max_hp: int
    state: str
    level: int = 1
    tier: int = 0
    faction: str = "hero_guild"
    weapon_range: int = 1
    combat_target_id: int | None = None
    loot_progress: int = 0
    loot_duration: int = 3

    model_config = {
        "frozen": True
    }


class EntitySchema(BaseModel):
    id: int
    kind: str
    display_name: str = ""
    x: int
    y: int
    hp: int
    max_hp: int
    atk: int
    def_: int = Field(0, alias="def")
    spd: int
    luck: int = 0
    crit_rate: float = 0.05
    evasion: float = 0.0
    matk: int = 0
    mdef: int = 0
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    gold: int = 0
    tier: int = 0
    faction: str = "hero_guild"
    state: str
    weapon: str | None = None
    armor: str | None = None
    accessory: str | None = None
    inventory_count: int = 0
    inventory_max_slots: int = 0
    inventory_items: list[str] = Field(default_factory=list)
    inventory_weight: float = 0.0
    inventory_max_weight: float = 0.0
    vision_range: int = 6
    terrain_memory: dict[str, int] = Field(default_factory=dict)
    entity_memory: list[dict] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    loot_progress: int = 0
    loot_duration: int = 3
    known_recipes: list[str] = Field(default_factory=list)
    craft_target: str | None = None
    # RPG attributes
    stamina: int = 50
    max_stamina: int = 50
    attributes: AttributeSchema | None = None
    attribute_caps: AttributeCapSchema | None = None
    # Class & skills
    hero_class: str = "none"
    skills: list[SkillSchema] = Field(default_factory=list)
    class_mastery: float = 0.0
    active_effects: list[EffectSchema] = Field(default_factory=list)
    quests: list[QuestSchema] = Field(default_factory=list)
    traits: list[int] = Field(default_factory=list)
    # Base stats (before equipment/effects) for detailed breakdown
    base_atk: int = 0
    base_def: int = 0
    base_spd: int = 0
    base_matk: int = 0
    base_mdef: int = 0
    base_crit_rate: float = 0.05
    base_evasion: float = 0.0
    # Secondary / non-combat derived stats
    hp_regen: float = 1.0
    cooldown_reduction: float = 1.0
    loot_bonus: float = 1.0
    trade_bonus: float = 1.0
    interaction_speed: float = 1.0
    rest_efficiency: float = 1.0
    # Speed delay stats (computed from SPD + action type)
    speed_delay_move: float = 1.0
    speed_delay_attack: float = 0.9
    speed_delay_skill: float = 1.2
    speed_delay_harvest: float = 0.7
    # Elemental damage multipliers (from traits)
    fire_dmg_mult: float = 1.0
    ice_dmg_mult: float = 1.0
    lightning_dmg_mult: float = 1.0
    dark_dmg_mult: float = 1.0
    # Elemental vulnerability (from stats)
    elem_vuln_fire: float = 1.0
    elem_vuln_ice: float = 1.0
    elem_vuln_lightning: float = 1.0
    elem_vuln_dark: float = 1.0
    # Region (epic-15)
    region_id: str = ""
    difficulty_tier: int = 1
    current_region_id: str = ""
    # Combat visualization (epic-05)
    weapon_range: int = 1
    combat_target_id: int | None = None
    # Home storage
    home_storage_used: int = 0
    home_storage_max: int = 0
    home_storage_level: int = 0

    model_config = {
        "frozen": True,
        "populate_by_name": True
    }


# --- Map ---

class MapResponse(BaseModel):
    width: int
    height: int
    grid: list[int] = Field(description="RLE-encoded flat grid: [value, count, value, count, ...]")


# --- World State ---

class EventSchema(BaseModel):
    tick: int
    category: str
    message: str
    entity_ids: list[int] = Field(default_factory=list)
    metadata: dict | None = None


class GroundItemSchema(BaseModel):
    x: int
    y: int
    items: list[str]


class BuildingSchema(BaseModel):
    building_id: str
    name: str
    x: int
    y: int
    building_type: str
    owner_entity_id: int | None = None


class BuildingStateSchema(BaseModel):
    building_id: str
    storage_items: list[str] = Field(default_factory=list)
    storage_used: int = 0
    storage_max: int = 0
    storage_level: int = 0


class RecipeSchema(BaseModel):
    recipe_id: str
    output_item: str
    output_name: str
    gold_cost: int
    materials: dict[str, int]
    description: str = ""


class ShopItemSchema(BaseModel):
    item_id: str
    buy_price: int


class ResourceNodeSchema(BaseModel):
    node_id: int
    resource_type: str
    name: str
    x: int
    y: int
    terrain: int
    yields_item: str
    max_harvests: int
    respawn_cooldown: int
    harvest_ticks: int


class ResourceNodeStateSchema(BaseModel):
    node_id: int
    remaining: int
    is_available: bool


class TreasureChestSchema(BaseModel):
    chest_id: int
    x: int
    y: int
    tier: int


class TreasureChestStateSchema(BaseModel):
    chest_id: int
    looted: bool
    guard_entity_id: int | None = None


class LocationSchema(BaseModel):
    location_id: str
    name: str
    location_type: str
    x: int
    y: int
    region_id: str


class RegionSchema(BaseModel):
    region_id: str
    name: str
    terrain: int
    center_x: int
    center_y: int
    radius: int
    difficulty: int
    owner_faction: str | None = None
    influence: float = 0.0
    locations: list[LocationSchema] = Field(default_factory=list)


class WorldStateResponse(BaseModel):
    tick: int
    alive_count: int
    entities: list[EntitySlimSchema] = Field(default_factory=list)
    selected_entity: EntitySchema | None = None
    events: list[EventSchema] = Field(default_factory=list)
    ground_items: list[GroundItemSchema] = Field(default_factory=list)
    # Dynamic world object state (Audit Point 3 follow-up)
    resource_nodes: list[ResourceNodeStateSchema] = Field(default_factory=list)
    treasure_chests: list[TreasureChestStateSchema] = Field(default_factory=list)
    buildings: list[BuildingStateSchema] = Field(default_factory=list)
    # Strategic State (Milestone 11)
    war_status: dict[str, bool] = Field(default_factory=dict)
    faction_aggression: dict[str, float] = Field(default_factory=dict)


class StaticDataResponse(BaseModel):
    """Static world data fetched once after map load."""
    buildings: list[BuildingSchema] = Field(default_factory=list)
    resource_nodes: list[ResourceNodeSchema] = Field(default_factory=list)
    treasure_chests: list[TreasureChestSchema] = Field(default_factory=list)
    regions: list[RegionSchema] = Field(default_factory=list)


# --- Control ---

class ControlResponse(BaseModel):
    status: str
    message: str
    tick: int = 0


# --- Config ---

class SimulationConfigResponse(BaseModel):
    world_seed: int
    grid_width: int
    grid_height: int
    max_ticks: int
    num_workers: int
    initial_entity_count: int
    generator_spawn_interval: int
    generator_max_entities: int
    vision_range: int
    flee_hp_threshold: float
    tick_rate: float


# --- Stats ---

class SimulationStats(BaseModel):
    tick: int
    world_day: int
    alive_count: int
    total_spawned: int
    total_deaths: int
    running: bool
    paused: bool

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/config.py
"""Simulation configuration with sensible defaults."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SimulationConfig:
    """Immutable configuration for the simulation run."""

    # World
    world_seed: int = 42
    grid_width: int = 512
    grid_height: int = 512

    # Timing
    max_ticks: int = 50000
    worker_timeout_seconds: float = 2.0

    # Workers
    num_workers: int = 4

    # Entities
    initial_entity_count: int = 40
    generator_spawn_interval: int = 10
    generator_max_entities: int = 200

    # Spatial hash
    spatial_cell_size: int = 8

    # AI
    vision_range: int = 6
    flee_hp_threshold: float = 0.3
    flee_exit_threshold: float = 0.5         # HP ratio to stop fleeing (deadband)
    min_commitment_ticks: int = 3            # minimum ticks before goal re-evaluation
    goal_cooldown_ticks: int = 5             # ticks abandoned goals are penalized
    goal_cooldown_penalty: float = 0.5       # score multiplier during cooldown

    # Town
    town_center_x: int = 256
    town_center_y: int = 256
    town_radius: int = 6
    town_aura_damage: int = 2              # HP lost per tick by hostile entities in town
    town_passive_heal: int = 1             # HP regained per tick by heroes in town (even outside rest)

    # Hero
    hero_count: int = 4
    hero_respawn_ticks: int = 10
    hero_heal_per_tick: int = 3
    death_tier_max: int = 4                # Lives before permadeath

    # Combat
    base_damage: int = 5
    damage_variance: float = 0.3
    crit_chance: float = 0.1
    crit_multiplier: float = 2.0

    # Leveling
    xp_per_kill_base: int = 80
    
    # Milestone levels mapping (Level -> (Bonus HP, Bonus ATK, Bonus DEF, Bonus SPD))
    milestone_levels: dict[int, tuple[int, int, int, int]] = field(default_factory=lambda: {
        5:  (15, 3, 2, 2),
        10: (20, 4, 3, 3),
        15: (15, 3, 2, 2),
        20: (20, 4, 3, 2),
        25: (15, 3, 2, 2),
        30: (10, 2, 1, 1),
    })

    max_level: int = 30

    # Inventory
    hero_inventory_slots: int = 36
    hero_inventory_weight: float = 90.0
    goblin_inventory_slots: int = 12
    goblin_inventory_weight: float = 30.0

    # Chase mechanics (epic-05)
    opportunity_attack_damage_mult: float = 0.5   # Damage mult for free hit on melee disengage
    chase_spd_closing_base: int = 6              # Base ticks between bonus closing moves (lower = faster)

    # Aggro / threat system (epic-05 F3)
    threat_decay_rate: float = 0.10              # 10% threat decay per tick
    threat_damage_mult: float = 1.0              # Threat per point of damage dealt
    threat_heal_mult: float = 0.5                # Threat per point of healing done (on healer)
    threat_tank_class_mult: float = 1.5          # Threat multiplier for tank classes (Warrior/Champion)

    # Mob leash (enhance-04)
    mob_leash_radius: int = 15
    mob_leash_chase_multiplier: float = 1.5
    mob_chase_give_up_ticks: int = 20
    mob_return_heal_rate: float = 0.05  # 5% max HP per tick while returning

    # Camps
    num_camps: int = 8
    camp_radius: int = 2
    camp_spawn_interval: int = 20
    camp_max_guards: int = 5
    camp_min_distance_from_town: int = 60

    # Sanctuary (buffer zone around town)
    sanctuary_radius: int = 12

    # Calamity & Faction Raids (epic-17)
    raid_interval_days: int = 20
    raid_base_strength: int = 5

    # Regions (epic-15)
    num_forest_regions: int = 4
    num_desert_regions: int = 3
    num_swamp_regions: int = 3
    num_mountain_regions: int = 3
    num_grassland_regions: int = 4
    num_snow_regions: int = 3
    num_jungle_regions: int = 3
    num_volcanic_regions: int = 2
    region_min_radius: int = 30
    region_max_radius: int = 60
    region_min_distance: int = 40
    # Difficulty zone boundaries: (max_manhattan_distance_from_town, tier)
    difficulty_zones: tuple = ((80, 1), (150, 2), (220, 3), (999, 4))
    # Sub-locations per region
    min_locations_per_region: int = 3
    max_locations_per_region: int = 6
    location_min_spacing: int = 5

    # Roads & structures
    num_ruins: int = 4                         # Scattered ruins on the map
    num_dungeon_entrances: int = 2             # Dungeon entrances in remote areas
    road_from_town: bool = True                # Generate roads from town outward

    # Resource nodes
    resources_per_region: int = 4
    resource_respawn_ticks: int = 30
    harvest_duration: int = 2

    # Territory intrusion
    territory_debuff_duration: int = 3      # Ticks the debuff lasts after leaving
    territory_alert_radius: int = 6         # How far intrusion alert propagates

    # Looting
    loot_duration: int = 3                  # Ticks to channel before picking up loot

    # Subsystem tick rates (design-02): how often each subsystem group runs
    # rate=1 means every tick, rate=2 means every 2nd tick, etc.
    subsystem_rate_core: int = 1          # Cleanup, effects, stamina, cooldowns, engagement
    subsystem_rate_environment: int = 2   # Territory effects, entity memory, goals
    subsystem_rate_economy: int = 5       # Resource respawn, chest respawn, healing, quests

    # Logging
    log_level: str = "INFO"
    replay_file: str = "replay.json"

    # Chaos Mode (infra-06)
    chaos_enabled: bool = False
    chaos_drop_rate: float = 0.05        # Probability to drop an AI result

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/__init__.py
"""Core data models and world representation."""

from src.core.models.enums import AIState, ActionType, Direction, Domain, Material
from src.core.entities.entity import Entity
from src.core.entities.stats import Stats
from src.core.models.vectors import Vector2
from src.core.world.grid import Grid
from src.core.models.world_state import WorldState
from src.core.models.snapshot import Snapshot

__all__ = [
    "AIState",
    "ActionType",
    "Direction",
    "Domain",
    "Entity",
    "Grid",
    "Material",
    "Snapshot",
    "Stats",
    "Vector2",
    "WorldState",
]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/aspects/combat.py
from __future__ import annotations
from typing import Any
from pydantic import Field
from src.core.models.base import Aspect
from src.core.models.enums import Element

class CombatAspect(Aspect):
    """Aspect handling health, attack power, defense, and elemental vulnerabilities."""
    hp: int = 20
    max_hp: int = 20
    atk: int = 5
    def_: int = 0
    spd: int = 10
    luck: int = 0
    crit_rate: float = 0.05
    crit_dmg: float = 1.5
    evasion: float = 0.0

    # Magic combat
    matk: int = 5
    mdef: int = 0

    # Elemental vulnerability table
    elem_vuln: dict[int, float] = Field(default_factory=lambda: {
        Element.FIRE: 1.0,
        Element.ICE: 1.0,
        Element.LIGHTNING: 1.0,
        Element.DARK: 1.0,
        Element.HOLY: 1.0,
    })
    
    hp_regen: float = 1.0
    
    # Secondary stats (moved from legacy Stats)
    vision_range: int = 6
    loot_bonus: float = 1.0
    trade_bonus: float = 1.0
    interaction_speed: float = 1.0
    rest_efficiency: float = 1.0
    cooldown_reduction: float = 1.0
    
    # State & Targeting
    effects: list[Any] = Field(default_factory=list)
    combat_target_id: int | None = None
    loot_progress: int = 0

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def elemental_vulnerability(self, elem: Element) -> float:
        """Returns the vulnerability multiplier for a given element."""
        return self.elem_vuln.get(elem, 1.0)

    def model_copy(self, **kwargs) -> CombatAspect:
        """Deep copy collections even on shallow aspect copy."""
        copy_obj = super().model_copy(**kwargs)
        copy_obj.elem_vuln = dict(self.elem_vuln)
        copy_obj.effects = list(self.effects)
        return copy_obj

    @property
    def hp_ratio(self) -> float:
        if self.max_hp <= 0:
            return 0.0
        return max(0.0, min(1.0, self.hp / self.max_hp))

    def copy_stats(self) -> "CombatAspect":
        """Equivalent to the old Stats.copy()."""
        return CombatAspect(**self.model_dump())

    # --- Legacy Stats Compatibility ---
    # These properties delegate to other aspects on the entity
    
    @property
    def level(self) -> int: 
        if not self._entity: return 1
        return self.entity.progression.level
    @level.setter
    def level(self, val: int): 
        if self._entity: self.entity.progression.level = val

    @property
    def xp(self) -> int: 
        if not self._entity: return 0
        return self.entity.progression.xp
    @xp.setter
    def xp(self, val: int): 
        if self._entity: self.entity.progression.xp = val

    @property
    def xp_to_next(self) -> int: 
        if not self._entity: return 100
        return self.entity.progression.xp_to_next
    @xp_to_next.setter
    def xp_to_next(self, val: int): 
        if self._entity: self.entity.progression.xp_to_next = val

    @property
    def gold(self) -> int: 
        if not self._entity: return 0
        return self.entity.progression.gold
    @gold.setter
    def gold(self, val: int): 
        if self._entity: self.entity.progression.gold = val

    @property
    def stamina(self) -> int: 
        if not self._entity: return 100
        return self.entity.progression.stamina
    @stamina.setter
    def stamina(self, val: int): 
        if self._entity: self.entity.progression.stamina = val

    @property
    def max_stamina(self) -> int: 
        if not self._entity: return 100
        return self.entity.progression.max_stamina
    @max_stamina.setter
    def max_stamina(self, val: int): 
        if self._entity: self.entity.progression.max_stamina = val

    @property
    def fame(self) -> int: 
        if not self._entity: return 0
        return self.entity.progression.fame
    @fame.setter
    def fame(self, val: int): 
        if self._entity: self.entity.progression.fame = val

    @property
    def chase_ticks(self) -> int:
        if not self._entity: return 0
        return self.entity.mind.chase_ticks
    @chase_ticks.setter
    def chase_ticks(self, val: int):
        if self._entity: self.entity.mind.chase_ticks = val

    @property
    def engaged_ticks(self) -> int:
        if not self._entity: return 0
        return self.entity.mind.engaged_ticks
    @engaged_ticks.setter
    def engaged_ticks(self, val: int):
        if self._entity: self.entity.mind.engaged_ticks = val

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/aspects/identity.py
from __future__ import annotations
from pydantic import Field
from src.core.models.base import Aspect
from src.core.models.enums import EntityRole
from src.core.gameplay.faction import Faction

class IdentityAspect(Aspect):
    """Aspect handling entity name, faction, role, and tiering."""
    display_name: str = ""
    faction: Any = Faction.HERO_GUILD
    role: Any = EntityRole.MOB
    tier: int = 0
    is_world_boss: bool = False
    hero_class: Any = 0 # HeroClass.NONE
    reputation: float = 0.0
    
    # Pillar 1 & 5: Soul & Evolution
    life_directive: str = "EXPLORATION" # e.g. "CRAFTER", "MONSTER_HUNTER", "GOBLIN_BANE"
    kill_count: int = 0
    
    # Metadata & Traits
    death_count: int = 0
    generation: int = 1
    traits: list[Any] = Field(default_factory=list)
    titles: list[str] = Field(default_factory=list)
    weakness: str = ""
    hero_familiarity: dict[int, float] = Field(default_factory=dict)
    known_recipes: list[str] = Field(default_factory=list)
    craft_target: str | None = None
    
    # Personality (OCEAN model, 0.0 - 1.0)
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/aspects/inventory.py
from __future__ import annotations
from typing import Any
from pydantic import Field
from src.core.models.base import Aspect

class InventoryAspect(Aspect):
    """Aspect handling items, equipment, and weight management."""
    items: list[str] = Field(default_factory=list)
    max_slots: int = 8
    max_weight: float = 20.0
    weapon: str | None = None
    armor: str | None = None
    accessory: str | None = None
    
    # Home storage (heroes only)
    home_storage: Any = None

    def model_copy(self, **kwargs) -> InventoryAspect:
        """Deep copy items and home_storage even on shallow aspect copy."""
        copy_obj = super().model_copy(**kwargs)
        copy_obj.items = list(self.items) # Always ensure new list object
        if self.home_storage and hasattr(self.home_storage, "copy"):
            copy_obj.home_storage = self.home_storage.copy()
        return copy_obj

    def __eq__(self, other: Any) -> bool:
        if not hasattr(other, "items"): return False
        return (
            list(self.items) == list(other.items) and
            self.max_slots == getattr(other, "max_slots", -1) and
            abs(self.max_weight - getattr(other, "max_weight", 0.0)) < 0.001 and
            self.weapon == getattr(other, "weapon", None) and
            self.armor == getattr(other, "armor", None) and
            self.accessory == getattr(other, "accessory", None)
        )

    @property
    def used_slots(self) -> int:
        return len(self.items)

    @property
    def is_full(self) -> bool:
        return self.used_slots >= self.max_slots

    @property
    def current_weight(self) -> float:
        total = 0.0
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        for iid in self.items:
            t = ITEM_REGISTRY.get(iid)
            if t: total += t.weight
        for slot_id in (self.weapon, self.armor, self.accessory):
            if slot_id:
                t = ITEM_REGISTRY.get(slot_id)
                if t: total += t.weight
        return total

    @property
    def total_weight(self) -> float:
        return self.current_weight

    @property
    def is_effectively_full(self) -> bool:
        """True if inventory is full by slots or near weight limit."""
        return self.is_full or (self.current_weight >= self.max_weight * 0.9)

    @property
    def weight_ratio(self) -> float:
        """Ratio of current weight to max weight (0.0 to 1.0+)."""
        if self.max_weight <= 0:
            return 1.0
        return self.current_weight / self.max_weight

    def count_item(self, item_id: str) -> int:
        """Count how many copies of item_id are in the bag."""
        return self.items.count(item_id)

    def has_consumable(self, item_id: str) -> bool:
        """Check if item_id is in inventory Bag."""
        return item_id in self.items
    
    def can_add(self, item_id: str) -> bool:
        if self.used_slots >= self.max_slots: return False
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        t = ITEM_REGISTRY.get(item_id)
        if t is None: return False
        return self.current_weight + t.weight <= self.max_weight

    def add_item(self, item_id: str) -> bool:
        if not self.can_add(item_id): return False
        self.items.append(item_id)
        return True

    def remove_item(self, item_id: str) -> bool:
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False

    def equip(self, item_id: str) -> bool:
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        from src.core.gameplay.items.items import ItemType
        t = ITEM_REGISTRY.get(item_id)
        if t is None or item_id not in self.items: return False
        if t.item_type == ItemType.WEAPON:
            if self.weapon: self.items.append(self.weapon)
            self.weapon = item_id
        elif t.item_type == ItemType.ARMOR:
            if self.armor: self.items.append(self.armor)
            self.armor = item_id
        elif t.item_type == ItemType.ACCESSORY:
            if self.accessory: self.items.append(self.accessory)
            self.accessory = item_id
        else: return False
        self.items.remove(item_id)
        return True

    def auto_equip_best(self, item_id: str, hero_class: Any = 0) -> bool:
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        from src.core.gameplay.items.items import ItemType, _item_power
        t = ITEM_REGISTRY.get(item_id)
        if t is None or item_id not in self.items: return False
        if t.item_type not in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY): return False
        if t.item_type == ItemType.WEAPON: current_id = self.weapon
        elif t.item_type == ItemType.ARMOR: current_id = self.armor
        else: current_id = self.accessory
        
        if current_id is None: return self.equip(item_id)
        current_t = ITEM_REGISTRY.get(current_id)
        if current_t is None or _item_power(t, hero_class) > _item_power(current_t, hero_class):
            return self.equip(item_id)
        return False

    def equipment_bonus(self, stat: str) -> int | float:
        total = 0
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        for slot_id in (self.weapon, self.armor, self.accessory):
            if slot_id:
                t = ITEM_REGISTRY.get(slot_id)
                if t: total += getattr(t, stat, 0)
        return total

    def get_all_item_ids(self) -> list[str]:
        result = list(self.items)
        if self.weapon: result.append(self.weapon)
        if self.armor: result.append(self.armor)
        if self.accessory: result.append(self.accessory)
        return result

    def copy_inventory(self) -> "InventoryAspect":
        """Compatibility for old inventory.copy() calls."""
        return InventoryAspect(**self.model_dump())

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/aspects/mind.py
from __future__ import annotations
from typing import Any
from pydantic import Field
from src.core.models.base import Aspect
from src.core.models.enums import AIState

class MindAspect(Aspect):
    """Aspect handling AI state, memory, goals, and threat/aggro."""
    ai_state: AIState = AIState.IDLE
    goals: list[str] = Field(default_factory=list)
    memory: dict[int, Any] = Field(default_factory=dict)
    threat_table: dict[int, float] = Field(default_factory=dict)
    last_reason: str = ""
    
    # Sensory Memory
    terrain_memory: dict[tuple[int, int], int] = Field(default_factory=dict)
    entity_memory: list[dict] = Field(default_factory=list)
    memory_log: list[dict[str, Any]] = Field(default_factory=list) # Narrative log: (tick, type, desc, impact)
    
    # Engagement and paths
    engaged_ticks: int = 0
    cached_path: list[Any] | None = Field(default=None, repr=False)
    cached_path_target: Any | None = Field(default=None, repr=False)
    
    consecutive_idle_ticks: int = 0
    chase_ticks: int = 0
    # Cognitive Pipeline: Selective Attention
    last_goal: str | None = None
    pos_history: list[Any] = Field(default_factory=list)
    attention_pool: list[int] = Field(default_factory=list)
    max_attention_slots: int = 5
    hero_familiarity: dict[int, float] = Field(default_factory=dict)
    
    # Emotional States & Personality (short-term & long-term)
    emotional_state: dict[str, float] = Field(default_factory=dict)
    mood: float = 0.5  # 0.0 (despair/fear) to 1.0 (confidence/fury)
    
    # Nemesis & Memory
    grudges: dict[int, float] = Field(default_factory=dict) # entity_id -> grudge level
    memory_locations: dict[str, float] = Field(default_factory=dict) # region_id -> sentiment (-1.0 to 1.0)
    region_fatigue: dict[str, float] = Field(default_factory=dict) # region_id -> fatigue penalty (0.0 to 1.0)
    
    # Ambition & Directives
    life_directive: str | None = None # e.g. "DRAGON_SLAYER", "CRAFTER"
    
    # Action Styles (Stances)
    action_style: str = "balanced"
    
    # Hysteresis & Loop Prevention
    boredom_multipliers: dict[str, float] = Field(default_factory=dict)
    goal_committed_at: int = 0  # tick when current goal was committed
    goal_cooldowns: dict[str, int] = Field(default_factory=dict)  # goal→expiry tick
    goal_switch_count: int = 0  # diagnostic counter
    bonuses: dict[str, Any] = Field(default_factory=dict)

    # --- Narrative Memory Helpers ---

    def total_glory(self) -> float:
        """Sum of all positive-impact memory entries."""
        return sum(
            e.get("impact", 0.0)
            for e in self.memory_log
            if e.get("impact", 0.0) > 0
        )

    def total_trauma(self) -> float:
        """Sum of all negative-impact memory entries (returns negative value)."""
        return sum(
            e.get("impact", 0.0)
            for e in self.memory_log
            if e.get("impact", 0.0) < 0
        )

    def prune_memories(self, max_entries: int = 50) -> None:
        """Keep only the top *max_entries* memories by absolute impact."""
        if len(self.memory_log) <= max_entries:
            return
        self.memory_log.sort(key=lambda e: abs(float(e.get("impact", 0.0))), reverse=True)
        self.memory_log = self.memory_log[:max_entries]

    def get_emotional_modifier(self, emotion: str) -> float:
        """Return a weight multiplier derived from internal emotional state.
        
        Default neutral is 1.0.
        """
        val = self.emotional_state.get(emotion, 0.0)
        # Hysteresis and mood influence
        if emotion == "panic":
            return 1.0 + (val * 1.5) # Up to 2.5x weight for Fleeing
        if emotion == "boredom":
            # Boredom is tracked per goal in boredom_multipliers, but this is a general factor
            return 1.0 - (val * 0.5)
        if emotion == "stuck":
            return val * 5.0 # Massive boost to "Get Unstuck" goals
        return 1.0

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/aspects/progression.py
from __future__ import annotations
from typing import TYPE_CHECKING, Any
from pydantic import Field
from src.core.models.base import Aspect

if TYPE_CHECKING:
    from src.core.gameplay.classes import SkillInstance
    from src.core.gameplay.attributes import Attributes, AttributeCaps

class ProgressionAspect(Aspect):
    """Aspect handling levelling, XP, gold, skills, and attributes."""
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    gold: int = 0
    fame: int = 0
    stamina: int = 50
    max_stamina: int = 50
    
    # Hero skills and class
    hero_class: int = 0                 # HeroClass enum value
    skills: list[Any] = Field(default_factory=list)
    class_mastery: float = 0.0
    
    # veterancy
    veterancy_points: int = 0
    veterancy_rank: int = 0
    
    # RPG attributes
    attributes: Any = None
    attribute_caps: Any = None
    
    # Genetic Pillar (The Body)
    genetic_seed: int = 0
    age_ticks: int = 0
    longevity_limit: int = 100000        # Max lifecycle in ticks
    aptitudes: dict[str, float] = Field(default_factory=dict)
    
    # Talents & Quests
    talent_points: int = 0
    talents: list[str] = Field(default_factory=list)
    quests: list[Any] = Field(default_factory=list)

    @property
    def stamina_ratio(self) -> float:
        return self.stamina / self.max_stamina if self.max_stamina > 0 else 0.0

    @property
    def xp_ratio(self) -> float:
        return self.xp / self.xp_to_next if self.xp_to_next > 0 else 0.0

    def model_copy(self, **kwargs) -> ProgressionAspect:
        """Ensure nested collections and attributes are copied even on shallow aspect copy."""
        copy_obj = super().model_copy(**kwargs)
        # Copy lists & dicts to ensure isolation
        # Elements in these lists (SkillInstance, Quest) also need to be copied
        copy_obj.skills = [s.copy() if hasattr(s, "copy") else s for s in self.skills]
        copy_obj.talents = list(self.talents)
        copy_obj.quests = [q.copy() if hasattr(q, "copy") else q for q in self.quests]
        copy_obj.aptitudes = dict(self.aptitudes)
        
        if self.attributes and hasattr(self.attributes, "copy"):
            copy_obj.attributes = self.attributes.copy()
        if self.attribute_caps and hasattr(self.attribute_caps, "copy"):
            copy_obj.attribute_caps = self.attribute_caps.copy()
        return copy_obj

    def on_attach(self, owner: Any) -> None:
        """Called when the aspect is attached to an Entity."""
        super().on_attach(owner)
        if self.genetic_seed != 0 and not self.aptitudes:
            self.init_genetics()

    def init_genetics(self) -> None:
        """Initialize aptitudes and longevity from the genetic seed."""
        import random
        rng = random.Random(self.genetic_seed)
        attrs = ["str", "agi", "vit", "int", "spi", "wis", "end", "per", "cha"]
        self.aptitudes = {a: rng.uniform(0.8, 1.25) for a in attrs}
        self.longevity_limit = rng.randint(50000, 150000)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/aspects/spatial.py
from __future__ import annotations
from pydantic import Field
from src.core.models.base import Aspect
from src.core.models.vectors import Vector2

class SpatialAspect(Aspect):
    """Aspect handling entity position, regions, and leash constraints."""
    pos: Vector2 = Field(default_factory=lambda: Vector2(0, 0))
    region_id: str = ""
    current_region_id: str = ""
    home_pos: Vector2 | None = None
    leash_radius: int = 0
    difficulty_tier: int = 1
    facing: Vector2 = Field(default_factory=lambda: Vector2(0, 1))
    is_hidden: bool = False

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/data/__init__.py


#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/data/events.py
from dataclasses import dataclass
from typing import Dict, Optional

class DomainEvent:
    """Base class for all strictly-typed simulation events."""
    pass

@dataclass
class CombatEvent(DomainEvent):
    attacker_id: int
    defender_id: int
    damage: int
    is_crit: bool
    is_evasion: bool
    skill_used: str
    attacker_hp: int
    defender_hp: int

@dataclass
class DeathEvent(DomainEvent):
    entity_id: int
    killer_id: Optional[int]
    x: int
    y: int
    level_at_death: int
    is_permadeath: bool

@dataclass
class LootEvent(DomainEvent):
    entity_id: int
    item_id: str
    item_name: str
    source: str

@dataclass
class LevelUpEvent(DomainEvent):
    entity_id: int
    old_level: int
    new_level: int
    attribute_gains: Dict[str, int]

@dataclass
class TradeEvent(DomainEvent):
    entity_id: int
    action: str  # "buy" or "sell"
    item_id: str
    gold_change: int

@dataclass
class CraftEvent(DomainEvent):
    entity_id: int
    recipe_id: str
    output_item: str

@dataclass
class QuestEvent(DomainEvent):
    entity_id: int
    quest_title: str
    quest_type: str
    status: str # "accepted", "completed", "failed"
    gold_reward: int
    xp_reward: int

@dataclass
class RenownEvent(DomainEvent):
    entity_id: int
    glory_type: str # "boss_kill", "saved_town", "monument_builder", "evolution"
    description: str
    renown_gain: float

@dataclass
class WarEvent(DomainEvent):
    faction_id: int
    is_declared: bool
    aggression: float

@dataclass
class ConquestEvent(DomainEvent):
    region_id: str
    region_name: str
    old_owner: str | None
    new_owner: str | None
    is_liberation: bool

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/data/hero_names.py
"""Hero name generation tables and logic."""

from __future__ import annotations
from typing import TYPE_CHECKING
from src.core.models.enums import TraitType

if TYPE_CHECKING:
    from src.platform.rng import DeterministicRNG

# --- Name Tables ---

FIRST_NAMES = [
    "Kael", "Lyra", "Thorne", "Sera", "Aldric", "Mira", "Rowan", "Elowen",
    "Garrick", "Talia", "Caden", "Elara", "Bryn", "Sylas", "Vane", "Kira",
    "Joram", "Liora", "Finn", "Aria", "Corvus", "Lyza", "Torin", "Maia",
    "Rylan", "Eryn", "Kaelen", "Valer", "Zada", "Caelum", "Nyx", "Oberon"
]

TRAIT_TITLES = {
    TraitType.AGGRESSIVE: "the Fierce",
    TraitType.CAUTIOUS: "the Careful",
    TraitType.BRAVE: "the Bold",
    TraitType.COWARDLY: "the Craven",
    TraitType.BLOODTHIRSTY: "the Merciless",
    TraitType.GREEDY: "the Grasper",
    TraitType.GENEROUS: "the Kind",
    TraitType.CHARISMATIC: "the Bright",
    TraitType.LONER: "the Silent",
    TraitType.DILIGENT: "the Steadfast",
    TraitType.LAZY: "the Idle",
    TraitType.CURIOUS: "the Seeker",
    TraitType.BERSERKER: "the Wild",
    TraitType.TACTICAL: "the Sharp",
    TraitType.RESILIENT: "the Iron",
    TraitType.ARCANE_GIFTED: "the Mystic",
    TraitType.SPIRIT_TOUCHED: "the Pale",
    TraitType.ELEMENTALIST: "the Storm",
    TraitType.KEEN_EYED: "the Watcher",
    TraitType.OBLIVIOUS: "the Dreamer",
}

def generate_hero_name(rng: DeterministicRNG, eid: int, tick: int, traits: list[int]) -> str:
    """Generate a unique hero name based on RNG and traits.
    
    Format: "{first_name} {title}"
    """
    from src.core.models.enums import Domain
    
    # Pick a first name
    name_idx = rng.next_int(Domain.SPAWN, eid, tick, 0, len(FIRST_NAMES) - 1)
    first_name = FIRST_NAMES[name_idx]
    
    # Pick a title from traits (if any)
    title = ""
    if traits:
        # Sort to ensure determinism if traits list order varies (unlikely but safe)
        valid_traits = sorted([t for t in traits if t in TRAIT_TITLES])
        if valid_traits:
            trait_idx = rng.next_int(Domain.SPAWN, eid, tick + 1, 0, len(valid_traits) - 1)
            title = TRAIT_TITLES[valid_traits[trait_idx]]
            
    if title:
        return f"{first_name} {title}"
    return first_name

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/entities/__init__.py


#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/entities/entity.py
"""Core data models: Vector2, Stats, Entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, ConfigDict, model_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass, rebuild_dataclass
from src.core.models.enums import AIState, DamageType, Element, EnemyTier, EntityRole, TraitType, HeroClass
from src.core.gameplay.faction import Faction

if TYPE_CHECKING:
    from src.core.gameplay.attributes import Attributes, AttributeCaps
    from src.core.gameplay.classes import SkillInstance
    from src.core.gameplay.effects import StatusEffect
    from src.core.gameplay.quests import Quest
    from src.api.schemas import EntitySlimSchema, EntitySchema, AttributeSchema, AttributeCapSchema, EffectSchema
    from src.core.models.base import Aspect
    from src.core.aspects.identity import IdentityAspect
    from src.core.aspects.spatial import SpatialAspect
    from src.core.aspects.combat import CombatAspect
    from src.core.aspects.inventory import InventoryAspect
    from src.core.aspects.progression import ProgressionAspect
    from src.core.aspects.mind import MindAspect


from src.core.entities.traits import TraitType
from src.core.models.vectors import Vector2, FloatVector2, DIRECTION_OFFSETS
from src.core.entities.stats import Stats
from src.core.entities.stats_proxy import StatsProxy

from src.core.models.world_objects import HomeStorage, TreasureChest, CorpseNode

class Entity(BaseModel):
    """A simulation entity — character, generator, or any world actor.
    
    Refactored to an Aspect-Oriented container.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    id: int
    kind: str
    next_act_at: int = 0
    
    # New Aspect Registry
    aspects: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, id: Any = None, kind: Any = None, **data: Any) -> None:
        """Support positional arguments for backward compatibility.
        
        Usage:
            Entity(10, "hero", ...)
            Entity(id=10, kind="hero", ...)
        """
        # If the first arg is a dict, it's likely Pydantic's internal state
        if isinstance(id, dict) and not data:
            super().__init__(**id)
            return

        # Prepare final data dict for Pydantic
        final_data = dict(data)
        if id is not None:
            final_data["id"] = id
        if kind is not None:
            final_data["kind"] = kind
            
        # Coerce ID to int if it's a float
        if "id" in final_data and isinstance(final_data["id"], float):
            final_data["id"] = int(final_data["id"])
            
        super().__init__(**final_data)

    @model_validator(mode="before")
    @classmethod
    def _validate_before(cls, data: Any) -> Any:
        """Ensure core fields have correct types before Pydantic validation."""
        if isinstance(data, dict):
            if "id" in data and isinstance(data["id"], float):
                data["id"] = int(data["id"])
            if "next_act_at" in data and isinstance(data["next_act_at"], float):
                data["next_act_at"] = int(data["next_act_at"])
        return data

    def model_post_init(self, __context: Any) -> None:
        """Handle legacy constructor arguments and ensure aspects exist."""
        # Ensure all core aspects exist even if not provided
        if not self.aspects:
            from src.core.aspects.identity import IdentityAspect
            from src.core.aspects.spatial import SpatialAspect
            from src.core.aspects.combat import CombatAspect
            from src.core.aspects.inventory import InventoryAspect
            from src.core.aspects.progression import ProgressionAspect
            from src.core.aspects.mind import MindAspect
            self.aspects = {
                "identity": IdentityAspect(),
                "spatial": SpatialAspect(),
                "combat": CombatAspect(),
                "inventory": InventoryAspect(),
                "progression": ProgressionAspect(),
                "mind": MindAspect(),
            }
        
        # Ensure 'stats' proxy exists if needed and re-attach all aspects
        # Re-attach aspects to ensure parent pointers/references are correct
        for aspect in self.aspects.values():
            if hasattr(aspect, "on_attach"):
                aspect.on_attach(self)

        # Handle legacy constructor arguments
        extra_data = getattr(self, "__pydantic_extra__", {})
        if not extra_data:
            return

        # Simple auto-mapping to our property shims!
        for key, value in extra_data.items():
            # If we have a setter for this name (like pos.setter), then use it!
            # Since pydantic already put it in __pydantic_extra__, we just need to shift it
            if hasattr(self, key):
                try:
                    setattr(self, key, value)
                except AttributeError:
                    # Might be a read-only property or some other issue
                    pass

        # Re-export world objects for backward compatibility
        # These were extracted to world_objects.py to reduce models.py size.
        from src.core.models.world_objects import HomeStorage, TreasureChest, CorpseNode

    @property
    def identity(self) -> "IdentityAspect":
        return self.aspects["identity"]

    @property
    def faction(self) -> Any: return self.identity.faction
    @faction.setter
    def faction(self, val: Any): self.identity.faction = val

    @property
    def role(self) -> Any: return self.identity.role
    @role.setter
    def role(self, val: Any): self.identity.role = val

    @property
    def rarity(self) -> int: return self.identity.tier
    @rarity.setter
    def rarity(self, val: int): self.identity.tier = val

    @property
    def weakness(self) -> str: return self.identity.weakness
    @weakness.setter
    def weakness(self, val: str): self.identity.weakness = val

    @property
    def tier(self) -> int: return self.identity.tier
    @tier.setter
    def tier(self, val: int): self.identity.tier = val

    @property
    def hero_class(self) -> Any: return self.identity.hero_class
    @hero_class.setter
    def hero_class(self, val: Any): self.identity.hero_class = val

    @property
    def spatial(self) -> "SpatialAspect":
        return self.aspects["spatial"]

    @property
    def titles(self) -> list[str]: return self.identity.titles
    @titles.setter
    def titles(self, val: list[str]): self.identity.titles = val

    @property
    def combat(self) -> "CombatAspect":
        return self.aspects["combat"]

    @property
    def effects(self) -> list[Any]: return self.combat.effects
    @effects.setter
    def effects(self, val: list[Any]): self.combat.effects = val

    @property
    def mind(self) -> "MindAspect":
        return self.aspects["mind"]

    @property
    def consecutive_idle_ticks(self) -> int: return self.mind.consecutive_idle_ticks
    @consecutive_idle_ticks.setter
    def consecutive_idle_ticks(self, val: int): self.mind.consecutive_idle_ticks = val

    @property
    def boredom_multipliers(self) -> dict[str, float]: return self.mind.boredom_multipliers
    @boredom_multipliers.setter
    def boredom_multipliers(self, val: dict[str, float]): self.mind.boredom_multipliers = val

    @property
    def progression(self) -> "ProgressionAspect":
        return self.aspects["progression"]

    @property
    def level(self) -> int: return self.progression.level
    @level.setter
    def level(self, val: int): self.progression.level = val

    @property
    def veterancy_points(self) -> int: return self.progression.veterancy_points
    @veterancy_points.setter
    def veterancy_points(self, val: int): self.progression.veterancy_points = val

    @property
    def veterancy_rank(self) -> int: return self.progression.veterancy_rank
    @veterancy_rank.setter
    def veterancy_rank(self, val: int): self.progression.veterancy_rank = val

    @property
    def talents(self) -> list[str]: return self.progression.talents
    @talents.setter
    def talents(self, val: list[str]): self.progression.talents = val

    @property
    def quests(self) -> list[Any]: return self.progression.quests
    @quests.setter
    def quests(self, val: list[Any]): self.progression.quests = val

    @property
    def attributes(self) -> Any: return self.progression.attributes
    @attributes.setter
    def attributes(self, val: Any): self.progression.attributes = val

    @property
    def attribute_caps(self) -> Any: return self.progression.attribute_caps
    @attribute_caps.setter
    def attribute_caps(self, val: Any): self.progression.attribute_caps = val

    @property
    def skills(self) -> list[Any]: return self.progression.skills
    @skills.setter
    def skills(self, val: list[Any]): self.progression.skills = val

    @property
    def inventory(self) -> "InventoryAspect | None":
        return self.aspects.get("inventory")

    @inventory.setter
    def inventory(self, val: "InventoryAspect"):
        self.aspects["inventory"] = val

    # --- Spatial Shims ---
    @property
    def pos(self) -> Vector2: return self.spatial.pos
    @pos.setter
    def pos(self, val: Vector2): self.spatial.pos = val

    @property
    def region_id(self) -> str: return self.spatial.region_id
    @region_id.setter
    def region_id(self, val: str): self.spatial.region_id = val

    @property
    def current_region_id(self) -> str: return self.spatial.current_region_id
    @current_region_id.setter
    def current_region_id(self, val: str): self.spatial.current_region_id = val

    @property
    def home_pos(self) -> Vector2 | None: return self.spatial.home_pos
    @home_pos.setter
    def home_pos(self, val: Vector2 | None): self.spatial.home_pos = val

    @property
    def leash_radius(self) -> int: return self.spatial.leash_radius
    @leash_radius.setter
    def leash_radius(self, val: int): self.spatial.leash_radius = val

    @property
    def difficulty_tier(self) -> int: return self.spatial.difficulty_tier
    @difficulty_tier.setter
    def difficulty_tier(self, val: int): self.spatial.difficulty_tier = val

    # --- Derived Counters Shims ---
    
    @property
    def chase_ticks(self) -> int: return self.mind.chase_ticks
    @chase_ticks.setter
    def chase_ticks(self, val: int): self.mind.chase_ticks = val

    @property
    def consecutive_idle_ticks(self) -> int: return self.mind.consecutive_idle_ticks
    @consecutive_idle_ticks.setter
    def consecutive_idle_ticks(self, val: int): self.mind.consecutive_idle_ticks = val

    @property
    def engaged_ticks(self) -> int: return self.mind.engaged_ticks
    @engaged_ticks.setter
    def engaged_ticks(self, val: int): self.mind.engaged_ticks = val

    @property
    def combat_target_id(self) -> int | None: return self.combat.combat_target_id
    @combat_target_id.setter
    def combat_target_id(self, val: int | None): self.combat.combat_target_id = val

    @property
    def loot_progress(self) -> int: return self.combat.loot_progress
    @loot_progress.setter
    def loot_progress(self, val: int): self.combat.loot_progress = val

    @property
    def quests(self) -> list["Quest"]: return self.progression.quests
    @quests.setter
    def quests(self, val: list["Quest"]): self.progression.quests = val

    @property
    def terrain_memory(self) -> dict: return self.mind.terrain_memory
    @terrain_memory.setter
    def terrain_memory(self, val: dict): self.mind.terrain_memory = val

    @property
    def last_reason(self) -> str: return self.mind.last_reason
    @last_reason.setter
    def last_reason(self, val: str): self.mind.last_reason = val

    @property
    def hero_familiarity(self) -> dict[int, float]: return self.mind.hero_familiarity
    @hero_familiarity.setter
    def hero_familiarity(self, val: dict[int, float]): self.mind.hero_familiarity = val

    @property
    def boredom_multipliers(self) -> dict[str, float]: return self.mind.boredom_multipliers
    @boredom_multipliers.setter
    def boredom_multipliers(self, val: dict[str, float]): self.mind.boredom_multipliers = val

    @property
    def known_recipes(self) -> list[str]: return self.identity.known_recipes
    @known_recipes.setter
    def known_recipes(self, val: list[str]): self.identity.known_recipes = val

    @property
    def craft_target(self) -> str | None: return self.identity.craft_target
    @craft_target.setter
    def craft_target(self, val: str | None): self.identity.craft_target = val

    @property
    def entity_memory(self) -> list[dict]: return self.mind.entity_memory
    @entity_memory.setter
    def entity_memory(self, val: list[dict]): self.mind.entity_memory = val

    @property
    def home_storage(self) -> Any:
        inv = self.inventory
        return inv.home_storage if inv else None
    @home_storage.setter
    def home_storage(self, val: Any):
        inv = self.inventory
        if inv: inv.home_storage = val

    @property
    def inventory_aspect(self) -> "InventoryAspect" | None:
        return self.aspects.get("inventory")

    @property
    def stats(self) -> "StatsProxy":
        from .stats_proxy import StatsProxy
        return StatsProxy(self)

    @stats.setter
    def stats(self, value: Any):
        """Legacy setter for Stats object from builders."""
        from src.core.entities.stats import Stats
        if not isinstance(value, Stats):
            return
            
        # Combat Aspect
        c = self.combat
        c.hp = value.hp
        c.max_hp = value.max_hp
        c.atk = value.atk
        c.def_ = value.def_
        c.spd = value.spd
        c.luck = value.luck
        c.crit_rate = value.crit_rate
        c.crit_dmg = value.crit_dmg
        c.evasion = value.evasion
        c.matk = value.matk
        c.mdef = value.mdef
        if value.elem_vuln:
            c.elem_vuln = dict(value.elem_vuln)
        c.vision_range = value.vision_range
        c.loot_bonus = value.loot_bonus
        c.trade_bonus = value.trade_bonus
        c.interaction_speed = value.interaction_speed
        c.rest_efficiency = value.rest_efficiency
        c.hp_regen = value.hp_regen
        c.cooldown_reduction = value.cooldown_reduction
        
        # Progression Aspect
        p = self.progression
        p.level = value.level
        p.xp = value.xp
        p.xp_to_next = value.xp_to_next
        p.gold = value.gold
        p.fame = value.fame
        p.stamina = value.stamina
        p.max_stamina = value.max_stamina

    # --- Lifecycle ---
    
    def on_tick(self, tick: int) -> None:
        """Propagate tick to all aspects."""
        for aspect in self.aspects.values():
            aspect.on_tick(tick)


    def has_trait(self, trait: int) -> bool:
        """Check if entity has a specific TraitType."""
        return trait in self.identity.traits

    # --- Serialization (epic-05 api standardization) ---

    def _get_weapon_range(self) -> int:
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        inventory = self.aspects.get("inventory")
        if inventory and inventory.weapon:
            tmpl = ITEM_REGISTRY.get(inventory.weapon)
            if tmpl:
                return tmpl.weapon_range
        return 1

    def to_slim_schema(self, loot_duration: int = 3) -> "EntitySlimSchema":
        from src.api.schemas import EntitySlimSchema
        identity = self.aspects["identity"]
        spatial = self.aspects["spatial"]
        combat = self.aspects["combat"]
        mind = self.aspects["mind"]
        progression = self.aspects["progression"]
        
        return EntitySlimSchema(
            id=self.id,
            kind=self.kind,
            display_name=identity.display_name,
            x=spatial.pos.x,
            y=spatial.pos.y,
            hp=combat.hp,
            max_hp=combat.max_hp,
            state=mind.ai_state.name.lower(),
            level=progression.level,
            tier=identity.tier,
            faction=identity.faction.name.lower() if hasattr(identity.faction, "name") else str(identity.faction).lower(),
            weapon_range=self._get_weapon_range(),
            combat_target_id=combat.combat_target_id,
            loot_progress=combat.loot_progress,
            loot_duration=loot_duration,
        )

    def to_full_schema(self, loot_duration: int = 3) -> "EntitySchema":
        from src.api.schemas import EntitySchema, EffectSchema, QuestSchema
        identity = self.aspects["identity"]
        spatial = self.aspects["spatial"]
        combat = self.aspects["combat"]
        mind = self.aspects["mind"]
        progression = self.aspects["progression"]
        inventory = self.aspects.get("inventory")
        
        elem = self._elem_dmg()
        from src.core.models.enums import Element
        return EntitySchema(
            id=self.id,
            kind=self.kind,
            display_name=identity.display_name,
            x=spatial.pos.x,
            y=spatial.pos.y,
            hp=combat.hp,
            max_hp=combat.max_hp,
            atk=combat.atk,
            def_=combat.def_,
            spd=combat.spd,
            luck=combat.luck,
            crit_rate=combat.crit_rate,
            evasion=combat.evasion,
            matk=combat.matk,
            mdef=combat.mdef,
            level=progression.level,
            xp=progression.xp,
            xp_to_next=progression.xp_to_next,
            gold=progression.gold,
            tier=identity.tier,
            faction=identity.faction.name.lower() if hasattr(identity.faction, "name") else str(identity.faction).lower(),
            state=mind.ai_state.name.lower(),
            weapon=inventory.weapon if inventory else None,
            armor=inventory.armor if inventory else None,
            accessory=inventory.accessory if inventory else None,
            inventory_count=inventory.used_slots if inventory else 0,
            inventory_max_slots=inventory.max_slots if inventory else 0,
            inventory_items=list(inventory.items) if inventory else [],
            inventory_weight=round(inventory.current_weight, 1) if inventory else 0.0,
            inventory_max_weight=inventory.max_weight if inventory else 0.0,
            vision_range=combat.vision_range,
            terrain_memory={f"{k[0]},{k[1]}": v for k, v in mind.terrain_memory.items()},
            entity_memory=list(mind.entity_memory),
            goals=list(mind.goals),
            loot_progress=combat.loot_progress,
            loot_duration=loot_duration,
            known_recipes=list(identity.known_recipes),
            craft_target=identity.craft_target,
            stamina=progression.stamina,
            max_stamina=progression.max_stamina,
            attributes=self._serialize_attrs(),
            attribute_caps=self._serialize_caps(),
            hero_class=self._serialize_hero_class(),
            skills=[s.to_api_schema() for s in progression.skills],
            class_mastery=progression.class_mastery,
            active_effects=[
                EffectSchema(
                    effect_type=eff.effect_type.name.lower() if hasattr(eff.effect_type, "name") else str(eff.effect_type).lower(),
                    source=eff.source,
                    remaining_ticks=eff.remaining_ticks,
                    atk_mult=eff.atk_mult,
                    def_mult=eff.def_mult,
                    spd_mult=eff.spd_mult,
                    crit_mult=eff.crit_mult,
                    evasion_mult=eff.evasion_mult,
                    hp_per_tick=eff.hp_per_tick,
                )
                for eff in combat.effects
                if not eff.expired
            ],
            base_atk=combat.atk,
            base_def=combat.def_,
            base_spd=combat.spd,
            base_matk=combat.matk,
            base_mdef=combat.mdef,
            base_crit_rate=combat.crit_rate,
            base_evasion=combat.evasion,
            hp_regen=combat.hp_regen,
            cooldown_reduction=combat.cooldown_reduction,
            loot_bonus=combat.loot_bonus,
            trade_bonus=combat.trade_bonus,
            interaction_speed=combat.interaction_speed,
            rest_efficiency=combat.rest_efficiency,
            speed_delay_move=round(1.0 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            speed_delay_attack=round(0.9 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            speed_delay_skill=round(1.2 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            speed_delay_harvest=round(0.7 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            fire_dmg_mult=elem.fire_dmg_mult,
            ice_dmg_mult=elem.ice_dmg_mult,
            lightning_dmg_mult=elem.lightning_dmg_mult,
            dark_dmg_mult=elem.dark_dmg_mult,
            elem_vuln_fire=combat.elemental_vulnerability(Element.FIRE),
            elem_vuln_ice=combat.elemental_vulnerability(Element.ICE),
            elem_vuln_lightning=combat.elemental_vulnerability(Element.LIGHTNING),
            elem_vuln_dark=combat.elemental_vulnerability(Element.DARK),
            region_id=spatial.region_id,
            difficulty_tier=spatial.difficulty_tier,
            current_region_id=spatial.current_region_id,
            weapon_range=self._get_weapon_range(),
            combat_target_id=combat.combat_target_id,
            traits=list(identity.traits),
            home_storage_used=inventory.home_storage.used_slots if inventory and inventory.home_storage else 0,
            home_storage_max=inventory.home_storage.max_slots if inventory and inventory.home_storage else 0,
            home_storage_level=inventory.home_storage.level if inventory and inventory.home_storage else 0,
            quests=[
                QuestSchema(
                    quest_id=q.quest_id,
                    quest_type=q.quest_type.name.lower() if hasattr(q.quest_type, "name") else str(q.quest_type).lower(),
                    title=q.title,
                    description=q.description,
                    target_kind=q.target_kind,
                    target_x=q.target_pos.x if q.target_pos else None,
                    target_y=q.target_pos.y if q.target_pos else None,
                    target_count=q.target_count,
                    progress=q.progress,
                    completed=q.completed,
                    gold_reward=q.gold_reward,
                    xp_reward=q.xp_reward,
                )
                for q in progression.quests
            ],
        )


    def _elem_dmg(self):
        """Calculates elemental damage multipliers based on traits."""
        from src.core.models.enums import TraitType
        fire = 1.0; ice = 1.0; lightning = 1.0; dark = 1.0
        
        traits = self.identity.traits
        if TraitType.ELEMENTALIST in traits:
            fire += 0.2; ice += 0.2; lightning += 0.2
        if TraitType.ARCANE_GIFTED in traits:
            dark += 0.2
        if TraitType.SPIRIT_TOUCHED in traits:
            fire += 0.1; ice += 0.1; lightning += 0.1; dark += 0.1

        # Use a simple class to match the 'elem.X' access in to_full_schema
        class ElemDmg:
            def __init__(self, f, i, l, d):
                self.fire_dmg_mult = f
                self.ice_dmg_mult = i
                self.lightning_dmg_mult = l
                self.dark_dmg_mult = d
        return ElemDmg(fire, ice, lightning, dark)

    def _serialize_attrs(self):
        """Serializes RPG attributes to Schema."""
        if not self.progression or not self.progression.attributes:
            return None
        from src.api.schemas import AttributeSchema
        a = self.progression.attributes
        return AttributeSchema(
            str=a.str_, agi=a.agi, vit=a.vit, int=a.int_,
            spi=a.spi, wis=a.wis, end=a.end, per=a.per, cha=a.cha,
            str_frac=a._str_frac, agi_frac=a._agi_frac, vit_frac=a._vit_frac,
            int_frac=a._int_frac, spi_frac=a._spi_frac, wis_frac=a._wis_frac,
            end_frac=a._end_frac, per_frac=a._per_frac, cha_frac=a._cha_frac
        )

    def _serialize_caps(self):
        """Serializes attribute caps to Schema."""
        if not self.progression or not self.progression.attribute_caps:
            return None
        from src.api.schemas import AttributeCapSchema
        c = self.progression.attribute_caps
        return AttributeCapSchema(
            str_cap=c.str_cap, agi_cap=c.agi_cap, vit_cap=c.vit_cap,
            int_cap=c.int_cap, spi_cap=c.spi_cap, wis_cap=c.wis_cap,
            end_cap=c.end_cap, per_cap=c.per_cap, cha_cap=c.cha_cap
        )

    def _serialize_hero_class(self) -> str:
        """Returns the lower-case name of the hero class."""
        from src.core.models.enums import HeroClass
        try:
            # self.progression.hero_class is assumed to be the enum value (int)
            return HeroClass(self.progression.hero_class).name.lower()
        except (ValueError, TypeError, AttributeError):
            return "none"

    def _get_weapon_range(self) -> int:
        """Returns the effective weapon range."""
        if not self.inventory or not self.inventory.weapon:
            return 1
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        w = ITEM_REGISTRY.get(self.inventory.weapon)
        return getattr(w, "range", 1) if w else 1

    def copy(self) -> Entity:
        """Fast copy for snapshot generation.
        
        Uses shallow model_copy for aspects because the Snapshot will be 
        pickled (deep copied) before reaching worker threads.
        """
        new_aspects = {}
        for name, aspect in self.aspects.items():
            if hasattr(aspect, "model_copy"):
                # Shallow copy is much faster and safe here as pickle handles the deep copy later
                new_aspects[name] = aspect.model_copy(deep=False)
            elif hasattr(aspect, "copy"):
                new_aspects[name] = aspect.copy()
            else:
                import copy
                new_aspects[name] = copy.copy(aspect)

        new_ent = Entity(
            id=self.id,
            kind=self.kind,
            next_act_at=self.next_act_at,
            aspects=new_aspects
        )
        
        # Re-attach aspects to ensure parent pointers/references are correct
        for aspect in new_ent.aspects.values():
            if hasattr(aspect, "on_attach"):
                aspect.on_attach(new_ent)
                
        return new_ent

from src.core.models.inventory import Inventory
from src.core.models.world_objects import HomeStorage, TreasureChest, CorpseNode

from src.core.aspects.identity import IdentityAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.aspects.combat import CombatAspect
from src.core.aspects.inventory import InventoryAspect
from src.core.aspects.progression import ProgressionAspect
from src.core.aspects.mind import MindAspect

# Resolve forward references for Pydantic
# Rebuild all models to resolve forward references in a safe order
Entity.model_rebuild()

IdentityAspect.model_rebuild()
SpatialAspect.model_rebuild()
CombatAspect.model_rebuild()
InventoryAspect.model_rebuild()
ProgressionAspect.model_rebuild()
MindAspect.model_rebuild()

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/entities/entity_builder.py
"""EntityBuilder — fluent API for constructing Entity instances.

Consolidates duplicated spawn logic from __main__.py, engine_manager.py,
and generator.py into a single, chainable builder.

Usage::

    hero = (
        EntityBuilder(rng, world.allocate_entity_id(), tick=0)
        .kind("hero")
        .at(town_center)
        .with_base_stats(hp=50, atk=10, def_=3, spd=10)
        .with_hero_class(HeroClass.WARRIOR)
        .with_faction(Faction.HERO_GUILD)
        .with_inventory(max_slots=20, max_weight=100, weapon="iron_sword", armor="leather_vest")
        .with_starting_items(["small_hp_potion"] * 3)
        .with_traits(race_prefix="hero")
        .build()
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.gameplay.attributes import Attributes, AttributeCaps, recalc_derived_stats
from src.core.gameplay.classes import (
    CLASS_DEFS, RACE_SKILLS, SKILL_DEFS, SkillInstance,
    available_class_skills,
)
from src.core.models.enums import AIState, Domain, EntityRole
from src.core.gameplay.faction import Faction
from src.core.gameplay.items.items import HomeStorage
from src.core.entities.entity import Entity, Stats, Vector2, Inventory
from src.core.entities.traits import assign_traits

if TYPE_CHECKING:
    from src.platform.rng import DeterministicRNG


class EntityBuilder:
    """Fluent builder for Entity construction.

    All ``with_*`` methods return ``self`` for chaining.
    Call ``build()`` to produce the final Entity.
    """

    __slots__ = (
        "_rng", "_eid", "_tick",
        "_kind", "_pos", "_ai_state", "_faction", "_role",
        "_home_pos", "_leash_radius", "_tier",
        "_base_hp", "_base_atk", "_base_def", "_base_spd",
        "_luck", "_crit_rate", "_crit_dmg", "_evasion",
        "_level", "_xp", "_xp_to_next", "_gold",
        "_hero_class", "_class_def",
        "_attrs", "_caps",
        "_skills", "_inventory", "_home_storage", "_traits",
        "_attr_base", "_attr_randomness",
        "_talents", "_weakness",
        "_display_name", "_generation", "_death_count",
        "_fame", "_titles", "_is_world_boss",
    )

    def __init__(
        self,
        rng: DeterministicRNG,
        entity_id: int,
        tick: int = 0,
    ) -> None:
        self._rng = rng
        self._eid = entity_id
        self._tick = tick

        # Defaults
        self._kind: str = "unknown"
        self._pos: Vector2 = Vector2(0, 0)
        self._ai_state: AIState = AIState.WANDER
        self._faction: Faction = Faction.HERO_GUILD
        self._role: EntityRole = EntityRole.MOB
        self._home_pos: Vector2 | None = None
        self._leash_radius: int = 0
        self._tier: int = 0

        self._base_hp: int = 20
        self._base_atk: int = 5
        self._base_def: int = 0
        self._base_spd: int = 10
        self._luck: int = 0
        self._crit_rate: float = 0.05
        self._crit_dmg: float = 1.5
        self._evasion: float = 0.0
        self._level: int = 1
        self._xp: int = 0
        self._xp_to_next: int = 100
        self._gold: int = 0
        self._fame: int = 0
        self._titles: list[str] = []
        self._is_world_boss: bool = False

        self._hero_class: int | None = None
        self._class_def = None
        self._attrs: Attributes | None = None
        self._caps: AttributeCaps | None = None
        self._skills: list[SkillInstance] = []
        self._inventory: Inventory | None = None
        self._home_storage: HomeStorage | None = None
        self._traits: list[int] = []
        self._talents: list[str] | None = None
        self._weakness: str | None = None
        self._display_name: str = ""
        self._generation: int = 1
        self._death_count: int = 0

    # -------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------

    def kind(self, kind_str: str) -> EntityBuilder:
        self._kind = kind_str
        return self

    def with_identity(self, display_name: str = "", generation: int = 1, death_count: int = 0) -> EntityBuilder:
        self._display_name = display_name
        self._generation = generation
        self._death_count = death_count
        return self

    def at(self, pos: Vector2) -> EntityBuilder:
        self._pos = pos
        return self

    def home(self, pos: Vector2 | None) -> EntityBuilder:
        self._home_pos = pos
        return self

    def leash(self, radius: int) -> EntityBuilder:
        self._leash_radius = radius
        return self

    def ai_state(self, state: AIState) -> EntityBuilder:
        self._ai_state = state
        return self

    def faction(self, f: Faction) -> EntityBuilder:
        self._faction = f
        return self

    def role(self, r: EntityRole) -> EntityBuilder:
        self._role = r
        return self

    def tier(self, t: int) -> EntityBuilder:
        self._tier = t
        return self

    def is_world_boss(self, val: bool) -> EntityBuilder:
        self._is_world_boss = val
        return self

    # -------------------------------------------------------------------
    # Base stats
    # -------------------------------------------------------------------

    def with_base_stats(
        self, *,
        hp: int = 20, atk: int = 5, def_: int = 0, spd: int = 10,
        luck: int = 0, crit_rate: float = 0.05, crit_dmg: float = 1.5,
        evasion: float = 0.0, level: int = 1, xp_to_next: int = 100,
        gold: int = 0, fame: int = 0,
    ) -> EntityBuilder:
        self._base_hp = hp
        self._base_atk = atk
        self._base_def = def_
        self._base_spd = spd
        self._luck = luck
        self._crit_rate = crit_rate
        self._crit_dmg = crit_dmg
        self._evasion = evasion
        self._level = level
        self._xp_to_next = xp_to_next
        self._gold = gold
        self._fame = fame
        return self

    def titles(self, t_list: list[str]) -> EntityBuilder:
        self._titles = list(t_list)
        return self

    def with_randomized_stats(self) -> EntityBuilder:
        """Add RNG variance to base stats (typical for hero spawns)."""
        eid = self._eid
        self._base_hp += self._rng.next_int(Domain.SPAWN, eid, self._tick + 2, 0, 15)
        self._base_atk += self._rng.next_int(Domain.SPAWN, eid, self._tick + 3, 0, 4)
        self._base_spd += self._rng.next_int(Domain.SPAWN, eid, self._tick + 4, 0, 3)
        self._base_def += self._rng.next_int(Domain.SPAWN, eid, self._tick + 5, 0, 2)
        return self

    # -------------------------------------------------------------------
    # Hero class + attributes
    # -------------------------------------------------------------------

    def with_attributes(self, **kwargs) -> EntityBuilder:
        """Manually set or override specific attributes."""
        if self._attrs is None:
            self._attrs = Attributes(str_=5, agi=5, vit=5, int_=5, spi=5, wis=5, end=5, per=5, cha=5)
        for k, v in kwargs.items():
            if hasattr(self._attrs, k):
                setattr(self._attrs, k, v)
        return self

    def with_caps(self, **kwargs) -> EntityBuilder:
        """Manually set or override specific attribute caps."""
        if self._caps is None:
            self._caps = AttributeCaps()
        for k, v in kwargs.items():
            if hasattr(self._caps, k):
                setattr(self._caps, k, v)
        return self

    def with_hero_class(self, hero_class) -> EntityBuilder:
        """Set hero class and derive attributes from class definition."""
        self._hero_class = int(hero_class)
        self._class_def = CLASS_DEFS.get(hero_class)
        if self._class_def:
            cdef = self._class_def
            eid = self._eid
            rng = self._rng
            tick = self._tick
            self._attrs = Attributes(
                str_=5 + cdef.str_bonus + rng.next_int(Domain.SPAWN, eid, tick + 10, 0, 2),
                agi=5 + cdef.agi_bonus + rng.next_int(Domain.SPAWN, eid, tick + 11, 0, 2),
                vit=5 + cdef.vit_bonus + rng.next_int(Domain.SPAWN, eid, tick + 12, 0, 2),
                int_=5 + cdef.int_bonus + rng.next_int(Domain.SPAWN, eid, tick + 13, 0, 2),
                spi=5 + cdef.spi_bonus + rng.next_int(Domain.SPAWN, eid, tick + 16, 0, 2),
                wis=5 + cdef.wis_bonus + rng.next_int(Domain.SPAWN, eid, tick + 14, 0, 2),
                end=5 + cdef.end_bonus + rng.next_int(Domain.SPAWN, eid, tick + 15, 0, 2),
                per=5 + cdef.per_bonus + rng.next_int(Domain.SPAWN, eid, tick + 17, 0, 2),
                cha=5 + cdef.cha_bonus + rng.next_int(Domain.SPAWN, eid, tick + 18, 0, 2),
            )
            self._caps = AttributeCaps(
                str_cap=15 + cdef.str_cap_bonus, agi_cap=15 + cdef.agi_cap_bonus,
                vit_cap=15 + cdef.vit_cap_bonus, int_cap=15 + cdef.int_cap_bonus,
                spi_cap=15 + cdef.spi_cap_bonus, wis_cap=15 + cdef.wis_cap_bonus,
                end_cap=15 + cdef.end_cap_bonus, per_cap=15 + cdef.per_cap_bonus,
                cha_cap=15 + cdef.cha_cap_bonus,
            )
        return self

    def with_mob_class(self, mob_class) -> EntityBuilder:
        """Set mob archetype class."""
        self._hero_class = int(mob_class)
        self._class_def = CLASS_DEFS.get(mob_class)
        return self

    def with_mob_attributes(self, attr_base: int, tier: int) -> EntityBuilder:
        """Generate mob-style attributes scaled by tier + class bonuses."""
        eid = self._eid
        rng = self._rng
        tick = self._tick
        cd = self._class_def
        c_str = cd.str_bonus if cd else 0
        c_agi = cd.agi_bonus if cd else 0
        c_vit = cd.vit_bonus if cd else 0
        c_int = cd.int_bonus if cd else 0
        c_spi = cd.spi_bonus if cd else 0
        c_wis = cd.wis_bonus if cd else 0
        c_end = cd.end_bonus if cd else 0
        c_per = cd.per_bonus if cd else 0
        c_cha = cd.cha_bonus if cd else 0
        self._attrs = Attributes(
            str_=max(1, attr_base + c_str + rng.next_int(Domain.SPAWN, eid, tick + 20, 0, 3)),
            agi=max(1, attr_base + c_agi + rng.next_int(Domain.SPAWN, eid, tick + 21, 0, 3)),
            vit=max(1, attr_base + c_vit + rng.next_int(Domain.SPAWN, eid, tick + 22, 0, 3)),
            int_=max(1, attr_base - 2 + c_int + rng.next_int(Domain.SPAWN, eid, tick + 23, 0, 2)),
            spi=max(1, attr_base - 2 + c_spi + rng.next_int(Domain.SPAWN, eid, tick + 26, 0, 2)),
            wis=max(1, attr_base - 2 + c_wis + rng.next_int(Domain.SPAWN, eid, tick + 24, 0, 2)),
            end=max(1, attr_base + c_end + rng.next_int(Domain.SPAWN, eid, tick + 25, 0, 3)),
            per=max(1, attr_base - 1 + c_per + rng.next_int(Domain.SPAWN, eid, tick + 27, 0, 2)),
            cha=max(1, attr_base - 3 + c_cha + rng.next_int(Domain.SPAWN, eid, tick + 28, 0, 2)),
        )
        cc_str = cd.str_cap_bonus if cd else 0
        cc_agi = cd.agi_cap_bonus if cd else 0
        cc_vit = cd.vit_cap_bonus if cd else 0
        cc_int = cd.int_cap_bonus if cd else 0
        cc_spi = cd.spi_cap_bonus if cd else 0
        cc_wis = cd.wis_cap_bonus if cd else 0
        cc_end = cd.end_cap_bonus if cd else 0
        cc_per = cd.per_cap_bonus if cd else 0
        cc_cha = cd.cha_cap_bonus if cd else 0
        self._caps = AttributeCaps(
            str_cap=15 + tier * 5 + cc_str, agi_cap=15 + tier * 5 + cc_agi,
            vit_cap=15 + tier * 5 + cc_vit, int_cap=10 + tier * 3 + cc_int,
            spi_cap=10 + tier * 3 + cc_spi, wis_cap=10 + tier * 3 + cc_wis,
            end_cap=15 + tier * 5 + cc_end, per_cap=10 + tier * 3 + cc_per,
            cha_cap=8 + tier * 2 + cc_cha,
        )
        return self

    def with_race_attributes(
        self, attr_base: int, tier: int,
        r_str: int = 0, r_agi: int = 0, r_vit: int = 0,
        r_spi: int = 0, r_per: int = 0, r_cha: int = 0,
    ) -> EntityBuilder:
        """Generate race-specific attributes with racial + class modifiers."""
        eid = self._eid
        rng = self._rng
        tick = self._tick
        cd = self._class_def
        c_str = cd.str_bonus if cd else 0
        c_agi = cd.agi_bonus if cd else 0
        c_vit = cd.vit_bonus if cd else 0
        c_int = cd.int_bonus if cd else 0
        c_spi = cd.spi_bonus if cd else 0
        c_wis = cd.wis_bonus if cd else 0
        c_end = cd.end_bonus if cd else 0
        c_per = cd.per_bonus if cd else 0
        c_cha = cd.cha_bonus if cd else 0
        self._attrs = Attributes(
            str_=max(1, attr_base + r_str + c_str + rng.next_int(Domain.SPAWN, eid, tick + 20, 0, 3)),
            agi=max(1, attr_base + r_agi + c_agi + rng.next_int(Domain.SPAWN, eid, tick + 21, 0, 3)),
            vit=max(1, attr_base + r_vit + c_vit + rng.next_int(Domain.SPAWN, eid, tick + 22, 0, 3)),
            int_=max(1, attr_base - 2 + c_int + rng.next_int(Domain.SPAWN, eid, tick + 23, 0, 2)),
            spi=max(1, attr_base - 2 + r_spi + c_spi + rng.next_int(Domain.SPAWN, eid, tick + 26, 0, 2)),
            wis=max(1, attr_base - 2 + c_wis + rng.next_int(Domain.SPAWN, eid, tick + 24, 0, 2)),
            end=max(1, attr_base + c_end + rng.next_int(Domain.SPAWN, eid, tick + 25, 0, 3)),
            per=max(1, attr_base - 1 + r_per + c_per + rng.next_int(Domain.SPAWN, eid, tick + 27, 0, 2)),
            cha=max(1, attr_base - 3 + r_cha + c_cha + rng.next_int(Domain.SPAWN, eid, tick + 28, 0, 2)),
        )
        cc_str = cd.str_cap_bonus if cd else 0
        cc_agi = cd.agi_cap_bonus if cd else 0
        cc_vit = cd.vit_cap_bonus if cd else 0
        cc_int = cd.int_cap_bonus if cd else 0
        cc_spi = cd.spi_cap_bonus if cd else 0
        cc_wis = cd.wis_cap_bonus if cd else 0
        cc_end = cd.end_cap_bonus if cd else 0
        cc_per = cd.per_cap_bonus if cd else 0
        cc_cha = cd.cha_cap_bonus if cd else 0
        self._caps = AttributeCaps(
            str_cap=15 + tier * 5 + cc_str, agi_cap=15 + tier * 5 + cc_agi,
            vit_cap=15 + tier * 5 + cc_vit, int_cap=10 + tier * 3 + cc_int,
            spi_cap=10 + tier * 3 + cc_spi, wis_cap=10 + tier * 3 + cc_wis,
            end_cap=15 + tier * 5 + cc_end, per_cap=10 + tier * 3 + cc_per,
            cha_cap=8 + tier * 2 + cc_cha,
        )
        return self

    # -------------------------------------------------------------------
    # Skills
    # -------------------------------------------------------------------

    def with_race_skills(self, race: str) -> EntityBuilder:
        """Add skills from the race skill table."""
        for sid in RACE_SKILLS.get(race, []):
            if sid in SKILL_DEFS:
                self._skills.append(SkillInstance(skill_id=sid))
        return self

    def with_class_skills(self, hero_class, level: int = 1) -> EntityBuilder:
        """Add class skills available at the given level."""
        for sid in available_class_skills(hero_class, level):
            self._skills.append(SkillInstance(skill_id=sid))
        return self

    # -------------------------------------------------------------------
    # Inventory
    # -------------------------------------------------------------------

    def with_inventory(
        self, *,
        max_slots: int = 10,
        max_weight: int = 50,
        weapon: str | None = None,
        armor: str | None = None,
        accessory: str | None = None,
    ) -> EntityBuilder:
        self._inventory = Inventory(
            items=[], max_slots=max_slots, max_weight=max_weight,
            weapon=weapon, armor=armor, accessory=accessory,
        )
        return self

    def with_starting_items(self, item_ids: list[str]) -> EntityBuilder:
        """Add starting items."""
        if self._inventory:
            for item_id in item_ids:
                self._inventory.add_item(item_id)
        return self

    def with_existing_inventory(self, inv: Inventory) -> EntityBuilder:
        self._inventory = inv
        return self

    def with_equipment(
        self, *,
        weapon: str | None = None,
        armor: str | None = None,
        accessory: str | None = None,
    ) -> EntityBuilder:
        if self._inventory:
            if weapon:
                self._inventory.weapon = weapon
            if armor:
                self._inventory.armor = armor
            if accessory:
                self._inventory.accessory = accessory
        return self

    # -------------------------------------------------------------------
    # Traits + Talents
    # -------------------------------------------------------------------

    def with_home_storage(self, max_slots: int = 30) -> EntityBuilder:
        self._home_storage = HomeStorage(max_slots=max_slots)
        return self

    def with_traits(self, race_prefix: str = "", trait_ids: list[int] | None = None) -> EntityBuilder:
        if trait_ids is not None:
            self._traits = trait_ids
        else:
            self._traits = assign_traits(
                self._rng, Domain.SPAWN, self._eid, self._tick,
                race_prefix=race_prefix,
            )
        return self

    def with_talents(self, race: str = "") -> EntityBuilder:
        """Assign 2 random talents and 1 weakness."""
        race = race or self._kind
        attributes = ["str", "agi", "vit", "int", "spi", "wis", "end", "per", "cha"]
        weights = [1.0] * 9
        if "orc" in race: weights[0] = 5.0; weights[2] = 5.0
        elif "wolf" in race: weights[1] = 5.0; weights[7] = 3.0
        elif "undead" in race: weights[2] = 5.0; weights[4] = 3.0
        
        t1 = self._rng.weighted_choice(Domain.SPAWN, self._eid, self._tick + 30, attributes, weights)
        remaining = [a for a in attributes if a != t1]
        rem_weights = [weights[attributes.index(a)] for a in remaining]
        t2 = self._rng.weighted_choice(Domain.SPAWN, self._eid, self._tick + 31, remaining, rem_weights)
        self._talents = [t1, t2]
        
        remaining_weak = [a for a in attributes if a not in self._talents]
        inv_weights = [1.0 / weights[attributes.index(a)] for a in remaining_weak]
        self._weakness = self._rng.weighted_choice(Domain.SPAWN, self._eid, self._tick + 32, remaining_weak, inv_weights)
        
        return self

    # -------------------------------------------------------------------
    # Build
    # -------------------------------------------------------------------

    def _init_aspects(self) -> dict[str, Any]:
        """Create Aspect instances from builder data."""
        from src.core.aspects.identity import IdentityAspect
        from src.core.aspects.spatial import SpatialAspect
        from src.core.aspects.combat import CombatAspect
        from src.core.aspects.progression import ProgressionAspect
        from src.core.aspects.inventory import InventoryAspect
        from src.core.aspects.mind import MindAspect
        
        stamina = 50 if self._kind == "hero" else 30
        
        combat = CombatAspect(
            hp=self._base_hp, max_hp=self._base_hp,
            atk=self._base_atk, def_=self._base_def, spd=self._base_spd,
            luck=self._luck, crit_rate=self._crit_rate, crit_dmg=self._crit_dmg,
            evasion=self._evasion,
        )
        
        prog = ProgressionAspect(
            level=self._level, xp_to_next=self._xp_to_next,
            gold=self._gold, fame=self._fame,
            stamina=stamina, max_stamina=stamina,
            hero_class=self._hero_class or 0,
            skills=self._skills,
            attributes=self._attrs,
            attribute_caps=self._caps,
            talents=self._talents or [],
        )
        
        if self._attrs:
            from src.core.gameplay.attributes import recalc_derived_stats
            recalc_derived_stats(combat, self._attrs)
            combat.hp = combat.max_hp
        
        # logger already imported or need to add it?
        # Check imports in entity_builder.py
        identity = IdentityAspect(
            display_name=self._display_name or self._kind,
            faction=self._faction,
            role=self._role,
            tier=self._tier,
            traits=list(self._traits),
            is_world_boss=self._is_world_boss,
            death_count=self._death_count,
            generation=self._generation,
        )

        aspects = {
            "identity": identity,
            "spatial": SpatialAspect(
                pos=self._pos,
                region_id="unknown", 
                difficulty_tier=0, 
                home_pos=self._home_pos,
                leash_radius=self._leash_radius,
            ),
            "combat": combat,
            "progression": prog,
            "mind": MindAspect(
                ai_state=self._ai_state,
                next_act_at=self._tick or 0
            ),
        }

        # Only add inventory if configured
        if self._inventory:
            inv_aspect = InventoryAspect()
            inv_aspect.items = list(self._inventory.items)
            inv_aspect.max_slots = self._inventory.max_slots
            inv_aspect.max_weight = self._inventory.max_weight
            inv_aspect.weapon = self._inventory.weapon
            inv_aspect.armor = self._inventory.armor
            inv_aspect.accessory = self._inventory.accessory
            
            aspects["inventory"] = inv_aspect

        return aspects

    def build(self) -> Entity:
        """Construct and return the final Entity."""
        aspects_dict = self._init_aspects()
        
        entity = Entity(
            id=self._eid,
            kind=self._kind,
            aspects=aspects_dict
        )
        
        # Attach aspects to the entity
        for aspect in aspects_dict.values():
            aspect.on_attach(entity)
            
        return entity

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/entities/stats.py
from __future__ import annotations
from dataclasses import dataclass, field
from src.core.models.enums import Element

@dataclass(slots=True)
class Stats:
    """Mutable combat statistics for an entity."""

    # --- Core combat ---
    hp: int = 20
    max_hp: int = 20
    atk: int = 5
    def_: int = 0
    spd: int = 10
    luck: int = 0
    crit_rate: float = 0.05
    crit_dmg: float = 1.5
    evasion: float = 0.0

    # --- Magic combat ---
    matk: int = 5           # Magic attack power
    mdef: int = 0           # Magic defense

    # --- Elemental vulnerability table ---
    elem_vuln: dict[int, float] = field(default_factory=lambda: {
        Element.FIRE: 1.0,
        Element.ICE: 1.0,
        Element.LIGHTNING: 1.0,
        Element.DARK: 1.0,
        Element.HOLY: 1.0,
    })

    # --- Progression ---
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    gold: int = 0
    fame: int = 0
    stamina: int = 50
    max_stamina: int = 50

    # --- Secondary / non-combat ---
    vision_range: int = 6
    loot_bonus: float = 1.0
    trade_bonus: float = 1.0
    interaction_speed: float = 1.0
    rest_efficiency: float = 1.0
    hp_regen: float = 1.0
    cooldown_reduction: float = 1.0

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def hp_ratio(self) -> float:
        if self.max_hp <= 0:
            return 0.0
        return max(0.0, min(1.0, self.hp / self.max_hp))

    @property
    def stamina_ratio(self) -> float:
        return self.stamina / self.max_stamina if self.max_stamina > 0 else 0.0

    def copy(self) -> Stats:
        return Stats(
            hp=self.hp, max_hp=self.max_hp, atk=self.atk, def_=self.def_,
            spd=self.spd, luck=self.luck, crit_rate=self.crit_rate,
            crit_dmg=self.crit_dmg, evasion=self.evasion,
            matk=self.matk, mdef=self.mdef,
            elem_vuln=dict(self.elem_vuln),
            level=self.level, xp=self.xp, xp_to_next=self.xp_to_next,
            gold=self.gold, fame=self.fame, 
            stamina=self.stamina, max_stamina=self.max_stamina,
            vision_range=self.vision_range, loot_bonus=self.loot_bonus,
            trade_bonus=self.trade_bonus,
            interaction_speed=self.interaction_speed,
            rest_efficiency=self.rest_efficiency,
            hp_regen=self.hp_regen,
            cooldown_reduction=self.cooldown_reduction,
        )

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/entities/stats_proxy.py
from __future__ import annotations
from typing import TYPE_CHECKING, Any
from src.core.models.enums import Element

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

class StatsProxy:
    """Entry point for effective stats. Partitioned by Domain/Aspect."""
    __slots__ = ("combat", "progression")

    def __init__(self, entity: Entity) -> None:
        self.combat = StatsProxyCombat(entity)
        self.progression = StatsProxyProgression(entity)

    # --- Top-Level Shims for Legacy Compatibility ---
    @property
    def hp(self) -> int: return self.combat.hp
    @hp.setter
    def hp(self, v: int): self.combat.hp = v

    @property
    def max_hp(self) -> int: return self.combat.max_hp
    @max_hp.setter
    def max_hp(self, v: int): self.combat.max_hp = v

    @property
    def atk(self) -> int: return self.combat.atk
    @atk.setter
    def atk(self, v: int): self.combat.atk = v

    @property
    def def_(self) -> int: return self.combat.def_
    @def_.setter
    def def_(self, v: int): self.combat.def_ = v

    @property
    def spd(self) -> int: return self.combat.spd
    @spd.setter
    def spd(self, v: int): self.combat.spd = v

    @property
    def vision_range(self) -> int: return self.combat.vision_range
    @vision_range.setter
    def vision_range(self, v: int): self.combat.vision_range = v

    @property
    def level(self) -> int: return self.progression.level
    @level.setter
    def level(self, v: int): self.progression.level = v

    @property
    def gold(self) -> int: return self.progression.gold
    @gold.setter
    def gold(self, v: int): self.progression.gold = v

    @property
    def xp(self) -> int: return self.progression.xp
    @xp.setter
    def xp(self, v: int): self.progression.xp = v

    @property
    def xp_to_next(self) -> int: return self.progression.xp_to_next
    @xp_to_next.setter
    def xp_to_next(self, v: int): self.progression.xp_to_next = v

    @property
    def fame(self) -> int: return self.progression.fame
    @fame.setter
    def fame(self, v: int): self.progression.fame = v

    @property
    def stamina(self) -> int: return self.progression.stamina
    @stamina.setter
    def stamina(self, v: int): self.progression.stamina = v

    @property
    def max_stamina(self) -> int: return self.progression.max_stamina
    @max_stamina.setter
    def max_stamina(self, v: int): self.progression.max_stamina = v

    @property
    def matk(self) -> int: return self.combat.matk
    @matk.setter
    def matk(self, v: int): self.combat.matk = v

    @property
    def mdef(self) -> int: return self.combat.mdef
    @mdef.setter
    def mdef(self, v: int): self.combat.mdef = v

    @property
    def luck(self) -> int: return self.combat.luck
    @luck.setter
    def luck(self, v: int): self.combat.luck = v

    @property
    def crit_rate(self) -> float: return self.combat.crit_rate
    @crit_rate.setter
    def crit_rate(self, v: float): self.combat.crit_rate = v

    @property
    def crit_dmg(self) -> float: return self.combat.crit_dmg
    @crit_dmg.setter
    def crit_dmg(self, v: float): self.combat.crit_dmg = v

    @property
    def evasion(self) -> float: return self.combat.evasion
    @evasion.setter
    def evasion(self, v: float): self.combat.evasion = v

    @property
    def hp_regen(self) -> float: return self.combat.hp_regen
    @hp_regen.setter
    def hp_regen(self, v: float): self.combat.hp_regen = v

    @property
    def loot_bonus(self) -> float: return self.combat.loot_bonus
    @loot_bonus.setter
    def loot_bonus(self, v: float): self.combat.loot_bonus = v

    @property
    def trade_bonus(self) -> float: return self.combat.trade_bonus
    @trade_bonus.setter
    def trade_bonus(self, v: float): self.combat.trade_bonus = v

    @property
    def interaction_speed(self) -> float: return self.combat.interaction_speed
    @interaction_speed.setter
    def interaction_speed(self, v: float): self.combat.interaction_speed = v

    @property
    def rest_efficiency(self) -> float: return self.combat.rest_efficiency
    @rest_efficiency.setter
    def rest_efficiency(self, v: float): self.combat.rest_efficiency = v

    @property
    def cooldown_reduction(self) -> float: return self.combat.cooldown_reduction
    @cooldown_reduction.setter
    def cooldown_reduction(self, v: float): self.combat.cooldown_reduction = v

    @property
    def stamina_ratio(self) -> float: return self.progression.stamina_ratio
    @property
    def xp_ratio(self) -> float: return self.progression.xp_ratio

    # --- Primary Attributes Shims ---
    @property
    def str(self) -> int: return self.progression.str
    @str.setter
    def str(self, v: int): self.progression.str = v

    @property
    def agi(self) -> int: return self.progression.agi
    @agi.setter
    def agi(self, v: int): self.progression.agi = v

    @property
    def vit(self) -> int: return self.progression.vit
    @vit.setter
    def vit(self, v: int): self.progression.vit = v

    @property
    def int(self) -> int: return self.progression.int
    @int.setter
    def int(self, v: int): self.progression.int = v

    @property
    def spi(self) -> int: return self.progression.spi
    @spi.setter
    def spi(self, v: int): self.progression.spi = v

    @property
    def wis(self) -> int: return self.progression.wis
    @wis.setter
    def wis(self, v: int): self.progression.wis = v

    @property
    def end(self) -> int: return self.progression.end
    @end.setter
    def end(self, v: int): self.progression.end = v

    @property
    def per(self) -> int: return self.progression.per
    @per.setter
    def per(self, v: int): self.progression.per = v

    @property
    def cha(self) -> int: return self.progression.cha
    @cha.setter
    def cha(self, v: int): self.progression.cha = v

class StatsProxyCombat:
    """Effective stats for Combat domain."""
    __slots__ = ("_entity",)
    def __init__(self, entity: Entity) -> None:
        self._entity = entity

    @property
    def atk(self) -> int:
        ent = self._entity
        base = ent.combat.atk
        if hasattr(ent, "inventory_aspect") and ent.inventory_aspect:
            base += int(ent.inventory_aspect.equipment_bonus("atk_bonus"))
        mult = self._effect_mult("atk_mult") * self._veterancy_mult("atk") * self._bravery_mult("atk")
        return max(int(base * mult), 1)

    @atk.setter
    def atk(self, value: int) -> None:
        self._entity.combat.atk = value

    @property
    def def_(self) -> int:
        ent = self._entity
        base = ent.combat.def_
        if hasattr(ent, "inventory_aspect") and ent.inventory_aspect:
            base += int(ent.inventory_aspect.equipment_bonus("def_bonus"))
        mult = self._effect_mult("def_mult") * self._veterancy_mult("def") * self._bravery_mult("def")
        return max(int(base * mult), 0)

    @def_.setter
    def def_(self, value: int) -> None:
        self._entity.combat.def_ = value

    @property
    def spd(self) -> int:
        ent = self._entity
        base = ent.combat.spd
        if hasattr(ent, "inventory_aspect") and ent.inventory_aspect:
            base += int(ent.inventory_aspect.equipment_bonus("spd_bonus"))
        mult = self._effect_mult("spd_mult") * self._veterancy_mult("spd") * self._bravery_mult("spd")
        return max(int(base * mult), 1)

    @spd.setter
    def spd(self, value: int) -> None:
        self._entity.combat.spd = value

    @property
    def max_hp(self) -> int:
        ent = self._entity
        base = ent.combat.max_hp
        if hasattr(ent, "inventory_aspect") and ent.inventory_aspect:
            base += int(ent.inventory_aspect.equipment_bonus("hp_bonus"))
        mult = self._effect_mult("max_hp_mult") * self._veterancy_mult("hp")
        return max(int(base * mult), 1)
    @property
    def mdef(self) -> int: return self._entity.combat.mdef
    @mdef.setter
    def mdef(self, v: int): self._entity.combat.mdef = v

    @property
    def matk(self) -> int: return self._entity.combat.matk
    @matk.setter
    def matk(self, v: int): self._entity.combat.matk = v

    @property
    def luck(self) -> int: return self._entity.combat.luck
    @luck.setter
    def luck(self, v: int): self._entity.combat.luck = v

    @property
    def crit_rate(self) -> float: return self._entity.combat.crit_rate
    @crit_rate.setter
    def crit_rate(self, v: float): self._entity.combat.crit_rate = v

    @property
    def crit_dmg(self) -> float: return self._entity.combat.crit_dmg
    @crit_dmg.setter
    def crit_dmg(self, v: float): self._entity.combat.crit_dmg = v

    @property
    def evasion(self) -> float: return self._entity.combat.evasion
    @evasion.setter
    def evasion(self, v: float): self._entity.combat.evasion = v

    @property
    def hp_regen(self) -> float: return self._entity.combat.hp_regen
    @hp_regen.setter
    def hp_regen(self, v: float): self._entity.combat.hp_regen = v

    @max_hp.setter
    def max_hp(self, value: int) -> None:
        self._entity.combat.max_hp = value

    @property
    def hp(self) -> int: return self._entity.combat.hp
    @hp.setter
    def hp(self, value: int): self._entity.combat.hp = value
    
    @property
    def hp_ratio(self) -> float: return self._entity.combat.hp_ratio

    @property
    def vision_range(self) -> int: return self._entity.combat.vision_range
    @vision_range.setter
    def vision_range(self, v: int): self._entity.combat.vision_range = v

    @property
    def loot_bonus(self) -> float: return self._entity.combat.loot_bonus
    @loot_bonus.setter
    def loot_bonus(self, v: float): self._entity.combat.loot_bonus = v

    @property
    def trade_bonus(self) -> float: return self._entity.combat.trade_bonus
    @trade_bonus.setter
    def trade_bonus(self, v: float): self._entity.combat.trade_bonus = v

    @property
    def interaction_speed(self) -> float: return self._entity.combat.interaction_speed
    @interaction_speed.setter
    def interaction_speed(self, v: float): self._entity.combat.interaction_speed = v

    @property
    def rest_efficiency(self) -> float: return self._entity.combat.rest_efficiency
    @rest_efficiency.setter
    def rest_efficiency(self, v: float): self._entity.combat.rest_efficiency = v

    @property
    def cooldown_reduction(self) -> float: return self._entity.combat.cooldown_reduction
    @cooldown_reduction.setter
    def cooldown_reduction(self, v: float): self._entity.combat.cooldown_reduction = v

    def _effect_mult(self, attr: str) -> float:
        m = 1.0
        for eff in self._entity.combat.effects:
            v = getattr(eff, attr, 1.0)
            if v is not None: m *= v
        return m

    def _veterancy_mult(self, stat: str) -> float:
        rank = self._entity.progression.veterancy_rank
        if rank <= 0: return 1.0
        elif rank == 1: return 1.03 if stat in ("atk", "def") else 1.0
        elif rank == 2:
            if stat in ("atk", "def"): return 1.06
            return 1.05 if stat == "hp" else 1.0
        elif rank == 3:
            if stat in ("atk", "def", "hp"): return 1.10
            return 1.05 if stat == "spd" else 1.0
        return 1.15

    def _bravery_mult(self, stat: str) -> float:
        bravery = self._entity.mind.emotional_state.get("bravery", 0.5)
        if bravery > 0.8:
            if stat in ("atk", "spd"): return 1.1
        elif bravery < 0.3:
            if stat in ("atk", "def", "spd"): return 0.9
        return 1.0

class StatsProxyProgression:
    """Effective stats for Progression domain."""
    __slots__ = ("_entity",)
    def __init__(self, entity: Entity) -> None:
        self._entity = entity

    @property
    def level(self) -> int: return self._entity.progression.level
    @level.setter
    def level(self, v: int): self._entity.progression.level = v

    @property
    def gold(self) -> int: return self._entity.progression.gold
    @gold.setter
    def gold(self, v: int): self._entity.progression.gold = v

    @property
    def xp(self) -> int: return self._entity.progression.xp
    @xp.setter
    def xp(self, v: int): self._entity.progression.xp = v

    @property
    def xp_to_next(self) -> int: return self._entity.progression.xp_to_next
    @xp_to_next.setter
    def xp_to_next(self, v: int): self._entity.progression.xp_to_next = v

    @property
    def fame(self) -> int: return self._entity.progression.fame
    @fame.setter
    def fame(self, v: int): self._entity.progression.fame = v

    @property
    def stamina(self) -> int: return self._entity.progression.stamina
    @stamina.setter
    def stamina(self, v: int): self._entity.progression.stamina = v

    @property
    def max_stamina(self) -> int: return self._entity.progression.max_stamina
    @max_stamina.setter
    def max_stamina(self, v: int): self._entity.progression.max_stamina = v

    @property
    def stamina_ratio(self) -> float: return self._entity.progression.stamina_ratio
    @property
    def xp_ratio(self) -> float: return self._entity.progression.xp_ratio

    @property
    def xp_mult(self) -> float:
        from src.core.gameplay.attributes import derive_xp_multiplier
        attrs = self._entity.progression.attributes
        if not attrs: 
            return 1.0 * self._effect_mult("xp_mult")
        mult = derive_xp_multiplier(attrs.wis, attrs.int_)
        return mult * self._effect_mult("xp_mult")

    def _effect_mult(self, attr: str) -> float:
        m = 1.0
        # XP mult is influenced by effects on the combat aspect (where statuses live)
        for eff in self._entity.combat.effects:
            v = getattr(eff, attr, 1.0)
            if v is not None: m *= v
        return m

    # --- Attributes Shims ---
    @property
    def str(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.str_ if attrs else 5
    @str.setter
    def str(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.str_ = v

    @property
    def agi(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.agi if attrs else 5
    @agi.setter
    def agi(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.agi = v

    @property
    def vit(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.vit if attrs else 5
    @vit.setter
    def vit(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.vit = v

    @property
    def int(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.int_ if attrs else 5
    @int.setter
    def int(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.int_ = v

    @property
    def spi(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.spi if attrs else 5
    @spi.setter
    def spi(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.spi = v

    @property
    def wis(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.wis if attrs else 5
    @wis.setter
    def wis(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.wis = v

    @property
    def end(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.end if attrs else 5
    @end.setter
    def end(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.end = v

    @property
    def per(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.per if attrs else 5
    @per.setter
    def per(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.per = v

    @property
    def cha(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.cha if attrs else 5
    @cha.setter
    def cha(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.cha = v

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/entities/traits.py
"""Trait system — Rimworld-style discrete personality traits.

Each entity gets 2-4 traits at spawn.  Traits modify utility scores
in the AI goal-evaluation layer and can provide passive stat bonuses.

Incompatible trait pairs (e.g. AGGRESSIVE + CAUTIOUS) are enforced
during assignment so an entity never has contradictory personality.

Key types:
  TraitDef          — immutable blueprint for one trait
  UtilityBonus      — typed additive modifiers for goal scoring
  TraitStatModifiers— typed passive stat modifiers
  TraitRegistry     — central registry for definitions, compatibility, race bias
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING

from pydantic.dataclasses import dataclass as pydantic_dataclass

from src.core.models.enums import TraitType

if TYPE_CHECKING:
    from src.platform.rng import DeterministicRNG


# ---------------------------------------------------------------------------
# Trait definition
# ---------------------------------------------------------------------------

@pydantic_dataclass(frozen=True)
class TraitDef:
    """Immutable blueprint describing one trait's effects."""

    trait_type: int          # TraitType enum value
    name: str
    description: str
    # Utility score modifiers (additive bonuses to goal utility)
    combat_utility: float = 0.0     # Hunt/attack goal
    flee_utility: float = 0.0       # Flee/retreat goal
    explore_utility: float = 0.0    # Explore/wander goal
    loot_utility: float = 0.0       # Loot/gather goal
    trade_utility: float = 0.0      # Shop/trade goal
    rest_utility: float = 0.0       # Rest/heal goal
    craft_utility: float = 0.0      # Craft/harvest goal
    social_utility: float = 0.0     # Guild/interact goal
    # Passive stat multipliers (1.0 = no change)
    atk_mult: float = 1.0
    def_mult: float = 1.0
    matk_mult: float = 1.0
    mdef_mult: float = 1.0
    crit_bonus: float = 0.0
    evasion_bonus: float = 0.0
    vision_bonus: int = 0
    hp_regen_mult: float = 1.0
    interaction_speed_mult: float = 1.0
    # Elemental damage bonus multipliers (1.0 = no change, >1 = bonus dmg)
    fire_dmg_mult: float = 1.0
    ice_dmg_mult: float = 1.0
    lightning_dmg_mult: float = 1.0
    dark_dmg_mult: float = 1.0
    # Flee HP threshold modifier (additive; positive = flee sooner)
    flee_threshold_mod: float = 0.0


# ---------------------------------------------------------------------------
# Trait registry
# ---------------------------------------------------------------------------

TRAIT_DEFS: dict[int, TraitDef] = {}





# ---------------------------------------------------------------------------
# Incompatible pairs — entities cannot have both traits
# ---------------------------------------------------------------------------

INCOMPATIBLE_PAIRS: list[tuple[int, int]] = [
    (TraitType.AGGRESSIVE, TraitType.CAUTIOUS),
    (TraitType.AGGRESSIVE, TraitType.COWARDLY),
    (TraitType.BRAVE, TraitType.COWARDLY),
    (TraitType.BLOODTHIRSTY, TraitType.CAUTIOUS),
    (TraitType.GREEDY, TraitType.GENEROUS),
    (TraitType.DILIGENT, TraitType.LAZY),
    (TraitType.BERSERKER, TraitType.CAUTIOUS),
    (TraitType.KEEN_EYED, TraitType.OBLIVIOUS),
    (TraitType.LONER, TraitType.CHARISMATIC),
]

# Build a fast lookup set for incompatibility checks
_INCOMPAT_SET: set[tuple[int, int]] = set()
for a, b in INCOMPATIBLE_PAIRS:
    _INCOMPAT_SET.add((a, b))
    _INCOMPAT_SET.add((b, a))


def are_compatible(trait_a: int, trait_b: int) -> bool:
    """Check if two traits can coexist on one entity."""
    return (trait_a, trait_b) not in _INCOMPAT_SET


# ---------------------------------------------------------------------------
# Race-biased trait pools — some races are more likely to get certain traits
# ---------------------------------------------------------------------------

# Maps race prefix -> list of (TraitType, weight) for biased selection
# Traits not in the list still have a base weight of 1.0
RACE_TRAIT_BIAS: dict[str, list[tuple[int, float]]] = {
    "hero": [
        (TraitType.BRAVE, 2.0),
        (TraitType.CURIOUS, 1.5),
        (TraitType.DILIGENT, 1.5),
        (TraitType.TACTICAL, 1.5),
    ],
    "goblin": [
        (TraitType.GREEDY, 2.5),
        (TraitType.COWARDLY, 2.0),
        (TraitType.CAUTIOUS, 1.5),
    ],
    "wolf": [
        (TraitType.AGGRESSIVE, 2.5),
        (TraitType.BLOODTHIRSTY, 2.0),
        (TraitType.KEEN_EYED, 1.5),
    ],
    "bandit": [
        (TraitType.GREEDY, 2.0),
        (TraitType.AGGRESSIVE, 1.5),
        (TraitType.LONER, 1.5),
    ],
    "undead": [
        (TraitType.RESILIENT, 2.0),
        (TraitType.OBLIVIOUS, 1.5),
        (TraitType.SPIRIT_TOUCHED, 2.0),
    ],
    "orc": [
        (TraitType.BERSERKER, 2.5),
        (TraitType.BRAVE, 2.0),
        (TraitType.AGGRESSIVE, 2.0),
    ],
}


# ---------------------------------------------------------------------------
# Assignment: pick 2-4 compatible traits for an entity
# ---------------------------------------------------------------------------

ALL_TRAIT_TYPES: list[int] = [t.value for t in TraitType]


def assign_traits(
    rng: DeterministicRNG,
    domain_id: int,
    entity_id: int,
    tick: int,
    race_prefix: str = "",
    count_min: int = 2,
    count_max: int = 4,
) -> list[int]:
    """Randomly assign traits to an entity, respecting incompatibility.

    Uses weighted selection biased by race.  Returns a list of TraitType
    int values.
    """
    from src.core.models.enums import Domain

    # Determine how many traits
    num_traits = rng.next_int(domain_id, entity_id, tick + 100, count_min, count_max)

    # Build weighted pool
    base_weight = 1.0
    weight_map: dict[int, float] = {t: base_weight for t in ALL_TRAIT_TYPES}
    # Apply race bias
    for prefix, biases in RACE_TRAIT_BIAS.items():
        if race_prefix.startswith(prefix):
            for trait_type, weight in biases:
                weight_map[trait_type] = weight
            break

    chosen: list[int] = []
    available = list(ALL_TRAIT_TYPES)

    for i in range(num_traits):
        if not available:
            break

        # Compute cumulative weights for available traits
        weights = [weight_map.get(t, base_weight) for t in available]
        total = sum(weights)
        if total <= 0:
            break

        # Weighted random selection using RNG
        roll = rng.next_float(domain_id, entity_id, tick + 200 + i) * total
        cumulative = 0.0
        selected_idx = 0
        for idx, w in enumerate(weights):
            cumulative += w
            if roll <= cumulative:
                selected_idx = idx
                break

        selected = available[selected_idx]
        chosen.append(selected)

        # Remove selected and all incompatible traits from pool
        available = [
            t for t in available
            if t != selected and are_compatible(t, selected)
        ]

    return chosen


# ---------------------------------------------------------------------------
# Typed aggregation dataclasses
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class UtilityBonus:
    """Typed additive modifiers for AI goal scoring."""
    combat: float = 0.0
    flee: float = 0.0
    explore: float = 0.0
    loot: float = 0.0
    trade: float = 0.0
    rest: float = 0.0
    craft: float = 0.0
    social: float = 0.0


@dataclass
class TraitStatModifiers:
    """Typed passive stat modifiers aggregated from traits.

    Multiplicative fields start at 1.0 (no change).
    Additive fields start at 0.0.
    """
    atk_mult: float = 1.0
    def_mult: float = 1.0
    matk_mult: float = 1.0
    mdef_mult: float = 1.0
    crit_bonus: float = 0.0
    evasion_bonus: float = 0.0
    vision_bonus: int = 0
    hp_regen_mult: float = 1.0
    interaction_speed_mult: float = 1.0
    fire_dmg_mult: float = 1.0
    ice_dmg_mult: float = 1.0
    lightning_dmg_mult: float = 1.0
    dark_dmg_mult: float = 1.0
    flee_threshold_mod: float = 0.0


# ---------------------------------------------------------------------------
# Aggregate trait effects for an entity
# ---------------------------------------------------------------------------

def aggregate_trait_utility(traits: list[int]) -> UtilityBonus:
    """Sum utility modifiers across all traits."""
    bonus = UtilityBonus()
    for t in traits:
        tdef = TRAIT_DEFS.get(t)
        if tdef is None:
            continue
        bonus.combat += tdef.combat_utility
        bonus.flee += tdef.flee_utility
        bonus.explore += tdef.explore_utility
        bonus.loot += tdef.loot_utility
        bonus.trade += tdef.trade_utility
        bonus.rest += tdef.rest_utility
        bonus.craft += tdef.craft_utility
        bonus.social += tdef.social_utility
    return bonus


def aggregate_trait_stats(traits: list[int]) -> TraitStatModifiers:
    """Aggregate passive stat modifiers from all traits."""
    mods = TraitStatModifiers()
    for t in traits:
        tdef = TRAIT_DEFS.get(t)
        if tdef is None:
            continue
        mods.atk_mult *= tdef.atk_mult
        mods.def_mult *= tdef.def_mult
        mods.matk_mult *= tdef.matk_mult
        mods.mdef_mult *= tdef.mdef_mult
        mods.crit_bonus += tdef.crit_bonus
        mods.evasion_bonus += tdef.evasion_bonus
        mods.vision_bonus += tdef.vision_bonus
        mods.hp_regen_mult *= tdef.hp_regen_mult
        mods.interaction_speed_mult *= tdef.interaction_speed_mult
        mods.fire_dmg_mult *= tdef.fire_dmg_mult
        mods.ice_dmg_mult *= tdef.ice_dmg_mult
        mods.lightning_dmg_mult *= tdef.lightning_dmg_mult
        mods.dark_dmg_mult *= tdef.dark_dmg_mult
        mods.flee_threshold_mod += tdef.flee_threshold_mod
    return mods

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/gameplay/__init__.py
from .items.items import Item, ItemType, Rarity, Weapon, Armor, Accessory, Consumable, MaterialItem
from .items.item_registry import ITEM_REGISTRY, get_item
from .attributes import Attributes, AttributeCaps, recalc_derived_stats
from .classes import HeroClass, ClassDef, SkillDef, SkillInstance
from .effects import StatusEffect, EffectType
from .faction import Faction
from .quests import Quest, QuestType

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/gameplay/attributes.py
"""RPG Attribute system — 9 primary attributes that derive combat & non-combat stats.

Primary Attributes:
  STR (Strength)     — ATK, carry weight
  AGI (Agility)      — SPD, evasion, crit rate
  VIT (Vitality)     — HP, physical DEF
  INT (Intelligence) — Skill power, XP gain, cooldown reduction
  SPI (Spirit)       — MATK (magic attack), mana-like resource scaling
  WIS (Wisdom)       — MDEF (magic defense), LUCK, cooldown reduction
  END (Endurance)    — Stamina, HP regen
  PER (Perception)   — Vision range, detection, loot quality, trap awareness
  CHA (Charisma)     — Trade prices, morale, social influence, recruitment

Each attribute has a base value (current) and a cap (max trainable).
Level ups increase both base (+2) and cap (+5).
Attributes can be slowly trained through actions.
"""

from __future__ import annotations

import math as _math
from dataclasses import dataclass, field


@dataclass(slots=True)
class Attributes:
    """Primary RPG attributes for an entity (9 attributes)."""

    str_: int = 5      # Strength
    agi: int = 5        # Agility
    vit: int = 5        # Vitality
    int_: int = 5       # Intelligence
    spi: int = 5        # Spirit
    wis: int = 5        # Wisdom
    end: int = 5        # Endurance
    per: int = 5        # Perception
    cha: int = 5        # Charisma

    # Fractional training accumulator (not exposed to API, internal only)
    _str_frac: float = 0.0
    _agi_frac: float = 0.0
    _vit_frac: float = 0.0
    _int_frac: float = 0.0
    _spi_frac: float = 0.0
    _wis_frac: float = 0.0
    _end_frac: float = 0.0
    _per_frac: float = 0.0
    _cha_frac: float = 0.0

    def copy(self) -> Attributes:
        return Attributes(
            str_=self.str_, agi=self.agi, vit=self.vit,
            int_=self.int_, spi=self.spi, wis=self.wis,
            end=self.end, per=self.per, cha=self.cha,
            _str_frac=self._str_frac, _agi_frac=self._agi_frac,
            _vit_frac=self._vit_frac, _int_frac=self._int_frac,
            _spi_frac=self._spi_frac, _wis_frac=self._wis_frac,
            _end_frac=self._end_frac, _per_frac=self._per_frac,
            _cha_frac=self._cha_frac,
        )

    def total(self) -> int:
        """Sum of all primary attributes."""
        return (self.str_ + self.agi + self.vit + self.int_ + self.spi
                + self.wis + self.end + self.per + self.cha)


@dataclass(slots=True)
class AttributeCaps:
    """Maximum trainable values for each attribute.
    Caps increase on level up and can be boosted by class bonuses.
    """

    str_cap: int = 15
    agi_cap: int = 15
    vit_cap: int = 15
    int_cap: int = 15
    spi_cap: int = 15
    wis_cap: int = 15
    end_cap: int = 15
    per_cap: int = 15
    cha_cap: int = 15

    def copy(self) -> AttributeCaps:
        return AttributeCaps(
            str_cap=self.str_cap, agi_cap=self.agi_cap, vit_cap=self.vit_cap,
            int_cap=self.int_cap, spi_cap=self.spi_cap, wis_cap=self.wis_cap,
            end_cap=self.end_cap, per_cap=self.per_cap, cha_cap=self.cha_cap,
        )

    def increase_all(self, amount: int) -> None:
        """Increase all caps by a flat amount (called on level up)."""
        self.str_cap += amount
        self.agi_cap += amount
        self.vit_cap += amount
        self.int_cap += amount
        self.spi_cap += amount
        self.wis_cap += amount
        self.end_cap += amount
        self.per_cap += amount
        self.cha_cap += amount


# ---------------------------------------------------------------------------
# Attribute → derived stat formulas
# ---------------------------------------------------------------------------

def derive_max_hp(base_max_hp: int, vit: int, end: int) -> int:
    """Max HP = base + VIT*2 + END*0.5"""
    return base_max_hp + vit * 2 + int(end * 0.5)


def derive_atk(base_atk: int, str_: int) -> int:
    """ATK = base + STR*0.5"""
    return base_atk + int(str_ * 0.5)


def derive_def(base_def: int, vit: int) -> int:
    """DEF = base + VIT*0.3"""
    return base_def + int(vit * 0.3)


def derive_spd(base_spd: int, agi: int) -> int:
    """SPD = base + AGI*0.4"""
    return base_spd + int(agi * 0.4)


def derive_crit_rate(base_crit: float, agi: int, luck: int = 0) -> float:
    """Crit rate = base + AGI*0.004 + Luck*0.01"""
    return base_crit + agi * 0.004 + luck * 0.01


def derive_evasion(base_evasion: float, agi: int) -> float:
    """Evasion = base + AGI*0.003"""
    return base_evasion + agi * 0.003


def derive_luck(base_luck: int, wis: int) -> int:
    """Luck = base + WIS*0.3"""
    return base_luck + int(wis * 0.3)


def derive_stamina(base_stamina: int, end: int) -> int:
    """Max stamina = base + END*2"""
    return base_stamina + end * 2


def derive_xp_multiplier(wis: int, int_: int) -> float:
    """XP gain multiplier based on Wisdom and Intelligence. Base 1.0 at 0/0."""
    return 1.0 + wis * 0.01 + int_ * 0.005


# ---------------------------------------------------------------------------
# New derived stats for expanded attribute system
# ---------------------------------------------------------------------------

def derive_matk(base_matk: int, spi: int, int_: int) -> int:
    """Magic ATK = base + SPI*0.6 + INT*0.2"""
    return base_matk + int(spi * 0.6) + int(int_ * 0.2)


def derive_mdef(base_mdef: int, wis: int, spi: int) -> int:
    """Magic DEF = base + WIS*0.4 + SPI*0.15"""
    return base_mdef + int(wis * 0.4) + int(spi * 0.15)


def derive_vision(base_vision: int, per: int) -> int:
    """Vision range = base + PER*0.3  (integer tiles)"""
    return base_vision + int(per * 0.3)


def derive_loot_bonus(per: int, wis: int) -> float:
    """Loot quality / drop chance multiplier. Base 1.0."""
    return 1.0 + per * 0.008 + wis * 0.003


def derive_loot_modifier(luck: int) -> float:
    """Extra loot rarity modifier from Luck. Base 1.0 + Luck/100."""
    return 1.0 + luck * 0.01


def derive_trade_bonus(cha: int) -> float:
    """Trade price modifier (buy discount / sell bonus). Base 1.0."""
    return 1.0 + cha * 0.01


def derive_interaction_speed(cha: int, int_: int) -> float:
    """Interaction speed multiplier (harvest, craft, etc.). Base 1.0."""
    return 1.0 + cha * 0.005 + int_ * 0.005


def derive_rest_efficiency(end: int, wis: int) -> float:
    """Rest / regen efficiency multiplier. Base 1.0."""
    return 1.0 + end * 0.008 + wis * 0.004


def derive_hp_regen(end: int, vit: int) -> float:
    """HP regen per rest tick. Base 1.0."""
    return 1.0 + end * 0.15 + vit * 0.05


def derive_cooldown_reduction(int_: int, wis: int) -> float:
    """Cooldown reduction multiplier for skills. Base 1.0 (lower=faster)."""
    return max(0.5, 1.0 - int_ * 0.005 - wis * 0.003)


def check_breakthroughs(attrs: Attributes, traits: list[str]) -> None:
    """Add breakthrough traits if attributes hit milestones (25, 50, 100)."""
    # 25 Milestone
    if attrs.str_ >= 25 and "str_25" not in traits: traits.append("str_25")
    if attrs.vit >= 25 and "vit_25" not in traits: traits.append("vit_25")
    if attrs.agi >= 25 and "agi_25" not in traits: traits.append("agi_25")
    if attrs.int_ >= 25 and "int_25" not in traits: traits.append("int_25")
    if attrs.per >= 25 and "per_25" not in traits: traits.append("per_25")
    
    # 50 Milestone (Advanced)
    if attrs.str_ >= 50 and "str_50" not in traits: traits.append("str_50") # Might
    if attrs.vit >= 50 and "vit_50" not in traits: traits.append("vit_50") # Juggernaut
    if attrs.agi >= 50 and "agi_50" not in traits: traits.append("agi_50") # Wind-dancer
    if attrs.int_ >= 50 and "int_50" not in traits: traits.append("int_50") # Savant

    # 100 Milestone (Legendary - Pillar Traits)
    if attrs.str_ >= 100 and "str_100" not in traits: traits.append("str_100") # Colossus
    if attrs.int_ >= 100 and "int_100" not in traits: traits.append("int_100") # Archmage


# ---------------------------------------------------------------------------
# Recalculate all derived stats from attributes
# ---------------------------------------------------------------------------

def recalc_derived_stats(
    target: Any,
    new_attrs: "Attributes",
    old_attrs: "Attributes | None" = None,
) -> None:
    """Recompute all attribute-derived fields on a target (Entity, StatsProxy, or Aspect)."""
    combat = target.combat if hasattr(target, "combat") else target
    prog = target.progression if hasattr(target, "progression") else target
    has_combat = hasattr(combat, "hp")
    has_prog = hasattr(prog, "stamina")

    if old_attrs is not None:
        if has_combat:
            combat.max_hp -= derive_max_hp(0, old_attrs.vit, old_attrs.end)
            combat.atk -= derive_atk(0, old_attrs.str_)
            combat.def_ -= derive_def(0, old_attrs.vit)
            combat.spd -= derive_spd(0, old_attrs.agi)
            if hasattr(combat, "crit_rate"): combat.crit_rate -= derive_crit_rate(0.0, old_attrs.agi, old_attrs.wis)
            combat.evasion -= derive_evasion(0.0, old_attrs.agi)
            combat.luck -= derive_luck(0, old_attrs.wis)
            combat.matk -= derive_matk(0, old_attrs.spi, old_attrs.int_)
            combat.mdef -= derive_mdef(0, old_attrs.wis, old_attrs.spi)
        if has_prog:
            prog.max_stamina -= derive_stamina(0, old_attrs.end)

    if has_combat:
        combat.max_hp = derive_max_hp(combat.max_hp, new_attrs.vit, new_attrs.end)
        combat.atk = derive_atk(combat.atk, new_attrs.str_)
        combat.def_ = derive_def(combat.def_, new_attrs.vit)
        combat.spd = derive_spd(combat.spd, new_attrs.agi)
        if hasattr(combat, "crit_rate"): combat.crit_rate = derive_crit_rate(combat.crit_rate, new_attrs.agi, new_attrs.wis)
        combat.evasion = derive_evasion(combat.evasion, new_attrs.agi)
        combat.luck = derive_luck(combat.luck, new_attrs.wis)
        combat.matk = derive_matk(combat.matk, new_attrs.spi, new_attrs.int_)
        combat.mdef = derive_mdef(combat.mdef, new_attrs.wis, new_attrs.spi)
        combat.hp_regen = derive_hp_regen(new_attrs.end, new_attrs.vit)

    if has_prog:
        prog.max_stamina = derive_stamina(prog.max_stamina, new_attrs.end)

    if has_combat:
        if hasattr(combat, "vision_range"):
            combat.vision_range = derive_vision(6, new_attrs.per)
        if hasattr(combat, "cooldown_reduction"):
            combat.cooldown_reduction = derive_cooldown_reduction(new_attrs.int_, new_attrs.wis)
        if hasattr(combat, "loot_bonus"):
            combat.loot_bonus = derive_loot_bonus(new_attrs.per, new_attrs.wis)
        if hasattr(combat, "trade_bonus"):
            combat.trade_bonus = derive_trade_bonus(new_attrs.cha)
        if hasattr(combat, "interaction_speed"):
            combat.interaction_speed = derive_interaction_speed(new_attrs.cha, new_attrs.int_)
        if hasattr(combat, "rest_efficiency"):
            combat.rest_efficiency = derive_rest_efficiency(new_attrs.end, new_attrs.wis)

    # 3. Apply Breakthrough Passives
    traits = []
    id_source = None
    if hasattr(target, "identity") and target.identity:
        id_source = target.identity
    else:
        # Check for attached aspect parent
        _parent = getattr(target, "_entity", None)
        if _parent and hasattr(_parent, "identity"):
            id_source = _parent.identity
            
    if id_source and has_combat:
        traits = id_source.traits
        if "str_25" in traits: combat.atk = int(combat.atk * 1.1)
        if "vit_25" in traits: combat.max_hp = int(combat.max_hp * 1.1)
        if "agi_25" in traits: combat.spd = int(combat.spd * 1.1)
        if "str_50" in traits: combat.atk = int(combat.atk * 1.25)
        if "vit_50" in traits: combat.max_hp = int(combat.max_hp * 1.25)
        if "agi_50" in traits: combat.evasion += 0.05
        if "int_50" in traits: combat.matk = int(combat.matk * 1.3)
        if "str_100" in traits: combat.atk = int(combat.atk * 1.5)
        if "int_100" in traits: combat.matk = int(combat.matk * 1.5)


    if has_combat and hasattr(combat, "hp"):
        combat.hp = min(combat.hp, combat.max_hp)
    if has_prog and hasattr(prog, "stamina"):
        prog.stamina = min(prog.stamina, prog.max_stamina)
# ---------------------------------------------------------------------------
# Training: attribute gain from actions
# ---------------------------------------------------------------------------

# Training rates per action type (very slow)
TRAIN_RATES: dict[str, dict[str, float]] = {
    "move":     {"agi": 0.008, "end": 0.005, "per": 0.003},
    "attack":   {"str": 0.015, "agi": 0.008},
    "defend":   {"vit": 0.010, "end": 0.008},
    "rest":     {"wis": 0.006, "end": 0.003},
    "harvest":  {"end": 0.010, "wis": 0.005, "per": 0.004},
    "loot":     {"wis": 0.005, "per": 0.006},
    "skill":    {"int": 0.010, "wis": 0.005, "spi": 0.008},
    "magic_attack": {"spi": 0.015, "int": 0.008},
    "trade":    {"cha": 0.012, "wis": 0.003},
    "explore":  {"per": 0.010, "agi": 0.005},
    "interact": {"cha": 0.008, "int": 0.004},
}


def train_attributes(
    attrs: Attributes,
    caps: AttributeCaps,
    action: str,
    stats: 'Stats | None' = None,
    race: str = "hero",
    talents: list[str] | None = None,
    weakness: str = "",
    aptitudes: dict[str, float] | None = None,
) -> None:
    """Apply fractional training gains from an action."""
    rates = TRAIN_RATES.get(action, {})
    if not rates:
        return
        
    from src.core.models.enums import RACE_PROFILES
    profile = RACE_PROFILES.get(race)
    if not profile:
        base_race = race.split('_')[0]
        profile = RACE_PROFILES.get(base_race)
        
    train_rate_mult = profile.train_rate if profile else 1.0
    if train_rate_mult == 0.0:
        return  # e.g., Undead don't train
        
    talents = talents or []
    old_snapshot = attrs.copy() if stats is not None else None
    changed = False
    
    aptitudes = aptitudes or {}
    
    # Pillar 3: Attribute Soft-Caps
    # Total trainable gain is limited by (Level * 5) + Base
    level = stats.level if stats else 1
    soft_cap_limit = level * 5 + 15 # +15 safe buffer for starter stats
    
    for attr_key, base_rate in rates.items():
        # Check Soft-Cap before training
        mapping = _TRAIN_MAP.get(attr_key)
        if mapping:
            current = getattr(attrs, mapping[0])
            if current >= soft_cap_limit:
                continue # Soft-Capped at this level

        # Apply multipliers
        rate = base_rate * train_rate_mult * aptitudes.get(attr_key, 1.0)
        if attr_key in talents:
            rate *= 2.0
        elif attr_key == weakness:
            rate *= 0.5
            
        if _apply_train(attrs, caps, attr_key, rate):
            changed = True
            
    if changed and stats is not None and old_snapshot is not None:
        # Increase region fatigue when performing actions (Anti-loop)
        rid = getattr(stats, "_entity", None).current_region_id if hasattr(stats, "_entity") else None
        if rid and action in ("attack", "harvest", "explore", "loot"):
            attrs.mind.region_fatigue[rid] = min(1.0, attrs.mind.region_fatigue.get(rid, 0.0) + 0.01)
            
        recalc_derived_stats(stats, attrs, old_attrs=old_snapshot)


# Map from train key → (attr_field, frac_field, cap_field)
_TRAIN_MAP: dict[str, tuple[str, str, str]] = {
    "str": ("str_",  "_str_frac", "str_cap"),
    "agi": ("agi",   "_agi_frac", "agi_cap"),
    "vit": ("vit",   "_vit_frac", "vit_cap"),
    "int": ("int_",  "_int_frac", "int_cap"),
    "spi": ("spi",   "_spi_frac", "spi_cap"),
    "wis": ("wis",   "_wis_frac", "wis_cap"),
    "end": ("end",   "_end_frac", "end_cap"),
    "per": ("per",   "_per_frac", "per_cap"),
    "cha": ("cha",   "_cha_frac", "cha_cap"),
}


def decay_attributes(
    attrs: Attributes,
    stats: 'Stats',
    rng: 'DeterministicRNG',
    entity_id: int,
    tick: int,
    decay_amount: float = 0.1,
) -> bool:
    """Fractionally reduce a random primary attribute.
    
    If fractional reaches negative and integer attribute is > 5,
    reduce the integer attribute. Returns True if attribute was reduced.
    """
    from src.core.models.enums import Domain
    # Pick a random attribute to decay
    attr_keys = list(_TRAIN_MAP.keys())
    # Deterministic choice
    idx = rng.next_int(Domain.AI_DECISION, entity_id, tick + 99, 0, len(attr_keys) - 1)
    key = attr_keys[idx]
    
    mapping = _TRAIN_MAP.get(key)
    if mapping is None:
        return False
        
    attr_field, frac_field, _ = mapping
    old_snapshot = attrs.copy()
    
    current = getattr(attrs, attr_field)
    frac = getattr(attrs, frac_field) - decay_amount
    
    changed = False
    if frac < 0.0:
        if current > 5: # Don't decay below base starting value
            setattr(attrs, attr_field, current - 1)
            frac += 1.0
            changed = True
        else:
            frac = 0.0 # Clamp at 0.0 if we can't reduce integer
            
    setattr(attrs, frac_field, frac)
    
    if changed:
        recalc_derived_stats(stats, attrs, old_attrs=old_snapshot)
        
    return changed


def _apply_train(attrs: Attributes, caps: AttributeCaps, key: str, rate: float) -> bool:
    """Add fractional training to one attribute. Returns True if attribute incremented."""
    mapping = _TRAIN_MAP.get(key)
    if mapping is None:
        return False
    attr_field, frac_field, cap_field = mapping
    cap = getattr(caps, cap_field)
    current = getattr(attrs, attr_field)
    frac = getattr(attrs, frac_field) + rate
    incremented = False
    if frac >= 1.0 and current < cap:
        gain = int(frac)
        setattr(attrs, attr_field, min(current + gain, cap))
        frac -= gain
        incremented = True
    setattr(attrs, frac_field, frac)
    return incremented


# ---------------------------------------------------------------------------
# Level-up attribute gains
# ---------------------------------------------------------------------------

def level_up_attributes(attrs: Attributes, caps: AttributeCaps, aptitudes: dict[str, float] | None = None) -> None:
    """Apply attribute gains on level up.

    - Base attributes: +2 (modified by aptitude) to each (up to cap)
    - Caps: +5 to each
    """
    caps.increase_all(5)
    
    aptitudes = aptitudes or {}

    attrs.str_ = min(attrs.str_ + int(2 * aptitudes.get("str", 1.0)), caps.str_cap)
    attrs.agi = min(attrs.agi + int(2 * aptitudes.get("agi", 1.0)), caps.agi_cap)
    attrs.vit = min(attrs.vit + int(2 * aptitudes.get("vit", 1.0)), caps.vit_cap)
    attrs.int_ = min(attrs.int_ + int(2 * aptitudes.get("int", 1.0)), caps.int_cap)
    attrs.spi = min(attrs.spi + int(2 * aptitudes.get("spi", 1.0)), caps.spi_cap)
    attrs.wis = min(attrs.wis + int(2 * aptitudes.get("wis", 1.0)), caps.wis_cap)
    attrs.end = min(attrs.end + int(2 * aptitudes.get("end", 1.0)), caps.end_cap)
    attrs.per = min(attrs.per + int(2 * aptitudes.get("per", 1.0)), caps.per_cap)
    attrs.cha = min(attrs.cha + int(2 * aptitudes.get("cha", 1.0)), caps.cha_cap)


# ---------------------------------------------------------------------------
# Speed → action delay (Option D: logarithmic + action-type multipliers)
# ---------------------------------------------------------------------------

# Action-type delay multipliers (lower = faster for that action type)
_ACTION_DELAY_MULT: dict[str, float] = {
    "move": 2.0,
    "attack": 1.5,
    "skill": 2.5,
    "loot": 1.2,
    "harvest": 1.2,
    "use_item": 1.0,
    "rest": 1.5,
    "building": 2.0,     # Building visit interactions (shop, blacksmith, guild, etc.)
}

# Minimum delay floor (prevents infinitely fast actions)
_MIN_DELAY = 0.3
# Maximum delay ceiling
_MAX_DELAY = 4.0


def speed_delay(spd: int, action: str = "move", interaction_speed: float = 1.0) -> float:
    """Compute action delay from speed stat using logarithmic diminishing returns.

    Formula: delay = action_mult / (1.0 + ln(max(spd, 1)))
    Then scaled by interaction_speed for loot/harvest/use_item.

    SPD →  delay (move, mult=2.0):
      1  → 2.00
      5  → 0.76
     10  → 0.60
     15  → 0.54
     20  → 0.50
     30  → 0.45
     50  → 0.40

    Returns a float clamped to [_MIN_DELAY, _MAX_DELAY].
    """
    s = max(spd, 1)
    base = 1.0 / (1.0 + _math.log(s))
    mult = _ACTION_DELAY_MULT.get(action, 1.0)
    delay = base * mult

    # Apply interaction_speed stat for non-combat actions
    if action in ("loot", "harvest", "use_item", "rest"):
        delay /= max(interaction_speed, 0.5)

    return max(_MIN_DELAY, min(_MAX_DELAY, delay))

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/gameplay/buildings.py
"""Town buildings — Shop, Blacksmith, Guild Hall, Class Hall, Inn.

Buildings are fixed locations in town that heroes can interact with.
Each building type provides different services:
  - Store: buy/sell items
  - Blacksmith: craft powerful items from materials + gold
  - Guild: get intel about enemy camps and material sources
  - Class Hall: learn new class skills, attempt breakthroughs
  - Inn: rest to recover HP and stamina quickly
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.core.models.enums import ItemType, Rarity
from src.core.gameplay.items.item_registry import ItemTemplate

if TYPE_CHECKING:
    from src.core.models import Vector2


# ---------------------------------------------------------------------------
# Building data model
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Building:
    """A fixed building in the town."""

    building_id: str          # "store", "blacksmith", "guild"
    name: str
    pos: Vector2
    building_type: str        # "store" | "blacksmith" | "guild"
    durability: float = 100.0
    max_durability: float = 100.0
    is_functional: bool = True

    def take_damage(self, amount: float) -> None:
        self.durability = max(0.0, self.durability - amount)
        if self.durability <= 0:
            self.is_functional = False

    def repair(self, amount: float) -> None:
        self.durability = min(self.max_durability, self.durability + amount)
        if self.durability > 0:
            self.is_functional = True


# ---------------------------------------------------------------------------
# Shop economy — sell/buy prices
# ---------------------------------------------------------------------------

# Sell prices by rarity (gold received when hero sells to shop)
SELL_PRICES: dict[int, int] = {
    Rarity.COMMON: 5,
    Rarity.UNCOMMON: 15,
    Rarity.RARE: 40,
}


def item_sell_price(item_id: str, reputation: float = 0.0) -> int:
    """Calculate how much gold a hero gets for selling an item."""
    from src.core.gameplay.items.item_registry import ITEM_REGISTRY
    t = ITEM_REGISTRY.get(item_id)
    if t is None:
        return 0
    
    base = 0
    if t.sell_value > 0:
        base = t.sell_value
    elif t.gold_value > 0:
        base = t.gold_value
    else:
        base = SELL_PRICES.get(t.rarity, 3)
        
    # Reputation bonus: up to +20% at 40 rep
    bonus = 1.0 + min(0.2, reputation * 0.005)
    return int(base * bonus)


# Items available for purchase at the store: (item_id, buy_price)
SHOP_INVENTORY: list[tuple[str, int]] = [
    # ---- Healing potions ----
    ("small_hp_potion", 15),
    ("medium_hp_potion", 40),
    ("large_hp_potion", 80),
    ("herbal_remedy", 20),
    # ---- Buff potions ----
    ("atk_potion", 25),
    ("def_potion", 25),
    ("spd_potion", 25),
    ("crit_potion", 45),
    ("antidote", 15),
    # ---- Weapons (tiered) ----
    ("wooden_club", 20),
    ("bandit_dagger", 35),
    ("iron_sword", 50),
    ("orc_axe", 65),
    ("steel_greatsword", 120),
    # ---- Magic weapons ----
    ("apprentice_staff", 30),
    ("fire_staff", 90),
    # ---- Armor (tiered) ----
    ("leather_vest", 25),
    ("chainmail", 60),
    ("orc_shield", 70),
    ("plate_armor", 150),
    # ---- Magic armor ----
    ("cloth_robe", 25),
    ("silk_robe", 60),
    # ---- Accessories ----
    ("lucky_charm", 30),
    ("speed_ring", 55),
    ("mana_crystal", 30),
    ("spirit_pendant", 55),
    # ---- Materials ----
    ("mana_shard", 30),
    ("silver_ingot", 35),
    ("phoenix_feather", 60),
]


def shop_buy_price(item_id: str, reputation: float = 0.0) -> int | None:
    """Return the buy price for an item, or None if not sold at shop."""
    for iid, price in SHOP_INVENTORY:
        if iid == item_id:
            # Reputation discount: up to 30% at 30 rep
            discount = 1.0 - min(0.3, reputation * 0.01)
            return int(price * discount)
    return None


# ---------------------------------------------------------------------------
# Blacksmith recipes
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Recipe:
    """A crafting recipe at the blacksmith."""

    recipe_id: str
    output_item: str          # item_id produced
    gold_cost: int
    materials: dict[str, int]  # {item_id: quantity}
    description: str = ""

    def to_dict(self) -> dict:
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        t = ITEM_REGISTRY.get(self.output_item)
        return {
            "recipe_id": self.recipe_id,
            "output_item": self.output_item,
            "output_name": t.name if t else self.output_item,
            "gold_cost": self.gold_cost,
            "materials": dict(self.materials),
            "description": self.description,
        }


RECIPES: list[Recipe] = [
    # --- Goblin-material recipes ---
    Recipe(
        recipe_id="craft_steel_sword",
        output_item="steel_sword",
        gold_cost=60,
        materials={"iron_ore": 2, "wood": 1},
        description="A well-forged steel blade with improved balance.",
    ),
    Recipe(
        recipe_id="craft_battle_axe",
        output_item="battle_axe",
        gold_cost=90,
        materials={"iron_ore": 3, "steel_bar": 1},
        description="A heavy battle axe that hits hard but swings slow.",
    ),
    Recipe(
        recipe_id="craft_enchanted_blade",
        output_item="enchanted_blade",
        gold_cost=200,
        materials={"steel_bar": 2, "enchanted_dust": 2},
        description="A blade infused with magical energy. Requires rare dust.",
    ),
    Recipe(
        recipe_id="craft_iron_plate",
        output_item="iron_plate",
        gold_cost=70,
        materials={"iron_ore": 3, "leather": 1},
        description="Heavy iron plate armor. Strong defense at the cost of speed.",
    ),
    Recipe(
        recipe_id="craft_enchanted_robe",
        output_item="enchanted_robe",
        gold_cost=150,
        materials={"leather": 2, "enchanted_dust": 1},
        description="A light robe enchanted for agility and evasion.",
    ),
    Recipe(
        recipe_id="craft_ring_of_power",
        output_item="ring_of_power",
        gold_cost=120,
        materials={"iron_ore": 1, "enchanted_dust": 1},
        description="A ring that amplifies both attack and defense.",
    ),
    Recipe(
        recipe_id="craft_evasion_amulet",
        output_item="evasion_amulet",
        gold_cost=80,
        materials={"leather": 2, "wood": 1},
        description="An amulet carved from fine materials for enhanced agility.",
    ),
    # --- Wolf-material recipes (Forest) ---
    Recipe(
        recipe_id="craft_wolf_cloak",
        output_item="wolf_cloak",
        gold_cost=50,
        materials={"wolf_pelt": 2, "leather": 1},
        description="A light cloak sewn from wolf pelts. Fast and evasive.",
    ),
    Recipe(
        recipe_id="craft_fang_necklace",
        output_item="fang_necklace",
        gold_cost=45,
        materials={"wolf_fang": 2, "fiber": 1},
        description="A necklace of wolf fangs that enhances critical strikes.",
    ),
    # --- Bandit-material recipes (Desert) ---
    Recipe(
        recipe_id="craft_desert_bow",
        output_item="desert_bow",
        gold_cost=75,
        materials={"raw_gem": 1, "fiber": 2},
        description="A composite bow with gem-tipped arrows. Precise and deadly.",
    ),
    # --- Undead-material recipes (Swamp) ---
    Recipe(
        recipe_id="craft_bone_shield",
        output_item="bone_shield",
        gold_cost=65,
        materials={"bone_shard": 3, "dark_moss": 1},
        description="A shield of fused bones. Sturdy and HP-boosting.",
    ),
    Recipe(
        recipe_id="craft_spectral_blade",
        output_item="spectral_blade",
        gold_cost=180,
        materials={"ectoplasm": 2, "enchanted_dust": 1},
        description="A ghostly blade that strikes with ethereal precision.",
    ),
    # --- Orc-material recipes (Mountain) ---
    Recipe(
        recipe_id="craft_mountain_plate",
        output_item="mountain_plate",
        gold_cost=160,
        materials={"stone_block": 3, "iron_ore": 2},
        description="Massive stone-reinforced plate armor. Extremely heavy but durable.",
    ),
    # --- Harvestable-material recipes ---
    Recipe(
        recipe_id="craft_herbal_remedy",
        output_item="herbal_remedy",
        gold_cost=15,
        materials={"herb": 3, "glowing_mushroom": 1},
        description="A natural healing draught brewed from forest herbs and mushrooms.",
    ),
]

RECIPE_MAP: dict[str, Recipe] = {r.recipe_id: r for r in RECIPES}


def can_craft(recipe: Recipe, gold: int, inventory_items: list[str]) -> bool:
    """Check if the hero has enough gold and materials to craft."""
    if gold < recipe.gold_cost:
        return False
    for mat_id, qty in recipe.materials.items():
        if inventory_items.count(mat_id) < qty:
            return False
    return True


# ---------------------------------------------------------------------------
# Guild intel
# ---------------------------------------------------------------------------

# Material drop hints the guild provides
MATERIAL_HINTS: dict[str, str] = {
    # Goblin drops
    "wood": "Dropped by basic goblins. Also harvestable from Timber nodes in forests.",
    "leather": "Skinned from goblins, scouts, and wolves.",
    "iron_ore": "Found on goblin warriors, orcs, and in camp raids. Harvestable in deserts, swamps, and mountains.",
    "steel_bar": "Rare drop from goblin warriors and orc warriors.",
    "enchanted_dust": "Harvested from elite goblins, liches, and orc warlords. Crystal Nodes in mountains also yield it.",
    # Wolf drops (Forest)
    "wolf_pelt": "Skinned from wolves in forest regions. Common from all wolf types.",
    "wolf_fang": "Dropped by dire wolves and alpha wolves in forests.",
    # Bandit drops (Desert)
    "fiber": "Gathered from bandits in desert regions. Also harvestable from Cactus Fiber nodes.",
    "raw_gem": "Found on bandit archers and chiefs in desert regions. Gem Deposits also yield them.",
    # Undead drops (Swamp)
    "bone_shard": "Collected from skeletons and zombies in swamp regions.",
    "ectoplasm": "Extracted from zombies and liches in swamp regions. Rare and valuable.",
    "dark_moss": "Found in swamp regions. Dropped by skeletons or harvested from Dark Moss Patches.",
    "glowing_mushroom": "Grows in swamp regions. Dropped by zombies or harvested from Mushroom Groves.",
    # Orc drops (Mountain)
    "stone_block": "Mined from orcs in mountain regions. Also harvestable from Granite Quarries.",
    # Harvestable
    "herb": "Grows in forest regions. Harvestable from Herb Patch nodes.",
}


def get_sell_value_for_item(t: ItemTemplate) -> int:
    """Calculate sell value for display purposes."""
    if t.sell_value > 0:
        return t.sell_value
    if t.gold_value > 0:
        return t.gold_value
    return SELL_PRICES.get(t.rarity, 3)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/gameplay/classes.py
"""Hero class system — classes, skills, breakthrough, and mastery.

Heroes choose a class which provides:
  - Attribute bonuses (base + cap)
  - Class-specific skills (learnable at class buildings for gold)
  - Breakthrough path (e.g. Warrior → Champion at Lv10+ with STR 30+)
  - Mastery progression (using skills increases mastery)

All entities also have race skills (innate, no cost to learn).

Skill types:
  - ACTIVE: Costs stamina, has cooldown, used in combat/exploration
  - PASSIVE: Always active, provides stat bonuses
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import Annotated

from pydantic import PlainSerializer
from pydantic.dataclasses import dataclass as pydantic_dataclass

from src.core.models.enums import (
    DamageType, HeroClass, SkillType, SkillTarget, Element,
    SkillTypeSer, SkillTargetSer, HeroClassSer, DamageTypeSer, ElementSer
)

# ---------------------------------------------------------------------------
# Skill definition
# ---------------------------------------------------------------------------


@pydantic_dataclass(frozen=True)
class SkillDef:
    """Immutable skill template/definition."""
    skill_id: str
    name: str
    description: str
    skill_type: SkillTypeSer
    target: SkillTargetSer
    class_req: HeroClassSer       # NONE = race skill (no class required)
    level_req: int = 1
    gold_cost: int = 0         # Cost to learn at building
    cooldown: int = 5          # Ticks between uses
    stamina_cost: int = 10     # Stamina to activate
    # Effects
    power: float = 1.0         # Damage multiplier or heal amount multiplier
    duration: int = 0          # Buff/debuff duration in ticks
    range: int = 1             # Cast distance in tiles (how far you can use it)
    # AoE (epic-05 F1)
    radius: int = 0            # AoE spread from impact point (0 = single target)
    aoe_falloff: float = 0.15  # Damage reduction per tile from center (0.15 = -15%/tile)
    # Learning prerequisites
    mastery_req: str = ""       # Prerequisite skill_id that must have mastery >= mastery_threshold
    mastery_threshold: float = 25.0  # Min mastery on prerequisite skill
    # Stat modifiers (for passive skills)
    atk_mod: float = 0.0
    def_mod: float = 0.0
    spd_mod: float = 0.0
    crit_mod: float = 0.0
    evasion_mod: float = 0.0
    hp_mod: float = 0.0
    # Damage type: determines which stat pair (ATK/DEF vs MATK/MDEF) is used
    damage_type: DamageTypeSer = DamageType.PHYSICAL
    element: ElementSer = Element.NONE


# ---------------------------------------------------------------------------
# Skill Metadata (Legacy mapping to be replaced by JSON data)
# ---------------------------------------------------------------------------

# Skills that deal magical damage (use MATK instead of ATK)
_MAGICAL_SKILLS = frozenset({
    "arcane_bolt", "frost_shield", "mana_surge", "drain_life",
})

# Skill → element mapping (skills not listed default to NONE)
_SKILL_ELEMENTS: dict[str, Element] = {
    "frost_shield": Element.ICE,
    "arcane_bolt": Element.NONE,
    "drain_life": Element.DARK,
    "poison_blade": Element.DARK,
}


@dataclass(slots=True)
class SkillInstance:
    """A learned skill on an entity, tracking cooldown and mastery."""
    skill_id: str
    cooldown_remaining: int = 0
    mastery: float = 0.0       # 0.0 to 100.0
    times_used: int = 0

    def is_ready(self) -> bool:
        return self.cooldown_remaining <= 0

    def use(self, base_cooldown: int) -> None:
        self.cooldown_remaining = base_cooldown
        self.times_used += 1
        # Mastery gain: diminishing returns
        gain = max(0.1, 1.0 - self.mastery * 0.008)
        self.mastery = min(100.0, self.mastery + gain)

    def to_schema(self) -> SkillSchema:
        """Standardized serialization for the /state endpoint."""
        from src.api.schemas import SkillSchema
        return SkillSchema(
            skill_id=self.skill_id,
            mastery=self.mastery,
            cooldown_remaining=self.cooldown_remaining,
        )

    def tick(self) -> None:
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

    @property
    def mastery_tier(self) -> int:
        """0=novice, 1=apprentice(25), 2=adept(50), 3=expert(75), 4=master(100)"""
        if self.mastery >= 100.0:
            return 4
        if self.mastery >= 75.0:
            return 3
        if self.mastery >= 50.0:
            return 2
        if self.mastery >= 25.0:
            return 1
        return 0

    def effective_power(self, base_power: float) -> float:
        """Power modified by mastery. +20% at mastery tier 2+."""
        mult = 1.0
        if self.mastery >= 50.0:
            mult += 0.20
        if self.mastery >= 100.0:
            mult += 0.15  # Total +35% at master
        return base_power * mult

    def effective_stamina_cost(self, base_cost: int) -> int:
        """Stamina cost reduced by mastery. -10% at tier 1+, -20% at tier 3+."""
        mult = 1.0
        if self.mastery >= 25.0:
            mult -= 0.10
        if self.mastery >= 75.0:
            mult -= 0.10  # Total -20%
        return max(1, int(base_cost * mult))

    def effective_cooldown(self, base_cd: int) -> int:
        """Cooldown reduced by mastery. -10% at tier 2, -20% at tier 4."""
        mult = 1.0
        if self.mastery >= 50.0:
            mult -= 0.10
        if self.mastery >= 100.0:
            mult -= 0.10  # Total -20%
        return max(1, int(base_cd * mult))

    def to_api_schema(self) -> "SkillSchema":
        """Convert to API response schema (FastAPI/Pydantic)."""
        from src.api.schemas import SkillSchema
        from src.core.gameplay.classes import SKILL_DEFS, _MAGICAL_SKILLS, _SKILL_ELEMENTS
        from src.core.models.enums import Element
        
        sdef = SKILL_DEFS.get(self.skill_id)
        # Use new fields if present, else fallback to legacy constants
        if sdef and hasattr(sdef, "damage_type") and sdef.damage_type is not None:
             # This will be used once JSONs are updated
             dmg_type = "magical" if sdef.damage_type == 1 else "physical"
             element_name = sdef.element.name.lower() if hasattr(sdef, "element") else "none"
        else:
            dmg_type = "magical" if self.skill_id in _MAGICAL_SKILLS else "physical"
            element_enum = _SKILL_ELEMENTS.get(self.skill_id, Element.NONE)
            element_name = element_enum.name.lower()
        
        return SkillSchema(
            skill_id=self.skill_id,
            name=sdef.name if sdef else self.skill_id,
            cooldown_remaining=self.cooldown_remaining,
            mastery=self.mastery,
            times_used=self.times_used,
            skill_type=sdef.skill_type.name.lower() if sdef else "active",
            target=sdef.target.name.lower() if sdef else "self",
            stamina_cost=self.effective_stamina_cost(sdef.stamina_cost) if sdef else 0,
            cooldown=self.effective_cooldown(sdef.cooldown) if sdef else 0,
            power=self.effective_power(sdef.power) if sdef else 1.0,
            description=sdef.description if sdef else "",
            damage_type=dmg_type,
            element=element_name,
        )

    def copy(self) -> SkillInstance:
        return SkillInstance(
            skill_id=self.skill_id,
            cooldown_remaining=self.cooldown_remaining,
            mastery=self.mastery,
            times_used=self.times_used,
        )


# ---------------------------------------------------------------------------
# Class definition
# ---------------------------------------------------------------------------

# Attribute scaling grades — determines how effectively a class
# benefits from investing in each attribute.  Higher grades yield
# larger derived-stat bonuses from that attribute.
SCALING_GRADES = ('E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS')

SCALING_MULTIPLIER: dict[str, float] = {
    'E': 0.60, 'D': 0.75, 'C': 0.90, 'B': 1.00,
    'A': 1.15, 'S': 1.30, 'SS': 1.50, 'SSS': 1.80,
}


@pydantic_dataclass(frozen=True)
class ClassDef:
    """Immutable class template."""
    class_id: HeroClassSer
    name: str
    description: str
    # Attribute bonuses applied when class is chosen
    str_bonus: int = 0
    agi_bonus: int = 0
    vit_bonus: int = 0
    int_bonus: int = 0
    spi_bonus: int = 0
    wis_bonus: int = 0
    end_bonus: int = 0
    per_bonus: int = 0
    cha_bonus: int = 0
    # Attribute cap bonuses
    str_cap_bonus: int = 0
    agi_cap_bonus: int = 0
    vit_cap_bonus: int = 0
    int_cap_bonus: int = 0
    spi_cap_bonus: int = 0
    wis_cap_bonus: int = 0
    end_cap_bonus: int = 0
    per_cap_bonus: int = 0
    cha_cap_bonus: int = 0
    # Breakthrough target
    breakthrough_class: HeroClassSer = HeroClass.NONE
    breakthrough_level: int = 10
    breakthrough_attr: str = ""      # e.g. "str" — which attribute must be >= threshold
    breakthrough_threshold: int = 30
    # Attribute scaling grades (E–SSS)
    str_scaling: str = 'E'
    agi_scaling: str = 'E'
    vit_scaling: str = 'E'
    int_scaling: str = 'E'
    spi_scaling: str = 'E'
    wis_scaling: str = 'E'
    end_scaling: str = 'E'
    per_scaling: str = 'E'
    cha_scaling: str = 'E'
    # Lore & identity
    tier: int = 1                    # 1 = base, 2 = breakthrough, 3 = transcendence
    lore: str = ''
    playstyle: str = ''
    role: str = ''                   # e.g. "DPS", "Tank", "Support"
    # Starting gear & Skills
    starting_gear: dict[str, str | None] = field(default_factory=dict)
    class_skills: list[str] = field(default_factory=list)


@pydantic_dataclass(frozen=True)
class BreakthroughDef:
    """Breakthrough (promotion) definition."""
    from_class: HeroClassSer
    to_class: HeroClassSer
    level_req: int
    attr_req: str              # e.g. "str"
    attr_threshold: int
    # Bonuses on breakthrough
    str_bonus: int = 0
    agi_bonus: int = 0
    vit_bonus: int = 0
    int_bonus: int = 0
    spi_bonus: int = 0
    wis_bonus: int = 0
    end_bonus: int = 0
    per_bonus: int = 0
    cha_bonus: int = 0
    str_cap_bonus: int = 0
    agi_cap_bonus: int = 0
    vit_cap_bonus: int = 0
    int_cap_bonus: int = 0
    spi_cap_bonus: int = 0
    wis_cap_bonus: int = 0
    end_cap_bonus: int = 0
    per_cap_bonus: int = 0
    cha_cap_bonus: int = 0
    talent: str = ""           # Special passive ability name


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

# -- Class Definitions --

CLASS_DEFS: dict[HeroClass, ClassDef] = {}
SKILL_DEFS: dict[str, SkillDef] = {}
BREAKTHROUGHS: dict[HeroClass, BreakthroughDef] = {}

# ---------------------------------------------------------------------------
# Backward-compatible computed shims
# ---------------------------------------------------------------------------
# These properties let old consumer code (entity_builder, __main__, etc.)
# continue to reference RACE_SKILLS / CLASS_SKILLS / HERO_STARTING_GEAR
# while the actual data lives in RACE_PROFILES and CLASS_DEFS.

class _DictShim(dict):
    """Dict-like wrapper that lazily computes values from a registry."""
    def __init__(self, compute_fn, keys_fn=None):
        super().__init__()
        self._compute_fn = compute_fn
        self._keys_fn = keys_fn
    def __getitem__(self, key):
        return self._compute_fn(key)
    def get(self, key, default=None):
        val = self._compute_fn(key)
        return val if val is not None else default
    def __contains__(self, key):
        val = self._compute_fn(key)
        return val is not None and val != []
    def __iter__(self):
        if self._keys_fn:
            return iter(self._keys_fn())
        return super().__iter__()
    def __len__(self):
        if self._keys_fn:
            return len(self._keys_fn())
        return super().__len__()
    def items(self):
        if self._keys_fn:
            return [(k, self._compute_fn(k)) for k in self._keys_fn()]
        return super().items()

def _race_skills_lookup(race: str) -> list[str]:
    from src.core.models.enums import RACE_PROFILES
    profile = RACE_PROFILES.get(race)
    return list(profile.starting_skills) if profile else []

def _class_skills_lookup(hero_class) -> list[str]:
    cdef = CLASS_DEFS.get(hero_class)
    return list(cdef.class_skills) if cdef else []

def _hero_starting_gear_lookup(hero_class) -> dict[str, str | None]:
    cdef = CLASS_DEFS.get(hero_class)
    return dict(cdef.starting_gear) if cdef else {}

def _race_class_lookup(key) -> HeroClass:
    # key is (race, tier)
    if not isinstance(key, tuple): return HeroClass.NONE
    race, tier = key
    from src.core.world.spawn_config import SPAWN_CONFIGS
    cfg = SPAWN_CONFIGS.get((race, tier))
    if cfg:
        # Archetype is a HeroClass enum or int
        return HeroClass(cfg.archetype) if cfg.archetype else HeroClass.NONE
    return HeroClass.NONE

RACE_SKILLS = _DictShim(_race_skills_lookup)
CLASS_SKILLS = _DictShim(_class_skills_lookup)
HERO_STARTING_GEAR = _DictShim(_hero_starting_gear_lookup)
RACE_CLASS_MAP = _DictShim(_race_class_lookup)

# --- Building mapping remains as it's static meta ---
CLASS_BUILDING_MAP: dict[str, HeroClass] = {
    "warrior_hall":  HeroClass.WARRIOR,
    "ranger_lodge":  HeroClass.RANGER,
    "mage_tower":    HeroClass.MAGE,
    "rogue_den":     HeroClass.ROGUE,
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_attr_value(attrs, attr_name: str) -> int:
    """Get attribute value by string name."""
    mapping = {"str": attrs.str_, "agi": attrs.agi, "vit": attrs.vit,
               "int": attrs.int_, "spi": attrs.spi, "wis": attrs.wis,
               "end": attrs.end, "per": attrs.per, "cha": attrs.cha}
    return mapping.get(attr_name, 0)


def can_breakthrough(hero_class: HeroClass, level: int, attrs) -> bool:
    """Check if an entity can breakthrough to the next class."""
    bt = BREAKTHROUGHS.get(hero_class)
    if bt is None:
        return False
    if level < bt.level_req:
        return False
    return get_attr_value(attrs, bt.attr_req) >= bt.attr_threshold


def available_class_skills(hero_class: HeroClass, level: int) -> list[str]:
    """Get skill IDs available for a class at a given level (ignores mastery)."""
    cdef = CLASS_DEFS.get(hero_class)
    if not cdef:
        return []
    
    skill_ids = cdef.class_skills
    result = []
    for sid in skill_ids:
        sdef = SKILL_DEFS.get(sid)
        if sdef and level >= sdef.level_req:
            result.append(sid)
    return result


def can_learn_skill(
    sdef: SkillDef,
    level: int,
    known_skills: list[SkillInstance],
    class_mastery: float = 0.0,
) -> tuple[bool, str]:
    """Check whether a hero meets all requirements to learn a skill.

    Returns (can_learn, reason_if_not).
    """
    if level < sdef.level_req:
        return False, f"Requires level {sdef.level_req} (current: {level})"
    if sdef.mastery_req:
        prereq = None
        for si in known_skills:
            if si.skill_id == sdef.mastery_req:
                prereq = si
                break
        if prereq is None:
            prereq_def = SKILL_DEFS.get(sdef.mastery_req)
            prereq_name = prereq_def.name if prereq_def else sdef.mastery_req
            return False, f"Requires knowledge of {prereq_name}"
        if prereq.mastery < sdef.mastery_threshold:
            prereq_def = SKILL_DEFS.get(sdef.mastery_req)
            prereq_name = prereq_def.name if prereq_def else sdef.mastery_req
            return False, f"Requires {prereq_name} mastery {sdef.mastery_threshold:.0f}+ (current: {prereq.mastery:.0f})"
    return True, ""


# ---------------------------------------------------------------------------
# Race + Tier → Mob class mapping
# ---------------------------------------------------------------------------

def mob_class_for(race: str, tier: int) -> HeroClass:
    """Look up the mob archetype class for a given race and tier."""
    from src.core.world.spawn_config import SPAWN_CONFIGS
    from src.core.models.enums import EnemyTier
    
    cfg = SPAWN_CONFIGS.get((race, EnemyTier(tier)))
    return cfg.archetype if cfg else HeroClass.BRUTE

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/gameplay/effects.py
"""Status effect system — temporary buffs and debuffs on entities.

Design:
  - Effects are lightweight dataclasses attached to an entity.
  - Each effect has a type, stat multipliers, and a remaining duration (ticks).
  - The WorldLoop ticks down durations and removes expired effects.
  - Entity.effective_*() methods query active effects for multipliers.
  - New effect types can be added by extending EffectType and creating
    factory functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, unique


@unique
class EffectType(IntEnum):
    """Categories of status effects.  Extend to add new buff/debuff families."""

    TERRITORY_DEBUFF = 0      # Stat penalty for being on hostile territory
    TERRITORY_BUFF = 1        # Stat bonus for being on home territory
    POISON = 2                # DoT
    BERSERK = 3               # ATK up, DEF down
    SHIELD = 4                # Temporary DEF boost
    HASTE = 5                 # SPD boost
    SLOW = 6                  # SPD penalty
    SKILL_BUFF = 7            # Buff from a skill (self / ally)
    SKILL_DEBUFF = 8          # Debuff from a skill (applied to enemy)
    
    # Elemental States
    FROZEN = 10
    WET = 11
    SHOCKED = 12
    BURNED = 13
    SUPPRESSION = 14          # Regional fear effect
    CONQUERED_DEBUFF = 15     # Heavy penalty in conquered regions
    RESTED = 16               # Milestone 9: Well-Rested buff from Town Inn


@dataclass(slots=True)
class StatusEffect:
    """A temporary modifier applied to an entity.

    Multipliers are applied multiplicatively to base stats.
    A value of 1.0 means no change; < 1.0 is a debuff; > 1.0 is a buff.
    """

    effect_type: EffectType
    remaining_ticks: int        # -1 = permanent until explicitly removed, >0 = timed
    source: str = ""            # Human-readable origin, e.g. "goblin_camp_territory"

    # Stat multipliers (1.0 = neutral)
    atk_mult: float = 1.0
    def_mult: float = 1.0
    spd_mult: float = 1.0
    crit_mult: float = 1.0
    evasion_mult: float = 1.0
    max_hp_mult: float = 1.0
    xp_mult: float = 1.0 # Milestone 9 extension

    # Direct stat mods per tick
    hp_per_tick: int = 0
    stamina_per_tick: int = 0

    def tick(self) -> None:
        """Called each world tick if duration > 0."""
        if self.remaining_ticks > 0:
            self.remaining_ticks -= 1

    @property
    def expired(self) -> bool:
        """Expired if duration reached 0."""
        return self.remaining_ticks == 0

    def copy(self) -> StatusEffect:
        """Create a full copy (used when applying templates)."""
        return StatusEffect(
            effect_type=self.effect_type,
            remaining_ticks=self.remaining_ticks,
            source=self.source,
            atk_mult=self.atk_mult,
            def_mult=self.def_mult,
            spd_mult=self.spd_mult,
            crit_mult=self.crit_mult,
            evasion_mult=self.evasion_mult,
            max_hp_mult=self.max_hp_mult,
            xp_mult=self.xp_mult,
            hp_per_tick=self.hp_per_tick,
            stamina_per_tick=self.stamina_per_tick,
        )


# =====================================================================
# Factory functions for common effects
# =====================================================================

def territory_debuff(source: str, duration: int = -1, atk_mult: float = 0.8, def_mult: float = 0.8) -> StatusEffect:
    """Create a stat penalty for hostile territory."""
    return StatusEffect(
        effect_type=EffectType.TERRITORY_DEBUFF,
        remaining_ticks=duration,
        source=source,
        atk_mult=atk_mult,
        def_mult=def_mult,
    )


def territory_buff(source: str, duration: int = -1, atk_mult: float = 1.2, def_mult: float = 1.2) -> StatusEffect:
    """Create a stat bonus for home territory."""
    return StatusEffect(
        effect_type=EffectType.TERRITORY_BUFF,
        remaining_ticks=duration,
        source=source,
        atk_mult=atk_mult,
        def_mult=def_mult,
    )


def skill_buff(source: str, duration: int, atk_mod: float = 0.0, def_mod: float = 0.0, crit_mod: float = 0.0) -> StatusEffect:
    """Generic buff from a skill (e.g. atk_mod=0.15 → +15% ATK)."""
    return StatusEffect(
        effect_type=EffectType.SKILL_BUFF,
        remaining_ticks=duration,
        source=source,
        atk_mult=1.0 + atk_mod,
        def_mult=1.0 + def_mod,
        crit_mult=1.0 + crit_mod,
    )


def skill_debuff(source: str, duration: int, atk_mod: float = 0.0, def_mod: float = 0.0) -> StatusEffect:
    """Generic debuff from a skill (e.g. atk_mod=-0.15 → -15% ATK)."""
    return StatusEffect(
        effect_type=EffectType.SKILL_DEBUFF,
        remaining_ticks=duration,
        source=source,
        atk_mult=1.0 + atk_mod,
        def_mult=1.0 + def_mod,
    )


def skill_effect(source: str = "", duration: int = 1, atk_mod: float = 0.0, def_mod: float = 0.0, spd_mod: float = 0.0, crit_mod: float = 0.0, hp_per_tick: int = 0, is_debuff: bool = False) -> StatusEffect:
    """Legacy factory for skill-based effects (M6 compatibility)."""
    etype = EffectType.SKILL_DEBUFF if is_debuff else EffectType.SKILL_BUFF
    return StatusEffect(
        effect_type=etype,
        remaining_ticks=duration,
        source=source,
        atk_mult=1.0 + atk_mod,
        def_mult=1.0 + def_mod,
        spd_mult=1.0 + spd_mod,
        crit_mult=1.0 + crit_mod,
        hp_per_tick=hp_per_tick,
    )


def poison_effect(duration: int = 10, damage: int = 2, source: str = "poison") -> StatusEffect:
    """Poison DoT."""
    return StatusEffect(
        effect_type=EffectType.POISON,
        remaining_ticks=duration,
        source=source,
        hp_per_tick=-damage,
    )


def haste_effect(duration: int = 20, speed_mult: float = 1.5) -> StatusEffect:
    """SPD boost."""
    return StatusEffect(
        effect_type=EffectType.HASTE,
        remaining_ticks=duration,
        source="haste",
        spd_mult=speed_mult,
    )


def slow_effect(duration: int = 15, speed_mult: float = 0.5) -> StatusEffect:
    """SPD penalty."""
    return StatusEffect(
        effect_type=EffectType.SLOW,
        remaining_ticks=duration,
        source="slow",
        spd_mult=speed_mult,
    )


def frozen_effect(duration: int = 5) -> StatusEffect:
    """Freeze target (SPD down drastically)."""
    return StatusEffect(
        effect_type=EffectType.FROZEN,
        remaining_ticks=duration,
        source="frozen",
        spd_mult=0.0,  # Immobilized
    )


def wet_effect(duration: int = 8) -> StatusEffect:
    """Wet target (Lightning vulnerability)."""
    return StatusEffect(
        effect_type=EffectType.WET,
        remaining_ticks=duration,
        source="wet",
        def_mult=0.9,
    )


def burned_effect(duration: int = 5, damage: int = 3) -> StatusEffect:
    """Burn target (DoT)."""
    return StatusEffect(
        effect_type=EffectType.BURNED,
        remaining_ticks=duration,
        source="burned",
        hp_per_tick=-damage,
    )


def suppression_effect(duration: int = 100) -> StatusEffect:
    """Create a suppression debuff (regional fear after many deaths)."""
    return StatusEffect(
        effect_type=EffectType.SUPPRESSION,
        remaining_ticks=duration,
        source="regional_suppression",
        atk_mult=0.8,
        spd_mult=0.8,
    )


def conquered_debuff(duration: int = 2) -> StatusEffect:
    """Create a conquered region debuff (stronghold presence)."""
    return StatusEffect(
        effect_type=EffectType.CONQUERED_DEBUFF,
        remaining_ticks=duration,
        source="conquered_stronghold",
        atk_mult=0.8,
        def_mult=0.8,
        spd_mult=0.9, # Slight slowdown
    )


def well_rested_effect(duration: int = 100) -> StatusEffect:
    """Create a Well-Rested buff (+10% Max HP, +20% XP Gain)."""
    return StatusEffect(
        effect_type=EffectType.RESTED,
        remaining_ticks=duration,
        source="well_rested",
        max_hp_mult=1.1,
        xp_mult=1.2,
    )

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/gameplay/faction.py
"""Faction system — data-driven relationships between entity groups.

Design:
  - Every entity belongs to exactly one Faction.
  - Relationships between factions are stored in a registry and looked up at
    runtime, so new factions can be added without touching AI or combat code.
  - Each faction owns a territory tile type (Material) where its members heal
    and intruders receive debuffs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import TYPE_CHECKING

from src.core.models.enums import Material, Faction


# ---------------------------------------------------------------------------
# Relationship between two factions
# ---------------------------------------------------------------------------

@unique
class FactionRelation(IntEnum):
    """How two factions regard each other."""

    ALLIED = 0     # Will not attack; may cooperate
    NEUTRAL = 1    # Ignore each other (unless provoked)
    HOSTILE = 2    # Attack on sight


# ---------------------------------------------------------------------------
# Territory descriptor
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TerritoryInfo:
    """Describes what a faction considers home turf."""

    tile: Material                  # The Material that is this faction's territory
    atk_debuff: float = 0.7        # Multiplier applied to intruder ATK
    def_debuff: float = 0.7        # Multiplier applied to intruder DEF
    spd_debuff: float = 0.85       # Multiplier applied to intruder SPD
    alert_radius: int = 6          # How far the intrusion alert propagates


# ---------------------------------------------------------------------------
# Faction registry — single source of truth
# ---------------------------------------------------------------------------

class FactionRegistry:
    """Data-driven registry mapping factions → territories and relations.

    Usage:
        reg = FactionRegistry.default()
        reg.relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE)  # → HOSTILE
        reg.territory_for(Faction.GOBLIN_HORDE)                 # → TerritoryInfo(CAMP, ...)
        reg.identity.faction_for_kind("hero")                            # → Faction.HERO_GUILD
        reg.is_hostile(attacker_faction, defender_faction)       # → bool
        reg.owns_tile(Faction.HERO_GUILD, Material.TOWN)        # → True
    """

    __slots__ = ("_relations", "_territories", "_kind_map")

    def __init__(self) -> None:
        # (faction_a, faction_b) → FactionRelation  (order-independent)
        self._relations: dict[tuple[Faction, Faction], FactionRelation] = {}
        # faction → TerritoryInfo
        self._territories: dict[Faction, TerritoryInfo] = {}
        # entity kind string → faction
        self._kind_map: dict[str, Faction] = {}

    # -- builders --

    def set_relation(self, a: Faction, b: Faction, rel: FactionRelation) -> None:
        self._relations[(a, b)] = rel
        self._relations[(b, a)] = rel

    def set_territory(self, faction: Faction, info: TerritoryInfo) -> None:
        self._territories[faction] = info

    def register_kind(self, kind: str, faction: Faction) -> None:
        self._kind_map[kind] = faction

    # -- queries --

    def relation(self, a: Faction, b: Faction) -> FactionRelation:
        if a == b:
            return FactionRelation.ALLIED
        return self._relations.get((a, b), FactionRelation.NEUTRAL)

    def is_hostile(self, a: Faction, b: Faction) -> bool:
        return self.relation(a, b) == FactionRelation.HOSTILE

    def is_allied(self, a: Faction, b: Faction) -> bool:
        return self.relation(a, b) == FactionRelation.ALLIED

    def territory_for(self, faction: Faction) -> TerritoryInfo | None:
        return self._territories.get(faction)

    def faction_for_kind(self, kind: str) -> Faction | None:
        return self._kind_map.get(kind)

    def owns_tile(self, faction: Faction, mat: Material) -> bool:
        """Return True if *mat* is this faction's home territory tile."""
        info = self._territories.get(faction)
        return info is not None and info.tile == mat

    def tile_owner(self, mat: Material) -> Faction | None:
        """Return the faction that owns *mat*, or None."""
        for fac, info in self._territories.items():
            if info.tile == mat:
                return fac
        return None

    def is_home_territory(self, faction: Faction, mat: Material) -> bool:
        """Check if *mat* is home territory for *faction*."""
        return self.owns_tile(faction, mat)

    def is_enemy_territory(self, faction: Faction, mat: Material) -> bool:
        """Check if *mat* is territory of a hostile faction."""
        owner = self.tile_owner(mat)
        if owner is None:
            return False
        return self.is_hostile(faction, owner)

    # -- factory --

    @classmethod
    def default(cls) -> FactionRegistry:
        """Build the default registry with Hero Guild vs Goblin Horde."""
        reg = cls()

        # --- Relations: hero vs all hostile; most factions hostile to each other ---
        all_hostile = [
            Faction.GOBLIN_HORDE, Faction.WOLF_PACK, Faction.BANDIT_CLAN,
            Faction.UNDEAD, Faction.ORC_TRIBE, Faction.CENTAUR_HERD,
            Faction.FROST_KIN, Faction.LIZARDFOLK, Faction.DEMON_HORDE,
        ]
        for fac in all_hostile:
            reg.set_relation(Faction.HERO_GUILD, fac, FactionRelation.HOSTILE)
        # Inter-faction hostility (everyone fights everyone)
        for i, a in enumerate(all_hostile):
            for b in all_hostile[i + 1:]:
                reg.set_relation(a, b, FactionRelation.HOSTILE)
        # Exception: goblins and orcs are neutral
        reg.set_relation(Faction.GOBLIN_HORDE, Faction.ORC_TRIBE, FactionRelation.NEUTRAL)

        # --- Territories ---
        reg.set_territory(Faction.HERO_GUILD, TerritoryInfo(
            tile=Material.TOWN,
            atk_debuff=0.6, def_debuff=0.6, spd_debuff=0.8, alert_radius=6,
        ))
        reg.set_territory(Faction.GOBLIN_HORDE, TerritoryInfo(
            tile=Material.CAMP,
            atk_debuff=0.7, def_debuff=0.7, spd_debuff=0.85, alert_radius=6,
        ))
        reg.set_territory(Faction.WOLF_PACK, TerritoryInfo(
            tile=Material.FOREST,
            atk_debuff=0.8, def_debuff=0.8, spd_debuff=0.9, alert_radius=5,
        ))
        reg.set_territory(Faction.BANDIT_CLAN, TerritoryInfo(
            tile=Material.DESERT,
            atk_debuff=0.75, def_debuff=0.75, spd_debuff=0.85, alert_radius=6,
        ))
        reg.set_territory(Faction.UNDEAD, TerritoryInfo(
            tile=Material.SWAMP,
            atk_debuff=0.7, def_debuff=0.7, spd_debuff=0.8, alert_radius=7,
        ))
        reg.set_territory(Faction.ORC_TRIBE, TerritoryInfo(
            tile=Material.MOUNTAIN,
            atk_debuff=0.75, def_debuff=0.75, spd_debuff=0.85, alert_radius=6,
        ))
        reg.set_territory(Faction.CENTAUR_HERD, TerritoryInfo(
            tile=Material.GRASSLAND,
            atk_debuff=0.8, def_debuff=0.8, spd_debuff=0.9, alert_radius=8,
        ))
        reg.set_territory(Faction.FROST_KIN, TerritoryInfo(
            tile=Material.SNOW,
            atk_debuff=0.7, def_debuff=0.7, spd_debuff=0.8, alert_radius=6,
        ))
        reg.set_territory(Faction.LIZARDFOLK, TerritoryInfo(
            tile=Material.JUNGLE,
            atk_debuff=0.75, def_debuff=0.75, spd_debuff=0.85, alert_radius=5,
        ))
        reg.set_territory(Faction.DEMON_HORDE, TerritoryInfo(
            tile=Material.VOLCANIC,
            atk_debuff=0.65, def_debuff=0.65, spd_debuff=0.75, alert_radius=7,
        ))

        # --- Kind → faction mapping ---
        reg.register_kind("hero", Faction.HERO_GUILD)
        # Goblins
        reg.register_kind("goblin", Faction.GOBLIN_HORDE)
        reg.register_kind("goblin_scout", Faction.GOBLIN_HORDE)
        reg.register_kind("goblin_warrior", Faction.GOBLIN_HORDE)
        reg.register_kind("goblin_chief", Faction.GOBLIN_HORDE)
        # Wolves (forest)
        reg.register_kind("wolf", Faction.WOLF_PACK)
        reg.register_kind("dire_wolf", Faction.WOLF_PACK)
        reg.register_kind("alpha_wolf", Faction.WOLF_PACK)
        # Bandits (desert)
        reg.register_kind("bandit", Faction.BANDIT_CLAN)
        reg.register_kind("bandit_archer", Faction.BANDIT_CLAN)
        reg.register_kind("bandit_chief", Faction.BANDIT_CLAN)
        # Undead (swamp)
        reg.register_kind("skeleton", Faction.UNDEAD)
        reg.register_kind("zombie", Faction.UNDEAD)
        reg.register_kind("lich", Faction.UNDEAD)
        # Orcs (mountain)
        reg.register_kind("orc", Faction.ORC_TRIBE)
        reg.register_kind("orc_warrior", Faction.ORC_TRIBE)
        reg.register_kind("orc_warlord", Faction.ORC_TRIBE)
        # Centaurs (grassland)
        reg.register_kind("centaur", Faction.CENTAUR_HERD)
        reg.register_kind("centaur_lancer", Faction.CENTAUR_HERD)
        reg.register_kind("centaur_elder", Faction.CENTAUR_HERD)
        # Frost kin (snow)
        reg.register_kind("frost_wolf", Faction.FROST_KIN)
        reg.register_kind("frost_giant", Faction.FROST_KIN)
        reg.register_kind("frost_shaman", Faction.FROST_KIN)
        # Lizardfolk (jungle)
        reg.register_kind("lizard", Faction.LIZARDFOLK)
        reg.register_kind("lizard_warrior", Faction.LIZARDFOLK)
        reg.register_kind("lizard_chief", Faction.LIZARDFOLK)
        # Demons (volcanic)
        reg.register_kind("imp", Faction.DEMON_HORDE)
        reg.register_kind("hellhound", Faction.DEMON_HORDE)
        reg.register_kind("demon_lord", Faction.DEMON_HORDE)

        return reg

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/gameplay/items/__init__.py


#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/gameplay/items/item_registry.py
"""Standalone ITEM_REGISTRY to break circular dependencies."""

from __future__ import annotations

from typing import Annotated
from pydantic import PlainSerializer, BeforeValidator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from src.core.models.enums import (
    DamageType, Element, ItemType, Rarity,
    DamageTypeSer, ElementSer, ItemTypeSer, RaritySer
)

# Serialization helpers
def _parse_enum(cls):
    def _parse(v):
        if isinstance(v, cls): return v
        if isinstance(v, int):
            try: return cls(v)
            except ValueError: return v
        if isinstance(v, str):
            try: return cls[v.upper()]
            except KeyError: pass
        return v
    return _parse




@pydantic_dataclass(frozen=True)
class ItemTemplate:
    item_id: str
    name: str
    item_type: ItemTypeSer
    rarity: RaritySer
    weight: float = 1.0
    atk_bonus: int = 0
    def_bonus: int = 0
    spd_bonus: int = 0
    max_hp_bonus: int = 0
    crit_rate_bonus: float = 0.0
    evasion_bonus: float = 0.0
    luck_bonus: int = 0
    matk_bonus: int = 0
    mdef_bonus: int = 0
    damage_type: DamageTypeSer = DamageType.PHYSICAL
    element: ElementSer = Element.NONE
    weapon_range: int = 1
    heal_amount: int = 0
    mana_restore: int = 0
    gold_value: int = 0
    sell_value: int = 0
    description: str = ""


ITEM_REGISTRY: dict[str, ItemTemplate] = {}

def get_item(item_id: str) -> ItemTemplate | None:
    """Return an ItemTemplate from the registry, or None if not found."""
    return ITEM_REGISTRY.get(item_id)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/gameplay/items/items.py
"""Item, Equipment, and Inventory system for the RPG engine."""

from __future__ import annotations

# Re-export core registry components
from src.core.gameplay.items.item_registry import ITEM_REGISTRY, ItemTemplate

# Re-export core enums and factions used by items
from src.core.models.enums import EnemyTier, ItemType, Rarity, HeroClass
from src.core.gameplay.faction import Faction

# ---------------------------------------------------------------------------
# Class-based Weighting
# ---------------------------------------------------------------------------

CLASS_WEIGHTS: dict[HeroClass, dict[str, float]] = {
    HeroClass.WARRIOR: {"atk_bonus": 1.0, "def_bonus": 2.0, "hp_bonus": 2.0, "spd_bonus": 0.5},
    HeroClass.MAGE: {"matk_bonus": 2.5, "mdef_bonus": 1.5, "atk_bonus": 0.2, "hp_bonus": 0.5},
    HeroClass.RANGER: {"atk_bonus": 1.5, "crit_bonus": 2.0, "spd_bonus": 1.2, "def_bonus": 0.5},
    HeroClass.ROGUE: {"atk_bonus": 1.2, "crit_bonus": 2.5, "spd_bonus": 1.5, "evasion_bonus": 2.0},
    HeroClass.NONE: {"atk_bonus": 1.0, "def_bonus": 1.0, "hp_bonus": 1.0},
}

# Re-export moved models for backwards compatibility
from src.core.models.inventory import Inventory
from src.core.models.world_objects import HomeStorage, TreasureChest, CorpseNode


# ---------------------------------------------------------------------------
# Item power utilities
# ---------------------------------------------------------------------------

def _item_power(template, hero_class: HeroClass = HeroClass.NONE) -> int:
    """Calculate item power weighted by class priorities."""
    weights = CLASS_WEIGHTS.get(hero_class, CLASS_WEIGHTS[HeroClass.NONE])
    
    power = 0.0
    for attr, weight in weights.items():
        val = getattr(template, attr, 0)
        if isinstance(val, (int, float)):
            power += val * weight
            
    # Also add standard bonuses if they exist but aren't weighted
    all_attrs = ['atk_bonus', 'def_bonus', 'spd_bonus', 'hp_bonus', 'matk_bonus', 'mdef_bonus']
    for attr in all_attrs:
        if attr not in weights:
            val = getattr(template, attr, 0)
            if isinstance(val, (int, float)):
                power += val * 1.0

    # Percents (always weighted 100x base)
    for attr in ['crit_bonus', 'evasion_bonus']:
        val = getattr(template, attr, 0.0)
        if isinstance(val, (int, float)):
            power += val * 100 * weights.get(attr, 1.0)
    
    return int(power)


def item_power(item_id: str) -> int:
    """Public wrapper — returns 0 if item not found."""
    t = ITEM_REGISTRY.get(item_id)
    return _item_power(t) if t else 0


# ---------------------------------------------------------------------------
# Power calculation
# ---------------------------------------------------------------------------

TERRAIN_RACE: dict[int, str] = {
    6: "wolf",    # Material.FOREST
    7: "bandit",  # Material.DESERT
    8: "undead",  # Material.SWAMP
    9: "orc",     # Material.MOUNTAIN
}

HOUSE_UPGRADE_COSTS: dict[int, int] = {
    0: 200,
    1: 500,
}

CHEST_LOOT_TABLES: dict[int, list[tuple[str, float, int, int]]] = {
    1: [("iron_ore", 0.5, 1, 3), ("wood", 0.5, 2, 5)],
    2: [("silver_ingot", 0.3, 1, 2), ("mana_shard", 0.2, 1, 1)],
    3: [("gold_ingot", 0.1, 1, 1), ("phoenix_feather", 0.05, 1, 1)],
    4: [
        ("calamity_essence", 0.15, 1, 2),
        ("calamity_remnant", 0.10, 1, 1),
        ("enchanted_dust", 0.25, 1, 3),
        ("phoenix_feather", 0.20, 1, 2),
        ("gold_ingot", 0.30, 2, 5),
        ("mana_shard", 0.35, 2, 4),
    ],
}

RACE_FACTION: dict[str, Faction] = {
    "hero": Faction.HERO_GUILD,
    "goblin": Faction.GOBLIN_HORDE,
    "wolf": Faction.WOLF_PACK,
    "bandit": Faction.BANDIT_CLAN,
    "undead": Faction.UNDEAD,
    "orc": Faction.ORC_TRIBE,
}

DIFFICULTY_DROP_MULTIPLIER = {1: 1.0, 2: 1.2, 3: 1.5, 4: 2.0}

DIFFICULTY_BONUS_LOOT: dict[int, list[tuple[str, float]]] = {
    1: [],
    2: [("enchanted_dust", 0.03)],
    3: [("enchanted_dust", 0.1)],
    4: [("calamity_essence", 0.05), ("calamity_remnant", 0.02)],
}

# ---------------------------------------------------------------------------
# Backward-compatible shims for removed constants
# ---------------------------------------------------------------------------
# world_loop.py still imports these for the evolution system.
# They now compute from the SPAWN_CONFIGS registry.

def _build_race_tier_kinds() -> dict:
    """Build RACE_TIER_KINDS: {race: {tier_int: kind_string}}"""
    from src.core.world.spawn_config import SPAWN_CONFIGS
    result: dict[str, dict[int, str]] = {}
    for (race, tier), cfg in SPAWN_CONFIGS.items():
        result.setdefault(race, {})[int(tier)] = cfg.kind
    return result

def _build_tier_kind_names() -> dict:
    """Build TIER_KIND_NAMES: {tier_int: generic kind name}"""
    return {0: "goblin", 1: "goblin_scout", 2: "goblin_warrior", 3: "goblin_chief"}

def _build_race_starting_gear() -> dict:
    """Build RACE_STARTING_GEAR: {race: {tier: {slot: item_id}}}"""
    from src.core.world.spawn_config import SPAWN_CONFIGS
    result: dict[str, dict[int, dict[str, str]]] = {}
    for (race, tier), cfg in SPAWN_CONFIGS.items():
        if cfg.starting_gear:
            gear_dict: dict[str, str] = {}
            for item_id in cfg.starting_gear:
                # Infer slot from item name pattern
                if "sword" in item_id or "bow" in item_id or "staff" in item_id or "dagger" in item_id or "axe" in item_id or "mace" in item_id:
                    gear_dict["weapon"] = item_id
                elif "armor" in item_id or "vest" in item_id or "robe" in item_id or "mail" in item_id or "hide" in item_id:
                    gear_dict["armor"] = item_id
                else:
                    gear_dict.setdefault("accessory", item_id)
            result.setdefault(race, {})[int(tier)] = gear_dict
    return result

class _LazyDict(dict):
    """Dict that populates itself on first access."""
    def __init__(self, builder):
        super().__init__()
        self._builder = builder
        self._populated = False
    def _ensure(self):
        if not self._populated:
            self.update(self._builder())
            self._populated = True
    def __getitem__(self, key):
        self._ensure()
        return super().__getitem__(key)
    def get(self, key, default=None):
        self._ensure()
        return super().get(key, default)
    def __contains__(self, key):
        self._ensure()
        return super().__contains__(key)

RACE_TIER_KINDS = _LazyDict(_build_race_tier_kinds)
TIER_KIND_NAMES = _LazyDict(_build_tier_kind_names)
RACE_STARTING_GEAR = _LazyDict(_build_race_starting_gear)
TIER_STARTING_GEAR = _LazyDict(lambda: {
    1: {"weapon": "iron_sword", "armor": "leather_vest"},
    2: {"weapon": "steel_sword", "armor": "chainmail"},
    3: {"weapon": "windpiercer", "armor": "plate_armor"},
})

# ---------------------------------------------------------------------------
# Item & Equipment Classes (re-added for compatibility)
# ---------------------------------------------------------------------------

Item = ItemTemplate

class Weapon(Item): pass
class Armor(Item): pass
class Accessory(Item): pass
class Consumable(Item): pass
class MaterialItem(Item): pass

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/gameplay/quests.py
"""Quest system — generation, tracking, and completion for heroes.

Quest types:
  - HUNT: Kill N enemies of a specific kind.
  - EXPLORE: Visit a specific map coordinate.
  - GATHER: Collect N of a specific item.

Quests are generated at the Guild building and tracked per-entity.
Completion awards gold, XP, and optionally items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models import Vector2
    from src.platform.rng import DeterministicRNG
from src.core.models.enums import Faction


# ---------------------------------------------------------------------------
# Quest type enum
# ---------------------------------------------------------------------------

@unique
class QuestType(IntEnum):
    HUNT = 0       # Kill N enemies of a kind
    EXPLORE = 1    # Visit a map tile
    GATHER = 2     # Collect N items
    BOUNTY = 3     # Kill a world boss
    LIBERATE = 4   # Destroy a stronghold in a conquered region


# ---------------------------------------------------------------------------
# Quest data model
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Quest:
    """A single quest tracked on a hero."""

    quest_id: str              # Unique identifier, e.g. "hunt_goblin_3"
    quest_type: QuestType
    title: str
    description: str
    # Target specification
    target_kind: str = ""      # Enemy kind for HUNT, item_id for GATHER
    target_pos: Vector2 | None = None  # For EXPLORE
    target_count: int = 1      # How many to kill/collect
    # Progress
    progress: int = 0
    completed: bool = False
    # Rewards
    gold_reward: int = 0
    xp_reward: int = 0
    item_reward: str = ""      # Optional item_id reward

    @property
    def progress_ratio(self) -> float:
        if self.target_count <= 0:
            return 1.0
        return min(self.progress / self.target_count, 1.0)

    def advance(self, amount: int = 1) -> bool:
        """Advance quest progress. Returns True if quest just completed."""
        if self.completed:
            return False
        self.progress = min(self.progress + amount, self.target_count)
        if self.progress >= self.target_count:
            self.completed = True
            return True
        return False

    def copy(self) -> Quest:
        return Quest(
            quest_id=self.quest_id,
            quest_type=self.quest_type,
            title=self.title,
            description=self.description,
            target_kind=self.target_kind,
            target_pos=self.target_pos,
            target_count=self.target_count,
            progress=self.progress,
            completed=self.completed,
            gold_reward=self.gold_reward,
            xp_reward=self.xp_reward,
            item_reward=self.item_reward,
        )

    def to_dict(self) -> dict:
        d: dict = {
            "quest_id": self.quest_id,
            "quest_type": self.quest_type.name,
            "title": self.title,
            "description": self.description,
            "target_kind": self.target_kind,
            "target_count": self.target_count,
            "progress": self.progress,
            "completed": self.completed,
            "gold_reward": self.gold_reward,
            "xp_reward": self.xp_reward,
            "item_reward": self.item_reward,
        }
        if self.target_pos is not None:
            d["target_x"] = self.target_pos.x
            d["target_y"] = self.target_pos.y
        return d


# ---------------------------------------------------------------------------
# Quest templates — used by the generator
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class QuestTemplate:
    """Blueprint for generating quests."""
    template_id: str
    quest_type: QuestType
    title_fmt: str             # Python format string, e.g. "Hunt {count} {kind}"
    desc_fmt: str
    target_kinds: list[str]    # Possible target kinds/items
    count_range: tuple[int, int] = (1, 5)
    gold_range: tuple[int, int] = (20, 100)
    xp_range: tuple[int, int] = (30, 150)
    min_level: int = 1


QUEST_TEMPLATES: list[QuestTemplate] = [
    # Hunt quests
    QuestTemplate(
        "hunt_goblin", QuestType.HUNT,
        "Hunt {count} {kind}s", "Track down and eliminate {count} {kind}s terrorizing the region.",
        ["goblin", "goblin_scout", "goblin_warrior"],
        count_range=(2, 6), gold_range=(25, 80), xp_range=(40, 120),
    ),
    QuestTemplate(
        "hunt_wolf", QuestType.HUNT,
        "Cull {count} {kind}s", "The wolf population is growing. Cull {count} {kind}s.",
        ["wolf", "dire_wolf"],
        count_range=(2, 5), gold_range=(20, 60), xp_range=(30, 100),
    ),
    QuestTemplate(
        "hunt_bandit", QuestType.HUNT,
        "Eliminate {count} {kind}s", "Bandits have been raiding travelers. Eliminate {count} of them.",
        ["bandit", "bandit_archer", "bandit_chief"],
        count_range=(2, 5), gold_range=(30, 90), xp_range=(50, 130),
        min_level=2,
    ),
    QuestTemplate(
        "hunt_undead", QuestType.HUNT,
        "Purge {count} {kind}s", "Undead creatures stir in the swamps. Purge {count} {kind}s.",
        ["skeleton", "zombie"],
        count_range=(2, 5), gold_range=(35, 100), xp_range=(50, 140),
        min_level=3,
    ),
    QuestTemplate(
        "hunt_orc", QuestType.HUNT,
        "Defeat {count} {kind}s", "Orcs from the mountains threaten the realm. Defeat {count}.",
        ["orc", "orc_warrior"],
        count_range=(1, 4), gold_range=(50, 150), xp_range=(80, 200),
        min_level=4,
    ),
    # Gather quests
    QuestTemplate(
        "gather_herbs", QuestType.GATHER,
        "Gather {count} herbs", "The apothecary needs {count} herbs for potions.",
        ["herb"],
        count_range=(3, 8), gold_range=(15, 50), xp_range=(20, 60),
    ),
    QuestTemplate(
        "gather_ore", QuestType.GATHER,
        "Collect {count} iron ore", "The blacksmith needs raw materials.",
        ["iron_ore"],
        count_range=(2, 5), gold_range=(30, 80), xp_range=(30, 80),
        min_level=2,
    ),
    QuestTemplate(
        "gather_pelts", QuestType.GATHER,
        "Collect {count} wolf pelts", "The tanner needs wolf pelts for crafting.",
        ["wolf_pelt"],
        count_range=(2, 4), gold_range=(25, 60), xp_range=(25, 70),
    ),
    # Explore quests (target_pos filled at generation time)
    QuestTemplate(
        "explore_region", QuestType.EXPLORE,
        "Scout the frontier", "Explore an uncharted area of the map and report back.",
        [],
        count_range=(1, 1), gold_range=(20, 60), xp_range=(30, 80),
    ),
    QuestTemplate(
        "calamity_hunter", QuestType.BOUNTY,
        "Calamity: {kind}", "The world trembles. Slay {kind} and restore peace to the realm.",
        ["Gorath the World-Breaker", "Vexira the Soul-Weaver"],
        count_range=(1, 1), gold_range=(1000, 2000), xp_range=(1500, 3000),
        min_level=12,
    ),
    # Milestone 9: Dynamic Narrative Templates
    QuestTemplate(
        "liberate_region", QuestType.LIBERATE,
        "Liberate {kind}", "The region of {kind} has fallen! Destroy the monster stronghold and reclaim our lands.",
        [], # Filled dynamically
        count_range=(1, 1), gold_range=(500, 1000), xp_range=(800, 1500),
        min_level=8,
    ),
    QuestTemplate(
        "frontline_defense", QuestType.HUNT,
        "Frontline: {kind}s", "The war rages on. Culls {count} {kind}s on the frontlines.",
        ["goblin_warrior", "orc_warrior", "bandit_chief"],
        count_range=(3, 8), gold_range=(100, 300), xp_range=(150, 400),
        min_level=5,
    ),
]

TEMPLATE_MAP: dict[str, QuestTemplate] = {t.template_id: t for t in QUEST_TEMPLATES}


# ---------------------------------------------------------------------------
# Quest generation
# ---------------------------------------------------------------------------

MAX_ACTIVE_QUESTS = 3  # Max quests a hero can hold at once


def generate_quest(
    hero_level: int,
    existing_quest_ids: set[str],
    rng: DeterministicRNG,
    entity_id: int = 0,
    tick: int = 0,
    grid_width: int = 100,
    grid_height: int = 100,
    force_template_id: str | None = None,
    world: WorldState | None = None,
) -> Quest | None:
    """Generate a random quest appropriate for the hero's level.

    If force_template_id is provided, tries to use that specific template regardless of random chance.
    Returns None if no suitable template is available.
    """
    from src.core.models.enums import Domain
    from src.core.models import Vector2

    # Use tick offsets so each rng call produces a distinct value
    _seq = 0
    target_pos: Vector2 | None = None

    def _rng_int(lo: int, hi: int) -> int:
        nonlocal _seq
        _seq += 1
        return rng.next_int(Domain.AI_DECISION, entity_id, tick * 100 + _seq, lo, hi)

    if force_template_id:
        template = TEMPLATE_MAP.get(force_template_id)
        if not template:
            return None
    else:
        eligible = [t for t in QUEST_TEMPLATES if hero_level >= t.min_level]
        if not eligible:
            return None

        # Milestone 9: Dynamic Weighting
        weights = [1.0] * len(eligible)
        if world:
            for i, t in enumerate(eligible):
                # 1. Conquest weighting
                conquered_regions = [r for r in world.regions if r.owner_faction is not None and r.owner_faction != Faction.HERO_GUILD]
                if t.quest_type == QuestType.LIBERATE:
                    weights[i] = 10.0 if conquered_regions else 0.0
                
                # 2. War weighting
                is_at_war = any(status for status in world.war_status.values())
                if is_at_war and t.template_id == "frontline_defense":
                    weights[i] = 5.0
                
                # 3. Safe-zone weighting (prefer gather/explore)
                if t.quest_type in (QuestType.GATHER, QuestType.EXPLORE):
                    weights[i] = 2.0

        # Weighted selection
        total_w = sum(weights)
        if total_w <= 0: return None
        
        r_val = rng.next_float(Domain.AI_DECISION, entity_id, tick) * total_w
        running = 0.0
        template = eligible[0]
        for i, w in enumerate(weights):
            running += w
            if r_val <= running:
                template = eligible[i]
                break

    # Pick target kind
    if template.quest_type == QuestType.LIBERATE and world:
        conquered = [r for r in world.regions if r.owner_faction is not None and r.owner_faction != Faction.HERO_GUILD]
        if conquered:
            # Pick a conquered region
            r_idx = _rng_int(0, len(conquered) - 1)
            target_region = conquered[r_idx]
            target_kind = target_region.name
            target_pos = target_region.center
        else:
            return None
    elif template.target_kinds:
        kind_idx = _rng_int(0, len(template.target_kinds) - 1)
        target_kind = template.target_kinds[kind_idx]
    else:
        target_kind = ""

    # Determine count
    lo, hi = template.count_range
    count = _rng_int(lo, hi)

    # Build quest ID
    suffix = target_kind or "explore"
    quest_id = f"{template.template_id}_{suffix}_{count}"

    # Skip if hero already has this exact quest
    if quest_id in existing_quest_ids:
        return None

    # Gold and XP rewards scale with count and level
    g_lo, g_hi = template.gold_range
    gold = _rng_int(g_lo, g_hi)
    gold = int(gold * (1.0 + hero_level * 0.1))

    x_lo, x_hi = template.xp_range
    xp = _rng_int(x_lo, x_hi)
    xp = int(xp * (1.0 + hero_level * 0.1))

    # Format title and description
    kind_display = target_kind.replace("_", " ")
    title = template.title_fmt.format(count=count, kind=kind_display)
    desc = template.desc_fmt.format(count=count, kind=kind_display)

    # Target position for EXPLORE and LIBERATE quests
    if template.quest_type == QuestType.EXPLORE:
        tx = _rng_int(5, max(6, grid_width - 5))
        ty = _rng_int(5, max(6, grid_height - 5))
        target_pos = Vector2(tx, ty)
        title = f"Scout ({tx},{ty})"
        desc = f"Travel to coordinates ({tx},{ty}) and survey the area."
    elif template.quest_type == QuestType.LIBERATE:
        # target_pos already set in target kind block
        pass

    return Quest(
        quest_id=quest_id,
        quest_type=template.quest_type,
        title=title,
        description=desc,
        target_kind=target_kind,
        target_pos=target_pos,
        target_count=count,
        gold_reward=gold,
        xp_reward=xp,
    )

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/models/__init__.py
from src.core.entities.entity import Entity
from src.core.entities.stats import Stats
from src.core.entities.stats_proxy import StatsProxy
from .enums import AIState, DamageType, Element, EnemyTier, EntityRole, TraitType, HeroClass, Domain, Material, ActionType, Direction
from .vectors import Vector2, FloatVector2, DIRECTION_OFFSETS
from .snapshot import Snapshot
from .world_state import WorldState
from .base import Aspect
from .world_objects import HomeStorage, TreasureChest, CorpseNode

# Re-export InventoryAspect as Inventory for compatibility
from .inventory import Inventory

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/models/base.py
from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Type, Any
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

T = TypeVar("T", bound="Aspect")

class Aspect(BaseModel):
    """Base class for all entity functional modules (Aspects/Components).
    
    Aspects are Pydantic models that hold both data and lifecycle hooks.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Internal reference to the parent entity (not serialized)
    _entity: Any = PrivateAttr(default=None)

    def on_attach(self, entity: Entity) -> None:
        """Called when the aspect is added to an entity."""
        self._entity = entity

    def on_tick(self, tick: int) -> None:
        """Lifecycle hook called every world tick."""
        pass
    
    @property
    def entity(self) -> Entity:
        if self._entity is None:
            raise RuntimeError(f"Aspect {self.__class__.__name__} is not attached to an entity.")
        return self._entity

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/models/calamities.py
"""World Boss (Calamity) templates and definitions."""

from __future__ import annotations
from dataclasses import dataclass, field
from src.core.models.enums import Faction, HeroClass

@dataclass(frozen=True, slots=True)
class CalamityTemplate:
    """Blueprint for a world boss."""
    template_id: str
    name: str
    faction: Faction
    archetype: HeroClass
    stat_multiplier: float = 5.0
    legendary_loot: list[str] = field(default_factory=list)
    traits: list[int] = field(default_factory=list)
    description: str = ""

CALAMITY_TEMPLATES: dict[str, CalamityTemplate] = {
    "gorath": CalamityTemplate(
        template_id="gorath",
        name="Gorath the World-Breaker",
        faction=Faction.ORC_TRIBE,
        archetype=HeroClass.CHAMPION,
        stat_multiplier=6.0,
        legendary_loot=["gorath_cleaver", "calamity_remnant"],
        traits=[0, 12, 14],  # AGGRESSIVE, BERSERKER, RESILIENT (manual map for now)
        description="A mountain-sized orc warlord whose mere footsteps crack the earth."
    ),
    "vexira": CalamityTemplate(
        template_id="vexira",
        name="Vexira the Soul-Weaver",
        faction=Faction.UNDEAD,
        archetype=HeroClass.ARCHMAGE,
        stat_multiplier=5.0,
        legendary_loot=["vexira_fang", "calamity_remnant"],
        traits=[1, 13, 15],  # CAUTIOUS, TACTICAL, ARCANE_GIFTED
        description="An ancient lich queen who drains the life from entire regions."
    )
}

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/models/enums.py
"""Enumerations."""
from __future__ import annotations
from enum import IntEnum, unique

@unique
class ActionType(IntEnum):
    REST = 0; MOVE = 1; ATTACK = 2; USE_ITEM = 3; LOOT = 4; HARVEST = 5; USE_SKILL = 6; REPAIR = 7

@unique
class SkillType(IntEnum):
    """Skill categories."""
    ACTIVE = 0
    PASSIVE = 1

@unique
class SkillTarget(IntEnum):
    """Who a skill targets."""
    SELF = 0
    SINGLE_ENEMY = 1
    AREA_ENEMIES = 2
    SINGLE_ALLY = 3
    AREA_ALLIES = 4

@unique
class AIState(IntEnum):
    IDLE = 0; WANDER = 1; HUNT = 2; COMBAT = 3; FLEE = 4; RETURN_TO_TOWN = 5; RESTING_IN_TOWN = 6; RETURN_TO_CAMP = 7; GUARD_CAMP = 8; LOOTING = 9; ALERT = 10; VISIT_SHOP = 11; VISIT_BLACKSMITH = 12; VISIT_GUILD = 13; HARVESTING = 14; VISIT_CLASS_HALL = 15; VISIT_INN = 16; VISIT_HOME = 17; RAID = 18; EXHAUSTED = 19; RECOVER_CORPSE = 20

@unique
class Direction(IntEnum): NORTH = 0; EAST = 1; SOUTH = 2; WEST = 3

@unique
class Domain(IntEnum): COMBAT = 0; LOOT = 1; AI_DECISION = 2; SPAWN = 3; WEATHER = 4; LEVEL_UP = 5; ITEM = 6; HARVEST = 7; MAP_GEN = 8; CALAMITY = 9

@unique
class Material(IntEnum): FLOOR = 0; WALL = 1; WATER = 2; TOWN = 3; CAMP = 4; SANCTUARY = 5; FOREST = 6; DESERT = 7; SWAMP = 8; MOUNTAIN = 9; ROAD = 10; BRIDGE = 11; RUINS = 12; DUNGEON_ENTRANCE = 13; LAVA = 14; GRASSLAND = 15; SNOW = 16; JUNGLE = 17; SHALLOW_WATER = 18; FARMLAND = 19; CAVE = 20; VOLCANIC = 21; GRAVEYARD = 22

@unique
class ItemType(IntEnum): WEAPON = 0; ARMOR = 1; ACCESSORY = 2; CONSUMABLE = 3; MATERIAL = 4

@unique
class Rarity(IntEnum): COMMON = 0; UNCOMMON = 1; RARE = 2; EPIC = 3; LEGENDARY = 4

@unique
class EntityRole(IntEnum): HERO = 0; MOB = 1; NPC = 2; WORLD_BOSS = 3; STRONGHOLD = 4

@unique
class EnemyTier(IntEnum):
    """Enemy difficulty tiers — affects stats, behavior, and loot."""

    BASIC = 0
    SCOUT = 1
    WARRIOR = 2
    ELITE = 3

@unique
class HeroClass(IntEnum):
    """Available classes for hero entities and mob archetypes."""
    NONE = 0
    # --- Primary Hero Classes ---
    WARRIOR = 1
    RANGER = 2
    MAGE = 3
    ROGUE = 4
    # --- Breakthrough Classes (Tier 2) ---
    CHAMPION = 5
    SHARPSHOOTER = 6
    ARCHMAGE = 7
    ASSASSIN = 8
    # --- Transcendence Classes (Tier 3) ---
    WARLORD = 9
    STORM_CALLER = 10
    GHOST_STALKER = 11
    NIGHTSHADE = 12
    # --- Mob Archetypes ---
    BRUTE = 20
    SCOUT = 21
    CASTER = 22
    TANK = 23
    BEAST = 24

class Faction(IntEnum):
    """World factions for alignment, territory, and aggression."""
    HERO_GUILD = 0
    GOBLIN_HORDE = 1
    WOLF_PACK = 2
    BANDIT_CLAN = 3
    UNDEAD = 4
    ORC_TRIBE = 5
    CENTAUR_HERD = 6
    FROST_KIN = 7
    LIZARDFOLK = 8
    DEMON_HORDE = 9
    # Legacy aliases (to be removed in future refactor)
    GOBLIN_TRIBE = 1
    BANDIT_GANG = 3
    UNDEAD_HORDE = 4
    ORC_CLAN = 5

@unique
class DamageType(IntEnum): PHYSICAL = 0; MAGICAL = 1

@unique
class Element(IntEnum): NONE = 0; FIRE = 1; ICE = 2; LIGHTNING = 3; DARK = 4; HOLY = 5

@unique
class TraitType(IntEnum): AGGRESSIVE = 0; CAUTIOUS = 1; BRAVE = 2; COWARDLY = 3; BLOODTHIRSTY = 4; GREEDY = 5; GENEROUS = 6; CHARISMATIC = 7; LONER = 8; DILIGENT = 9; LAZY = 10; CURIOUS = 11; BERSERKER = 12; TACTICAL = 13; RESILIENT = 14; ARCANE_GIFTED = 15; SPIRIT_TOUCHED = 16; ELEMENTALIST = 17; KEEN_EYED = 18; OBLIVIOUS = 19

@unique
class VeterancyRank(IntEnum): GREEN = 0; BLOODED = 1; VETERAN = 2; ELITE = 3; LEGEND = 4

from typing import Annotated
from pydantic import BeforeValidator, PlainSerializer

def _parse_enum(cls):
    def _parse(v):
        if isinstance(v, cls): return v
        if isinstance(v, int):
            try: return cls(v)
            except ValueError: return v
        if isinstance(v, str):
            try: return cls[v.upper()]
            except (KeyError, ValueError): pass
        return v
    return _parse

FactionSer = Annotated[Faction, BeforeValidator(_parse_enum(Faction)), PlainSerializer(lambda v: Faction(v).name.lower(), return_type=str)]
HeroClassSer = Annotated[HeroClass, BeforeValidator(_parse_enum(HeroClass)), PlainSerializer(lambda v: HeroClass(v).name.lower(), return_type=str)]
EnemyTierSer = Annotated[EnemyTier, BeforeValidator(_parse_enum(EnemyTier)), PlainSerializer(lambda v: EnemyTier(v).name.lower(), return_type=str)]
ItemTypeSer = Annotated[ItemType, BeforeValidator(_parse_enum(ItemType)), PlainSerializer(lambda v: ItemType(v).name.lower(), return_type=str)]
RaritySer = Annotated[Rarity, BeforeValidator(_parse_enum(Rarity)), PlainSerializer(lambda v: Rarity(v).name.lower(), return_type=str)]
SkillTypeSer = Annotated[SkillType, BeforeValidator(_parse_enum(SkillType)), PlainSerializer(lambda v: SkillType(v).name.lower(), return_type=str)]
SkillTargetSer = Annotated[SkillTarget, BeforeValidator(_parse_enum(SkillTarget)), PlainSerializer(lambda v: SkillTarget(v).name.lower(), return_type=str)]
DamageTypeSer = Annotated[int, BeforeValidator(_parse_enum(DamageType)), PlainSerializer(lambda v: DamageType(v).name.lower(), return_type=str)]
ElementSer = Annotated[int, BeforeValidator(_parse_enum(Element)), PlainSerializer(lambda v: Element(v).name.lower(), return_type=str)]

from dataclasses import dataclass, field
@dataclass(frozen=True)
class RaceProfile:
    train_rate: float
    level_cap: int
    evolves: bool
    starting_skills: list[str] = field(default_factory=list)
    factions: list[FactionSer] = field(default_factory=list)
    stat_mods: list[float] = field(default_factory=lambda: [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

RACE_PROFILES: dict[str, RaceProfile] = {}

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/models/inventory.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.gameplay.items.item_registry import ITEM_REGISTRY
    from src.core.gameplay.items.items import ItemType

@dataclass(slots=True)
class Inventory:
    """Mutable item container with slot and weight limits."""
    items: list[str] = field(default_factory=list)
    max_slots: int = 8
    max_weight: float = 20.0
    weapon: str | None = None
    armor: str | None = None
    accessory: str | None = None

    @property
    def current_weight(self) -> float:
        total = 0.0
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        for iid in self.items:
            t = ITEM_REGISTRY.get(iid)
            if t: total += t.weight
        for slot_id in (self.weapon, self.armor, self.accessory):
            if slot_id:
                t = ITEM_REGISTRY.get(slot_id)
                if t: total += t.weight
        return total

    @property
    def total_weight(self) -> float:
        return self.current_weight

    @property
    def used_slots(self) -> int: return len(self.items)

    @property
    def is_full(self) -> bool:
        return self.used_slots >= self.max_slots

    @property
    def is_effectively_full(self) -> bool:
        """True if inventory is full by slots or near weight limit."""
        return self.is_full or (self.current_weight >= self.max_weight * 0.9)

    @property
    def weight_ratio(self) -> float:
        """Ratio of current weight to max weight (0.0 to 1.0+)."""
        if self.max_weight <= 0:
            return 1.0
        return self.current_weight / self.max_weight

    def count_item(self, item_id: str) -> int:
        """Count how many copies of item_id are in the bag."""
        return self.items.count(item_id)

    def has_consumable(self, item_id: str) -> bool:
        """Check if item_id is in inventory."""
        return item_id in self.items
    
    def can_add(self, item_id: str) -> bool:
        if self.used_slots >= self.max_slots: return False
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        t = ITEM_REGISTRY.get(item_id)
        if t is None: return False
        return self.current_weight + t.weight <= self.max_weight

    def add_item(self, item_id: str) -> bool:
        if not self.can_add(item_id): return False
        self.items.append(item_id)
        return True

    def remove_item(self, item_id: str) -> bool:
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False

    def equip(self, item_id: str) -> bool:
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        from src.core.gameplay.items.items import ItemType
        t = ITEM_REGISTRY.get(item_id)
        if t is None or item_id not in self.items: return False
        if t.item_type == ItemType.WEAPON:
            if self.weapon: self.items.append(self.weapon)
            self.weapon = item_id
        elif t.item_type == ItemType.ARMOR:
            if self.armor: self.items.append(self.armor)
            self.armor = item_id
        elif t.item_type == ItemType.ACCESSORY:
            if self.accessory: self.items.append(self.accessory)
            self.accessory = item_id
        else: return False
        self.items.remove(item_id)
        return True

    def auto_equip_best(self, item_id: str) -> bool:
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        from src.core.gameplay.items.items import ItemType, _item_power
        t = ITEM_REGISTRY.get(item_id)
        if t is None or item_id not in self.items: return False
        if t.item_type not in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY): return False
        if t.item_type == ItemType.WEAPON: current_id = self.weapon
        elif t.item_type == ItemType.ARMOR: current_id = self.armor
        else: current_id = self.accessory
        if current_id is None: return self.equip(item_id)
        current_t = ITEM_REGISTRY.get(current_id)
        if current_t is None or _item_power(t) > _item_power(current_t):
            return self.equip(item_id)
        return False

    def copy(self) -> Inventory:
        return Inventory(items=list(self.items), max_slots=self.max_slots, max_weight=self.max_weight, weapon=self.weapon, armor=self.armor, accessory=self.accessory)

    def equipment_bonus(self, stat: str) -> int | float:
        total = 0
        from src.core.gameplay.items.items import ITEM_REGISTRY
        for slot_id in (self.weapon, self.armor, self.accessory):
            if slot_id:
                t = ITEM_REGISTRY.get(slot_id)
                if t: total += getattr(t, stat, 0)
        return total

    def get_all_item_ids(self) -> list[str]:
        result = list(self.items)
        if self.weapon: result.append(self.weapon)
        if self.armor: result.append(self.armor)
        if self.accessory: result.append(self.accessory)
        return result

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/models/snapshot.py
"""Immutable snapshot of the world state for worker threads."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Mapping

from src.core.gameplay.buildings import Building
from src.core.world.grid import Grid
from src.core.entities.entity import Entity
from src.core.models.world_objects import TreasureChest
from src.core.world.regions import Region
from src.core.world.resource_nodes import ResourceNode
from src.core.models.world_state import WorldState

_SPATIAL_CELL = 16  # cell size for snapshot spatial index


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Read-only view of the world, safe to share across threads.

    Uses deep-copied entities and a MappingProxyType for the entity dict
    to enforce immutability at runtime.
    """

    tick: int
    seed: int
    entities: Mapping[int, Entity]
    grid: Grid
    ground_items: Mapping[tuple[int, int], list[str]]
    camps: tuple[tuple[int, int], ...]
    buildings: tuple[Building, ...]
    resource_nodes: tuple[ResourceNode, ...]
    treasure_chests: tuple[TreasureChest, ...]
    regions: tuple[Region, ...]
    # Strategic State (Milestone 11)
    region_control: Mapping[str, float] = field(default_factory=dict)
    war_status: Mapping[int, bool] = field(default_factory=dict)
    faction_aggression: Mapping[int, float] = field(default_factory=dict)
    _spatial: dict = field(default_factory=dict, repr=False, compare=False)
    _spatial_ground: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def world_day(self) -> int:
        return self.tick // 100

    @classmethod
    def from_world(cls, world: WorldState) -> Snapshot:
        copied_entities = {eid: e.copy() for eid, e in world.entities.items()}
        copied_ground = {k: list(v) for k, v in world.ground_items.items()}
        
        # Build lightweight spatial index for fast neighbor queries
        spatial: dict[tuple[int, int], list[int]] = defaultdict(list)
        for eid, e in copied_entities.items():
            if e.stats.combat.hp > 0 and e.kind != "generator":
                spatial[(e.spatial.pos.x // _SPATIAL_CELL, e.spatial.pos.y // _SPATIAL_CELL)].append(eid)
                
        # NEW: Spatial index for ground items to avoid O(N_ground) scans
        spatial_ground: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
        for pos_key, items in copied_ground.items():
            if items:
                # Key is (gx, gy)
                spatial_ground[(pos_key[0] // _SPATIAL_CELL, pos_key[1] // _SPATIAL_CELL)].append(pos_key)
                
        return cls(
            tick=world.tick,
            seed=world.seed,
            entities=copied_entities,
            grid=world.grid,
            ground_items=copied_ground,
            camps=tuple((c.x, c.y) for c in world.camps),
            buildings=tuple(world.buildings),
            resource_nodes=tuple(n.copy() for n in world.resource_nodes.values()),
            treasure_chests=tuple(c.copy() for c in world.treasure_chests.values()),
            regions=tuple(r.copy() for r in world.regions),
            region_control=dict(world.region_control),
            war_status=dict(world.war_status),
            faction_aggression=dict(world.faction_aggression),
            _spatial=dict(spatial),
            _spatial_ground=dict(spatial_ground),
        )

    def nearby_entity_ids(self, x: int, y: int, radius: int) -> list[int]:
        """Return entity IDs in cells overlapping the Manhattan-radius neighborhood."""
        cx, cy = x // _SPATIAL_CELL, y // _SPATIAL_CELL
        r = (radius // _SPATIAL_CELL) + 1
        result: list[int] = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                bucket = self._spatial.get((cx + dx, cy + dy))
                if bucket:
                    result.extend(bucket)
        return result

    def nearby_ground_positions(self, x: int, y: int, radius: int) -> list[tuple[int, int]]:
        """Return ground item positions (gx, gy) in neighboring spatial cells."""
        cx, cy = x // _SPATIAL_CELL, y // _SPATIAL_CELL
        r = (radius // _SPATIAL_CELL) + 1
        result: list[tuple[int, int]] = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                bucket = self._spatial_ground.get((cx + dx, cy + dy))
                if bucket:
                    result.extend(bucket)
        return result

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/models/vectors.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Vector2:
    """Immutable 2D integer coordinate."""

    x: int = 0
    y: int = 0

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def manhattan(self, other: Vector2) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"


@dataclass(frozen=True, slots=True)
class FloatVector2:
    """Immutable 2D float coordinate for physics and smoothing."""
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: FloatVector2) -> FloatVector2:
        return FloatVector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: FloatVector2) -> FloatVector2:
        return FloatVector2(self.x - other.x, self.y - other.y)

    def length(self) -> float:
        import math
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self) -> FloatVector2:
        L = self.length()
        if L < 1e-6: return FloatVector2(0, 0)
        return FloatVector2(self.x / L, self.y / L)

    def __repr__(self) -> str:
        return f"f({self.x:.2f}, {self.y:.2f})"


# Direction offsets mapped to Direction enum values
DIRECTION_OFFSETS: dict[int, Vector2] = {
    0: Vector2(0, -1),  # NORTH
    1: Vector2(1, 0),   # EAST
    2: Vector2(0, 1),   # SOUTH
    3: Vector2(-1, 0),  # WEST
}

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/models/world_objects.py
from __future__ import annotations
from dataclasses import dataclass, field
from src.core.models.vectors import Vector2

@dataclass(slots=True)
class HomeStorage:
    """Persistent storage located at the hero's home."""
    items: list[str] = field(default_factory=list)
    max_slots: int = 20
    level: int = 0

    @property
    def used_slots(self) -> int:
        return len(self.items)

    @property
    def is_full(self) -> bool:
        return self.used_slots >= self.max_slots

    def add_item(self, item_id: str) -> bool:
        if self.is_full:
            return False
        self.items.append(item_id)
        return True

    def remove_item(self, item_id: str) -> bool:
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False

    def upgrade_cost(self) -> int | None:
        """Gold cost to upgrade storage capacity."""
        costs = {0: 200, 1: 500}
        return costs.get(self.level)

    def upgrade(self) -> bool:
        cost = self.upgrade_cost()
        if cost is None:
            return False
        self.level += 1
        self.max_slots += 20 if self.level == 1 else 30
        return True

    def copy(self) -> HomeStorage:
        return HomeStorage(
            items=list(self.items),
            max_slots=self.max_slots,
            level=self.level,
        )


@dataclass(slots=True)
class TreasureChest:
    """A respawning treasure chest placed in the world."""
    chest_id: int
    pos: Vector2
    tier: int = 1
    looted: bool = False
    respawn_at: int | None = None
    guard_entity_id: int | None = None

    @property
    def is_available(self) -> bool:
        return not self.looted

    def loot(self, current_tick: int, respawn_ticks: int = 50) -> None:
        self.looted = True
        self.respawn_at = current_tick + respawn_ticks

    def try_respawn(self, current_tick: int) -> bool:
        if not self.looted or self.respawn_at is None:
            return False
        if current_tick >= self.respawn_at:
            self.looted = False
            self.respawn_at = None
            return True
        return False

    def copy(self) -> TreasureChest:
        return TreasureChest(
            chest_id=self.chest_id,
            pos=self.pos,
            tier=self.tier,
            looted=self.looted,
        )

@dataclass(slots=True)
class CorpseNode:
    """A retrievable 'grave' left by a deceased entity (Hero/Boss)."""
    node_id: int
    entity_id: int
    pos: Vector2
    items: list[str] = field(default_factory=list)
    gold: int = 0
    created_tick: int = 0

    def copy(self) -> CorpseNode:
        return CorpseNode(
            node_id=self.node_id,
            entity_id=self.entity_id,
            pos=self.pos,
            items=list(self.items),
            gold=self.gold,
            created_tick=self.created_tick
        )

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/models/world_state.py
"""Mutable authoritative world state — only mutated by the WorldLoop."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.gameplay.buildings import Building
from src.core.world.grid import Grid
from src.core.entities.entity import Entity
from .vectors import Vector2
from .world_objects import TreasureChest
from src.core.world.regions import Region
from src.core.world.resource_nodes import ResourceNode

if TYPE_CHECKING:
    from src.platform.spatial_hash import SpatialHash


class WorldState:
    """The single source of truth for the simulation."""

    __slots__ = ("world_age", "faction_aggression", "difficulty_modifier", "monuments", "tick", "seed", "entities", "grid", "spatial_index", "_next_entity_id", "ground_items", "camps", "buildings", "resource_nodes", "_next_node_id", "treasure_chests", "_next_chest_id", "regions", "maturity", "last_calamity_tick", "event_bus", "faction_deaths_per_region", "region_control", "war_status", "history", "_history_subscribed", "town_treasury", "corpse_nodes", "_next_corpse_id")

    def __init__(
        self,
        seed: int,
        grid: Grid,
        spatial_index: SpatialHash,
    ) -> None:
        self.tick: int = 0
        self.seed: int = seed
        self.world_age: int = 0
        self.maturity: int = 0
        self.last_calamity_tick: int = 0
        self.faction_aggression: dict[int, float] = {}
        self.faction_deaths_per_region: dict[tuple[int, int], int] = {} # (faction_id, region_id) -> count
        self.region_control: dict[str, float] = {} # region_id -> influence (-100 to 100)
        self.war_status: dict[int, bool] = {} # faction_id -> is_at_war
        self.history: list[dict] = []
        self._history_subscribed: bool = False
        self.difficulty_modifier: float = 1.0
        self.monuments: list = []
        self.entities: dict[int, Entity] = {}
        self.grid: Grid = grid
        self.spatial_index: SpatialHash = spatial_index
        self._next_entity_id: int = 1
        self.ground_items: dict[tuple[int, int], list[str]] = {}
        self.camps: list[Vector2] = []
        self.buildings: list[Building] = []
        self.resource_nodes: dict[int, ResourceNode] = {}
        self._next_node_id: int = 1
        self.treasure_chests: dict[int, TreasureChest] = {}
        self._next_chest_id: int = 1
        self.regions: list[Region] = []
        self.town_treasury: int = 0
        self.corpse_nodes: dict[int, CorpseNode] = {}
        self._next_corpse_id: int = 1
        self.event_bus = None

    def allocate_entity_id(self) -> int:
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid

    @property
    def world_day(self) -> int:
        return self.tick // 100

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity
        self.spatial_index.insert(entity.id, entity.spatial.pos)

    def remove_entity(self, entity_id: int) -> Entity | None:
        entity = self.entities.pop(entity_id, None)
        if entity is not None:
            self.spatial_index.remove(entity_id, entity.spatial.pos)
        return entity

    def move_entity(self, entity_id: int, new_pos: Vector2) -> None:
        entity = self.entities.get(entity_id)
        if entity is None:
            return
        old_pos = entity.spatial.pos
        entity.spatial.pos = new_pos
        self.spatial_index.move(entity_id, old_pos, new_pos)

    def entities_at_radius(self, pos: Vector2, radius: int) -> list[Entity]:
        """Return all entities within *radius* of *pos*."""
        ids = self.spatial_index.query_radius(pos, radius)
        return [self.entities[eid] for eid in ids if eid in self.entities]

    def drop_items(self, pos: Vector2, item_ids: list[str]) -> None:
        """Place items on the ground at *pos*."""
        if not item_ids:
            return
        key = (pos.x, pos.y)
        if key not in self.ground_items:
            self.ground_items[key] = []
        self.ground_items[key].extend(item_ids)

    def pickup_items(self, pos: Vector2) -> list[str]:
        """Remove and return all ground items at *pos*."""
        key = (pos.x, pos.y)
        return self.ground_items.pop(key, [])

    def add_resource_node(self, node: ResourceNode) -> None:
        self.resource_nodes[node.node_id] = node

    def allocate_node_id(self) -> int:
        nid = self._next_node_id
        self._next_node_id += 1
        return nid

    def resource_at(self, pos: Vector2) -> ResourceNode | None:
        """Return the resource node at *pos*, if any."""
        for node in self.resource_nodes.values():
            if node.spatial.pos == pos:
                return node
        return None

    @classmethod
    def from_snapshot(cls, snap: 'Snapshot', spatial_index: SpatialHash) -> WorldState:
        """Reconstruct a mutable WorldState from a serialized Snapshot."""
        world = cls(seed=snap.seed, grid=snap.grid, spatial_index=spatial_index)
        world.tick = snap.tick
        
        for eid, entity in snap.entities.items():
            world.add_entity(entity.copy())
            world._next_entity_id = max(world._next_entity_id, eid + 1)
            
        world.ground_items = {k: list(v) for k, v in snap.ground_items.items()}
        world.camps = [Vector2(x, y) for x, y in snap.camps]
        world.buildings = list(snap.buildings)
        
        for node in snap.resource_nodes:
            world.add_resource_node(node.copy())
            world._next_node_id = max(world._next_node_id, node.node_id + 1)
            
        for chest in snap.treasure_chests:
            world.treasure_chests[chest.chest_id] = chest.copy()
            world._next_chest_id = max(world._next_chest_id, chest.chest_id + 1)
            
        world.regions = [r.copy() for r in snap.regions]
        world.event_bus = None
        
        return world

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/registry/__init__.py


#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/registry/registry_loader.py
import json
import logging
from pathlib import Path
from pydantic import TypeAdapter

from src.core.gameplay.items.item_registry import ItemTemplate, ITEM_REGISTRY
from src.core.gameplay.classes import ClassDef, BreakthroughDef, SkillDef, CLASS_DEFS, BREAKTHROUGHS, SKILL_DEFS
from src.core.entities.traits import TraitDef, TRAIT_DEFS
from src.core.models.enums import RaceProfile, RACE_PROFILES
from src.core.world.spawn_config import SpawnConfig, LootConfig, SPAWN_CONFIGS, LOOT_CONFIGS

logger = logging.getLogger(__name__)

def load_all_registries(data_dir: Path | str = "data") -> None:
    """Load all definition JSON files from the given directory into the core registries."""
    data_path = Path(data_dir)
    logger.info("Loading registries from %s", data_path.resolve())

    _load_items(data_path / "items.json")
    _load_classes(data_path / "classes.json")
    _load_skills(data_path / "skills.json")
    _load_breakthroughs(data_path / "breakthroughs.json")
    _load_traits(data_path / "traits.json")
    _load_races(data_path / "races.json")
    _load_spawn_configs(data_path / "spawn_config.json")
    _load_loot_configs(data_path / "loot_config.json")
    
    logger.debug("load_all_registries FINISHING. CLASS_DEFS=%d, SKILL_DEFS=%d", len(CLASS_DEFS), len(SKILL_DEFS))
    logger.info("Successfully loaded all registries.")

def _load_races(path: Path) -> None:
    if not path.exists():
        logger.warning("Race definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(dict[str, RaceProfile])
    races = adapter.validate_python(data)
    
    RACE_PROFILES.clear()
    RACE_PROFILES.update(races)
    
    logger.info("Loaded %d races.", len(RACE_PROFILES))

def _load_spawn_configs(path: Path) -> None:
    if not path.exists():
        logger.warning("Spawn configuration not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[SpawnConfig])
    configs = adapter.validate_python(data)
    
    SPAWN_CONFIGS.clear()
    for cfg in configs:
        SPAWN_CONFIGS[(cfg.race, cfg.tier)] = cfg
        
    logger.info("Loaded %d spawn configurations.", len(SPAWN_CONFIGS))

def _load_loot_configs(path: Path) -> None:
    if not path.exists():
        logger.warning("Loot configuration not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[LootConfig])
    configs = adapter.validate_python(data)
    
    LOOT_CONFIGS.clear()
    for cfg in configs:
        LOOT_CONFIGS[cfg.kind] = cfg
        
    logger.info("Loaded %d loot configurations.", len(LOOT_CONFIGS))

def _load_items(path: Path) -> None:
    if not path.exists():
        logger.warning("Item definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[ItemTemplate])
    items = adapter.validate_python(data)
    
    ITEM_REGISTRY.clear()
    for item in items:
        ITEM_REGISTRY[item.item_id] = item
    
    logger.info("Loaded %d items.", len(ITEM_REGISTRY))

def _load_classes(path: Path) -> None:
    if not path.exists():
        logger.warning("Class definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[ClassDef])
    classes = adapter.validate_python(data)
    
    CLASS_DEFS.clear()
    for c in classes:
        CLASS_DEFS[c.class_id] = c
        
    logger.info("Loaded %d classes.", len(CLASS_DEFS))

def _load_skills(path: Path) -> None:
    if not path.exists():
        logger.warning("Skill definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[SkillDef])
    skills = adapter.validate_python(data)
    logger.debug("Loading skills from %s, found %d items", path, len(skills))
    
    SKILL_DEFS.clear()
    for s in skills:
        SKILL_DEFS[s.skill_id] = s
        
    logger.info("Loaded %d skills.", len(SKILL_DEFS))

def _load_breakthroughs(path: Path) -> None:
    if not path.exists():
        logger.warning("Breakthrough definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[BreakthroughDef])
    breakthroughs = adapter.validate_python(data)
    
    BREAKTHROUGHS.clear()
    for b in breakthroughs:
        BREAKTHROUGHS[b.from_class] = b
        
    logger.info("Loaded %d breakthroughs.", len(BREAKTHROUGHS))

def _load_traits(path: Path) -> None:
    if not path.exists():
        logger.warning("Trait definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[TraitDef])
    traits = adapter.validate_python(data)
    
    TRAIT_DEFS.clear()
    for t in traits:
        TRAIT_DEFS[t.trait_type] = t
        
    logger.info("Loaded %d traits.", len(TRAIT_DEFS))

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/world/__init__.py


#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/world/grid.py
"""Grid / map system."""

from __future__ import annotations

from src.core.models.enums import Material
from src.core.models import Vector2

# Pre-cache Material objects to avoid the high overhead of Material(int_value) 
# during frequent grid lookups (Clean Code: Performance Optimization)
_MATERIAL_CACHE = [Material.WALL] * 256
for m in Material:
    _MATERIAL_CACHE[int(m)] = m


class Grid:
    """2D tile grid backed by a flat list for cache-friendly access."""

    __slots__ = ("width", "height", "_tiles")

    def __init__(self, width: int, height: int, default: Material = Material.FLOOR) -> None:
        self.width = width
        self.height = height
        self._tiles = bytearray([int(default)]) * (width * height)

    # -- access --

    def _idx(self, x: int, y: int) -> int:
        return y * self.width + x

    def in_bounds(self, pos: Vector2) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def get(self, pos: Vector2) -> Material:
        if not self.in_bounds(pos):
            return Material.WALL
        val = self._tiles[self._idx(pos.x, pos.y)]
        return _MATERIAL_CACHE[val]

    def set(self, pos: Vector2, material: Material) -> None:
        if self.in_bounds(pos):
            self._tiles[self._idx(pos.x, pos.y)] = int(material)

    def is_walkable(self, pos: Vector2) -> bool:
        mat = self.get(pos)
        return mat not in (Material.WALL, Material.WATER, Material.LAVA)

    def is_forest(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.FOREST

    def is_desert(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.DESERT

    def is_swamp(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.SWAMP

    def is_mountain(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.MOUNTAIN

    def is_town(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.TOWN

    def is_camp(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.CAMP

    def is_sanctuary(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.SANCTUARY

    def is_road(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.ROAD

    def is_bridge(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.BRIDGE

    def is_ruins(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.RUINS

    def is_dungeon_entrance(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.DUNGEON_ENTRANCE

    def is_lava(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.LAVA

    # -- line-of-sight (Bresenham) --

    def has_line_of_sight(self, x0: int, y0: int, x1: int, y1: int) -> bool:
        """Check if there is a clear line of sight between two positions.

        Uses Bresenham's line algorithm. Returns False if any WALL tile
        lies on the line between (x0,y0) and (x1,y1), exclusive of endpoints.
        """
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        cx, cy = x0, y0
        while True:
            if cx == x1 and cy == y1:
                return True
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy
            # Check intermediate tile (skip start and end)
            if (cx != x1 or cy != y1) and self.get_xy(cx, cy) == Material.WALL:
                return False
        return True

    def has_adjacent_wall(self, x: int, y: int) -> bool:
        """Check if any of the 4 cardinal neighbors is a WALL tile (for cover)."""
        return (
            self.get_xy(x - 1, y) == Material.WALL
            or self.get_xy(x + 1, y) == Material.WALL
            or self.get_xy(x, y - 1) == Material.WALL
            or self.get_xy(x, y + 1) == Material.WALL
        )

    # -- fast raw-coordinate access (no Vector2 alloc, for hot loops) --

    def in_bounds_xy(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_xy(self, x: int, y: int) -> Material:
        if 0 <= x < self.width and 0 <= y < self.height:
            val = self._tiles[y * self.width + x]
            return _MATERIAL_CACHE[val]
        return Material.WALL

    # -- copy --

    def copy(self) -> Grid:
        new = Grid.__new__(Grid)
        new.width = self.width
        new.height = self.height
        new._tiles = bytearray(self._tiles)
        return new

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/world/monuments.py
"""Historical legacy objects."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models import Vector2

@dataclass(slots=True)
class Monument:
    monument_id: str
    hero_name: str
    hero_class: str
    level: int
    pos: Vector2
    buff_type: str
    buff_value: float

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/world/regions.py
"""Region & Location data model for the world map (epic-15).

Regions are large named areas with a terrain type, difficulty tier, and
sub-locations.  Locations are points of interest within a region (camps,
groves, ruins, dungeons, shrines, boss arenas).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.core.models.enums import Material
from src.core.models import Vector2

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Location types
# ---------------------------------------------------------------------------

LOCATION_TYPES = (
    "enemy_camp",
    "resource_grove",
    "ruins",
    "dungeon_entrance",
    "shrine",
    "boss_arena",
    "outpost",
    "watchtower",
    "portal",
    "fishing_spot",
    "graveyard",
    "obelisk",
)


@dataclass(slots=True)
class Location:
    """A point of interest within a region."""

    location_id: str
    name: str
    location_type: str          # one of LOCATION_TYPES
    pos: Vector2
    region_id: str
    reinforcement_level: int = 0


@dataclass(slots=True)
class Region:
    """A named area of the world map."""

    region_id: str
    name: str
    terrain: Material           # FOREST, DESERT, SWAMP, MOUNTAIN
    center: Vector2
    radius: int
    difficulty: int             # 1–4
    owner_faction: Faction | None = None
    locations: list[Location] = field(default_factory=list)

    def contains(self, pos: Vector2) -> bool:
        """Rough bounding check (Manhattan distance).

        For authoritative Voronoi ownership use ``find_region_at()``.
        """
        return self.center.manhattan(pos) <= self.radius

    def copy(self) -> Region:
        return Region(
            region_id=self.region_id,
            name=self.name,
            terrain=self.terrain,
            center=Vector2(self.center.x, self.center.y),
            radius=self.radius,
            difficulty=self.difficulty,
            locations=[Location(
                location_id=loc.location_id,
                name=loc.name,
                location_type=loc.location_type,
                pos=Vector2(loc.pos.x, loc.pos.y),
                region_id=loc.region_id,
            ) for loc in self.locations],
        )


# ---------------------------------------------------------------------------
# Region name tables (per terrain)
# ---------------------------------------------------------------------------

REGION_NAMES: dict[int, list[str]] = {
    Material.FOREST: [
        "Whispering Woods",
        "Verdant Hollow",
        "Thornwood",
        "Mossy Glen",
        "Eldergrove",
        "Shadeleaf Thicket",
    ],
    Material.DESERT: [
        "Scorched Wastes",
        "Dustwind Basin",
        "Sunfire Plateau",
        "Sandstone Reach",
        "Dry Gulch",
        "Ember Flats",
    ],
    Material.SWAMP: [
        "Rotmire Bog",
        "Gloomfen",
        "Witchwater Marsh",
        "Deadtide Swamp",
        "Murkhollow",
        "Venom Pools",
    ],
    Material.MOUNTAIN: [
        "Ironpeak Ridge",
        "Stormcrag Heights",
        "Frostbreak Summit",
        "Ashvein Slopes",
        "Granite Pass",
        "Windshear Cliffs",
    ],
    Material.GRASSLAND: [
        "Sunlit Meadows",
        "Windswept Plains",
        "Golden Steppe",
        "Rider's Expanse",
        "Verdant Prairie",
        "Wildflower Fields",
    ],
    Material.SNOW: [
        "Frostfang Tundra",
        "Blizzard Wastes",
        "Icebound Reaches",
        "Frozen Hollow",
        "Snowdrift Expanse",
        "Pale Summit",
    ],
    Material.JUNGLE: [
        "Serpent's Canopy",
        "Tanglewood Depths",
        "Emerald Wilds",
        "Venomthorn Jungle",
        "Muggy Thicket",
        "Primal Basin",
    ],
    Material.VOLCANIC: [
        "Cinderfall Caldera",
        "Magma Rift",
        "Obsidian Wastes",
        "Scorchstone Basin",
        "Hellfire Crater",
        "Sulfur Peaks",
    ],
}

# Name index counters (reset per world build)
_name_counters: dict[int, int] = {}


def pick_region_name(terrain: Material) -> str:
    """Return the next unique name for a terrain type."""
    key = int(terrain)
    idx = _name_counters.get(key, 0)
    names = REGION_NAMES.get(key, ["Unknown Region"])
    name = names[idx % len(names)]
    _name_counters[key] = idx + 1
    return name


def reset_name_counters() -> None:
    """Reset name counters (call before each world build)."""
    _name_counters.clear()


# ---------------------------------------------------------------------------
# Location name templates (per location type)
# ---------------------------------------------------------------------------

LOCATION_NAME_TEMPLATES: dict[str, list[str]] = {
    "enemy_camp": [
        "{race} Outpost",
        "{race} Encampment",
        "{race} Hideout",
        "{race} Stockade",
        "{race} Watchtower",
    ],
    "resource_grove": [
        "Harvest Clearing",
        "Gatherer's Nook",
        "Rich Vein",
        "Abundant Patch",
        "Forager's Dell",
    ],
    "ruins": [
        "Crumbling Tower",
        "Forgotten Shrine",
        "Ancient Pillars",
        "Lost Archway",
        "Broken Monument",
    ],
    "dungeon_entrance": [
        "Dark Cavern",
        "Sunken Passage",
        "Sealed Gate",
        "Obsidian Rift",
    ],
    "shrine": [
        "Shrine of Vigor",
        "Blessed Stone",
        "Wayward Altar",
        "Pilgrim's Rest",
    ],
    "boss_arena": [
        "The Arena",
        "Champion's Ring",
        "Proving Ground",
        "Warlord's Domain",
    ],
    "outpost": [
        "Frontier Outpost",
        "Border Station",
        "Ranger Outpost",
        "Scout Camp",
    ],
    "watchtower": [
        "Watchtower",
        "Lookout Tower",
        "Signal Tower",
        "Sentinel Spire",
    ],
    "portal": [
        "Ancient Portal",
        "Rift Gate",
        "Waystone",
        "Teleport Circle",
    ],
    "fishing_spot": [
        "Fishing Spot",
        "Angler's Cove",
        "Still Pond",
        "River Bend",
    ],
    "graveyard": [
        "Forgotten Graveyard",
        "Haunted Cemetery",
        "Bone Field",
        "Tomb of the Fallen",
    ],
    "obelisk": [
        "Ancient Obelisk",
        "Runic Monolith",
        "Eldritch Pillar",
        "Mystic Spire",
    ],
}

# Race labels for location names
TERRAIN_RACE_LABEL: dict[int, str] = {
    Material.FOREST: "Wolf",
    Material.DESERT: "Bandit",
    Material.SWAMP: "Undead",
    Material.MOUNTAIN: "Orc",
    Material.GRASSLAND: "Centaur",
    Material.SNOW: "Frost Giant",
    Material.JUNGLE: "Lizardfolk",
    Material.VOLCANIC: "Demon",
}


# ---------------------------------------------------------------------------
# Difficulty multiplier tables
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DifficultyMultipliers:
    """Stat multipliers for a given difficulty tier."""
    hp: float
    atk: float
    def_: float
    xp: float
    gold: float
    level_min: int
    level_max: int


DIFFICULTY_TIERS: dict[int, DifficultyMultipliers] = {
    1: DifficultyMultipliers(hp=1.0, atk=1.0, def_=1.0, xp=1.0, gold=1.0, level_min=1, level_max=3),
    2: DifficultyMultipliers(hp=1.5, atk=1.3, def_=1.2, xp=1.5, gold=1.5, level_min=3, level_max=6),
    3: DifficultyMultipliers(hp=2.5, atk=2.0, def_=1.8, xp=3.0, gold=2.5, level_min=5, level_max=10),
    4: DifficultyMultipliers(hp=4.0, atk=3.0, def_=2.5, xp=5.0, gold=4.0, level_min=8, level_max=15),
}


def find_region_at(pos: Vector2, regions: list[Region] | tuple[Region, ...]) -> Region | None:
    """Return the region whose center is nearest to *pos* (Voronoi ownership).

    Returns ``None`` if *regions* is empty.
    """
    best: Region | None = None
    best_dist = float("inf")
    for r in regions:
        d = r.center.manhattan(pos)
        if d < best_dist:
            best_dist = d
            best = r
    return best


def difficulty_for_distance(distance: float, zone_boundaries: list[tuple[int, int]]) -> int:
    """Determine difficulty tier based on distance from town center.

    zone_boundaries is a list of (max_distance, tier) sorted ascending.
    """
    for max_dist, tier in zone_boundaries:
        if distance <= max_dist:
            return tier
    # Beyond all boundaries → highest tier
    return zone_boundaries[-1][1] if zone_boundaries else 1

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/world/resource_nodes.py
"""Resource nodes — harvestable objects scattered across terrain regions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.models.enums import Material
from src.core.models import Vector2

if TYPE_CHECKING:
    pass


@dataclass(slots=True)
class ResourceNode:
    """A harvestable resource on the map."""

    node_id: int
    resource_type: str          # e.g. "herb_patch", "ore_vein", "timber"
    name: str                   # display name
    pos: Vector2
    terrain: Material           # which terrain this spawns on
    yields_item: str            # item_id produced on harvest
    remaining: int = 3          # harvests left before depletion
    max_harvests: int = 3
    respawn_cooldown: int = 30  # ticks to respawn after depletion
    cooldown_remaining: int = 0 # 0 = harvestable; >0 = depleted, counting down
    harvest_ticks: int = 2      # ticks to channel harvest

    @property
    def is_depleted(self) -> bool:
        return self.remaining <= 0

    @property
    def is_available(self) -> bool:
        return self.remaining > 0 and self.cooldown_remaining <= 0

    def harvest(self) -> str | None:
        """Consume one harvest charge, return the item_id or None."""
        if not self.is_available:
            return None
        self.remaining -= 1
        if self.remaining <= 0:
            self.cooldown_remaining = self.respawn_cooldown
        return self.yields_item

    def tick_cooldown(self) -> None:
        """Decrement cooldown; respawn if ready."""
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
            if self.cooldown_remaining <= 0:
                self.remaining = self.max_harvests

    def copy(self) -> ResourceNode:
        return ResourceNode(
            node_id=self.node_id,
            resource_type=self.resource_type,
            name=self.name,
            pos=self.pos,
            terrain=self.terrain,
            yields_item=self.yields_item,
            remaining=self.remaining,
            max_harvests=self.max_harvests,
            respawn_cooldown=self.respawn_cooldown,
            cooldown_remaining=self.cooldown_remaining,
            harvest_ticks=self.harvest_ticks,
        )


# ---------------------------------------------------------------------------
# Resource type definitions per terrain
# ---------------------------------------------------------------------------

# (resource_type, name, yields_item, max_harvests, respawn_cooldown, harvest_ticks)
TERRAIN_RESOURCES: dict[int, list[tuple[str, str, str, int, int, int]]] = {
    Material.FOREST: [
        ("herb_patch",   "Herb Patch",       "herb",           3, 25, 2),
        ("timber",       "Timber",           "wood",           4, 30, 3),
        ("berry_bush",   "Berry Bush",       "wild_berries",   2, 20, 1),
    ],
    Material.DESERT: [
        ("gem_deposit",  "Gem Deposit",      "raw_gem",        2, 35, 3),
        ("cactus_fiber", "Cactus Fiber",     "fiber",          3, 20, 2),
        ("sand_iron",    "Desert Iron",      "iron_ore",       3, 30, 3),
    ],
    Material.SWAMP: [
        ("mushroom_grove", "Mushroom Grove", "glowing_mushroom", 3, 25, 2),
        ("bog_iron",     "Bog Iron Deposit", "iron_ore",       3, 30, 3),
        ("dark_moss",    "Dark Moss",        "dark_moss",      2, 20, 2),
    ],
    Material.MOUNTAIN: [
        ("ore_vein",     "Ore Vein",         "iron_ore",       4, 30, 3),
        ("crystal_node", "Crystal Node",     "enchanted_dust", 2, 40, 4),
        ("granite_quarry", "Granite Quarry", "stone_block",    3, 35, 3),
    ],
    Material.GRASSLAND: [
        ("wheat_field",   "Wheat Field",      "wheat",          4, 20, 2),
        ("herb_patch",    "Wild Herbs",        "herb",           3, 25, 2),
        ("berry_bush",    "Berry Bush",        "wild_berries",   2, 20, 1),
    ],
    Material.SNOW: [
        ("ice_crystal",   "Ice Crystal",       "frost_shard",    2, 40, 3),
        ("frozen_herb",   "Frost Herb",        "herb",           2, 30, 3),
        ("mammoth_bone",  "Mammoth Bone",      "bone",           3, 35, 3),
    ],
    Material.JUNGLE: [
        ("exotic_plant",  "Exotic Plant",      "herb",           3, 25, 2),
        ("venom_gland",   "Venom Sac",         "venom",          2, 30, 2),
        ("timber",        "Jungle Hardwood",   "wood",           4, 30, 3),
    ],
    Material.VOLCANIC: [
        ("obsidian_vein", "Obsidian Vein",     "obsidian",       3, 35, 3),
        ("sulfur_pit",    "Sulfur Pit",        "sulfur",         2, 30, 2),
        ("fire_crystal",  "Fire Crystal",      "enchanted_dust", 2, 40, 4),
    ],
    Material.FLOOR: [
        ("berry_bush",   "Wild Berry Bush",  "wild_berries",   2, 25, 1),
    ],
}

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/world/spawn_config.py
"""Data models for spawn and loot configuration."""
from __future__ import annotations
from dataclasses import field
from pydantic.dataclasses import dataclass as pydantic_dataclass
from src.core.models.enums import EnemyTier, HeroClass, ItemType, EnemyTierSer, HeroClassSer, ItemTypeSer

@pydantic_dataclass(frozen=True)
class SpawnConfig:
    """Maps race and tier to a specific 'kind' string used for naming and lookups."""
    race: str
    tier: EnemyTierSer
    kind: str
    archetype: HeroClassSer
    starting_gear: list[str] = field(default_factory=list)

@pydantic_dataclass(frozen=True)
class LootConfig:
    """Defines drop patterns for different entity types or tiers."""
    kind: str
    drop_chance: float
    guaranteed_items: list[str]
    random_pool: list[str]
    gold_min: int
    gold_max: int

# Global registries to be populated by registry_loader
SPAWN_CONFIGS: dict[tuple[str, EnemyTier], SpawnConfig] = {}
LOOT_CONFIGS: dict[str, LootConfig] = {}

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/core/world/world_generator.py

import logging
from src.core.models.enums import Domain, EnemyTier, EntityRole, Material
from src.core.gameplay.faction import Faction
from src.core.world.grid import Grid
from src.core.models import Vector2, TreasureChest
from src.core.gameplay.buildings import Building
from src.core.models.world_state import WorldState
from src.core.world.regions import (
    Region, Location, LOCATION_NAME_TEMPLATES, TERRAIN_RACE_LABEL,
    difficulty_for_distance, pick_region_name, reset_name_counters,
)
from src.core.world.resource_nodes import ResourceNode, TERRAIN_RESOURCES
from src.core.gameplay.items.items import TERRAIN_RACE
from src.systems.world.generator import EntityGenerator
from src.platform.rng import DeterministicRNG
from src.platform.spatial_hash import SpatialHash

logger = logging.getLogger(__name__)

TERRAIN_RACE_MAP = {
    int(Material.FOREST): "Goblin",
    int(Material.DESERT): "Orc",
    int(Material.SWAMP): "Undead",
    int(Material.MOUNTAIN): "Drake",
    int(Material.GRASSLAND): "Humanoid",
    int(Material.SNOW): "Frostborn",
    int(Material.JUNGLE): "Beast",
    int(Material.VOLCANIC): "Elemental",
}

class WorldGenerator:
    """Service class responsible for procedurally generating a new WorldState.
    
    This decouples the engine's lifecycle management (EngineManager) from the
    complex map generation, building placement, and initial entity spawning.
    """

    def __init__(self, cfg, rng: DeterministicRNG):
        self.cfg = cfg
        self.rng = rng
        self.total_spawned = 0

    def generate(self) -> tuple[WorldState, EntityGenerator]:
        """Generate a completely new world from scratch based on the provided config."""
        cfg = self.cfg
        rng = self.rng
        self.total_spawned = 0

        grid = Grid(cfg.grid_width, cfg.grid_height)
        spatial = SpatialHash(cfg.spatial_cell_size)
        world = WorldState(seed=cfg.world_seed, grid=grid, spatial_index=spatial)

        town_center = Vector2(cfg.town_center_x, cfg.town_center_y)
        TOWN_TILES = frozenset({Material.TOWN, Material.SANCTUARY})

        # --- 1. Base Terrain Layout ---
        self._place_town_and_sanctuary(grid, cfg)
        
        region_seeds = self._place_region_seeds(cfg, rng, town_center)
        region_max_dist = self._assign_voronoi_regions(grid, cfg, region_seeds, TOWN_TILES)
        
        # --- 2. Regions and Locations ---
        reset_name_counters()
        generator = EntityGenerator(cfg, rng)
        zone_bounds = list(cfg.difficulty_zones)
        region_centers: list[Vector2] = []

        for idx, (rpos, mat) in enumerate(region_seeds):
            dist_to_town = rpos.manhattan(town_center)
            difficulty = difficulty_for_distance(dist_to_town, zone_bounds)
            region_name = pick_region_name(mat)
            region_id = region_name.lower().replace(" ", "_").replace("'", "")
            effective_radius = region_max_dist.get(idx, cfg.region_max_radius)
            
            region = Region(
                region_id=region_id, name=region_name,
                terrain=mat, center=rpos, radius=effective_radius,
                difficulty=difficulty,
            )

            self._generate_locations_in_region(world, region, grid, cfg, rng, idx, mat, region_id, difficulty, effective_radius)
            
            world.regions.append(region)
            region_centers.append(rpos)
            logger.info("Created region '%s' (%s, tier %d) at %s r=%d with %d locations",
                        region.name, mat.name, difficulty, rpos, effective_radius, len(region.locations))

        # --- 3. Terrain Detail & Roads ---
        from src.systems.world.terrain_detail import TerrainDetailGenerator
        terrain_gen = TerrainDetailGenerator(grid, rng)
        terrain_gen.generate_all(world.regions)

        if cfg.road_from_town:
            self._generate_roads(grid, cfg, town_center, region_centers)

        # --- 4. Buildings (Town) ---
        self._place_town_buildings(world, cfg, town_center)

        # --- 5. Initial Entities ---
        self._spawn_initial_entities(world, generator, cfg, rng, town_center)

        logger.info("Generated world with %d entities, %d buildings, %d regions",
                    len(world.entities), len(world.buildings), len(world.regions))
        return world, generator

    def _place_town_and_sanctuary(self, grid: Grid, cfg):
        # Place town tiles (safe zone)
        for ty in range(cfg.town_center_y - cfg.town_radius, cfg.town_center_y + cfg.town_radius + 1):
            for tx in range(cfg.town_center_x - cfg.town_radius, cfg.town_center_x + cfg.town_radius + 1):
                pos = Vector2(tx, ty)
                if grid.in_bounds(pos):
                    grid.set(pos, Material.TOWN)

        # Place sanctuary tiles (debuff zone around town)
        for sy in range(cfg.town_center_y - cfg.sanctuary_radius, cfg.town_center_y + cfg.sanctuary_radius + 1):
            for sx in range(cfg.town_center_x - cfg.sanctuary_radius, cfg.town_center_x + cfg.sanctuary_radius + 1):
                pos = Vector2(sx, sy)
                if grid.in_bounds(pos) and grid.get(pos) == Material.FLOOR:
                    grid.set(pos, Material.SANCTUARY)

    def _place_region_seeds(self, cfg, rng: DeterministicRNG, town_center: Vector2):
        region_specs = [
            (Material.FOREST, cfg.num_forest_regions),
            (Material.DESERT, cfg.num_desert_regions),
            (Material.SWAMP, cfg.num_swamp_regions),
            (Material.MOUNTAIN, cfg.num_mountain_regions),
            (Material.GRASSLAND, cfg.num_grassland_regions),
            (Material.SNOW, cfg.num_snow_regions),
            (Material.JUNGLE, cfg.num_jungle_regions),
            (Material.VOLCANIC, cfg.num_volcanic_regions),
        ]
        region_seeds: list[tuple[Vector2, Material]] = []
        for mat, count in region_specs:
            for ri in range(count):
                seed_key = mat * 100 + ri
                for attempt in range(120):
                    rx = rng.next_int(Domain.MAP_GEN, seed_key, attempt, 6, cfg.grid_width - 7)
                    ry = rng.next_int(Domain.MAP_GEN, seed_key, attempt + 200, 6, cfg.grid_height - 7)
                    rpos = Vector2(rx, ry)
                    if rpos.manhattan(town_center) < cfg.camp_min_distance_from_town:
                        continue
                    too_close = any(rpos.manhattan(s[0]) < cfg.region_min_distance for s in region_seeds)
                    if too_close:
                        continue
                    region_seeds.append((rpos, mat))
                    break
        return region_seeds

    def _assign_voronoi_regions(self, grid: Grid, cfg, region_seeds, town_tiles):
        region_max_dist: dict[int, int] = {i: 0 for i in range(len(region_seeds))}
        for y in range(cfg.grid_height):
            for x in range(cfg.grid_width):
                pos = Vector2(x, y)
                if grid.get(pos) in town_tiles:
                    continue
                best_idx = -1
                best_dist = float("inf")
                for idx, (center, _mat) in enumerate(region_seeds):
                    d = center.manhattan(pos)
                    if d < best_dist:
                        best_dist = d
                        best_idx = idx
                if best_idx >= 0:
                    _center, r_mat = region_seeds[best_idx]
                    grid.set(pos, r_mat)
                    d_int = int(best_dist)
                    if d_int > region_max_dist[best_idx]:
                        region_max_dist[best_idx] = d_int
        return region_max_dist

    def _generate_locations_in_region(self, world, region, grid, cfg, rng: DeterministicRNG, idx, mat, region_id, difficulty, effective_radius):
        seed_key = mat * 100 + (idx % 10)
        num_locs = rng.next_int(Domain.MAP_GEN, seed_key, 500 + idx, cfg.min_locations_per_region, cfg.max_locations_per_region)
        loc_positions: list[Vector2] = []
        race_label = TERRAIN_RACE_LABEL.get(int(mat), "Goblin")

        loc_types: list[str] = ["enemy_camp", "resource_grove"]
        if difficulty >= 3:
            loc_types.extend(["dungeon_entrance", "boss_arena", "portal"])
        else:
            loc_types.extend(["shrine", "outpost"])
        loc_types.append("ruins")
        
        if mat in (Material.SWAMP, Material.SNOW, Material.GRAVEYARD):
            loc_types.append("graveyard")
        if mat in (Material.GRASSLAND, Material.JUNGLE, Material.FOREST):
            loc_types.append("watchtower")
        if mat in (Material.DESERT, Material.VOLCANIC, Material.MOUNTAIN):
            loc_types.append("obelisk")

        while len(loc_types) < num_locs:
            extra = ["enemy_camp", "resource_grove", "ruins", "fishing_spot"]
            pick = rng.next_int(Domain.MAP_GEN, seed_key + len(loc_types), 600 + idx, 0, len(extra) - 1)
            loc_types.append(extra[pick])

        loc_range = max(effective_radius // 2, 8)
        for li, loc_type in enumerate(loc_types[:num_locs]):
            for loc_attempt in range(60):
                ox = rng.next_int(Domain.MAP_GEN, seed_key + li * 100, loc_attempt + 700, -loc_range, loc_range)
                oy = rng.next_int(Domain.MAP_GEN, seed_key + li * 100, loc_attempt + 800, -loc_range, loc_range)
                lpos = Vector2(region.center.x + ox, region.center.y + oy)
                if not grid.in_bounds(lpos) or grid.get(lpos) != mat:
                    continue
                if any(lpos.manhattan(lp) < cfg.location_min_spacing for lp in loc_positions):
                    continue

                templates = LOCATION_NAME_TEMPLATES.get(loc_type, ["{race} Place"])
                tpl_idx = rng.next_int(Domain.MAP_GEN, seed_key + li, loc_attempt + 900, 0, len(templates) - 1)
                loc_name = templates[tpl_idx].format(race=race_label)
                loc_id = f"{region_id}_{loc_type}_{li}"

                loc = Location(location_id=loc_id, name=loc_name, location_type=loc_type, pos=lpos, region_id=region_id)
                region.locations.append(loc)
                loc_positions.append(lpos)
                self._paint_location_terrain(world, loc, grid, cfg, mat, difficulty)
                break

    def _paint_location_terrain(self, world, loc, grid, cfg, mat, difficulty):
        if loc.location_type == "enemy_camp":
            for cdy in range(-cfg.camp_radius, cfg.camp_radius + 1):
                for cdx in range(-cfg.camp_radius, cfg.camp_radius + 1):
                    cp = Vector2(loc.pos.x + cdx, loc.pos.y + cdy)
                    if grid.in_bounds(cp) and grid.get(cp) == mat:
                        grid.set(cp, Material.CAMP)
            world.camps.append(loc.pos)
        elif loc.location_type == "ruins":
            for rdy in range(-1, 2):
                for rdx in range(-1, 2):
                    rtp = Vector2(loc.pos.x + rdx, loc.pos.y + rdy)
                    if grid.in_bounds(rtp) and grid.get(rtp) == mat:
                        grid.set(rtp, Material.RUINS)
        elif loc.location_type == "dungeon_entrance":
            grid.set(loc.pos, Material.DUNGEON_ENTRANCE)
        elif loc.location_type == "graveyard":
            for gdy in range(-2, 3):
                for gdx in range(-2, 3):
                    gp = Vector2(loc.pos.x + gdx, loc.pos.y + gdy)
                    if grid.in_bounds(gp) and grid.get(gp) == mat:
                        grid.set(gp, Material.GRAVEYARD)
        elif loc.location_type in ("outpost", "watchtower", "portal", "fishing_spot", "obelisk"):
            world.buildings.append(Building(building_id=loc.location_id, name=loc.name, pos=loc.pos, building_type=loc.location_type))

        if loc.location_type in ("ruins", "dungeon_entrance"):
            cid = world._next_chest_id
            world._next_chest_id += 1
            world.treasure_chests[cid] = TreasureChest(chest_id=cid, pos=loc.pos, tier=min(difficulty, 4))

    def _generate_roads(self, grid: Grid, cfg, town_center: Vector2, region_centers: list[Vector2]):
        ROAD_PAINTABLE = frozenset({
            Material.FLOOR, Material.FOREST, Material.DESERT, Material.SWAMP,
            Material.MOUNTAIN, Material.GRASSLAND, Material.SNOW, Material.JUNGLE,
            Material.VOLCANIC, Material.FARMLAND, Material.GRAVEYARD,
        })
        sorted_regions = sorted(region_centers, key=lambda r: r.manhattan(town_center))
        for rt in sorted_regions[:8]:
            cx, cy = town_center.x, town_center.y
            tx, ty = rt.x, rt.y
            step_x = 1 if tx > cx else -1
            x = cx
            while x != tx:
                x += step_x
                rp = Vector2(x, cy)
                if grid.in_bounds(rp):
                    tile = grid.get(rp)
                    if tile in ROAD_PAINTABLE: grid.set(rp, Material.ROAD)
                    elif tile == Material.WATER: grid.set(rp, Material.BRIDGE)
            step_y = 1 if ty > cy else -1
            y = cy
            while y != ty:
                y += step_y
                rp = Vector2(tx, y)
                if grid.in_bounds(rp):
                    tile = grid.get(rp)
                    if tile in ROAD_PAINTABLE: grid.set(rp, Material.ROAD)
                    elif tile == Material.WATER: grid.set(rp, Material.BRIDGE)

    def _place_town_buildings(self, world, cfg, town_center: Vector2):
        town_radius = cfg.town_radius
        buildings = [
            ("store", "General Store", Vector2(town_center.x - town_radius + 1, town_center.y - town_radius + 1), "store"),
            ("blacksmith", "Blacksmith", Vector2(town_center.x + town_radius - 1, town_center.y - town_radius + 1), "blacksmith"),
            ("guild", "Adventurer's Guild", Vector2(town_center.x, town_center.y + town_radius - 1), "guild"),
            ("class_hall", "Class Hall", Vector2(town_center.x - town_radius + 1, town_center.y + town_radius - 1), "class_hall"),
            ("inn", "Traveler's Inn", Vector2(town_center.x + town_radius - 1, town_center.y + town_radius - 1), "inn"),
        ]
        for bid, name, pos, btype in buildings:
            world.buildings.append(Building(building_id=bid, name=name, pos=pos, building_type=btype))

    def _spawn_initial_entities(self, world, generator: EntityGenerator, cfg, rng: DeterministicRNG, town_center: Vector2):
        from src.core.gameplay.classes import HeroClass, HERO_STARTING_GEAR
        from src.core.entities.entity_builder import EntityBuilder
        from src.core.data.hero_names import generate_hero_name
        from src.core.models.enums import Faction

        class_choices = [HeroClass.WARRIOR, HeroClass.RANGER, HeroClass.MAGE, HeroClass.ROGUE]
        for h_idx in range(cfg.hero_count):
            hero_eid = world.allocate_entity_id()
            hero_class = class_choices[h_idx % len(class_choices)]
            gear = HERO_STARTING_GEAR.get(hero_class, {})
            builder = (EntityBuilder(rng, hero_eid, tick=0).kind("hero").at(Vector2(cfg.town_center_x, cfg.town_center_y)).home(town_center).faction(Faction.HERO_GUILD).role(EntityRole.HERO))
            builder.with_traits(race_prefix="hero")
            hero_name = generate_hero_name(rng, hero_eid, 0, builder._traits)
            hero = (builder.with_identity(display_name=hero_name, generation=1).with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3, crit_rate=0.08, crit_dmg=1.8, evasion=0.03, gold=50).with_randomized_stats().with_hero_class(hero_class).with_race_skills("hero").with_class_skills(hero_class, level=1).with_inventory(max_slots=cfg.hero_inventory_slots, max_weight=cfg.hero_inventory_weight, weapon=gear.get("weapon", "iron_sword"), armor=gear.get("armor", "leather_vest"), accessory=gear.get("accessory")).with_starting_items(["small_hp_potion"] * 3).with_home_storage().with_talents(race="hero").build())
            world.add_entity(hero)
            self.total_spawned += 1
            
            # Hero house
            h_pos = Vector2(cfg.town_center_x + (h_idx % 3) - 1, cfg.town_center_y + (h_idx // 3) + 1)
            world.buildings.append(Building(building_id=f"hero_house_{hero_eid}", name=f"{hero_name}'s House", pos=h_pos, building_type="hero_house"))

        # Global wanderers
        for _ in range(1, cfg.initial_entity_count):
            world.add_entity(generator.spawn(world))
            self.total_spawned += 1

        # Region-specific spawns
        for region in world.regions:
            mat = region.terrain
            race = TERRAIN_RACE.get(int(mat))
            for loc in region.locations:
                self._spawn_location_mobs(world, loc, region, generator, cfg, rng, mat, race)
            
            if race:
                roam_count = rng.next_int(Domain.SPAWN, int(mat) * 500 + region.center.x, region.center.y, 2, 4)
                for _ in range(roam_count):
                    ent = generator.spawn_race(world, race, near_pos=region.center, difficulty_tier=region.difficulty)
                    ent.region_id = region.region_id
                    world.add_entity(ent)
                    self.total_spawned += 1

        # Resource nodes
        self._spawn_wild_resources(world, cfg, rng)

    def _spawn_location_mobs(self, world, loc, region, generator: EntityGenerator, cfg, rng: DeterministicRNG, mat, race):
        if loc.location_type == "enemy_camp":
            chief = generator.spawn(world, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=region.difficulty)
            chief.region_id = region.region_id
            world.add_entity(chief)
            self.total_spawned += 1
            for _ in range(min(cfg.camp_max_guards, 3)):
                guard = generator.spawn(world, tier=EnemyTier.WARRIOR, near_pos=loc.pos, difficulty_tier=region.difficulty)
                guard.region_id = region.region_id
                world.add_entity(guard)
                self.total_spawned += 1
            if race:
                mob_count = rng.next_int(Domain.SPAWN, int(mat) * 1000 + loc.pos.x, loc.pos.y, 2, 4)
                for _ in range(mob_count):
                    ent = generator.spawn_race(world, race, near_pos=loc.pos, difficulty_tier=region.difficulty)
                    ent.region_id = region.region_id
                    world.add_entity(ent)
                    self.total_spawned += 1
        elif loc.location_type == "boss_arena":
            boss_diff = min(region.difficulty + 1, 4)
            boss = generator.spawn(world, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=boss_diff)
            boss.region_id = region.region_id
            world.add_entity(boss)
            self.total_spawned += 1
            if race:
                elite = generator.spawn_race(world, race, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=boss_diff)
                elite.region_id = region.region_id
                world.add_entity(elite)
                self.total_spawned += 1
        elif loc.location_type == "resource_grove":
            resource_defs = TERRAIN_RESOURCES.get(int(mat), [])
            if resource_defs:
                node_count = rng.next_int(Domain.HARVEST, loc.pos.x * 100, loc.pos.y, 3, 5)
                for ni in range(node_count):
                    rtype, rname, yields, max_h, respawn, h_ticks = resource_defs[ni % len(resource_defs)]
                    for attempt in range(30):
                        ox = rng.next_int(Domain.HARVEST, loc.pos.x * 10 + ni, attempt, -4, 4)
                        oy = rng.next_int(Domain.HARVEST, loc.pos.y * 10 + ni, attempt + 50, -4, 4)
                        npos = Vector2(loc.pos.x + ox, loc.pos.y + oy)
                        if world.grid.in_bounds(npos) and world.grid.get(npos) in (mat, Material.FLOOR):
                            node = ResourceNode(node_id=world.allocate_node_id(), resource_type=rtype, name=rname, pos=npos, terrain=mat, yields_item=yields, remaining=max_h, max_harvests=max_h, respawn_cooldown=respawn, harvest_ticks=h_ticks)
                            world.add_resource_node(node)
                            break
        elif loc.location_type == "dungeon_entrance":
            if race:
                for _ in range(2):
                    guard = generator.spawn_race(world, race, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=region.difficulty)
                    guard.region_id = region.region_id
                    world.add_entity(guard)
                    self.total_spawned += 1

    def _spawn_wild_resources(self, world, cfg, rng: DeterministicRNG):
        for bi in range(12):
            for attempt in range(30):
                bx = rng.next_int(Domain.HARVEST, 5000 + bi, attempt, 0, cfg.grid_width - 1)
                by = rng.next_int(Domain.HARVEST, 5000 + bi, attempt + 50, 0, cfg.grid_height - 1)
                bpos = Vector2(bx, by)
                if world.grid.in_bounds(bpos) and world.grid.get(bpos) == Material.FLOOR:
                    node = ResourceNode(node_id=world.allocate_node_id(), resource_type="berry_bush", name="Wild Berry Bush", pos=bpos, terrain=Material.FLOOR, yields_item="wild_berries", remaining=2, max_harvests=2, respawn_cooldown=25, harvest_ticks=1)
                    world.add_resource_node(node)
                    break

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/engine/__init__.py
"""Engine layer: world loop, action queue, worker pool, conflict resolution."""

from src.engine.action_queue import ActionQueue
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.engine.world_loop import WorldLoop

__all__ = ["ActionQueue", "ConflictResolver", "WorkerPool", "WorldLoop"]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/engine/action_queue.py
"""Thread-safe action queue connecting workers to the WorldLoop."""

from __future__ import annotations

import queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.actions.base import ActionProposal


class ActionQueue:
    """MPSC (multiple-producer, single-consumer) queue for ActionProposals.

    Workers push proposals; the WorldLoop drains them each tick.
    """

    __slots__ = ("_queue",)

    def __init__(self) -> None:
        self._queue: queue.Queue[ActionProposal] = queue.Queue()

    def push(self, proposal: ActionProposal) -> None:
        """Thread-safe enqueue."""
        self._queue.put_nowait(proposal)

    def drain(self) -> list[ActionProposal]:
        """Drain all pending proposals (called by WorldLoop on the main thread)."""
        proposals: list[ActionProposal] = []
        while True:
            try:
                proposals.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return proposals

    def size(self) -> int:
        """Return the approximate size of the queue (not guaranteed exact across threads)."""
        return self._queue.qsize()

    @property
    def empty(self) -> bool:
        return self._queue.empty()

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/engine/conflict_resolver.py
"""Deterministic conflict resolution for parallel action proposals."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.actions.combat import CombatAction
from src.actions.move import MoveAction
from src.actions.rest import RestAction
from src.actions.repair import RepairAction
from src.core.models.enums import ActionType
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)


class ConflictResolver:
    """Sorts, validates, and applies proposals in deterministic order.

    Resolution policies:
    - Movement: earliest next_act_at wins; tie-break by lowest entity ID.
    - Combat: processed sequentially by initiative (speed); dead targets fail validation.
    """

    __slots__ = ("_config", "_combat_action")

    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._combat_action = CombatAction(config, rng)

    def resolve(self, proposals: list[ActionProposal], world: WorldState) -> list[ActionProposal]:
        """Validate and apply proposals. Returns the list of *applied* proposals."""
        if not proposals:
            return []

        sorted_proposals = self._sort(proposals, world)
        applied: list[ActionProposal] = []
        occupied = self._build_occupied_set(world)

        for p in sorted_proposals:
            if self._apply_one(p, world, occupied):
                applied.append(p)

        return applied

    # -- internals --

    @staticmethod
    def _sort(proposals: list[ActionProposal], world: WorldState) -> list[ActionProposal]:
        """Deterministic sort: action type priority, then next_act_at, then entity ID."""

        def sort_key(p: ActionProposal) -> tuple[int, float, int]:
            entity = world.entities.get(p.actor_id)
            next_act = entity.next_act_at if entity else float("inf")
            return (p.verb.value, next_act, p.actor_id)

        return sorted(proposals, key=sort_key)

    @staticmethod
    def _build_occupied_set(world: WorldState) -> set[tuple[int, int]]:
        return {(e.spatial.pos.x, e.spatial.pos.y) for e in world.entities.values() if e.combat.alive}

    def _apply_one(
        self,
        proposal: ActionProposal,
        world: WorldState,
        occupied: set[tuple[int, int]],
    ) -> bool:
        match proposal.verb:
            case ActionType.REPAIR:
                if RepairAction.validate(proposal, world):
                    RepairAction.apply(proposal, world)
                    return True
            case ActionType.REST:
                if RestAction.validate(proposal, world):
                    RestAction.apply(proposal, world)
                    return True

            case ActionType.MOVE:
                if MoveAction.validate(proposal, world, occupied):
                    entity = world.entities.get(proposal.actor_id)
                    if entity:
                        # Free old position, claim new
                        occupied.discard((entity.spatial.pos.x, entity.spatial.pos.y))
                    MoveAction.apply(proposal, world)
                    target: Vector2 = proposal.target
                    occupied.add((target.x, target.y))
                    return True

            case ActionType.ATTACK:
                if self._combat_action.validate(proposal, world):
                    self._combat_action.apply(proposal, world)
                    return True

            case ActionType.USE_ITEM | ActionType.LOOT | ActionType.HARVEST | ActionType.USE_SKILL:
                # Validated and applied later in WorldLoop
                entity = world.entities.get(proposal.actor_id)
                if entity and entity.combat.alive:
                    return True

        from src.utils.metrics import SIM_INVALID_ACTIONS_TOTAL
        SIM_INVALID_ACTIONS_TOTAL.labels(action_type=proposal.verb.name.lower(), reason="validation_failed").inc()
        
        logger.debug("Rejected: %s", proposal)
        return False

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/engine/worker_pool.py
"""Parallel worker pool for AI decision-making (RabbitMQ Distributed AMQP)."""

from __future__ import annotations

import logging
import pickle
import time
from typing import TYPE_CHECKING, Any

import pika
from pika.exceptions import AMQPError

from src.core.models.enums import AIState, Domain
from src.api.rabbitmq_client import get_rabbitmq

if TYPE_CHECKING:
    from src.actions.base import ActionProposal
    from src.config import SimulationConfig
    from src.core.entities.entity import Entity
    from src.core.models.snapshot import Snapshot
    from src.engine.action_queue import ActionQueue

from src.ai.brain import AIBrain
from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)


class WorkerPool:
    """Distributes AI decisions to external RabbitMQ Docker workers.

    Picks the complete immutable Snapshot once per tick and broadcasts
    it to all workers. Then publishes lightweight `(tick, entity_id)` tasks to a 
    round-robin work queue, and consumes the resulting ActionProposals.
    """

    __slots__ = ("_config", "_brain", "_rng", "_channel", "_snapshot_exchange", "_tasks_queue", "_results_queue", "_logger")

    def __init__(self, config: SimulationConfig, brain: AIBrain, rng: DeterministicRNG) -> None:
        self._config = config
        self._brain = brain
        self._rng = rng
        
        # We only use RabbitMQ if num_workers > 1
        self._channel: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._snapshot_exchange = 'ai_snapshots'
        self._tasks_queue = 'ai_tasks'
        self._results_queue = 'ai_results'

        if self._config.num_workers > 1:
            self._init_rabbitmq()
            
        # Wrapped logger (Phase L3 Logging)
        from src.utils.logging import RobustLoggerAdapter
        self._logger = RobustLoggerAdapter(logger, {'component': 'worker_pool', 'worker_id': 'master', 'tick': 0})

    def _init_rabbitmq(self) -> None:
        try:
            conn = get_rabbitmq()
            if conn is not None:
                self._channel = conn.channel()
                # Declare infrastructure
                self._channel.exchange_declare(exchange=self._snapshot_exchange, exchange_type='fanout')
                self._channel.queue_declare(queue=self._tasks_queue, durable=False)
                self._channel.queue_declare(queue=self._results_queue, durable=False)
                logger.info("WorkerPool initialized RabbitMQ connection.")
            else:
                logger.warning("WorkerPool: RabbitMQ connection unavailable. Falling back to inline.")
                self._channel = None
        except Exception as e:
            from src.utils.metrics import SIM_ERRORS_TOTAL
            SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="worker_pool").inc()
            logger.error("WorkerPool failed to connect to RabbitMQ: %s. Falling back to inline execution.", e)
            self._channel = None

    def dispatch(
        self,
        entities: list[Entity],
        snapshot: Snapshot,
        action_queue: ActionQueue,
    ) -> None:
        """Submit AI tasks for all *entities* and collect results into *action_queue*."""
        if not entities:
            return

        # Fast path: single-worker mode or unrecoverable RMQ error — run inline
        if self._config.num_workers <= 1 or not self._channel:
            from src.utils.metrics import SIM_WORKER_HEALTH
            SIM_WORKER_HEALTH.labels(worker_id="inline", state="busy").set(1)
            self._dispatch_inline(entities, snapshot, action_queue)
            SIM_WORKER_HEALTH.labels(worker_id="inline", state="busy").set(0)
            return

        # Distributed path
        try:
            from src.utils.metrics import SIM_WORKER_HEALTH
            SIM_WORKER_HEALTH.labels(worker_id="rabbitmq", state="busy").set(1)
            self._dispatch_rabbitmq(entities, snapshot, action_queue)
            SIM_WORKER_HEALTH.labels(worker_id="rabbitmq", state="busy").set(0)
            SIM_WORKER_HEALTH.labels(worker_id="rabbitmq", state="error").set(0)
        except Exception as e:
            from src.utils.metrics import SIM_ERRORS_TOTAL, SIM_WORKER_HEALTH
            SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="rabbitmq_dispatch").inc()
            SIM_WORKER_HEALTH.labels(worker_id="rabbitmq", state="busy").set(0)
            SIM_WORKER_HEALTH.labels(worker_id="rabbitmq", state="error").set(1)
            self._logger.exception("RabbitMQ dispatch crashed, falling back to inline.", extra={'tick': snapshot.tick})
            # Reconnect for next tick
            self._channel = None
            self._init_rabbitmq()
            self._dispatch_inline(entities, snapshot, action_queue)

    def _dispatch_inline(
        self,
        entities: list[Entity],
        snapshot: Snapshot,
        action_queue: ActionQueue,
    ) -> None:
        """Fallback inline execution loop (No GIL workaround)."""
        for entity in entities:
            # --- Chaos Mode: Fault Injection ---
            if self._config.chaos_enabled and self._rng.next_float(Domain.AI_DECISION, entity.id, snapshot.tick + 77) < self._config.chaos_drop_rate:
                logger.warning("Chaos Mode (Inline): Dropping AI result for entity %d", entity.id)
                continue

            try:
                _eid, new_state, proposal = self._think(entity, snapshot)
                action_queue.push(proposal)
            except Exception as e:
                from src.utils.metrics import SIM_ERRORS_TOTAL
                SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="ai_think_inline").inc()
                logger.exception("AI failed for entity %d", entity.id)
    def _dispatch_rabbitmq(
        self,
        entities: list[Entity],
        snapshot: Snapshot,
        action_queue: ActionQueue,
    ) -> None:
        """Distribute workloads across RabbitMQ nodes using batching."""
        assert self._channel is not None
        
        # 1. Broadcast the tick's snapshot to all workers
        snapshot_bytes = pickle.dumps(snapshot)
        self._channel.basic_publish(
            exchange=self._snapshot_exchange,
            routing_key='',
            body=snapshot_bytes,
        )

        # 2. Publish the batch task
        entity_ids = [e.id for e in entities]
        batch_task = {"tick": snapshot.tick, "entity_ids": entity_ids}
        logger.info("WorkerPool publishing AI batch for tick %d (%d entities)", snapshot.tick, len(entity_ids))
        self._channel.basic_publish(
            exchange='',
            routing_key=self._tasks_queue,
            body=pickle.dumps(batch_task),
        )

        # 3. Synchronously wait for the batched result
        timeout = float(self._config.worker_timeout_seconds)
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                from src.utils.metrics import SIM_ERRORS_TOTAL
                SIM_ERRORS_TOTAL.labels(exception_type="TimeoutError", component="worker_pool_batch").inc()
                logger.warning("WorkerPool timed out waiting for AI batch. Tick: %d", snapshot.tick)
                break
                
            method_frame, header_frame, body = self._channel.basic_get(queue=self._results_queue, auto_ack=True)
            if method_frame:
                try:
                    result_batch = pickle.loads(body)
                    tick = result_batch.get("tick")
                    
                    if tick == snapshot.tick:
                        results = result_batch.get("results", [])
                        for res in results:
                            eid = res.get("entity_id")
                            proposal = res.get("proposal")
                            
                            # --- Chaos Mode: Fault Injection ---
                            if self._config.chaos_enabled and self._rng.next_float(Domain.AI_DECISION, eid or 0, tick + 99) < self._config.chaos_drop_rate:
                                continue

                            if proposal:
                                action_queue.push(proposal)
                        
                        # We got our batch, we are done for this tick
                        break
                    else:
                        # Stale result from a previous timed-out tick, keep looking
                        continue
                except Exception as e:
                    from src.utils.metrics import SIM_ERRORS_TOTAL
                    SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="worker_unpickle_batch").inc()
                    logger.error("Failed to unpickle worker batch response: %s", e)
                    break 
            else:
                # Polling interval - slightly more aggressive wait than 5ms if we know we are waiting for a big batch
                time.sleep(0.002)


    def _think(self, entity: Entity, snapshot: Snapshot) -> tuple[int, AIState, ActionProposal]:
        """Run AI for a single entity (executed inline)."""
        from dataclasses import replace

        new_state, proposal = self._brain.decide(entity, snapshot)
        proposal = replace(proposal, new_ai_state=int(new_state))
        return entity.id, new_state, proposal

    def shutdown(self) -> None:
        """Close RabbitMQ channels."""
        if self._channel and self._channel.is_open:
            try:
                self._channel.close()
            except AMQPError:
                pass
            self._channel = None

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/engine/world_loop.py
"""WorldLoop — the authoritative 4-phase tick engine.

Phase cycle:
  1. Scheduling — identify ready entities, dispatch to workers
  2. Wait & Collect — drain the action queue
  3. Conflict Resolution & Application — validate + apply proposals
  4. Cleanup & Advancement — remove dead, territory effects, advance tick
"""

from __future__ import annotations

import logging
import random
import time
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.core.gameplay.effects import EffectType, territory_debuff
from src.core.models.enums import AIState, ActionType, Domain
from src.core.entities.entity import Entity, Stats, Vector2, Inventory
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.models.snapshot import Snapshot
from src.engine.action_queue import ActionQueue
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.systems.infrastructure.manager import SystemManager
from src.systems.infrastructure.base import SystemContext
from src.systems.gameplay.combat_system import CombatSystem
from src.systems.lifecycle.progression_system import ProgressionSystem
from src.systems.world.world_object_system import WorldObjectSystem
from src.systems.gameplay.quest_system import QuestSystem
from src.systems.calamity.calamity_system import CalamitySystem
from src.systems.world.environment_system import EnvironmentSystem
from src.systems.gameplay.economy_system import EconomySystem
from src.systems.gameplay.action_system import ActionSystem
from src.systems.lifecycle.hero_lifecycle_system import HeroLifecycleSystem
from src.systems.infrastructure.telemetry_system import TelemetrySystem
from src.systems.lifecycle.world_evolution_system import WorldEvolutionSystem
from src.systems.world.generator import EntityGenerator
from src.utils.metrics import SIM_TICK_DURATION

import pickle
from src.api.kafka_client import get_kafka_producer, KAFKA_TOPIC_EVENTS, KAFKA_TOPIC_SNAPSHOTS

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG
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
        "_system_manager",
        "_action_system",
        "_hero_lifecycle",
        "_logger",
        "_telemetry_bridge",
        "_history_system"
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
        
        # Wrapped logger for automatic context (Phase L3 Logging)
        from src.utils.logging import RobustLoggerAdapter
        self._logger = RobustLoggerAdapter(logger, {'tick': 0, 'component': 'world_loop'})
        
        # Initialize Systems (Phase 4)
        self._system_manager = SystemManager(config, rng or DeterministicRNG(0))
        self._system_manager.register(CombatSystem(config, self._rng), config.subsystem_rate_core)
        self._system_manager.register(ProgressionSystem(config, self._rng), config.subsystem_rate_economy)
        self._system_manager.register(WorldObjectSystem(config, self._rng), config.subsystem_rate_economy)
        self._system_manager.register(QuestSystem(config, self._rng), config.subsystem_rate_economy)
        self._system_manager.register(CalamitySystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(EnvironmentSystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(EconomySystem(config, self._rng), config.subsystem_rate_economy)
        
        from src.systems.world.strategy_system import StrategySystem
        from src.systems.calamity.calamity_evolution import CalamityEvolutionSystem
        from src.systems.infrastructure.history_system import HistorySystem
        self._system_manager.register(StrategySystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(CalamityEvolutionSystem(config, self._rng), config.subsystem_rate_environment)
        self._history_system = HistorySystem(config, self._rng)
        self._system_manager.register(self._history_system, config.subsystem_rate_environment)
        
        # ActionSystem for post-resolution hooks
        self._action_system = ActionSystem(config, self._rng)
        
        # Dedicated Epic-17 Hero Mechanics
        self._hero_lifecycle = HeroLifecycleSystem(config, self._rng)
        self._system_manager.register(self._hero_lifecycle, config.subsystem_rate_core)
        
        # New decoupled systems (Phase 2)
        self._system_manager.register(WorldEvolutionSystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(TelemetrySystem(config, self._rng), config.subsystem_rate_economy)
        
        from src.systems.infrastructure.event_system import EventBus, TelemetryBridge
        self._world.event_bus = EventBus()
        self._telemetry_bridge = TelemetryBridge(self._world, self._emit)
        self._telemetry_bridge.attach(self._world.event_bus)
        
        # Explicit initialization of all systems with context
        self._system_manager.init_all(world, generator, self._faction_reg, self._emit)
        self._action_system.on_init(SystemContext(config, world, self._rng, generator, self._faction_reg, self._emit))

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
        alive_count = sum(1 for e in self._world.entities.values() if e.combat.alive and e.kind != "generator")

        if alive_count == 0 and tick > 0:
            self._logger.info("Tick %d: No entities alive — simulation ended.", tick, extra={'tick': tick})
            return False

        if tick >= self._config.max_ticks:
            self._logger.info("Tick %d: Max ticks reached.", tick, extra={'tick': tick})
            return False

        self._step()
        self._world.tick += 1
        return True

    def create_snapshot(self) -> Snapshot:
        """Create an immutable snapshot of the current world state."""
        return Snapshot.from_world(self._world)

    def run(self) -> None:
        """Execute the simulation until max_ticks or no entities remain."""
        self._logger.extra['tick'] = self._world.tick
        self._logger.info("=== Simulation started (seed=%d) ===", self._world.seed)

        self._world.tick = 0
        while self._world.tick < self._config.max_ticks:
            if not self.tick_once():
                break

            if self._world.tick % 50 == 0:
                alive_count = sum(1 for e in self._world.entities.values() if e.combat.alive and e.kind != "generator")
                self._logger.info(
                    "Tick %d: %d entities alive",
                    self._world.tick,
                    alive_count,
                    extra={'tick': self._world.tick}
                )

        self._logger.info("=== Simulation finished at tick %d ===", self._world.tick, extra={'tick': self._world.tick})
        if self._recorder:
            self._recorder.flush()

    def _step(self) -> None:
        """Execute one complete tick cycle (Phase 4 Orchestration)."""
        self._logger.extra['tick'] = self._world.tick
        self._tick_events = []
        tick = self._world.tick
        t0 = time.perf_counter()

        # --- Phase 1: Pre-Action Systems (Calamities, Environment, etc.) ---
        # Note: These run at various rates via the SystemManager
        with SIM_TICK_DURATION.labels(phase="subsystems").time():
            self._system_manager.tick(self._world, tick)

        # --- Phase 2: Action Generation & Resolution ---
        self._phase_generators()
        
        with SIM_TICK_DURATION.labels(phase="scheduling").time():
            ready_entities = self._phase_scheduling()

        applied: list[ActionProposal] = []
        if ready_entities:
            # Wait & Collect
            with SIM_TICK_DURATION.labels(phase="collect").time():
                snapshot = Snapshot.from_world(self._world)
                self._worker_pool.dispatch(ready_entities, snapshot, self._action_queue)
                proposals = self._action_queue.drain()

                # Chaos Resilience
                if len(proposals) < len(ready_entities):
                    acted_ids = {p.actor_id for p in proposals}
                    for entity in ready_entities:
                        if entity.id not in acted_ids:
                            from src.utils.metrics import SIM_INVALID_ACTIONS_TOTAL
                            SIM_INVALID_ACTIONS_TOTAL.labels(action_type="rest", reason="timeout").inc()
                            
                            proposals.append(ActionProposal(
                                actor_id=entity.id,
                                verb=ActionType.REST,
                                target=None,
                                reason="Chaos Drop / Worker Timeout",
                                new_ai_state=int(entity.mind.ai_state)
                            ))

            # Resolution & Application
            with SIM_TICK_DURATION.labels(phase="resolve").time():
                pre_positions = {e.id: (e.spatial.pos.x, e.spatial.pos.y) for e in self._world.entities.values()}
                applied = self._conflict_resolver.resolve(proposals, self._world)
                self._last_applied = applied
                self._update_ai_states(applied)

                # --- Phase 3: Post-Action Tactical Hooks ---
                ctx = SystemContext(self._config, self._world, self._rng, self._generator, self._faction_reg, self._emit)
                self._action_system.handle_tactical_maneuvers(ctx, applied, pre_positions)
                
                # Execute state mutations (items, loot, harvest) and visualization updates
                with SIM_TICK_DURATION.labels(phase="item_processing").time():
                    self._action_system.process_applied_actions(ctx, applied)

                # --- Phase 4: Spatial Index Consistency ---
                # Rebuild after MOVE actions have updated entity positions
                self._world.spatial_index.rebuild(self._world.entities.values())

                # Emit standardized events
                _cat_map = {"REST": "rest", "MOVE": "movement", "USE_ITEM": "item", "LOOT": "loot", "HARVEST": "harvest"}
                for action in applied:
                    if action.verb.name in ("ATTACK", "USE_SKILL"):
                        continue
                    involved = [action.actor_id]
                    if isinstance(action.target, int): involved.append(action.target)
                    cat = _cat_map.get(action.verb.name, action.verb.name.lower())
                    self._emit(cat, f"Entity {action.actor_id}: {action.verb.name} → {action.reason}", entity_ids=tuple(involved))

        t4 = time.perf_counter()
        if ready_entities:
            SIM_TICK_DURATION.labels(phase="total_active").observe(t4 - t0)
        else:
            SIM_TICK_DURATION.labels(phase="total_idle").observe(t4 - t0)

        # --- Phase 5: Persistence & Streaming ---
        with SIM_TICK_DURATION.labels(phase="persistence").time():
            self._handle_kafka_publishing(tick, applied)
            self._handle_redis_publishing(tick, applied)

        # --- Phase 4: Cleanup & Advancement ---
        with SIM_TICK_DURATION.labels(phase="cleanup").time():
            self._phase_cleanup()

    def _handle_kafka_publishing(self, tick: int, applied: list[ActionProposal]) -> None:
        """Publish snapshots and events to Kafka for persistence and analytics."""
        from src.utils.metrics import SIM_KAFKA_PUBLISH_DURATION
        
        # publish immutable snapshot to Kafka every 1000 ticks for compaction
        if tick % 1000 == 0:
            producer = get_kafka_producer()
            if producer:
                try:
                    with SIM_KAFKA_PUBLISH_DURATION.labels(type="snapshot").time():
                        snap = Snapshot.from_world(self._world)
                        producer.produce(
                            KAFKA_TOPIC_SNAPSHOTS,
                            key="latest", # use static key for log compaction
                            value=pickle.dumps(snap)
                        )
                        producer.poll(0)
                except Exception as e:
                    logger.error("Failed to publish snapshot to Kafka: %s", e)
                    
        # publish deterministic tick events
        if applied:
            producer = get_kafka_producer()
            if producer:
                try:
                    with SIM_KAFKA_PUBLISH_DURATION.labels(type="events").time():
                        payload = {"tick": tick, "proposals": applied}
                        producer.produce(
                            KAFKA_TOPIC_EVENTS,
                            key=str(tick),
                            value=pickle.dumps(payload)
                        )
                        producer.poll(0)
                except Exception as e:
                    logger.error("Failed to publish events to Kafka: %s", e)

    def _handle_redis_publishing(self, tick: int, applied: list[ActionProposal]) -> None:
        """Hook for additional Redis-based persistence (managed primarily by EngineManager)."""
        # We can use this to track secondary Redis tasks if needed.
        # For now, it's a placeholder to satisfy the persistence phase call in _step.
        pass

    def _phase_generators(self) -> None:
        """Run generator entities (immediate, no worker dispatch)."""
        if self._generator.should_spawn(self._world):
            entity = self._generator.spawn(self._world)
            self._world.add_entity(entity)
            self._logger.info("Tick %d: Spawned %s #%d at %s", self._world.tick, entity.kind, entity.id, entity.spatial.pos)

    def _phase_scheduling(self) -> list:
        """Identify entities ready to act this tick."""
        current_time = float(self._world.tick)
        ready = [
            e
            for e in self._world.entities.values()
            if e.combat.alive and e.kind != "generator" and e.next_act_at <= current_time
        ]
        # Deterministic order: next_act_at, then entity ID
        ready.sort(key=lambda e: (e.next_act_at, e.id))
        return ready

    def _update_ai_states(self, applied: list[ActionProposal]) -> None:
        """Propagate new AI states from brain decisions after action resolution."""
        for proposal in applied:
            entity = self._world.entities.get(proposal.actor_id)
            if entity is None:
                continue
            if proposal.new_ai_state is not None:
                entity.mind.ai_state = AIState(proposal.new_ai_state)
            if proposal.reason:
                entity.mind.last_reason = proposal.reason

    def _phase_cleanup(self) -> None:
        """Remove dead entities, respawn heroes at town, drop loot, rebuild spatial index."""
        dead_ids = sorted([eid for eid, e in self._world.entities.items() if not e.combat.alive])
        for eid in dead_ids:
            entity = self._world.entities.get(eid)
            if entity is None:
                continue

            if entity.identity.faction == Faction.HERO_GUILD and entity.home_pos is not None:
                ctx = SystemContext(self._config, self._world, self._rng, self._generator, self._faction_reg, self._emit)
                resolved = self._hero_lifecycle.process_hero_death(ctx, entity, self._world.tick)
                if resolved:
                    continue

            # Default logic for generic mobs / non-hero entities
            from src.utils.metrics import TOTAL_DEATHS
            TOTAL_DEATHS.inc()

            if entity.inventory:
                dropped = entity.inventory.get_all_item_ids()
                if dropped:
                    self._world.drop_items(entity.spatial.pos, dropped)
                    self._logger.info(
                        "Tick %d: Entity %d (%s) dropped %d items at %s",
                        self._world.tick, eid, entity.kind, len(dropped), entity.spatial.pos,
                    )

            removed = self._world.remove_entity(eid)
            if removed:
                self._logger.info("Tick %d: Entity %d (%s Lv%d) died.", self._world.tick, eid, removed.kind, removed.stats.progression.level)
                if hasattr(self._world, "event_bus") and self._world.event_bus:
                    from src.core.data.events import DeathEvent
                    self._world.event_bus.publish(DeathEvent(
                        entity_id=eid, killer_id=None,
                        x=removed.spatial.pos.x, y=removed.spatial.pos.y,
                        level_at_death=removed.stats.progression.level,
                        is_permadeath=True
                    ))

    def _check_endgame_conditions(self) -> bool:
        if self._world.world_age < 50000: return True
        func = sum(1 for b in self._world.buildings if b.is_functional and b.durability > b.max_durability * 0.8)
        if func == len(self._world.buildings): return False
        dest = sum(1 for b in self._world.buildings if not b.is_functional)
        if dest >= 3: return False
        return True

    def _apply_monument_buffs(self, hero) -> None:
        for m in self._world.monuments:
            if m.buff_type == "hp":
                hero.stats.combat.max_hp = int(hero.stats.combat.max_hp * 1.1)
                hero.stats.combat.hp = hero.stats.combat.max_hp
            elif m.buff_type == "atk":
                hero.stats.combat.atk = int(hero.stats.combat.atk * 1.1)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/platform/rng.py
"""Domain-separated deterministic RNG using xxhash.

The Golden Rule: The outcome of Tick T depends ONLY on
WorldSeed + State at T-1. Thread scheduling order must not matter.

Formula: RNG_Value = Hash(WorldSeed, Domain, EntityID, Tick)
"""

from __future__ import annotations
import struct
import xxhash
from src.core.models.enums import Domain

class DeterministicRNG:
    """Stateless domain-separated pseudo-random number generator.
    Each call is a pure function of (seed, domain, entity_id, tick).
    """

    __slots__ = ("_seed",)
    _MAX_UINT64 = (1 << 64) - 1

    def __init__(self, seed: int) -> None:
        self._seed = seed

    def _hash(self, domain: Domain, entity_id: int, tick: int) -> int:
        payload = struct.pack("<qiqi", self._seed, domain.value, entity_id, tick)
        return xxhash.xxh64(payload).intdigest()

    def next_float(self, domain: Domain, entity_id: int, tick: int) -> float:
        """Return a deterministic float in [0.0, 1.0)."""
        return self._hash(domain, entity_id, tick) / (self._MAX_UINT64 + 1)

    def next_int(self, domain: Domain, entity_id: int, tick: int, low: int, high: int) -> int:
        """Return a deterministic integer in [low, high] inclusive."""
        f = self.next_float(domain, entity_id, tick)
        return low + int(f * (high - low + 1))

    def next_bool(self, domain: Domain, entity_id: int, tick: int, probability: float = 0.5) -> bool:
        """Return True with the given probability."""
        return self.next_float(domain, entity_id, tick) < probability

    def weighted_choice(self, domain: Domain, entity_id: int, tick: int, items: list, weights: list[float]):
        """Deterministic weighted choice."""
        total = sum(weights)
        if total <= 0: return items[0]
        roll = self.next_float(domain, entity_id, tick) * total
        accum = 0.0
        for i, weight in enumerate(weights):
            accum += weight
            if roll <= accum:
                return items[i]
        return items[-1]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/platform/spatial_hash.py
"""Spatial hashing for O(1) neighbor lookups."""

from __future__ import annotations

from collections import defaultdict

from src.core.models import Vector2


class SpatialHash:
    """Grid-based spatial index mapping cell keys to sets of entity IDs."""

    __slots__ = ("_cell_size", "_cells")

    def __init__(self, cell_size: int = 8) -> None:
        self._cell_size = cell_size
        self._cells: dict[tuple[int, int], set[int]] = defaultdict(set)

    def _key(self, pos: Vector2) -> tuple[int, int]:
        return pos.x // self._cell_size, pos.y // self._cell_size

    def insert(self, entity_id: int, pos: Vector2) -> None:
        self._cells[self._key(pos)].add(entity_id)

    def remove(self, entity_id: int, pos: Vector2) -> None:
        key = self._key(pos)
        bucket = self._cells.get(key)
        if bucket is not None:
            bucket.discard(entity_id)
            if not bucket:
                del self._cells[key]

    def move(self, entity_id: int, old_pos: Vector2, new_pos: Vector2) -> None:
        old_key = self._key(old_pos)
        new_key = self._key(new_pos)
        if old_key != new_key:
            self.remove(entity_id, old_pos)
            self.insert(entity_id, new_pos)

    def query_cell(self, pos: Vector2) -> set[int]:
        """Return entity IDs in the same cell as *pos*."""
        return set(self._cells.get(self._key(pos), set()))

    def query_radius(self, pos: Vector2, radius: int) -> set[int]:
        """Return entity IDs within *radius* cells of *pos*."""
        cx, cy = self._key(pos)
        r = (radius // self._cell_size) + 1
        result: set[int] = set()
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                bucket = self._cells.get((cx + dx, cy + dy))
                if bucket:
                    result.update(bucket)
        return result

    def clear(self) -> None:
        self._cells.clear()

    def rebuild(self, entities: Iterable[Entity]) -> None:
        """Clear and re-insert all entities to ensure index consistency."""
        self.clear()
        for entity in entities:
            if hasattr(entity, "spatial") and entity.spatial:
                self.insert(entity.id, entity.spatial.pos)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/__init__.py
"""Engine systems: RNG, spatial indexing, entity generation."""

from src.platform.rng import DeterministicRNG
from src.platform.spatial_hash import SpatialHash
from src.systems.world.generator import EntityGenerator

__all__ = ["DeterministicRNG", "EntityGenerator", "SpatialHash"]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/calamity/__init__.py


#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/calamity/calamity_evolution.py
"""CalamityEvolutionSystem manages world boss growth and skill acquisition."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.models.enums import AIState, Element
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class CalamityEvolutionSystem(System):
    """System that evolves World Bosses (Calamities) based on their achievements."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Process evolution checks every 500 ticks."""
        if tick % 500 != 0:
            return

        for entity in context.world.entities.values():
            if not entity.combat.alive or not entity.identity.is_world_boss:
                continue

            self._check_evolution(context, entity, tick)

    def _check_evolution(self, context: SystemContext, entity: Any, tick: int) -> None:
        """Evaluate glory and trigger evolution if threshold met."""
        glory_total = sum(
            entry.get("impact", 0.0) 
            for entry in entity.mind.memory_log 
            if entry.get("type") == "GLORY"
        )

        # Basic evolution logic: every 50 glory = 1 evolution level
        current_evo = entity.mind.memory.get("evolution_level", 0)
        target_evo = int(glory_total // 50)

        if target_evo > current_evo:
            self._evolve(context, entity, current_evo, target_evo)
            entity.mind.memory["evolution_level"] = target_evo

    def _evolve(self, context: SystemContext, entity: Any, old_level: int, new_level: int) -> None:
        """Apply stat boosts and new skills upon evolution."""
        levels_gained = new_level - old_level
        
        # Stat boosts: +20% HP/ATK per evolution level
        boost_factor = 1.0 + (0.2 * levels_gained)
        entity.combat.max_hp = int(entity.combat.max_hp * boost_factor)
        entity.combat.hp = entity.combat.max_hp
        entity.combat.atk = int(entity.combat.atk * boost_factor)
        
        # Evolution title update
        entity.identity.display_name = f"Evolved {entity.identity.display_name}"
        
        from src.core.data.events import RenownEvent
        if hasattr(context.world, "event_bus") and context.world.event_bus:
            context.world.event_bus.publish(RenownEvent(
                entity_id=entity.id,
                glory_type="evolution",
                description=f"The calamity {entity.kind} has EVOLVED into a more powerful form!",
                renown_gain=levels_gained * 10
            ))

        if context.emit:
            context.emit("calamity", f"CALAMITY {entity.id} ({entity.kind}) HAS EVOLVED! Level {old_level} → {new_level}",
                        entity_ids=(entity.id,),
                        metadata={"type": "evolution", "level": new_level})
        
        logger.info("Calamity %d evolved to level %d", entity.id, new_level)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/calamity/calamity_system.py
"""CalamitySystem manages world boss spawns and global maturity."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.models.enums import Domain, EnemyTier, EntityRole
from src.core.models import Vector2
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class CalamitySystem(System):
    """System for periodic world events and world boss orchestration."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute calamity phases."""
        self._update_world_evolution(context, tick)
        self._check_calamity_spawns(context, tick)
        self._apply_calamity_auras(context, tick)
        self._check_camp_reinforcements(context, tick)
        self._check_faction_raids(context, tick)

    def _update_world_evolution(self, context: SystemContext, tick: int) -> None:
        """Advance world 'maturity' which affects spawn rates and boss stats."""
        cfg = context.config
        world = context.world
        
        # World 'matures' every N ticks, increasing global difficulty
        if tick % 1000 == 0 and tick > 0:
            world.maturity = getattr(world, "maturity", 0) + 1
            if context.emit:
                context.emit("world", f"World maturity increased to level {world.maturity}",
                          metadata={"maturity": world.maturity})

    def _check_calamity_spawns(self, context: SystemContext, tick: int) -> None:
        """Randomly spawn a World Boss if conditions are met."""
        cfg = context.config
        world = context.world
        rng = context.rng
        
        # Check spawn interval
        last_spawn = getattr(world, "last_calamity_tick", 0)
        if tick - last_spawn < 2000 and tick > 0:
            return

        # Guaranteed spawn at 5000/10000 etc. or random chance
        force_spawn = (tick % 5000 == 0 and tick > 0)
        if force_spawn or rng.next_bool(Domain.SPAWN, 0, tick, 0.005):
            self._spawn_world_boss(context, tick)
            world.last_calamity_tick = tick

    def _spawn_world_boss(self, context: SystemContext, tick: int) -> None:
        """Construct and add a World Boss entity and bounty quests."""
        world = context.world
        gen = context.generator
        
        # Position far from town
        pos = Vector2(
            x=context.rng.next_int(Domain.SPAWN, 0, tick, 10, world.grid.width-10),
            y=context.rng.next_int(Domain.SPAWN, 0, tick + 1, 10, world.grid.height-10)
        )
        
        boss = gen.spawn_calamity(world, "gorath") if hasattr(gen, 'spawn_calamity') else gen.spawn_boss(world, pos=pos)
        boss.spatial.pos = pos
        boss.identity.role = EntityRole.WORLD_BOSS
        
        world.add_entity(boss)
        
        # Generate bounties for all high-level heroes
        from src.core.gameplay.quests import Quest, QuestType
        for hero in world.entities.values():
            if hero.combat.alive and hero.identity.role == EntityRole.HERO:
                bounty = Quest(
                    quest_id=f"bounty_{boss.kind}_{tick}_{hero.id}",
                    quest_type=QuestType.BOUNTY,
                    title=f"Bounty: {boss.identity.display_name}",
                    description=f"A great calamity has appeared! Defeat {boss.identity.display_name} to restore peace.",
                    target_kind=boss.identity.display_name,
                    target_count=1,
                    gold_reward=1000,
                    xp_reward=1000
                )
                hero.quests.append(bounty)

        if context.emit:
            context.emit("calamity", f"A great calamity has appeared: {boss.identity.display_name} at {pos}!",
                      entity_ids=(boss.id,),
                      metadata={"kind": boss.kind, "pos": (pos.x, pos.y)})
        logger.warning("Tick %d: Spawned World Boss %s #%d at %s", tick, boss.identity.display_name, boss.id, pos)

    def _apply_calamity_auras(self, context: SystemContext, tick: int) -> None:
        """World Bosses emit global debuffs or local terrain effects."""
        world = context.world
        for entity in world.entities.values():
            if not entity.combat.alive or entity.identity.role != EntityRole.WORLD_BOSS:
                continue
                
            # Local aura: slow nearby non-bosses
            for other in world.entities_at_radius(entity.spatial.pos, 5):
                if other.id != entity.id and other.identity.role != EntityRole.WORLD_BOSS:
                    from src.core.gameplay.effects import skill_effect
                    other.effects.append(skill_effect(
                        spd_mod=-0.3,
                        duration=2,
                        source="Calamity Aura",
                        is_debuff=True
                    ))

    def _check_camp_reinforcements(self, context: SystemContext, tick: int) -> None:
        """Reinforce camps every 500 ticks."""
        if tick % 500 != 0 or tick == 0:
            return
            
        world = context.world
        gen = context.generator
        cfg = context.config
        
        for region in world.regions:
            for loc in region.locations:
                if loc.location_type == "enemy_camp":
                    guards = [e for e in world.entities_at_radius(loc.pos, cfg.camp_radius) 
                              if e.identity.role == EntityRole.MOB and e.home_pos and e.home_pos.manhattan(loc.pos) <= cfg.camp_radius]
                    
                    if len(guards) < cfg.camp_max_guards // 2:
                        target_tier = region.difficulty + loc.reinforcement_level
                        mob = gen.spawn(world, tier=min(target_tier, 3), near_pos=loc.pos, difficulty_tier=region.difficulty)
                        world.add_entity(mob)
                    elif len(guards) >= cfg.camp_max_guards:
                        loc.reinforcement_level = min(loc.reinforcement_level + 1, 3)

    def _check_faction_raids(self, context: SystemContext, tick: int) -> None:
        """Spawn a raid targeting the town based on world_day."""
        cfg = context.config
        world = context.world
        gen = context.generator
        
        ticks_per_day = 100
        raid_interval_ticks = cfg.raid_interval_days * ticks_per_day
        if tick % raid_interval_ticks != 0 or tick == 0:
            return
            
        raid_size = cfg.raid_base_strength + (world.world_day // 10)
        
        angle = context.rng.next_float(Domain.CALAMITY, 0, tick) * 6.28
        import math
        dist = cfg.sanctuary_radius + 5
        spawn_pos = Vector2(
            int(cfg.town_center_x + math.cos(angle) * dist),
            int(cfg.town_center_y + math.sin(angle) * dist)
        )
        if not world.grid.is_walkable(spawn_pos):
            spawn_pos = gen._find_nearest_walkable_non_town(world, spawn_pos)
            
        from src.core.models.enums import AIState
        for i in range(raid_size):
            mob = gen.spawn(world, tier=max(1, min(world.world_day // 50, 3)), near_pos=spawn_pos, difficulty_tier=4)
            mob.mind.ai_state = AIState.RAID
            mob.home_pos = None  # Raid mobs don't return home
            world.add_entity(mob)
            
        if context.emit:
            context.emit("raid", f"A faction raid party of {raid_size} enemies approaches the town!", metadata={"size": raid_size})
        logger.warning("Tick %d: Faction Raid spawned at %s with %d enemies.", tick, spawn_pos, raid_size)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/gameplay/__init__.py
from .action_system import ActionSystem
from .combat_system import CombatSystem
from .economy_system import EconomySystem
from .enhancement_system import EnhancementSystem
from .quest_system import QuestSystem

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/gameplay/action_system.py
"""ActionSystem handles post-resolution state mutations and tactical maneuvers."""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

from src.core.models.enums import ActionType, AIState, Domain, SkillTarget, SkillType, DamageType, HeroClass
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.gameplay.classes import SKILL_DEFS
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.actions.base import ActionProposal
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class ActionSystem(System):
    """System for processing applied actions and tactical state changes."""

    def process_applied_actions(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        """Process state mutations (looting, items) for successfully applied actions."""
        world = context.world
        for proposal in applied:
            entity = world.entities.get(proposal.actor_id)
            if entity is None or not entity.combat.alive:
                continue

            # Apply state transition
            if hasattr(proposal, "new_ai_state") and proposal.new_ai_state is not None:
                entity.mind.ai_state = proposal.new_ai_state

            if proposal.verb == ActionType.USE_ITEM and proposal.target:
                self._handle_use_item(context, entity, proposal.target)
            elif proposal.verb == ActionType.LOOT and proposal.target:
                self._handle_looting(context, entity, proposal.target)
            elif proposal.verb == ActionType.HARVEST and proposal.target:
                self._handle_harvesting(context, entity, proposal.target)
            elif proposal.verb == ActionType.USE_SKILL and proposal.target:
                target_data = proposal.target if isinstance(proposal.target, tuple) else (proposal.target, None)
                self._handle_use_skill(context, entity, target_data[0], target_data[1])

        # Visualization and tactical state updates
        self._update_combat_visualization(context, applied)
        self._update_ai_derived_states(context, applied)

    def _handle_use_item(self, context: SystemContext, entity: Any, item_id: str) -> None:
        """Handle consumable usage including healing and act delay."""
        if entity.inventory and entity.inventory.remove_item(item_id):
            template = ITEM_REGISTRY.get(item_id)
            if template and template.heal_amount > 0:
                old_hp = entity.combat.hp
                entity.combat.hp = min(entity.combat.hp + template.heal_amount, entity.combat.max_hp)
                healed = entity.combat.hp - old_hp
                
                if context.emit:
                    context.emit("item", f"Entity {entity.id} used {item_id} → healed {healed}",
                              entity_ids=(entity.id,),
                              metadata={"item_id": item_id, "healed": healed})
            
            # Action delay penalty
            from src.core.gameplay.attributes import speed_delay
            entity.next_act_at += speed_delay(entity.combat.spd, "use_item", entity.combat.interaction_speed)

    def _handle_looting(self, context: SystemContext, entity: Any, pos: Any) -> None:
        """Handle ground looting and chest interactions."""
        from src.core.models import Vector2
        if not isinstance(pos, Vector2):
            return
            
        world = context.world
        items = world.pickup_items(pos)
        if items and entity.inventory:
            looted_items = []
            for iid in items:
                if not entity.inventory.add_item(iid):
                    world.drop_items(pos, [iid])
                else:
                    entity.inventory.auto_equip_best(iid)
                    looted_items.append(iid)
                    
            if looted_items and hasattr(world, "event_bus") and world.event_bus:
                from src.core.data.events import LootEvent
                from src.core.gameplay.items.item_registry import ITEM_REGISTRY
                for iid in looted_items:
                    tmpl = ITEM_REGISTRY.get(iid)
                    name = tmpl.name if tmpl else iid
                    world.event_bus.publish(LootEvent(
                        entity_id=entity.id,
                        item_id=iid,
                        item_name=name,
                        source="ground"
                    ))
        
        # Check for chests
        self._try_loot_chest(context, entity, pos)
        
        # Action delay
        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.stats.combat.spd, "loot", entity.stats.interaction_speed)

    def _try_loot_chest(self, context: SystemContext, entity: Any, pos: Any) -> None:
        """If there's an available treasure chest at pos, loot it."""
        from src.core.gameplay.items.items import CHEST_LOOT_TABLES
        world = context.world
        
        for chest in world.treasure_chests.values():
            if chest.pos == pos and chest.is_available:
                # Check guard
                if chest.guard_entity_id is not None:
                    guard = world.entities.get(chest.guard_entity_id)
                    if guard and guard.combat.alive:
                        continue
                
                # Generate loot
                loot_table = CHEST_LOOT_TABLES.get(chest.tier, [])
                loot_items = []
                for item_id, chance, min_c, max_c in loot_table:
                    roll = context.rng.next_float(Domain.LOOT, entity.id, world.tick + chest.chest_id)
                    if roll < chance:
                        count = context.rng.next_int(Domain.LOOT, entity.id, world.tick + chest.chest_id + 10, min_c, max_c)
                        loot_items.extend([item_id] * count)
                
                if loot_items:
                    world.drop_items(pos, loot_items)
                    
                chest.loot(world.tick, respawn_ticks=150 + chest.identity.tier * 50)
                logger.info("Tick %d: Entity %d looted chest %d", world.tick, entity.id, chest.chest_id)
                break

    def _handle_harvesting(self, context: SystemContext, entity: Any, pos: Any) -> None:
        """Handle resource harvesting."""
        world = context.world
        node = world.resource_at(pos)
        if node and node.is_available and entity.inventory:
            item_id = node.harvest()
            if item_id and entity.inventory.add_item(item_id):
                entity.progression.stamina = max(0, entity.progression.stamina - 2)
                if context.emit:
                    context.emit("harvest", f"Entity {entity.id} harvested {item_id}",
                              entity_ids=(entity.id,),
                              metadata={"item_id": item_id})
        
        # Action delay
        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.combat.spd, "harvest", entity.combat.interaction_speed)

    def _handle_use_skill(self, context: SystemContext, entity: Any, skill_id: str, target_id: int | None = None) -> None:
        """Execute a combat or utility skill, applying effects to target(s)."""
        sdef = SKILL_DEFS.get(skill_id)
        if not sdef or sdef.skill_type != SkillType.ACTIVE:
            return

        instance = next((si for si in entity.progression.skills if si.skill_id == skill_id), None)
        if not instance:
            # print(f"DEBUG_ACTION_SKILL: Entity {entity.id} does not have skill {skill_id}")
            return
            
        if not instance.is_ready():
            # print(f"DEBUG_ACTION_SKILL: Skill {skill_id} on CD for Entity {entity.id} (CD={instance.cooldown_remaining})")
            return

        cost = instance.effective_stamina_cost(sdef.stamina_cost)
        if entity.progression.stamina < cost:
            # print(f"DEBUG_ACTION_SKILL: No stamina for {skill_id} (Need {cost}, Has {entity.progression.stamina})")
            return
            
        # Resolve targets
        targets = self._resolve_skill_targets(context, entity, sdef, target_id)

        # --- Metrics: Skill Event ---
        from src.core.gameplay.faction import Faction
        from src.utils.metrics import SIM_SKILL_EVENTS
        SIM_SKILL_EVENTS.labels(
            attacker_faction=Faction(entity.identity.faction).name.lower(),
            skill_name=sdef.name.lower().replace(" ", "_")
        ).inc()

        # Consume stamina
        if entity.progression.stamina < cost:
            return
        entity.progression.stamina -= cost

        # Resolve targets
        targets = self._resolve_skill_targets(context, entity, sdef, target_id)
        
        # Apply effects
        hit_count = 0
        for target in targets:
            if self._apply_skill_effect(context, entity, target, sdef, instance):
                hit_count += 1

        # Trigger cooldown
        instance.use(sdef.cooldown)
        instance.times_used += 1
        # Mastery increase (small chance/amount per use)
        instance.mastery = min(100.0, instance.mastery + 0.1)

        if context.emit:
            context.emit("skill", f"Entity {entity.id} used {sdef.name} → hit {hit_count} targets",
                      entity_ids=(entity.id,),
                      metadata={
                          "skill_id": skill_id,
                          "skill_name": sdef.name,
                          "hits": hit_count,
                          "verb": "USE_SKILL",
                          "aoe": sdef.radius > 0
                      })

        # Action delay
        from src.core.gameplay.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.combat.spd, "use_skill", 1.0)

    def _resolve_skill_targets(self, context: SystemContext, entity: Any, sdef: Any, primary_target_id: int | None = None) -> list[Any]:
        """Find all entities affected by the skill based on its target type and radius."""
        from src.core.gameplay.faction import Faction
        world = context.world
        reg = context.faction_reg  # FactionRegistry is passed as 'faction_reg' in SystemContext
        targets = []

        if sdef.target == SkillTarget.SELF:
            return [entity]

        # For targeted skills, find the primary target first
        if not primary_target_id:
            primary_target_id = entity.combat_target_id
        primary_target = world.entities.get(primary_target_id) if primary_target_id else None

        # Area of Effect logic
        radius = sdef.radius or 0
        is_melee_aoe = (sdef.range or 1) <= 1
        
        # Ranged check: must have a target in range for offensive targeted skills
        if sdef.target in (SkillTarget.SINGLE_ENEMY, SkillTarget.AREA_ENEMIES):
            if not is_melee_aoe and (not primary_target or not primary_target.combat.alive):
                # Fallback: if it's a ranged AoE but target is gone/invalid, center on actor's current target or actor
                pass
            if primary_target and primary_target.combat.alive:
                dist = entity.spatial.pos.manhattan(primary_target.spatial.pos)
                if dist > (sdef.range or 1):
                    return []

        if radius > 0:
            # For melee-range AoE skills like Whirlwind, center on caster.
            # Ranged AoE (radius > 0 and range > 1) centers on the primary target.
            center = entity.spatial.pos if is_melee_aoe else (primary_target.spatial.pos if primary_target else entity.spatial.pos)
            potential = world.spatial_index.query_radius(center, radius)
            # LOGGING: Find out why AoE results in 0 hits
            logger.debug("Skill %s AoE at %s radius %d -> %d potentials", sdef.skill_id, center, radius, len(potential))
            
            # Use local targets list to avoid overriding external variables
            aoe_targets = []
            for oid in potential:
                other = world.entities.get(oid)
                if not other or not other.combat.alive:
                    continue
                
                # Precise distance check (since spatial hash is bucket-based)
                dist = other.spatial.pos.manhattan(center)
                if dist > radius:
                    continue

                # Hostility/Ally check
                is_hostile = reg.is_hostile(entity.identity.faction, other.identity.faction)
                
                added = False
                if sdef.target == SkillTarget.AREA_ENEMIES and is_hostile:
                    targets.append(other)
                    added = True
                elif sdef.target == SkillTarget.AREA_ALLIES and not is_hostile:
                    targets.append(other)
                    added = True
                elif sdef.target == SkillTarget.AREA_ALLIES and other.id == entity.id:
                    targets.append(other)
                    added = True
                
                if added:
                    logger.debug("  Hit: Entity %d (%s) at dist %d", other.id, other.kind, dist)
                    aoe_targets.append(other)
            
            # If an AoE hit anything, those (and only those) are our targets
            if aoe_targets:
                return aoe_targets
        elif primary_target:
            targets.append(primary_target)

        return targets

    def _apply_skill_effect(self, context: SystemContext, attacker: Any, defender: Any, sdef: Any, instance: Any) -> bool:
        """Apply the specific effect (damage, heal, buff) of a skill to a single target."""
        if sdef.skill_type != SkillType.ACTIVE:
            return False

        # Calculate base power (modified by mastery)
        power_mult = instance.effective_power(sdef.power)
        
        # Damage logic (Physical vs Magical)
        from src.actions.damage import get_damage_calculator
        calc = get_damage_calculator(sdef.damage_type)
        ctx = calc.resolve(attacker, defender)
        
        # Base damage formula: (Atk * Mult - Def/2) * Power
        raw_dmg = max(1, int(ctx.atk_power * ctx.atk_mult - ctx.def_power * ctx.def_mult // 2))
        final_dmg = int(raw_dmg * power_mult)

        # Falloff based on distance if AoE
        dist_from_center = 0
        is_aoe = sdef.radius > 0
        if is_aoe and attacker.combat_target_id != defender.id:
            center_ent = context.world.entities.get(attacker.combat_target_id) if attacker.combat_target_id else None
            center_pos = center_ent.spatial.pos if center_ent else attacker.spatial.pos
            dist_from_center = defender.spatial.pos.manhattan(center_pos)
            final_dmg = int(final_dmg * (1.0 - dist_from_center * sdef.aoe_falloff))

        actual_dmg = max(1, final_dmg)
        
        # --- Status Effect Combos ---
        for eff in list(defender.combat.effects):
            from src.core.gameplay.effects import EffectType
            # FROZEN + PHYSICAL -> SHATTER
            if eff.effect_type == EffectType.FROZEN and sdef.damage_type == DamageType.PHYSICAL:
                actual_dmg = int(actual_dmg * 1.5)
                eff.remaining_ticks = 0 # Remove Frozen
                if context.emit:
                    context.emit("combat", f"COMBO: SHATTER on {defender.id}!", (attacker.id, defender.id))
            
            # WET + MAGICAL (Lightning) -> OVERLOAD
            # Check sdef.name or add a specific element to SkillDef
            # For now, let's assume all MAGICAL vs WET triggers a small bonus
            elif eff.effect_type == EffectType.WET and sdef.damage_type == DamageType.MAGICAL:
                actual_dmg = int(actual_dmg * 1.3)
                if context.emit:
                    context.emit("combat", f"COMBO: OVERLOAD on {defender.id}!", (attacker.id, defender.id))

        # Apply damage
        defender.combat.hp -= actual_dmg
        
        # Low HP trigger
        if defender.combat.alive and defender.combat.hp_ratio < 0.2:
            last_surv = defender.mind.memory.get("last_survival_tick", -100)
            tick = context.world.tick if hasattr(context.world, "tick") else 0
            if tick - last_surv >= 20:  # At most once per 20 ticks
                defender.mind.memory_log.append({
                    "tick": tick,
                    "type": "SURVIVAL",
                    "desc": f"Survived near-death against {attacker.kind}",
                    "impact": -3.0,
                })
                defender.mind.memory["last_survival_tick"] = tick

        # --- Threat generation ---
        from src.core.gameplay.classes import HeroClass
        threat = final_dmg * context.config.threat_damage_mult
        if attacker.progression.hero_class in (HeroClass.WARRIOR, HeroClass.CHAMPION):
            threat *= context.config.threat_tank_class_mult
        defender.mind.threat_table[attacker.id] = defender.mind.threat_table.get(attacker.id, 0.0) + threat

        if context.emit:
            context.emit("skill", f"Skill {sdef.name} hit {defender.id} for {final_dmg} damage",
                      entity_ids=(attacker.id, defender.id),
                      metadata={
                          "skill_id": sdef.skill_id,
                          "skill_name": sdef.name,
                          "damage": final_dmg,
                          "aoe": is_aoe,
                          "dist_from_center": dist_from_center,
                          "verb": "USE_SKILL"
                      })

        # XP/Fame awards and Narrative Memory on kill
        if not defender.combat.alive:
            attacker.progression.xp += 10 # Simplified
            attacker.progression.gold += defender.progression.gold
            defender.progression.gold = 0
            
            # Milestone 6: Narrative Memory (Glory/Trauma)
            tick = context.world.tick if hasattr(context.world, "tick") else 0
            
            # Glory for Attacker
            attacker.mind.memory_log.append({
                "tick": tick,
                "type": "GLORY",
                "desc": f"Slayed {defender.kind} (ID:{defender.id})",
                "impact": 5.0 if not defender.identity.is_world_boss else 50.0
            })
            attacker.mind.emotional_state["bravery"] = min(1.0, attacker.mind.emotional_state.get("bravery", 0.5) + 0.05)
            
            if attacker.identity.hero_class != 0:
                attacker.progression.fame += 50
                attacker.identity.reputation += 20.0
                
                # Milestone 6: Hero Renown Broadcast
                if hasattr(context.world, "event_bus") and context.world.event_bus:
                    from src.core.data.events import RenownEvent
                    context.world.event_bus.publish(RenownEvent(
                        entity_id=attacker.id,
                        glory_type="boss_kill",
                        description=f"Slayed the legendary {defender.kind}",
                        renown_gain=20.0
                    ))
                
                if context.emit:
                    context.emit("renown", f"HERO {attacker.id} HAS ACHIEVED LEGENDARY FAME BY SLAYING {defender.kind}!",
                                entity_ids=(attacker.id,),
                                metadata={"type": "boss_kill", "renown_gain": 20.0})
                
            # Trauma for nearby Allies of Defender
            for eid, ent in context.world.entities.items():
                if ent.combat.alive and ent.identity.faction == defender.identity.faction and eid != defender.id:
                    dist = abs(ent.spatial.pos.x - defender.spatial.pos.x) + abs(ent.spatial.pos.y - defender.spatial.pos.y)
                    if dist <= 5: # Vision-ish range
                        ent.mind.memory_log.append({
                            "tick": tick,
                            "type": "TRAUMA",
                            "desc": f"Witnessed death of ally {defender.kind}",
                            "impact": -10.0
                        })
                        ent.mind.emotional_state["bravery"] = max(0.0, ent.mind.emotional_state.get("bravery", 0.5) - 0.1)

            # Milestone 6: Regional Suppression tracking
            reg_id = defender.current_region_id
            if reg_id:
                key = (int(defender.identity.faction), reg_id)
                deaths = context.world.faction_deaths_per_region.get(key, 0)
                context.world.faction_deaths_per_region[key] = deaths + 1

                # Milestone 7: Region Control shifts
                control = context.world.region_control.get(reg_id, 0.0)
                shift = 2.0 # default monster kill
                if defender.identity.faction == Faction.HERO_GUILD:
                    shift = -10.0 # hero death is a big blow
                elif defender.identity.is_world_boss:
                    shift = 50.0 # boss kill is a massive victory
                
                context.world.region_control[reg_id] = max(-100.0, min(100.0, control + shift))
        
        return True

    def handle_tactical_maneuvers(self, context: SystemContext, applied: list[ActionProposal], pre_positions: dict) -> None:
        """Process opportunity attacks and chase closing."""
        self._process_opportunity_attacks(context, applied, pre_positions)
        self._process_chase_closing(context)

    def _process_opportunity_attacks(self, context: SystemContext, applied: list[ActionProposal], pre_positions: dict) -> None:
        """Detect and execute opportunity attacks on fleeing enemies."""
        cfg = context.config
        world = context.world
        reg = context.faction_reg
        mult = cfg.opportunity_attack_damage_mult
        
        for proposal in applied:
            if proposal.verb != ActionType.MOVE:
                continue
            mover = world.entities.get(proposal.actor_id)
            if not mover or not mover.combat.alive:
                continue
            old_pos = pre_positions.get(proposal.actor_id)
            if not old_pos:
                continue
            
            # Find hostiles adjacent to OLD pos
            for eid in sorted(world.entities.keys()):
                ent = world.entities[eid]
                if eid == mover.id or not ent.combat.alive or ent.kind == "generator":
                    continue
                if not reg.is_hostile(mover.identity.faction, ent.identity.faction):
                    continue
                
                # Check adjacency to old pos
                old_dist = abs(ent.spatial.pos.x - old_pos[0]) + abs(ent.spatial.pos.y - old_pos[1])
                if old_dist != 1:
                    continue
                    
                # Did they move AWAY?
                new_dist = mover.spatial.pos.manhattan(ent.spatial.pos)
                if new_dist <= old_dist:
                    continue
                # OA Damage
                atk = ent.combat.atk
                df = mover.combat.def_
                raw = max(1, int(atk * mult) - df // 2)
                mover.combat.hp -= raw
                
                if context.emit:
                    context.emit("tactical", f"Entity {ent.id} Opportunity Attack → {mover.id} for {raw} dmg",
                              entity_ids=(ent.id, mover.id),
                              metadata={"verb": "OPPORTUNITY_ATTACK", "damage": raw})

    def _process_chase_closing(self, context: SystemContext) -> None:
        """SPD-based chase closing: faster hunters gain a bonus tile."""
        cfg = context.config
        world = context.world
        
        # Process in deterministic ID order
        for entity in sorted(world.entities.values(), key=lambda e: e.id):
            if not entity.combat.alive or entity.mind.ai_state != AIState.HUNT or entity.chase_ticks < 2:
                continue
            
            # Find current target
            target = self._find_nearest_hostile(context, entity)
            if not target:
                continue
                
            hunter_spd = entity.combat.spd
            target_spd = target.combat.spd
            if hunter_spd <= target_spd:
                continue
                
            interval = max(1, math.ceil(cfg.chase_spd_closing_base * target_spd / hunter_spd))
            if entity.chase_ticks % interval != 0:
                continue
                
            # Bonus move
            from src.ai.perception import Perception
            dir = Perception.direction_toward(entity.spatial.pos, target.spatial.pos)
            new_pos = entity.spatial.pos + dir
            if world.grid.is_walkable(new_pos):
                world.move_entity(entity.id, new_pos)
                if context.emit:
                    context.emit("movement", f"Entity {entity.id} sprints closer to {target.id}",
                              entity_ids=(entity.id,),
                              metadata={"verb": "CHASE_SPRINT", "actor_id": entity.id})

    def _update_combat_visualization(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        """Update entity combat targets for UI/visualization from recent actions."""
        world = context.world
        from src.core.models.enums import ActionType
        acted: set[int] = set()
        for proposal in applied:
            actor = world.entities.get(proposal.actor_id)
            if not actor:
                continue
            acted.add(actor.id)

            if proposal.verb == ActionType.ATTACK:
                actor.combat_target_id = proposal.target
            elif proposal.verb == ActionType.USE_SKILL:
                # Skill target_id is often a tuple (skill_id, target_id)
                if isinstance(proposal.target, tuple) and len(proposal.target) == 2:
                    actor.combat_target_id = proposal.target[1]
                elif isinstance(proposal.target, int):
                    actor.combat_target_id = proposal.target
            elif proposal.verb in (ActionType.MOVE, ActionType.USE_ITEM, ActionType.HARVEST, ActionType.LOOT, ActionType.REST):
                # These actions don't change combat target unless state changes.
                # If they already had a target, keep it!
                pass
            else:
                actor.combat_target_id = None
        
        # Clear target for entities that are no longer in combat or hunt state.
        for entity in world.entities.values():
            if entity.id in acted:
                continue
            # Only clear target if definitely NOT in a combat state.
            if entity.mind.ai_state not in (AIState.COMBAT, AIState.HUNT, AIState.FLEE):
                entity.combat_target_id = None

    def _update_ai_derived_states(self, context: SystemContext, applied: list[ActionProposal]) -> None:
        """Update secondary AI metrics like chase_ticks and idle_ticks."""
        world = context.world
        for proposal in applied:
            entity = world.entities.get(proposal.actor_id)
            if not entity or not entity.combat.alive: continue
            
            # State update
            if proposal.new_ai_state is not None:
                entity.mind.ai_state = AIState(proposal.new_ai_state)
            if proposal.reason:
                entity.last_reason = proposal.reason
            
            # Derived counters
            if entity.mind.ai_state == AIState.HUNT:
                entity.chase_ticks += 1
            else:
                entity.chase_ticks = 0
                
            if entity.mind.ai_state == AIState.IDLE:
                entity.consecutive_idle_ticks += 1
            else:
                entity.consecutive_idle_ticks = 0

    def _find_nearest_hostile(self, context: SystemContext, entity: Any) -> Any:
        """Find the nearest visible hostile entity."""
        world = context.world
        reg = context.faction_reg
        best_dist = 999
        best_target = None
        potential = sorted(world.spatial_index.query_radius(entity.spatial.pos, entity.combat.vision_range))
        for oid in potential:
            other = world.entities.get(oid)
            if not other or not other.combat.alive or other.id == entity.id:
                continue
            if not reg.is_hostile(entity.identity.faction, other.identity.faction):
                continue
            d = entity.spatial.pos.manhattan(other.spatial.pos)
            if d < best_dist:
                best_dist = d
                best_target = other
        return best_target

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/gameplay/combat_system.py
"""CombatSystem handles status effects, engagement, and threat decay."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class CombatSystem(System):
    """System for managing combat-related logic and status effects."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute combat sub-phases."""
        self._tick_effects(context)
        self._tick_engagement(context)
        self._tick_threat_decay(context)

    def _tick_effects(self, context: SystemContext) -> None:
        """Tick down status effect durations and apply per-tick HP changes."""
        for entity in context.world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
                
            combat = entity.combat
            if not combat or not combat.effects:
                continue
                
            # Use a list copy to allow removal during iteration if needed 
            # (though here we filter at the end)
            for eff in combat.effects:
                # Apply hp_per_tick (positive = regen, negative = DoT)
                if eff.hp_per_tick != 0 and not eff.expired:
                    combat.hp = max(0, min(
                        combat.hp + eff.hp_per_tick,
                        entity.stats.combat.max_hp,
                    ))
                eff.tick()
                
            combat.effects = [e for e in combat.effects if not e.expired]

    def _tick_engagement(self, context: SystemContext) -> None:
        """Track how many ticks each entity has been adjacent to a hostile."""
        reg = context.faction_reg
        spatial = context.world.spatial_index
        entities = context.world.entities
        
        for entity in entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
                
            combat = entity.combat
            if not combat:
                continue
                
            adjacent_hostile = False
            for oid in spatial.query_radius(entity.spatial.pos, 1):
                if oid == entity.id:
                    continue
                other = entities.get(oid)
                if other is None or not other.combat.alive or other.kind == "generator":
                    continue
                    
                # Manhattan distance check and hostility check
                if (abs(entity.spatial.pos.x - other.spatial.pos.x) + abs(entity.spatial.pos.y - other.spatial.pos.y) <= 1 
                    and reg.is_hostile(entity.identity.faction, other.identity.faction)):
                    adjacent_hostile = True
                    break
                    
            if adjacent_hostile:
                combat.engaged_ticks = min(combat.engaged_ticks + 1, 10)
            else:
                combat.engaged_ticks = 0

    def _tick_threat_decay(self, context: SystemContext) -> None:
        """Decay threat values over time."""
        decay = 1.0 - context.config.threat_decay_rate
        entities = context.world.entities
        
        for entity in entities.values():
            to_remove: list[int] = []
            for attacker_id, threat in entity.mind.threat_table.items():
                attacker = entities.get(attacker_id)
                if attacker is None or not attacker.combat.alive:
                    to_remove.append(attacker_id)
                    continue
                    
                new_threat = threat * decay
                if new_threat < 1.0:
                    to_remove.append(attacker_id)
                else:
                    entity.mind.threat_table[attacker_id] = new_threat
                    
            for aid in to_remove:
                del entity.mind.threat_table[aid]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/gameplay/economy_system.py
"""EconomySystem handles town healing, hero respawns, and global state."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.models.enums import AIState
from src.core.gameplay.faction import Faction
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class EconomySystem(System):
    """System for managing simulation lifecycle, town services, and rewards."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute economy phases."""
        self._heal_home_entities(context, tick)
        self._process_hero_replacements(context, tick)
        self._check_endgame_conditions(context, tick)

    def _heal_home_entities(self, context: SystemContext, tick: int) -> None:
        """Heal entities on home territory and apply town aura damage."""
        cfg = context.config
        world = context.world
        reg = context.faction_reg
        
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue

            on_town = world.grid.is_town(entity.spatial.pos)
            on_camp = world.grid.is_camp(entity.spatial.pos)

            # Town aura: hostile entities in town take damage
            if on_town and reg.is_hostile(entity.identity.faction, Faction.HERO_GUILD):
                entity.stats.combat.hp -= cfg.town_aura_damage
                continue

            # Healing in allied territory
            if entity.stats.combat.hp < entity.stats.combat.max_hp:
                if (entity.identity.faction == Faction.HERO_GUILD and on_town):
                    heal = cfg.hero_heal_per_tick if entity.mind.ai_state == AIState.RESTING_IN_TOWN else cfg.town_passive_heal
                    entity.stats.combat.hp = min(entity.stats.combat.hp + heal, entity.stats.combat.max_hp)
                elif (entity.identity.faction == Faction.GOBLIN_HORDE and on_camp and entity.mind.ai_state == AIState.GUARD_CAMP):
                    entity.stats.combat.hp = min(entity.stats.combat.hp + 1, entity.stats.combat.max_hp)

    def _process_hero_replacements(self, context: SystemContext, tick: int) -> None:
        """Handle hero respawn/replacement logic."""
        cfg = context.config
        world = context.world
        
        # Check for dead heroes to replace
        for eid, entity in list(world.entities.items()):
            if not entity.combat.alive and entity.identity.role == Faction.HERO_GUILD:
                # Logic for hero replacement (e.g., adding to a queue)
                pass

    def _check_endgame_conditions(self, context: SystemContext, tick: int) -> None:
        """Check for terminal world states (e.g., town destruction)."""
        # Future: If town is destroyed, signal simulation stop
        pass

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/gameplay/enhancement_system.py
"""EnhancementSystem handles gear upgrades (+1 to +15).

Enhancements cost Gold and specific Materials. Each level increases the item's power
and adds a suffix (e.g., "Steel Sword +1").

Tiers:
+1 to +5: Basic (Iron/Steel)
+6 to +10: Rare (Mithril/Adamant)
+11 to +15: Legendary (Orichalcum/Godsteel)

Success Rate:
+1 to +3: 100%
+4 to +7: 80% (failure = no change)
+8 to +12: 50% (failure = drop level -1)
+13 to +15: 35% (failure = drop level -1)
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.core.models.enums import Domain, ItemType

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)

class EnhancementSystem:
    """Business logic for the Blacksmith's enhancement service."""
    
    @staticmethod
    def can_enhance(entity: Entity, item_id: str) -> tuple[bool, str]:
        """Check if the entity can afford and has the level for the next upgrade."""
        # This is a simplified check. In a real system, we'd lookup item current level.
        # For our simulation, we'll store (+N) in the item instance data or just use a naming convention.
        # However, our ITEM_REGISTRY uses static IDs. We need a way to track INSTANCE level.
        # If the simulation doesn't support item instances with metadata, we might need to 
        # swap the item ID for a new one (e.g. "sword_1" -> "sword_2").
        return True, "Ready"

    @staticmethod
    def get_cost(current_level: int) -> int:
        """Gold cost for the next level."""
        return 50 * (current_level + 1) ** 2

    @staticmethod
    def get_material_cost(current_level: int) -> dict[str, int]:
        """Material requirements for the next level."""
        if current_level < 5:
            return {"iron_ore": 2}
        elif current_level < 10:
            return {"mithril_ore": 1}
        else:
            return {"godsteel_ore": 1}

    @staticmethod
    def perform_upgrade(entity: Entity, item_id: str, rng: DeterministicRNG, tick: int) -> str | None:
        """Attempt to upgrade the item. Returns new item_id if successful, or None."""
        # For this simulation, we'll assume item IDs follow the pattern "base_id[+N]"
        # or we just simulate the stat boost.
        # Given the current system, we'll implement a naming convention: "iron_sword" -> "iron_sword_+1"
        
        parts = item_id.split("_+")
        base_id = parts[0]
        current_lv = int(parts[1]) if len(parts) > 1 else 0
        
        if current_lv >= 15:
            return None # Max level
            
        cost = EnhancementSystem.get_cost(current_lv)
        if entity.stats.progression.gold < cost:
            return None
            
        # Success check
        rate = 1.0
        if current_lv >= 12: rate = 0.35
        elif current_lv >= 7: rate = 0.50
        elif current_lv >= 3: rate = 0.80
        
        entity.stats.progression.gold -= cost
        
        if rng.next_bool(Domain.ITEM, entity.id, tick, rate):
            new_lv = current_lv + 1
            new_id = f"{base_id}_+{new_lv}"
            logger.info(f"Tick {tick}: Entity {entity.id} enhanced {item_id} to SUCCESS (+{new_lv})")
            return new_id
        else:
            # Failure
            if current_lv >= 7:
                new_lv = max(0, current_lv - 1)
                new_id = f"{base_id}_+{new_lv}" if new_lv > 0 else base_id
                logger.info(f"Tick {tick}: Entity {entity.id} FAIL enhanced {item_id} -> Dropped to +{new_lv}")
                return new_id
            logger.info(f"Tick {tick}: Entity {entity.id} FAIL enhanced {item_id} -> No change")
            return item_id

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/gameplay/quest_system.py
"""QuestSystem handles quest progression and rewards."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class QuestSystem(System):
    """System for managing entity quests and rewards."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Check quest completion and prune finished quests."""
        from src.core.gameplay.quests import QuestType
        
        world = context.world
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator" or not entity.quests:
                continue
                
            for q in entity.quests:
                if q.completed:
                    continue
                    
                # EXPLORE: complete when hero is within 2 tiles of target
                if q.quest_type == QuestType.EXPLORE and q.target_pos is not None:
                    if entity.spatial.pos.manhattan(q.target_pos) <= 2:
                        q.advance()
                        from src.utils.metrics import SIM_QUEST_STATUS_TOTAL
                        SIM_QUEST_STATUS_TOTAL.labels(type="explore", status="completed").inc()
                        
                        # Use Aspects for rewards
                        prog = entity.progression
                        if prog:
                            prog.gold += q.gold_reward
                            prog.xp += q.xp_reward
                            entity.identity.reputation += 5.0
                            
                        logger.info(
                            "Tick %d: Entity %d completed quest '%s' → +%d gold, +%d XP",
                            tick, entity.id, q.title, q.gold_reward, q.xp_reward,
                        )
                        if hasattr(world, "event_bus") and world.event_bus:
                            from src.core.data.events import QuestEvent
                            world.event_bus.publish(QuestEvent(
                                entity_id=entity.id,
                                quest_title=q.title,
                                quest_type=q.quest_type.name,
                                status="completed",
                                gold_reward=q.progression.gold_reward,
                                xp_reward=q.progression.xp_reward
                            ))
            
            # Prune completed quests older than 50 ticks (keep for display briefly)
            entity.quests = [q for q in entity.quests if not q.completed or tick % 50 != 0]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/infrastructure/__init__.py


#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/infrastructure/base.py
"""Base classes for simulation systems and their execution context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG


@dataclass(frozen=True)
class SystemContext:
    """Narrow interface for systems to access world state and infrastructure."""
    config: SimulationConfig
    world: WorldState
    rng: DeterministicRNG
    generator: Any
    faction_reg: Any
    emit: Callable[[str, str, tuple[int, ...], dict | None], None]


class System:
    """Base class for all decoupled simulation systems."""
    
    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self.config = config
        self.rng = rng

    def on_init(self, context: SystemContext) -> None:
        """Called when the system is first initialized."""
        pass

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Called every N ticks based on registration rate."""
        pass

    def on_shutdown(self, context: SystemContext) -> None:
        """Called when the simulation ends."""
        pass

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/infrastructure/event_system.py
import logging
from typing import Callable, Type, Dict, List, Any

from src.core.data.events import (
    DomainEvent, CombatEvent, DeathEvent, LootEvent, LevelUpEvent, TradeEvent, CraftEvent, QuestEvent
)
from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)
EventHandler = Callable[[DomainEvent], None]

class EventBus:
    """Simple synchronous pub/sub event bus for domain events."""
    def __init__(self):
        self._subscribers: Dict[Type[DomainEvent], List[EventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []

    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        self._global_subscribers.append(handler)

    def publish(self, event: DomainEvent) -> None:
        evt_type = type(event)
        if evt_type in self._subscribers:
            for handler in self._subscribers[evt_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error("EventBus handler error for %s: %s", evt_type.__name__, e, exc_info=True)
        
        for handler in self._global_subscribers:
            try:
                handler(event)
            except Exception as e:
                logger.error("EventBus global handler error: %s", e, exc_info=True)


class TelemetryBridge:
    """Translates strongly typed DomainEvents into the legacy REST SimEvent ring buffer."""
    def __init__(self, world: WorldState, emit_func: Callable):
        self._world = world
        self._emit = emit_func

    def attach(self, bus: EventBus) -> None:
        bus.subscribe(CombatEvent, self.handle_combat)
        bus.subscribe(DeathEvent, self.handle_death)
        bus.subscribe(LootEvent, self.handle_loot)
        bus.subscribe(LevelUpEvent, self.handle_level_up)
        bus.subscribe(TradeEvent, self.handle_trade)
        bus.subscribe(CraftEvent, self.handle_craft)
        bus.subscribe(QuestEvent, self.handle_quest)

    def _get_name(self, entity_id: int) -> str:
        ent = self._world.entities.get(entity_id)
        if ent:
            return ent.identity.display_name or f"#{entity_id}"
        return f"#{entity_id}"

    def handle_combat(self, event: CombatEvent) -> None:
        att_name = self._get_name(event.attacker_id)
        dfd_name = self._get_name(event.defender_id)
        
        if event.is_evasion:
            msg = f"{att_name}'s attack was EVADED by {dfd_name}"
        else:
            crit_str = " (CRIT!)" if event.is_crit else ""
            msg = f"{att_name} hit {dfd_name} for {event.damage} damage{crit_str}"

        self._emit("combat", msg, entity_ids=(event.attacker_id, event.defender_id), metadata=event.__dict__)

    def handle_death(self, event: DeathEvent) -> None:
        name = self._get_name(event.entity_id)
        if event.is_permadeath:
            msg = f"{name} DIED PERMANENTLY at level {event.level_at_death}."
        else:
            msg = f"{name} died at level {event.level_at_death}."
        
        # killer_id can be None
        e_ids = [event.entity_id]
        if event.killer_id is not None:
            e_ids.append(event.killer_id)
            
        self._emit("death", msg, entity_ids=tuple(e_ids), metadata=event.__dict__)

    def handle_loot(self, event: LootEvent) -> None:
        name = self._get_name(event.entity_id)
        msg = f"{name} looted {event.item_name} from {event.source}"
        self._emit("loot", msg, entity_ids=(event.entity_id,), metadata=event.__dict__)

    def handle_level_up(self, event: LevelUpEvent) -> None:
        name = self._get_name(event.entity_id)
        msg = f"{name} leveled up! ({event.old_level} -> {event.new_level})"
        self._emit("level_up", msg, entity_ids=(event.entity_id,), metadata=event.__dict__)

    def handle_trade(self, event: TradeEvent) -> None:
        name = self._get_name(event.entity_id)
        action_word = "bought" if event.action == "buy" else "sold"
        cost_word = "for" if event.action == "buy" else "earning"
        msg = f"{name} {action_word} {event.item_id} {cost_word} {event.gold_change}g"
        self._emit("trade", msg, entity_ids=(event.entity_id,), metadata=event.__dict__)

    def handle_craft(self, event: CraftEvent) -> None:
        name = self._get_name(event.entity_id)
        msg = f"{name} crafted {event.output_item} (Recipe: {event.recipe_id})"
        self._emit("craft", msg, entity_ids=(event.entity_id,), metadata=event.__dict__)

    def handle_quest(self, event: QuestEvent) -> None:
        name = self._get_name(event.entity_id)
        msg = f"{name} {event.status} quest '{event.quest_title}'"
        if event.status == "completed":
            msg += f" (+{event.gold_reward}g, +{event.xp_reward}xp)"
        self._emit("quest", msg, entity_ids=(event.entity_id,), metadata=event.__dict__)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/infrastructure/history_system.py
"""HistorySystem records major world events into the narrative log."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class HistorySystem(System):
    """System that records major occurrences for world-wide narrative persistence."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Initialize subscriptions if not already done."""
        self._world = context.world
        if not context.world._history_subscribed:
            if hasattr(context.world, "event_bus") and context.world.event_bus:
                context.world.event_bus.subscribe_all(self._on_any_event)
                context.world._history_subscribed = True

    def _on_any_event(self, event: DomainEvent) -> None:
        """Handle any domain event and record if relevant."""
        from src.core.data.events import RenownEvent, WarEvent, ConquestEvent, QuestEvent
        
        # We only record high-level narrative events in the history
        if isinstance(event, (RenownEvent, WarEvent, ConquestEvent)):
            desc = getattr(event, "description", "")
            if isinstance(event, WarEvent):
                status = "DECLARED" if event.is_declared else "ENDED"
                desc = f"War {status} by Faction {event.faction_id} (Aggression: {event.aggression:.1f})"
            elif isinstance(event, ConquestEvent):
                type_str = "LIBERATED" if event.is_liberation else "CONQUERED"
                desc = f"Region {event.region_name} was {type_str}"

            self._record(desc, type(event).__name__, event.__dict__)

    def _record(self, description: str, event_type: str, metadata: dict) -> None:
        """Internal helper to append to world history."""
        if not hasattr(self, "_world"):
            return
            
        entry = {
            "tick": self._world.tick,
            "type": event_type,
            "desc": description,
            "meta": metadata
        }
        self._world.history.append(entry)
        
        logger.info("World History [%s]: %s", event_type, description)

    def record_event(self, context: SystemContext, tick: int, event_type: str, description: str, metadata: dict | None = None) -> None:
        """Manual injection for world events."""
        entry = {
            "tick": tick,
            "type": event_type,
            "desc": description,
            "meta": metadata or {}
        }
        context.world.history.append(entry)
        
        if context.emit:
            context.emit("history", f"WORLD RECORD: {description}",
                        metadata=entry)
        
        logger.info("World History [%s]: %s", event_type, description)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/infrastructure/manager.py
"""SystemManager for coordinates multiple simulation systems."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from src.systems.infrastructure.base import SystemContext

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG
    from src.systems.infrastructure.base import System

logger = logging.getLogger(__name__)


class SystemManager:
    """Orchestrates the execution of decoupled simulation systems."""
    
    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._rng = rng
        self._systems: list[tuple[System, int]] = []
        self._context: SystemContext | None = None

    def register(self, system: System, rate: int) -> None:
        """Register a system to run every 'rate' ticks."""
        logger.debug("Registering system %s at rate %d", system.__class__.__name__, rate)
        self._systems.append((system, rate))

    def init_all(self, world: WorldState, generator: Any, faction_reg: Any, emit: Callable) -> None:
        """Initialize all registered systems within a WorldContext."""
        self._context = SystemContext(
            config=self._config, 
            world=world, 
            rng=self._rng,
            generator=generator,
            faction_reg=faction_reg,
            emit=emit
        )
        for system, _ in self._systems:
            system.on_init(self._context)

    def tick(self, world: WorldState, tick: int) -> None:
        """Execute all systems that are due for a tick."""
        if self._context is None:
             # Lazy init if not already done
             self.init_all(world, None, None, lambda *a, **k: None)

        for system, rate in self._systems:
            if tick % rate == 0:
                system.on_tick(self._context, tick)

    def shutdown(self) -> None:
        """Shutdown all systems."""
        if self._context:
            for system, _ in self._systems:
                system.on_shutdown(self._context)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/infrastructure/telemetry_system.py
"""TelemetrySystem handles metrics collection and Prometheus exposure."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.systems.infrastructure.base import System, SystemContext

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)

class TelemetrySystem(System):
    """System for collecting and publishing simulation metrics."""

    def on_tick(self, ctx: SystemContext, tick: int) -> None:
        """Collect rich simulation metrics for Prometheus/Grafana."""
        from src.utils.metrics import (
            SIM_FACTION_POPULATION,
            SIM_ENTITY_LEVEL_DISTRIBUTION,
            SIM_HERO_CLASS_TOTAL,
            SIM_GOLD_CIRCULATION_TOTAL,
            SIM_BUILDING_DURABILITY_PERCENT,
            SIM_CALAMITY_ACTIVE,
            # SIM_ACTION_QUEUE_DEPTH, # Handled by WorldLoop since it owns the queue
            ACTIVE_ENTITIES,
            SIM_TOP_HERO_LEVEL,
            SIM_TOP_HERO_GOLD
        )
        from src.core.models.enums import Faction, HeroClass
        
        world = ctx.world
        
        # 1. Populations & Gold
        pop_counts = {f: 0 for f in Faction}
        gold_counts = {f: 0 for f in Faction}
        level_dist = {} # (kind, bracket) -> count
        class_dist = {} # (hc_name, tier) -> count
        
        total_alive = 0
        max_level = 0
        max_gold = 0
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
            
            total_alive += 1
            f = entity.identity.faction
            pop_counts[f] += 1
            gold_counts[f] += entity.stats.progression.gold
            
            if f == Faction.HERO_GUILD:
                max_level = max(max_level, entity.stats.progression.level)
                max_gold = max(max_gold, entity.stats.progression.gold)
            
            # Level distribution
            lvl = entity.stats.progression.level
            bracket = f"{(lvl-1)//10*10+1}-{(lvl-1)//10*10+10}"
            key = (entity.kind, bracket)
            level_dist[key] = level_dist.get(key, 0) + 1
            
            # Hero Class distribution
            if f == Faction.HERO_GUILD:
                raw_hc = getattr(entity, 'hero_class', HeroClass.NONE)
                try:
                    hc = HeroClass(raw_hc)
                except ValueError:
                    hc = HeroClass.NONE
                tier = 1
                if lvl >= 20: tier = 3
                elif lvl >= 10: tier = 2
                ckey = (hc.name.lower(), str(tier))
                class_dist[ckey] = class_dist.get(ckey, 0) + 1
                
        ACTIVE_ENTITIES.set(total_alive)
        SIM_TOP_HERO_LEVEL.set(max_level)
        SIM_TOP_HERO_GOLD.set(max_gold)
        for f, count in pop_counts.items():
            SIM_FACTION_POPULATION.labels(faction=f.name.lower()).set(count)
            SIM_GOLD_CIRCULATION_TOTAL.labels(faction=f.name.lower()).set(gold_counts[f])
            
        for (kind, bracket), count in level_dist.items():
            SIM_ENTITY_LEVEL_DISTRIBUTION.labels(kind=kind, level_bracket=bracket).set(count)
            
        for (hc_name, tier), count in class_dist.items():
            SIM_HERO_CLASS_TOTAL.labels(hero_class=hc_name, tier=tier).set(count)
            
        # 2. Buildings
        for b in world.buildings:
            pct = (b.durability / b.max_durability) * 100.0 if b.max_durability > 0 else 0
            SIM_BUILDING_DURABILITY_PERCENT.labels(building_id=b.building_id).set(pct)
            
        # 3. Calamity
        calamity_active = 0
        for entity in world.entities.values():
            if entity.combat.alive and "calamity" in entity.kind.lower():
                calamity_active = 1
                SIM_CALAMITY_ACTIVE.labels(region_id=entity.region_id).set(1)
                break
        if not calamity_active:
            SIM_CALAMITY_ACTIVE.labels(region_id="none").set(0)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/lifecycle/__init__.py


#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/lifecycle/evolution_system.py
"""EvolutionSystem handles Nemesis evolution and monster tier-ups.

When a monster kills a hero, it gains experience and can evolve into a higher tier
with a specialized prefix (e.g., 'Hero-Slayer').
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.core.models.enums import EnemyTier

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class EvolutionSystem:
    """Logic for entity evolution based on combat victory."""

    @staticmethod
    def on_hero_slain(monster: Entity, hero: Entity, world: WorldState) -> None:
        """Called when a monster successfully kills a hero."""
        if monster.identity.role != "enemy": # Roles might be strings or enums
            return

        monster.identity.kill_count += 1
        logger.info(f"Tick {world.tick}: Monster {monster.id} ({monster.kind}) killed Hero {hero.id}! Kill count: {monster.identity.kill_count}")

        # Evolution trigger: 1 kill for basic, more for higher
        threshold = 1 if monster.identity.tier < 2 else 3
        
        if monster.identity.kill_count >= threshold and monster.identity.tier < 3:
            EvolutionSystem.evolve_monster(monster, world)

    @staticmethod
    def evolve_monster(monster: Entity, world: WorldState) -> None:
        """Upgrade monster tier and stats."""
        old_kind = monster.kind
        monster.identity.tier += 1
        monster.identity.kill_count = 0
        
        # Add a prefix to the name
        prefixes = ["Bold", "Brutal", "Hero-Slayer", "Merciless", "Ancient"]
        prefix = prefixes[min(monster.identity.tier, len(prefixes)-1)]
        monster.identity.display_name = f"{prefix} {monster.identity.display_name}"
        
        # Stat boost
        monster.combat.max_hp = int(monster.combat.max_hp * 1.5)
        monster.combat.hp = monster.combat.max_hp
        monster.combat.atk += 5 * monster.identity.tier
        monster.combat.def_ += 2 * monster.identity.tier
        
        logger.info(f"Tick {world.tick}: NEMESIS EVOLUTION! {old_kind} #{monster.id} evolved into {monster.identity.display_name} (Tier {monster.identity.tier})")
        
        # Add a visual or region-wide aura effect (Pillar 5)
        if hasattr(world, "event_bus") and world.event_bus:
            # world.event_bus.publish(NemesisEvolutionEvent(...))
            pass

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/lifecycle/hero_lifecycle_system.py
"""Hero Lifecycle System — Manages hero specific progression events like familiarity and permadeath."""

import logging
from src.systems.infrastructure.base import System, SystemContext
from src.core.models.world_state import WorldState
from src.core.models.enums import AIState, ItemType, Domain
from src.core.gameplay.faction import Faction

logger = logging.getLogger(__name__)


class HeroLifecycleSystem(System):
    """System to extract Hero-specific tick constraints, bonding, and permadeath spanning."""

    def __init__(self, config, rng):
        super().__init__(config, rng)
        self._pending_hero_replacements: list[dict] = []

    def on_tick(self, ctx: SystemContext, tick: int) -> None:
        """Executed during the standard core tick interval sequence.
        
        Responsibilities:
        - Determine Hero proximity bonding vectors.
        - Handle any Pending Replacement hero spawning intervals.
        """
        self._tick_proximity_familiarity(ctx, tick)
        self._tick_inn_gossip(ctx, tick)
        self._tick_hero_trading(ctx, tick)
        self._process_hero_replacements(ctx, tick)

    # -------------------------------------------------------------------------
    # Proximity Familiarity
    # -------------------------------------------------------------------------
    def _tick_proximity_familiarity(self, ctx: SystemContext, tick: int) -> None:
        """Increase mutual familiarity between heroes in close proximity.
        
        Optimized: uses spatial index for O(1) neighbor lookup.
        """
        heroes = [e for e in ctx.world.entities.values() if e.kind == "hero" and e.combat.alive]
        if len(heroes) < 2:
            return
            
        v_range = self.config.vision_range
        
        # 1. Increase for those nearby (using spatial index)
        nearby_pairs = set()
        for h1 in heroes:
            nearby = ctx.world.entities_at_radius(h1.spatial.pos, v_range)
            for h2 in nearby:
                if h1.id == h2.id or h2.kind != "hero" or not h2.combat.alive:
                    continue
                
                # Precise distance check (spatial index is just a coarse filter)
                if h1.spatial.pos.manhattan(h2.spatial.pos) > v_range:
                    continue
                
                pair = tuple(sorted((h1.id, h2.id)))
                if pair not in nearby_pairs:
                    nearby_pairs.add(pair)
                    
                    old1 = h1.identity.hero_familiarity.get(h2.id, 0.0)
                    # Pillar 7: CHA-based Familiarity (Charisma impact)
                    # Base gain 0.002, scales with CHA (1% per point)
                    gain = 0.002 * (1.0 + h1.stats.cha * 0.01)
                    new1 = min(1.0, old1 + gain)
                    h1.identity.hero_familiarity[h2.id] = new1
                    h2.identity.hero_familiarity[h1.id] = new1 # Symmetric
                    
                    if old1 < 0.5 <= new1:
                        logger.info("Tick %d: %s and %s are now Allies!", tick, h1.identity.display_name, h2.identity.display_name)
                        if ctx.emit:
                            ctx.emit("alliance", f"{h1.identity.display_name} and {h2.identity.display_name} are now Allies",
                                       entity_ids=(h1.id, h2.id),
                                       metadata={"hero1_id": h1.id, "hero2_id": h2.id, "score": new1})
                                   
        # 2. Decay for everyone else who has a familiarity entry
        for h1 in heroes:
            for h2_id in list(h1.identity.hero_familiarity.keys()):
                pair = tuple(sorted((h1.id, h2_id)))
                if pair in nearby_pairs:
                    continue
                
                # Decay Apart: -0.0005
                h1.identity.hero_familiarity[h2_id] = max(0.0, h1.identity.hero_familiarity[h2_id] - 0.0005)
                # Symmetric decay for the other hero
                if h2_id in ctx.world.entities and ctx.world.entities[h2_id].kind == "hero":
                    ctx.world.entities[h2_id].identity.hero_familiarity[h1.id] = h1.identity.hero_familiarity[h2_id]

    def _tick_inn_gossip(self, ctx: SystemContext, tick: int) -> None:
        """Heroes at the same Inn share random entity memories."""
        at_inn = [h for h in ctx.world.entities.values() if h.kind == "hero" and h.combat.alive and h.mind.ai_state == AIState.VISIT_INN]
        if len(at_inn) < 2:
            return
            
        # Group by position
        by_pos: dict[tuple[int, int], list[Any]] = {}
        for h in at_inn:
            pos = (h.spatial.pos.x, h.spatial.pos.y)
            if pos not in by_pos:
                by_pos[pos] = []
            by_pos[pos].append(h)
            
        for pos, group in by_pos.items():
            if len(group) < 2:
                continue
            
            # Gossip chance: 20% per tick
            if self.rng.next_float(Domain.AI_DECISION, group[0].id, tick) > 0.2:
                continue
                
            # Pick two random heroes
            h1 = group[self.rng.next_int(Domain.AI_DECISION, group[0].id, tick + 1, 0, len(group)-1)]
            h2 = group[self.rng.next_int(Domain.AI_DECISION, group[1].id, tick + 2, 0, len(group)-1)]
            if h1.id == h2.id:
                continue
                
            # Transfer a random memory entry
            if h1.mind.entity_memory:
                mem = h1.mind.entity_memory[self.rng.next_int(Domain.AI_DECISION, h1.id, tick, 0, len(h1.mind.entity_memory)-1)]
                # Check if h2 already knows this
                if not any(m["id"] == mem["id"] for m in h2.mind.entity_memory):
                    h2.mind.entity_memory.append(mem.copy())
                    if ctx.emit:
                        ctx.emit("social", f"{h1.identity.display_name} shared rumors about {mem.get('kind', 'something')} with {h2.identity.display_name}",
                                   entity_ids=(h1.id, h2.id),
                                   metadata={"rumor_id": mem["id"]})

    def _tick_hero_trading(self, ctx: SystemContext, tick: int) -> None:
        """Heroes at the same resting place share items they don't need."""
        # Active in Visit Inn or Visit Guild
        at_rest = [h for h in ctx.world.entities.values() if h.kind == "hero" and h.combat.alive and h.mind.ai_state in (AIState.VISIT_INN, AIState.VISIT_GUILD)]
        if len(at_rest) < 2:
            return
            
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY, ItemTemplate
        
        def item_pwr(template: ItemTemplate) -> int:
            return (template.atk_bonus + template.def_bonus + template.matk_bonus + template.mdef_bonus + 
                    template.max_hp_bonus // 5 + int(template.crit_rate_bonus * 100) + 
                    int(template.evasion_bonus * 100))

        # Group by position
        by_pos: dict[tuple[int, int], list[Any]] = {}
        for h in at_rest:
            pos = (h.spatial.pos.x, h.spatial.pos.y)
            if pos not in by_pos:
                by_pos[pos] = []
            by_pos[pos].append(h)
            
        for pos, group in by_pos.items():
            if len(group) < 2:
                continue
            
            # Trading chance: 15% per tick
            if self.rng.next_float(Domain.AI_DECISION, group[0].id, tick) > 0.15:
                continue
                
            # Pick donor and recipient
            h1 = group[self.rng.next_int(Domain.AI_DECISION, group[0].id, tick + 3, 0, len(group)-1)]
            h2 = group[self.rng.next_int(Domain.AI_DECISION, group[1].id, tick + 4, 0, len(group)-1)]
            if h1.id == h2.id or not h1.inventory or not h2.inventory:
                continue
                
            # Donor (h1) looks for an item they don't have equipped and don't need
            # For simplicity, donor just checks all items in inventory
            for iid in list(h1.inventory.items):
                t = ITEM_REGISTRY.get(iid)
                if not t or t.item_type not in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                    continue
                
                # h1 doesn't need it if they have better equipped
                eq_id = h1.inventory.equipped.get(t.item_type)
                if eq_id:
                    eq_t = ITEM_REGISTRY.get(eq_id)
                    if eq_t and item_pwr(t) <= item_pwr(eq_t):
                        # h1 has better, so this iid is a "spare"
                        # Check if h2 can use it
                        h2_eq_id = h2.inventory.equipped.get(t.item_type)
                        better_for_h2 = False
                        if not h2_eq_id:
                            better_for_h2 = True
                        else:
                            h2_eq_t = ITEM_REGISTRY.get(h2_eq_id)
                            if h2_eq_t and item_pwr(t) > item_pwr(h2_eq_t):
                                better_for_h2 = True
                        
                        if better_for_h2 and h2.inventory.can_add(iid):
                            # Trade!
                            h1.inventory.remove_item(iid)
                            h2.inventory.add_item(iid)
                            h2.inventory.auto_equip_best(iid, getattr(h2, "hero_class", 0))
                            if ctx.emit:
                                ctx.emit("social", f"{h1.identity.display_name} gifted {t.name} to {h2.identity.display_name}",
                                           entity_ids=(h1.id, h2.id),
                                           metadata={"item_id": iid})
                            break

    # -------------------------------------------------------------------------
    # Mortality Escallation
    # -------------------------------------------------------------------------
    def process_hero_death(self, ctx: SystemContext, entity, tick: int) -> bool:
        """Handle dropping bags and tracking permadeath strikes.
        Returns False if generic handling is sufficient, True if this handler fully resolved removal.
        """
        if entity.identity.faction != Faction.HERO_GUILD or entity.home_pos is None:
            return False

        entity.identity.death_count += 1
        is_permadeath = entity.identity.death_count >= self.config.death_tier_max
        
        if is_permadeath:
            if entity.inventory:
                dropped = entity.inventory.get_all_item_ids()
                if dropped:
                    ctx.world.drop_items(entity.spatial.pos, dropped)
            
            logger.info("Tick %d: Hero %s (%s Lv%d) has DIED PERMANENTLY (deaths=%d).", 
                        tick, (entity.identity.display_name or f"#{entity.id}"), entity.kind, 
                        entity.stats.progression.level, entity.identity.death_count)
            
            if hasattr(ctx.world, "event_bus") and ctx.world.event_bus:
                from src.core.data.events import DeathEvent
                ctx.world.event_bus.publish(DeathEvent(
                    entity_id=entity.id, killer_id=None,
                    x=entity.spatial.pos.x, y=entity.spatial.pos.y,
                    level_at_death=entity.stats.progression.level,
                    is_permadeath=True
                ))
            
            # Monument spawning
            if entity.stats.progression.level >= 15:
                m_id = f"monument_{entity.id}_{tick}"
                from src.core.world.monuments import Monument
                from src.core.models.enums import HeroClass
                hc = getattr(entity, 'hero_class', None)
                bt = "hp"
                if hc == HeroClass.WARRIOR: bt = "hp"
                elif hc == HeroClass.MAGE: bt = "atk"
                elif hc == HeroClass.RANGER: bt = "atk"
                
                monument = Monument(m_id, entity.identity.display_name or f"#{entity.id}", 
                                    hc.name if hc else "NONE", 
                                    entity.stats.progression.level, entity.home_pos, bt, 0.1)
                ctx.world.monuments.append(monument)

            ctx.world.remove_entity(entity.id)
            self._schedule_hero_replacement(entity, tick)
            return True

        # Normal respawn
        entity.stats.combat.hp = entity.stats.combat.max_hp
        old_pos = entity.spatial.pos
        entity.spatial.pos = entity.home_pos
        entity.mind.ai_state = AIState.RESTING_IN_TOWN
        ctx.world.spatial_index.move(entity.id, old_pos, entity.home_pos)
        entity.next_act_at = float(tick + self.config.hero_respawn_ticks)
        entity.mind.memory.clear()
        entity.combat.effects.clear()
        
        # Tiered drop algorithm
        if entity.inventory:
            dropped_ids = []
            dropped_ids.extend(entity.inventory.items)
            entity.inventory.items.clear()
            
            if entity.identity.death_count >= 2 and entity.inventory.accessory:
                dropped_ids.append(entity.inventory.accessory)
                entity.inventory.accessory = None
            if entity.identity.death_count >= 3 and entity.inventory.armor:
                dropped_ids.append(entity.inventory.armor)
                entity.inventory.armor = None
                
            if dropped_ids:
                ctx.world.drop_items(old_pos, dropped_ids)
                logger.info("Tick %d: Hero #%d dropped %d items on death tier %d",
                            tick, entity.id, len(dropped_ids), entity.identity.death_count)
        
        logger.info("Tick %d: Hero %s died → respawning at home %s.",
                    tick, (entity.identity.display_name or f"#{entity.id}"), entity.home_pos)
        
        if hasattr(ctx.world, "event_bus") and ctx.world.event_bus:
            from src.core.data.events import DeathEvent
            ctx.world.event_bus.publish(DeathEvent(
                entity_id=entity.id, killer_id=None,
                x=entity.spatial.pos.x, y=entity.spatial.pos.y,
                level_at_death=entity.stats.progression.level,
                is_permadeath=False
            ))
            
        # Returning True skips standard mob death procedures.
        return True

    def _schedule_hero_replacement(self, dead_hero, tick: int) -> None:
        """Schedule a new hero to spawn after a delay to replace a permadead one."""
        spawn_tick = tick + 50
        self._pending_hero_replacements.append({
            "tick": spawn_tick,
            "generation": dead_hero.identity.generation + 1,
            "home_pos": dead_hero.home_pos,
        })
        logger.info("Tick %d: Hero replacement scheduled for tick %d (Gen %d)", 
                    tick, spawn_tick, dead_hero.identity.generation + 1)

    def _process_hero_replacements(self, ctx: SystemContext, tick: int) -> None:
        """Spawn replacements for permadead heroes after their countdown."""
        from src.core.gameplay.classes import HeroClass, HERO_STARTING_GEAR
        from src.core.entities.entity_builder import EntityBuilder
        from src.core.data.hero_names import generate_hero_name
        from src.core.models.enums import Faction, EntityRole
        
        still_pending = []
        class_choices = [HeroClass.WARRIOR, HeroClass.RANGER, HeroClass.MAGE, HeroClass.ROGUE]

        for rep in self._pending_hero_replacements:
            if tick >= rep["tick"]:
                new_eid = ctx.world.allocate_entity_id()
                h_class = class_choices[new_eid % len(class_choices)]
                gear = HERO_STARTING_GEAR.get(h_class, {})
                home_pos = rep["home_pos"]

                builder = (
                    EntityBuilder(self.rng, new_eid, tick=tick)
                    .kind("hero")
                    .at(home_pos)
                    .home(home_pos)
                    .faction(Faction.HERO_GUILD)
                    .role(EntityRole.HERO)
                )
                builder.with_traits(race_prefix="hero")
                hero_name = generate_hero_name(self.rng, new_eid, tick, builder._traits)

                hero = (
                    builder
                    .with_identity(display_name=hero_name, generation=rep["generation"])
                    .with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3,
                                     crit_rate=0.08, crit_dmg=1.8, evasion=0.03, gold=50)
                    .with_hero_class(h_class)
                    .with_race_skills("hero")
                    .with_class_skills(h_class, level=1)
                    .with_inventory(max_slots=self.config.hero_inventory_slots,
                                    max_weight=self.config.hero_inventory_weight,
                                    weapon=gear.get("weapon", "iron_sword"),
                                    armor=gear.get("armor", "leather_vest"),
                                    accessory=gear.get("accessory"))
                    .with_starting_items(["small_hp_potion"] * 3)
                    .with_home_storage()
                    .with_talents(race="hero")
                    .build()
                )
                ctx.world.add_entity(hero)
                hero.inventory.auto_equip_best(gear.get("weapon"), hero.progression.hero_class)
                hero.inventory.auto_equip_best(gear.get("armor"), hero.progression.hero_class)
                hero.inventory.auto_equip_best(gear.get("accessory"), hero.progression.hero_class)

                for b in ctx.world.buildings:
                    if b.spatial.pos == home_pos and b.building_type == "hero_house":
                        b.name = f"{hero_name}'s House"
                
                logger.info("Tick %d: New hero %s (Gen %d) has arrived!", 
                            tick, hero_name, hero.identity.generation)
                if ctx.emit:
                    ctx.emit("hero_arrival", f"Hero {hero_name} arrives (Gen {hero.identity.generation})",
                               entity_ids=(new_eid,),
                               metadata={"entity_id": new_eid, "name": hero_name, "generation": hero.identity.generation})
            else:
                still_pending.append(rep)
        self._pending_hero_replacements = still_pending

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/lifecycle/progression_system.py
"""ProgressionSystem handles level-ups, stamina regeneration, and skill cooldowns."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.systems.infrastructure.base import System
from src.core.models.enums import AIState

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class ProgressionSystem(System):
    """System for managing entity progression, level-ups, and resource regeneration."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute progression sub-phases."""
        self._tick_stamina_and_skills(context)
        self._check_level_ups(context)
        if tick % 100 == 0:
            self._handle_stat_decay(context)

    def _handle_stat_decay(self, context: SystemContext) -> None:
        """Decrease attributes for entities who stay idle for too long."""
        from src.core.gameplay.attributes import decay_attributes
        for entity in context.world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
            
            # Decay if idle for > 1000 ticks
            if entity.consecutive_idle_ticks > 1000 and entity.attributes:
                decay_attributes(
                    entity.attributes,
                    entity.stats,
                    context.rng,
                    entity.id,
                    context.world.tick
                )

    def _tick_stamina_and_skills(self, context: SystemContext) -> None:
        """Regenerate stamina and tick skill cooldowns for all entities."""
        for entity in context.world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
                
            prog = entity.progression
            if not prog:
                continue
                
            # Pillar 3: Tactical Stamina & Exhaustion
            if prog.stamina <= 0 and entity.mind.ai_state != AIState.EXHAUSTED:
                entity.mind.ai_state = AIState.EXHAUSTED
                logger.info("Tick %s: Entity #%s (%s) is EXHAUSTED!", context.world.tick, entity.id, entity.kind)
            
            # Stamina regen: faster when resting, slower otherwise
            if entity.mind.ai_state == AIState.EXHAUSTED:
                regen = 3 # Recovery is slow but steady
                if prog.stamina >= prog.max_stamina * 0.2:
                    entity.mind.ai_state = AIState.IDLE
                    logger.info("Tick %s: Entity #%s (%s) recovered from exhaustion.", context.world.tick, entity.id, entity.kind)
            elif entity.mind.ai_state in (AIState.RESTING_IN_TOWN, AIState.IDLE):
                regen = 5
            elif entity.mind.ai_state in (AIState.VISIT_SHOP, AIState.VISIT_BLACKSMITH,
                                     AIState.VISIT_GUILD, AIState.VISIT_CLASS_HALL,
                                     AIState.VISIT_INN):
                regen = 4
            else:
                regen = 1
                
            prog.stamina = min(prog.stamina + regen, prog.max_stamina)
            
            # Tick skill cooldowns
            if prog.skills:
                for skill in prog.skills:
                    skill.tick()

    def _check_level_ups(self, context: SystemContext) -> None:
        """Check and apply level-ups and evolution."""
        from src.core.models.enums import RACE_PROFILES
        from src.core.gameplay.attributes import recalc_derived_stats
        
        cfg = context.config
        world = context.world
        
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
                
            prog = entity.progression
            combat = entity.combat
            if not prog or not combat:
                continue
                
            # Look up racial profile
            profile = RACE_PROFILES.get(entity.kind, None)
            if not profile:
                base_race = entity.kind.split('_')[0]
                profile = RACE_PROFILES.get(base_race)
                
            if not profile or profile.train_rate == 0.0:
                continue
                
            max_level = min(cfg.max_level, profile.level_cap)
            
            # 1. Check Level Ups
            leveled_up = False
            while prog.xp >= prog.xp_to_next and prog.level < max_level:
                prog.xp -= prog.xp_to_next
                prog.level += 1
                new_level = prog.level
                leveled_up = True
                
                # Check if milestone level
                milestone = cfg.milestone_levels.get(new_level)
                
                if milestone:
                    hp_growth, atk_growth, def_growth, spd_growth = milestone
                    combat.max_hp += hp_growth
                    combat.hp = min(combat.hp + hp_growth, combat.max_hp)
                    combat.atk += atk_growth
                    combat.matk += atk_growth
                    combat.def_ += def_growth
                    combat.spd += spd_growth
                else:
                    # Normal diminishing returns stat growth
                    if new_level <= 10:
                        hp_g, atk_g, def_g, spd_g = 5, 1, 1, 1
                    elif new_level <= 20:
                        hp_g, atk_g, def_g, spd_g = 3, 1, 1, 1
                    else:
                        hp_g, atk_g, def_g, spd_g = 2, 0, 0, 0
                        
                    combat.max_hp += hp_g
                    combat.hp = min(combat.hp + hp_g, combat.max_hp)
                    combat.atk += atk_g
                    combat.matk += atk_g
                    combat.def_ += def_g
                    combat.spd += spd_g
                
                # Bracketed XP curve
                if new_level < 10:
                    scale = 1.4
                elif new_level < 20:
                    scale = 1.6
                else:
                    scale = 2.0
                prog.xp_to_next = int(prog.xp_to_next * scale)
                
                # Recalculate derived stats if attributes exist
                if entity.attributes:
                    from src.core.gameplay.attributes import recalc_derived_stats as _recalc, check_breakthroughs
                    # 1. Update breakthroughs (milestones)
                    check_breakthroughs(entity.attributes, entity.identity.traits)
                    # 2. Re-derive stats (includes breakthrough bonuses)
                    _recalc(entity.stats, entity.attributes)
                
                # Talent Points at level 25, 50, etc.
                if new_level % 25 == 0:
                    prog.talent_points += 1
                    
                logger.info("Tick %s: Entity #%s (%s) leveled up to %s!", 
                            world.tick, entity.id, entity.kind, new_level)
                if hasattr(world, "event_bus") and world.event_bus:
                    from src.core.data.events import LevelUpEvent
                    world.event_bus.publish(LevelUpEvent(
                        entity_id=entity.id,
                        old_level=new_level - 1,
                        new_level=new_level,
                        attribute_gains={"max_hp": combat.max_hp, "atk": combat.atk, "def": combat.def_, "spd": combat.spd}
                    ))

            # 2. Check Evolution (Phase D)
            if (profile.evolves 
                and prog.level >= profile.level_cap
                and entity.identity.tier < 3):
                self._evolve_entity(context, entity, profile)

    def _evolve_entity(self, context: SystemContext, entity: Any, profile: Any) -> None:
        """Transform an entity into its next tier (Phase D)."""
        from src.core.gameplay.items.items import TIER_KIND_NAMES, RACE_TIER_KINDS, RACE_STARTING_GEAR, TIER_STARTING_GEAR
        from src.core.gameplay.attributes import recalc_derived_stats
        
        base_race = entity.kind.split('_')[0]
        next_tier = entity.identity.tier + 1
        
        # Determine new kind
        tier_kinds = RACE_TIER_KINDS.get(base_race)
        if tier_kinds:
            new_kind = tier_kinds.get(next_tier)
            if not new_kind or new_kind == entity.kind and next_tier < 3:
                next_tier += 1
                new_kind = tier_kinds.get(next_tier)
        else:
            new_kind = TIER_KIND_NAMES.get(next_tier)
            
        if not new_kind:
            return

        old_kind = entity.kind
        entity.kind = new_kind
        entity.identity.tier = next_tier
        
        prog = entity.progression
        combat = entity.combat
        
        # Reset level and scale stats
        prog.level = 1
        prog.xp = 0
        prog.xp_to_next = 100 
        
        # Evolution Bonus
        combat.max_hp += 30
        combat.hp = combat.max_hp
        combat.atk += 8
        combat.def_ += 3
        combat.spd += 2
        
        # Attribute cap boost
        if entity.attribute_caps:
            entity.attribute_caps.increase_all(10)
            
        # Recalculate
        if entity.attributes:
            recalc_derived_stats(entity.stats, entity.attributes)

        if context.generator and entity.inventory:
            context.generator.equip_entity(entity)

        logger.info("Tick %s: Entity %s (%s) evolved into %s (Tier %s)!", 
                    context.world.tick, entity.id, old_kind, new_kind, next_tier)
        context.emit("evolution", f"Entity {entity.id}: {old_kind} → {new_kind}!",
                   (entity.id,),
                   {"entity_id": entity.id, "old_kind": old_kind, "new_kind": new_kind, "tier": next_tier})

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/lifecycle/world_evolution_system.py
"""WorldEvolutionSystem manages global difficulty scaling and faction aggression."""

from __future__ import annotations
from src.systems.infrastructure.base import System, SystemContext

class WorldEvolutionSystem(System):
    """System for managing simulation-wide difficulty and aggressive scaling."""

    def on_tick(self, ctx: SystemContext, tick: int) -> None:
        """Advance world age and update global modifiers."""
        world = ctx.world
        world.world_age += 1
        
        # Difficulty increases every 10k ticks
        world.difficulty_modifier = 1.0 + (world.world_age // 10000) * 0.1
        
        from src.utils.metrics import SIM_WORLD_DIFFICULTY_MULT
        SIM_WORLD_DIFFICULTY_MULT.set(world.difficulty_modifier)
        
        # Faction slow-creep aggression
        for f in [1, 2, 3]: # Faction enums or hardcoded indices
            agg = world.faction_aggression.get(f, 0.0)
            world.faction_aggression[f] = min(100.0, agg + 0.001)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/world/__init__.py


#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/world/environment_system.py
"""EnvironmentSystem handles territory effects, perception, and memories."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.gameplay.effects import territory_debuff
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class EnvironmentSystem(System):
    """System for spatial-awareness, memory, and environmental effects."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute environment phases."""
        self._process_territory_effects(context)
        self._update_entity_memory(context, tick)
        self._update_entity_goals(context)

    def _process_territory_effects(self, context: SystemContext) -> None:
        """Apply passive debuffs to entities in non-allied territory."""
        world = context.world
        reg = context.faction_reg
        grid = world.grid
        
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
            
            # Check territory (Town vs Camp)
            is_town = grid.is_town(entity.spatial.pos)
            is_camp = grid.is_camp(entity.spatial.pos)
            
            if is_town and not reg.is_allied(entity.identity.faction, "HERO_GUILD"):
                entity.combat.effects.append(territory_debuff(source="Town Watch"))
            elif is_camp and not reg.is_allied(entity.identity.faction, "GOBLIN_HORDE"):
                entity.combat.effects.append(territory_debuff(source="Camp Sentinels"))

    def _update_entity_memory(self, context: SystemContext, tick: int) -> None:
        """Update entity perception of terrain and other entities."""
        world = context.world
        grid = world.grid
        
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
            
            # Vision-based terrain update
            vr = int(entity.combat.vision_range)
            px, py = int(entity.spatial.pos.x), int(entity.spatial.pos.y)
            for dx in range(-vr, vr + 1):
                for dy in range(-vr, vr + 1):
                    # Simple square vision for performance
                    tx, ty = px + dx, py + dy
                    if grid.in_bounds_xy(tx, ty):
                        mat = grid.get_xy(tx, ty)
                        entity.mind.terrain_memory[(tx, ty)] = mat
            
            # Entity awareness
            nearby = world.entities_at_radius(entity.spatial.pos, vr)
            # Filter and store (could be expanded for more complex AI)
            entity.mind.entity_memory = [
                {"id": other.id, "kind": other.kind, "pos": (other.spatial.pos.x, other.spatial.pos.y)}
                for other in nearby if other.id != entity.id and other.combat.alive
            ]

    def _update_entity_goals(self, context: SystemContext) -> None:
        """Re-evaluate goals for all entities if needed."""
        world = context.world
        for entity in world.entities.values():
            if not entity.combat.alive or not entity.mind.goals:
                continue
            
            # Logic for pruning completed goals or prioritizing new ones
            entity.mind.goals = [g for g in entity.mind.goals if not getattr(g, 'is_complete', False)]

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/world/generator.py
"""Entity generators — spawners that create new entities periodically."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.gameplay.classes import mob_class_for
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.enums import AIState, Domain, EnemyTier, RACE_PROFILES
from src.core.gameplay.faction import Faction
from src.core.gameplay.items.item_registry import ITEM_REGISTRY, ItemTemplate
from src.core.world.spawn_config import SPAWN_CONFIGS, LOOT_CONFIGS
from src.core.entities.entity import Entity, Vector2, Inventory
from src.core.world.regions import DIFFICULTY_TIERS

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG


# Stat multipliers per tier: (hp_mult, atk_mult, def_base, spd_mod, crit, evasion, luck)
_TIER_STATS: dict[int, tuple[float, float, int, int, float, float, int]] = {
    EnemyTier.BASIC:   (1.0, 1.0, 0,  0, 0.05, 0.00, 0),
    EnemyTier.SCOUT:   (0.8, 0.9, 0,  3, 0.08, 0.05, 2),
    EnemyTier.WARRIOR: (1.5, 1.3, 3,  -1, 0.07, 0.02, 1),
    EnemyTier.ELITE:   (2.5, 1.8, 6,  0, 0.12, 0.05, 5),
}


class EntityGenerator:
    """Spawns entities at a configurable interval up to a population cap."""

    __slots__ = ("_config", "_rng")

    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._rng = rng

    def should_spawn(self, world: WorldState) -> bool:
        alive_count = sum(1 for e in world.entities.values() if e.kind != "generator" and e.combat.alive)
        return (
            world.tick % self._config.generator_spawn_interval == 0
            and alive_count < self._config.generator_max_entities
        )

    def equip_entity(self, entity: Entity) -> None:
        """Refresh an entity's equipment based on its current race and tier."""
        from src.core.gameplay.items.items import RACE_STARTING_GEAR, TIER_STARTING_GEAR
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY

        if not entity.inventory:
            return

        base_race = entity.kind.split('_')[0]
        tier = entity.tier
        
        gear = RACE_STARTING_GEAR.get(base_race, {}).get(tier)
        if not gear:
            gear = TIER_STARTING_GEAR.get(tier)
            
        if gear:
            for item_id in gear.values():
                if item_id in ITEM_REGISTRY:
                    entity.inventory.add_item(item_id)
                    entity.inventory.auto_equip_best(item_id)

    def spawn_calamity(self, world: WorldState, template_id: str) -> Entity:
        """Spawn a unique World Boss (Calamity)."""
        from src.core.models.calamities import CALAMITY_TEMPLATES
        from src.core.models.enums import Domain, EntityRole

        template = CALAMITY_TEMPLATES.get(template_id)
        if not template:
            raise ValueError(f"Unknown calamity template: {template_id}")

        eid = world.allocate_entity_id()
        tick = world.tick

        # Calamity stats are significantly higher than Elites
        mult = template.stat_multiplier
        world_mod = world.difficulty_modifier
        
        # Scale stats
        base_hp = int(100 * mult * world_mod)
        base_atk = int(20 * mult * world_mod)
        base_def = int(10 * mult)
        
        # The Generator doesn't have a context-aware logger yet, but we can at least make this JSON-safe
        # by using a named logger. However, it's better to use the root logger which is already configured.
        logging.getLogger("generator").info(
            "Spawning calamity: %s", template_id,
            extra={'tick': tick, 'entity_id': eid, 'component': 'generator'}
        )
        
        base_spd = 12 + self._rng.next_int(Domain.SPAWN, eid, tick, 0, 4)
        pos = self._resolve_position(world, eid, tick, None)
        
        inv = Inventory(items=[], max_slots=20, max_weight=100.0)
        for item_id in template.legendary_loot:
            inv.add_item(item_id)
            inv.auto_equip_best(item_id)

        builder = EntityBuilder(self._rng, eid, tick=tick)
        entity = (
            builder
            .kind(template_id)
            .with_identity(display_name=template.name)
            .at(pos)
            .ai_state(AIState.WANDER)
            .faction(template.faction)
            .role(EntityRole.WORLD_BOSS)
            .with_base_stats(
                hp=base_hp, atk=base_atk, def_=base_def, spd=base_spd,
                luck=20, crit_rate=0.2, crit_dmg=2.0, evasion=0.1,
                level=30, xp_to_next=999999,
                gold=5000,
            )
            .with_existing_inventory(inv)
            .with_mob_class(template.archetype)
            .with_mob_attributes(50, 4)
            .with_traits(trait_ids=template.traits)
            .is_world_boss(True)
            .build()
        )
        return entity

    def spawn(
        self, world: WorldState, tier: int | None = None,
        near_pos: Vector2 | None = None, difficulty_tier: int = 1,
    ) -> Entity:
        """Create a new tiered entity, picking race based on terrain."""
        eid = world.allocate_entity_id()
        tick = world.tick

        if tier is None:
            # We don't know the race yet, so pass None for faction
            tier = self._roll_tier(eid, tick, faction=None, world=world)

        pos = self._resolve_position(world, eid, tick, near_pos)
        
        # Terrain-based race lookup (using fallback to goblin)
        terrain_type = int(world.grid.get(pos)) if hasattr(world, "grid") else 1
        from src.core.gameplay.items.items import TERRAIN_RACE
        race = TERRAIN_RACE.get(terrain_type, "goblin")
        
        return self.spawn_race(world, race, tier=tier, near_pos=pos, difficulty_tier=difficulty_tier)

    def spawn_race(
        self, world: WorldState, race: str,
        tier: int | None = None, near_pos: Vector2 | None = None,
        difficulty_tier: int = 1,
    ) -> Entity:
        """Spawn a race-specific entity."""
        eid = world.allocate_entity_id()
        tick = world.tick

        pos = self._resolve_position(world, eid, tick, near_pos)
        
        # Milestone 7: Safe-zone Expansion (Regional Suppression)
        is_safe_zone = False
        for r in world.regions:
            dist = pos.manhattan(r.center)
            if dist <= r.radius:
                control = world.region_control.get(r.region_id, 0.0)
                if control > 80.0:
                    is_safe_zone = True
                    # 50% chance to skip spawn in Safe-zones
                    if self._rng.next_int(Domain.SPAWN, eid, tick + 7, 0, 100) < 50:
                        return None 
                break

        if tier is None:
            profile = RACE_PROFILES.get(race)
            faction = profile.factions[0] if profile and profile.factions else Faction.GOBLIN_HORDE
            tier = self._roll_tier(eid, tick, faction=faction, world=world)
            
            # Safe-zones cap tiers at BASIC or SCOUT
            if is_safe_zone:
                tier = min(tier, EnemyTier.SCOUT)
        diff = DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])

        profile = RACE_PROFILES.get(race)
        race_mods = profile.stat_mods if profile else [1.0, 1.0, 0, 0, 0.05, 0.0, 0]
        r_hp_m, r_atk_m, r_def_mod, r_spd_mod, r_crit, r_evasion, r_luck = race_mods

        hp_m, atk_m, def_base, spd_mod, t_crit, t_evasion, t_luck = _TIER_STATS.get(
            tier, _TIER_STATS[EnemyTier.BASIC])

        # World Age Scaling (Epic 17 Phase 2)
        world_age_mult = 1.0 + (world.world_day / 200) * 0.5
        
        base_hp = int((15 + self._rng.next_int(Domain.SPAWN, eid, tick + 2, 0, 10)) * hp_m * r_hp_m * diff.hp * world_age_mult)
        base_atk = int((3 + self._rng.next_int(Domain.SPAWN, eid, tick + 3, 0, 4)) * atk_m * r_atk_m * diff.atk * world_age_mult)
        base_spd = 8 + self._rng.next_int(Domain.SPAWN, eid, tick + 4, 0, 4) + spd_mod + r_spd_mod
        base_def = int((def_base + r_def_mod + self._rng.next_int(Domain.SPAWN, eid, tick + 5, 0, 2)) * diff.def_ * world_age_mult)

        level_min = diff.level_min + (world.world_day // 50)
        level_max = diff.level_max + (world.world_day // 30)
        level = self._rng.next_int(Domain.SPAWN, eid, tick + 6, level_min, level_max)
        
        spawn_cfg = SPAWN_CONFIGS.get((race, EnemyTier(tier)))
        kind = spawn_cfg.kind if spawn_cfg else race
        
        # Factions are now in RaceProfile
        faction = profile.factions[0] if profile and profile.factions else Faction.GOBLIN_HORDE
        ai_state = self._resolve_ai_state(tier, near_pos)
        inv = self._build_race_inventory(eid, tick, tier, race, kind, difficulty_tier)

        attr_base = 3 + tier * 2
        r_str = int(r_atk_m * 3)
        r_agi = r_spd_mod
        r_vit = int(r_hp_m * 3)
        r_spi = int(r_hp_m * 2) if race == "undead" else 0
        r_per = r_spd_mod
        r_cha = 0

        mob_cls = mob_class_for(race, tier)
        entity = (
            EntityBuilder(self._rng, eid, tick=tick)
            .kind(kind)
            .at(pos)
            .home(near_pos)
            .leash(self._config.mob_leash_radius)
            .ai_state(ai_state)
            .faction(faction)
            .tier(tier)
            .with_base_stats(
                hp=max(base_hp, 5), atk=max(base_atk, 1),
                def_=max(base_def, 0), spd=max(base_spd, 1),
                luck=r_luck + t_luck, crit_rate=r_crit + t_crit, crit_dmg=1.5,
                evasion=r_evasion + t_evasion, level=level,
                xp_to_next=int(100 * (1.5 ** (level - 1))),
                gold=int(self._rng.next_int(Domain.LOOT, eid, tick, 0, 10 + tier * 10) * diff.gold),
            )
            .with_existing_inventory(inv)
            .with_mob_class(mob_cls)
            .with_race_attributes(
                attr_base, tier,
                r_str=r_str, r_agi=r_agi, r_vit=r_vit,
                r_spi=r_spi, r_per=r_per, r_cha=r_cha,
            )
            .with_race_skills(kind)
            .with_traits(race_prefix=race)
            .with_talents(race=race)
            .build()
        )
        entity.difficulty_tier = difficulty_tier
        return entity

    def _resolve_position(
        self, world: WorldState, eid: int, tick: int, near_pos: Vector2 | None,
    ) -> Vector2:
        if near_pos is not None:
            ox = self._rng.next_int(Domain.SPAWN, eid, tick, -3, 3)
            oy = self._rng.next_int(Domain.SPAWN, eid, tick + 1, -3, 3)
            pos = Vector2(near_pos.x + ox, near_pos.y + oy)
        else:
            x = self._rng.next_int(Domain.SPAWN, eid, tick, 0, world.grid.width - 1)
            y = self._rng.next_int(Domain.SPAWN, eid, tick + 1, 0, world.grid.height - 1)
            pos = Vector2(x, y)

        if not world.grid.is_walkable(pos) or world.grid.is_town(pos) or world.grid.is_sanctuary(pos):
            pos = self._find_nearest_walkable_non_town(world, pos)
        return pos

    def _resolve_ai_state(self, tier: int, near_pos: Vector2 | None) -> AIState:
        if tier == EnemyTier.ELITE or near_pos is not None:
            return AIState.GUARD_CAMP
        return AIState.WANDER

    def _build_race_inventory(
        self, eid: int, tick: int, tier: int, race: str, kind: str,
        difficulty_tier: int = 1,
    ) -> Inventory:
        from src.core.gameplay.items.items import Inventory
        inv = Inventory(
            items=[],
            max_slots=self._config.goblin_inventory_slots + tier,
            max_weight=self._config.goblin_inventory_weight + tier * 3.0,
        )
        
        spawn_cfg = SPAWN_CONFIGS.get((race, EnemyTier(tier)))
        if spawn_cfg:
            for item_id in spawn_cfg.starting_gear:
                if item_id in ITEM_REGISTRY:
                    inv.add_item(item_id)
                    inv.auto_equip_best(item_id)

        # Loot from LootConfig
        loot_cfg = LOOT_CONFIGS.get(kind)
        if loot_cfg:
            from src.core.gameplay.items.items import DIFFICULTY_DROP_MULTIPLIER
            drop_mult = DIFFICULTY_DROP_MULTIPLIER.get(difficulty_tier, 1.0)
            
            # Check for loot
            if self._rng.next_bool(Domain.LOOT, eid, tick, loot_cfg.drop_chance * drop_mult):
                for item_id in loot_cfg.guaranteed_items:
                    inv.add_item(item_id)
                
                # Roll for random pool
                for item_id in loot_cfg.random_pool:
                    if self._rng.next_bool(Domain.LOOT, eid, tick + hash(item_id) % 100, 0.2):
                         inv.add_item(item_id)

        return inv

    def _roll_tier(self, eid: int, tick: int, faction: Faction | None = None, world: WorldState | None = None) -> int:
        roll = self._rng.next_float(Domain.SPAWN, eid, tick + 10)
        
        # War Bonus: Shift distribution towards higher tiers
        war_bonus = 0.0
        if world and faction and world.war_status.get(int(faction), False):
            war_bonus = 0.15 # 15% shift
            
        if roll < (0.55 - war_bonus):
            return EnemyTier.BASIC
        if roll < (0.80 - war_bonus):
            return EnemyTier.SCOUT
        if roll < (0.95 - war_bonus):
            return EnemyTier.WARRIOR
        return EnemyTier.ELITE

    @staticmethod
    def _find_nearest_walkable_non_town(world: WorldState, origin: Vector2) -> Vector2:
        from collections import deque
        visited: set[tuple[int, int]] = set()
        queue: deque[Vector2] = deque([origin])
        while queue:
            pos = queue.popleft()
            if world.grid.is_walkable(pos) and not world.grid.is_town(pos):
                return pos
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                npos = Vector2(pos.x + dx, pos.y + dy)
                key = (npos.x, npos.y)
                if key not in visited and world.grid.in_bounds(npos):
                    visited.add(key)
                    queue.append(npos)
        return origin

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/world/strategy_system.py
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.systems.infrastructure.base import System
from src.core.models.enums import Faction, AIState, Material
from src.core.entities.entity import Entity, Stats, Vector2

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)

class StrategySystem(System):
    """Milestone 7: Strategic layer for Faction Wars and Territory Conquest."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Process strategic shifts every 10 ticks (faster feedback than 100)."""
        if tick % 10 != 0:
            return

        self._process_deaths(context)
        self._update_war_status(context)
        self._update_region_control(context)
        self._apply_regional_effects(context)

    def _process_deaths(self, context: SystemContext) -> None:
        """Shift region control based on recent deaths."""
        to_clear = []
        for (fac_id, reg_id), count in context.world.faction_deaths_per_region.items():
            # Shift influence: Hero death = -5.0, Monster death = +5.0
            shift = 5.0 * count
            if fac_id == int(Faction.HERO_GUILD):
                context.world.region_control[reg_id] = context.world.region_control.get(reg_id, 0.0) - shift
            else:
                context.world.region_control[reg_id] = context.world.region_control.get(reg_id, 0.0) + shift
            
            # Clamp Influence
            context.world.region_control[reg_id] = max(-100.0, min(100.0, context.world.region_control[reg_id]))
            to_clear.append((fac_id, reg_id))

        # We clear deaths in WorldLoop currently, but let's shift it here soon.
        # Actually, let's just clear what we processed.
        for key in to_clear:
            context.world.faction_deaths_per_region[key] = 0

    def _apply_regional_effects(self, context: SystemContext) -> None:
        """Apply Stronghold Auras and Regional Influence to entities."""
        from src.core.world.regions import find_region_at
        from src.core.gameplay.effects import EffectType, conquered_debuff

        # Pillar 5: Static Influence (Stronghold Auras)
        # We optimize by finding all active strongholds first
        strongholds = [e for e in context.world.entities.values() if e.kind == "stronghold" and e.combat.alive]
        
        for ent in context.world.entities.values():
            if not ent.combat.alive or ent.kind in ("generator", "stronghold"):
                continue
                
            region = find_region_at(ent.spatial.pos, context.world.regions)
            if not region:
                continue
            
            # 1. Stronghold Aura: Proximity based (Dist < 10) or Region-wide if conquered
            local_stronghold = next((s for s in strongholds if ent.spatial.pos.manhattan(s.spatial.pos) < 12), None)
            
            if ent.identity.faction == Faction.HERO_GUILD and local_stronghold:
                # Hero is under the shadow of a stronghold
                if not any(e.effect_type == EffectType.CONQUERED_DEBUFF for e in ent.combat.effects):
                    # Rename conceptually to 'Aura of Despair' or keep debuff class
                    ent.combat.effects.append(conquered_debuff(duration=5))
                    logger.debug(f"Tick {context.world.tick}: Hero {ent.id} affected by Stronghold Aura at {local_stronghold.spatial.pos}")
            else:
                # Remove if out of range
                ent.combat.effects = [e for e in ent.combat.effects if e.effect_type != EffectType.CONQUERED_DEBUFF]
            
            # 2. Regional Fatigue (Pillar 6 integration for Goal scoring)
            # This is handled in AIBrain/GoalEvaluator, but we can update world-state influence here

    def _update_war_status(self, context: SystemContext) -> None:
        """Handle transition to WAR state based on aggression."""
        for f_id, agg in context.world.faction_aggression.items():
            was_at_war = context.world.war_status.get(f_id, False)
            is_at_war = agg >= 80.0
            
            if is_at_war and not was_at_war:
                context.world.war_status[f_id] = True
                from src.core.data.events import WarEvent
                if hasattr(context.world, "event_bus") and context.world.event_bus:
                    context.world.event_bus.publish(WarEvent(faction_id=f_id, is_declared=True, aggression=agg))
                if context.emit:
                    context.emit("war", f"FACTION {Faction(f_id).name} HAS DECLARED WAR ON THE TOWN!",
                                metadata={"faction_id": f_id, "aggression": agg})
            elif not is_at_war and was_at_war:
                # Optional: Peace transition if aggression drops below 50
                if agg < 50.0:
                    context.world.war_status[f_id] = False
                    from src.core.data.events import WarEvent
                    if hasattr(context.world, "event_bus") and context.world.event_bus:
                        context.world.event_bus.publish(WarEvent(faction_id=f_id, is_declared=False, aggression=agg))
                    if context.emit:
                        context.emit("peace", f"FACTION {Faction(f_id).name} has signed a temporary truce.",
                                    metadata={"faction_id": f_id, "aggression": agg})

    def _update_region_control(self, context: SystemContext) -> None:
        """Evaluate territory ownership based on control index."""
        for region in context.world.regions:
            # Town region is always neutral/sanctuary
            if region.terrain == Material.TOWN:
                continue

            control = context.world.region_control.get(region.region_id, 0.0)
            
            # Conquest by Monsters: Influence < -50
            if control < -50.0 and region.owner_faction is None:
                # Find the most likely owner (simplification for now: matching terrain)
                from src.core.gameplay.faction import FactionRegistry
                owner = context.faction_reg.tile_owner(region.terrain)
                if owner:
                    region.owner_faction = owner
                    self._spawn_stronghold(context, region)
                    from src.core.data.events import ConquestEvent
                    if hasattr(context.world, "event_bus") and context.world.event_bus:
                        context.world.event_bus.publish(ConquestEvent(
                            region_id=region.region_id, region_name=region.name, 
                            old_owner=None, new_owner=owner.name, is_liberation=False
                        ))
                    if context.emit:
                        context.emit("conquest", f"REGION {region.name} HAS FALLEN TO {owner.name}!",
                                    metadata={"region_id": region.region_id, "owner": owner.name})

            # Liberation by Heroes: Influence > 50
            elif control > 50.0 and region.owner_faction is not None:
                old_owner = region.owner_faction
                region.owner_faction = None
                self._remove_stronghold(context, region)
                from src.core.data.events import ConquestEvent
                if hasattr(context.world, "event_bus") and context.world.event_bus:
                    context.world.event_bus.publish(ConquestEvent(
                        region_id=region.region_id, region_name=region.name, 
                        old_owner=old_owner.name, new_owner=None, is_liberation=True
                    ))
                if context.emit:
                    context.emit("liberation", f"REGION {region.name} HAS BEEN LIBERATED FROM {old_owner.name}!",
                                metadata={"region_id": region.region_id, "liberator": "HERO_GUILD"})

    def _spawn_stronghold(self, context: SystemContext, region: any) -> None:
        """Spawn a defensive fortification that heroes must destroy to retake the region."""
        from src.core.entities.entity_builder import EntityBuilder
        builder = EntityBuilder(context.rng, context.world.allocate_entity_id(), context.world.tick)
        stronghold = (
            builder
            .kind("stronghold")
            .at(region.center)
            .faction(region.owner_faction)
            .ai_state(AIState.IDLE)
            .with_base_stats(
                hp=2000,
                atk=0, def_=50, spd=0,
                level=region.difficulty * 5
            )
            .build()
        )
        context.world.add_entity(stronghold)
        logger.info("Spawned Stronghold at %s for faction %s", region.name, region.owner_faction)

    def _remove_stronghold(self, context: SystemContext, region: any) -> None:
        """Find and remove the stronghold in this region."""
        to_remove = []
        for ent in context.world.entities.values():
            if ent.kind == "stronghold" and ent.spatial.pos == region.center:
                to_remove.append(ent.id)
        
        for eid in to_remove:
            context.world.remove_entity(eid)

    def is_conquered(self, context: SystemContext, region_id: str) -> bool:
        """Helper to check if a region is currently conquered."""
        return context.world.region_control.get(region_id, 0.0) <= -80.0

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/world/terrain_detail.py
"""Terrain Detail Generator — adds intra-region variety (epic-09).

After Voronoi paints each region with a uniform terrain type, this generator
adds natural features: clearings, water bodies, cliff faces, paths, bridges,
lava vents, dense groves, etc.  Each biome has its own detail pass.

All generation is deterministic via DeterministicRNG.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.models.enums import Domain, Material
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.core.world.grid import Grid
    from src.core.world.regions import Region
    from src.platform.rng import DeterministicRNG


# ---------------------------------------------------------------------------
# Per-biome feature specs
# ---------------------------------------------------------------------------
# Each spec defines: (feature_material, chance_per_tile, cluster_size_range,
#                      min_count, max_count_per_region)
# "chance_per_tile" is checked per tile; "cluster" means we paint a blob.

_BIOME_FEATURES: dict[int, list[dict]] = {
    Material.FOREST: [
        {"name": "clearing", "mat": Material.FLOOR, "chance": 0.04,
         "cluster_min": 2, "cluster_max": 4},
        {"name": "dense_grove", "mat": Material.WALL, "chance": 0.01,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "stream", "type": "river", "width": 1, "count_min": 1, "count_max": 2},
        {"name": "path", "type": "road_network"},
    ],
    Material.DESERT: [
        {"name": "ridge", "mat": Material.WALL, "chance": 0.015,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "oasis", "mat": Material.WATER, "chance": 0.005,
         "cluster_min": 2, "cluster_max": 3},
        {"name": "hard_ground", "mat": Material.FLOOR, "chance": 0.03,
         "cluster_min": 1, "cluster_max": 3},
        {"name": "caravan_route", "type": "road_network"},
    ],
    Material.SWAMP: [
        {"name": "pool", "mat": Material.WATER, "chance": 0.06,
         "cluster_min": 2, "cluster_max": 3},
        {"name": "shallow", "mat": Material.SHALLOW_WATER, "chance": 0.04,
         "cluster_min": 1, "cluster_max": 3},
        {"name": "thicket", "mat": Material.WALL, "chance": 0.01,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "mudflat", "mat": Material.FLOOR, "chance": 0.03,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "bog_path", "type": "road_network"},
    ],
    Material.MOUNTAIN: [
        {"name": "cliff", "mat": Material.WALL, "chance": 0.02,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "valley", "mat": Material.FLOOR, "chance": 0.04,
         "cluster_min": 2, "cluster_max": 3},
        {"name": "lava_vent", "mat": Material.LAVA, "chance": 0.008,
         "cluster_min": 1, "cluster_max": 2, "min_difficulty": 3},
        {"name": "cave", "mat": Material.CAVE, "chance": 0.005,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "pass", "type": "road_network"},
    ],
    Material.GRASSLAND: [
        {"name": "wildflower", "mat": Material.FLOOR, "chance": 0.03,
         "cluster_min": 2, "cluster_max": 4},
        {"name": "pond", "mat": Material.SHALLOW_WATER, "chance": 0.008,
         "cluster_min": 2, "cluster_max": 3},
        {"name": "farmland", "mat": Material.FARMLAND, "chance": 0.02,
         "cluster_min": 2, "cluster_max": 4},
        {"name": "trail", "type": "road_network"},
    ],
    Material.SNOW: [
        {"name": "ice_sheet", "mat": Material.WATER, "chance": 0.03,
         "cluster_min": 2, "cluster_max": 3},
        {"name": "frozen_ridge", "mat": Material.WALL, "chance": 0.015,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "tundra_clearing", "mat": Material.FLOOR, "chance": 0.03,
         "cluster_min": 2, "cluster_max": 3},
        {"name": "frost_path", "type": "road_network"},
    ],
    Material.JUNGLE: [
        {"name": "canopy_gap", "mat": Material.FLOOR, "chance": 0.03,
         "cluster_min": 2, "cluster_max": 3},
        {"name": "dense_undergrowth", "mat": Material.WALL, "chance": 0.015,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "jungle_stream", "type": "river", "width": 1, "count_min": 1, "count_max": 2},
        {"name": "shallow_marsh", "mat": Material.SHALLOW_WATER, "chance": 0.02,
         "cluster_min": 1, "cluster_max": 3},
        {"name": "jungle_trail", "type": "road_network"},
    ],
    Material.VOLCANIC: [
        {"name": "lava_flow", "mat": Material.LAVA, "chance": 0.02,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "obsidian_wall", "mat": Material.WALL, "chance": 0.015,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "ash_field", "mat": Material.FLOOR, "chance": 0.04,
         "cluster_min": 2, "cluster_max": 3},
        {"name": "volcanic_cave", "mat": Material.CAVE, "chance": 0.005,
         "cluster_min": 1, "cluster_max": 2},
        {"name": "magma_path", "type": "road_network"},
    ],
}


class TerrainDetailGenerator:
    """Adds intra-region terrain detail after Voronoi assignment.

    Thread-safe: only called during world build.
    Deterministic: all randomness via DeterministicRNG.
    """

    __slots__ = ("_grid", "_rng")

    def __init__(self, grid: Grid, rng: DeterministicRNG) -> None:
        self._grid = grid
        self._rng = rng

    def generate_all(self, regions: list[Region]) -> None:
        """Run detail passes for every region."""
        for idx, region in enumerate(regions):
            self._detail_region(region, idx)

    def _detail_region(self, region: Region, region_idx: int) -> None:
        """Apply biome-specific detail to a single region."""
        features = _BIOME_FEATURES.get(int(region.terrain))
        if not features:
            return

        grid = self._grid
        rng = self._rng
        base_mat = region.terrain
        cx, cy = region.center.x, region.center.y
        radius = region.radius

        for fi, feat in enumerate(features):
            # Skip difficulty-gated features
            min_diff = feat.get("min_difficulty", 0)
            if min_diff and region.difficulty < min_diff:
                continue

            feat_type = feat.get("type")

            if feat_type == "river":
                self._place_river(region, region_idx, fi, feat)
            elif feat_type == "road_network":
                self._place_road_network(region, region_idx, fi)
            else:
                # Scatter-based feature (clusters)
                self._place_scatter(region, region_idx, fi, feat)

    def _place_scatter(self, region: Region, ridx: int, fidx: int, feat: dict) -> None:
        """Place scattered clusters of a material within the region."""
        grid = self._grid
        rng = self._rng
        base_mat = region.terrain
        target_mat = Material(feat["mat"])
        chance = feat["chance"]
        cluster_min = feat.get("cluster_min", 1)
        cluster_max = feat.get("cluster_max", 3)
        cx, cy = region.center.x, region.center.y
        radius = region.radius

        # Scan tiles within region radius
        seed_base = ridx * 1000 + fidx * 100
        placed = 0
        max_features = max(3, int(radius * radius * chance * 0.3))

        for y in range(max(0, cy - radius), min(grid.height, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(grid.width, cx + radius + 1)):
                if placed >= max_features:
                    return
                pos = Vector2(x, y)
                if grid.get(pos) != base_mat:
                    continue
                # Deterministic chance check
                tile_seed = seed_base + y * grid.width + x
                roll = rng.next_float(Domain.MAP_GEN, tile_seed, ridx + fidx * 50)
                if roll >= chance:
                    continue
                # Place a cluster centered here
                csize = rng.next_int(Domain.MAP_GEN, tile_seed, ridx + 300,
                                     cluster_min, cluster_max)
                self._paint_cluster(x, y, csize, target_mat, base_mat)
                placed += 1

    def _paint_cluster(
        self, cx: int, cy: int, size: int, mat: Material, base_mat: Material
    ) -> None:
        """Paint a small blob of *mat* around (cx, cy), only overwriting *base_mat*."""
        grid = self._grid
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                if abs(dx) + abs(dy) > size:
                    continue
                pos = Vector2(cx + dx, cy + dy)
                if grid.in_bounds(pos) and grid.get(pos) == base_mat:
                    grid.set(pos, mat)

    def _place_river(self, region: Region, ridx: int, fidx: int, feat: dict) -> None:
        """Place a winding river/stream through the region."""
        grid = self._grid
        rng = self._rng
        base_mat = region.terrain
        cx, cy = region.center.x, region.center.y
        radius = region.radius
        width = feat.get("width", 1)
        count_min = feat.get("count_min", 1)
        count_max = feat.get("count_max", 1)

        num_rivers = rng.next_int(Domain.MAP_GEN, ridx * 200 + fidx, 0,
                                  count_min, count_max)

        for ri in range(num_rivers):
            seed = ridx * 500 + fidx * 50 + ri
            # Pick start edge: top or left of region
            if rng.next_bool(Domain.MAP_GEN, seed, 1, 0.5):
                # Horizontal river (left to right)
                start_y = cy + rng.next_int(Domain.MAP_GEN, seed, 2,
                                            -radius // 3, radius // 3)
                ry = start_y
                for rx in range(max(0, cx - radius), min(grid.width, cx + radius + 1)):
                    pos = Vector2(rx, ry)
                    if grid.in_bounds(pos) and grid.get(pos) == base_mat:
                        grid.set(pos, Material.WATER)
                        # Paint width
                        for w in range(1, width + 1):
                            wp = Vector2(rx, ry + w)
                            if grid.in_bounds(wp) and grid.get(wp) == base_mat:
                                grid.set(wp, Material.WATER)
                    # Wander the river path
                    drift = rng.next_int(Domain.MAP_GEN, seed + rx, 10, -1, 1)
                    ry = max(0, min(grid.height - 1, ry + drift))
            else:
                # Vertical river (top to bottom)
                start_x = cx + rng.next_int(Domain.MAP_GEN, seed, 3,
                                            -radius // 3, radius // 3)
                rx = start_x
                for ry in range(max(0, cy - radius), min(grid.height, cy + radius + 1)):
                    pos = Vector2(rx, ry)
                    if grid.in_bounds(pos) and grid.get(pos) == base_mat:
                        grid.set(pos, Material.WATER)
                        for w in range(1, width + 1):
                            wp = Vector2(rx + w, ry)
                            if grid.in_bounds(wp) and grid.get(wp) == base_mat:
                                grid.set(wp, Material.WATER)
                    drift = rng.next_int(Domain.MAP_GEN, seed + ry, 11, -1, 1)
                    rx = max(0, min(grid.width - 1, rx + drift))

            # Place bridges where river crosses the region center ± a few tiles
            self._place_bridges_near(region, ri)

    def _place_bridges_near(self, region: Region, river_idx: int) -> None:
        """Place BRIDGE tiles at 2-3 points where WATER meets the region center area."""
        grid = self._grid
        rng = self._rng
        cx, cy = region.center.x, region.center.y
        bridge_range = max(region.radius // 3, 4)

        bridges_placed = 0
        for y in range(max(0, cy - bridge_range), min(grid.height, cy + bridge_range + 1)):
            for x in range(max(0, cx - bridge_range), min(grid.width, cx + bridge_range + 1)):
                if bridges_placed >= 3:
                    return
                pos = Vector2(x, y)
                if grid.get(pos) != Material.WATER:
                    continue
                # Place bridge if this water tile has walkable neighbors on opposite sides
                has_n = grid.in_bounds_xy(x, y - 1) and grid.get_xy(x, y - 1) not in (
                    Material.WATER, Material.WALL, Material.LAVA)
                has_s = grid.in_bounds_xy(x, y + 1) and grid.get_xy(x, y + 1) not in (
                    Material.WATER, Material.WALL, Material.LAVA)
                has_w = grid.in_bounds_xy(x - 1, y) and grid.get_xy(x - 1, y) not in (
                    Material.WATER, Material.WALL, Material.LAVA)
                has_e = grid.in_bounds_xy(x + 1, y) and grid.get_xy(x + 1, y) not in (
                    Material.WATER, Material.WALL, Material.LAVA)
                if (has_n and has_s) or (has_w and has_e):
                    grid.set(pos, Material.BRIDGE)
                    bridges_placed += 1

    def _place_road_network(self, region: Region, ridx: int, fidx: int) -> None:
        """Connect locations within a region with ROAD/BRIDGE paths."""
        grid = self._grid
        base_mat = region.terrain
        locs = region.locations
        if len(locs) < 2:
            return

        # Connect each location to its nearest neighbor (simple MST-like)
        connected: set[int] = {0}
        edges: list[tuple[int, int]] = []

        while len(connected) < len(locs):
            best_dist = float("inf")
            best_from = -1
            best_to = -1
            for ci in connected:
                for ti in range(len(locs)):
                    if ti in connected:
                        continue
                    d = locs[ci].pos.manhattan(locs[ti].pos)
                    if d < best_dist:
                        best_dist = d
                        best_from = ci
                        best_to = ti
            if best_to < 0:
                break
            connected.add(best_to)
            edges.append((best_from, best_to))

        # Draw L-shaped roads between connected locations
        for fi, ti in edges:
            fp = locs[fi].pos
            tp = locs[ti].pos
            self._draw_road_path(fp, tp, base_mat)

    def _draw_road_path(self, start: Vector2, end: Vector2, base_mat: Material) -> None:
        """Draw an L-shaped road/bridge path from start to end."""
        grid = self._grid
        x, y = start.x, start.y
        tx, ty = end.x, end.y

        # Horizontal first, then vertical
        step_x = 1 if tx > x else -1
        while x != tx:
            x += step_x
            pos = Vector2(x, y)
            if grid.in_bounds(pos):
                mat = grid.get(pos)
                if mat == Material.WATER:
                    grid.set(pos, Material.BRIDGE)
                elif mat == base_mat:
                    grid.set(pos, Material.ROAD)

        step_y = 1 if ty > y else -1
        while y != ty:
            y += step_y
            pos = Vector2(x, y)
            if grid.in_bounds(pos):
                mat = grid.get(pos)
                if mat == Material.WATER:
                    grid.set(pos, Material.BRIDGE)
                elif mat == base_mat:
                    grid.set(pos, Material.ROAD)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/systems/world/world_object_system.py
"""WorldObjectSystem handles resource nodes and treasure chests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class WorldObjectSystem(System):
    """System for managing world objects like resource nodes and chests."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute world object sub-phases."""
        self._tick_resource_nodes(context)
        self._tick_treasure_chests(context, tick)

    def _tick_resource_nodes(self, context: SystemContext) -> None:
        """Tick cooldowns on depleted resource nodes so they respawn."""
        for node in context.world.resource_nodes.values():
            node.tick_cooldown()

    def _tick_treasure_chests(self, context: SystemContext, tick: int) -> None:
        """Respawn looted treasure chests and their guards."""
        for chest in context.world.treasure_chests.values():
            if chest.try_respawn(tick):
                # Respawn guard if it was killed
                if chest.guard_entity_id is not None:
                    guard = context.world.entities.get(chest.guard_entity_id)
                    if guard is None or not guard.combat.alive:
                        self._spawn_chest_guard(context, chest)
                logger.info("Tick %d: Treasure chest %d respawned at %s (tier %d)",
                            tick, chest.chest_id, chest.spatial.pos, chest.identity.tier)

    def _spawn_chest_guard(self, context: SystemContext, chest: Any) -> None:
        """Spawn an elite guard entity next to a treasure chest."""
        from src.core.models.enums import EnemyTier
        from src.core.gameplay.items.items import TERRAIN_RACE
        
        world = context.world
        # Determine race from terrain at chest position
        mat = world.grid.material_at(chest.spatial.pos.x, chest.spatial.pos.y)
        race = TERRAIN_RACE.get(mat, "goblin")
        tier = min(chest.identity.tier + 1, EnemyTier.ELITE)  # Chest tier 1→WARRIOR, 2→ELITE, 3→ELITE
        
        entity = context.generator.spawn_race(
            world, race=race, tier=tier, near_pos=chest.spatial.pos)
        world.add_entity(entity)
        chest.guard_entity_id = entity.id
        logger.info("Tick %d: Spawned chest guard %s #%d at %s (tier %d)",
                    world.tick, entity.kind, entity.id, entity.spatial.pos, tier)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/utils/__init__.py
"""Utilities: logging setup and replay serialization."""

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/utils/event_log.py
"""Thread-safe ring buffer for simulation events exposed via the API."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SimEvent:
    """A single simulation event for the API event feed."""

    tick: int
    category: str
    message: str
    entity_ids: tuple[int, ...] = ()  # IDs of entities involved in this event
    metadata: dict | None = None      # Structured context (enhance-01)


class EventLog:
    """Capped ring-buffer event log. Writers append; readers snapshot a slice.

    Oldest events are evicted when *maxlen* is exceeded.
    Thread-safe via a simple lock — writes are rare (once per tick batch)
    and reads are non-blocking copies.
    """

    __slots__ = ("_buffer", "_lock")

    def __init__(self, maxlen: int = 10_000) -> None:
        self._buffer: deque[SimEvent] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def append(self, event: SimEvent) -> None:
        with self._lock:
            self._buffer.append(event)

    def append_many(self, events: list[SimEvent]) -> None:
        with self._lock:
            self._buffer.extend(events)

    def since_tick(self, tick: int) -> list[SimEvent]:
        """Return all events with tick >= *tick*."""
        with self._lock:
            return [e for e in self._buffer if e.tick >= tick]

    def latest(self, count: int = 50) -> list[SimEvent]:
        """Return the *count* most recent events."""
        with self._lock:
            items = list(self._buffer)
        return items[-count:]

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/utils/logging.py
import logging
import sys
import json
import threading
from datetime import datetime
from pythonjsonlogger import jsonlogger

# Thread-local storage for logging context
_log_context = threading.local()

def set_logging_context(**kwargs):
    """Set persistent context fields for the current thread's logs."""
    for key, value in kwargs.items():
        setattr(_log_context, key, value)

class ContextFilter(logging.Filter):
    """Filter that injects thread-local context into every LogRecord."""
    def filter(self, record):
        # We also support 'extra' passed directly to the log call
        # but thread-local takes precedence or provides fallbacks
        for attr in ('tick', 'component', 'worker_id', 'entity_id'):
            # Only set if not already present in the record (from 'extra')
            if not hasattr(record, attr):
                val = getattr(_log_context, attr, None)
                if val is not None:
                    setattr(record, attr, val)
        return True

class RobustLoggerAdapter(logging.LoggerAdapter):
    """Legacy wrapper, now just updates thread-local context before logging."""
    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            # Sync our extra to thread-local to support mixed usage
            set_logging_context(**self.extra)
            super().log(level, msg, *args, **kwargs)

class StructuredJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for RPG simulation logs."""
    
    def add_fields(self, log_record, record, message_dict):
        super(StructuredJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Capture all custom fields from the record __dict__
        standard_fields = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msg', 'name', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName', 'message', 'taskName'
        }
        for key, value in record.__dict__.items():
            if key not in standard_fields and not key.startswith('_'):
                log_record[key] = value

        if not log_record.get('timestamp'):
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
            
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
            
        if not log_record.get('component'):
            log_record['component'] = record.name

def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with a JSON formatter and ContextFilter."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.setFormatter(StructuredJsonFormatter('%(message)s'))
    
    # Add our context filter to the handler
    handler.addFilter(ContextFilter())

    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()
    root.addHandler(handler)
    
    # Silence chatty third-party loggers
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/utils/metrics.py
"""Prometheus metrics definitions for the RPG engine."""

from prometheus_client import Counter, Gauge, Histogram, Info

# --- HTTP Metrics ---

API_REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# --- Engine Metrics ---

SIM_TICK_DURATION = Histogram(
    "sim_tick_duration_seconds",
    "Time spent computing simulation ticks",
    ["phase"], # e.g. "scheduling", "resolve", "subsystems", "cleanup", "total"
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)

ACTIVE_ENTITIES = Gauge(
    "sim_active_entities",
    "Number of alive entities currently in the world"
)

TOTAL_SPAWNS = Counter(
    "sim_total_spawns",
    "Total entities spawned since boot"
)

TOTAL_DEATHS = Counter(
    "sim_total_deaths",
    "Total entities died since boot"
)

SIM_CURRENT_TICK = Gauge(
    "sim_current_tick",
    "Current simulation tick number"
)

SIM_TICKS_PER_SECOND = Gauge(
    "sim_ticks_per_second",
    "Actual simulation throughput in ticks per second"
)

SIM_WORLD_DIFFICULTY_MULT = Gauge(
    "sim_world_difficulty_mult",
    "Current global stat multiplier based on world age"
)

SIM_TOP_HERO_LEVEL = Gauge(
    "sim_top_hero_level",
    "Current highest hero level in the world"
)

SIM_TOP_HERO_GOLD = Gauge(
    "sim_top_hero_gold",
    "Current highest gold amount held by a single hero"
)

# --- Combat Metrics ---

SIM_COMBAT_EVENTS = Counter(
    "sim_combat_events_total",
    "Total combat events emitted",
    ["attacker_faction", "defender_faction"]
)

SIM_SKILL_EVENTS = Counter(
    "sim_skill_events_total",
    "Total skill usage events emitted",
    ["attacker_faction", "skill_name"]
)

# --- Worker & Queue Metrics ---

SIM_WORKER_DISPATCH_DURATION = Histogram(
    "sim_worker_dispatch_seconds",
    "Time to dispatch and collect AI decisions from workers",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
)

SIM_WORKER_ENTITIES_DISPATCHED = Counter(
    "sim_worker_entities_dispatched_total",
    "Total entities dispatched to AI workers"
)

SIM_ACTION_QUEUE_DEPTH = Gauge(
    "sim_action_queue_depth",
    "Current number of pending actions in the queue"
)

SIM_WORKER_HEALTH = Gauge(
    "sim_worker_health",
    "Health status of AI workers (1=OK, 0=Busy/Error)",
    ["worker_id", "state"] # state: "idle", "busy", "error"
)

# --- Infrastructure Metrics ---

SIM_REDIS_LATENCY = Histogram(
    "sim_redis_latency_seconds",
    "Latency of Redis operations by type",
    ["op"], # e.g. "publish", "get_state", "set_snapshot"
    buckets=[0.0005, 0.001, 0.005, 0.01, 0.05, 0.1]
)

SIM_REDIS_PUBLISH_DURATION = Histogram(
    "sim_redis_publish_seconds",
    "Time to publish state delta to Redis stream",
    buckets=[0.0005, 0.001, 0.005, 0.01, 0.05]
)

SIM_KAFKA_PUBLISH_DURATION = Histogram(
    "sim_kafka_publish_seconds",
    "Time to publish snapshot/events to Kafka",
    ["type"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1]
)

# --- Process Resource Metrics ---

PROCESS_CPU_PERCENT = Gauge(
    "process_cpu_percent",
    "Backend Python process CPU usage percentage"
)

PROCESS_MEMORY_RSS = Gauge(
    "process_memory_rss_bytes",
    "Backend Python process resident set size in bytes"
)

PROCESS_MEMORY_VMS = Gauge(
    "process_memory_vms_bytes",
    "Backend Python process virtual memory size in bytes"
)

PROCESS_THREAD_COUNT = Gauge(
    "process_thread_count",
    "Number of threads in the backend process"
)

# --- Simulation Depth Metrics ---

SIM_FACTION_POPULATION = Gauge(
    "sim_faction_population",
    "Current headcount per faction",
    ["faction"]
)

SIM_ENTITY_LEVEL_DISTRIBUTION = Gauge(
    "sim_entity_level_distribution",
    "Number of entities at each level bracket",
    ["kind", "level_bracket"] # e.g. "1-10", "11-20", etc.
)

SIM_HERO_CLASS_TOTAL = Gauge(
    "sim_hero_class_total",
    "Total heroes in each class and tier",
    ["hero_class", "tier"]
)

SIM_GOLD_CIRCULATION_TOTAL = Gauge(
    "sim_gold_circulation_total",
    "Total gold held by all entities in a faction",
    ["faction"]
)

SIM_BUILDING_DURABILITY_PERCENT = Gauge(
    "sim_building_durability_percent",
    "Health of town infrastructure (0-100)",
    ["building_id"]
)

SIM_QUEST_STATUS_TOTAL = Counter(
    "sim_quest_status_total",
    "Tracking GATHER/HUNT/EXPLORE success/failure rates",
    ["type", "status"] # e.g. "hunt", "completed"
)

SIM_ITEMS_CRAFTED_TOTAL = Counter(
    "sim_items_crafted_total",
    "Tracking blacksmith activity and gear quality",
    ["item_id", "tier"]
)

SIM_SHOP_TRANSACTIONS_TOTAL = Counter(
    "sim_shop_transactions_total",
    "Tracking general store buy/sell volume",
    ["type", "item_id"] # type: "buy" or "sell"
)

SIM_CALAMITY_ACTIVE = Gauge(
    "sim_calamity_active",
    "1 if a world boss is active, 0 otherwise",
    ["region_id"]
)

# --- Admin & Diagnostic Metrics ---

SIM_ERRORS_TOTAL = Counter(
    "sim_errors_total",
    "Caught exceptions in world loop, AI, or networking",
    ["exception_type", "component"]
)

SIM_INVALID_ACTIONS_TOTAL = Counter(
    "sim_invalid_actions_total",
    "Actions proposed by AI that failed validation",
    ["action_type", "reason"]
)

SIM_STATE_TRANSITION_FAILURES = Counter(
    "sim_state_transition_failures_total",
    "Failures in AI state logic transitions",
    ["from_state", "to_state"]
)

# NOTE: SIM_TICK_DURATION already exists at line 16, but we will use the "phase" label heavily.

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/utils/replay.py
"""Replay serialization — records tick-by-tick events for deterministic replay."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.actions.base import ActionProposal
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)


class ReplayRecorder:
    """Accumulates tick events and flushes to a JSON replay file."""

    __slots__ = ("_path", "_ticks", "_seed")

    def __init__(self, path: str | Path, seed: int) -> None:
        self._path = Path(path)
        self._seed = seed
        self._ticks: list[dict[str, Any]] = []

    def record_tick(
        self,
        tick: int,
        applied_actions: list[ActionProposal],
        world: WorldState,
    ) -> None:
        entities_snapshot = [
            {
                "id": e.id,
                "kind": e.kind,
                "pos": [e.spatial.pos.x, e.spatial.pos.y],
                "hp": e.stats.combat.hp,
                "state": e.mind.ai_state.name,
            }
            for e in world.entities.values()
            if e.combat.alive
        ]
        actions_log = [
            {
                "actor": a.actor_id,
                "verb": a.verb.name,
                "target": (
                    [a.target.x, a.target.y]
                    if hasattr(a.target, "x")
                    else a.target
                ),
                "reason": a.reason,
            }
            for a in applied_actions
        ]

        self._ticks.append(
            {
                "tick": tick,
                "actions": actions_log,
                "entities": entities_snapshot,
            }
        )

    def flush(self) -> None:
        """Write accumulated data to disk."""
        replay = {
            "version": "1.0",
            "seed": self._seed,
            "total_ticks": len(self._ticks),
            "ticks": self._ticks,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(replay, indent=2), encoding="utf-8")
        logger.info("Replay saved to %s (%d ticks)", self._path, len(self._ticks))

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/utils/resource_collector.py
"""Background thread that periodically updates process resource metrics."""

from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)

_collector_thread: threading.Thread | None = None


def start_resource_collector(interval: float = 2.0) -> None:
    """Launch a daemon thread that updates CPU/RAM gauges every *interval* seconds."""
    global _collector_thread
    if _collector_thread is not None:
        return  # Already running

    def _collect_loop() -> None:
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not installed — resource metrics disabled.")
            return

        from src.utils.metrics import (
            PROCESS_CPU_PERCENT,
            PROCESS_MEMORY_RSS,
            PROCESS_MEMORY_VMS,
            PROCESS_THREAD_COUNT,
        )

        proc = psutil.Process()
        # Prime CPU measurement (first call always returns 0.0)
        proc.cpu_percent(interval=None)

        while True:
            try:
                PROCESS_CPU_PERCENT.set(proc.cpu_percent(interval=None))
                mem = proc.mind.memory_info()
                PROCESS_MEMORY_RSS.set(mem.rss)
                PROCESS_MEMORY_VMS.set(mem.vms)
                PROCESS_THREAD_COUNT.set(proc.num_threads())
            except Exception:
                logger.debug("Resource collection tick failed", exc_info=True)

            time.sleep(interval)

    _collector_thread = threading.Thread(target=_collect_loop, daemon=True, name="resource-collector")
    _collector_thread.start()
    logger.info("Resource collector started (interval=%.1fs)", interval)

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/utils/watchdog.py
import os
import time
import logging
import requests
from typing import Dict, Any

# Configure logging to flow into the same JSON telemetry stream
from src.utils.logging import setup_logging
setup_logging(os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("watchdog")

# Configuration from environment
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "10"))

class SimulationWatchdog:
    """Persistent monitor that audits the simulation stack's health."""
    
    def __init__(self):
        self.last_tick = -1
        self.consecutive_failures = 0
        self.max_failures = 3
        logger.info("Watchdog initialized. Targets: Backend=%s, Loki=%s", BACKEND_URL, LOKI_URL)

    def check_health(self) -> bool:
        """Poll the /health endpoint."""
        try:
            resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if resp.status_code == 200:
                return True
            logger.error("Health check failed: HTTP %d", resp.status_code)
        except Exception as e:
            logger.error("Health check exception: %s", e)
        return False

    def check_metrics(self) -> tuple[bool, str]:
        """Poll metrics to ensure the simulation is actually ticking."""
        try:
            resp = requests.get(f"{BACKEND_URL}/metrics", timeout=5)
            if resp.status_code != 200:
                return False, f"Metrics HTTP {resp.status_code}"
            
            # Find sim_current_tick in Prometheus text format
            for line in resp.text.splitlines():
                if line.startswith("sim_current_tick"):
                    curr_tick = float(line.split()[1])
                    if curr_tick > self.last_tick:
                        self.last_tick = curr_tick
                        return True, f"Tick {curr_tick}"
                    elif curr_tick == self.last_tick:
                        if curr_tick == 0:
                            return True, "Tick 0 (Starting)"
                        return False, f"Tick Stalled at {curr_tick}"
            return True, "Metric Not Found (Pending)"
        except Exception as e:
            return False, f"Metrics Error: {str(e)[:50]}"

    def check_loki_errors(self) -> list[str]:
        """Query Loki for any error/fail logs and return specific messages."""
        try:
            query = '{level=~"(?i)error|critical", component!="watchdog"}'
            end_time = int(time.time() * 1e9)
            start_time = end_time - (POLL_INTERVAL * 2 * 10**9)
            
            params = {'query': query, 'start': start_time, 'end': end_time, 'limit': 3}
            resp = requests.get(f"{LOKI_URL}/loki/api/v1/query_range", params=params, timeout=5)
            if resp.status_code == 200:
                results = resp.json().get('data', {}).get('result', [])
                error_msgs = []
                for res in results:
                    container = res.get('stream', {}).get('container', 'unknown')
                    container = container.replace('/rpg-based-simulation-', '').replace('-1', '')
                    for val in res.get('values', []):
                        try:
                            # Log content is usually the second element in the value array
                            error_msgs.append(f"[{container}] {val[1][:150]}")
                        except: pass
                return error_msgs
        except Exception as e:
            logger.error("Loki query exception: %s", e)
        return []

    def run_cycle(self):
        """Execute one full monitoring cycle with detailed reasons."""
        health_ok = self.check_health()
        metrics_ok, metrics_reason = self.check_metrics()
        errors = self.check_loki_errors()

        status_report = {
            "health": "OK" if health_ok else "FAIL",
            "metrics": metrics_reason,
            "error_count": len(errors),
            "sample_errors": errors[:2]
        }

        if not health_ok or not metrics_ok or errors:
            self.consecutive_failures += 1
            logger.warning("Watchdog detected anomaly: %s. Failure count: %d", 
                         status_report, self.consecutive_failures)
        else:
            if self.consecutive_failures > 0:
                logger.info("Watchdog recovered. Status: %s", status_report)
            else:
                logger.info("Watchdog Health Check OK: %s", status_report)
            self.consecutive_failures = 0

        if self.consecutive_failures >= self.max_failures:
            logger.critical("SYSTEM_CRITICAL: Persistent failure! Reason: %s",
                          status_report, extra={'component': 'watchdog', 'diagnostics': status_report})

    def start(self):
        """Main loop."""
        while True:
            try:
                self.run_cycle()
            except Exception as e:
                logger.error("Watchdog loop error: %s", e)
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    watchdog = SimulationWatchdog()
    watchdog.start()

#####

# D:/Non-Working/Projects/rpg-based-simulation-rpg_core/src/workers/ai_worker_daemon.py
import logging
import os
import pickle
import time
from typing import Any

import pika

from src.ai.brain import AIBrain
from src.config import SimulationConfig
from src.core.gameplay.faction import FactionRegistry
from src.platform.rng import DeterministicRNG

from src.utils.logging import setup_logging
setup_logging(os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ai_worker")

class AIWorkerDaemon:
    """Daemon that listens for broadcast snapshots and processes AI tasks."""
    
    def __init__(self):
        self.config = SimulationConfig()
        # The AI Brain is stateless, we can instantiate one per worker
        self.rng = DeterministicRNG(seed=999) # Seed doesn't deeply matter here because RNG is Domain-based with tick/eid seeds
        self.brain = AIBrain(self.config, self.rng, FactionRegistry.default())
        
        # Wrapped logger (Phase L3 Logging)
        self.worker_id = f"worker_{os.getpid()}"
        from src.utils.logging import RobustLoggerAdapter
        self._logger = RobustLoggerAdapter(logger, {'component': 'ai_worker', 'worker_id': self.worker_id, 'tick': -1})
        
        # Local state
        self.current_tick: int = -1
        self.current_snapshot: Any | None = None
        
        # RabbitMQ setup
        url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        parameters = pika.URLParameters(url)
        parameters.heartbeat = 600
        parameters.blocked_connection_timeout = 300
        
        while True:
            try:
                self.conn = pika.BlockingConnection(parameters)
                self.channel = self.conn.channel()
                self._logger.info("Worker successfully connected to RabbitMQ at %s", url)
                break
            except Exception as e:
                self._logger.error("Waiting for RabbitMQ... %s", e)
                time.sleep(2)
        
        # 1. Setup Snapshot Broadcast (Fanout)
        self.channel.exchange_declare(exchange='ai_snapshots', exchange_type='fanout')
        # Exclusive queue bound to fanout exchange so it gets deleted if worker dies
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.snapshot_queue_name = result.method.queue
        self.channel.queue_bind(exchange='ai_snapshots', queue=self.snapshot_queue_name)
        
        # 2. Setup Task Queue (Direct/Round robin)
        self.channel.queue_declare(queue='ai_tasks', durable=False)
        self.channel.basic_qos(prefetch_count=10) # Process 10 tasks at a time
        
        # 3. Setup Results Queue (Direct back to engine)
        self.channel.queue_declare(queue='ai_results', durable=False)
        
        # 4. Setup Isolated Chaos Queues for throughput testing
        self.channel.queue_declare(queue='ai_tasks_test', durable=False)
        self.channel.queue_declare(queue='ai_results_test', durable=False)

    def on_snapshot(self, ch, method, properties, body):
        """Receive pickled snapshot from main engine."""
        try:
            snapshot = pickle.loads(body)
            self.current_snapshot = snapshot
            self.current_tick = snapshot.tick
            self._logger.debug("Worker received Snapshot for tick %d", snapshot.tick, extra={'tick': snapshot.tick})
        except Exception as e:
            self._logger.error("Failed to unpickle snapshot: %s", e)

    def on_task(self, ch, method, properties, body):
        """Receive a batch of entity tasks."""
        try:
            batch = pickle.loads(body)
            tick = batch["tick"]
            entity_ids = batch["entity_ids"]
            self._logger.info("Worker received Batch for tick %d (%d entities)", tick, len(entity_ids))
            
            if tick > self.current_tick:
                self._logger.warning("Batch for tick %d arrived before snapshot (current %d). Requeueing.", tick, self.current_tick)
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                return
            if tick < self.current_tick:
                self._logger.debug("Obsolete batch for tick %d (current %d)", tick, self.current_tick)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            if not self.current_snapshot:
                self._logger.warning("No snapshot available for batch at tick %d", tick)
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                return

            results = []
            for eid in entity_ids:
                res = self._process_single_entity(eid, tick)
                results.append(res)
                
            self._send_batch_result(tick, results)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self._logger.error("Failed to process batch task: %s", e)
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

    def _process_single_entity(self, entity_id: int, tick: int) -> dict:
        """Helper to run AI for a single ID within a batch."""
        entity = self.current_snapshot.entities.get(entity_id)
        if not entity or not entity.combat.alive:
            return {"entity_id": entity_id, "new_state": None, "proposal": None}
            
        try:
            from dataclasses import replace
            new_state, proposal = self.brain.decide(entity, self.current_snapshot)
            proposal = replace(proposal, new_ai_state=int(new_state))
            return {
                "entity_id": entity_id,
                "new_state": int(new_state),
                "proposal": proposal
            }
        except Exception as e:
            self._logger.exception("AI crashed for entity %d", entity_id, extra={'tick': tick})
            return {"entity_id": entity_id, "new_state": None, "proposal": None}

    def _send_batch_result(self, tick: int, results: list[dict]):
        """Send the batched results back to engine."""
        payload = {
            "tick": tick,
            "results": results
        }
        self.channel.basic_publish(
            exchange='',
            routing_key='ai_results',
            body=pickle.dumps(payload)
        )

    def on_test_task(self, ch, method, properties, body):
        """Blindly reflect chaos test payloads to simulate rapid physical queue consumption."""
        try:
            self.channel.basic_publish(exchange='', routing_key='ai_results_test', body=body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self._logger.error("Chaos test bounce failed: %s", e)
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

    def run(self):
        """Start consuming."""
        self.channel.basic_consume(
            queue=self.snapshot_queue_name, 
            on_message_callback=self.on_snapshot, 
            auto_ack=True
        )
        self.channel.basic_consume(
            queue='ai_tasks', 
            on_message_callback=self.on_task,
            auto_ack=False
        )
        self.channel.basic_consume(
            queue='ai_tasks_test', 
            on_message_callback=self.on_test_task,
            auto_ack=False
        )
        
        self._logger.info("AI Worker Daemon started, listening for tasks...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.conn.close()

if __name__ == "__main__":
    daemon = AIWorkerDaemon()
    daemon.run()
