---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT
phase: done
date: 2026-09-08
tags: [architecture, strategy]
---

# TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT

## Title
Decide the disposition of the confirmed-dead Doctrine/Values motivation chain — delete or formally retire in place

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Follow-up from the Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`,
merged via PR #144). `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` confirmed 4 modules/classes are
dead in production — not merely under-used — and disclosed this in
`docs/guidelines/intentional_divergences.md` §2.53, but deliberately did not delete or formally retire
them (out of that ticket's own narrow scope), leaving a "CONFIRMED DEAD LEGACY CODE" docstring as the
only in-code signal:
- `MotivationBiasService.compute_bias_multiplier()` (`src/domains/motivation/service.py`) — zero real
  callers anywhere in `src/`.
- `DoctrineResolver.resolve()` (`src/domains/motivation/resolver.py`) — zero real (non-test) callers;
  the only two `identity(class_id=...)` construction sites in the codebase
  (`src/testing/scenario_runner.py`, `src/domains/campaigns/runner.py`) are test/analysis utilities,
  not the real corpus-world entity population path.
- `IdentityDoctrine`, `ValuePreferenceProfile` (`src/core/cognition.py`) — `ValuePreferenceProfile`'s
  fields all default to exactly `0.5`, so `compute_bias_multiplier()`'s own `(value - 0.5) * 0.5` terms
  are mathematically guaranteed to evaluate to `0.0` for every real entity even if the service were
  called.

§2.53 itself flagged this as a real, disclosed gap needing a future decision, not resolved there.

## Scope
- Re-confirm during Investigate that all 4 are still genuinely dead (re-grep for real callers) — do
  not assume the 2026-09-07 finding is still accurate without re-checking.
- Present the real decision (see Assumptions/Open Questions) to the user/roadmap owner: delete the 4
  modules/classes outright, or formally document them as permanently-retired-in-place if deletion
  carries real risk (e.g. external tooling or a future roadmap idea referencing these module paths by
  name).
- Whichever is chosen, update `docs/guidelines/intentional_divergences.md` §2.53 to record the final
  disposition (not leave it as a standing "not actioned" note indefinitely).

## Out of Scope
- Reviving the chain — already ruled out by `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own
  decision (bypass legacy, extend `personality_bias`); not re-litigated here.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [x] A real, evidenced decision (delete vs. formally retire-in-place) is made and recorded.
- [x] If deleted: no regression in the touched-area test suite; the 4 "CONFIRMED DEAD LEGACY CODE"
      docstring cross-references in `personality_bias`'s own §2.53/§2.55 branches are updated to stop
      pointing at now-nonexistent code.
- [x] `docs/guidelines/intentional_divergences.md` §2.53 updated to reflect the final disposition.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (`tickets/done/` — parent epic)
- `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (`tickets/done/` — original dead-chain finding)

## Related Docs
- `docs/guidelines/intentional_divergences.md` §2.53

## Related Stored Artifacts
`stored_artifacts/TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT/` (`investigation.md`,
`plan.md`, `test_plan.md`)

## Related Code Areas
- `src/domains/motivation/service.py`, `src/domains/motivation/resolver.py`
- `src/core/cognition.py` (`IdentityDoctrine`, `ValuePreferenceProfile`)

## Assumptions / Open Questions
- **Decided 2026-09-08 (real user decision)**: **delete the 4 modules/classes outright.** Investigate
  should still check for any reference to these exact module/class paths outside `src/` (docs,
  external tooling, roadmap docs) before deleting — the decision to delete stands regardless, but if
  a real external reference is found, update it rather than silently leaving a dangling reference.

## Implementation Notes
Re-confirmed via direct grep all 4 remain genuinely dead — zero real (non-test, non-definition)
callers anywhere in `src/`. Found one thing the 2026-09-07 investigation hadn't surfaced:
`MotivationModel.doctrine`/`.values` fields (`src/core/cognition.py`) typed these two classes and
were themselves never read outside the now-deleted `compute_bias_multiplier()` — confirmed via
grep before removing both fields alongside the classes, not left dangling with a broken type.
`RoleFitPreference`/`RoleFitEvaluator` (a separate, live class/service in the same package)
confirmed untouched — not part of this dead chain.

Deleted:
- `src/domains/motivation/service.py` (`MotivationBiasService`)
- `src/domains/motivation/resolver.py` (`DoctrineResolver`)
- `IdentityDoctrine`, `ValuePreferenceProfile` classes from `src/core/cognition.py`, plus the
  `doctrine`/`values` fields (and their `to_canonical_dict()` entries) on `MotivationModel`

Updated (docstring cross-references, not code behavior):
`src/domains/motivation/__init__.py`, `src/domains/adventure/scoring.py`,
`src/domains/culture/exporter.py`, `src/domains/culture/applicator.py`.

No real external reference (docs/tooling/roadmap) to these exact module/class paths was found
outside `src/` — deletion carried no real risk, matching the ratified decision.

## Test Summary
Deleted 4 test files whose entire subject was the deleted code
(`tests/unit/domains/motivation/test_phase14_bias_service.py`,
`tests/unit/domains/motivation/test_phase14_doctrine_resolver.py`,
`tests/unit/motivation/test_motivation_bias_culture.py`,
`tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py`). Trimmed 4 more test
files to remove only the specific tests/imports exercising deleted code, keeping every other real
test in those files untouched
(`tests/unit/domains/motivation/test_phase14_motivation_models.py`,
`tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`,
`tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py`,
`tests/architecture/test_fame_legend_fact_distinctness.py` — the last one's static guard
generalized to catch the symbol's reintroduction under any path, not just the deleted module).

`pytest tests/unit/domains/motivation/ tests/unit/motivation/
tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py
tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py
tests/architecture/test_fame_legend_fact_distinctness.py -q` → 13 passed. Broader regression
(`tests/unit/domains/ tests/unit/ai/ tests/unit/strategic/ tests/architecture/
tests/integration/scenarios/ -m "not slow"`) → 1514 passed, 1 skipped, 0 failed.

## Files Changed
- Deleted: `src/domains/motivation/service.py`, `src/domains/motivation/resolver.py`
- Deleted: `tests/unit/domains/motivation/test_phase14_bias_service.py`,
  `tests/unit/domains/motivation/test_phase14_doctrine_resolver.py`,
  `tests/unit/motivation/test_motivation_bias_culture.py`,
  `tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py`
- Edited: `src/core/cognition.py`, `src/domains/motivation/__init__.py`,
  `src/domains/adventure/scoring.py`, `src/domains/culture/exporter.py`,
  `src/domains/culture/applicator.py`
- Edited: `tests/unit/domains/motivation/test_phase14_motivation_models.py`,
  `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`,
  `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py`,
  `tests/architecture/test_fame_legend_fact_distinctness.py`
- Edited: `docs/guidelines/intentional_divergences.md` (§2.53 final disposition)

## Completion Summary
Real user decision: delete the 4 confirmed-dead Doctrine/Values modules/classes outright.
Re-confirmed dead, found and correctly handled one additional blast-radius item the original
investigation missed (`MotivationModel.doctrine`/`.values` fields, themselves also dead),
deleted cleanly with all cross-references updated and no real external reference found. Full
touched-area regression clean (1514 passed, 0 failed). `docs/guidelines/intentional_divergences.md`
§2.53 updated to record the final disposition.
