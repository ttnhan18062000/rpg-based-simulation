---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK
artifact_type: test_plan
tags: [engine, determinism]
---

# Test plan

`tests/unit/core/test_dirty_set_builder_identity.py`: with every `id()` forced to collide, both entities must be
marked (fails on the old keying, verified by restoring the old `dirty.py`: 2 of 3 failed); a shared update object
re-marked on a later call is harmless; the builder keeps no identity registry. Wide determinism-adjacent sweep:
2717 passed, 3 skipped, 1 xfailed, 1 failed (the known local 60 s `test_behavioral_5k_regression` timeout).

## Proof Plan

- level: unit (the regression test) and engine integration (the measurements)
- proof kind: discriminating experiment with a control arm, then a fix verified against the same instrument
- oracle source: `docs/engine/deterministic_execution.md` (proof digest is `CanonicalStateHasher.get_hash`)
- expected effect: identical canonical hash traces across identical runs; the plain arm diverges, the
  strong-reference and fixed arms do not
- selected commands: scratch multi-trial probe (24 trials x 8 ticks per process) plus
  `pytest tests/unit/core/test_dirty_set_builder_identity.py`
