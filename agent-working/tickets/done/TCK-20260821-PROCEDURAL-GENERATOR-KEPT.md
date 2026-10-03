---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-PROCEDURAL-GENERATOR-KEPT
phase: done
date: 2026-08-21
tags: [world, documentation]
---

# TCK-20260821-PROCEDURAL-GENERATOR-KEPT

## Title
Confirm WorldProceduralGenerator is an intentionally preserved legacy path, not dead code

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
The epic asked to investigate whether WorldProceduralGenerator is safe to delete as dead code, or whether it's intentionally kept for a reason not surfaced by the epic's own investigation. Investigation found the epic's premise was wrong: WorldProceduralGenerator is explicitly documented in docs/world/generator_contract.md as the intentionally preserved 'Spec-based (legacy, preserved)' generation path, and carries a live P0 parity claim (SUBSTRATE-NEW-002) in docs/parity_ledger/substrate.yaml. This ticket records that finding and closes the question with a decision to keep the class, rather than deleting it.

## Scope
- Document, in the ticket, the authoritative evidence that WorldProceduralGenerator (src/worldgeneration/generator.py) is an intentionally preserved 'Spec-based (legacy, preserved)' generation path per docs/world/generator_contract.md and a live P0 parity claim (SUBSTRATE-NEW-002 in docs/parity_ledger/substrate.yaml).
- Record that TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY invested real engineering effort in this class 13 days before this concern was raised, with full knowledge of its 'unwired to any CLI' status — and that the 'unwired' concern was itself root-caused to a predecessor's missing .load_all() call, not a defect in this class.
- Close the epic's Scope item 5 with a decision NOT to delete WorldProceduralGenerator, correcting the epic's own false 'confirmed dead code' premise.
- Name, as a process note, that call-site-only grep methodology for 'is X dead code' has now produced two false leads in this codebase's recent history (this one and the sibling rendering epic's C10), worth flagging for future investigations of this shape.

## Out of Scope
- Deleting WorldProceduralGenerator (src/worldgeneration/generator.py) or any of its files, tests, or references.
- Retiring Compliance IDs WORLD-GEN-003/004 — not applicable since the class is being kept, not removed.
- Editing .github/workflows/test.yml or removing any of the other 3 test files in tests/unit/worldgeneration/.

## Acceptance Criteria
- [x] The ticket records the finding that WorldProceduralGenerator is documented (docs/world/generator_contract.md) and parity-tracked (docs/parity_ledger/substrate.yaml, SUBSTRATE-NEW-002, P0, status: verified) as an intentionally preserved legacy generation path.
- [x] The ticket closes with an explicit decision NOT to delete WorldProceduralGenerator, correcting the epic's own 'likely dead code' premise.
- [~] `grep -rln "WorldProceduralGenerator" src/ tools/ tests/` returns 4 files, not the 2 this AC anticipated: `src/worldgeneration/generator.py`, `tests/unit/worldgeneration/test_generator.py` (the expected real call sites), plus `tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json` and `tests/tools/fixtures/kgmcp_phase5_working_log_snapshot.json`. Verified these 2 extra hits are frozen JSON test fixtures for an unrelated tool (kgmcp/knowledge-gateway monitoring test snapshots) that happen to contain the string "WorldProceduralGenerator" inside captured historical prose (e.g. a snapshotted working-log sentence about it being "unwired to any CLI") — not real Python call sites, not new references introduced by this ticket, and not something this ticket's own investigation created. Reporting this honestly rather than silently claiming an exact match: the AC's literal wording is not satisfied, but the substance it protects (no new/missed real call sites) is confirmed true.
- [x] tests/unit/worldgeneration/ retains its other 3 test files regardless of outcome; .github/workflows/test.yml requires no edit — confirmed, neither was touched by this ticket.

## Related Tickets
- TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN
- TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY
- TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION
- TCK-20260612-WORLDGEN-CONTRACT

## Related Docs
- docs/world/generator_contract.md
- docs/parity_ledger/substrate.yaml
- docs/plans/world_generation_organic_terrain_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/worldgeneration/generator.py
- tests/unit/worldgeneration/test_generator.py

