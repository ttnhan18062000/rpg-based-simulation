---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260716-PLACELEGAL-SIMQ-SIGNAL
phase: done
date: 2026-07-16
tags: [simulation-quality, observability, world]
---

# TCK-20260716-PLACELEGAL-SIMQ-SIGNAL

## Title
Route the new spawn-occupancy hard-law violation into SimQ's WORLD DYNAMICS pillar as a frequency-scored signal

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`src/simulation_quality/quality_hub.py`'s `_translate_invariant()` is an already-shipped `law_id`-prefix dispatcher routing `HardLawMonitor` violations into SimQ scored events — it already routes `COMBAT`-prefixed violations to `combat_hard_law_violation`, scored by `CombatScorer`. `TCK-20260716-PLACELEGAL-HARDLAW` (this folder) adds a new law (working name `LAW-SPAWN-OCCUPANCY`) with no existing dispatcher branch. This ticket adds that branch and its scoring, following the exact precedent of the existing `building_sabotaged` row (`WorldDynamicsScorer`, `docs/simulation_quality/quality_scoring_contract.md` SQ-23): a system outside SimQ produces an event, WORLD DYNAMICS scores its frequency as a gradient.

This follows a real, already-established project precedent rather than inventing new SimQ scope: SimQ's own prior investigation (`stored_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2.2) explicitly excluded *determinism* from SimQ's scope — *"does not score correctness — that is `hard_law_monitor`; determinism/replay is a correctness property, not a health gradient."* Placement legality (is this one position walkable, yes/no) is a correctness property in exactly the same sense — a binary fact about one instant, not itself a gradient. What SimQ scores here is not "was this placement legal" (that's `HardLawMonitor`'s job, done in the parent ticket) but "how often does this violation class occur" — a frequency signal, same shape as `building_sabotaged`.

## Scope
- `src/simulation_quality/quality_hub.py::_translate_invariant()`: add a new branch matching the new law's `law_id` prefix (e.g. `LAW-SPAWN-OCCUPANCY`, confirmed against the parent ticket's final naming), routing to a new event type (e.g. `spawn_occupancy_violation`) — mirroring the existing `COMBAT*` branch's shape exactly.
- `src/simulation_quality/scorers/world_dynamics.py::WorldDynamicsScorer`: add the new event type to `EVENT_TYPES`, and add scoring logic matching the `building_sabotaged` row's shape (`worth_dynamics.py:175-176`) — a negative/penalized signal, since this event only ever represents a correctness violation (unlike some WORLD signals that have a healthy range, this one is unconditionally bad — zero occurrences is the correct target).
- `docs/simulation_quality/quality_scoring_contract.md`: add one new signal row to the `WORLD DYNAMICS` pillar table, matching the exact shape/column format of the existing `building_sabotaged` row (SQ-23).
- Confirm no re-anchor risk: run SimQ's existing anchor/grade-check tooling (`make evaluate --dry-run` or equivalent, per the `obs-isolation` folder's precedent for this exact check) against the current corpus before and after the change — the new signal should only fire on worlds/runs that already exhibit the reproduced seed-42 collision (a small, known subset), so existing anchor grades for unaffected runs must not shift.

## Out of Scope
- Anything in `HardLawMonitor` itself, or the call-site wiring in `Kernel.__init__` — entirely owned by `TCK-20260716-PLACELEGAL-HARDLAW` (this ticket only consumes the `law_id` that ticket produces).
- Any change to `EconomyScorer`'s existing, already-fully-wired `CONSERVATION` branch (`conservation_law_violated`/`conservation_law_verified`) — a separate, unrelated, already-complete piece of `_translate_invariant()`, not touched here.
- A new SimQ pillar or a standalone determinism-scoring mechanism — explicitly rejected per the Request Summary's precedent citation; this is a WORLD DYNAMICS frequency signal, not a new correctness-scoring system.
- Historical/retroactive re-scoring of past runs' existing `hard_law_violations.jsonl` records that predate this signal's addition.

## Acceptance Criteria
- [x] `_translate_invariant()` correctly routes the new law's violations to the new event type; unit test covers both branches (violation present → event emitted; no violation → no event), mirroring existing `COMBAT*` branch test coverage.
- [x] `WorldDynamicsScorer.EVENT_TYPES` includes the new event type; scoring logic produces a real, non-zero grade delta when the event fires, matching the `building_sabotaged` row's negative-signal shape.
- [x] `docs/simulation_quality/quality_scoring_contract.md` WORLD DYNAMICS table has a new row for this signal, in the same format as SQ-23.
- [x] Anchor/grade-stability check: existing anchor runs (unaffected by the seed-42 collision) show no grade change after this signal is added; affected runs show a real, expected grade delta.
- [x] Depends on `TCK-20260716-PLACELEGAL-HARDLAW` being DONE first — the new `law_id` must exist and be producing real violations before this ticket's dispatcher branch has anything to route.

