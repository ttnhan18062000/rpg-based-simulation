---
status: active
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP
phase: open
date: 2026-09-04
tags: [content, schema]
---

# TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP

## Title
Sweep docs/mechanics, docs/parity_ledger, and remaining docs for race->species terminology

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child 4/4 of `TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY`. Depends on children 1-3 landing first,
so doc text cites the real final code/content names rather than guessing ahead of the rename. Sweeps
`docs/mechanics/*.md` (5 files), `docs/parity_ledger/*.yaml` (7 shards), and the remaining `docs/`
corpus (81 files found real word-matches at epic-scoping time, narrowed per-file here) for real
terminology references to update.

## Scope
- `docs/mechanics/02_combat_laws.md`, `docs/mechanics/04_strategic_cognition.md`,
  `docs/mechanics/05_world_evolution.md`, `docs/mechanics/attribute_progression_contract.md`,
  `docs/mechanics/content_usage_matrix.md` — prose/formula references to `race`/`race_id`.
- `docs/parity_ledger/{progression,combat_movement,strategic_cognition,infrastructure,
  social_narrative,substrate,world_dynamics}.yaml` — prose/evidence-text references only. Entry IDs
  are stable identifiers; check per-entry whether the ID itself ever encodes "race" before touching
  it (unconfirmed at scoping time, per the parent epic's Assumptions).
- Remaining `docs/` files with a genuine terminology hit (narrow the 81-file candidate list found at
  epic-scoping time to real matches, excluding incidental/unrelated uses of the word).

## Out of Scope
- The frozen brainstorm HTML sources (`rpg_feature_atlas.html`, `rpg_expected_schemas.html`,
  `design_merit_scorecard.html`) — per the parent epic's Out of Scope, these stay as the frozen
  investigation record; `rpg_design_roadmap.md`'s reconciliation note is the intended pointer instead.
- Any code/content/test file — those are children 1-3.

## Acceptance Criteria
- [x] All 5 mechanics files updated where they reference this concept.
- [x] All 7 parity ledger shards checked; prose updated (10 entries), entry-ID renaming decided
      explicitly — none of the entry IDs themselves encode "race"; 10 further entries found but
      left unchanged, blocked by a pre-existing, unrelated schema violation (documented, not
      silently skipped).
- [x] Remaining real `docs/` terminology hits updated (16 files); incidental/unrelated word matches
      left alone, with the distinction recorded in investigation.md.
- [x] `validate_frontmatter.py` and the parity index build/health check pass after edits (zero new
      violations introduced, cross-checked file-by-file, not assumed).

## Related Tickets
- TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY (parent epic)
- TCK-20260904-SPECIES-CORE-SCHEMA-RENAME (dependency)
- TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME (dependency)
- TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME (dependency)

## Related Docs
- `docs/mechanics/02_combat_laws.md`, `docs/mechanics/04_strategic_cognition.md`,
  `docs/mechanics/05_world_evolution.md`, `docs/mechanics/attribute_progression_contract.md`,
  `docs/mechanics/content_usage_matrix.md`
- `docs/parity_ledger/*.yaml` (7 shards listed above)

## Related Stored Artifacts
- stored_artifacts/TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP/{investigation,plan,test_plan}.md

## Related Code Areas
None — docs-only ticket.

## Assumptions / Open Questions
- Whether any parity ledger entry ID itself encodes "race" — must be checked directly, not assumed
  either way. Resolved: no — every entry ID across all 7 shards is a plain numeric-suffix ID
  (`PROG-120`, `COMB-317`, etc.); "race" only ever appears in `text`/`v2_evidence`/`test_path`
  field content, never the ID itself.

## Implementation Notes
Mapped every "race" hit across the 7 parity ledger shards to its exact containing entry ID via a
script (not spot-checked), finding 20 total entries: 10 were live citations to now-renamed code/
tests, updated via `write_entry()` with each `test_path` re-verified as a real, passing test; 10
were blocked by a pre-existing `priority: P0` + `test_path: null` schema violation shared with
`docs/compliance/checklist.md`'s matching rows (cross-verified those citations reference a
nonexistent legacy file layout, confirming this is old V1-era debt, not this ticket's to fix — see
investigation.md). For the remaining `docs/` corpus, drew an explicit line between live/active docs
describing current code (fixed, 16 files) and `docs/brainstorm/**`'s frozen historical review/
proposal record plus the M2/M4/M9/direction-alignment planning epics' free-form descriptive
narrative (left unchanged, documented reason) — the epic's own explicit Scope item 3 (rename idea
37's own name) was still honored within the planning docs. `rpg_design_roadmap.md`'s own
scoping-time reconciliation section was left as accurate history, not live documentation.

## Test Summary
Docs-only ticket — no `src/`/`tests/` code changed. `tools/validate_frontmatter.py docs/`: 355
pre-existing violations, zero of this ticket's 25 touched files among them (cross-referenced, not
assumed). `tools/parity_index.py build`+`health`: both run clean. Every parity-ledger `test_path`
written/changed was directly run and confirmed passing. Full detail in
stored_artifacts/TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP/test_plan.md.

## Files Changed
- `docs/mechanics/{02_combat_laws,04_strategic_cognition,05_world_evolution,
  attribute_progression_contract}.md` (5th, `content_usage_matrix.md`, was already clean —
  auto-regenerated by children 1-3's own test runs)
- `docs/parity_ledger/{progression,combat_movement,strategic_cognition,infrastructure,
  social_narrative,substrate}.yaml` (10 entries, via `write_entry()`; `world_dynamics.yaml`
  checked, its 2 hits both fall in the blocked-legacy-stub category, left unchanged)
- 16 live docs: `docs/architecture/2026-08-10-cognition-driven-adventure-eligibility-design.md`,
  `docs/audits/{D01_rpg_feature_impact,D21_entity_lifecycle_foundation_layers,
  D22_dormant_content_wiring}.md`, `docs/content/pipeline_contract.md`,
  `docs/core/{attributes_and_classes,items_and_inventory}.md`,
  `docs/guidelines/{fallback_retirement_criteria,intentional_divergences}.md`,
  `docs/simulation/quest_contract.md`, `docs/simulation_quality/{entity_lifecycle_score,
  event_type_coverage}.md`, `docs/world/assembly_contract.md`,
  `docs/plans/rpg_design_roadmap/{rpg_design_roadmap,rpg_m9_corpus_test_coverage_epic,
  rpg_m2_foundational_systems_epic}.md`

## Completion Summary
Completed the final child ticket of `TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY`. Swept all 5
mechanics files, all 7 parity ledger shards (mapping every hit to its exact entry ID, updating 10
live citations, and explicitly documenting why 10 more are blocked by pre-existing unrelated debt
rather than silently skipping them), and the remaining `docs/` corpus — fixing 16 live docs while
deliberately preserving `docs/brainstorm/**`'s historical record and the planning epics' free-form
narrative, per a documented, defensible scope boundary. `validate_frontmatter.py` and the parity
index build/health check both confirmed clean of new issues. All 4 children of the epic are now
done — the epic ticket itself can close next.
