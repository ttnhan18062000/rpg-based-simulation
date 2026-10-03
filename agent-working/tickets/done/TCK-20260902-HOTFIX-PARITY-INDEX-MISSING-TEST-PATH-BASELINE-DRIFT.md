---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT
phase: done
date: 2026-09-02
tags: [testing]
---

# TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT

## Title
Update stale `live_missing == 1320` baseline literal in `test_baseline_manifest_does_not_coerce_missing_test_path` to 1317

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
(line 154) hardcodes `assert live_missing == 1320`, a second-order guard against silent large swings
in the count of `docs/parity_ledger/*.yaml` entries with `status in (verified, divergent)` and a
null/missing `test_path`, on top of the primary assertion that the manifest's own reported count
matches a fresh independent live scan (line 120). This is a documented, expected-to-drift value —
the test's own multi-paragraph changelog comment (lines 121-153) already tracks 6 prior identical
hotfixes moving it down from 1343 to 1320 as parity ledger entries legitimately gain real
`test_path` citations over time.

`TCK-20260902-PARITY-TEST-PATH-GAP` (done, same worktree) repointed 3 P0 parity ledger entries from
`test_path: null` to real, verified test citations — `SUB-051` (`docs/parity_ledger/substrate.yaml`),
`TOWN-027` and `TOWN-076` (`docs/parity_ledger/town_resource.yaml`) — dropping the live count from
1320 to 1317. This ticket updates the stale literal and extends the changelog comment, following the
exact same pattern as every prior hotfix in this series.

## Scope
- Update `tests/tools/test_parity_index_baseline.py` line 154 from `assert live_missing == 1320` to
  `assert live_missing == 1317`.
- Append one new dated bullet to the existing changelog comment block (lines 121-153), in the same
  prose style as the prior 6 entries, documenting the 1320→1317 drop: citing
  `TCK-20260902-PARITY-TEST-PATH-GAP`, the 3 entry IDs (`SUB-051`, `TOWN-027`, `TOWN-076`), their
  ledger files, and their new real `test_path` citations.

## Out of Scope
- Any change to `docs/parity_ledger/*.yaml` content itself — those writes already landed under
  `TCK-20260902-PARITY-TEST-PATH-GAP` via `tools/parity_ledger_writer.py`.
- Any change to `build_manifest` / `tools/parity_index_baseline.py` logic or the primary assertion
  (line 120) — only the secondary hardcoded swing-guard literal and its changelog comment are in
  scope.
- Any other `missing_test_path_count`-adjacent entries surfaced incidentally elsewhere (e.g. the
  widespread pre-existing null-`test_path` pattern noted as out of scope in
  `TCK-20260902-PARITY-TEST-PATH-GAP`) — not this ticket's concern.

## Acceptance Criteria
- [x] Line 154 of `tests/tools/test_parity_index_baseline.py` reads `assert live_missing == 1317`.
- [x] A fresh, independent live scan (status in verified/divergent, null/missing `test_path`,
  across all `docs/parity_ledger/*.yaml`) genuinely returns `1317`, re-verified independently of
  the originating ticket's own claim, before the literal is changed.
- [x] The changelog comment block gains exactly one new dated bullet, in the same prose format as
  the existing 6, naming `TCK-20260902-PARITY-TEST-PATH-GAP`, the 3 entry IDs/files, and their new
  `test_path` citations.
- [x] `pytest tests/tools/test_parity_index_baseline.py -v` passes in full.

## Related Tickets
- `TCK-20260902-PARITY-TEST-PATH-GAP` (done) — the ticket whose legitimate ledger repoints caused
  this drift (1320 → 1317).
- `TCK-20260830-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT`,
  `TCK-20260831-ITEM-INSTANCE-HISTORY`, `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION`, and the
  earlier entries named in the test's own comment history (`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC`,
  `TCK-20260819-HOTFIX-RNG-BOUNDARY-VIOLATION-BACKOFF-JITTER`,
  `TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION`,
  `TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD`,
  `TCK-20260824-ALLOCATE-AP-BRANCH-DECISION`) — the identical prior instances of this same drift
  pattern.

