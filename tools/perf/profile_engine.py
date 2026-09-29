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

from src.config.profiles import PROD_LARGE, RuntimeProfile
from src.core.state import AuthoritativeState
from src.core.strategic import ProjectStatus
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.perf.scenarios import SCENARIO_BUILDERS

OUT_DIR = Path("reports/profile")


class ProfilingHarness:
    """Orchestrates profiling runs for various simulation scenarios."""

    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.last_kernel: Any = None

    def run_scenario(
        self, 
        scenario_name: str, 
        entity_count: int, 
        ticks: int,
        profile: RuntimeProfile = PROD_LARGE,
        mode: str = "pure"
    ) -> None:
        """Executes a named scenario under cProfile."""
        flags = {
            "pure": {"no_replay": True, "no_frame_pacing": True, "audit_mode": False},
            "runtime": {"no_replay": False, "no_frame_pacing": False, "audit_mode": False},
            "audit": {"no_replay": False, "no_frame_pacing": True, "audit_mode": True},
        }.get(mode, {"no_replay": True, "no_frame_pacing": True, "audit_mode": False})

        print(f"--- Running Scenario: {scenario_name.upper()} ({entity_count} entities, {ticks} ticks, mode: {mode}) ---")
        
        state = self._make_state(scenario_name, entity_count)
        kernel = Kernel(
            profile,
            state,
            DeterministicRNG(42),
            flags=flags
        )
        self.last_kernel = kernel

        profile_path = self.out_dir / f"{scenario_name}_{entity_count}_{mode}.prof"
        text_path = self.out_dir / f"{scenario_name}_{entity_count}_{mode}.txt"
        report_path = self.out_dir / "report.md"

        profiler = cProfile.Profile()
        profiler.enable()

        try:
            for t in range(ticks):
                kernel.tick_once()
                if self._is_scenario_completed(scenario_name, kernel._state):
                    print(f"[*] Scenario {scenario_name.upper()} successfully completed early at tick {t + 1}/{ticks}")
                    break
        finally:
            kernel.shutdown()

        profiler.disable()
        profiler.dump_stats(profile_path)

        with text_path.open("w", encoding="utf-8") as f:
            f.write("=== RPG Engine Profile Report ===\n")
            f.write(f"Scenario: {scenario_name} | Entities: {entity_count} | Ticks: {ticks}\n")
            f.write(f"Mode: {mode} | Flags: {flags}\n")
            f.write("=================================\n\n")
            stats = pstats.Stats(profiler, stream=f)
            stats.strip_dirs()
            stats.sort_stats("cumtime")
            stats.print_stats(80)

        with report_path.open("w", encoding="utf-8") as f:
            f.write("# V2 RPG Engine Profiling Report\n\n")
            f.write("## Scenario Execution Summary\n")
            f.write(f"- **Scenario**: {scenario_name}\n")
            f.write(f"- **Entities**: {entity_count}\n")
            f.write(f"- **Ticks**: {ticks}\n")
            f.write(f"- **Mode**: {mode}\n")
            f.write(f"- **Flags**: `{flags}`\n\n")
            f.write("## Generated Output Artifacts\n")
            f.write(f"- **Binary Profile**: `{profile_path}`\n")
            f.write(f"- **Text Summary**: `{text_path}`\n\n")
            f.write("## Memory & Garbage Collection Statement\n")
            f.write("> [!IMPORTANT]\n")
            f.write("> **Memory & GC Verification Notice**: This profiling run evaluates compute execution efficiency under cProfile. ")
            f.write("It does **not** collect active Garbage Collection (GC) metrics or Physical RSS memory snapshots. \n")
            f.write("> Consequently, **no claims regarding GC resilience, lack of memory leaks, or absence of heap fragmentation ")
            f.write("can be made from this report** without explicit GC and RSS telemetry verification.\n")

        print(f"  Binary Profile: {profile_path}")
        print(f"  Human Report:   {text_path}")
        print(f"  Markdown Report:{report_path}")

    def _make_state(self, scenario_name: str, entity_count: int) -> AuthoritativeState:
        """Generates a world state tailored to the scenario."""
        builder_fn = SCENARIO_BUILDERS[scenario_name]
        if scenario_name == "resource":
            return builder_fn(entity_count=int(entity_count * 0.7), node_count=int(entity_count * 0.3))
        elif scenario_name == "combat":
            side_count = max(1, entity_count // 2)
            return builder_fn(team_a_count=side_count, team_b_count=side_count)
        else:
            return builder_fn(entity_count=entity_count)

    def _is_scenario_completed(self, scenario_name: str, state: AuthoritativeState) -> bool:
        if scenario_name == "combat":
            # Check if all entities on one side are dead or incapacitated
            factions_alive = set()
            for entity in state.entities.values():
                if entity.combat and entity.combat.alive and entity.combat.hp > 0:
                    factions_alive.add(entity.identity.faction)
            return len(factions_alive) <= 1
            
        elif scenario_name == "movement":
            # Check if all moving entities have reached their target or have no target
            for entity in state.entities.values():
                if entity.navigation and entity.navigation.target is not None:
                    px, py = entity.navigation.position
                    tx, ty = entity.navigation.target
                    if abs(px - tx) > 0.5 or abs(py - ty) > 0.5:
                        return False
            return True
            
        elif scenario_name == "resource":
            # Check if all resource nodes are fully depleted
            if not state.resource_nodes:
                return True
            return all(node.remaining_charges <= 0 for node in state.resource_nodes.values())
            
        elif scenario_name == "strategic":
            # Check if all strategic projects are completed
            has_active_projects = False
            for entity in state.entities.values():
                if entity.strategic and entity.strategic.projects:
                    for proj in entity.strategic.projects.values():
                        if proj.status == ProjectStatus.ACTIVE:
                            has_active_projects = True
                            break
                    if has_active_projects:
                        break
            return not has_active_projects

        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="RPG Engine Profiler")
    parser.add_argument(
        "--scenario", 
        choices=list(SCENARIO_BUILDERS.keys()), 
        default="idle",
        help="Simulation scenario to profile"
    )
    parser.add_argument("--entities", type=int, default=1000, help="Number of entities")
    parser.add_argument("--ticks", type=int, default=500, help="Number of ticks to run")
    parser.add_argument(
        "--mode",
        choices=["pure", "runtime", "audit"],
        default="pure",
        help="Profiling harness isolation mode"
    )
    args = parser.parse_args()

    harness = ProfilingHarness(OUT_DIR)
    harness.run_scenario(args.scenario, args.entities, args.ticks, mode=args.mode)


if __name__ == "__main__":
    main()

