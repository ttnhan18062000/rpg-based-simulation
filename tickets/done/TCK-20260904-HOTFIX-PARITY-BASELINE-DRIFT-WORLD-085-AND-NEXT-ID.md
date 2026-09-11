---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-PARITY-BASELINE-DRIFT-WORLD-085-AND-NEXT-ID
phase: done
date: 2026-09-04
tags: [testing]
---

# TCK-20260904-HOTFIX-PARITY-BASELINE-DRIFT-WORLD-085-AND-NEXT-ID

## Title
Update two hardcoded parity-tooling test baselines that this session's own legitimate M4 tickets caused to drift

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
CI's "API / tools / logging" job failed on two hardcoded-baseline regression tests, both drifted by
this session's own real, already-landed M4 ticket work — matching the documented baseline-drift class
`docs/testing/regression_policy.md`/CLAUDE.md already name (`tests/tools/test_parity_index_baseline.py`'s
`missing_test_path_count`, explicitly called out as needing this exact kind of hotfix).

1. **`tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard`**
   — asserted `next_available_id("world_dynamics.yaml") == "WORLD-124"`, documented at the time as
   correct because `world_dynamics.yaml`'s last entry was a bare `WORLD-NNN` id (`WORLD-123`). Since
   then, this session's own `TCK-20260904-CAMP-NEST-CLASSIFICATION` (added `WORLD-124`) and
   `TCK-20260904-SETTLEMENT-CULTURE-READ` (added `WORLD-CULT-004`, now the shard's real last entry)
   both landed. `next_available_id()`'s own documented design (tracks max suffix per full id-family
   prefix, reports whichever family belongs to the shard's last matching entry) now correctly returns
   `WORLD-CULT-005` — confirmed directly by reading the function's own docstring/logic in
   `tools/gate_checks/parity_updater_static.py` and the real file's tail (`WORLD-123`, `WORLD-124`,
   `WORLD-CULT-004` in that order). This is not a tool bug — the test's hardcoded expectation is
   simply stale.
2. **`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`**
   — asserted `live_missing == 1317`. Independently re-computed the live scan directly: **1316**.
   Traced the exact -1 drift to `WORLD-085` (`docs/parity_ledger/world_dynamics.yaml`, P1,
   `status: verified`): its `test_path` was `null` when `1317` was last set, and this session's own
   `TCK-20260904-LAIR-ENTITY-ANCHOR` ticket gave it a real `test_path`
   (`tests/unit/world/test_world_dynamics.py::test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`)
   as part of generalizing the boss-spawn idempotency pattern to Lair. This is the exact "legitimately
   gains a real `test_path` over time" case the test's own comment already documents as non-frozen.

## Scope
- Update `test_next_available_id_against_real_world_dynamics_shard`'s expected value from
  `"WORLD-124"` to `"WORLD-CULT-005"`, and update its comment to explain the new real state (last
  entry is now `WORLD-CULT-004`, added by `TCK-20260904-SETTLEMENT-CULTURE-READ`), mirroring the
  existing comment's own documentation style.
- Update `test_baseline_manifest_does_not_coerce_missing_test_path`'s expected value from `1317` to
  `1316`, appending one more entry to its existing running-changelog comment (matching its established
  format: drift amount, ticket ID, entry ID, what changed) citing `WORLD-085`/
  `TCK-20260904-LAIR-ENTITY-ANCHOR`.
- Re-run both tests directly to confirm they pass against the real, current parity-ledger state.

## Out of Scope
- Any change to `next_available_id()`'s own logic in `tools/gate_checks/parity_updater_static.py` —
  confirmed correct and working as documented; only the test's stale expectation needs updating.
- Any change to `docs/parity_ledger/world_dynamics.yaml` itself — both `WORLD-124`/`WORLD-CULT-004`
  (ticket 1) and `WORLD-085`'s `test_path` (ticket 2) are real, already-verified, already-landed
  parity-ledger content from prior tickets this session — not touched here.
- Any other stale baseline in the repo (e.g. the previously-flagged ~44 stale `tests_v2/`/`tests/rpg/`
  parity test-path citations, tracked separately by `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT`)
  — unrelated root cause, not this ticket's job.

## Acceptance Criteria
- `test_next_available_id_against_real_world_dynamics_shard` asserts `"WORLD-CULT-005"` and passes.
- `test_baseline_manifest_does_not_coerce_missing_test_path` asserts `1316` and passes.
- Both tests' comments accurately cite the real ticket/entry that caused the drift, matching each
  file's own established documentation convention.
