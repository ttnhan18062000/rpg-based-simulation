from __future__ import annotations
import logging
import time
from typing import List, Dict, Any, Optional

from src.core.models.arena import Scenario, ParticipantProfile, ArenaResult, ScenarioReport
from src.core.models.enums import ArenaStopCondition, EntityRole, Faction, Domain
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.engine.world_loop import WorldLoop
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.ai.brain import AIBrain
from src.core.gameplay.faction import FactionRegistry
from src.systems.world.generator import EntityGenerator
from src.core.entities.entity_builder import EntityBuilder
from src.engine.arena.metrics import MetricService

logger = logging.getLogger(__name__)

class ArenaRunner:
    """Authoritative runner for Milestone 6 Arena Scenarios.
    
    Provides deterministic, headless execution of combat/movement scenarios
    with statistical aggregation over multiple iterations.
    """
    
    def __init__(self, config: SimulationConfig):
        # Force strict determinism and isolation for arena runs
        from dataclasses import replace
        self.base_config = replace(config,
            num_workers=1,
            max_ticks=1000,
            log_level=config.log_level if config.log_level != "INFO" else "WARNING"
        )
        # Disable infrastructure via environment (AOA Barrier Implementation)
        import os
        os.environ["DISABLE_KAFKA"] = "1"
        os.environ["DISABLE_RABBITMQ"] = "1"
        os.environ["DISABLE_REDIS"] = "1"

    def run_scenario(self, scenario: Scenario) -> ScenarioReport:
        """Execute all iterations of a scenario and aggregate results. [Milestone 6]"""
        results: List[ArenaResult] = []
        
        # Scenario-root seed derived from ID for cross-version stability
        # We use a simple hash of the scenario ID as the root seed if not provided
        root_seed = self.base_config.world_seed
        
        for i in range(scenario.iterations):
            # Deriving distinct but stable iteration seeds
            iter_seed = root_seed + (i * 1000)
            res = self._run_iteration(scenario, i, iter_seed)
            results.append(res)
            
        return self._aggregate(scenario, results)

    def _run_iteration(self, scenario: Scenario, iteration: int, seed: int) -> ArenaResult:
        """Single deterministic execution of a scenario. [Milestone 6]"""
        rng = DeterministicRNG(seed)
        grid = Grid(scenario.grid_width, scenario.grid_height)
        
        # Apply materials from scenario (e.g. walls for chokepoints)
        for mat_name, positions in scenario.grid_materials.items():
            from src.core.models.enums import Material
            try:
                mat = Material[mat_name.upper()]
                for pos in positions:
                    from src.core.models.vectors import Vector2
                    pos_v = Vector2.from_any(pos)
                    if grid.in_bounds(pos_v):
                        grid.set(pos_v, mat)
            except (KeyError, ValueError):
                logger.warning("Invalid material name in scenario: %s", mat_name)
                    
        spatial = SpatialHash(self.base_config.spatial_cell_size)
        world = WorldState(seed=seed, grid=grid, spatial_index=spatial)
        
        # Setup Registries
        faction_reg = FactionRegistry.default()
        generator = EntityGenerator(self.base_config, rng)
        
        # Spawn Participants
        for idx, profile in enumerate(scenario.participants):
            pos = scenario.initial_placements[idx]
            eid = world.allocate_entity_id()
            
            builder = (
                EntityBuilder(rng, eid, tick=0)
                .kind(profile.kind)
                .at(pos)
                .home(pos) # Anchor for leash-based behaviors
                .faction(profile.faction)
                .role(profile.role)
            )
            
            if profile.hero_class:
                builder.with_hero_class(profile.hero_class)
                builder.with_class_skills(profile.hero_class, level=profile.level)
            
            ent = builder.build()
            
            # Apply individual overrides for fine-grain tuning
            if profile.hp_over is not None: 
                ent.combat.max_hp = profile.hp_over
                ent.combat.hp = profile.hp_over
            if profile.atk_over is not None: 
                ent.combat.atk_base = profile.atk_over
            if profile.spd_over is not None: 
                ent.combat.spd_base = profile.spd_over
            
            # General attribute/progression overrides
            for k, v in profile.stat_overrides.items():
                if hasattr(ent.combat, k):
                    setattr(ent.combat, k, v)
                elif hasattr(ent.progression, k):
                    setattr(ent.progression, k, v)
            
            world.add_entity(ent)

        # Setup Engine Components
        brain = AIBrain(self.base_config, rng, faction_reg)
        worker_pool = WorkerPool(self.base_config, brain, rng)
        conflict_resolver = ConflictResolver(self.base_config, rng)
        
        loop = WorldLoop(
            config=self.base_config,
            world=world,
            worker_pool=worker_pool,
            conflict_resolver=conflict_resolver,
            generator=generator,
            faction_reg=faction_reg,
            rng=rng
        )
        
        # simplified execution loop with StopCondition monitoring
        stop_reason = ArenaStopCondition.TIMEOUT
        ticks = 0
        
        # Calculate initial faction count for wipe detection logic
        initial_factions = set()
        for ent in world.entities.values():
            if ent.kind != "generator":
                initial_factions.add(ent.identity.faction)
        initial_faction_count = len(initial_factions)
        
        # Stall tracking state
        stagnant_ticks = 0
        recent_hps = {e.id: e.combat.hp for e in world.entities.values()}
        
        # Pillar 6: Harden coordinate extraction against dict-based positions
        from src.core.models.vectors import Vector2
        recent_positions = {}
        for e in world.entities.values():
            pos = Vector2.from_any(e.spatial.pos)
            recent_positions[e.id] = (pos.x, pos.y)
        
        # Performance Monitoring: Track resource growth per iteration
        try:
            import psutil
            process = psutil.Process()
            start_rss = process.memory_info().rss
            start_cpu = process.cpu_times()
        except (ImportError, Exception):
            start_rss = None
            start_cpu = None
            process = None

        try:
            while ticks < scenario.max_ticks:
                # Stall Detection (Activity check every 5 ticks)
                if ticks > 0 and ticks % 5 == 0:
                    is_stagnant = MetricService.detect_stall(world, recent_hps, recent_positions)
                    if is_stagnant:
                        stagnant_ticks += 5
                    else:
                        stagnant_ticks = 0
                    
                    # Refresh activity snapshots
                    recent_hps = {e.id: e.combat.hp for e in world.entities.values()}
                    recent_positions = {}
                    for e in world.entities.values():
                        pos = Vector2.from_any(e.spatial.pos)
                        recent_positions[e.id] = (pos.x, pos.y)
                
                # 100 ticks of zero activity = STALL
                if stagnant_ticks >= 100:
                    stop_reason = ArenaStopCondition.STALL
                    break

                # Check Stop Conditions (Faction Wipes)
                reason = self._check_stop_conditions(world, scenario, ticks, initial_faction_count)
                if reason is not None:
                    stop_reason = reason
                    break
                    
                if not loop.tick_once():
                    # Check conditions one last time after the final tick
                    last_reason = self._check_stop_conditions(world, scenario, ticks)
                    if last_reason:
                        stop_reason = last_reason
                    break
                ticks += 1
                
                # Tier 3 Protection: Active Memory Guard
                # Raise error if current iteration leaks more than 300MB mid-run
                if process and ticks % 10 == 0:
                    current_rss = process.memory_info().rss
                    delta_mb = (current_rss - start_rss) / (1024 * 1024)
                    DELTA_LIMIT_MB = 600 # 600MB safety delta [Milestone 7 Hardening]
                    if delta_mb > DELTA_LIMIT_MB:
                        raise RuntimeError(f"Arena Iteration {iteration} exceeded safety memory delta: {delta_mb:.1f}MB > {DELTA_LIMIT_MB}MB. Aborting scenario.")

                if ticks % 100 == 0:
                    logger.info("Arena Iteration %d: Tick %d...", iteration, ticks)

            # Determine winner based on survivor faction
            winner = self._determine_winner(world)
            deaths = [e.id for e in world.entities.values() if not e.combat.alive]
            
            result = ArenaResult(
                iteration=iteration,
                winner_faction=winner,
                ticks=ticks,
                stop_reason=stop_reason,
                deaths=deaths
            )
            
            # Post-iteration resource check
            if process and start_rss is not None and start_cpu is not None:
                end_info = process.memory_info()
                end_cpu = process.cpu_times()
                
                delta_mb = (end_info.rss - start_rss) / (1024 * 1024)
                # Combined User/System time
                delta_cpu = (end_cpu.user + end_cpu.system) - (start_cpu.user + start_cpu.system)
                
                # We expect roughly < 2s for 1000 ticks in headless arena
                avg_ms_per_tick = (delta_cpu * 1000) / max(1, ticks)
                
                if delta_mb > 50: # Threshold for a single iteration leak
                    logger.warning("Arena Iteration %d leaked %.2f MB", iteration, delta_mb)
                
                if delta_cpu > 5.0: # 5 seconds for a single iteration is very slow for arena
                    logger.warning("Arena Iteration %d occupied too much CPU: %.2fs (%.2fms/tick)", 
                                   iteration, delta_cpu, avg_ms_per_tick)
            
            return result
        finally:
            # Hermetic Cleanup: Ensure worker pools and systems are closed 
            # to prevent memory leaks and resource exhaustion between iterations.
            if hasattr(loop, "shutdown"):
                loop.shutdown()
            
            worker_pool.shutdown()
            
            # Explicitly clear large data structures [Hardening]
            # Use local names to avoid UnboundLocalError if loop/worker_pool init failed
            if 'world' in locals() and world:
                world.shutdown()
            
            if 'loop' in locals(): del loop
            if 'worker_pool' in locals(): del worker_pool
            if 'world' in locals(): del world
            if 'grid' in locals(): del grid
            if 'spatial' in locals(): del spatial
            if 'rng' in locals(): del rng
            
            import gc
            # Pillar 6: Full generation collection to reclaim cyclic structures broken by weakref
            gc.collect(2)

    def _check_stop_conditions(self, world: WorldState, scenario: Scenario, ticks: int, initial_faction_count: int = 2) -> Optional[ArenaStopCondition]:
        """Detect scenario-specific termination. [Milestone 6]"""
        
        # Predefined Check: Faction Wipe
        alive_factions = set()
        for ent in world.entities.values():
            if ent.combat.alive and ent.kind != "generator":
                alive_factions.add(ent.identity.faction)
        
        # WIPE logic: 
        # 1. More than one faction started, now only one (or zero) left.
        # 2. Only one faction started, now zero left.
        if len(alive_factions) < initial_faction_count:
            if len(alive_factions) <= 1:
                return ArenaStopCondition.WIPE
            
        # Optional: Stall Detection (To be enhanced in Task 3)
        # We could track damage history, if no damage for N ticks, STALL.
        
        return None

    def _determine_winner(self, world: WorldState) -> Optional[Faction]:
        """Identify the faction that owns the field."""
        alive = [ent for ent in world.entities.values() if ent.combat.alive and ent.kind != "generator"]
        if not alive:
            return None
        
        surviving_factions = set(ent.identity.faction for ent in alive)
        if len(surviving_factions) == 1:
            return list(surviving_factions)[0]
        
        # If multiple factions survive (Timeout/Stall), no clear winner
        return None

    def _aggregate(self, scenario: Scenario, results: List[ArenaResult]) -> ScenarioReport:
        """Calculate statistical patterns across all iterations. [Milestone 6]"""
        total = len(results)
        if total == 0:
            return ScenarioReport(scenario_id=scenario.id, total_iterations=0, win_rates={}, avg_ticks=0, stall_rate=0, avg_damage=0)

        win_counts: Dict[str, int] = {}
        total_ticks = 0
        stalls = 0
        
        for res in results:
            wf = res.winner_faction
            if wf is not None:
                # Faction enum values can be logged by name
                if hasattr(wf, "name"):
                    fname = wf.name
                else:
                    # Fallback for serialized/coerced values
                    from src.core.models.enums import Faction
                    try:
                        fname = Faction(wf).name if not isinstance(wf, str) else wf
                    except (ValueError, TypeError):
                        fname = str(wf)
                win_counts[fname] = win_counts.get(fname, 0) + 1
            
            total_ticks += res.ticks
            if res.stop_reason == ArenaStopCondition.STALL:
                stalls += 1
        # Dominant stop reason (heuristic: if any iteration stalled, report STALL)
        dominant_reason = ArenaStopCondition.TIMEOUT
        if stalls > 0:
            dominant_reason = ArenaStopCondition.STALL
        elif results:
            # Otherwise use the most frequent reason
            from collections import Counter
            reasons = [res.stop_reason for res in results]
            dominant_reason = Counter(reasons).most_common(1)[0][0]

        return ScenarioReport(
            scenario_id=scenario.id,
            total_iterations=total,
            win_rates={k: v/total for k, v in win_counts.items()},
            avg_ticks=total_ticks / total,
            stall_rate=stalls / total,
            avg_damage=0.0, # Placeholder for Task 3 damage tracking
            stop_reason=dominant_reason
        )
