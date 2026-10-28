---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS-STATUS-CHANGES
phase: open
date: 2026-10-29
tags: []
---

# TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS-STATUS-CHANGES

## Title
Parity-ledger paydown, child 1b: resolve the world_dynamics.yaml entries that have no proving test, by status change or a new test

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
This is a sibling of TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS (child 1 of TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN).
Child 1 hit its AC4 split limit: research on WORLD-001..048 projected about 35-45 status changes, against a limit of about 15.
Under rpg-planner (u24)'s ruling, child 1 keeps the test_path citations (PR A), and the remaining entries move here, in a second PR.

rpg-planner's ruling of 2026-10-29, relayed by lead-planner-u24 and then lead-planner (not an owner approval), word for word:
"(b) Status for each kind of entry
- Retired feature (code removed from src by a decision): `unsupported` + support_boundary.
  - The boundary text names the removal: the ticket or commit that retired it (`git log -S<symbol>` or the ticket corpus). \"grep finds nothing\" alone is not enough evidence.
  - Keep the entry's text and priority unchanged.
- Intended but never built, or absent with no retirement decision: `missing` + support_boundary saying what's absent. List these separately, because a missing P0 is a disclosure the owner should see.
- divergent: only where V2 behaviour exists and differs. It needs a test_path, so it never fits retired code.
- Code exists but no test proves it (the ~7: 012, 022, 042, 043, 048 …): write the proving test in the sibling (tests/** only, no src; rpg owns tests) and cite it. If the code read can't confirm the claimed behaviour, use what the evidence supports, give the reason, and flag it in the table.
- Removing entries: NOT allowed. The ledger is the history, and the epic's three ways stand.
- The draft table comes to rpg-planner entry by entry before the sibling's PR: id, old -> new status, evidence (test, or removal commit/ticket), and reason."

Dispatch needs its own owner go (lead-planner is asking; it is not covered by #715 6474978097 item 1).

## Scope
1. Every world_dynamics.yaml entry with a test_path error that child 1's PR A did not resolve by citation.
2. Classify each entry under the ruling: retired -> unsupported; never built -> missing; code exists but untested -> write a
   proving test in tests/** and cite it.
3. Draft table first, sent to rpg-planner-ubuntu, which relays it to rpg-planner for entry-by-entry review. The table gives:
   id, priority, old -> new status, evidence (the test, or the removal commit/ticket found with `git log -S` or the ticket corpus),
   the support_boundary text, and the reason. The `missing` entries are listed in a separate section.
4. Only after rpg-planner OKs the table: write via parity_ledger_writer.py, in chunks of about 20 entries.
5. As the last step after the final sync with origin/main, run the tighten under codebase-planner's four conditions (as in child 1's AC7).

## Out of Scope
- Removing any ledger entry (not allowed).
- Any src/ change. If a new test shows the code contradicts the entry, record that and stop; don't fix the code.
- Changing an entry's text or priority.
- Other ledger files; the schema; the proof_type enum.

## Acceptance Criteria
1. world_dynamics.yaml has 0 P0 test_path errors and 0 proof_type errors at the PR head, together with child 1.
2. rpg-planner OK'd the draft table before any ledger write, with the OK recorded in the ticket.
3. Every `unsupported` boundary names the retiring ticket or commit, with the evidence command recorded. "grep finds nothing" alone is not accepted.
4. The `missing` P0 entries are listed separately in the ticket and the PR body, as an owner-visible disclosure.
5. Every new test is in tests/** and passes. Every cited test was run.
6. The tighten meets codebase-planner's four conditions. `parity_ledger_schema check` and `make code-health` are clean.
7. (Added 2026-10-29) The 26 group-1/2/4 entries are `unsupported`, retired by owner decision #715 issuecomment-6476511728 (fold-in go 6476585722).

## Related Tickets
- TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS (child 1, PR A)
- TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN (parent)

## Related Docs
- docs/parity_ledger/world_dynamics.yaml, docs/parity_ledger/schema.json, docs/mechanics/05_world_evolution.md

## Related Stored Artifacts

## Related Code Areas
- docs/parity_ledger/world_dynamics.yaml, tests/**, codebase/baselines/parity_ledger_schema_baseline.json

## Assumptions / Open Questions
- Merge order: this sibling lands after PR A. The tighten is re-run on whichever lands last.

## Implementation Notes
Rulings, word for word: rpg_planner_table_rulings_2026-10-29.md (first and second ruling; rpg-planner (u24) via lead-planner-u24 and lead-planner; not owner approvals). The final table (final_table.md in the staging directory) was OK'd by rpg-planner on 2026-10-29, with group 4 and the group-3 recommendation added. Owner decision on section E: #715 issuecomment-6476511728 (retire groups 1, 2, 4; accept group 3 as authored), folded into this PR by the owner's go #715 issuecomment-6476585722.
- Section-E decision record: 26 entries written `unsupported` (14 superseded by a V2 structure, 6 gameplay features absent, 6 never built with no removal commit: 022, 026, 028, 035, 053, 089), each with its factual sentence, the V2 successor where the table gives one, and "Retired by owner decision #715 issuecomment-6476511728 (2026-10-29)". WORLD-054 stays `missing` (three corpus worlds with an isolated region, named in the boundary).
- Written through parity_ledger_writer.py in three commits (15, 14, 26 entries): 23 cited tests (status unchanged), WORLD-006/033/034/078 `unsupported`, WORLD-084 `divergent` (test_path test_calamity_boss_spawn plus tests/architecture/test_calamity_intensity_producer_unwired.py, cited and not edited; divergence_note names TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES), WORLD-054 `missing`.
- v2_evidence is untouched on the status-changed rows (rpg-planner-ubuntu's instruction): the legacy "exhaustive checklist audit" wording remains on them, a known caveat for the PR body.
- Slip, reverted before any commit: my first write pass wrote 12 of the then-held entries as `missing` in the working tree, before the hold message reached me. I discarded the file (`git checkout -- docs/parity_ledger/world_dynamics.yaml`) and re-wrote only the 29 released entries; no held entry was committed in any form before the fold-in go.
- Tests written (tests only, no src change; all run and passing): tests/unit/world/test_difficulty_tier_properties.py, test_region_lookup_properties.py, test_spawned_entity_validity.py, test_calamity_trigger_rules.py, test_terrain_names_cover_the_catalog.py, test_world_rules_are_deterministic.py, test_calamity_intensity_scales_regional_drain.py; tests/unit/engine/test_canonical_hash_covers_world_components.py; tests/unit/resource/test_loot_aborts_when_overweight.py; tests/integration/kernel/test_read_models_do_not_move_the_run.py. A corpus test for WORLD-054 failed on three worlds and was not kept (its result is the 054 boundary).
- The 091 test runs with audit_mode: two quiet runs of one seed can differ under machine load without it (known: TCK-20261005-TICK-BUDGET-THROTTLE-MAKES-NON-AUDIT-RUNS-WALL-CLOCK-DEPENDENT, TCK-20261009-AUTONOMOUS-LOOP-DRIFT-GUARD-RUNS-WITHOUT-AUDIT-MODE-SO-HOST-LOAD-FLIPS-IT; rpg-planner: no new ticket). The test includes a positive control.
- The guard test file tests/unit/core/test_same_name_class_guard.py is unrelated and untouched.

## Test Summary

## Files Changed

## Completion Summary