## Assumptions / Open Questions
None.

## Implementation Notes
Verified every claim in this ticket's Request Summary against real repo state, not trusted blindly:

1. **`docs/world/generator_contract.md`** (read directly): line 28's generation-strategy table lists
   `**Spec-based** (legacy, preserved) | WorldProceduralGenerator | GenerationIntentSpec +
   CatalogRepository | ResolvedWorldBundle | Builds a WorldSpec directly from catalog records (no
   modules)`. Line 88 gives its entry point signature. Line 317 maps Compliance ID `WORLD-GEN-003` to
   `WorldProceduralGenerator`'s constructor/`generate()`. This is unambiguous, deliberate, authoritative
   documentation of the class as a currently-supported legacy path — not an oversight.
2. **`docs/parity_ledger/substrate.yaml`** (read directly): `SUBSTRATE-NEW-002` (line 3836) is real,
   `status: verified`, `priority: P0`, with `v2_evidence` citing `generator_contract.md`,
   `generator.py:57`'s `DeterministicRNG(intent.seed)` construction, `TCK-20260619-P0-DETERMINISM`
   (the ticket that replaced bare `random.Random` with `DeterministicRNG` here), and 2 real test
   files. A live P0 parity claim cannot be deleted-out-from-under without violating the parity
   ledger's own P0 discipline.
3. **`TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY`** (`tickets/done/`, confirmed present, dated
   2026-08-08 — exactly 13 days before this ticket's 2026-08-21 date): confirmed this ticket invested
   real engineering effort in `WorldProceduralGenerator` with contemporaneous knowledge of its
   "unwired to any CLI" status, and that status was itself root-caused elsewhere (a predecessor's
   missing `.load_all()` call), not a defect in this class — corroborating that "unwired to CLI" is
   not evidence of abandonment.
4. **Call-site grep** (`grep -rln "WorldProceduralGenerator" src/ tools/ tests/`): returned 4 files,
   not the 2 the AC anticipated. The 2 extra hits (`tests/tools/fixtures/kgmcp_phase5_*_snapshot.json`)
   are frozen test fixtures for an unrelated monitoring tool containing the string inside captured
   historical prose, not real call sites. See AC checklist above for full disclosure — reported
   honestly rather than glossed over, per Gate Integrity.
5. **Process note** (per Scope item 4): this is the second time in this codebase's recent history
   that call-site-only grep methodology has produced a false "likely dead code" lead for a class that
   turned out to be intentionally preserved and actively documented/parity-tracked (the sibling
   rendering epic's own C10 item was the first). Worth flagging for any future "is X dead code"
   investigation: check `docs/world/*_contract.md` and `docs/parity_ledger/` for a live claim before
   concluding from call-site absence alone.

**Decision: WorldProceduralGenerator is KEPT.** The epic's own "likely dead code, confirm before
deleting" premise (Scope item 5) is corrected — it is not dead code, and this ticket does not delete
it, retire its Compliance IDs, or touch its tests/CI wiring.

## Test Summary
No test changes — this is a documentation/decision-record ticket, no code touched. Confirmed
`tests/unit/worldgeneration/` still contains its other 3 test files (`grep -rl` scoped to that
directory shows 4 files total, unchanged) and `.github/workflows/test.yml` has zero diff.

## Files Changed
- `tickets/inprogress/TCK-20260821-PROCEDURAL-GENERATOR-KEPT.md` — this file: Status, Acceptance
  Criteria (including honest disclosure of the grep-count discrepancy), Implementation Notes, Test
  Summary, Files Changed, Completion Summary.

## Completion Summary
Confirmed `WorldProceduralGenerator` (`src/worldgeneration/generator.py`) is a genuinely,
authoritatively documented and P0-parity-tracked "Spec-based (legacy, preserved)" generation path —
not dead code — correcting the epic's own investigation premise. No deletion, no Compliance ID
retirement, no test/CI changes. Flagged a recurring false-lead pattern in call-site-only "is X dead
code" methodology for future investigations of this shape.
