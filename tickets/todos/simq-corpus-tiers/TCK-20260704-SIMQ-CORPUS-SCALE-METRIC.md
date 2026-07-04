---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-SCALE-METRIC
phase: open
date: 2026-07-04T12:17:33Z
tags: [simulation_quality, world-content, corpus, faction, scale-metric]
---

# TCK-20260704-SIMQ-CORPUS-SCALE-METRIC

## Title
Track "distinct populated factions" as an explicit per-world scale metric

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 found that
"distinct factions actually assigned to a population" ranges 2-9 across the 10 worlds under
`data/worlds/` (`wilderness_survival`: 2, `frontier_extended`: 9), and that this is a genuine,
currently-untracked per-world scale axis — distinct from `AuthoritativeState.factions`, which is
always the full 16-entry catalog regardless of content and therefore not meaningful as a per-world
signal on its own (investigation.md §2, table note: "Factions in catalog" is a global constant).
`world_compile_report.json` already tracks entity/region/resource-node/building/quest counts per
world but has no field for populated-faction count. This ticket adds it, per investigation.md §4
open question 1.

## Scope
1. Locate the `world_compile_report.json` generation code path (likely `WorldCompiler.compile()` or
   a report-writing helper it calls) and add a `distinct_populated_factions` field — the count of
   unique faction IDs actually assigned to at least one entity's population in the compiled world
   (matching the definition used in investigation.md §2's table, not the raw catalog count).
2. Verify the new field against investigation.md §2's table for all 10 existing worlds as a
   correctness check (e.g. `wilderness_survival` → 2, `frontier_extended` → 9) — recompile each
   world and confirm the generated report matches the investigation's numbers exactly, or document
   and resolve any discrepancy found.
3. Add a corresponding row/column to `docs/simulation_quality/eval_matrix_results.md`'s world-scale
   reporting section, alongside the existing entity/region/resource-node scale reporting.
4. Add a unit test (likely alongside or extending
   `tests/unit/worldassembly/test_corpus_diversity.py`, created by
   `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`) asserting the new field is present and numerically
   correct for at least 2-3 of the existing worlds with known faction counts from the investigation
   table.
5. Recompile all 10 worlds under `data/worlds/` so `world_compile_report.json` picks up the new
   field (content/report regeneration only — no world.yaml changes, no calibration grade changes
   expected since this is purely additive reporting).
6. Run `make evaluate --dry-run` to confirm zero grade regressions (this ticket should not change
   any pillar score, only add a reporting field).

## Out of Scope
- Authoring any new worlds (that is tickets 4-8 in this batch) — this ticket only instruments
  existing worlds and the reporting pipeline
- Changing faction assignment logic, `FactionState`, or `WorldCompiler`'s faction-resolution
  behavior — this is a read-only count derived from already-resolved state, not a new mechanic
- Adding the metric to any SimQ pillar's scoring formula (this is a diagnostic/reporting metric, not
  a scored signal — do not conflate with FACTION pillar scoring)

## Acceptance Criteria
- [ ] `world_compile_report.json` includes a `distinct_populated_factions` field for every
      compiled world
- [ ] Field value matches investigation.md §2's table exactly for all 10 existing worlds after
      recompile (or any discrepancy is investigated and documented, not silently accepted)
- [ ] `docs/simulation_quality/eval_matrix_results.md` world-scale reporting section includes the
      new metric alongside entity/region/resource-node counts
- [ ] New/extended unit test asserts correctness of the field for at least 2-3 worlds
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions (purely additive change)
- [ ] `make knowledge-index-update` run if `docs/` files were modified

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — this metric should be referenced as a scale-diversity
  criterion in the taxonomy doc's future-classification section
- TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS — will use this metric to verify its many-factions/
  small-map stress world actually achieves a high distinct-faction count
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — established `test_corpus_diversity.py`, the likely home
  for this ticket's new/extended test

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 (scale diversity
  table, populated-faction column) and §4 open question 1
- `docs/simulation_quality/eval_matrix_results.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — precedent for corpus-wide recompile
  + verification discipline

## Related Code Areas
- `src/worldbuilding/` — `WorldCompiler.compile()` and wherever `world_compile_report.json` is
  written
- `data/worlds/*/world_compile_report.json` — all 10 worlds, regenerated
- `tests/unit/worldassembly/test_corpus_diversity.py`
- `docs/simulation_quality/eval_matrix_results.md`

## Assumptions / Open Questions
- UQ-1: Is "populated" defined as "at least one entity currently assigned this faction ID at
  compile time" (investigation.md's apparent definition) or does it need to also account for
  factions that gain population only via runtime spawn events? Scope this ticket to the compile-time
  definition (matching investigation.md's own methodology) — runtime-population drift is a
  separate, more complex signal and out of scope here.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
