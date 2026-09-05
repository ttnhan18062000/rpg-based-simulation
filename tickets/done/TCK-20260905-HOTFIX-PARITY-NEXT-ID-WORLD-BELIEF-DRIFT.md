---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260905-HOTFIX-PARITY-NEXT-ID-WORLD-BELIEF-DRIFT
phase: open
date: 2026-09-05
tags: [strategy]
---

# TCK-20260905-HOTFIX-PARITY-NEXT-ID-WORLD-BELIEF-DRIFT

## Title
Fix stale `next_available_id()` real-corpus regression test after WORLD-BELIEF-* entries landed

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
CI's "API / tools / logging" job failed on PR #128 (branch `m5-death-lineage-reputation-implementation`).
Root-caused via local reproduction of the exact CI command (`pytest tests/api tests/cli tests/tools
tests/logging tests/engine tests/observability -m "not slow and not extra_slow"`), narrowed to a single
failing test: `tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard`.
This is the documented "hardcoded test baseline drift" class CLAUDE.md's own CI Triage guidance names
`test_parity_index_baseline.py`'s `missing_test_path_count` as the canonical example of — a test
asserting an exact value against live repo state that legitimately drifted because this session's own
already-verified M5 ticket work (`TCK-20260905-BELIEF-INSTITUTION-DESIGN`, idea 63) added new
`WORLD-BELIEF-001`/`WORLD-BELIEF-002` entries to `docs/parity_ledger/world_dynamics.yaml`, after the
existing `WORLD-CULT-004` entry the test's hardcoded expectation (`"WORLD-CULT-005"`) was based on.

Verified directly: `next_available_id("world_dynamics.yaml", ledger_dir="docs/parity_ledger")`'s real,
live output is now `"WORLD-BELIEF-003"` — correct per its own documented per-family-suffix design (it
tracks max suffix per full id-family prefix, reporting whichever family belongs to the shard's own last
matching entry; `WORLD-BELIEF-002` is now that last matching entry, added after `WORLD-CULT-004`).
Confirmed via direct grep of the live ledger's own `id:` lines that `WORLD-BELIEF-002` is genuinely the
highest-numbered entry, and `next_available_id()`'s own logic is unmodified and correct — this is not a
bug in the function, only a stale hardcoded expectation in its own real-corpus regression test.

## Scope
- Update `tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard`'s
  hardcoded expected value from `"WORLD-CULT-005"` to `"WORLD-BELIEF-003"`, with the test's own comment
  rewritten to cite the real, current evidence (`WORLD-BELIEF-002`, added by
  `TCK-20260905-BELIEF-INSTITUTION-DESIGN`) rather than leaving the stale `WORLD-CULT-004`/
  `SETTLEMENT-CULTURE-READ` citation in place.

## Out of Scope
- Any change to `next_available_id()`'s own implementation — confirmed correct, not a bug.
- Any other test file — `tests/tools/test_parity_index_baseline.py`'s own `missing_test_path_count`
  assertion computes its expected value dynamically (`live_missing`) at test time, not a hardcoded
  literal, so it does not need a matching fix.
- The other 5 test directories in the failing CI job's own pytest command (`tests/api`, `tests/cli`,
  `tests/engine`, `tests/logging`, `tests/observability`) — `tests/engine`, `tests/logging`, and
  `tests/observability` were independently re-run and confirmed passing; `tests/api`/`tests/cli` were
  not fully re-run locally due to sustained memory contention from a concurrent session's own long-running
  test process, but the single failure found and fixed here is sufficient to explain the CI job's
  failure signature (a real, isolated hardcoded-baseline drift, not a systemic breakage).

## Acceptance Criteria
- [x] `tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard`
      passes against the live `docs/parity_ledger/world_dynamics.yaml` corpus.
- [x] The test's own comment cites fresh, real evidence (the actual current last-matching entry and the
      ticket that added it), not a stale prior state.
- [x] No production code (`tools/gate_checks/parity_updater_static.py`) is touched.

## Related Tickets
- TCK-20260905-BELIEF-INSTITUTION-DESIGN (idea 63, DONE — the ticket whose new `WORLD-BELIEF-*` parity
  entries caused this legitimate drift)
- TCK-20260904-HOTFIX-PARITY-BASELINE-DRIFT-WORLD-085-AND-NEXT-ID (the M4-batch precedent for this exact
  drift class, same test file, same underlying `next_available_id()` real-corpus regression test)

## Related Docs
- CLAUDE.md's CI Failure Triage section (documents this exact drift class as an accepted hotfix pattern)
- docs/parity_ledger/world_dynamics.yaml

## Related Stored Artifacts
None — hotfix tier, self-evident intent captured in this ticket.

## Related Code Areas
- tests/tools/test_parity_updater_static.py

## Assumptions / Open Questions
None.

## Implementation Notes
Changed the single hardcoded assertion from `"WORLD-CULT-005"` to `"WORLD-BELIEF-003"` and rewrote the
test's own explanatory comment to cite `WORLD-BELIEF-002` (added by `TCK-20260905-BELIEF-INSTITUTION-DESIGN`)
as the real current last-matching entry, replacing the stale `WORLD-CULT-004`/`SETTLEMENT-CULTURE-READ`
citation. No production code touched.

## Test Summary
`tests/tools/test_parity_index_baseline.py tests/tools/test_parity_updater_static.py` — 35 passed, 0
failed (up from 1 failed/34 passed before the fix).

## Files Changed
- `tests/tools/test_parity_updater_static.py`

## Completion Summary
Fixed a real, legitimate hardcoded-baseline test drift caused by this session's own already-verified
`TCK-20260905-BELIEF-INSTITUTION-DESIGN` work adding new `WORLD-BELIEF-*` parity entries — the exact
drift class CLAUDE.md's own CI Triage guidance documents as an accepted hotfix pattern, matching the
precedent `TCK-20260904-HOTFIX-PARITY-BASELINE-DRIFT-WORLD-085-AND-NEXT-ID` set on the same test file.
`next_available_id()`'s own implementation was independently confirmed correct and untouched.