## Related Docs
- `docs/parity_ledger/schema.json` — defines the `verified`/`divergent` + `test_path` requirement
  this count tracks compliance against.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts.

## Related Code Areas
- `tests/tools/test_parity_index_baseline.py` (the only file changed).
- `docs/parity_ledger/substrate.yaml`, `docs/parity_ledger/town_resource.yaml` — source of the
  count change (already modified by `TCK-20260902-PARITY-TEST-PATH-GAP`, not touched here).

## Assumptions / Open Questions
- Assumes the live count is genuinely 1317 at the time of this ticket, independently re-verified by
  running the same scan logic the test itself uses (not just trusting the 1320→1317 claim from the
  originating ticket) — confirmed: a fresh scan returned exactly 1317 across all 9
  `docs/parity_ledger/*.yaml` files.
- Assumes no other ledger writes landed between `TCK-20260902-PARITY-TEST-PATH-GAP`'s completion and
  this ticket's scan that would change the count further — the live scan performed during this
  ticket's own scoping is the authoritative source, not an assumption carried from the originating
  ticket.
- `layer: testing` chosen to match the file's own established layer (mirrors all 6 prior identical
  hotfixes in this series).

## Implementation Notes
Changed `tests/tools/test_parity_index_baseline.py` line 154 from `assert live_missing == 1320` to
`assert live_missing == 1317`, and appended one new dated bullet to the existing changelog comment
block (after the prior bullet ending "...status_effect_update path)."), in the same prose style,
documenting the drop to 1317 via `TCK-20260902-PARITY-TEST-PATH-GAP`'s repoint of `SUB-051`
(`docs/parity_ledger/substrate.yaml`) to
`tests/unit/core/test_rpg_math.py::test_combat_stats_stay_within_bounds_after_normal_recalculation`,
`TOWN-027` (`docs/parity_ledger/town_resource.yaml`) to
`tests/unit/social/test_teach.py::test_teach_resolves_target_capability_blocker_not_teacher`, and
`TOWN-076` (`docs/parity_ledger/town_resource.yaml`) to
`tests/unit/resource/test_loot_channeling.py::test_loot_corpse_completion_transfers_all_item_stacks`
— a 3-entry net drop, independently re-verified via a fresh live scan before editing (see Test
Summary). No other lines in the file were touched.

## Test Summary
- Independent live scan (pre-edit verification): scanned all `docs/parity_ledger/*.yaml` files for
  `status in (verified, divergent)` entries with a null/missing `test_path`, matching the test's own
  logic — result: `live_missing = 1317` (per-file breakdown: combat_movement.yaml=241,
  faction.yaml=0, infrastructure.yaml=149, progression.yaml=90, social_narrative.yaml=166,
  strategic_cognition.yaml=142, substrate.yaml=309, town_resource.yaml=131, world_dynamics.yaml=89).
- `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest
  tests/tools/test_parity_index_baseline.py -v` — all tests in the file passed after the edit,
  including `test_baseline_manifest_does_not_coerce_missing_test_path`.

## Files Changed
- `tests/tools/test_parity_index_baseline.py` — updated the hardcoded `live_missing` baseline
  literal from `1320` to `1317` (line 154) and appended one new dated changelog bullet to the
  existing comment block.

## Completion Summary
Re-verified via an independent fresh live scan that the true count of `verified`/`divergent` parity
ledger entries with a null `test_path` is now 1317 (down from 1320), matching the net -3 effect of
`TCK-20260902-PARITY-TEST-PATH-GAP`'s legitimate repoints of `SUB-051`, `TOWN-027`, and `TOWN-076` to
real test citations. Updated the stale hardcoded literal at
`tests/tools/test_parity_index_baseline.py:154` from `1320` to `1317` and appended a matching dated
changelog bullet documenting the cause, following the identical format used by the 6 prior hotfixes
in this same drift series. `pytest tests/tools/test_parity_index_baseline.py -v` passes in full.
