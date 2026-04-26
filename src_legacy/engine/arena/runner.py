from __future__ import annotations
import logging
import time
import threading
from typing import List, Dict, Any, Optional

from src_legacy.core.models.arena import Scenario, ParticipantProfile, ArenaResult, ScenarioReport
from src_legacy.core.models.enums import ArenaStopCondition, EntityRole, Faction, Domain
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.world.grid import Grid
from src_legacy.platform.spatial_hash import SpatialHash
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.config import SimulationConfig
from src_legacy.engine.world_loop import WorldLoop
from src_legacy.engine.conflict_resolver import ConflictResolver
from src_legacy.engine.worker_pool import WorkerPool
from src_legacy.ai.brain import AIBrain
from src_legacy.core.gameplay.faction import FactionRegistry
from src_legacy.systems.world.generator import EntityGenerator
from src_legacy.core.entities.entity_builder import EntityBuilder
from src_legacy.engine.arena.metrics import MetricService

logger = logging.getLogger(__name__)

class WatchdogTimeoutError(RuntimeError):
    """Raised when a single simulation tick takes too long in real-time. [Milestone 6]"""
    pass

class ArenaWatchdog:
    """Background monitoring for simulation hangs. [Milestone 6]"""
    def __init__(self, timeout: float):
        self.timeout = timeout
        self.last_tick_time = 0.0
        self.running = False
        self._thread = None

    def start(self) -> None:
        self.last_tick_time = time.time()
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="ArenaWatchdog")
        self._thread.start()

    def stop(self) -> None:
        self.running = False

    def poke(self) -> None:
        """Mark a logical tick as completed."""
        self.last_tick_time = time.time()

    def _run(self) -> None:
        while self.running:
            elapsed = time.time() - self.last_tick_time
            if elapsed > self.timeout:
                logger.error("WATCHDOG: Tick exceeded real-time limit of %.1fs (Elapsed: %.1fs). Aborting.", self.timeout, elapsed)
                import _thread
                # Elevate to main thread to break infinite loops
                _thread.interrupt_main()
                break
            time.sleep(min(0.5, self.timeout / 4))

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
        # 1. Initialize heavy refs to None [Milestone 6 Defensive Pattern]
        rng = None
        grid = None
        spatial = None
        world = None
        worker_pool = None
        loop = None
        watchdog = None
        
        # Resource tracking
        start_stats = MetricService.record_usage_stats()
        peak_rss = start_stats["rss_mb"]

        try:
            rng = DeterministicRNG(seed)
            grid = Grid(scenario.grid_width, scenario.grid_height)
            
            # Apply materials from scenario
            for mat_name, positions in scenario.grid_materials.items():
                from src_legacy.core.models.enums import Material
                try:
                    mat = Material[mat_name.upper()]
                    for pos in positions:
                        from src_legacy.core.models.vectors import Vector2
                        pos_v = Vector2.from_any(pos)
                        if grid.in_bounds(pos_v):
                            grid.set(pos_v, mat)
                except (KeyError, ValueError):
                    logger.warning("Invalid material name in scenario: %s", mat_name)
                        
            spatial = SpatialHash(self.base_config.spatial_cell_size)
            world = WorldState(seed=seed, grid=grid, spatial_index=spatial)
            
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
                    .home(pos)
                    .faction(profile.faction)
                    .role(profile.role)
                )
                
                if profile.hero_class:
                    builder.with_hero_class(profile.hero_class)
                    builder.with_class_skills(profile.hero_class, level=profile.level)
                
                ent = builder.build()
                
                if profile.hp_over is not None: 
                    ent.combat.max_hp = profile.hp_over
                    ent.combat.hp = profile.hp_over
                if profile.atk_over is not None: 
                    ent.combat.atk_base = profile.atk_over
                if profile.spd_over is not None: 
                    ent.combat.spd_base = profile.spd_over
                
                for k, v in profile.stat_overrides.items():
                    if hasattr(ent.combat, k):
                        setattr(ent.combat, k, v)
                    elif hasattr(ent.progression, k):
                        setattr(ent.progression, k, v)
                
                world.add_entity(ent)

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
            
            # Watchdog initialization (Milestone 6)
            timeout = getattr(self.base_config, "watchdog_timeout", 2.0)
            watchdog = ArenaWatchdog(timeout)
            watchdog.start()

            stop_reason = ArenaStopCondition.TIMEOUT
            ticks = 0
            
            initial_factions = set(e.identity.faction for e in world.entities.values() if e.kind != "generator")
            initial_faction_count = len(initial_factions)
            stagnant_ticks = 0
            recent_hps = {e.id: e.combat.hp for e in world.entities.values()}
            
            from src_legacy.core.models.vectors import Vector2
            recent_positions = {e.id: (Vector2.from_any(e.spatial.pos).x, Vector2.from_any(e.spatial.pos).y) for e in world.entities.values()}
            rejection_stats: Dict[str, int] = {}

            while ticks < scenario.max_ticks:
                watchdog.poke()
                
                if ticks > 0 and ticks % 5 == 0:
                    is_stagnant = MetricService.detect_stall(world, recent_hps, recent_positions)
                    stagnant_ticks = stagnant_ticks + 5 if is_stagnant else 0
                    
                    recent_hps = {e.id: e.combat.hp for e in world.entities.values()}
                    recent_positions = {e.id: (Vector2.from_any(e.spatial.pos).x, Vector2.from_any(e.spatial.pos).y) for e in world.entities.values()}
                
                if stagnant_ticks >= 100:
                    stop_reason = ArenaStopCondition.STALL
                    break
                
                # --- Milestone 7: Explicit Rejection Auditing ---
                for p in loop.last_rejected:
                    from src_legacy.core.models.reason_codes import ActionReason
                    if isinstance(p.reason, ActionReason) and p.reason.is_rejection:
                        rcode = p.reason.code.value
                        rejection_stats[rcode] = rejection_stats.get(rcode, 0) + 1

                reason = self._check_stop_conditions(world, scenario, ticks, initial_faction_count)
                if reason is not None:
                    stop_reason = reason
                    break
                    
                if not loop.tick_once():
                    last_reason = self._check_stop_conditions(world, scenario, ticks)
                    if last_reason: stop_reason = last_reason
                    break
                ticks += 1
                
                # Active Memory Guard & Peak RSS Tracking
                current_stats = MetricService.record_usage_stats()
                current_rss = current_stats["rss_mb"]
                peak_rss = max(peak_rss, current_rss)
                
                if current_rss - start_stats["rss_mb"] > 600:
                    raise RuntimeError(f"Arena leaked > 600MB mid-run. Current: {current_rss:.1f}MB")

                if ticks % 100 == 0:
                    logger.info("Arena Iteration %d: Tick %d...", iteration, ticks)

            winner = self._determine_winner(world)
            end_stats = MetricService.record_usage_stats()
            
            return ArenaResult(
                iteration=iteration,
                winner_faction=winner,
                ticks=ticks,
                stop_reason=stop_reason,
                deaths=[e.id for e in world.entities.values() if not e.combat.alive],
                rejection_counts=rejection_stats,
                peak_rss_mb=peak_rss,
                cpu_time_sec=end_stats["cpu_total"] - start_stats["cpu_total"]
            )

        except KeyboardInterrupt:
            # Watchdog interrupt_main raises this
            logger.critical("Arena Iteration %d ABORTED by Watchdog (Tick hang)", iteration)
            return ArenaResult(iteration=iteration, ticks=ticks, stop_reason=ArenaStopCondition.WATCHDOG_TIMEOUT)
        finally:
            self._cleanup_hermetic_resources(world, loop, worker_pool, watchdog)

    def _cleanup_hermetic_resources(self, world=None, loop=None, pool=None, watchdog=None) -> None:
        """Centralized idempotent resource reclamation for Milestone 6."""
        if watchdog:
            watchdog.stop()
        if pool:
            pool.shutdown()
        if world:
            world.shutdown()
        if loop and hasattr(loop, "shutdown"):
            loop.shutdown()
            
        import gc
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
        watchdog_timeouts = 0
        total_rss = 0.0
        peak_rss_high_water = 0.0
        total_cpu = 0.0
        rejection_totals: Dict[str, int] = {}
        
        for res in results:
            total_rss += res.peak_rss_mb
            peak_rss_high_water = max(peak_rss_high_water, res.peak_rss_mb)
            total_cpu += res.cpu_time_sec
            
            # Aggregate rejections [Milestone 7]
            for rcode, count in res.rejection_counts.items():
                rejection_totals[rcode] = rejection_totals.get(rcode, 0) + count
            
            wf = res.winner_faction
            if wf is not None:
                # Faction enum values can be logged by name
                if hasattr(wf, "name"):
                    fname = wf.name
                else:
                    # Fallback for serialized/coerced values
                    from src_legacy.core.models.enums import Faction
                    try:
                        fname = Faction(wf).name if not isinstance(wf, str) else wf
                    except (ValueError, TypeError):
                        fname = str(wf)
                win_counts[fname] = win_counts.get(fname, 0) + 1
            
            total_ticks += res.ticks
            if res.stop_reason == ArenaStopCondition.STALL:
                stalls += 1
            elif res.stop_reason == ArenaStopCondition.WATCHDOG_TIMEOUT:
                watchdog_timeouts += 1
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
            watchdog_timeout_rate=watchdog_timeouts / total,
            avg_damage=0.0, # Placeholder for Task 3 damage tracking
            stop_reason=dominant_reason,
            avg_rejection_counts={k: v / total for k, v in rejection_totals.items()},
            avg_peak_rss=total_rss / total,
            peak_rss_high_water=peak_rss_high_water,
            total_cpu_time=total_cpu
        )
