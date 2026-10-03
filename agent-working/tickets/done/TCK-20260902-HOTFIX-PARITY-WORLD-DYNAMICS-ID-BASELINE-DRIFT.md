---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260902-HOTFIX-PARITY-WORLD-DYNAMICS-ID-BASELINE-DRIFT
phase: done
date: 2026-09-02
tags: [testing]
---

# TCK-20260902-HOTFIX-PARITY-WORLD-DYNAMICS-ID-BASELINE-DRIFT

## Title
`test_next_available_id_against_real_world_dynamics_shard` hardcoded baseline drifted — this
session's legitimate WORLD-120/WORLD-121 additions moved the live shard's last-entry id family

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
CI job "API / tools / logging" failed on PR #107
(`https://github.com/ttnhan18062000/rpg-based-simulation/pull/107`) with:
```
tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard
AssertionError: assert 'WORLD-122' == 'WORLD-DEMO-007'
```
`tests/tools/test_parity_updater_static.py:273-276` hardcodes an expectation against the real,
live `docs/parity_ledger/world_dynamics.yaml` file: "the live shard's last entry is a WORLD-DEMO-*
id, so `next_available_id()` must propose the next id in that family." That premise was true when
the test was written, but two tickets landed earlier in this same M3 batch
(`TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH`, `TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH`)
legitimately appended new `WORLD-120`/`WORLD-121` entries (bare `WORLD-NNN` family, correctly
proposed by `next_available_id()` itself at the time via `tools/parity_ledger_writer.py`) after the
prior last entry. `next_available_id()`'s own documented contract (`tools/gate_checks/
parity_updater_static.py:146-148`) is "the reported family is whichever prefix belongs to the last
matching entry in the shard (its ids' own file order)" — so `next_available_id("world_dynamics.yaml")`
correctly now returns `WORLD-122`, not `WORLD-DEMO-007`. This is the identical drift pattern already
documented and fixed once before in this repo via
`TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (M2 batch) — a hardcoded
real-corpus test literal legitimately drifting because of in-scope, correct ledger changes, not a
bug in `next_available_id()` itself.

## Scope
- Update `tests/tools/test_parity_updater_static.py:273-276`
  (`test_next_available_id_against_real_world_dynamics_shard`): change the hardcoded expected value
  from `"WORLD-DEMO-007"` to `"WORLD-122"`, and update the accompanying comment to describe the
  current real state of the shard (last entry is now a bare `WORLD-NNN` id, not `WORLD-DEMO-*`)
  rather than the stale premise.
- Confirm the sibling synthetic-fixture test just above it
  (`test_next_available_id_returns_next_in_family_when_shard_mixes_id_families`, using `tmp_path`,
  not the real ledger) is unaffected — it does not touch the real `docs/parity_ledger/` directory
  and should not be changed.

## Out of Scope
- Any change to `next_available_id()` itself (`tools/gate_checks/parity_updater_static.py`) — its
  behavior is correct and already verified by three separate architecture-reviewer/parity-updater
  passes across this M3 batch's own tickets.
- Any change to `docs/parity_ledger/world_dynamics.yaml` itself — `WORLD-120`/`WORLD-121` are
  correct, already-verified entries from landed tickets.

## Acceptance Criteria
- [x] `tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard`
      passes against the current real `docs/parity_ledger/world_dynamics.yaml`.
- [x] The test's comment accurately describes the current real state (last entry's id family), not
      the stale WORLD-DEMO-only premise.
- [x] No other test in `tests/tools/test_parity_updater_static.py` is modified.

## Related Tickets
- TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH (added WORLD-120, the first cause of this drift)
- TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH (added WORLD-121, the second cause)
- TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT (M2 batch — identical drift
  pattern precedent)

## Related Docs
None — test-only fix, no docs/ behavior change.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- tests/tools/test_parity_updater_static.py

## Assumptions / Open Questions
None.

## Implementation Notes
Confirmed the drift by calling `next_available_id("world_dynamics.yaml", ledger_dir="docs/parity_ledger")`
directly against the current live shard: it returns `"WORLD-122"`, matching the CI failure. Updated
`test_next_available_id_against_real_world_dynamics_shard` (tests/tools/test_parity_updater_static.py,
was lines 273-276) to assert `"WORLD-122"` instead of `"WORLD-DEMO-007"`, and rewrote its comment to
state the current real premise (last entry is now bare `WORLD-121`, not `WORLD-DEMO-*`). No other test
in the file was touched — in particular the sibling synthetic-fixture test
`test_next_available_id_groups_max_suffix_per_prefix_family_not_globally` (uses `tmp_path`) was left
exactly as-is, confirmed by diff. No changes to `tools/gate_checks/parity_updater_static.py` or
`docs/parity_ledger/world_dynamics.yaml` — implementation matched scope exactly, no deviations.

## Test Summary
Ran `tests/tools/test_parity_updater_static.py` with the repo's project venv
(`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/tools/test_parity_updater_static.py -q`):
20 passed, including the fixed `test_next_available_id_against_real_world_dynamics_shard`.

## Files Changed
- tests/tools/test_parity_updater_static.py

## Completion Summary
Fixed a stale hardcoded test expectation in
`test_next_available_id_against_real_world_dynamics_shard` that had drifted out of sync with the
real, live `docs/parity_ledger/world_dynamics.yaml` after two earlier in-batch tickets legitimately
appended `WORLD-120`/`WORLD-121` entries. Updated the expected value from `"WORLD-DEMO-007"` to
`"WORLD-122"` and rewrote the comment to describe the current real shard state. Test-only change,
no production code or ledger data touched; all 20 tests in the file pass.
