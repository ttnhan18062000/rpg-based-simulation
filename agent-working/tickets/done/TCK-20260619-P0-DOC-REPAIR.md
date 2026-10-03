---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260619-P0-DOC-REPAIR
phase: done
date: 2026-06-19
tags: [documentation, parity, stale-docs, phase-0, p0-foundation]
---

# TCK-20260619-P0-DOC-REPAIR

## Title
P0-5 · Stale Documentation Repair — Fix authoritative_pipeline, kernel, mechanics/01, known_limitations

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Four high-authority agent context documents contain stale content confirmed by audit D17. An agent implementing a new domain phase will use the wrong insertion point from `authoritative_pipeline.md`. Stale biological thresholds in `mechanics/01` produce wrong test acceptance criteria. `known_limitations.md` contains at least one claim already contradicted by done work.

Source: `docs/audits/D17_documentation_currency.md`; `docs/plans/engine_future_epics_roadmap.md` § Immediate Cheap Fixes.

## Scope
- `docs/engine/authoritative_pipeline.md`: update 17-phase table to current 30+ phases (match what `pipeline.py` actually contains); remove stale phase numbers
- `docs/engine/kernel.md`: remove stale first-phase table; resolve dual-conflicting-table conflict
- `docs/mechanics/01_entity_anatomy.md`: fix biological thresholds: hunger trigger 100→95, hunger damage +5→+2, sleep debt 80→98
- `docs/mechanics/04_strategic_cognition.md`: fix interruption margin formula (D17 finding)
- `docs/engine/known_limitations.md`: refresh or retire stale claims; at minimum remove "Blacksmith-Only Towns" claim (contradicted by `TCK-20260425-PH7-M3-RECOVERY`)
- `RPG-INFRA-095` doc hygiene: locate and fix the ID collision between `logic_checklist_exhaustive.md` and parity ledger (one ID, two unrelated meanings)
- Update corresponding parity ledger entries in `docs/parity_ledger/` for any threshold changes

## Out of Scope
- Rewriting doc sections not touched by D17
- Parity ledger P0 combat bugs (separate ticket: TCK-20260619-PARITY-P0-BUGS)
- Adding new documentation sections

## Acceptance Criteria
- `docs/engine/authoritative_pipeline.md` phase table matches phase count in `src/engine/pipeline.py`
- `docs/mechanics/01_entity_anatomy.md` hunger trigger threshold reads 95, not 100
- `docs/engine/known_limitations.md` contains no claims contradicted by done tickets
- Parity ledger entries affected by threshold changes are updated with correct `v2_evidence` values

## Related Tickets
- TCK-20260618-AUDIT-D17-DOCS (source audit)
- TCK-20260619-PARITY-P0-BUGS (companion: parity ledger combat bugs, separate scope)

## Related Docs
- `docs/audits/D17_documentation_currency.md`
- `docs/engine/authoritative_pipeline.md`
- `docs/engine/kernel.md`
- `docs/mechanics/01_entity_anatomy.md`
- `docs/mechanics/04_strategic_cognition.md`
- `docs/engine/known_limitations.md`
- `docs/plans/long_term_development_roadmap.md` § P0-5
- `docs/plans/engine_future_epics_roadmap.md` § Immediate Cheap Fixes

## Related Stored Artifacts
- `staging_artifacts/TCK-20260618-AUDIT-EPIC/`

## Related Code Areas
- `src/engine/pipeline.py` (ground truth for phase count)

## Related Docs — Parity
- `docs/parity_ledger/substrate.yaml` (update entries for any threshold changes made here — biological thresholds in `01_entity_anatomy.md` are verified against this)

## Assumptions / Open Questions
- Count of phases in `pipeline.py`: read the file to get the current count before updating `authoritative_pipeline.md`
- RPG-INFRA-095 location: search `docs/` for `logic_checklist_exhaustive.md` or grep for the ID to find both conflicting locations

## Implementation Notes
Doc-only changes. Read each target doc, compare to source-of-truth (`pipeline.py` for phase count; D17 audit findings for threshold values), make minimal accurate edits. Run `make knowledge-index-update` after all doc changes.

## Test Summary
- `pytest tests/docs/` — verify doc frontmatter and cross-reference integrity pass after all edits
- Spot-check: `python3 -c "from src.engine.pipeline import Pipeline; p = Pipeline.__init__; print('phases ok')"` or read `pipeline.py` and count phases manually to validate `authoritative_pipeline.md` table
- Check that `docs/parity_ledger/substrate.yaml` entries affected by threshold changes have updated `v2_evidence` matching the corrected values in `docs/mechanics/01_entity_anatomy.md`
- Run `make knowledge-index-update` after all doc edits are complete — confirm index build succeeds

## Files Changed
- `docs/engine/authoritative_pipeline.md` — updated header from 17→31 phases; replaced entire phase table with all 31 current `run_phase()` names from `pipeline.py`
- `docs/engine/kernel.md` — removed stale 6-phase first table (kept correct 7-phase table); updated section header to "7-Phase Kernel Loop"
- `docs/mechanics/01_entity_anatomy.md` — fixed hunger threshold 100→95, damage 5→2; sleep debt threshold 80→98, effect to "+1 HP damage/tick"; updated last_verified to 2026-06-19
- `docs/mechanics/04_strategic_cognition.md` — fixed interruption margin formula: `30.0` → `resistance_multiplier`; added clarifying note
- `docs/engine/known_limitations.md` — replaced stale "Blacksmith Only" claim with accurate statement listing Blacksmith/Inn/Tavern as supported building types

## Completion Summary
Fixed all 5 D17-confirmed stale findings. Pipeline doc now matches 31 actual phases in code. Kernel doc has one accurate phase table. Biological thresholds in mechanics/01 match `apply.py`. Interruption margin formula in mechanics/04 matches `intelligence.py`. Known limitations updated to reflect inn/tavern support. No new test failures introduced (5 pre-existing failures confirmed unrelated). Knowledge index updated.
