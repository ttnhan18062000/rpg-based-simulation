---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260623-DEAD-CODE-REMOVAL
phase: done
date: 2026-06-23
tags: [dead-code, audit-correction, D11, parity-ledger, doc-fix]
---

# TCK-20260623-DEAD-CODE-REMOVAL

## Title
D11 Audit Correction: Mark Misclassified "Orphan" Directories + Parity Ledger legacy_verified Pass

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Investigation during TCK-20260623-DEAD-CODE-REMOVAL (2026-06-23) proved the D11 audit's
"zero importer" classification is incorrect for all 9 directories. `src/quests/QuestService`
and `src/progression/LevelingService` are imported top-level by `src/engine/apply.py`
(the authoritative mutation path). `src/ai/GoalRegistry` and `ScoreModifierSystem` are
imported by `src/systems/strategic_systems/intelligence.py` (live AI decision code).
`src/content_semantics/` is imported by 10+ engine files. These are active modules, not
dead code.

No `src/` deletions will occur. The ticket now covers: (1) correcting the D11 audit doc,
(2) updating `open_audit_findings_backlog.md` Section 1E, (3) marking COMB-093–099,
STRAT-166–174, SOC-142 as `legacy_verified` in the parity ledger (they have `test_path: null`
with no live V2 test backing them, and the described behavior lives in V1 modules that are
actually live — not deleted V1 orphans as assumed), and (4) removing the dead reference to
`src/ai/states.py` in `design_patterns.md` (that file does not exist on disk).

## Scope

**Doc corrections (no src/ changes):**

1. `docs/audits/D11_dead_code.md` — add "Post-Audit Correction" section documenting that
   the zero-importer claim was incorrect; list confirmed live importers per directory;
   update status from `done` to `corrected`.

2. `docs/plans/open_audit_findings_backlog.md` — Section 1E: replace deletion plan with
   "INVALID — directories confirmed live (see TCK-20260623-DEAD-CODE-REMOVAL investigation)".

3. `docs/guidelines/design_patterns.md` — remove Section 5 reference to `src/ai/states.py`
   (file does not exist on disk; dead reference causing confusion).

**Parity ledger updates:**

4. `docs/parity_ledger/combat_movement.yaml` — entries COMB-093 through COMB-099:
   set `status: legacy_verified`, add `divergence_note: "Behavior implemented in live
   src/ai/score_modifiers.py (not a V1 orphan); test_path null because no dedicated
   unit tests exist for these score modifier behaviors in V2 test suite."`.

5. `docs/parity_ledger/strategic_cognition.yaml` — entries STRAT-166 through STRAT-174:
   same treatment — `legacy_verified` with note that src/ai/personality.py is live code,
   no dedicated V2 test_path available.

6. `docs/parity_ledger/social_narrative.yaml` — entry SOC-142:
   `legacy_verified` with same rationale.

**Knowledge index:**

7. Run `make knowledge-index-update` after all doc changes.

## Out of Scope

- Any deletion of src/ directories (all confirmed live)
- Adding new tests for V1 module behaviors
- Migrating or refactoring src/ai/, src/quests/, src/town/ etc. (separate migration epic
  if ever needed)
- Changing behavior of any live code

## Acceptance Criteria

- [ ] `docs/audits/D11_dead_code.md` contains a "Post-Audit Correction" section with
      confirmed importer evidence per directory.
- [ ] `docs/plans/open_audit_findings_backlog.md` Section 1E marked INVALID with
      reference to investigation findings.
- [ ] COMB-093–099 in `combat_movement.yaml` all have `status: legacy_verified`.
- [ ] STRAT-166–174 in `strategic_cognition.yaml` all have `status: legacy_verified`.
- [ ] SOC-142 in `social_narrative.yaml` has `status: legacy_verified`.
- [ ] Dead `src/ai/states.py` reference removed from `design_patterns.md`.
- [ ] `make knowledge-index-update` runs without error.
- [ ] `pytest tests/docs/` still passes.

## Related Tickets

- `TCK-20260618-AUDIT-D11-DEAD` — original audit (DONE; findings now partially corrected)
- `TCK-20260623-TYPE-CHECKER` — companion ticket (D13 type safety, separate scope)

