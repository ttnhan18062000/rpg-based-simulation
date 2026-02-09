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
    from src.core.enums import AIState, Domain, EnemyTier, Material
    from src.core.grid import Grid
    from src.core.items import Inventory
    from src.core.models import Entity, Stats, Vector2
    from src.core.world_state import WorldState
    from src.engine.conflict_resolver import ConflictResolver
    from src.engine.worker_pool import WorkerPool
    from src.engine.world_loop import WorldLoop
    from src.systems.generator import EntityGenerator
    from src.systems.rng import DeterministicRNG
    from src.systems.spatial_hash import SpatialHash
    from src.utils.logging import setup_logging
    from src.utils.replay import ReplayRecorder

    config = SimulationConfig(
        world_seed=args.seed,
        max_ticks=args.ticks,
        initial_entity_count=args.entities,
        num_workers=args.workers,
        replay_file=args.replay,
        log_level=args.log_level,
    )

    setup_logging(config.log_level)

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

    # Spawn hero with attributes, class, and skills
    from src.core.attributes import Attributes, AttributeCaps
    from src.core.classes import (
        HeroClass, CLASS_DEFS, RACE_SKILLS, SKILL_DEFS, SkillInstance,
        available_class_skills,
    )

    hero_eid = world.allocate_entity_id()
    base_hp = 50 + rng.next_int(Domain.SPAWN, hero_eid, 2, 0, 15)
    base_atk = 10 + rng.next_int(Domain.SPAWN, hero_eid, 3, 0, 4)
    base_spd = 10 + rng.next_int(Domain.SPAWN, hero_eid, 4, 0, 3)
    base_def = 3 + rng.next_int(Domain.SPAWN, hero_eid, 5, 0, 2)

    class_choices = [HeroClass.WARRIOR, HeroClass.RANGER, HeroClass.MAGE, HeroClass.ROGUE]
    hero_class = class_choices[rng.next_int(Domain.SPAWN, hero_eid, 6, 0, 3)]
    cdef = CLASS_DEFS[hero_class]

    hero_attrs = Attributes(
        str_=5 + cdef.str_bonus, agi=5 + cdef.agi_bonus, vit=5 + cdef.vit_bonus,
        int_=5 + cdef.int_bonus, wis=5 + cdef.wis_bonus, end=5 + cdef.end_bonus,
    )
    hero_caps = AttributeCaps(
        str_cap=15 + cdef.str_cap_bonus, agi_cap=15 + cdef.agi_cap_bonus,
        vit_cap=15 + cdef.vit_cap_bonus, int_cap=15 + cdef.int_cap_bonus,
        wis_cap=15 + cdef.wis_cap_bonus, end_cap=15 + cdef.end_cap_bonus,
    )
    hero_stamina = 50 + hero_attrs.end * 2

    hero_skills: list[SkillInstance] = []
    for sid in RACE_SKILLS.get("hero", []):
        if sid in SKILL_DEFS:
            hero_skills.append(SkillInstance(skill_id=sid))
    for sid in available_class_skills(hero_class, 1):
        hero_skills.append(SkillInstance(skill_id=sid))

    hero_inv = Inventory(
        items=[], max_slots=config.hero_inventory_slots,
        max_weight=config.hero_inventory_weight,
        weapon="iron_sword", armor="leather_vest",
    )
    for _ in range(3):
        hero_inv.add_item("small_hp_potion")
    hero = Entity(
        id=hero_eid, kind="hero", pos=Vector2(config.town_center_x, config.town_center_y),
        stats=Stats(
            hp=base_hp, max_hp=base_hp, atk=base_atk, def_=base_def,
            spd=base_spd, luck=3, crit_rate=0.08, crit_dmg=1.8,
            evasion=0.03, level=1, xp=0, xp_to_next=100, gold=50,
            stamina=hero_stamina, max_stamina=hero_stamina,
        ),
        ai_state=AIState.WANDER, next_act_at=0.0,
        home_pos=town_center, inventory=hero_inv,
        attributes=hero_attrs, attribute_caps=hero_caps,
        hero_class=int(hero_class), skills=hero_skills,
    )
    world.add_entity(hero)

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

    brain = AIBrain(config, rng)
    worker_pool = WorkerPool(config, brain)
    conflict_resolver = ConflictResolver(config, rng)
    recorder = ReplayRecorder(config.replay_file, config.world_seed)

    loop = WorldLoop(
        config=config, world=world, worker_pool=worker_pool,
        conflict_resolver=conflict_resolver, generator=generator, recorder=recorder,
    )

    try:
        loop.run()
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
