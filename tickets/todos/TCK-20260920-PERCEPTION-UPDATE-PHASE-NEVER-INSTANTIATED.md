---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED
phase: open
date: 2026-09-20
tags: [simulation-quality, cognition]
---

# TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED

## Title
`perception` mechanism is dead in production: `PerceptionUpdatePhase` is never instantiated by
`src/engine/pipeline.py` or anywhere else in `src/`

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`'s differential
runtime scenario, not fixed there per that program's explicit governing constraint (record the
contradiction, do not fix the code to make the old claim true in the same pass).

`registries/mechanisms.yaml`'s `perception` entry previously read `state: done`, `verified:
{instrument: code_trace, verdict: observed}`, citing `PerceptionFilterService.filter()` as "called
from `src/domains/perception/phase.py:43`, a real, non-test integration into the per-tick
pipeline." That citation is only half true: line 43 is a real call site, but it lives inside
`PerceptionUpdatePhase.run()` (`src/domains/perception/phase.py`), and **nothing in `src/` outside
`phase.py` itself ever constructs a `PerceptionUpdatePhase` or calls `.run()`** — confirmed by a
full-tree grep, and independently by a real differential Kernel-run scenario
(`tests/mechanic_scenarios/test_perception_pipeline_wiring.py`): across 5 real ticks against a
world with an adjacent, alive, hostile entity, `PerceptionFilterService.filter` is called zero
times and `entity.cognition.subjective.perception.perceived_entities` stays empty on every entity.
A positive control (calling `.filter()` directly) does produce a real perceived entity, so the code
itself is not broken — it is simply never reached from `src/engine/pipeline.py::refine()`.

The registry has already been corrected (`state: done` → `orphan`, verdict → `contradicted`) as
part of that ticket. This ticket is the real fix, or a deliberate decision not to fix it yet.

## Scope
Investigate and decide:
1. Should `PerceptionUpdatePhase` be wired into `src/engine/pipeline.py::refine()` (a real,
   unconditional or flag-gated phase, matching the shape of `self_model`/`belief_staleness_decay`)?
2. If so, where does `world_signals` (currently a direct argument to `.run()`, never sourced by
   anything real) get built from? No code anywhere in `src/` currently constructs a `WorldSignal`
   list from live world state — this may be a second, larger gap than the wiring itself.
3. Assess blast radius: what (if anything) currently reads `entity.cognition.subjective.perception`
   downstream, expecting it to be populated? If nothing does, this may be lower-urgency than its
   `P1` placeholder suggests.

## Out of Scope
- Re-verifying the finding itself — already confirmed by a real differential scenario, not to be
  re-litigated here without new evidence.
- Any other `cognition` mechanism.

## Acceptance Criteria
1. A real investigation into whether `world_signals` sourcing exists anywhere, or needs to be
   built from scratch.
2. Either a real fix (phase wired in, `perception`'s registry state corrected back once genuinely
   fixed and re-verified), or a documented, evidence-backed decision to defer, same as this arc's
   own established pattern for other found-but-not-fixed defects (e.g.
   `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`).

## Related Tickets
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — found this, did not fix it

## Related Docs
None yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/perception/phase.py::PerceptionUpdatePhase`
- `src/domains/perception/filter.py::PerceptionFilterService`
- `src/domains/perception/salience.py::WorldSignal`
- `src/engine/pipeline.py`

## Assumptions / Open Questions
Whether any downstream consumer expects `perceived_entities` etc. to be populated is not yet
investigated — this determines real urgency vs. theoretical urgency.

## Implementation Notes
(none yet — not started)

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)
