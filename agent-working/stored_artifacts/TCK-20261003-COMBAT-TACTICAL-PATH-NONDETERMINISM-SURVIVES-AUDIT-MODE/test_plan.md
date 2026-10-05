---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE
artifact_type: test_plan
tags: [engine, combat, determinism, root-cause]
---

# Test plan

No code changes, so no regression test is added here. A regression test cannot be a run-twice-and-compare, because
the second trace appeared only intermittently (after trial 7 in three of five experiments, never in two); the fix
ticket owns that design.

## Proof Plan

- level: engine integration (real `Kernel.tick_once()`, full 2000-tick runs and 8-tick trials)
- proof kind: confirm-or-refute measurement with a positive control
- oracle source: `docs/engine/deterministic_execution.md` (the proof digest is `CanonicalStateHasher.get_hash`)
  and the ticket's six acceptance criteria
- expected effect: either identical canonical hashes across identical runs, or a named first divergent tick and
  fields; the control (a different seed) must differ, proving the instrument can detect a difference
- selected commands: scratch probes (not in the repo): a per-tick canonical-hash run harness and an 8-tick
  multi-trial harness that records `StrategicWorkQueue.build` inputs and `id()`-reuse in
  `DirtySetBuilder.mark_from_update`
