---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP
artifact_type: test_plan
tags: [simulation-quality, world, adventure, bug]
---

# Test Plan: TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP

## Scope of testing

Verify: (1) the catalog fix makes `hometown` a valid gating region for at least one resource kind
present in `simq_routing_test`/`urban_political`; (2) a hero spawned in `hometown` with
`sociability < 0.2` and no active needs/weaknesses now gets a `gather_resource` candidate route
every tick instead of being permanently stuck on `defer_with_reason`; (3) no regression to any
other world/region that currently relies on the untouched tags (`near_forest`, `moon_cave`,
`old_mine`, etc.); (4) `simq_routing_test` seed42/123/456 calibrations re-run clean, with seed456's
AGENCY grade/anchor re-verified against the new expected outcome.

## Normal flow

1. **Unit — catalog projection.** Re-run the live adapter check (as done during investigation):
   `CatalogRepository("data/content").load_all()` →
   `CatalogToResourceRegistryAdapter.adapt()` → assert `resources["wood_node"].source_region_tags`
   (and/or `resources["herb_patch"].source_region_tags`, per whichever kind(s) Implementation
   chooses) now includes `"hometown"`, **and** still includes the pre-existing tags
   (`"near_forest"` for wood_node; `"near_forest"`, `"moon_cave"` for herb_patch) — i.e. additive,
   not replaced.
2. **Unit — `ResourceOpportunityProvider` in `hometown`.** New test in
   `tests/unit/strategic/test_opportunities.py` (or a new test module) mirroring
   `test_resource_opportunities_basic`'s pattern: build an entity with
   `navigation.region_id = "hometown"`, construct a `ResourceNodeState` with
   `kind="wood_node"` (or `herb_patch`), call `ResourceOpportunityProvider.get_opportunities()`,
   assert the returned list is non-empty and contains a `gather_resource` opportunity for that
   node's kind. This is the direct unit-level proof the gating bug is fixed, independent of full
   calibration.
3. **Integration — world compile.** Compile `simq_routing_test` (`WorldCompiler.compile()`) for
   all 3 shipped seeds (42, 123, 456) and confirm: 5 resource nodes still present (no count
   regression), and — via the fixed `ResourceRegistry` — a hero entity placed in `hometown`
   receives at least one non-empty opportunity list from `ResourceOpportunityProvider`.
4. **End-to-end — calibration re-run.** Re-run
   `ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed {42,123,456}
   --name simq_routing_test` for all 3 seeds (clearing `data/calibration/simq_routing_test_seed*_500t/`
   first per the known append-mode footgun documented in the AGENCY-STASIS-COLLAPSE investigation).
   Confirm:
   - seed42/123: AGENCY grade stays `A` (no regression) — these seeds never relied on the
     `hometown` fallback since entity 23's sociability already clears the `FORM_PARTY` gate in
     both.
   - seed456: entity 23's `decision_trace.jsonl` no longer shows `defer_with_reason` at every
     tick — it should now show `gather_resource` (or a mix) for at least a meaningful fraction of
     the run. Confirm the resulting AGENCY grade (whatever it computes to, expected to improve
     from `D`) and update `tests/simulation_quality/fixtures/grade_anchors.json`'s
     `simq_routing_test_seed456_500t.AGENCY` entry accordingly (ticket AC5).

## Edge cases

- **Node depletion.** If the fix targets only one kind (e.g. `wood_node`, 8 charges) and that
  node's charges are exhausted mid-run, confirm the *other* hometown-placed kind (`herb_patch`, if
  also fixed) still provides a fallback — this is the reasoning for fixing both kinds rather than
  one, but should be explicitly verified if Implementation chooses the single-kind minimal fix
  instead: does entity 23 (or any hero) fall back to `defer_with_reason` again once the sole fixed
  node's charges hit 0 mid-run? If so, that's an acceptable-but-should-be-documented residual risk,
  not a test failure per se (matches "legitimate stasis" framing from the AGENCY-STASIS-COLLAPSE
  ticket), but Implementation Notes should call it out.
