"""
Personality → Long-Run Behavior Calibration Audit.

Ticket: TCK-20260628-E11B-PERSONALITY-AUDIT
Usage:  python3 tools/personality_audit.py [--ticks N] [--seed S] [--world W]

Runs a simulation with LIGHT observability, reads per-entity personality snapshots,
and reports whether OCEAN traits (bravery, greed, industry, sociability, curiosity)
produce statistically distinct behavioral clusters (project_kind distributions).

Output: reports/personality_audit.json  +  stdout summary
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from dataclasses import replace
from pathlib import Path
from typing import Any

SEED = 42
WORLD_ID = "urban_political"
TICKS = 1000
REPORT_PATH = Path("reports/personality_audit.json")

TRAIT_NAMES = ["bravery", "greed", "industry", "sociability"]  # curiosity is in .properties


def _run_simulation(ticks: int, seed: int, world_id: str) -> str:
    """Run simulation with LIGHT obs and return the run_id."""
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler
    from src.engine.kernel import Kernel
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.platform.rng import DeterministicRNG
    from src.observability.config import ObservabilityConfig, ObservabilityMode

    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)

    try:
        repo = WorldRepository("data/worlds")
        spec = repo.load_world(world_id)
        state, _ = WorldCompiler.compile(spec, seed=seed)

        flags = dict(state.feature_flags)
        flags["ENABLE_ADVENTURE_ROUTING"] = 1.0
        state = replace(state, feature_flags=flags)

        profile = RuntimeProfile(
            name="personality-audit",
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=2048,
            max_cpu_percent=100.0,
            max_worker_count=1,
            max_queue_depth=2000,
            max_replay_buffer_kb=0,
            max_observability_budget_percent=0.0,
            max_tick_budget_ms=500.0,
        )

        kernel = Kernel(
            profile=profile,
            state=state,
            rng=DeterministicRNG(seed),
            flags={"no_frame_pacing": True},
        )
        run_id = kernel._run_id

        print(f"  run_id: {run_id}")
        for tick in range(1, ticks + 1):
            kernel.tick_once()
            if tick % 200 == 0:
                print(f"  tick {tick}/{ticks}...")

        kernel.shutdown()
        return run_id
    finally:
        ObservabilityConfig.set_override_mode(None)


def _find_snapshot_file(run_id: str) -> Path | None:
    """Locate entity_personality_snapshots.jsonl for this run."""
    candidates = [
        Path(f"data/runs/{run_id}/entity_personality_snapshots.jsonl"),
        Path("data/runs") / run_id / "entity_personality_snapshots.jsonl",
    ]
    for p in candidates:
        if p.exists():
            return p
    # Search under data/runs/
    for p in Path("data/runs").rglob("entity_personality_snapshots.jsonl"):
        if run_id in str(p):
            return p
    return None


def _load_snapshots(path: Path) -> list[dict[str, Any]]:
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


@dataclass
class EntityProfile:
    entity_id: int
    personality: dict[str, float] = field(default_factory=dict)
    project_kinds: list[str | None] = field(default_factory=list)

    @property
    def bravery(self) -> float:
        return self.personality.get("bravery", 0.0)

    @property
    def greed(self) -> float:
        return self.personality.get("greed", 0.0)

    @property
    def industry(self) -> float:
        return self.personality.get("industry", 0.0)

    @property
    def sociability(self) -> float:
        return self.personality.get("sociability", 0.0)

    @property
    def curiosity(self) -> float:
        return self.personality.get("curiosity", 0.0)

    def dominant_project_kind(self) -> str | None:
        counts: dict[str, int] = defaultdict(int)
        for k in self.project_kinds:
            counts[k or "NONE"] += 1
        if not counts:
            return None
        return max(counts, key=lambda k: counts[k])

    def behavioral_diversity(self) -> float:
        """Shannon entropy of project_kind distribution (0 = always same, high = diverse)."""
        from math import log2
        counts: dict[str, int] = defaultdict(int)
        for k in self.project_kinds:
            counts[k or "NONE"] += 1
        total = sum(counts.values())
        if total == 0:
            return 0.0
        entropy = 0.0
        for c in counts.values():
            p = c / total
            if p > 0:
                entropy -= p * log2(p)
        return round(entropy, 4)


def _build_profiles(snapshots: list[dict]) -> dict[int, EntityProfile]:
    profiles: dict[int, EntityProfile] = {}
    for rec in snapshots:
        eid = rec["entity_id"]
        if eid not in profiles:
            profiles[eid] = EntityProfile(entity_id=eid)
        prof = profiles[eid]
        # Keep the most recent personality (traits are stable but update last seen)
        if rec.get("personality"):
            prof.personality = rec["personality"]
        prof.project_kinds.append(rec.get("active_project_kind"))
    return profiles


def _quartile_label(value: float) -> str:
    if value < 0.25:
        return "Q1 (low)"
    elif value < 0.50:
        return "Q2 (mid-low)"
    elif value < 0.75:
        return "Q3 (mid-high)"
    return "Q4 (high)"


def _analyze(profiles: dict[int, EntityProfile]) -> dict[str, Any]:
    results: dict[str, Any] = {
        "entity_count": len(profiles),
        "total_snapshots": sum(len(p.project_kinds) for p in profiles.values()),
        "traits": {},
    }

    for trait in TRAIT_NAMES:
        by_quartile: dict[str, list[float]] = defaultdict(list)
        for prof in profiles.values():
            val = getattr(prof, trait)
            q = _quartile_label(val)
            by_quartile[q].append(prof.behavioral_diversity())

        trait_report: dict[str, Any] = {}
        for q_label in ["Q1 (low)", "Q2 (mid-low)", "Q3 (mid-high)", "Q4 (high)"]:
            divs = by_quartile.get(q_label, [])
            if divs:
                trait_report[q_label] = {
                    "entity_count": len(divs),
                    "avg_diversity": round(sum(divs) / len(divs), 4),
                }
            else:
                trait_report[q_label] = {"entity_count": 0, "avg_diversity": None}
        results["traits"][trait] = trait_report

    # Project kind distribution
    all_kinds: dict[str, int] = defaultdict(int)
    for prof in profiles.values():
        for k in prof.project_kinds:
            all_kinds[k or "NONE"] += 1
    results["project_kind_totals"] = dict(sorted(all_kinds.items(), key=lambda x: -x[1]))

    # Abandonment proxy: project switches per entity by personality group (E11D)
    # High-industry (Q4 industry) vs high-neuroticism (Q1 bravery = high-caution)
    high_industry_switches = [
        len(p.project_kinds) for p in profiles.values()
        if p.industry >= 0.75
    ]
    high_neuroticism_switches = [
        len(p.project_kinds) for p in profiles.values()
        if p.bravery < 0.25
    ]
    avg_hi = round(sum(high_industry_switches) / len(high_industry_switches), 4) if high_industry_switches else None
    avg_hn = round(sum(high_neuroticism_switches) / len(high_neuroticism_switches), 4) if high_neuroticism_switches else None
    ratio = round(avg_hi / avg_hn, 4) if (avg_hi is not None and avg_hn and avg_hn > 0) else None
    results["abandonment_proxy"] = {
        "high_industry_q4_count": len(high_industry_switches),
        "high_neuroticism_q1bravery_count": len(high_neuroticism_switches),
        "avg_switches_high_industry": avg_hi,
        "avg_switches_high_neuroticism": avg_hn,
        "ratio_industry_over_neuroticism": ratio,
        "ac_met": ratio is not None and ratio <= 0.5,
        "note": "ratio ≤ 0.50 means high-industry abandons projects ≤ 50% as often (E11D AC)",
    }

    # Per-entity summary
    entity_summaries = []
    for prof in sorted(profiles.values(), key=lambda p: p.entity_id):
        entity_summaries.append({
            "entity_id": prof.entity_id,
            "bravery": round(prof.bravery, 4),
            "greed": round(prof.greed, 4),
            "industry": round(prof.industry, 4),
            "sociability": round(prof.sociability, 4),
            "behavioral_diversity": prof.behavioral_diversity(),
            "dominant_project": prof.dominant_project_kind(),
            "snapshot_count": len(prof.project_kinds),
        })
    results["entities"] = entity_summaries

    return results


def _print_summary(analysis: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  PERSONALITY AUDIT SUMMARY")
    print(f"{'='*60}")
    print(f"  Entities:    {analysis['entity_count']}")
    print(f"  Snapshots:   {analysis['total_snapshots']}")
    print()

    print("  Project kind distribution:")
    for kind, count in analysis["project_kind_totals"].items():
        print(f"    {kind:25s} {count:5d}")
    print()

    print("  OCEAN trait → behavioral diversity (avg Shannon entropy by quartile):")
    for trait, quartiles in analysis["traits"].items():
        q1 = quartiles["Q1 (low)"]["avg_diversity"]
        q4 = quartiles["Q4 (high)"]["avg_diversity"]
        trend = ""
        if q1 is not None and q4 is not None:
            diff = q4 - q1
            trend = f"  Δ={diff:+.4f} ({'↑' if diff > 0 else '↓' if diff < 0 else '→'})"
        print(f"    {trait:15s}: Q1={q1}  Q4={q4}{trend}")
    print()

    ap = analysis.get("abandonment_proxy", {})
    print("  Abandonment proxy — project switches (E11D validation):")
    print(f"    High-industry (Q4)   n={ap.get('high_industry_q4_count',0):3d}  avg_switches={ap.get('avg_switches_high_industry')}")
    print(f"    High-neuroticism(Q1) n={ap.get('high_neuroticism_q1bravery_count',0):3d}  avg_switches={ap.get('avg_switches_high_neuroticism')}")
    ratio = ap.get("ratio_industry_over_neuroticism")
    ac_met = ap.get("ac_met")
    if ratio is not None:
        print(f"    Ratio (industry/neuroticism): {ratio:.4f}  {'✓ AC MET (≤0.50)' if ac_met else '✗ AC NOT MET (>0.50)'}")
    else:
        print("    Ratio: N/A (insufficient data in one or both groups)")
    print(f"{'='*60}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Personality→behavior calibration audit")
    parser.add_argument("--ticks", type=int, default=TICKS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--world", default=WORLD_ID)
    args = parser.parse_args()

    print(f"Running {args.ticks}-tick personality audit (world={args.world}, seed={args.seed})...")
    run_id = _run_simulation(args.ticks, args.seed, args.world)

    snap_path = _find_snapshot_file(run_id)
    if snap_path is None:
        print(f"ERROR: No entity_personality_snapshots.jsonl found for run {run_id}", file=sys.stderr)
        sys.exit(1)

    print(f"  Reading snapshots from: {snap_path}")
    snapshots = _load_snapshots(snap_path)
    print(f"  Loaded {len(snapshots)} snapshot records.")

    profiles = _build_profiles(snapshots)
    analysis = _analyze(profiles)
    analysis["run_id"] = run_id
    analysis["ticks"] = args.ticks
    analysis["seed"] = args.seed
    analysis["world_id"] = args.world

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(analysis, indent=2))
    print(f"  Report written to: {REPORT_PATH}")

    _print_summary(analysis)


if __name__ == "__main__":
    main()
