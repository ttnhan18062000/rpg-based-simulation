---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL
artifact_type: plan
tags: [simulation-quality, world, observability]
---

# Implementation Plan — TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL

## Summary

Add a `building_sabotaged` observability signal for the live `BuildingSabotageSystem.resolve()`
mutation and score it under the existing WORLD pillar. Per investigation.md, the emission site is
**not** `src/engine/sabotage.py`, despite the ticket's literal Scope wording — every comparable
WORLD-pillar sibling event (`region_trauma_delta`, `hazard_drain_applied`, etc.) is synthesized
post-hoc in `EventExtractor.extract()` by diffing the committed `StateUpdate`, and `sabotage.py` has
no event-emitter access at its call site. This plan routes the fix to
`src/observability/event_extractor.py` (new diff block reading `update.building_updates`,
discriminated by `hp_delta < 0`) and `src/simulation_quality/scorers/world_dynamics.py` (new scoring
branch), following the `TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS` structural template exactly: extractor
block → scorer branch → weights key → contract §5/§6 → event_type_coverage.md row → parity ledger
entry → tests → calibration. `BuildingSabotageSystem.resolve()`'s mutation logic, `src/town/sabotage.py`
(dead legacy path), and `src/engine/pipeline.py`'s phase wiring are untouched throughout.

Three non-blocking implementation-detail decisions from investigation.md are resolved here, not left
open: (1) delta polarity is **positive** (`+1`, matching `hazard_active`'s WORLD-consequence framing,
not a "damage = bad" framing); (2) a **new** §6 Scenario Registry row is added (not folded into
SQ-17); (3) `docs/simulation_quality/event_type_coverage.md` gets a new row per its own maintenance
contract. The parity ledger entry uses **WORLD-111** (the next free ID — WORLD-088 and WORLD-089
already exist in `docs/parity_ledger/world_dynamics.yaml` and cover unrelated mutation-level building
service/repair facts, confirmed by direct read of the file; do not reuse those IDs).

## Steps

### Step 1 — Add the `building_sabotaged` diff block to `EventExtractor.extract()`
**Files:** `src/observability/event_extractor.py`

**Change:** In the "World dynamics events — from StateUpdate world_updates and entities_add" section
(the `for rid, w_upd in (getattr(update, "world_updates", None) or {}).items():` loop area, around
line 855-895), add a **new, separate** loop over `update.building_updates` (do not nest inside the
`world_updates` loop — `building_updates` is keyed by building id, not region id):

```python
# World: building_sabotaged — building took sabotage damage (hp_delta < 0 discriminates
# BuildingSabotageSystem.resolve() from town_resolution.py's insolvency writes, which only
# ever set functional_set=False with no hp_delta)
for b_id, b_upd in (getattr(update, "building_updates", None) or {}).items():
    if getattr(b_upd, "hp_delta", 0.0) is not None and getattr(b_upd, "hp_delta", 0.0) < 0:
        _region = SpatialQueryService.get_building_region(current_state, b_id) if current_state else None
        events.append(SimulationEvent(
            event_type="building_sabotaged", event_category="region",
            tick=tick, entity_id=None, severity="WARNING",
            source_system="event_extractor", message="",
            payload={"building_id": b_id, "hp_delta": b_upd.hp_delta,
                     "region_id": _region.id if _region else None},
        ))
```

Place this new loop adjacent to the existing `world_updates` loop (same general "World dynamics
events" section) so it reads naturally as a sibling block, not interleaved with region-keyed logic.
Confirm `SpatialQueryService` is already imported in this file (it is used elsewhere in
`event_extractor.py` per investigation.md's region-attribution finding — if not already imported at
module level, add the import at the top alongside the other `src.engine` imports already present in
this file). Use `current_state` (the post-commit state, already a parameter of `extract()`) for the
region lookup, matching the two other `building_updates` writers' (`town_resolution.py`,
`conservation.py`) use of the same `SpatialQueryService.get_building_region(state, building_id)`
helper (`src/engine/spatial_query.py:239`).

