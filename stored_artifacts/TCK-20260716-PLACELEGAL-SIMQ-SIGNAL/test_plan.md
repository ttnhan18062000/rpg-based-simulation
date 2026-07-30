---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260716-PLACELEGAL-SIMQ-SIGNAL
artifact_type: test_plan
tags: [simulation-quality, observability, world]
---

# Test Plan — TCK-20260716-PLACELEGAL-SIMQ-SIGNAL

## Regression Surface

Existing tests that must keep passing — grouped by category. All are affected because
`_translate_invariant()` gains a new branch, `WorldDynamicsScorer.EVENT_TYPES`/`score()` gains a
new event type, and `scoring_weights.yaml`'s `WORLD:` section gains a new key.

**Unit**
- `tests/simulation_quality/test_quality_hub_event_translation.py` — all existing
  `test_invariant_*` tests (`test_invariant_combat_law`, `test_invariant_conservation_law`,
  `test_invariant_unknown_no_translation`) must keep passing unmodified; confirms the new branch
  does not change `COMBAT*`/`CONSERVATION*` routing or the unknown-law pass-through default.
- `tests/simulation_quality/test_world_dynamics_scorer.py` — full file, especially the existing
  `building_sabotaged` block (lines ~148-155) and the `test_threat_evolved_no_score`/
  `test_node_recharged_no_score` `None`-return tests — confirms adding a new `EVENT_TYPES` entry and
  `score()` branch doesn't perturb existing event-type handling or the terminal `return None`.
- `tests/simulation_quality/test_scenario_coverage.py` — full file (SQ-01 through SQ-23); confirms
  no accidental cross-pillar leakage from the new branch (e.g. must not also get scored by
  `EconomyScorer`/`CombatScorer`).
- `tests/simulation_quality/test_scorer_pillar_binding.py` — confirms `WorldDynamicsScorer` stays
  correctly bound to `PillarId.WORLD` and the SCORER_REGISTRY wiring in `QualityHub.__init__` is
  unaffected by the new `EVENT_TYPES` entry.
- `tests/unit/simulation_quality/` (or wherever `ScoringWeights.load()` / `PillarWeightsView` unit
  tests live — locate during implementation) — confirms the new `WORLD:` weight key doesn't break
  YAML parsing, flat-index ambiguity detection, or trigger a spurious "declared in multiple
  pillars" `KeyError` (verify the new key name doesn't collide with an existing key in another
  pillar's section — check `config/simulation_quality/scoring_weights.yaml` for name collisions
  before choosing the final key).

**Integration**
- `tests/simulation_quality/test_traceability_path.py` — full file, especially
  `test_worst_event_id_resolves_in_simulation_events_jsonl` and
  `test_worst_event_id_matches_originating_envelope_exactly`; confirms the existing
  `combat_hard_law_violation`-via-`_event_recorder.record()` injection pattern this ticket's own
  new integration test should mirror still works unmodified.
- `tests/simulation_quality/test_kernel_simq_integration.py` — Kernel + QualityHub wiring; confirms
  no new exception path from the added dispatcher branch under normal Kernel construction/ticking.

**Config/contract consistency**
- Any test that loads `config/simulation_quality/scoring_weights.yaml` wholesale and asserts
  structural properties (e.g. every pillar section is a flat `str -> float` mapping) — locate via
  `grep -rl scoring_weights.yaml tests/` during implementation and re-run.

## New Tests Required

Per acceptance criteria (`tickets/inprogress/TCK-20260716-PLACELEGAL-SIMQ-SIGNAL.md`):

1. **`test_invariant_spawn_occupancy_law`**
   - Category: unit
   - Verifies: `QualityHub._translate(_env("InvariantViolation", {"law_id":
     "LAW-SPAWN-OCCUPANCY"}))` returns `event_type == "spawn_occupancy_violation"` (or whatever
     final event-type name Plan settles on) — direct sibling of `test_invariant_combat_law`/
     `test_invariant_conservation_law`, same `_env()` helper, same file.
   - Location: `tests/simulation_quality/test_quality_hub_event_translation.py`

