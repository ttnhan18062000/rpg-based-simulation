"""Compile every corpus world (seed 42) and report camps / population_cohorts seeding.

Runtime evidence for the `camp` and `demographic_cohort_cycle` registry entries
(TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE). Run from the repo root:
    python3 staging_artifacts/<ticket>/compile_census.py
"""
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

registry = yaml.safe_load((ROOT / "config/simulation_quality/corpus_registry.yaml").read_text())
repo = WorldRepository(str(ROOT / "data" / "worlds"))
worlds_with_camps = worlds_with_cohorts = compiled = 0
for world in sorted(registry["_worlds"]):
    try:
        spec, context = repo.load_world_with_context(world)
        state, _ = WorldCompiler.compile(spec, 42, context=context)
    except Exception as exc:  # noqa: BLE001
        print(f"{world}: COMPILE FAILED {type(exc).__name__}: {exc}")
        continue
    compiled += 1
    camps = len(getattr(state, "camps", {}) or {})
    regions = list((getattr(state, "regions", {}) or {}).values())
    seeded = [r for r in regions if getattr(r, "population_cohorts", None)]
    worlds_with_camps += bool(camps)
    worlds_with_cohorts += bool(seeded)
    print(f"{world}: camps={camps} regions={len(regions)} regions_with_cohorts={len(seeded)}")
print(f"SUMMARY compiled={compiled} worlds_with_camps={worlds_with_camps} worlds_with_cohorts={worlds_with_cohorts}")
