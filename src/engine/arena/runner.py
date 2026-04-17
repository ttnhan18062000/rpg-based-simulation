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
            log_level="WARNING"
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
                    if grid.in_bounds(pos):
                        grid.set(pos, mat)
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
        
        # Simplified execution loop with StopCondition monitoring
        stop_reason = ArenaStopCondition.TIMEOUT
        ticks = 0
        
        # Stall tracking state
        stagnant_ticks = 0
        recent_hps = {e.id: e.combat.hp for e in world.entities.values()}
        recent_positions = {e.id: e.spatial.pos.model_copy() for e in world.entities.values()}
        
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
                recent_positions = {e.id: e.spatial.pos.model_copy() for e in world.entities.values()}
            
            # 100 ticks of zero activity = STALL
            if stagnant_ticks >= 100:
                stop_reason = ArenaStopCondition.STALL
                break

            # Check Stop Conditions (Faction Wipes)
            reason = self._check_stop_conditions(world, scenario, ticks)
            if reason:
                stop_reason = reason
                break
                
            if not loop.tick_once():
                break
            ticks += 1
            
            if ticks % 100 == 0:
                logger.info("Arena Iteration %d: Tick %d...", iteration, ticks)

        # Determine winner based on survivor faction
        winner = self._determine_winner(world)
        deaths = [e.id for e in world.entities.values() if not e.combat.alive]
        
        worker_pool.shutdown()
        
        return ArenaResult(
            iteration=iteration,
            winner_faction=winner,
            ticks=ticks,
            stop_reason=stop_reason,
            deaths=deaths
        )

    def _check_stop_conditions(self, world: WorldState, scenario: Scenario, ticks: int) -> Optional[ArenaStopCondition]:
        """Detect scenario-specific termination. [Milestone 6]"""
        
        # Predefined Check: Faction Wipe
        alive_factions = set()
        for ent in world.entities.values():
            if ent.combat.alive and ent.kind != "generator":
                alive_factions.add(ent.identity.faction)
        
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
            if res.winner_faction is not None:
                # Faction enum values can be logged by name
                fname = res.winner_faction.name
                win_counts[fname] = win_counts.get(fname, 0) + 1
            
            total_ticks += res.ticks
            if res.stop_reason == ArenaStopCondition.STALL:
                stalls += 1
                
        return ScenarioReport(
            scenario_id=scenario.id,
            total_iterations=total,
            win_rates={k: v/total for k, v in win_counts.items()},
            avg_ticks=total_ticks / total,
            stall_rate=stalls / total,
            avg_damage=0.0 # Placeholder for Task 3 damage tracking
        )