2. **`test_invariant_spawn_occupancy_no_violation_no_translation`** (negative case, per AC's
   "violation present → event emitted; no violation → no event" framing)
   - Category: unit
   - Verifies: an `InvariantViolation` envelope with an unrelated/absent `law_id` (e.g.
     `{"law_id": "LAW-HP-NONNEGATIVE"}` or `{}`) does **not** translate to
     `spawn_occupancy_violation` — falls through to the existing `test_invariant_unknown_no_translation`-style
     pass-through, or (if `LAW-HP-NONNEGATIVE` etc. also legitimately fall through today) confirms
     no accidental cross-law contamination.
   - Location: `tests/simulation_quality/test_quality_hub_event_translation.py`

3. **`test_spawn_occupancy_violation_in_world_dynamics_event_types`**
   - Category: unit
   - Verifies: the new event type string is present in `WorldDynamicsScorer.EVENT_TYPES` — direct
     sibling of the existing `assert "building_sabotaged" in WorldDynamicsScorer.EVENT_TYPES`
     pattern (`test_world_dynamics_scorer.py` line ~150).
   - Location: `tests/simulation_quality/test_world_dynamics_scorer.py`

4. **`test_spawn_occupancy_violation_scores_negative`**
   - Category: unit
   - Verifies: `scorer.score(_env("spawn_occupancy_violation", payload={...}), _ctx())` returns a
     `ScoreRecord` with `delta < 0` (this is the one place this ticket's own scope text explicitly
     diverges from a literal `building_sabotaged` copy — building_sabotaged's `infrastructure_damaged`
     is `+2.0`; this signal must be negative, e.g. mirroring `ecology_broken`/`trauma_hazard_broken`'s
     sign). Assert `rec.delta == -weights["<chosen_key>"]` is **not** the right assertion shape (the
     weight itself should already be negative in YAML, so `rec.delta == weights["<chosen_key>"]` with
     a negative stored value) — confirm the actual sign convention against `_rec()`'s call shape once
     the key is chosen.
   - Location: `tests/simulation_quality/test_world_dynamics_scorer.py`

5. **`test_scoring_weights_yaml_has_spawn_occupancy_key`**
   - Category: unit / config-consistency guard
   - Verifies: loading `ScoringWeights.load(...)` and calling
     `weights.for_pillar(PillarId.WORLD)["<chosen_key>"]` does not raise `KeyError` — guards the
     hard runtime dependency identified in investigation.md (§7.2 step 2a; `config/simulation_quality/
     scoring_weights.yaml`'s `WORLD:` section must contain the new key or every real score() call
     hard-crashes).
   - Location: `tests/simulation_quality/test_world_dynamics_scorer.py` or a scoring-weights-specific
     test file if one exists (locate during implementation).

