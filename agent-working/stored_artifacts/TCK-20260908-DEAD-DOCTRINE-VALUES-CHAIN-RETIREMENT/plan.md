---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT
artifact_type: plan
tags: [architecture, strategy]
---

# Plan — TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT

Real user decision: delete the 4 modules/classes outright (see ticket's own
`## Assumptions / Open Questions`).

## Steps

1. Delete `src/domains/motivation/service.py` (`MotivationBiasService`) and
   `src/domains/motivation/resolver.py` (`DoctrineResolver`).
2. Update `src/domains/motivation/__init__.py` to stop importing/exporting the deleted classes,
   keep `RoleFitEvaluator` (a separate, live service, out of scope).
3. Remove `IdentityDoctrine`/`ValuePreferenceProfile` classes from `src/core/cognition.py`; remove
   the now-dead `doctrine`/`values` fields from `MotivationModel` (per Investigate's new finding)
   and their entries in `MotivationModel.to_canonical_dict()`.
4. Update docstring cross-references in `src/domains/adventure/scoring.py` (the `personality_bias`
   comment citing the dead chain), `src/domains/culture/exporter.py`, and
   `src/domains/culture/applicator.py` (both describe Culture Drift's real target as
   `personality_bias` now, not the deleted `MotivationBiasService`).
5. Delete the 4 test files whose entire subject is deleted code; trim the 4 mixed test files to
   remove only the specific tests/imports touching deleted code, verified against Investigate's
   own file-by-file breakdown — never touch an unrelated test in the same file.
6. Update `docs/guidelines/intentional_divergences.md` §2.53's own "not actioned" note to record
   the final "deleted" disposition.
7. Verify: focused test run on all 8 touched test files, then a broader touched-area regression
   sweep (`tests/unit/domains/`, `tests/unit/ai/`, `tests/unit/strategic/`, `tests/architecture/`,
   `tests/integration/scenarios/`).

## Risk

Low. Every candidate for deletion was independently re-confirmed dead in Investigate, including
the newly-found `MotivationModel.doctrine`/`.values` fields. The only real risk was accidentally
touching a test asserting on a *different*, live class sharing a file with a dead-code test
(`RoleFitPreference` in `test_phase14_motivation_models.py`, `RoleModelBundle` in
`test_phase18_cognition_hierarchy_e2e.py`) — mitigated by per-file, per-test review rather than a
blanket file-level grep-and-delete.