- CI's "API / tools / logging" job passes with these two fixes (in combination with the already-landed
  `TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH`).

## Related Tickets
- TCK-20260904-CAMP-NEST-CLASSIFICATION (added WORLD-124)
- TCK-20260904-SETTLEMENT-CULTURE-READ (added WORLD-CULT-004)
- TCK-20260904-LAIR-ENTITY-ANCHOR (gave WORLD-085 a real test_path)
- TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH (the sibling hotfix landed just before this one, same CI job)

## Related Docs
- docs/parity_ledger/world_dynamics.yaml (WORLD-085, WORLD-124, WORLD-CULT-004 — read-only reference, not modified)

## Related Stored Artifacts
None (hotfix tier, no staging artifacts required).

## Related Code Areas
- tests/tools/test_parity_updater_static.py
- tests/tools/test_parity_index_baseline.py
- tools/gate_checks/parity_updater_static.py (read-only reference, confirmed correct, not modified)

## Assumptions / Open Questions
None — both drifts were traced to their exact, real, already-landed root cause before fixing.

## Implementation Notes
Traced both failures to real, already-landed causes before fixing anything — neither was a tool bug.

1. Confirmed `next_available_id()`'s own logic (`tools/gate_checks/parity_updater_static.py:137-176`)
   is correct: it tracks max numeric suffix per full id-family prefix (never globally), and reports
   whichever family belongs to the shard's own last matching entry, by explicit design (documented in
   its own docstring). Confirmed directly against the real file's tail
   (`grep "^- id:" docs/parity_ledger/world_dynamics.yaml | tail -3` → `WORLD-123`, `WORLD-124`,
   `WORLD-CULT-004`) that `WORLD-CULT-004` really is the last entry, making `WORLD-CULT-005` the
   correct output — the test's `"WORLD-124"` expectation was simply stale.
2. Independently re-computed the live `missing_test_path` scan directly via a standalone Python script
   (not trusting the CI failure's own number blindly) — confirmed **1316**. Checked the specific
   candidate entries this session's own tickets touched (`WORLD-085`, `WORLD-109`, `WORLD-124`,
   `WORLD-CULT-004`) for a `test_path` transition from `null` to real — found `WORLD-085` (`status:
   verified`) now has `test_path:
   'tests/unit/world/test_world_dynamics.py::test_boss_spawn_is_idempotent_even_if_existing_boss_left_region'`,
   confirming it was the exact -1 drift source, landed by `TCK-20260904-LAIR-ENTITY-ANCHOR`'s own
   Parity phase.

Updated both test files' hardcoded expectations to match the real, current state, with fresh
comments citing the exact ticket/entry responsible — matching each file's own established
running-changelog documentation convention (both files already had multiple prior such updates from
earlier tickets, e.g. `TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT`).

## Test Summary
Ran the two specific tests directly:
`pytest tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path -v`
→ **2 passed**, 0 failures. Matches CI's own exact failing tests (confirmed via real CI logs pulled
directly from the failing run, not assumed from the job name).

## Files Changed
- `tests/tools/test_parity_updater_static.py` — updated expected value `"WORLD-124"` →
  `"WORLD-CULT-005"` + updated comment.
- `tests/tools/test_parity_index_baseline.py` — updated expected value `1317` → `1316` + appended a
  new changelog-comment entry.

No production (`src/`) code or parity-ledger YAML content touched — both changes are test-baseline
corrections only.

## Completion Summary
Fixed two real, hardcoded parity-tooling test baselines that this session's own legitimate M4 ticket
work caused to drift, both matching the documented "hardcoded baseline drift" class CLAUDE.md already
names for exactly this test file. Neither was a tool bug: `next_available_id()`'s per-family-suffix
logic and the live `missing_test_path` scan both work correctly; the tests' own hardcoded expectations
were simply stale relative to real, already-landed, already-verified parity-ledger content
(`WORLD-124`/`WORLD-CULT-004` added by `TCK-20260904-CAMP-NEST-CLASSIFICATION`/
`TCK-20260904-SETTLEMENT-CULTURE-READ`; `WORLD-085` gaining a real `test_path` from
`TCK-20260904-LAIR-ENTITY-ANCHOR`). Fixed both with fresh, cited evidence rather than blindly bumping
numbers. Together with the already-landed `TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH`,
this closes out CI's "API / tools / logging" job — confirmed via real CI logs that these were the only
2 remaining failures after that sibling hotfix landed.
