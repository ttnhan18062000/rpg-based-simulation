---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-SOCIAL
artifact_type: test_plan
tags: [simulation-quality, social, world, corpus, calibration, feature-flags]
---

# Test Plan — TCK-20260710-SIMQ-DEPTH-SOCIAL

## Regression Surface

Existing tests that must keep passing after this ticket's profile-YAML-only edits and parity-ledger update.

**Unit — cooperation domain (must not regress; this ticket does not touch these files, but flag activation on new worlds exercises them for the first time in those worlds' calibration runs):**
- `tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py`
- `tests/unit/domains/cooperation/test_phase7_partner_candidate_provider.py`
- `tests/unit/domains/cooperation/test_phase7_partner_fit_evaluator.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_intent_bridge.py`
- `tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py`
- `tests/unit/domains/cooperation/test_phase7_party_objective_alignment.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_learning.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_postures.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_events.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_boundary.py`
- `tests/unit/domains/cooperation/test_cooperation_phase.py`

**Unit — social domain (group formation law SOC-007 touches these):**
- `tests/unit/social/test_domain_7_social.py`
- `tests/unit/social/test_social_party_regression.py`
- `tests/unit/social/test_multi_hero.py`
- `tests/unit/social/test_party_agency.py`
- `tests/unit/social/test_phantom_leader.py`
- `tests/unit/social/test_social_contracts.py`
- `tests/unit/social/test_social_bonds.py`
- `tests/unit/social/test_social_lifecycle.py`
- `tests/unit/social/test_social_phase7.py`
- `tests/unit/social/test_social_memory.py`

**Unit — observability (cooperation_event emission contract, PP-05):**
- `tests/unit/observability/test_event_extractor_social_faction.py`
- `tests/unit/observability/test_event_extractor_social_memory.py`

**Integration:**
- `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py`

**Perf (budget guard — relevant since this ticket adds live per-tick cooperation evaluation to 2 more worlds' populations):**
- `tests/perf/test_phase7_social_cooperation_budget.py`

**Simulation-quality regression (grade-anchor suite — the direct regression surface for this ticket's own acceptance criteria):**
- `tests/simulation_quality/test_grade_regression.py` — covers `FAST_ANCHOR_KEYS`, which already includes `frontier_living_world_seed{42,123,456}_200t` and `highland_traverse_seed{42,123,456}_200t` (pre-existing anchors from the prior FACTION/INFORMATION expansion ticket). These anchors' non-SOCIAL pillars (FACTION=S, INFORMATION=B, etc.) must remain unchanged; only `SOCIAL` moves.
- `tests/simulation_quality/` world-composition/content tests that read `data/content/world_compositions/{frontier_living_world,highland_traverse}.yaml` mirrors (e.g. `test_real_content_world_compositions.py`, referenced in `eval_matrix_results.md:744`) — this ticket does not touch world composition, only calibration-profile YAML, so these should be unaffected, but must still be run to confirm no incidental drift.

**Explicitly NOT required (out of scope, confirmed no touch):**
- `dungeon_crawl`'s own grade-anchor tests (`dungeon_crawl_seed*_{200,500,1000,2000}t`) — this ticket does not add `ENABLE_SOCIAL_COOPERATION` to `dungeon_crawl`'s profile (see investigation.md's empirical finding: 0 SOCIAL events with flag ON). These anchors must be run as regression-surface (their SOCIAL=C values must NOT change) but require no new anchor edits.
- `urban_political`'s anchors — untouched control world, regression-only.

## New Tests Required

Acceptance-criterion-mapped. This ticket's actual code change is profile-YAML-only (`feature_flags: ENABLE_SOCIAL_COOPERATION: "ON"` in 2 files) plus a parity-ledger doc update — so "new tests" here means grade-anchor updates (which are themselves tests, evaluated by `test_grade_regression.py`) and any missing observability coverage the investigation surfaced as a gap, not new unit-test files for `CooperationPhase` internals (already covered).

1. **Anchor update — `frontier_living_world_seed{42,123,456}_200t` SOCIAL field**
   - Category: simulation-quality grade regression (via `tests/simulation_quality/test_grade_regression.py`, data-driven from `grade_anchors.json`)
   - Verifies: SOCIAL grade for `frontier_living_world` at 200t, seeds 42/123/456, moves from `C` (pre-activation, currently anchored) to the actual post-activation grade obtained by a real 3-seed calibration run with the flag ON in the committed profile YAML (seed42 empirically confirmed `S`/545 events in this investigation's scratch probe — Implement must re-run for-real against the committed profile to get the canonical anchor values, since the scratch probe used an env-var override, not the committed YAML).
   - Location: `tests/simulation_quality/fixtures/grade_anchors.json` (edit in place, 3 existing keys), no new key needed. `FAST_ANCHOR_KEYS` in `test_grade_regression.py` already lists all 3 — no addition needed.

2. **Anchor update — `highland_traverse_seed{42,123,456}_200t` SOCIAL field**
   - Category: simulation-quality grade regression
   - Verifies: same as above for `highland_traverse` (seed42 empirically confirmed `S`/1496 events).
   - Location: same file, 3 existing keys, no new `FAST_ANCHOR_KEYS` entry needed (already present).

3. **`cooperation_event` non-zero assertion for both newly-activated worlds**
   - Category: integration / calibration smoke check
   - Verifies: acceptance criterion "SOCIAL grade moves measurably off C (calibration_hits > 0 for `cooperation_event`...)" is directly checkable — either as an assertion inside the grade-regression test's per-world event-count check (if the harness already exposes `event_count` per pillar per anchor, confirm and reuse) or as a small standalone assertion added to whichever calibration-summary test currently exists for the corpus. Do not write a bespoke new test file if the grade-anchor mechanism already encodes this (it does — `grade_anchors.json` values are graded from `event_count`).
   - Location: `tests/simulation_quality/test_grade_regression.py` (extend only if the existing anchor-diff mechanism does not already surface event counts; verify before adding).

4. **SOC-007 evidence-path correction test (parity-ledger hygiene, surfaced by this investigation, not by the ticket's original scope, but required because this ticket is the one touching SOC-007)**
   - Category: architecture guard / parity-ledger hygiene
   - Verifies: `docs/parity_ledger/social_narrative.yaml`'s SOC-007 `v2_evidence` path (`src/systems/groups.py`) actually resolves to a real file, and `test_path` (`tests_v2/parity/test_group_coordination.py`) actually exists and passes. Both currently fail this check (stale path, nonexistent test file) — confirmed independently of this ticket's SOCIAL-activation work. Fix as part of this ticket's SOC-007 edit: correct `v2_evidence` to `src/systems/world_systems/groups.py` (class `GroupSystem` is correct), and point `test_path` at real, passing coverage (`tests/unit/social/test_social_party_regression.py` is the closest existing match for "proximity alone does not create a party" — confirm it actually asserts that law before citing it; otherwise add a minimal new assertion there rather than inventing a new file).
   - Location: `docs/parity_ledger/social_narrative.yaml` (SOC-007 entry) + whichever test file is chosen/confirmed above.

5. **World-population baseline-alive floor check for the 2 newly-activated worlds**
   - Category: regression / population stability
   - Verifies: acceptance criterion "holds its existing population-alive floor... through its calibration run length" — check whether `tests/simulation_quality/` already has a `test_population_stability[<world>]`-style parametrized test (confirmed pattern exists for `wilderness_survival` per `eval_matrix_results.md:701`); if so, confirm `frontier_living_world`/`highland_traverse` are already parametrized into it (likely yes, from the prior FACTION/INFORMATION ticket) and simply re-run; do not duplicate.
   - Location: wherever `test_population_stability` is defined (search before assuming; not independently located in this investigation).

## Scoped Pytest Commands

```
# Cooperation domain unit + integration (regression surface, unaffected by this ticket's changes but must stay green)
pytest tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ -v

# Social domain unit tests (group formation law SOC-007 touches these)
pytest tests/unit/social/ -v

# Observability event-extraction contract (cooperation_event / PP-05)
pytest tests/unit/observability/test_event_extractor_social_faction.py tests/unit/observability/test_event_extractor_social_memory.py -v

# Cooperation scenario integration + perf budget guard
pytest tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py tests/perf/test_phase7_social_cooperation_budget.py -v

# SimQ grade-regression suite (the direct acceptance-criteria check — this is the one that must show
# frontier_living_world/highland_traverse SOCIAL C->S and dungeon_crawl/urban_political unchanged)
pytest tests/simulation_quality/test_grade_regression.py -v

# Full simulation_quality directory (composition/content mirrors + grade regression together)
pytest tests/simulation_quality/ -v
```

Never `pytest tests/`. Not scoped to `-m "not slow"` broadly since `test_grade_regression.py` itself is the acceptance-criteria-bearing test and must run in full for this ticket; if it is independently marked `slow`, run it explicitly by path rather than relying on marker-based inclusion.

Full corpus sweep (`make evaluate` / `make evaluate-full`) is a separate, non-pytest Verify-phase step per the ticket's own scope item 6 — not part of the scoped pytest commands above, budgeted separately (see investigation.md's Compute/Timing Feasibility section).

## Anti-Drift Test Guards

- **`dungeon_crawl` anchors must show zero diff.** Since this ticket does not add the flag to `dungeon_crawl`'s profile, any test run showing `dungeon_crawl_seed*_*t` SOCIAL moving off `C`, or any other pillar shifting, indicates an unintended cross-contamination (e.g., a stray env var leaking into a real profile-YAML edit, or accidentally editing the wrong profile file) — this must fail loudly, not be silently reconciled.
- **`urban_political` anchors must show zero diff.** Same rationale — the control world for SOCIAL must be untouched by this ticket.
- **Non-SOCIAL pillars in the touched worlds' anchors must show zero diff.** `frontier_living_world`/`highland_traverse` anchors currently encode FACTION=S, INFORMATION=B, COGNITION=B/C (dual-emission, pre-existing from the earlier expansion ticket) at seed42_200t — this ticket's scope-guard is that only the `SOCIAL` field of these 6 anchor entries changes. A diff touching FACTION/INFORMATION/COGNITION/COMBAT/etc. numeric values for these worlds is an unattributed regression per the acceptance criteria and must be investigated, not merged.
- **`ENABLE_SOCIAL_COOPERATION` must be the only new key** added to `config/simulation_quality/profiles/{frontier_living_world,highland_traverse}.yaml`'s `feature_flags:` block — both files already carry `ENABLE_BELIEF_ASSIMILATION: "ON"` from the prior INFORMATION expansion; a diff that touches or removes that existing key is scope creep.
- **`apply_generation()` and `CooperationPhase`'s serialization sentinel must show zero diff** in `src/engine/apply.py` / `src/domains/cooperation/phase.py` — these were already fixed by `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`; any diff touching them in this ticket's PR is an explicit anti-scope violation per the ticket's Out of Scope section.
- **SOC-007's `test_path` fix must resolve to a real, passing file** — do not leave a "corrected" path that still points at a nonexistent file; run the chosen test file explicitly (`pytest <path> -v`) before citing it in the parity ledger.
- **Full-sweep COGNITION drift must be attributed, not absorbed.** Per the ticket's own Pattern-6 warning, if `make evaluate`'s full-sweep diff shows COGNITION movement in `frontier_living_world`/`highland_traverse`, cross-check it against the *pre-existing* `ENABLE_BELIEF_ASSIMILATION`-driven COGNITION signal documented in `eval_matrix_results.md` (already present before this ticket) before attributing any COGNITION delta to this ticket's SOCIAL flag flip.