## Related Tickets
TCK-20260716-PLACELEGAL-HARDLAW (must complete first — see `SEQUENCE.md` in this folder)

## Related Docs
docs/plans/idea_placement_legality_check.md (originating investigation), docs/simulation_quality/quality_scoring_contract.md (WORLD DYNAMICS pillar table, SQ-23 precedent row), stored_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md (§2.2, the determinism-exclusion precedent this ticket's scope is built on)

## Related Stored Artifacts
none yet

## Related Code Areas
src/simulation_quality/quality_hub.py (`_translate_invariant`), src/simulation_quality/scorers/world_dynamics.py (`WorldDynamicsScorer`, `EVENT_TYPES`), docs/simulation_quality/quality_scoring_contract.md

## Assumptions / Open Questions
- Exact event-type name (`spawn_occupancy_violation` working name) and scoring weight — not calibrated; follow the same calibration discipline as other WORLD DYNAMICS signals (`tools/calibrate_simq.py` if a real weight-tuning pass is warranted, or a reasonable default matching `building_sabotaged`'s magnitude if the signal is expected to be rare).
- Whether this signal needs a positive/"no violations this run" counterpart event (mirroring `CONSERVATION`'s paired `_violated`/`_verified` events) or whether absence-of-event is sufficient (matching `building_sabotaged`, which has no positive counterpart) — default to no positive counterpart unless Investigate finds a concrete scoring reason to add one.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260716-PLACELEGAL-SIMQ-SIGNAL/plan.md`'s 6 steps
(both prior review rounds already APPROVED; Revision 1 already folded into the plan before
Implement started):

1. **`src/simulation_quality/quality_hub.py::_translate_invariant()`** — added a third branch,
   `law_id.startswith("LAW-SPAWN-OCCUPANCY")` → `"spawn_occupancy_violation"`, placed after the
   existing `COMBAT`/`CONSERVATION` branches, before the pass-through default. `COMBAT`/`CONSERVATION`
   branches, order, and `_TRANSLATE_CONDITIONAL`'s registration table (`InvariantViolation` was
   already registered) untouched.

2. **`src/simulation_quality/scorers/world_dynamics.py::WorldDynamicsScorer`** — added
   `"spawn_occupancy_violation"` as the 16th `EVENT_TYPES` entry (after `building_sabotaged`), and a
   new unconditional `score()` branch (`return _rec(self.weights["spawn_occupancy_violation"], ...)`)
   placed directly after the `building_sabotaged` branch, exactly as specified in the plan.
   `config/simulation_quality/scoring_weights.yaml`'s `WORLD:` section got `spawn_occupancy_violation:
   -30.0`, grouped with the negative-weight block after `trauma_accumulation_broken: -8.0` — mirrors
   `combat_hard_law: -30.0`'s magnitude, not `building_sabotaged`'s positive `+2.0` sign (per the
   plan's explicit Anti-Drift Note).

3. **Docs (4 edits, 2 files, per Revision 1's already-approved scope):**
   `docs/simulation_quality/quality_scoring_contract.md` — appended `spawn_occupancy_violation` to
   §5's "Event types scored" list; added a `| Spawn placement violates occupancy/terrain legality
   (LAW-SPAWN-OCCUPANCY) | −30 | spawn_occupancy_violation |` row to §5's Signal/Delta/Tag table
   (negative-signal block, directly after the `infrastructure_damaged` row); added a new `SQ-24` row
   to §6 Scenario Registry directly after `SQ-23`. `docs/simulation_quality/event_type_coverage.md` —
   appended a `spawn_occupancy_violation` row to §1.3's `_TRANSLATE_CONDITIONAL` table (mirroring the
   `COMBAT`/`CONSERVATION` rows' shape, under the same `InvariantViolation` key — no new dict key, so
   the doc's "5 `_TRANSLATE_CONDITIONAL` entries" count at lines 36/177 stays accurate and did not
   need updating); bumped the Summary "scored" count 82 → 83; updated the "Last updated" line.

4. **`src/engine/kernel.py::_run_initial_placement_check()`** — user-approved narrow scope
   extension (see plan.md Deviations). Added one new block directly after the existing
   `AlertsManager` routing `try/except`, before the final `mode in (DEBUG, CERTIFICATION)`
   raise/`LIGHT` log branch: constructs one `SimulationEvent(event_type="InvariantViolation",
   event_category="hard_law", tick=0, ...)` per violation, with `payload["law_id"] = v.law_id`
   explicitly merged into `dict(v.details)` (load-bearing — `v.details` never carries `law_id`
   natively, confirmed by direct source read during planning), and records it via
   `self._event_recorder.record(event)`. Confirmed via direct source read that `self._event_recorder`
   is assigned at `Kernel.__init__` line 260, well before `_run_initial_placement_check()`'s call site
   at line 321 — so the `is not None` guard is always-true/defensive, kept per the plan's explicit
   ruling (Revision 1's reviewer note). Existing mode-gating, `hard_law_violations.jsonl` persistence,
   and `AlertsManager` routing are byte-identical before/after; `HardLawMonitor.check_initial_placement()`
   and the `Kernel.__init__` call site (still called exactly once) are untouched.

5. **`tests/simulation_quality/test_traceability_path.py`** — two new tests, both passing:
   `test_spawn_occupancy_violation_reaches_world_pillar_via_minimal_kernel` (injection-pattern,
   mirrors `_inject_combat_hard_law_violation`) and
   `test_spawn_occupancy_violation_reaches_world_pillar_via_real_kernel_construction` (constructs a
   real `Kernel` against `unit_information_density` compiled at `seed=42` — the parent ticket's known
   entity-6/entity-14 tile-(27,38) collision — and confirms `WORLD.worst_events` is populated purely
   from `Kernel.__init__`'s real production wiring, proving Step 4's block actually fires). Also added
   `test_invariant_spawn_occupancy_law`/`test_invariant_spawn_occupancy_no_violation_no_translation`
   (`test_quality_hub_event_translation.py`) and a `TestSpawnOccupancyViolation` class in
   `test_world_dynamics_scorer.py` (`EVENT_TYPES` membership, negative-delta scoring, YAML-key
   presence, and the Anti-Drift `weight < 0` guard).

6. **Anchor/grade-stability check** — `python3 tools/evaluate_simq.py --dry-run` first confirmed a
   trivial 0-pillars/0-regressions baseline (this sandbox's `data/calibration/` starts empty — matches
   the pre-existing `test_grade_anchor_file_exists_and_valid` failure, see Test Summary). Regenerated
   calibration for the known-affected scenario (`tools/calibrate_simq.py --name
   unit_information_density --seed 42 --ticks 200`): WORLD pillar shifted from the committed anchor
   (`B`, score 0.03, 0 WORLD events) to `C`, score -0.12, 2 WORLD events — a real, negative,
   non-trivial delta directly attributable to `spawn_occupancy_violation` firing twice (both of
   `HardLawMonitor.check_initial_placement()`'s two emission sites for the entity-6/entity-14
   collision). `--dry-run` reports this as `PASS` (not `REGRESS`) because the tool's `_within_band()`
   tolerance is ±1 grade step and B→C is exactly 1 step — expected, correct tool behavior, not a bug;
   the score-level delta is real and visible in the report. Also regenerated calibration for
   `wilderness_survival` (seed=42, 200t — confirmed collision-free by the parent ticket) as the
   unaffected-anchor control: WORLD pillar matched the committed anchor exactly (`B`==`B`, 4 events
   both times) — confirms no diff for an unaffected anchor. Neither `grade_anchors.json` nor any other
   committed fixture was edited, per the plan's explicit "Do NOT touch" guard and the `obs-isolation`
   "stop and investigate before recalibrating" precedent. `data/calibration/`'s two newly-generated
   report directories, `data/runs/`, and `reports/release_proof/` were all cleaned up afterward (both
   directories are gitignored/transient per `.gitignore`).

**Deviation beyond plan.md's own two documented deviations (recorded as plan.md Revision 2):** while
implementing, found that the already-twice-reviewed, APPROVED plan's Step 3 scope (contract doc +
`event_type_coverage.md`) omitted a parity ledger entry, even though `investigation.md`'s Parity
Ledger Overlap section had explicitly flagged one as needed ("No existing parity ledger entry
currently documents `_translate_invariant()`'s `law_id` dispatch table... A new entry is needed").
Per the project's Authoritative Mechanics Rule ("If logic changes, update the corresponding doc AND
the parity ledger entry... in the same session"), added `WORLD-113` to
`docs/parity_ledger/world_dynamics.yaml` (status: verified, priority: P2, following `WORLD-112`'s
exact shape) documenting the new dispatcher branch, scorer, weight, and Step 4's Kernel emission
path, with `test_path` pointing at the new tests. Recorded as plan.md Revision 2 rather than silently
added. No code behavior changed as a result; no other parity ledger entry was touched.

## Test Summary
All new tests pass; all pre-existing regression-surface tests listed in `test_plan.md` pass
unmodified, except one confirmed pre-existing failure unrelated to this ticket (see below).

```
.venv/bin/python3 -m pytest tests/simulation_quality/test_quality_hub_event_translation.py \
  tests/simulation_quality/test_world_dynamics_scorer.py \
  tests/simulation_quality/test_scenario_coverage.py \
  tests/simulation_quality/test_scorer_pillar_binding.py -q
# 107 passed

.venv/bin/python3 -m pytest tests/simulation_quality/test_traceability_path.py -q
# 5 passed (2 new: minimal_kernel injection + real Kernel-construction wiring test)

.venv/bin/python3 -m pytest tests/simulation_quality/test_kernel_simq_integration.py -q
# 4 passed

.venv/bin/python3 -m pytest tests/engine/test_hard_law_monitor.py \
  tests/integration/observability/test_initial_placement_check.py -q
# 14 passed — parent ticket's own tests, confirms zero collateral change to
# detection/persistence/alerting

.venv/bin/python3 -m pytest tests/simulation_quality/ -q
# 435 passed, 78 skipped, 1 pre-existing failure (test_grade_regression.py::
# test_grade_anchor_file_exists_and_valid — confirmed via `git stash` to fail
# identically before this ticket's diff; caused by a missing
# data/calibration/hero_guild_routing_seed42_1000t report file in this sandbox,
# unrelated to spawn_occupancy_violation)

python3 tools/validate_frontmatter.py <all touched docs/ticket/artifacts>
# OK — no violations

.venv/bin/python3 -m pytest tests/tools/test_parity_ledger_scan.py -q
# 3 passed — confirms the new WORLD-113 entry doesn't break parity ledger validation
```

Anchor/grade-stability check (`python3 tools/evaluate_simq.py --dry-run`): see Implementation Notes
step 6 for full detail — unaffected anchor (`wilderness_survival_seed42_200t`) exact match; affected
anchor (`unit_information_density_seed42_200t`) shows a real WORLD-pillar score delta (0.03 → -0.12),
reported `PASS` under the tool's ±1-grade-band tolerance (B→C), which is expected tool behavior, not
a defect.

## Files Changed
- `src/simulation_quality/quality_hub.py` — new `LAW-SPAWN-OCCUPANCY` branch in `_translate_invariant()`
- `src/simulation_quality/scorers/world_dynamics.py` — `spawn_occupancy_violation` added to `EVENT_TYPES` + new `score()` branch
- `config/simulation_quality/scoring_weights.yaml` — `WORLD: spawn_occupancy_violation: -30.0`
- `src/engine/kernel.py` — `_run_initial_placement_check()` gains one new `SimulationEvent`-construction block (user-approved scope extension, plan.md Deviations)
- `docs/simulation_quality/quality_scoring_contract.md` — §5 event-types list, §5 Signal/Delta/Tag table row, §6 `SQ-24` scenario row
- `docs/simulation_quality/event_type_coverage.md` — §1.3 `_TRANSLATE_CONDITIONAL` row, Summary "scored" count 82→83, "Last updated" line
- `docs/parity_ledger/world_dynamics.yaml` — new `WORLD-113` entry (plan.md Revision 2)
- `tests/simulation_quality/test_quality_hub_event_translation.py` — `test_invariant_spawn_occupancy_law`, `test_invariant_spawn_occupancy_no_violation_no_translation`
- `tests/simulation_quality/test_world_dynamics_scorer.py` — `TestSpawnOccupancyViolation` class (4 tests)
- `tests/simulation_quality/test_traceability_path.py` — `_inject_spawn_occupancy_violation` helper + 2 new tests
- `staging_artifacts/TCK-20260716-PLACELEGAL-SIMQ-SIGNAL/plan.md` — Revision 2 added to Deviations section

## Completion Summary
All 6 plan steps implemented exactly as specified; the one implementation-time gap found (a missing
parity ledger entry, `investigation.md`-flagged but omitted from the approved plan's Step 3 scope)
was corrected and documented as plan.md Revision 2, not silently patched. `LAW-SPAWN-OCCUPANCY`
violations now flow end-to-end from `HardLawMonitor.check_initial_placement()` →
`Kernel._run_initial_placement_check()`'s new `SimulationEvent` emission →
`_translate_invariant()`'s new dispatch branch → `WorldDynamicsScorer`'s new
`spawn_occupancy_violation` signal (weight -30.0) → SimQ's WORLD DYNAMICS pillar, verified both via
hand-built envelope injection and via a real `Kernel` construction against the parent ticket's known
seed-42 collision. All scoped tests pass; the one failing test in the broader `tests/simulation_quality/`
suite is a pre-existing, unrelated environment issue (missing calibration fixture data), confirmed via
`git stash` to predate this ticket's diff. `data/runs/`, `reports/release_proof/`, and the two
transient `data/calibration/` report directories generated for the Step 6 check were cleaned up.
Ready to move to `tickets/done/` and migrate staging artifacts to `stored_artifacts/`.
