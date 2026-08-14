---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT
artifact_type: test_plan
tags: [simulation-quality, calibration, corpus, agency, cognition, adventure]
---

# Test Plan — TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT

## Regression Surface

**Unit — AgencyScorer logic (must stay green; NOT a signal for this ticket's own fix, per
investigation.md's Anti-Drift Hazards — these bypass the broken emission wiring entirely):**
- `tests/simulation_quality/test_agency_scorer.py` (all classes, including `TestDefer` and
  `TestNewEventTypes::test_scorer_handles_defer_with_reason_event`, `::test_scorer_handles_
  commitment_abandoned_returns_none`, `::test_scorer_handles_rejection_cascade_tick_at_500`)

**Unit — Cognition/adventure-deletion guards (must stay green; confirm this ticket doesn't
regress the already-disclosed §2.41 contract):**
- `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py`
  (`test_defer_property_name_constant_matches_phase_and_extractor` especially — if Plan decides
  to port `last_routing_family` emission, this test's own `last_defer_reason`-only assertion is
  unaffected and should still pass unless `last_defer_reason` is also separately ported, which is
  explicitly a different, still-`Bounded` decision)
- `tests/unit/ai/goals/test_adventure_goal_scorer.py`
- `tests/unit/strategic/test_adventure_route_materialization.py`

**Integration — event extraction/shaping (must stay green; confirm no unrelated event-type
regressions from any source-level fix, if Plan/Implement chooses to port emission):**
- `tests/unit/observability/test_event_extractor_agency2.py`
- `tests/unit/observability/test_decision_trace.py`

**Fast-tier grade regression corpus (must show 0 *unexplained* failures outside the 6 named
run_keys — confirms this ticket's fixture edits don't collide with any other anchor):**
- `tests/simulation_quality/test_grade_regression.py -m "not slow"` (full `FAST_ANCHOR_KEYS`
  sweep, 89 keys as of this session)

**Slow-tier corpus-diversity guards (must confirm no unrelated `*_grade_stability` guard
regressed from the `grade_anchors.json`/test-file edits):**
- `tests/unit/worldassembly/test_corpus_diversity.py -m slow` (full sweep, run **isolated**
  per `make simq-corpus-diversity-slow-isolated`, not a raw sequential `-m slow` invocation —
  `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE` cumulative-session-load flake pattern)

**Parity sanity (spot-check only, not modified by this ticket):**
- `tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
  (STRAT-186)

## New Tests Required

Per this ticket's Acceptance Criteria, this is primarily a recalibration + doc-correction ticket
(no new behavior to unit-test), but the following new/updated coverage is required:

1. **Test name:** `test_simq_routing_test_seed42_1000t_cognition_grade_stability` (update, not
   new)
   **Category:** unit / architecture guard (slow-tier)
   **What it verifies:** `simq_routing_test_seed42_1000t` COGNITION matches its confirmed-current
   live behavior. Per investigation.md Finding 3, current live behavior is `event_count=0,
   grade=C` across 6/6 sampled trials — the anchor dict (`{"grade": "A", "score": 1.7961, ...}`)
   and the 3-trial mean-tolerance shape are both stale. Update to reflect the confirmed value,
   following the `_500t` sibling's own precedent (`test_corpus_diversity.py:525`) for whether a
   strict bit-identical (2a) or tolerance-guard (2b) shape is warranted — see investigation.md's
   Anti-Drift Hazards for why a fresh induced-load trial should inform this choice, not just the
   6 idle-condition trials sampled during Investigate.
   **Where it lives:** `tests/unit/worldassembly/test_corpus_diversity.py:633`

2. **Test name:** `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` (update, not
   new)
   **Category:** unit / architecture guard (slow-tier)
   **Same verification/shape decision as item 1**, for the `hero_guild_routing_seed42_1000t`
   variant (currently anchored `{"grade": "S", "score": 2.0641, ...}`).
   **Where it lives:** `tests/unit/worldassembly/test_corpus_diversity.py:717`

3. **If Plan decides Finding 1's `last_routing_family` loss is a real code gap to fix (not just a
   stale anchor — see investigation.md Risk #1), a new regression test is required:**
   **Test name:** e.g. `test_adventure_route_win_writes_last_routing_family_property` (name
   illustrative, Plan should finalize)
   **Category:** unit
   **What it verifies:** a winning `ADVENTURE_ROUTE` candidate's materialization
   (`intelligence.py`'s `GoalKind.ADVENTURE_ROUTE` branch) produces an `EntityUpdate.
   property_updates` (or equivalent `StrategicUpdate` field) carrying the route family, so
   `route_selected`/`action_executed`/`route_family_first_use` can fire again — mirroring the
   pre-deletion `AdventureDecisionPhase.apply()` contract at `phase.py:178-179` (deleted, but
   readable via `git show 1825f914^:src/domains/adventure/phase.py`).
   **Where it should live:** `tests/unit/strategic/test_adventure_route_materialization.py` or a
   new file alongside it, matching that file's existing test shape.
   **This test is conditional** — only required if Plan/Implement chooses the code-fix path over
   the recalibrate-and-accept path; do not assume it is required.

4. **If AGENCY is recalibrated (the baseline expectation per Finding 1/2's evidence), no new test
   is required beyond the existing `test_grade_within_anchor_band[run_key]` parametrized cases in
   `test_grade_regression.py` — they already cover all 6 named run_keys once `grade_anchors.json`
   is updated. Do not add a redundant new test for the same assertion.**

5. **Doc-correctness guard (optional, matching `test_delete_adventure_decision_phase_guards.py`'s
   own established pattern of pinning a doc claim against source):** a test asserting
   `docs/simulation_quality/eval_matrix_results.md`'s "AGENCY — Cross-World Design Note" section no
   longer references the deleted `AdventureDecisionPhase`/`phase.py` path as live — mirrors
   `test_adventure_contract_engine_phase_does_not_reference_adventure_decision_phase` in the same
   guard file. Nice-to-have, not required by any AC.

## Scoped Pytest Commands

Fast-tier AC gate (matches this ticket's own AC):
```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
```

Fast-tier, scoped to just the 6 named run_keys (fast iteration during Implement):
```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k \
  "simq_routing_test_seed42_500t or simq_routing_test_seed123_500t or simq_routing_test_seed456_500t or hero_guild_routing_seed42_500t or hero_guild_routing_seed123_500t or hero_guild_routing_seed456_500t"
```

Slow-tier AC gate (the 2 named `_1000t` guards, isolated invocation per the flake-avoidance
precedent — do NOT run as part of a combined `-k` sweep with other slow tests):
```
pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_simq_routing_test_seed42_1000t_cognition_grade_stability" --resource-budget large --tb=short -q -m slow
pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_hero_guild_routing_seed42_1000t_cognition_grade_stability" --resource-budget large --tb=short -q -m slow
```

Full slow-tier corpus-diversity sweep (final gate, confirms no unrelated guard regressed —
isolated per-test subprocess invocation, not raw sequential):
```
make simq-corpus-diversity-slow-isolated
```

AgencyScorer unit regression surface:
```
pytest tests/simulation_quality/test_agency_scorer.py -q
```

Adventure/deletion-guard regression surface:
```
pytest tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py tests/unit/ai/goals/test_adventure_goal_scorer.py tests/unit/strategic/test_adventure_route_materialization.py -q
```

Event extraction/shaping regression surface (only needed if Implement touches emission code):
```
pytest tests/unit/observability/test_event_extractor_agency2.py tests/unit/observability/test_decision_trace.py -q
```

**Never:** `pytest tests/` (repo-wide) — explicitly disallowed by CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- `tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid` —
  structural guard (81+ scenario keys, exactly 10 pillars/entry, `{"grade","score"}` shape per
  pillar) — any `grade_anchors.json` edit must keep this passing; catches accidental
  addition/removal of a top-level key or malformed pillar object.
- `tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars`
  and `::test_score_tolerance_overrides_do_not_affect_unlisted_anchors` — confirm none of the 6
  named run_keys/pillars accidentally land in `SCORE_TOLERANCE_OVERRIDES` (none currently do,
  confirmed by direct read; a point-anchor edit should not add any).
- The **full** `FAST_ANCHOR_KEYS` sweep (not just the 6 named keys) after any `grade_anchors.json`
  edit — catches accidental cross-contamination of a sibling run_key's fixture entry, matching
  the parent ticket's own precedent (`git diff` should show changes to exactly the 6 named
  top-level entries' AGENCY/COGNITION sub-fields, nothing else).
- `tests/simulation_quality/test_agency_scorer.py`'s full suite — if Implement touches
  `src/simulation_quality/scorers/agency.py` for any reason (not expected, but guard against
  scope creep), this is the authoritative scorer-logic regression surface; it must stay green
  independent of whatever the emission-side decision is.
- `make simq-corpus-diversity-slow-isolated`'s own `nodeid_count < 32` guard — catches accidental
  test deletion/collection breakage if the two `_1000t` tests are edited carelessly (e.g. a typo
  in `@pytest.mark.slow` or a broken import).
- If Plan/Implement chooses the code-fix path (Finding 1's Risk #1), the existing
  `test_defer_property_name_constant_matches_phase_and_extractor` guard must be re-read and
  explicitly reconciled — it currently asserts `"last_defer_reason" not in
  inspect.getsource(AdventureGoalScorer.score)`; a `last_routing_family`-only fix (leaving
  `last_defer_reason` still un-ported, per §2.41's still-valid `Bounded` rationale) would leave
  this guard's assertion correct and unchanged — but this must be verified, not assumed, once the
  actual diff exists.
