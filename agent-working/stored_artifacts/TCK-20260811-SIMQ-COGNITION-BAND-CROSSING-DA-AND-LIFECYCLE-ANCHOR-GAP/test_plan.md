---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP
artifact_type: test_plan
tags: [simulation-quality, calibration, corpus]
---

# Test Plan — TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP

## Regression Surface

Existing tests that must keep passing.

**unit / fixture-structural:**
- `tests/simulation_quality/test_grade_regression.py` — `FAST_ANCHOR_KEYS`-parametrized
  `test_grade_within_anchor_band` for every key *other* than the 5 this ticket touches (must not
  regress from an unrelated edit to `grade_anchors.json`).
- Any test that loads `grade_anchors.json`/`score_ceilings.json` structurally (JSON-validity,
  schema-shape checks) — confirm these fixtures still parse after edits.

**integration / arena-combat (worldassembly):**
- `tests/unit/worldassembly/test_corpus_diversity.py` — all 17 other `*_grade_stability` guard
  tests (the ones this ticket does NOT touch:
  `test_simq_routing_test_seed42_1000t_cognition_grade_stability`,
  `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`, and 15 more) must still pass
  unmodified. Note (disclosed in investigation.md, not fixed here): the two 1000t/SLOW-tier
  COGNITION guards for the same two worlds (`simq_routing_test_seed42_1000t`,
  `hero_guild_routing_seed42_1000t`) share the identical root cause and are very likely also now
  stale/failing — out of this ticket's explicit 500t-scoped item list, but Plan should decide
  whether to fold them in or file a fast follow-up, not silently leave them red with no ticket
  tracking them.
- `tests/unit/worldbuilding/test_world_repository.py` — SUB-384's own regression suite, unrelated
  to this ticket's edits but in the same subsystem family; not expected to be touched, confirm no
  incidental breakage.

