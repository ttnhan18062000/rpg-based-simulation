#!/usr/bin/env python3
"""
Engine profiling harness for V2 simulation.
Establishes performance baselines and isolates subsystem hotspots.
"""

from __future__ import annotations

import argparse
import cProfile
import pstats
import sys
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.profiles import PROD_LARGE, RuntimeProfile, HardwareClass
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.strategic import ProjectState, ProjectKind, ProjectStatus, ObjectiveState, ObjectiveKind
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG

OUT_DIR = Path("reports/profile")


class ProfilingHarness:
    """Orchestrates profiling runs for various simulation scenarios."""

    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def run_scenario(
        self, 
        scenario_name: str, 
        entity_count: int, 
        ticks: int,
        profile: RuntimeProfile = PROD_LARGE
    ) -> None:
        """Executes a named scenario under cProfile."""
        print(f"--- Running Scenario: {scenario_name.upper()} ({entity_count} entities, {ticks} ticks) ---")
        
        state = self._make_state(scenario_name, entity_count)
        kernel = Kernel(
            profile,
            state,
            DeterministicRNG(42),
            flags={"audit_mode": False}
        )

        profile_path = self.out_dir / f"{scenario_name}_{entity_count}.prof"
        text_path = self.out_dir / f"{scenario_name}_{entity_count}.txt"

        profiler = cProfile.Profile()
        profiler.enable()

        for _ in range(ticks):
            kernel.tick_once()

        profiler.disable()
        profiler.dump_stats(profile_path)

        with text_path.open("w", encoding="utf-8") as f:
            stats = pstats.Stats(profiler, stream=f)
            stats.strip_dirs()
            stats.sort_stats("cumtime")
            stats.print_stats(80)

        print(f"  Binary Profile: {profile_path}")
        print(f"  Human Report:   {text_path}")

    def _make_state(self, scenario_name: str, entity_count: int) -> AuthoritativeState:
        """Generates a world state tailored to the scenario."""
        entities = {}
        for entity_id in range(1, entity_count + 1):
            builder = V2EntityBuilder(entity_id).kind("hero")
            
            # Scenario-specific customization
            if scenario_name == "idle":
                # Static heroes, no work
                builder.location(float(entity_id % 100), float(entity_id // 100))
            
            elif scenario_name == "movement":
                # Heroes with random movement targets
                builder.location(0.0, 0.0)
                builder.navigation(target=(100.0, 100.0))
            
            elif scenario_name == "strategic":
                # Heroes with active projects
                builder.location(float(entity_id % 50), float(entity_id // 50))
                project = ProjectState(
                    id=f"proj_{entity_id}",
                    kind=ProjectKind.QUEST,
                    status=ProjectStatus.ACTIVE,
                    objectives=[
                        ObjectiveState(id="obj_1", kind=ObjectiveKind.REACH_LOCATION, target="100,100")
                    ],
                    active_objective_id="obj_1"
                )
                builder.strategic(
                    projects={project.id: project},
                    current_project_id=project.id
                )
            
            elif scenario_name == "resource":
                # Heroes with gold/items to stress transaction logic
                builder.inventory(gold=1000)

            # Common components
            builder.identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
            builder.combat(hp=100, max_hp=100, alive=True, readiness=100.0)
            builder.lifecycle(active=True)
            
            entities[entity_id] = builder.build()

        return AuthoritativeState(
            tick=0,
            seed=42,
            entities=entities
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="RPG Engine Profiler")
    parser.add_argument(
        "--scenario", 
        choices=["idle", "movement", "resource", "strategic"], 
        default="idle",
        help="Simulation scenario to profile"
    )
    parser.add_argument("--entities", type=int, default=1000, help="Number of entities")
    parser.add_argument("--ticks", type=int, default=100, help="Number of ticks to run")
    args = parser.parse_args()

    harness = ProfilingHarness(OUT_DIR)
    harness.run_scenario(args.scenario, args.entities, args.ticks)


if __name__ == "__main__":
    main()
