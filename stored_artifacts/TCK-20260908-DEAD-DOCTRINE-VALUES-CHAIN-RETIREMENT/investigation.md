---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT
artifact_type: investigation
tags: [architecture, strategy]
---

# Investigation — TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT

## Re-confirming the 4 modules/classes are still dead

Direct grep, 2026-09-08, against `src/` (excluding the modules' own definitions):

- `MotivationBiasService` — only hits: `src/domains/motivation/__init__.py`'s own import/export,
  and 3 docstring/comment cross-references in `src/domains/adventure/scoring.py`,
  `src/domains/culture/exporter.py`, `src/domains/culture/applicator.py`. Zero real callers.
- `DoctrineResolver` — only hits: `__init__.py` export and one docstring cross-reference. Zero
  real callers.
- `IdentityDoctrine` — only hits: its own definition, `resolver.py`'s construction of it (the dead
  chain's own internals), and one docstring cross-reference. Zero real callers.
- `ValuePreferenceProfile` — only hits: its own definition and 2 docstring cross-references. Zero
  real callers.
- `identity(class_id=...)` construction sites: still only `src/testing/scenario_runner.py` and
  `src/domains/campaigns/runner.py` — both test/analysis utilities, not the real corpus-world
  entity population path. Unchanged from the 2026-09-07 finding.

**All 4 confirmed still genuinely dead.**

## New finding beyond the 2026-09-07 investigation

`MotivationModel.doctrine: IdentityDoctrine` and `MotivationModel.values: ValuePreferenceProfile`
(`src/core/cognition.py`) are typed fields referencing the two dead classes — not previously
flagged. Checked whether these fields themselves have any real reader independent of the already-
dead `compute_bias_multiplier()`:

```
grep -rn "\.doctrine\b|\.values\b" src/ | grep -v "MotivationModel|dict|.values()"
```

Only hit: `src/domains/motivation/service.py` (the file being deleted) reads
`motivation.doctrine.preferred_route_tags`/`.avoided_route_tags` and `motivation.values`. No other
code anywhere reads `MotivationModel.doctrine`/`.values`. Also checked `MotivationModel(...)`
construction sites (`src/domains/culture/applicator.py`, `src/systems/lifecycle_systems/
lifecycle.py`) — neither passes explicit `doctrine=`/`values=` kwargs; both rely on the
`default_factory`. **Confirmed: these two fields are themselves dead, not just the classes they
type** — safe to remove alongside the classes rather than leaving a dangling type reference.

## External reference check (docs/tooling/roadmap)

`grep -rln` for the 4 exact symbol names across `docs/`, `tools/`, and roadmap plan docs found only
historical/narrative references (past-tense descriptions of "what this decision superseded"), no
active dependency on these exact module/class/file paths continuing to exist. No real risk
identified for deletion.

## Test surface

8 test files reference the 4 symbols:
- 4 whose entire subject is the dead code (delete outright):
  `tests/unit/domains/motivation/test_phase14_bias_service.py`,
  `tests/unit/domains/motivation/test_phase14_doctrine_resolver.py`,
  `tests/unit/motivation/test_motivation_bias_culture.py`,
  `tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py`
- 4 with a mix of dead-code tests and real, unrelated tests (trim only the dead parts):
  `tests/unit/domains/motivation/test_phase14_motivation_models.py` (also tests
  `RoleFitPreference`, a live, separate class — kept),
  `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py` (only an unused
  import reference),
  `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` (1 of 3 tests uses the
  dead chain; the other 2 test `RoleModelBundle`, unrelated — kept),
  `tests/architecture/test_fame_legend_fact_distinctness.py` (a static-analysis guard test; keep
  and generalize rather than delete, since it correctly continues to guard against reintroduction)
