from __future__ import annotations

from typing import Dict, FrozenSet

from src.engine.phases import TickPhase

# Per-phase state domain declarations (RPG-INFRA-155, RPG-INFRA-156, RPG-INFRA-157).
# These are declarative only — no runtime enforcement. Enforcement is via
# architecture guard tests in tests/architecture/test_phase_domain_permissions.py.
#
# Domain labels:
#   entity    — EntityState / entity components
#   world     — World-level state (regions, resources, ecology)
#   policy    — Governance policy, mode, executor configuration
#   schedule  — Work scheduling output (work_items, budgets)
#   proposals — Worker proposals / final_results
#   lifecycle — Simulation lifecycle (tick counter, world_time)
#   infra     — Infrastructure (OccupancySnapshot, caches, metrics)
#   platform  — Platform signals (memory, timing)
#   replay    — Replay / persistence output
#   events    — Simulation events (observability)

PHASE_READ_DOMAINS: Dict[TickPhase, FrozenSet[str]] = {
    TickPhase.INIT:        frozenset({"policy", "platform", "infra"}),
    TickPhase.SCHEDULING:  frozenset({"entity", "policy"}),
    TickPhase.COLLECTION:  frozenset({"entity", "schedule"}),
    TickPhase.RESOLUTION:  frozenset({"proposals", "policy", "entity"}),
    TickPhase.CLEANUP:     frozenset({"platform", "infra"}),
    TickPhase.ADVANCEMENT: frozenset({"entity", "lifecycle"}),
    TickPhase.PERSISTENCE: frozenset({"entity", "world", "events"}),
}

PHASE_WRITE_DOMAINS: Dict[TickPhase, FrozenSet[str]] = {
    TickPhase.INIT:        frozenset({"policy", "infra"}),
    TickPhase.SCHEDULING:  frozenset({"schedule"}),
    TickPhase.COLLECTION:  frozenset({"proposals"}),
    TickPhase.RESOLUTION:  frozenset({"entity", "world", "policy", "infra"}),
    TickPhase.CLEANUP:     frozenset({"infra"}),
    TickPhase.ADVANCEMENT: frozenset({"lifecycle"}),
    TickPhase.PERSISTENCE: frozenset({"replay"}),
}

PHASE_EMIT_DOMAINS: Dict[TickPhase, FrozenSet[str]] = {
    TickPhase.INIT:        frozenset(),
    TickPhase.SCHEDULING:  frozenset(),
    TickPhase.COLLECTION:  frozenset(),
    TickPhase.RESOLUTION:  frozenset({"events", "replay"}),
    TickPhase.CLEANUP:     frozenset(),
    TickPhase.ADVANCEMENT: frozenset({"events"}),
    TickPhase.PERSISTENCE: frozenset({"replay", "events"}),
}

ALL_AUTHORITATIVE_PHASES: FrozenSet[TickPhase] = frozenset({
    TickPhase.INIT,
    TickPhase.SCHEDULING,
    TickPhase.COLLECTION,
    TickPhase.RESOLUTION,
    TickPhase.CLEANUP,
    TickPhase.ADVANCEMENT,
})