**strategic-cognition (untouched by this ticket, sanity-check only):**
- `tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
  (STRAT-186's own test) — not modified by this ticket; run once to confirm it's still green before
  trusting the "already fixed, already verified" framing in investigation.md.

## New Tests Required

Per acceptance criteria — this ticket's job is calibration-data correction, not new production
code, so "new tests" here means new/updated fixture-anchor assertions and one updated guard test,
not new source-level unit tests.

1. **`grade_anchors.json` COGNITION recalibration for the 4 Finding-(1) items**
   - Category: fixture data change, verified by existing parametrized test
     (`test_grade_within_anchor_band`)
   - What it verifies: `simq_routing_test_seed42_500t`, `simq_routing_test_seed456_500t`,
     `hero_guild_routing_seed42_500t`, `hero_guild_routing_seed456_500t` COGNITION entries updated
     to `{"grade": "C", "score": 0.0}` (the confirmed-deterministic live value, 15/15 trials
     bit-identical) so `test_grade_within_anchor_band[run_key]` passes for COGNITION on all 4
     without a band-tolerance or score-tolerance failure.
   - Where it lives: `tests/simulation_quality/fixtures/grade_anchors.json` (data only, no new
     test function — the existing parametrized test covers it once the fixture is corrected)

2. **`test_simq_routing_test_seed42_500t_cognition_grade_stability` anchor update**
   - Category: integration (arena-combat / worldassembly guard test)
   - What it verifies: the guard test's own inline `anchors` dict
     (`{"COGNITION": {"grade": "A", "score": 1.8373, "abs_floor": 0.0521}}`) must be updated to
     reflect the new deterministic value, or the test will keep failing on every `-m slow` run
     even after `grade_anchors.json` is fixed (this test reads its own hardcoded anchor, not the
     fixture file). Given the value is now provably deterministic (not variable), consider
     simplifying this specific guard to a plain bit-identical assertion (matching
     `test_urban_political_seed123_500t_cognition_bit_identical_under_load`'s shape) instead of
     keeping the now-unnecessary 3-trial tolerance machinery — Plan's call, not mandated here.
   - Where it lives: `tests/unit/worldassembly/test_corpus_diversity.py:501-582`

3. **`grade_anchors.json` recalibration for `lifecycle_full_coverage_world_seed42_200t`
   (7 or 8 pillars, per Plan's resolution of the ECONOMY open question)**
   - Category: fixture data change, verified by the newly-registered `FAST_ANCHOR_KEYS` entry
   - What it verifies: COGNITION/AGENCY/COMBAT/PROGRESSION/SOCIAL/WORLD/NARRATIVE (and ECONOMY, if
     Plan folds it in per investigation.md Risk #2) updated to fresh live values, re-verified
     immediately before the edit lands (not copied from this investigation's own snapshot — see
     investigation.md Risk #1). FACTION and INFORMATION are unchanged/already-passing — do not
     touch their anchor entries.
   - Where it lives: `tests/simulation_quality/fixtures/grade_anchors.json`

4. **Docs NOTE block + parity ledger UPDATE block** (not pytest-verified, but required by
   Definition of Done)
   - `docs/simulation_quality/eval_matrix_results.md` — dated NOTE per investigation.md's "Docs
     Requiring Update"
   - `docs/parity_ledger/substrate.yaml` SUB-384 `support_boundary` — UPDATE block adding
     `lifecycle_full_coverage_world_seed42_200t`

## Scoped Pytest Commands

Primary regression-verification command (matches this ticket's own AC5 exactly):

```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
```

Additional scoped commands to actually exercise what AC5's own command does NOT cover (the slow-
marked guard test flagged as a gap in investigation.md Risk #3):

```
pytest tests/unit/worldassembly/test_corpus_diversity.py -k "simq_routing_test_seed42_500t or hero_guild_routing" -m slow -v
```

Full corpus-diversity guard sweep (confirms no other `*_grade_stability` guard regressed from the
`grade_anchors.json` edit — these guards carry their own inline anchors, independent of the fixture
file, so this is a belt-and-suspenders check, not expected to be affected):

```
pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow -v
```

Never: `pytest tests/` (repo-wide) — out of scope per CLAUDE.md's testing rule.

## Anti-Drift Test Guards

- **A passing `test_grade_within_anchor_band` for these 5 run_keys after the fixture edit is not
  sufficient proof of correctness on its own** — it only proves the fixture now matches *some*
  captured value. The load-bearing verification is the *live* repro evidence in investigation.md
  (15/15 bit-identical trials, direct bisection to a specific commit), not the pytest green
  checkmark. Do not treat "tests pass" as license to skip re-reading the bisection evidence if this
  ticket is revisited later.
- **If a future re-run of `test_grade_within_anchor_band` for any of these 5 keys drifts to a
  non-zero/non-C COGNITION value again**, that is itself a signal worth investigating (not
  auto-recalibrating) — it would mean either a *new* behavior change landed on top of the
  `PROJECT-SWITCH-BYPASS-GENERALIZATION` fix, or (less likely, but confirm before assuming) that
  the "deterministic" classification in this ticket was wrong. Given investigation.md Risk #1's
  disclosure that this exact code area is under heavy concurrent churn, a future drift here is
  plausible and should not be dismissed as more F6 noise by default.
- **A guard against re-introducing the `watchdog_variance` misclassification**: if a future ticket
  is tempted to add a `score_ceilings.json` `watchdog_variance` entry for any of these 4
  (run_key, COGNITION) pairs, it should first re-run the same idle-vs-load repro this ticket did
  (2 idle + 2x/4x load) — a single anomalous sample is not sufficient grounds after this ticket's
  15-trial deterministic-zero finding.
- **Scope-creep guard**: no test in this ticket's scope should touch
  `src/systems/strategic_systems/intelligence.py`, `src/domains/adventure/`, or any other
  production strategic-cognition code — this ticket is calibration-data-only. If Implement finds
  itself editing source under `src/`, that is a signal the ticket has drifted beyond its Out of
  Scope boundary.
