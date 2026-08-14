---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-OBSERVABILITY-SKILL
artifact_type: investigation
tags: [skills, observability]
---

# Investigation — TCK-20260805-OBSERVABILITY-SKILL

## Context Search
`search_docs("HardLawMonitor invariant check dirty_set observability backpressure...")` surfaced
`docs/architecture/observability_hot_path_safety_contract.md` §5 (the real 4-mode backpressure
table), `docs/engine/kernel.md`'s "Hard Law Compliance Guard" section, and
`docs/observability/hard_law_monitor.md` (read in full).

## Real Content Grounded
- **Backpressure modes** (`docs/architecture/observability_hot_path_safety_contract.md` §5):
  `NORMAL` (<70% fill, all recorded), `PRESSURE` (70-90%, INFO/DEBUG sampled 1-in-5,
  WARNING+ always pass), `DEGRADED` (90-100%, INFO/DEBUG dropped, WARNING+ pass), `SURVIVAL`
  (≥100%, counter-only, zero IO/locks/allocations). `ObservabilityController.evaluate(queue_fill_ratio)`
  is a pure function returning the recommended mode.
- **HardLawMonitor's 7 laws** (`docs/observability/hard_law_monitor.md` §1): `LAW-HP-NONNEGATIVE`,
  `LAW-READINESS-NONNEGATIVE`, `LAW-GOLD-NONNEGATIVE`, `LAW-STAMINA-NONNEGATIVE`,
  `LAW-POSITION-FINITE`, `LAW-OCCUPANCY-COLLISION` (all DirtySet-scoped, O(1)-per-tick), plus
  `LAW-SPAWN-OCCUPANCY` (the one exception — a full-population scan run once at `Kernel.__init__`,
  since nothing has "moved" yet for the DirtySet-gated laws to catch).
- **ObservabilityMode policy** (§2): `OFF` bypasses entirely; `LIGHT` (default) logs + counts,
  never halts; `DEBUG`/`CERTIFICATION` raise `HardLawViolationError` and halt; `LONG_RUN` is a
  **documented real gap** — violations persist to `hard_law_violations.jsonl` and route to
  `AlertsManager`, but the mode-gating `if`/`elif` chain only handles `LIGHT`/`DEBUG`/`CERTIFICATION`
  explicitly, so `LONG_RUN` silently falls through both branches (neither logged nor raised) —
  worth flagging in the skill since it's a real, disclosed gotcha, not something to paper over.
- **Kernel integration**: HardLawMonitor runs during the Advancement phase, before state commit —
  `docs/engine/kernel.md`'s "Hard Law Compliance Guard" Law confirms this exactly.
- **Prometheus metrics**: `sim_hard_law_violations_total{law_id,severity}` (Counter),
  `sim_hard_law_last_violation_tick` (Gauge, `-1` if none).
- **Real test paths** (confirmed via `find`, not guessed): `tests/engine/test_hard_law_monitor.py`,
  `tests/perf/test_hard_law_monitor_overhead.py`, `tests/unit/observability/test_event_recorder.py`,
  `tests/unit/observability/test_observability_hardening.py`,
  `tests/integration/observability/test_phase28_observability_degradation.py`,
  `tests/architecture/test_phase19_observability_boundaries.py`.

## Scope Decision: one skill, not split
The ticket's Plan-decision point asked whether to split into a narrower "debugging" skill vs. a
broader "working in observability" skill. Decided: **one skill**, named `observability` (matching
this repo's other domain-skill naming convention — `combat`, `systems`, `cognition-strategy`, not
`observability-debugging`). Authoring and debugging observability code share the same grounding
(the 7 laws, the 4 modes, the kernel integration point) — splitting would duplicate that grounding
across two files for no real benefit, since a debugging session needs to know the same laws/modes
an authoring session does.

## Unresolved Questions
None — all cited content verified against real docs and real file paths.
