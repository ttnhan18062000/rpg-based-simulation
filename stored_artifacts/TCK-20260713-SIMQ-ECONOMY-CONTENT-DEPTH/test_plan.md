---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH
artifact_type: test_plan
tags: [simulation-quality, calibration, corpus]
---

# Test Plan — TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH

## Regression Surface

Existing tests that must keep passing, grouped by category. Scope mirrors
`TCK-20260710-SIMQ-DEPTH-SOCIAL`'s test surface (nearest precedent), narrowed/extended for
ECONOMY's specific event types and the 3 candidate worlds
(`frontier_living_world`, `frontier_extended`, `swamp_border_world`).

### Unit — SimQ scorer/weights layer
- `tests/simulation_quality/test_economy_scorer.py` — all classes (`TestHarvest`, `TestCrafting`,
  `TestTrade`, `TestGoldAndConservation`, `TestEcologyExclusion`, `TestMiscPositives`,
  `TestNullReturn`) must pass unmodified — this ticket does not change scorer logic, only world
  content volume.
- `tests/simulation_quality/test_timegate_penalties.py::TestEconomyTimegate` — zero_harvest/
  zero_crafting/zero_trade gate tests (thresholds 100/200/300 ticks) must still pass; new content
  must not accidentally suppress the zero-activity gates for worlds that still have none (not
  applicable to the 3 candidates, but must not regress the gate tests' own fixtures).
- `tests/simulation_quality/test_weights.py` — confirms `scoring_weights.yaml` still loads/parses;
  this ticket does not touch that file, so this is a pure regression guard.
- `tests/simulation_quality/test_report.py` — `normalized_score` formula stability; untouched by
  this ticket, guard against accidental drift.
- `tests/simulation_quality/test_accumulator.py`, `test_quality_hub_event_translation.py`,
  `test_quality_hub_integration.py`, `test_kernel_simq_integration.py` — event routing/translation
  layer; must remain unaffected by new world content (content flows through the same event path).

### Unit/Integration — economy engine (not touched, but exercised by new content)
- `tests/unit/economy/test_economy_health_monitor.py`, `test_economy_alerts.py`,
  `test_gold_sink.py` — `EconomyHealthMonitor`/Gini/gold-sink mechanics; not modified by this
  ticket, but new merchant population changes the Gini distribution the monitor samples — these
  tests guard that the *monitor logic* itself stays correct even as the population under test
  changes composition corpus-wide.
- `tests/unit/content/test_recipe_catalog_expansion.py` — the gather→craft recipe chain
  (`iron_ore → steel → ember_axe`) any new blacksmith/crafting activity in the 3 candidate worlds
  will exercise; not modified, but must stay green since new content depends on this substrate.
- `tests/unit/world/test_resource_ecology.py` — `RESOURCE_DEPLETED`/`RESOURCE_RECOVERED` event
  emission this ticket's new resource-node content (if any is added alongside merchant content)
  would exercise.
- `tests/integration/scenarios/test_macro_economy.py` — reputation discount / gold-sink integration
  scenarios; regression guard, not modified.

### World composition / compiler
- `tests/simulation_quality/test_scenario_coverage.py`, `test_calibrate_world_loading.py`,
  `test_evaluate_harness.py` — confirm the 3 edited `data/worlds/*/world.yaml` files still compile
  and calibrate correctly through the standard pipeline after adding `trading_company_hub` (or
  `merchant_caravan`, per Plan's final lever choice).
- `tests/simulation_quality/test_traceability_path.py` — full pipeline traceability; regression
  guard for the 3 touched worlds.
- Any `test_corpus_diversity.py`-style scale/composition guard (if it references entity/region
  counts for the 3 touched worlds) — new population additions change entity counts, so any hardcoded
  count assertion for these worlds must be updated deliberately, not left stale.

### Grade regression (anchors)
- `tests/simulation_quality/test_grade_regression.py` — `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS`
  parametrized sweep. Expected to **fail loudly** for the 3 touched worlds' ECONOMY column
  immediately after content is added and before `grade_anchors.json` is updated — this is the
  intended detection mechanism (mirrors `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s own Risk #5), not a
  bug. Must pass cleanly after the anchor update.

## New Tests Required

Per the ticket's Acceptance Criteria (ECONOMY moves off C in ≥2 worlds with calibration evidence;
0 regressions on a full sweep; a documented "fewer than 2-3 candidates" closure is equally valid):

1. **Test name:** `test_frontier_living_world_economy_activates` (or equivalent anchor-table
   entries, following the existing convention — this pillar's regression tests are anchor-driven,
   not bespoke assert-heavy unit tests, per the precedent in `TCK-20260710-SIMQ-DEPTH-SOCIAL`/
   `-FACTION`/`-INFORMATION`, none of which wrote new standalone test functions for their target
   worlds' pillar activation).
   **Category:** integration (grade-anchor regression).
   **Verifies:** `frontier_living_world`'s ECONOMY grade moves measurably off C (calibration_hits
   > 0 for `harvest_active`/`crafting_active`/`trade_active`) across a 3-seed matrix at whatever
   tick length the corpus's existing `frontier_living_world` anchors use (200t, per current
   `grade_anchors.json`).
   **Location:** `tests/simulation_quality/fixtures/grade_anchors.json` (new/updated ECONOMY value
   per existing `frontier_living_world_seed{42,123,456}_200t` keys) +
   `tests/simulation_quality/test_grade_regression.py`'s existing parametrized sweep (no new test
   function needed if these keys are already in `FAST_ANCHOR_KEYS`; confirm and add if not).

2. **Test name:** same shape for `frontier_extended` and `swamp_border_world` (or the final 2-3
   candidates Plan/Implement confirm).
   **Category:** integration (grade-anchor regression).
   **Verifies:** same as above, per world.
   **Location:** same files as above.

3. **Test name:** a corpus-diversity/module-composition assertion (new, if
   `tests/simulation_quality/test_corpus_diversity.py` or an equivalent architecture-guard test
   exists and tracks per-world module lists) confirming the 3 touched worlds now include
   `trading_company_hub` (or `merchant_caravan`) in their composition — guards against a future
   unrelated edit silently removing the newly-authored economy content.
   **Category:** architecture guard.
   **Verifies:** world composition content (not scorer behavior) — that the specific modules/
   populations this ticket adds remain present.
   **Location:** `tests/simulation_quality/test_scenario_coverage.py` or
   `tests/simulation_quality/test_corpus_diversity.py`, whichever already owns per-world
   composition assertions (confirm exact location during Plan; do not duplicate a mechanism if one
   already exists for FACTION/INFORMATION content and can be extended the same way).

4. **Test name:** a "stays C" zero-activity guard is **not needed as new test infrastructure** —
   `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s own Step 8 already confirmed 0 zero-event ECONOMY
   anchors need new coverage beyond what exists; this ticket only needs to confirm the *unchanged*
   worlds (everything except the 2-3 candidates) still show their pre-existing grades in the full
   sweep — covered by the Regression Surface section above, not a new test.

If Investigate/Plan finds fewer than 2 legitimate candidates survive a live probe (AC 3's explicit
escape valve), no new tests are required at all — the closure itself (documented in the ticket's
Completion Summary, with the probe evidence) satisfies the acceptance criteria per the ticket's own
text.

## Scoped Pytest Commands

```
# SimQ scorer/weights/report layer (must be unaffected by content-only changes)
pytest tests/simulation_quality/test_economy_scorer.py tests/simulation_quality/test_timegate_penalties.py::TestEconomyTimegate tests/simulation_quality/test_weights.py tests/simulation_quality/test_report.py -v

# Economy engine substrate the new content will exercise
pytest tests/unit/economy/ tests/unit/content/test_recipe_catalog_expansion.py tests/unit/world/test_resource_ecology.py tests/integration/scenarios/test_macro_economy.py -q

# World composition / compilation for the touched worlds
pytest tests/simulation_quality/test_scenario_coverage.py tests/simulation_quality/test_calibrate_world_loading.py tests/simulation_quality/test_evaluate_harness.py tests/simulation_quality/test_traceability_path.py -v

# Grade-anchor regression (expected to fail before the anchor update, pass after)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v
pytest tests/simulation_quality/test_grade_regression.py -m slow -v

# Full domain sweep — anti-drift guard, must run in full per the Testing Rule (never repo-wide)
pytest tests/simulation_quality/ -m "not slow" -v
pytest tests/simulation_quality/ -m slow -v

# Live-mode full-corpus sweep (AC "0 regressions" closure) — dry-run first per current_state.md's
# documented tooling-bug caveat (live mode's --profile forwarding bug affects only
# urban_political_selfmodel_probe_seed42_200t, not any of this ticket's candidates, but dry-run
# first is the documented-safe default)
python3 tools/evaluate_simq.py --dry-run
python3 tools/evaluate_simq.py
```

## Anti-Drift Test Guards

- **Byte-identical baseline check.** Before touching any world, re-confirm
  `dungeon_crawl_seed42_1000t` and `sandbox_world_seed42_1000t` still produce identical
  `raw_score=192.0/event_count=24` ECONOMY output (the generic `gold_sink_fired` baseline). If this
  baseline shifts for either world during this ticket's work, something leaked outside the 3 target
  worlds — stop and investigate before proceeding (mirrors `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s
  own "no unattributed diffs" discipline).
- **Shared-module non-leakage guard.** After editing the 3 candidate worlds' `data/worlds/*/
  world.yaml` files, diff `data/content/world_modules/frontier_village_core.yaml`,
  `settled_quarter.yaml`, and `old_mine_resource_loop.yaml` against their pre-ticket state — they
  must be byte-identical. Any diff there means content was authored at the wrong (module) level and
  will silently perturb every other world referencing that module (`urban_political`,
  `sandbox_world`, `generated_frontier_3_42`, and any others sharing it).
- **`urban_political` non-regression guard.** Explicitly re-run
  `pytest tests/simulation_quality/test_grade_regression.py -k urban_political` and confirm its
  ECONOMY anchors are untouched — it is Regression/baseline tier and not a target of this ticket;
  any diff here is an unattributed regression, not an intended improvement.
- **Cross-pillar attribution guard.** For each of the 3 touched worlds, the full sweep's NARRATIVE
  and PROGRESSION columns (the two pillars `TCK-20260710-SIMQ-DEPTH-SOCIAL` found move as a side
  effect of new content/population) must be individually reviewed: any grade shift must be
  attributed to specific new quest_definitions/XP-earning entities introduced by this ticket's
  content, documented in Implementation Notes — not silently folded into `grade_anchors.json` as an
  unexplained diff.
- **Stress/Unit/Regression tier-purity guard.** A diff-scope check before finalizing: `git diff
  --stat` must show changes only under `data/worlds/{frontier_living_world,frontier_extended,
  swamp_border_world}/world.yaml` (or the final confirmed candidate set) plus
  `tests/simulation_quality/fixtures/grade_anchors.json`, `docs/parity_ledger/*.yaml`,
  `docs/simulation_quality/{current_state.md,eval_matrix_results.md,corpus_tier_taxonomy.md}` — any
  change under `data/worlds/{crowded_frontier,resource_dense_basin,frontier_marches,unit_*,
  hero_guild_routing,simq_routing_test,urban_political}/` is out of scope and must be reverted
  before Finalize.
- **Gini/gold-sink interaction guard.** Explicitly compare each touched world's `gold_sink_fired`/
  `inflation_controlled` loop-flag count before vs. after the content addition (visible in each
  `quality_report.json`'s `loop_flags`) — if the generic baseline signal disappears or changes
  materially as a side effect of the new merchant population smoothing the Gini distribution, that
  must be documented as an attributed, understood effect (per Risk #3 in investigation.md), not
  silently absorbed.