- **Multiple hometown-spawned heroes simultaneously.** Confirm all 3 heroes in `hometown` (not just
  entity 23) can independently receive `gather_resource` opportunities without one exhausting the
  node for the others prematurely within a 500-tick run (charge counts: 8 for wood, 5 for herb —
  low charges could interact with `regen_rate: 1`; confirm regen keeps nodes viable long-run).
- **`urban_political` side effect.** Since the fix is at the shared catalog level, confirm
  (read-only check, not a new shipped calibration profile) that `urban_political`'s 3 hero
  entities in `hometown` would also now receive a `gather_resource` opportunity if
  `ENABLE_ADVENTURE_ROUTING` were enabled for that world — a quick unit-level check (entity in
  `hometown`, real `ResourceRegistry` state) suffices; do not add a new shipped
  `ENABLE_ADVENTURE_ROUTING=ON` calibration profile for `urban_political` as part of this ticket
  (out of scope).

## Failure modes / regression guards

- **Subset regression check.** Re-run `tests/unit/core/test_registry_parity.py::test_production_catalog_parity`
  and `tests/unit/core/test_registry_bridge.py` in full — both directly assert against the real
  catalog file being changed; both are expected to still pass (see investigation.md §6 for exact
  reasoning on why the additive-only edit preserves their assertions).
- **Adapter heuristic reporting.** Re-run `tests/unit/content/test_adapter_heuristic_reporting.py`
  — uses synthetic fixtures, expected unaffected, but re-run as a smoke check since it exercises
  the same adapter code path being relied upon.
- **Cross-world non-regression.** Re-run (or at minimum re-compile and inspect resource_node
  counts/opportunity behavior for) any world that places `wood_node`/`herb_patch` in `near_forest`
  or `moon_cave` (`frontier_extended`, `frontier_living_world`, `generated_frontier_3_42`,
  `sandbox_world`, `swamp_border_world`, `wilderness_survival`) to confirm those regions' existing
  opportunity behavior is unchanged (tags are additive, so this should be a no-op, but verify via
  `tests/integration/worldassembly/test_real_content_world_compositions.py` and
  `tests/integration/worldassembly/test_e2e_smoke.py`).
- **`grade_anchors.json` schema.** `GRADE_ORDER` (`tests/simulation_quality/test_grade_regression.py:34`)
  has no `F` slot — if seed456's grade lands anywhere at or above `D`, the anchor update is a
  normal value edit; if it somehow remains `F` (unexpected — the fix should prevent the zero-route
  condition entirely), that would itself be a surprising result worth investigating further before
  editing the anchor, not silently overwritten.

## Tests expected to need no changes (smoke/regression re-run only)

`tests/unit/strategic/test_opportunities.py` (existing tests use `near_forest`/`old_mine`, not
`hometown`), `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`,
`tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`,
`tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py`,
`tests/unit/domains/adventure/test_phase3_adventure_decision_service.py`,
`tests/perf/test_phase3_adventure_decision_budget.py` (decision logic itself is not touched by this
ticket — confirmed correct and out of scope per the ticket's own Out of Scope section).

## Test commands (scoped, not full suite, per repo Testing Rule)

```
pytest tests/unit/strategic/test_opportunities.py -v
pytest tests/unit/core/test_registry_bridge.py tests/unit/core/test_registry_parity.py -v
pytest tests/unit/content/test_adapter_heuristic_reporting.py -v
pytest tests/integration/content/test_registry_projection_parity.py -v
pytest tests/integration/worldassembly/test_e2e_smoke.py -v
pytest tests/simulation_quality/test_grade_regression.py -v
```
Plus the manual calibration re-runs described under "End-to-end" above (not part of `pytest`,
per `tools/calibrate_simq.py`).
