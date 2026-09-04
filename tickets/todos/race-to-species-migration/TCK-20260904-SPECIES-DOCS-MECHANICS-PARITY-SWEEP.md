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
OPEN

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
- [ ] All 5 mechanics files updated where they reference this concept.
- [ ] All 7 parity ledger shards checked; prose updated, entry-ID renaming decided explicitly (not
      silently skipped or silently renamed).
- [ ] Remaining real `docs/` terminology hits updated; incidental/unrelated word matches left alone,
      with the distinction recorded.
- [ ] `validate_frontmatter.py` and the parity index build/health check pass after edits.

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
None yet.

## Related Code Areas
None — docs-only ticket.

## Assumptions / Open Questions
- Whether any parity ledger entry ID itself encodes "race" — must be checked directly, not assumed
  either way.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
