---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT
phase: open
date: 2026-09-04
tags: [testing, registry]
---

# TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT

## Title
Repo-wide audit and repair of stale tests_v2/tests/rpg parity-ledger test_path citations, including P0 entries

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
`TCK-20260904-MATERIAL-POSSESSION-PREDICATE`'s Parity phase found that `docs/parity_ledger/town_resource.yaml`
has 6 entries (`TOWN-009`, `TOWN-010`, `TOWN-013`, `TOWN-014` citing `tests_v2/parity/test_resource_interaction_parity.py`;
`TOWN-011`, `TOWN-012` citing `tests/rpg/test_resource_conservation_v2.py`) whose `test_path` values
point at test files that no longer exist anywhere in this repo — both `tests_v2/` and `tests/rpg/` as
directories are entirely absent. All 6 are `status: verified`, `priority: P0`.

A repo-wide grep found this is not isolated to one shard: `tests_v2/`-style stale citations appear in
**combat_movement.yaml (9), strategic_cognition.yaml (10), substrate.yaml (5), social_narrative.yaml
(2), world_dynamics.yaml (2), progression.yaml (1), town_resource.yaml (15)**, plus 2 more
`tests/rpg/`-style citations — roughly **44 stale citations total**, spanning multiple shards and
multiple priority levels including P0. This is a pre-2026-09-02 test-tree migration whose ledger
citations were never propagated to their post-migration equivalents.

There is already a correct, real precedent for the fix within this same shard:
`docs/parity_ledger/town_resource.yaml`'s `TOWN-005`/`TOWN-006` entries were corrected on 2026-09-02
with an inline note ("path corrected... was `tests_v2/test_occupancy_conflicts.py` — that path never
existed in this repo, only in a pre-migration test tree"), re-pointing to
`tests/unit/movement/test_occupancy_conflicts.py`. This ticket generalizes that same fix across every
remaining stale citation.

## Scope
- Enumerate every stale `tests_v2/`/`tests/rpg/`-style `test_path` citation across all
  `docs/parity_ledger/*.yaml` shards (combat_movement.yaml, strategic_cognition.yaml, substrate.yaml,
  social_narrative.yaml, world_dynamics.yaml, progression.yaml, town_resource.yaml, and any others a
  fresh full-repo grep surfaces — the ~44 count above is from this session's own investigation and
  should be re-confirmed fresh, not assumed current).
- For each stale citation, determine the real post-migration equivalent test (if the test's coverage
  was preserved under a new path — matching the `TOWN-005`/`TOWN-006` precedent) or determine that the
  coverage was genuinely dropped during migration (in which case the entry's `status` may need to
  change, e.g. to `missing`, per the parity-ledger schema's real status vocabulary — do not force a
  `verified` status onto an entry whose real coverage no longer exists).
- Fix every entry via `tools/parity_ledger_writer.py::write_entry` (never hand-edit YAML), prioritizing
  the P0 entries first and confirming each fixed entry's cited test actually exists and passes.
- Run `python3 tools/parity_index.py build` after all fixes and confirm the health-finding counts for
  `missing_test_path`/`absent_file` genuinely decrease by the number of entries fixed.

## Out of Scope
- Any change to the actual mechanics/behavior the parity entries describe — this is a pure citation
  hygiene fix, not a behavior audit. If while investigating a stale citation this ticket finds the
  underlying mechanic itself has drifted from the entry's `text`, that's a separate finding to
  disclose (per this batch's own established process) but not necessarily fix in this ticket unless
  trivial.
- Building a general "prevent this class of drift" tool/pre-commit check — worth considering as a
  follow-up recommendation in this ticket's Completion Summary, but not required scope here.

## Acceptance Criteria
- A fresh, complete enumeration of every stale `tests_v2/`/`tests/rpg/` citation across all
  `docs/parity_ledger/*.yaml` shards is produced and recorded in investigation.md.
- Every enumerated entry is either (a) repointed to its real post-migration test path with the fix
  verified by actually running that test, or (b) has its `status` corrected to accurately reflect that
  coverage was lost, with a `divergence_note` explaining why — no entry is left silently pointing at a
  nonexistent file.
- All P0 entries among the stale set are fixed first and verified.
- `tools/parity_index.py build`'s health-finding counts for `missing_test_path`/`absent_file` show a
  real, measured decrease matching the number of entries fixed.

## Related Tickets
- TCK-20260904-MATERIAL-POSSESSION-PREDICATE (where this gap was found)

## Related Docs
- docs/parity_ledger/town_resource.yaml (TOWN-005/TOWN-006 — the real precedent fix to follow)
- docs/parity_ledger/combat_movement.yaml
- docs/parity_ledger/strategic_cognition.yaml
- docs/parity_ledger/substrate.yaml
- docs/parity_ledger/social_narrative.yaml
- docs/parity_ledger/world_dynamics.yaml
- docs/parity_ledger/progression.yaml
- docs/parity_ledger/schema.json

## Related Stored Artifacts
- stored_artifacts/TCK-20260904-MATERIAL-POSSESSION-PREDICATE/

## Related Code Areas
- docs/parity_ledger/*.yaml
- tools/parity_ledger_writer.py
- tools/parity_index.py

## Assumptions / Open Questions
- The exact ~44 count is from a single grep pass during a sibling ticket's Parity phase and should be
  treated as a starting estimate, not a final count — this ticket's own investigation must
  re-enumerate fresh.
- Some fraction of these citations may point to genuinely lost coverage (test deleted during migration
  with no replacement written), not just a renamed/moved file — the plan phase must distinguish these
  two cases per entry rather than assuming every citation has a live replacement.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled on completion.)
