---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-E41G-COHESION-SUSTAIN
phase: done
date: 2026-06-28
tags: [party, cohesion, composition-score, social, p3]
---

# TCK-20260628-E41G-COHESION-SUSTAIN

## Title
Composition-score-based defection threshold sustain (E41G)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
High-composition parties (scored by PartyCompositionScorer) should sustain longer
before members defect. The existing DEFECTION_GRIEVANCE_THRESHOLD=3 is fixed; this
ticket makes it dynamic based on `GroupRecord.composition_score`.

## Scope
1. `src/core/state.py` — Add `composition_score: float = 0.0` to `GroupRecord`
   and include in `to_canonical_dict()`.
2. `src/systems/social_systems/party_lifecycle.py` — Add
   `effective_defection_threshold(group)` static method; update `check_defection`
   to use it instead of the hardcoded constant.
3. `src/engine/pipeline_phases/groups.py` — Update defection early-exit guard to
   call `effective_defection_threshold`; compute and pass `composition_score` at
   group formation.
4. `src/systems/world_systems/groups.py` — Compute composition_score via
   `PartyCompositionScorer.score()` at group formation; pass to `GroupRecord(...)`.
5. Tests for threshold scaling and suppressed/triggered defection cases.

## Out of Scope
- Multi-hero orchestration (E41H).
- NemesisRelation / grief features (E43F+).

## Acceptance Criteria
- [x] `GroupRecord.composition_score` field exists and defaults to 0.0.
- [x] `effective_defection_threshold(group)` returns 3 at score=0.0, 4 at score=0.5, 5 at score=1.0.
- [x] `check_defection` uses dynamic threshold.
- [x] Defection early-exit guard in `groups.py` uses dynamic threshold.
- [x] Composition score computed at formation in `groups.py` and stored on `GroupRecord`.
- [x] 23 social lifecycle tests pass (5 new E41G tests).
- [x] Background regression suite exit code 0.

## Related Tickets
- Parent: TCK-20260628-E-PARTY-LOOP
- Depends on: TCK-20260628-E41F-PARTY-SCORER (composition scorer — DONE)
- Next: E41H-MULTI-HERO

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` — cooperation thresholds
- `docs/parity_ledger/social_narrative.yaml` — SOC-232 (add entry if missing)

## Related Code Areas
- `src/core/state.py` (GroupRecord.composition_score)
- `src/systems/social_systems/party_lifecycle.py` (effective_defection_threshold)
- `src/engine/pipeline_phases/groups.py` (guard + formation wiring)
- `src/systems/world_systems/groups.py` (formation score computation)
- `tests/unit/social/test_party_lifecycle.py` (5 new tests)

## Implementation Notes
- Bonus formula: `round(composition_score * 2)` → 0 at 0.0, 1 at 0.5, 2 at 1.0.
- `GroupRecord` uses `@dataclass(frozen=True, slots=True)`, so `dataclasses.replace`
  is used in tests for building variants with non-zero composition_score.
- Background test suite (bks0w1860): exit code 0, no regressions.

## Test Summary
- 23 tests in `tests/unit/social/test_party_lifecycle.py` — all pass.
- 5 new E41G-specific tests: threshold at 0.0, 0.5, 1.0; suppressed defection
  at score=1.0 with 3 grievances; triggered defection at score=0.0 with 3 grievances.
- Background broad suite: exit 0.

## Files Changed
- `src/core/state.py` (GroupRecord.composition_score field + canonical_dict)
- `src/systems/social_systems/party_lifecycle.py` (effective_defection_threshold + check_defection)
- `src/engine/pipeline_phases/groups.py` (guard update + formation score wiring)
- `src/systems/world_systems/groups.py` (PartyCompositionScorer.score at formation)
- `tests/unit/social/test_party_lifecycle.py` (5 new E41G tests)

## Completion Summary
`GroupRecord.composition_score` stores the OCEAN+role diversity score at formation.
`effective_defection_threshold()` scales from 3→5 grievances as score rises 0→1,
giving high-compatibility parties up to 2 extra grievances before dissolution.
Defection guard in both the lifecycle service and the groups pipeline phase now use
the dynamic threshold. All 23 lifecycle tests pass; background suite clean.
