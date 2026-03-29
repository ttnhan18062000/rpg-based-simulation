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
            .identity.faction(Faction.HERO_GUILD)
            .identity.role(EntityRole.HERO)
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
