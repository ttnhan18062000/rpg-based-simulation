---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION
artifact_type: test_plan
tags: [simulation-quality, bug, calibration]
---

# Test Plan — TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION

## Regression Surface

Existing tests that must keep passing (grouped; see investigation.md's blast-radius
analysis for why each group is or isn't expected to need a value/logic change, as opposed to
a mechanical call-site update if `__getitem__`'s signature changes):

**Unit — `ScoringWeights` itself**
- `tests/simulation_quality/test_weights.py` — all tests except the two named in AC #3 that
  do not currently exist (see New Tests Required). In particular
  `test_getitem_known_key` (asserts `scoring_weights["harvest_active"] == 12.0`,
  non-colliding key, must stay passing unchanged),
  `test_getitem_raises_on_missing_key`, `test_all_10_pillars_present`,
  `test_pillar_weight_default_profile_is_one`, `test_dungeon_crawl_profile_overrides`,
  `test_urban_political_profile_overrides`, `test_detection_params_load`,
  `test_missing_file_raises`.

**Unit — pillar scorers whose keys never collide (no value change expected, but syntax
must keep working if `__getitem__` stays bare-string-compatible)**
- `tests/simulation_quality/test_agency_scorer.py`
- `tests/simulation_quality/test_combat_scorer.py`
- `tests/simulation_quality/test_faction_scorer.py`
- `tests/simulation_quality/test_progression_scorer.py`
- `tests/simulation_quality/test_social_scorer.py`
- `tests/simulation_quality/test_narrative_scorer.py`
- `tests/simulation_quality/test_timegate_penalties.py`

**Unit — pillar scorers with known collisions (value assertions to inspect; see Anti-Drift
Test Guards for the exact 4 assertions expected to need updating)**
- `tests/simulation_quality/test_cognition_scorer.py`
- `tests/simulation_quality/test_information_scorer.py`
- `tests/simulation_quality/test_economy_scorer.py`
- `tests/simulation_quality/test_world_dynamics_scorer.py` (ecology pair — expected
  unaffected in value, since WORLD already reads its own correct value; must still pass
  unchanged as a confirmation the WORLD side never regresses)

**Integration**
- `tests/simulation_quality/test_quality_hub_integration.py`
- `tests/simulation_quality/test_quality_hub_event_translation.py`
- `tests/simulation_quality/test_kernel_simq_integration.py`
- `tests/simulation_quality/test_broker_feed_integration.py`
- `tests/simulation_quality/test_feed.py`
- `tests/simulation_quality/test_traceability_path.py`
- `tests/simulation_quality/test_persistence.py`
- `tests/simulation_quality/test_report.py`
- `tests/simulation_quality/test_accumulator.py`

**Calibration / arena-style regression**
- `tests/simulation_quality/test_grade_regression.py` — full run required (not skip-only);
  this is the AC #5 gate. Expect real diffs for the ~53 at-risk anchors identified in
  investigation.md (10 confirmed via `subjective_divergence` loop-flag evidence, the
  remaining ~43 unconfirmed from persisted artifacts alone and requiring an actual re-run).
  `test_grade_anchor_file_exists_and_valid`, `test_grade_anchors_entry_count_unchanged`
  (pinned at 76), `test_score_tolerance_catches_within_band_regression`,
  `test_within_band_default_tolerance_unchanged` must all keep passing structurally
  regardless of the fix (they don't depend on the 7 colliding keys' values).
- `tests/simulation_quality/test_evaluate_harness.py`
- `tests/simulation_quality/test_calibrate_world_loading.py`
- `tests/simulation_quality/test_scenario_coverage.py`
- `tests/simulation_quality/test_performance.py` (confirm no perf regression from any new
  per-scorer weights-view construction, however light)

**API surface (touches `ScoringWeights` indirectly via `QualityHub`)**
- `tests/simulation_quality/test_api_routes.py`

## New Tests Required

Per acceptance criteria — one entry per required new test:

1. **Pillar-scoped resolution, synthetic fixture**
   - Category: unit
   - Verifies: `ScoringWeights` (or its replacement/wrapper) instantiated from a fixture
     YAML with two pillars declaring the same rule key at different values resolves each
     pillar's own value independently, regardless of YAML declaration order (construct one
     fixture with the colliding pillar declared first and a second with it declared last —
     both must resolve correctly, proving the fix isn't just "later pillar coincidentally
     still wins").
   - Location: `tests/simulation_quality/test_weights.py` (new test function, e.g.
     `test_pillar_scoped_lookup_resolves_independently_of_declaration_order`)
   - Satisfies AC #1.

2. **Real-config regression — all 7 known collisions**
   - Category: unit / regression
   - Verifies: loading the real `config/simulation_quality/scoring_weights.yaml` and
     querying `belief_active`, `subjective_divergence`, `knowledge_rot`,
     `omniscience_collapse` through `CognitionScorer`'s own pillar path returns COGNITION's
     declared values (`2.0`, `5.0`, `-3.0`, `-20.0`) and through `InformationScorer`'s own
     pillar path returns INFORMATION's declared values (`10.0`, `30.0`, `-2.0`, `-20.0`);
     `ecology_cycling`/`ecology_broken` through `WorldDynamicsScorer`'s path return WORLD's
     values (`6.0`, `-20.0`); `knowledge_economy_active` through `EconomyScorer`'s path
     returns ECONOMY's `8.0` and through `InformationScorer`'s path returns INFORMATION's
     `15.0` — i.e., prove the two pillars sharing a key name now diverge correctly instead
     of collapsing.
   - Location: `tests/simulation_quality/test_weights.py` (new test, e.g.
     `test_real_config_seven_known_collisions_resolve_per_pillar`) — one parametrized test
     over the 7 keys × 2 pillars is preferable to 14 separate tests.
   - Satisfies AC #2.

3. **Validation behavior preserved — INFRA-234 gap closure**
   - Category: unit / architecture guard
   - Verifies: `ScoringWeights.load()` still raises `pydantic.ValidationError` when a
     required pillar/rule key is missing from the YAML, and when a rule value is
     malformed (e.g. a non-numeric string where a float is expected). **These two tests do
     not currently exist** (`INFRA-234`'s cited `test_path` is stale — see investigation.md)
     — write them now, named exactly as `INFRA-234` and the ticket's own AC #3 already
     reference them: `test_missing_key_raises_validation_error`,
     `test_malformed_value_raises_validation_error`. Closing this gap is a natural byproduct
     of this ticket touching `weights.py`'s validator; if planning instead defers this to a
     separate follow-up ticket, that decision must be named explicitly in Implementation
     Notes/Completion Summary, not silently skipped.
   - Location: `tests/simulation_quality/test_weights.py`
   - Satisfies AC #3.

4. **Scorer call-site consistency**
   - Category: unit
   - Verifies: every one of the 4 colliding-key scorers (`CognitionScorer`,
     `InformationScorer`, `EconomyScorer`, `WorldDynamicsScorer`) produces a `ScoreRecord.delta`
     equal to its OWN pillar's declared value for the shared key, using the real scorer
     `.score()` call path (not just direct `ScoringWeights` queries) — i.e., the existing
     `test_cognition_scorer.py`/`test_economy_scorer.py` assertions that today read
     `scoring_weights["belief_active"]`/`scoring_weights["knowledge_economy_active"]` as
     their oracle must be rewritten to assert against the pillar-scoped value explicitly
     (e.g. a literal `2.0`/`8.0`, or a pillar-scoped accessor call), not the bare
     `scoring_weights["key"]` expression, since that expression may no longer equal
     COGNITION's/ECONOMY's own value once the fix lands correctly for
     other pillars' benefit. Document each such test-file diff in Test Summary per AC #4.
   - Location: `tests/simulation_quality/test_cognition_scorer.py`,
     `tests/simulation_quality/test_economy_scorer.py` (existing tests, edited)
   - Satisfies AC #4.

5. **Non-colliding scorer syntax stays inert**
   - Category: architecture guard
   - Verifies: at least one non-colliding scorer (e.g. `AgencyScorer` or `FactionScorer`)
     still resolves its weights correctly through whatever mechanism is chosen — a smoke
     test that the fix's mechanism doesn't require every scorer's `__init__`/call sites to
     change syntax, only that the *values* returned for the 4 affected scorers change. If
     the chosen mechanism does require every scorer's constructor to learn its own
     `PillarId` (see investigation.md's "no `self.pillar_id` today" finding), this test
     should instead confirm every `PillarScorer` subclass's declared pillar matches its
     `_rec()` closure's hardcoded `PillarId` (an existing correctness invariant worth
     locking down while touching this code, e.g. via a small
     `PillarScorer` → pillar-attribute round-trip check across all 10 scorer classes).
   - Location: new file `tests/simulation_quality/test_scorer_pillar_binding.py`, or folded
     into `test_weights.py` if lighter-weight.
   - Satisfies AC #4 (breadth requirement — "audit call sites... confirm each call site is
     updated consistently").

6. **Grade regression diff enumeration**
   - Category: integration / calibration regression
   - Verifies: after the fix, `tests/simulation_quality/test_grade_regression.py` is run in
     full (fast anchors at minimum; slow anchors if time allows) and every failing/changed
     anchor is captured — not silently re-baselined. This is not a new test file; it's the
     existing suite used as the AC #5 gate. The **output** of this run (which anchors
     changed, old vs. new grade/score) must be recorded in the ticket's Test Summary
     verbatim, with each diff either re-anchored in this ticket or named to an explicit
     follow-up ticket ID.
   - Location: `tests/simulation_quality/test_grade_regression.py` (existing, run not
     written)
   - Satisfies AC #5.

## Scoped Pytest Commands

```bash
# Weights unit tests (fastest signal — run first, iterate here before touching scorers)
pytest tests/simulation_quality/test_weights.py -v

# All pillar scorer unit tests (colliding + non-colliding, one scoped command)
pytest tests/simulation_quality/test_cognition_scorer.py \
       tests/simulation_quality/test_information_scorer.py \
       tests/simulation_quality/test_economy_scorer.py \
       tests/simulation_quality/test_world_dynamics_scorer.py \
       tests/simulation_quality/test_agency_scorer.py \
       tests/simulation_quality/test_combat_scorer.py \
       tests/simulation_quality/test_faction_scorer.py \
       tests/simulation_quality/test_progression_scorer.py \
       tests/simulation_quality/test_social_scorer.py \
       tests/simulation_quality/test_narrative_scorer.py \
       tests/simulation_quality/test_timegate_penalties.py -v

# QualityHub / integration wiring (confirm no construction-order regression)
pytest tests/simulation_quality/test_quality_hub_integration.py \
       tests/simulation_quality/test_quality_hub_event_translation.py \
       tests/simulation_quality/test_kernel_simq_integration.py \
       tests/simulation_quality/test_broker_feed_integration.py \
       tests/simulation_quality/test_feed.py \
       tests/simulation_quality/test_accumulator.py \
       tests/simulation_quality/test_persistence.py \
       tests/simulation_quality/test_report.py \
       tests/simulation_quality/test_traceability_path.py -v

# Full SimQ domain, not-slow (broad regression sweep before the calibration pass)
pytest tests/simulation_quality/ -m "not slow" -v

# Grade regression — the AC #5 gate; run separately and inspect output carefully,
# this is expected to produce real failures/diffs pre-re-anchoring
pytest tests/simulation_quality/test_grade_regression.py -v

# Slow/long-run anchors — only if time budget allows before closing the ticket
pytest tests/simulation_quality/test_grade_regression.py -m slow -v
```

Never run `pytest tests/` — scope stays within `tests/simulation_quality/` for this ticket;
no other domain's tests import or exercise `ScoringWeights`.

## Anti-Drift Test Guards

- **`test_getitem_known_key` (`test_weights.py:50-54`) must keep asserting exactly `12.0`
  for `harvest_active`** — a non-colliding key. If this value changes, someone has touched
  weight *values* (out of scope) rather than the *lookup mechanism* (in scope) — this test
  is a tripwire for scope creep into re-tuning.
- **The 4 exact test-file line locations expected to need value-oracle rewrites** (call
  these out explicitly in the PR/Test Summary so a reviewer can confirm nothing else
  silently changed):
  - `tests/simulation_quality/test_cognition_scorer.py:40` (`belief_active`)
  - `tests/simulation_quality/test_cognition_scorer.py:68` (`knowledge_rot`)
  - `tests/simulation_quality/test_cognition_scorer.py:102` (`subjective_divergence`)
  - `tests/simulation_quality/test_economy_scorer.py:126` (`knowledge_economy_active`)
  Any other test file's value assertion changing is unexpected and should be treated as a
  signal that the fix's blast radius was under-scoped, not folded in silently.
- **`test_information_scorer.py`'s `belief_active`/`subjective_divergence`/
  `knowledge_economy_active`/`omniscience_collapse` assertions (lines 39, 85, 110) must
  keep passing with the SAME numeric outcome pre- and post-fix** — INFORMATION was always
  the flat-dict "winner" for these keys, so its own scorer's behavior is invariant to this
  fix. If any of these 4 assertions changes value, the fix has been implemented backwards
  (COGNITION/ECONOMY's values leaking into INFORMATION instead of the reverse).
- **`test_world_dynamics_scorer.py`'s `ecology_cycling`/`ecology_broken` assertions
  (lines 48, 51-54) must keep passing with the SAME numeric outcome** — same invariance
  argument; WORLD was always the winner for this pair.
- **`test_grade_anchors_entry_count_unchanged` must keep asserting exactly `76`** — the
  re-anchoring work this ticket triggers must edit existing entries' `{grade, score}` values,
  never add/remove/duplicate a scenario key. A count drift here means an anchor was
  accidentally dropped or duplicated during re-anchoring, not just re-valued.
- **`int_param()` and `pillar_weight()` behavior must stay byte-identical** — add or keep a
  guard test confirming `scoring_weights.int_param("stasis_gate_ticks") == 5` and
  `scoring_weights.pillar_weight("COGNITION") == 1.0` (default profile) pass unchanged; these
  two accessors don't touch `_flat_rules` and must be provably untouched by the refactor.
- **No test should start passing by relying on `ScoringWeights.__getitem__`'s signature
  changing silently** — if the mechanism changes bare-string `[key]` syntax to require a
  pillar argument, every one of the 11 files listed in investigation.md's Risk #1 must show
  an explicit, intentional diff. A "some tests pass, some don't, nobody's sure why" outcome
  after the fix is the single biggest anti-drift risk on this ticket, precisely because 9 of
  those 11 files have *no logical reason* to need any change at all.
