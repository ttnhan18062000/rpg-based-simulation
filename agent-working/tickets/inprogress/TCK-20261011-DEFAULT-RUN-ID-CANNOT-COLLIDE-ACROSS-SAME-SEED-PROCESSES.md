---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261011-DEFAULT-RUN-ID-CANNOT-COLLIDE-ACROSS-SAME-SEED-PROCESSES
phase: implement
date: 2026-10-11
tags: []
---

# TCK-20261011-DEFAULT-RUN-ID-CANNOT-COLLIDE-ACROSS-SAME-SEED-PROCESSES

## Title
Two same-seed Kernel runs started in the same wall-clock second write into one run directory; the default run id becomes collision-proof.

## Status
INPROGRESS

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Finding by testing-planner (2026-10-11), with evidence from testing-implementer's stage 1 of TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE. src/engine/kernel.py ~l.141-144: the default `run_id` is `run_<int(time.time())>_<suffix>`, where the suffix is `self._rng.get_int(Domain.INIT, 0, 0, 1000, 9999)`, which is SEEDED. So two same-seed processes that start in the same second share data/runs/<id>, and their events double or interleave: two runs started together gave COGNITION 2 vs 4 and COMBAT 7 vs 14, exactly double. This affects the slow CI job under xdist and local parallel calibration. It is a plausible second cause of the grade-anchor flakes. The rpg gate harness passes a unique run_id, so it is safe.

## Scope
- The default run id adds a NON-seeded part: the pid plus a short random nonce (os.urandom / uuid4). It must never draw from the simulation RNG: confirm the existing suffix draw is stateless (counter-based) so removing or keeping it moves no other draw. If it is stateful, KEEP the draw and only append to it.
- Create the run directory exclusively: fail loudly, or retry with a new nonce, if it already exists. Never write into another run's directory.
- The run id is not simulation state: confirm no state hash or canonical dict includes it.
- Tests:
  - two Kernels with the same seed, constructed in the same second, get different run ids and different directories;
  - a pre-existing directory is never reused;
  - state hashes are unchanged versus before (golden fixtures untouched).

## Out of Scope
- Callers that pass an explicit run_id (gate harness, tests): unchanged.

## Acceptance Criteria
- No two default-id runs can share a directory; determinism of simulation outputs is unchanged.

## Related Tickets
TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE (testing side passes a unique run_id).

## Related Docs
docs/engine/kernel.md (Persistence phase); docs/testing deterministic_execution.md.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/kernel.py (~l.141-144); src/observability/reporting/artifact_repository.py.

## Assumptions / Open Questions
None.

## Implementation Notes
- `default_run_id(seeded_suffix)` in `src/engine/kernel.py`: `run_<second>_<seeded suffix>_<pid>_<uuid4 hex[:8]>`. The `get_int(Domain.INIT, ...)` draw is stateless (`src/platform/rng.py:90`), so it is kept and only appended to; it moves no stream.
- `Kernel._create_run_directory`: an explicit run id keeps `overwrite=True` (the caller named it). A default id creates with `overwrite=False` and, on `FileExistsError`, takes a fresh id (8 attempts, then raises). Before this, a default id also used `overwrite=True`, so a collision removed another process's directory.
- The run id is in no state hash or canonical dict (grep of `checkpoint.py`/`state.py`: none).

## Test Summary
`tests/unit/engine/test_default_run_id_cannot_collide.py`: 5 pass alone (same-second same-seed kernels differ in id and dir; an existing directory is untouched and a fresh id is taken; an explicit id is unchanged; pid and a non-seeded nonce; two same-seed runs end with an identical state hash). Run inside `tests/unit/engine -k "kernel or run"`, 4 of them fail with `Mock object has no attribute 'species'` from `common_knowledge_seed.py:49`: another test leaves a Mock in a content registry (pre-existing order dependence in `compile_world`, not this change); the other 77 kernel/run tests pass.

## Files Changed
src/engine/kernel.py; tests/unit/engine/test_default_run_id_cannot_collide.py

## Completion Summary
TBD
