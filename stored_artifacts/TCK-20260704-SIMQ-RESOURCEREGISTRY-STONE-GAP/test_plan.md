---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP
artifact_type: test_plan
tags: [simulation_quality, world, ecology, resource-registry, bug]
---

# Test Plan — TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP

## Existing Coverage (must not break)

`tests/unit/world/test_resource_ecology.py` (25 tests) — covers `ResourceEcologyService`'s regen
loop only: `RESOURCE_DEPLETED`/`RESOURCE_RECOVERED` event emission, regen-per-tick accounting,
density-modifier math (`DENSITY_CAP`/`DENSITY_FLOOR`), ecology-interval gating. **None of these 25
tests exercise the dynamic node-seeding branch** (`process_ecology` lines 98-144, the
`region.kind`-based `kind` selection). The one node used across this file is a hand-built
`ResourceNodeState(kind="WOOD", ...)` fixture (line 27), never round-tripped through the actual
`FOREST`/`MOUNTAIN`/else selection logic.

`tests/unit/core/test_engine_integrity.py` — has one test that calls
`ResourceEcologyService.process_ecology(state_eco, generator)` and asserts a node was added
(`nodes_add`), but if the RNG roll doesn't naturally trigger a spawn it **manually substitutes** a
hardcoded `kind="WOOD"` node (lines 127-140) rather than exercising the real branch — so it does
not assert anything about `kind` correctness either, and passes regardless of what
`process_ecology` actually emits.

`tests/integration/scenarios/test_resource_depletion.py` — depletion/harvest scenario tests;
confirmed (via `graphify query` context and file read) unrelated to the seeding path.

**Conclusion: zero existing tests would have caught this bug.** All 25+ ecology tests and the
engine-integrity test must continue passing unmodified after the fix (they test unrelated regen/
density/depletion behavior) — run as a regression gate, not because they cover this bug.

## New Tests Required (Acceptance Criteria #5)

### 1. Unit: generator never emits an unregistered `kind`

Add to `tests/unit/world/test_resource_ecology.py` (or a new
`tests/unit/world/test_resource_ecology_seeding.py` if seeding tests warrant their own module):

- `test_seeded_node_kind_is_registered_in_resource_registry` — force a region of kind `FOREST`
  through `process_ecology` (deterministic seed/rng roll that guarantees the 50% seed-chance
  branch fires, or directly unit-test the kind-selection logic if it's extracted to a helper),
  assert the resulting `nodes_add[i].kind` satisfies `ResourceRegistry.contains(kind)`.
- Repeat for `MOUNTAIN` region kind.
- Repeat for a third, "other" region kind (e.g. `TOWN` or a synthetic kind not `FOREST`/`MOUNTAIN`)
  to cover the `else` branch specifically — this is the exact branch that produced `STONE`.
- Assert `ResourceRegistry.get(node.kind).yield_item` matches the `yields_item` set on the created
  `ResourceNodeState` (guards against the `yields_item` derivation drifting from the registry again,
  per the coupled-literal issue noted in investigation.md).

### 2. Regression: exact reproduction case

- `test_process_ecology_never_produces_unregistered_kind_across_all_region_kinds` — parametrize
  over every region `kind` value used anywhere in the engine (`FOREST`, `MOUNTAIN`, `TOWN`, and at
  least one arbitrary/unknown kind to prove the fallback path specifically is fixed), run
  `process_ecology` enough times (varying tick/seed) to force both the "seed chance" RNG branch and
  RNG-miss branch, and assert `ResourceRegistry.contains(kind)` holds for every node in
  `nodes_add` in every case. This directly targets the reported crash (`STONE` from the `else`
  branch) plus the two latent siblings (`WOOD`, `IRON`) identified in the investigation.

### 3. Integration: `ResourceOpportunityProvider` no longer crashes on ecology-seeded nodes

- Add/extend a test in `tests/unit/world/providers/` (or alongside
  `src/world/providers/resources.py`'s existing tests, if any — confirm location during
  implementation) that builds a state with a `resource_nodes` entry whose `kind` is set to the
  post-fix ecology-seeded value(s) and calls
  `ResourceOpportunityProvider.get_opportunities(hero, state)` directly, asserting no `KeyError` is
  raised and (if applicable) an `Opportunity` is returned. This is a defense-in-depth regression
  test independent of the generator fix — it protects `resources.py:60` even if a future change to
  ecology.py reintroduces a bad `kind`. Consider also adding the `contains()` guard at
  `resources.py:60` itself (matching `guild.py`'s and `action_intent.py`'s existing pattern) as
  defense-in-depth, since it is the one unguarded call site in the codebase — decide during
  implementation whether this belongs in this ticket's scope (it directly prevents recurrence of
  the *crash*, distinct from fixing the *root emission*) or is redundant once the generator no
  longer emits bad kinds. Recommend including it: cheap, consistent with the two existing sibling
  call sites, and closes the "some future consumer forgets the guard" risk the same way
  `guild.py`'s comment already documents as a known hazard class.

### 4. End-to-end: calibration reproduction no longer crashes

Not a pytest test, but a required manual verification step per the ticket's Acceptance Criteria:

```bash
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 42  --name simq_routing_test
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 123 --name simq_routing_test
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 456 --name simq_routing_test
```

All three must run to completion (confirmed currently reproducing the exact `KeyError: 'Resource
not found in ResourceRegistry: STONE'` crash on seed 42 before the fix — see investigation.md).
After the fix, diff the resulting `quality_report.json`'s 10 pillar grades for each of the 3
`run_key`s against the currently-committed `grade_anchors.json` entries
(`simq_routing_test_seed{42,123,456}_500t`). If any grade shifted, update `grade_anchors.json` in
place for that key only, with an attribution note following the precedent in
`docs/simulation_quality/eval_matrix_results.md` (same pattern used for the D2 formula fix and for
`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s Step 4a) — attribute to "STONE/WOOD/IRON kind-emission
fix in `ecology.py`," not an unexplained regression.

## Failure Modes / Edge Cases To Cover

- RNG seed-chance roll (`< 0.5` check at ecology.py:122) both fires and doesn't fire — the fix must
  not change this probabilistic gating, only the `kind` chosen when it does fire.
- A region kind that is neither `FOREST` nor `MOUNTAIN` (the exact branch that broke) — must be
  explicitly exercised, not just assumed fixed by symmetry with the other two branches.
- `ResourceRegistry` in an empty/unbootstrapped state (e.g. a unit test that doesn't call
  `seed_phase1_content()` first) — decide whether `process_ecology` should degrade gracefully
  (skip seeding) or is expected to always run after bootstrap in practice; existing tests already
  assume registries are bootstrapped module-wide, so match that convention rather than inventing a
  new one.

## Non-Goals For This Test Plan

- Not re-testing `guild.py`'s or `action_intent.py`'s existing `contains()`-guarded call sites —
  they are already correct and unaffected by this fix.
- Not testing the full `simq_routing_test` calibration/grading pipeline end-to-end in the unit
  suite — that is covered by the manual calibration re-run (#4 above) and the existing
  `test_grade_regression.py` anchor tests, which already run as part of standard CI and will
  exercise the updated anchors once `grade_anchors.json` is refreshed.