## Related Docs

- `docs/audits/D11_dead_code.md`
- `docs/plans/open_audit_findings_backlog.md`
- `docs/guidelines/design_patterns.md`
- `docs/parity_ledger/combat_movement.yaml`
- `docs/parity_ledger/strategic_cognition.yaml`
- `docs/parity_ledger/social_narrative.yaml`

## Related Stored Artifacts

- `staging_artifacts/TCK-20260623-DEAD-CODE-REMOVAL/investigation.md` (findings)
- `staging_artifacts/TCK-20260623-DEAD-CODE-REMOVAL/plan.md`
- `staging_artifacts/TCK-20260623-DEAD-CODE-REMOVAL/test_plan.md`

## Related Code Areas

- `src/engine/apply.py` — top-level imports of QuestService, LevelingService (proves life)
- `src/systems/strategic_systems/intelligence.py` — GoalRegistry import (proves src/ai/ life)
- `src/content_semantics/faction.py` — 10+ engine importers (proves not orphaned)

## Assumptions / Open Questions

None. Investigation is complete; all answers confirmed.

## Implementation Notes

Doc-only changes completed 2026-06-23. No src/ files modified.

1. `docs/parity_ledger/combat_movement.yaml` — COMB-093 through COMB-099 set to
   `legacy_verified`; `divergence_note` added explaining that `src/ai/score_modifiers.py`
   is live code imported by `intelligence.py`, and no dedicated V2 unit tests exist for
   these specific score-modifier behaviors.

2. `docs/parity_ledger/strategic_cognition.yaml` — STRAT-166 through STRAT-174 set to
   `legacy_verified`; `divergence_note` added explaining that `src/ai/personality.py` is
   live code (not a V1 orphan), and no dedicated V2 test_path exists for these trait-system
   behaviors.

3. `docs/parity_ledger/social_narrative.yaml` — SOC-142 set to `legacy_verified`;
   `divergence_note` added. Pre-existing YAML parse error near line 2789 untouched.

4. `docs/guidelines/design_patterns.md` — Removed: step "Add a StateHandler in
   ai/states.py" from Section 1 How-To; entire Section 5 "AI State Machine — Strategy
   Pattern" (dead reference to non-existent `src/ai/states.py`); Pattern Summary table
   row for "Strategy (State Handlers)"; File Map entries for non-existent `brain.py` and
   `goal_evaluator.py`. GoalScorer/src/ai/goals/ references preserved (live code).

5. `docs/audits/D11_dead_code.md` — Appended Post-Audit Correction section documenting
   that all directories have confirmed live importers; no deletions warranted.

6. `docs/plans/open_audit_findings_backlog.md` — Section 1E body replaced with INVALID
   notice referencing TCK-20260623-DEAD-CODE-REMOVAL investigation.

7. `make knowledge-index-update` ran successfully: 4 files re-embedded, 4489 chunks total.

## Test Summary

- `pytest tests/docs/` — verify doc frontmatter integrity after edits
- No new tests; no behavior changes

## Files Changed

- `docs/parity_ledger/combat_movement.yaml` (COMB-093–099 → legacy_verified)
- `docs/parity_ledger/strategic_cognition.yaml` (STRAT-166–174 → legacy_verified)
- `docs/parity_ledger/social_narrative.yaml` (SOC-142 → legacy_verified)
- `docs/guidelines/design_patterns.md` (removed dead states.py references)
- `docs/audits/D11_dead_code.md` (added Post-Audit Correction section)
- `docs/plans/open_audit_findings_backlog.md` (Section 1E → INVALID)

## Completion Summary

D11 audit correction complete. All 9 'orphaned' directories confirmed as live code with active engine importers — no src/ deletions performed. 17 parity ledger entries (COMB-093–099, STRAT-166–174, SOC-142) updated from `verified` to `legacy_verified` with divergence notes. Dead `src/ai/states.py` references removed from design_patterns.md (Section 5 and related references). D11 audit doc updated with Post-Audit Correction section. Backlog Section 1E marked INVALID. Knowledge index rebuilt.