**Do NOT touch:** the existing `world_updates` loop, `region_trauma_delta`/`threat_evolved`/
`region_ownership_changed`/`region_transformed` blocks, or any other event block in this file. Do not
add a `functional_set`-based branch — the discriminator is `hp_delta < 0` only, per investigation.md's
confirmed grep evidence that `hp_delta` is written exclusively by `sabotage.py` (negative) and never by
`town_resolution.py` (which only sets `functional_set`) or `conservation.py` (which never touches
`building_updates.hp_delta`).

**Verify:** `test_building_sabotaged_emitted_on_negative_hp_delta` and
`test_building_sabotaged_not_emitted_on_functional_only_update` (both new, in
`tests/unit/observability/test_event_extractor_world_dynamics.py`).

---

### Step 2 — Register `building_sabotaged` in `WorldDynamicsScorer.EVENT_TYPES` and add the scoring branch
**Files:** `src/simulation_quality/scorers/world_dynamics.py`

**Change:**
1. Add `"building_sabotaged"` to the `EVENT_TYPES` tuple (lines 17-32) — this **is** the registration
   step (no separate central enum; `QualityHub.__init__` auto-builds `SCORER_REGISTRY` from this
   tuple per investigation.md).
2. Add a new `if et == "building_sabotaged":` branch in `score()`. Mirror the `hazard_drain_applied`
   branch (lines 169-170) exactly in style — no conditional sub-logic needed (unlike
   `region_trauma_delta`'s `trauma_hazard_broken` check), since `hp_delta < 0` is already the full
   discriminator applied in Step 1:

```python
if et == "building_sabotaged":
    return _rec(self.weights["infrastructure_damaged"], "building took sabotage damage — real infrastructure consequence", ("infrastructure_damaged",))
```

Place it near the other single-line WORLD-positive branches (after `hazard_drain_applied`, before
`threat_evolved`'s `return None`).

**Do NOT touch:** `FactionScorer` or any other pillar scorer (§7.3 no-dual-ownership; the ticket's
Out of Scope explicitly forbids a FACTION rule for this event). Do not import
`SpatialQueryService`, `src.engine.sabotage`, or `src.core.state` into this file — the region lookup
already happened in Step 1's extractor block; this scorer only reads `payload.get("region_id")` via
the existing `_rec()` helper, exactly like every other WORLD branch.

**Verify:** `test_building_sabotaged_scored_by_world_dynamics`,
`test_building_sabotaged_registered_in_scorer_registry`, and `test_building_sabotaged_not_scored_by_faction`
(all new, in `tests/simulation_quality/test_world_dynamics_scorer.py` / `test_faction_scorer.py` per
test_plan.md).

**Dependency:** Step 2's test fixtures construct an `ObservabilityEventEnvelope` directly (no
dependency on Step 1's extractor code running) — Step 2 can be implemented and unit-tested
independently of Step 1, but Step 1 is what makes the signal real end-to-end (needed before Step 8's
calibration run and Step 6's integration tests).

---

### Step 3 — Add the `infrastructure_damaged` key to `scoring_weights.yaml`
**Files:** `config/simulation_quality/scoring_weights.yaml`

**Change:** Add one line to the `WORLD:` section (after `hazard_active: 1.0`, before the
`calamity_dormant` degenerate-tag block, to keep positive tags grouped before negative ones per the
file's existing ordering convention):

```yaml
  infrastructure_damaged: 1.0
```

Delta value rationale (recorded per investigation.md Risk #3 / this plan's Summary): **positive**,
`+1.0`, same magnitude as `hazard_active` — both signal "real infrastructure/environmental
consequence occurred," not narrative good/bad. Do not use a negative delta; WORLD's existing
degenerate tags (`calamity_dormant`, `world_static`, `world_depopulating`, etc.) all describe
*absence* of world activity, never "damage occurred."

**Do NOT touch:** any other pillar's section in this file, or any existing WORLD key's value.

**Verify:** `test_weights.py` (confirms `ScoringWeights` still loads/validates with the new key) and
transitively Step 2's `test_building_sabotaged_scored_by_world_dynamics` (asserts
`delta == scoring_weights["infrastructure_damaged"]`).

**Dependency:** Must land before or together with Step 2 — Step 2's scorer branch reads
`self.weights["infrastructure_damaged"]`, which raises `KeyError` if this key is missing (per
investigation.md: `ScoringWeights` fails loudly on unknown keys, no silent default).

---

### Step 4 — Update `docs/simulation_quality/quality_scoring_contract.md` §5 (WORLD section)
**Files:** `docs/simulation_quality/quality_scoring_contract.md`

**Change:** In the `### WORLD DYNAMICS` section (starts line 866):
1. Add `building_sabotaged` to the **"Event types scored"** list (currently ends
   `..., threat_evolved, node_recharged`) — append `, building_sabotaged`.
2. Add a new row to the **Signal table** (after the `Hazard drain applies damage in hazardous
   region | +1 | hazard_active` row, keeping positive signals grouped before the degenerate rows):

```
| Building takes sabotage damage (hp_delta < 0 on building_updates) | +1 | `infrastructure_damaged` |
```

**Do NOT touch:** the `**Pipeline:**` line's WD-01..WD-15 phase list (no new phase is being added —
this is an observability-layer addition, not a new pipeline phase), or any other pillar's section
(`FACTION`, `NARRATIVE`, etc.) in this file.

**Verify:** No automated test directly asserts doc prose; this step is verified by manual re-read
against §7.2 step 3/6 checklist compliance, and indirectly by Step 9's parity ledger entry citing this
section.

**Dependency:** Independent of Steps 1-3; can be done any time, but logically follows once the tag
name (`infrastructure_damaged`) and delta (`+1.0`) are finalized in Steps 2-3.

---

### Step 5 — Add a new row to §6 Scenario Registry
**Files:** `docs/simulation_quality/quality_scoring_contract.md`

**Change:** Add a new row to the `## 6. Scenario Registry` table (after the `SQ-22` row, following
the existing `SQ-NN` numbering convention — next free ID is `SQ-23`):

```
| SQ-23 | Does infrastructure sabotage register as a real-world consequence? | WORLD | — | `building_sabotaged` | Building damage is WORLD-owned per building-events-have-no-existing-pillar-owner (§7.3); do not duplicate in FACTION even though urban_political's sabotage framing is faction-conflict-adjacent |
```

This is a genuinely new scenario (infrastructure-damage-as-world-consequence), not a variant of SQ-17
("calamities, bosses, region transformations" — building sabotage is neither) or SQ-08/SQ-18
(ecology-specific) — per this plan's Summary decision, add as a new row rather than folding into an
existing one, matching the ticket's Scope item 3 explicit instruction ("Add a row to the contract's
§6 Scenario Registry for the new scenario").

**Do NOT touch:** any existing `SQ-NN` row's text, Primary/Secondary pillar, or Conflict Notes.

**Verify:** `test_scenario_coverage.py` — New Test 6 (`test_building_sabotaged_scenario_coverage` or
equivalent name matching the file's existing `test_sq*` naming pattern) asserting the new row's event
type reaches `WorldDynamicsScorer` with `PillarId.WORLD` and positive delta.

**Dependency:** Should land alongside Step 4 (both edit the same contract file); logically follows
Steps 1-3 (needs the finalized event/tag names).

---

### Step 6 — Add a coverage row to `docs/simulation_quality/event_type_coverage.md`
**Files:** `docs/simulation_quality/event_type_coverage.md`

**Change:** Add a new row to the `§1.1 Direct Emission — No Translation Required` table (same table
containing `hazard_drain_applied`, `node_recharged`, `threat_evolved`, etc., lines ~62-112), following
the exact column format `| event_type | source | scorer | calibration_hits | note |`:

```
| `building_sabotaged` | event_extractor | WorldDynamicsScorer | 0 | Emitted on hp_delta < 0 in building_updates (BuildingSabotageSystem.resolve()); 0 hits expected in all current calibration runs because no strategic/goal-selection/quest-reward code anywhere in src/ currently sets task_upd.work_kind_set="SABOTAGE" or payload_set["action"]="SABOTAGE" — confirmed via repo-wide grep (investigation.md Risk #1); this is a genuine engine emission path with no live producer yet, not a translation gap or missing-scorer gap. TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL. |
```

This is **not** a `no_engine_path`/`camp_constructed`-style entry — the engine (event_extractor) does
have a working emission path; the 0-hit count is because no upstream AI code ever triggers a SABOTAGE
intent, which is a different, more common pattern already represented by several existing 0-hit rows
in this same table (e.g. `paid_information_transaction`, `lead_certainty_updated`). Classify and word
it consistently with those precedents, not with `camp_constructed`.

Also update the `## Summary` counts near the top of the file (lines ~23-38) if this table maintains a
running total of scored/gap event types — check the current totals before editing and increment
whichever count `building_sabotaged` falls under (`scored`, per the classification table's
definition: "Event is emitted by the engine AND reaches the correct scorer(s)").

**Do NOT touch:** any other row in this table, or the `camp_constructed` / §3.9 entry (unrelated,
different classification).

**Verify:** No dedicated test for this doc; verified by manual cross-check against Step 1/2's actual
implementation and Step 8's calibration result.

**Dependency:** Should land after Step 1 and Step 2 (needs the actual emission/scoring behavior
confirmed) and ideally after Step 8's calibration run (to state the 0-hit count with confidence, though
investigation.md's grep evidence already makes this the expected, pre-known outcome).

---

### Step 7 — Add unit tests
**Files:**
- `tests/unit/observability/test_event_extractor_world_dynamics.py`
- `tests/simulation_quality/test_world_dynamics_scorer.py`
- `tests/simulation_quality/test_faction_scorer.py` (or as a class method in
  `test_world_dynamics_scorer.py`, matching the `TestEcologyOwnership.test_ecology_not_in_economy_scorer`
  precedent — implementer's choice, per test_plan.md's stated flexibility)
- `tests/simulation_quality/test_scenario_coverage.py`

**Change:** Implement the five new tests specified in `test_plan.md`'s "New Tests Required" section
(items 1-6; item 7 is the calibration run, covered in Step 8):
1. `test_building_sabotaged_emitted_on_negative_hp_delta` — mirrors the file's existing
   `_state`/`_update`/`_world_upd` `MagicMock` fixture style used for `region_trauma_delta` coverage;
   construct a `MagicMock` `BuildingUpdate` with `hp_delta=-50`, assert `extract()` produces a
   `SimulationEvent(event_type="building_sabotaged", ...)` with `payload["building_id"]` and
   `payload["region_id"]` populated (mock `SpatialQueryService.get_building_region` at the state level
   per the file's existing convention).
2. `test_building_sabotaged_not_emitted_on_functional_only_update` — `BuildingUpdate` with
   `functional_set=False, hp_delta=0` (or unset) must **not** produce a `building_sabotaged` event.
3. `test_building_sabotaged_scored_by_world_dynamics` — new `TestBuildingSabotage` class in
   `test_world_dynamics_scorer.py`, mirrors `TestStructureAndHazard`; asserts
   `delta == scoring_weights["infrastructure_damaged"]` and `pillar == PillarId.WORLD` using the
   session-scoped `scoring_weights` fixture from `tests/simulation_quality/conftest.py` (real
   `config/simulation_quality/*.yaml`, per the repo's established "inject `ScoringWeights` fixture"
   convention — do not hand-type example numbers).
4. `test_building_sabotaged_not_scored_by_faction` — asserts `FactionScorer.score()` returns `None`
   for a `building_sabotaged` envelope and `"building_sabotaged" not in FactionScorer.EVENT_TYPES`.
5. `test_building_sabotaged_registered_in_scorer_registry` — asserts
   `"building_sabotaged" in WorldDynamicsScorer.EVENT_TYPES`.
6. Scenario coverage test for the new SQ-23 row in `test_scenario_coverage.py`, matching the file's
   existing `test_sq*` pattern.

**Do NOT touch:** `tests/unit/world/test_building_sabotage.py` (dead `SabotageAction` legacy-path
tests — run only to confirm untouched, per test_plan.md).

**Verify:** All six tests pass; full scoped run:
```bash
python3 -m pytest tests/unit/observability/test_event_extractor_world_dynamics.py \
  tests/unit/observability/test_event_extractor_world.py \
  tests/unit/observability/test_event_extractor_simq.py \
  tests/simulation_quality/test_world_dynamics_scorer.py \
  tests/simulation_quality/test_faction_scorer.py \
  tests/simulation_quality/test_weights.py \
  tests/simulation_quality/test_quality_hub_integration.py \
  tests/simulation_quality/test_quality_hub_event_translation.py \
  tests/simulation_quality/test_scenario_coverage.py \
  tests/simulation_quality/test_kernel_simq_integration.py \
  tests/integration/pipeline/test_strategic_cadence.py \
  tests/integrity/test_logic_guards.py \
  tests/unit/world/test_building_sabotage.py \
  tests/simulation_quality/test_performance.py -v
```

**Dependency:** Requires Steps 1, 2, 3 complete (implementation must exist before tests can pass);
requires Step 5 (SQ-23 row) for test 6.

---

### Step 8 — Run before/after calibration comparison in `urban_political`
**Files:** none changed (verification-only step); output feeds Step 6's coverage-doc note and the
ticket's `Test Summary`/`Completion Summary` sections.

**Change:** Run `python3 tools/calibrate_simq.py --name urban_political --seed 42 --ticks <T>` (use
the same tick count as existing `urban_political_*` calibration artifacts referenced in
`event_type_coverage.md`, e.g. 500t) before and after Steps 1-3 land. Inspect
`quality_scores.jsonl`/`quality_report.json` for `building_sabotaged` hit count and any WORLD
grade delta. Per investigation.md Risk #1 (repo-wide grep confirms no `SABOTAGE`-intent producer
exists anywhere in `src/`), the expected, pre-authorized outcome is **zero hits and no grade change**
— document this plainly in the ticket's Completion Summary, citing the grep evidence, rather than
treating it as a surprise or investigating further (out of scope: authoring a SABOTAGE-intent producer
is not part of this ticket).

**Do NOT touch:** do not add synthetic/artificial triggers to force a non-zero hit count — an honest
null result is the acceptance criterion, not a required grade change (ticket Scope item 5, AC item 5).

**Verify:** AC item 5 (documented before/after comparison, honest result either way).

**Dependency:** Requires Steps 1-3 complete (the actual code must exist to calibrate against).

---

### Step 9 — Add parity ledger entry `WORLD-111`
**Files:** `docs/parity_ledger/world_dynamics.yaml`

**Change:** Append a new entry after the last existing entry (`WORLD-110`, ends at file line 1351).
**Do not reuse `WORLD-088` or `WORLD-089`** — both already exist in this file (confirmed by direct
read) and cover unrelated mutation-level facts ("Building damage affects service availability if
supported" / "Building repair restores service availability if supported"), not this ticket's
observability behavior. Use **`WORLD-111`** (next free ID after `WORLD-110`):

```yaml
- id: WORLD-111
  text: Building sabotage emits a scored building_sabotaged WORLD-pillar observability signal.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: "EventExtractor.extract() building_updates diff block (hp_delta < 0) + WorldDynamicsScorer infrastructure_damaged branch; TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL"
  proof_type: parity
  test_path: tests/simulation_quality/test_world_dynamics_scorer.py::TestBuildingSabotage::test_building_sabotaged_scored_by_world_dynamics
  divergence_note: null
  support_boundary: null
```

Priority is **P2**, not P0 — this is a lower-priority observability signal, not a hard mutation law
(`WORLD-087` already covers the mutation itself at P0 and is unaffected by this ticket). Use a real
`test_path` (not `null`), matching investigation.md's explicit recommendation to not perpetuate the
`P0`-with-`test_path:null` pattern seen in `COMB-068/069/070` for this ticket's own new entry.

**Do NOT touch:** `WORLD-087`, `WORLD-088`, `WORLD-089`, or any other existing entry in this file.

**Verify:** Entry references a real, passing test (confirmed in Step 7).

**Dependency:** Must land after Step 7 (needs the real test path to exist and pass).

---

### Step 10 — Full scoped regression + corpus dry-run
**Files:** none changed (verification-only).

**Change:** Run the full scoped test sweep and corpus check from test_plan.md:
```bash
python3 -m pytest tests/simulation_quality/ tests/unit/observability/ -m "not slow"
make evaluate --dry-run
```
Confirm 0 regressions. If `make evaluate --dry-run` flags a genuine anchor drift in
`tests/simulation_quality/fixtures/grade_anchors.json` for `urban_political` (or any other calibrated
world) caused by the new WORLD branch, update the anchor only if the drift is confirmed real (not
speculative) — per investigation.md's anti-drift hazard note.

**Do NOT touch:** grade anchors for worlds unrelated to this change, or anchors reflecting a
speculative/untriggered regression.

**Verify:** AC item 6 (`make evaluate --dry-run` confirms 0 regressions on the rest of the corpus).

**Dependency:** Final step; requires all prior steps complete.

## Scope Guards

- Do not modify `BuildingSabotageSystem.resolve()`'s mutation logic in `src/engine/sabotage.py` —
  `damage = 50` constant, Chebyshev proximity check, `functional_set` logic, and rejection codes are
  all out of scope. No import from `src.observability` should be added to `sabotage.py`.
- Do not modify `src/engine/pipeline.py`'s phase call site or ordering for `building_sabotage` —
  `tests/integrity/test_logic_guards.py` asserts this via source-position string checks; any diff to
  it is a signal the change landed in the wrong layer.
- Do not touch `src/town/sabotage.py::SabotageAction` (dead legacy path, different formula —
  Euclidean `<5.0`, damage = entity ATK — unwired, test-only reference) or its test,
  `tests/unit/world/test_building_sabotage.py`.
- Do not modify `docs/simulation/town_contract.md`'s "Sabotage Pipeline" section (documents the dead
  `SabotageAction` path) or `docs/systems/world_evolution_and_resilience.md` §2 "Building Durability &
  Sabotage" (documents a third, non-matching design). Both are pre-existing doc/code drift, explicitly
  out of scope per investigation.md — anchor strictly to `src/engine/sabotage.py` for all
  payload/formula details.
- Do not add a scoring rule for `building_sabotaged` to `FactionScorer` or any pillar other than
  `WorldDynamicsScorer`, even as a "secondary" — §7.3 no-dual-ownership, explicit Out of Scope item.
- Do not create an 11th top-level pillar or modify `PillarId`/`PILLAR_METADATA`.
- Do not add numeric literals directly in `world_dynamics.py`'s scorer branch — the delta value lives
  only in `scoring_weights.yaml`, read via `self.weights["infrastructure_damaged"]`.
- Do not reuse `WORLD-087`, `WORLD-088`, or `WORLD-089` parity ledger IDs — all three already exist
  and cover different (unaffected) facts. Use `WORLD-111`.
- Do not author new sabotage-relevant content in any world beyond what already exists in
  `urban_political`/`trading_company_hub.yaml`, and do not add a synthetic SABOTAGE-intent producer to
  force a non-zero calibration hit count.
- Do not import `SpatialQueryService`, `src.engine.sabotage`, or any engine-internal module into
  `src/simulation_quality/scorers/world_dynamics.py` — the region lookup belongs exclusively in
  `event_extractor.py` (§2 Coupling Law).

## Dependency Map

- Step 3 (weights key) must land before or with Step 2 (scorer branch reads the key; `KeyError` if
  missing).
- Step 2 and Step 1 are independently unit-testable but both are needed for Step 7's full suite and
  Step 8's live calibration.
- Step 4 and Step 5 (contract doc edits) logically follow Steps 1-3 (need finalized names) but do not
  block them technically — can be written in parallel once names are decided (they are decided in
  this plan already: `building_sabotaged`, `infrastructure_damaged`, `+1.0`, `SQ-23`).
- Step 6 (coverage doc) should land after Steps 1-2 (needs confirmed behavior) and ideally after
  Step 8 (needs the confirmed 0-hit count, though this is already the expected outcome per
  investigation.md).
- Step 7 (tests) requires Steps 1, 2, 3 (and Step 5 for the scenario-coverage test) complete.
- Step 9 (parity ledger) requires Step 7 (needs a real, passing `test_path`).
- Step 10 (final regression + dry-run) requires all prior steps.
- All steps are otherwise independent of each other's file edits (no two steps touch the same file
  except Steps 4 and 5, both editing `quality_scoring_contract.md` in different sections).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `BuildingSabotageSystem.resolve()` emits a `building_sabotaged` event, registered in the observability event-type system | Steps 1, 2 (routed to `EventExtractor.extract()` + `WorldDynamicsScorer.EVENT_TYPES`, per investigation.md's emission-site finding, not a direct call in `sabotage.py`) | `test_building_sabotaged_emitted_on_negative_hp_delta`, `test_building_sabotaged_registered_in_scorer_registry` |
| New WORLD-pillar scoring rule consumes this event, delta sourced from `scoring_weights.yaml`, no numeric literals in scorer code | Steps 2, 3 | `test_building_sabotaged_scored_by_world_dynamics`, `test_weights.py` |
| `quality_scoring_contract.md` §5 and §6 updated per §7.2 protocol | Steps 4, 5 | manual review; `test_scenario_coverage.py` (SQ-23) |
| Unit test for the new scoring rule, using an injected `ScoringWeights` fixture | Step 7 | `test_building_sabotaged_scored_by_world_dynamics` (session-scoped `scoring_weights` fixture) |
| Before/after calibration comparison in `urban_political`, honest documentation of the result | Step 8 | manual calibration run; documented in ticket Completion Summary |
| `make evaluate --dry-run` confirms 0 regressions on the rest of the corpus | Step 10 | `make evaluate --dry-run` output |

## Anti-Drift Notes

- The single highest-value anti-drift test is `test_building_sabotaged_not_scored_by_faction` (Step
  7) — the ticket text itself flags FACTION as a "plausible" temptation given `urban_political`'s
  faction-conflict framing; this test guards against that regression directly.
- `test_building_sabotaged_not_emitted_on_functional_only_update` (Step 7) guards against a
  broader-than-intended `building_updates` diff conflating `town_resolution.py`'s insolvency writes
  (`functional_set=False`, no `hp_delta`) with actual sabotage — a correctness bug, not just a scope
  violation, if missed.
- `tests/integrity/test_logic_guards.py` must show zero diff after this ticket — any change to it
  signals the fix landed in `pipeline.py` instead of `event_extractor.py`, contradicting
  investigation.md's core finding.
- Expect a **zero-hit** calibration result in Step 8 (investigation.md Risk #1: no `SABOTAGE`-intent
  producer exists anywhere in `src/` outside the consumer/legality-gate/unrelated-comment hits already
  enumerated). This is the expected, pre-authorized outcome — do not treat it as an implementation bug
  or attempt to manufacture a non-zero result.
- `WORLD-088` and `WORLD-089` in `docs/parity_ledger/world_dynamics.yaml` are pre-existing entries
  with similar-sounding text ("Building damage affects service availability...") but cover a different
  fact (mutation-level service availability, P0) than this ticket's new entry (observability emission,
  P2). Confirmed by direct file read during planning — do not confuse or overwrite either.
- Two same-subsystem-named test files exist: `tests/unit/world/test_building_sabotage.py` (dead
  `SabotageAction` path — irrelevant to this ticket) vs. the actual target files under
  `tests/unit/observability/` and `tests/simulation_quality/`. Do not add coverage to the former.

## Open Questions Status

All resolved — none outstanding. All three non-blocking questions flagged in investigation.md (delta
polarity, new vs. folded scenario registry row, event_type_coverage.md companion update) are
implementation-detail choices within the ticket's existing scope and are resolved directly in this
plan (Steps 2/3, 5, 6 respectively) — none require escalation to a human stakeholder.

## Deviations

- **Step 1 import placement:** the plan's fallback instruction was "add the import at the top
  alongside the other `src.engine` imports already present in this file" if `SpatialQueryService`
  wasn't already imported. On implementation, `event_extractor.py` had **no** existing `src.engine`
  imports at module level to add alongside (only `src.core`, `src.domains`, `src.observability`,
  `src.systems`). Rather than introduce a new module-level `src.observability` → `src.engine`
  coupling point, the import was placed as a local `from src.engine.spatial_query import
  SpatialQueryService` inside the new diff block — matching the identical local-import convention
  already used by both other `building_updates` writers, `town_resolution.py` and `sabotage.py`,
  for the same `get_building_region` lookup. Behaviorally equivalent; chosen for consistency with
  existing precedent rather than the plan's literal fallback wording.