6. **End-to-end propagation test, following the `test_traceability_path.py` injection pattern**
   (name TBD, e.g. `test_spawn_occupancy_violation_reaches_world_pillar_via_minimal_kernel`)
   - Category: integration
   - Verifies: using the `minimal_kernel` fixture pattern from `test_traceability_path.py`, call
     `kernel._event_recorder.record(SimulationEvent(event_type="InvariantViolation",
     event_category="hard_law", tick=0, severity="ERROR", source_system="hard_law_monitor",
     message="...", entity_id=<id>, payload={"law_id": "LAW-SPAWN-OCCUPANCY", "object_kind":
     "entity", ...}))` directly (bypassing the currently-nonexistent real emission path from
     `_run_initial_placement_check()` — see investigation.md's blocking finding), then assert
     `kernel._quality_hub.get_quality_report().pillars["WORLD"].worst_events` is non-empty and the
     matching record traces back to `simulation_events.jsonl`, mirroring
     `test_worst_event_id_resolves_in_simulation_events_jsonl` exactly. **This is the only test in
     this plan that exercises the full `QualityHub.on_envelope()` → `_translate` → `WorldDynamicsScorer.score`
     → `PillarAccumulator` path with a real `Kernel` instance**, and it deliberately does not depend
     on `Kernel._run_initial_placement_check()` actually emitting the event in production — that gap
     is a separate, currently-unresolved question (see investigation.md) and must not be silently
     papered over by this test pretending the production wiring exists.
   - Location: `tests/simulation_quality/test_traceability_path.py` (co-locate with the existing
     `combat_hard_law_violation` injection test, or a new sibling file if the existing file's fixture
     scope doesn't fit — check during implementation).

7. **Contract-doc consistency check** (may be a doc-lint/manual verification rather than a pytest
   test, per how `quality_scoring_contract.md` changes are normally verified in this repo — confirm
   during implementation whether an automated doc-parity test exists; `test_scenario_coverage.py`'s
   docstring claims coverage of "all 22 scenarios from §6" but is hand-written, not doc-scraped)
   - Category: architecture guard / manual
   - Verifies: all four `building_sabotaged`-parallel touch points for the new signal, per plan.md
     Step 3 (Revision 1) —
     `docs/simulation_quality/quality_scoring_contract.md`'s §5 "Event types scored" list, §5
     Signal/Delta/Tag table row, and §6 Scenario Registry `SQ-24` row; plus
     `docs/simulation_quality/event_type_coverage.md`'s §1.3 `_TRANSLATE_CONDITIONAL` table row
     (mirroring the `COMBAT`/`CONSERVATION` rows), the Summary table's "scored" count (82 → 83), and
     the "Last updated" line — this fourth location was added after architecture review found the
     real `building_sabotaged` precedent (`TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`) touched this
     doc too, and its "all `_TRANSLATE_CONDITIONAL` entries correct and complete" claim would go
     stale without it.
   - Location: manual verification during Implement + Verify phases; no dedicated test file unless
     one already exists (locate via `grep -rl quality_scoring_contract test*` during implementation).

8. **Anchor/grade-stability check** (AC-mandated, not a pytest test)
   - Run `make evaluate --dry-run` (= `python3 tools/evaluate_simq.py --dry-run`, confirmed real
     target, `Makefile:321-322`) before and after the code change.
   - **Per investigation.md's blocking finding, expect zero diff in both directions** under current
     wiring — `evaluate_simq.py --dry-run` only diffs existing `data/calibration/` reports against
     `grade_anchors.json`, and no real calibration run's `simulation_events.jsonl` will contain a
     `LAW-SPAWN-OCCUPANCY`-derived event unless `Kernel._run_initial_placement_check()` is also
     changed to emit one (currently out of this ticket's stated scope). **This AC, as literally
     written in the ticket ("affected runs show a real, expected grade delta"), cannot be
     satisfied by this ticket's stated Scope alone** — flag to Plan/requester rather than silently
     treating a no-op `--dry-run` diff as passing evidence of a working signal.
   - If Plan resolves the blocking finding by adding minimal event emission to
     `_run_initial_placement_check()`: re-run `tools/calibrate_simq.py` against a world/seed known to
     reproduce the seed-42 collision (e.g. `unit_information_density` at `seed=42`, per the parent
     ticket's regression test), then `make evaluate --dry-run` (or `evaluate-full` to force a fresh
     run) to confirm a real grade delta appears for that scenario and no delta appears for unaffected
     anchors (e.g. `wilderness_survival`, confirmed clean by the parent ticket).

## Scoped Pytest Commands

```bash
# QualityHub dispatch table (existing + new _translate_invariant branch)
.venv/bin/python3 -m pytest tests/simulation_quality/test_quality_hub_event_translation.py -v

# WorldDynamicsScorer (existing + new EVENT_TYPES/score() branch)
.venv/bin/python3 -m pytest tests/simulation_quality/test_world_dynamics_scorer.py -v

# Scenario coverage / cross-pillar ownership guard
.venv/bin/python3 -m pytest tests/simulation_quality/test_scenario_coverage.py -v

# Scorer-pillar binding guard
.venv/bin/python3 -m pytest tests/simulation_quality/test_scorer_pillar_binding.py -v

# Traceability path (existing combat_hard_law_violation injection pattern + new spawn-occupancy sibling)
.venv/bin/python3 -m pytest tests/simulation_quality/test_traceability_path.py -v

# Kernel + QualityHub wiring
.venv/bin/python3 -m pytest tests/simulation_quality/test_kernel_simq_integration.py -v

# Full simulation_quality unit/integration suite (scoped to the module actually touched)
.venv/bin/python3 -m pytest tests/simulation_quality/ -v

# Anchor/grade-stability check (not pytest — see New Tests Required #8)
make evaluate --dry-run
```

Do not run `pytest tests/` — scope to `tests/simulation_quality/` (the domain actually modified)
per project testing rule. `tests/engine/test_hard_law_monitor.py` and
`tests/integration/observability/test_initial_placement_check.py` (the parent ticket's own tests)
do **not** need to be re-run by this ticket unless Plan decides to modify
`_run_initial_placement_check()` to resolve the blocking finding — if so, add those two files to
this list.

## Anti-Drift Test Guards

- **`test_combat_conservation_branches_unmodified`** (or simply: the existing
  `test_invariant_combat_law`/`test_invariant_conservation_law` tests passing unmodified) — guards
  against the new `LAW-SPAWN-OCCUPANCY` branch accidentally being inserted in a way that shadows or
  reorders the existing `COMBAT`/`CONSERVATION` `startswith()` checks (e.g. an overly broad prefix
  match placed before them).
- **`test_economy_scorer_conservation_untouched`**: assert `EconomyScorer.EVENT_TYPES` and its
  `conservation_law_violated`/`conservation_law_verified` handling are byte-identical after this
  ticket's diff — guards against scope creep into the explicitly-out-of-scope `CONSERVATION` branch.
- **`test_no_new_pillar_introduced`**: assert `PillarId` enum membership is unchanged (still the
  same 10 pillars) — guards against accidentally promoting this into an 11th pillar, which both this
  ticket's Out of Scope and the cited `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC` §2.7 conclusion
  ("No new top-level pillar is justified") explicitly forbid.
- **`test_spawn_occupancy_weight_is_negative`**: explicit assertion that the chosen weight key's
  value in `scoring_weights.yaml`'s `WORLD:` section is `< 0` — guards against the single most likely
  literal-copy-of-`building_sabotaged` mistake (positive `+2.0`-style weight) identified in
  investigation.md.
- **`test_hard_law_monitor_and_kernel_init_untouched`**: this ticket's diff must not touch
  `src/observability/hard_law_monitor.py` or `Kernel.__init__`/`_run_initial_placement_check()`'s
  existing mode-gating/persistence/alert-routing code — confirmed via the parent ticket's own
  `tests/engine/test_hard_law_monitor.py` and `tests/integration/observability/
  test_initial_placement_check.py` passing unmodified (re-run only if Plan decides to add event
  emission there to resolve the blocking finding; if so, the guard becomes "only the new
  `SimulationEvent` construction + `record()` call are added, nothing else changes").
- **`test_evaluate_dry_run_unaffected_anchors_unchanged`**: run `make evaluate --dry-run` and assert
  (manually, or via a wrapper script) that grades for anchors *not* built on the seed-42 collision
  worlds (`wilderness_survival`, etc.) show no diff before/after — directly satisfies the ticket's
  own "existing anchor runs... show no grade change" AC half, independent of whether the blocking
  finding is resolved.
