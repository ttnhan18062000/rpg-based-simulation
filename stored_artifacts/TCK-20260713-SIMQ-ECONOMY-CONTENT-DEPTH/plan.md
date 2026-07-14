---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH
artifact_type: plan
tags: [simulation-quality, calibration, corpus]
---

# Implementation Plan — TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH

## Summary

Author real harvest/craft/trade volume into 3 candidate worlds — `frontier_living_world`,
`frontier_extended`, `swamp_border_world` — by composing the already-proven, already-tested
`trading_company_hub` module (currently used only by `urban_political`, the corpus's one ECONOMY=A
reference case) into each world's composition, at the module's own default `merchant_count: 3`
first, escalating per-world only where a live calibration run shows the default is insufficient to
move the grade off C, and only within each world's own `test_corpus_diversity.py`
`ANCHORED_WORLD_BANDS` entity-count ceiling. This plan makes one concrete correction to
`investigation.md`'s framing, verified directly against source during planning: adding
`trading_company_hub` to any of these 3 worlds is **not possible via the plain `modules: [...]`
list** at all, regardless of whether a non-default `merchant_count` is wanted. Both
`frontier_village_core.yaml` (already present in all 3 worlds) and `trading_company_hub.yaml`
declare a region with the identical id `"hometown"`, and `src/worldassembly/resolver.py` L346-347
raises `ValueError("Duplicate region ID collision ...")` on any unnamespaced merge of two modules
sharing a region id. `urban_political`'s own composition already works around this with
`namespace: "trading"` on its `trading_company_hub` `module_refs:` entry — this plan applies the
identical, already-proven workaround to all 3 candidates. The `modules:` → `module_refs:` format
migration is therefore mandatory infrastructure for this ticket, not an optional lever tied to a
parameter-override decision as `investigation.md` Risk 6 framed it.

A second finding from direct verification during planning: `traveling_merchant`'s faction is
already `merchant_league` (`data/content/entities/entity_archetypes.yaml` L126), and
`frontier_village_population` (already present in all 3 worlds via `frontier_village_core`) already
includes 1 `traveling_merchant`. This means `merchant_league` is already a *populated* faction in
all 3 worlds today — adding `trading_company_hub`'s own `merchant_league`-faction population does
**not** introduce a new distinct populated faction. `tests/unit/worldassembly/
test_corpus_diversity.py::test_distinct_populated_factions`'s existing per-world constants (6/9/4)
are expected to stay unchanged; this must be confirmed by recompiling, not assumed, but no edit to
that dict is anticipated.

`merchant_caravan` (the unused population identified in investigation.md) is **not used** by this
plan — `trading_company_hub` is a fully self-contained, already-tested, already-anchored lever
(its own population, buildings, resource nodes, and quest content) that requires zero new module
authoring, whereas `merchant_caravan` would still need a full new population-addition mechanism
proven out. It remains a viable, cheaper lever for a possible future `highland_traverse`-specific
ticket, explicitly out of scope here.

## Resolution of Open Questions (from investigation.md Risks 1, 2, 5 and the task's own open questions)

1. **Candidate count and lever, resolved:** 3 worlds — `frontier_living_world`, `frontier_extended`,
   `swamp_border_world` — using `trading_company_hub` via `module_refs:` with `namespace: "trading"`
   (mandatory, per the region-collision finding above), starting at `merchant_count: 3` (the
   module's own documented default, `data/content/world_modules/trading_company_hub.yaml` L9-13).
   `highland_traverse`'s alternate `merchant_caravan` lever is not needed — 3 candidates with a
   single proven lever satisfies the ticket's "≥2 additional worlds" AC with margin, and
   investigation's own recommendation already named these 3 as the strongest fit (only
   `frontier_extended`/`frontier_living_world` explicitly describe "trade road"/"mine economy";
   `swamp_border_world` is the plainer but still-valid third). This is a concrete choice, not a
   placeholder — Step 4 below is the empirical gate that would only be revisited if calibration
   contradicts it.
2. **`merchant_caravan` population addition: out of scope for this ticket.** The FACTION/
   INFORMATION/SOCIAL depth-wave precedent (`tickets/done/TCK-20260710-SIMQ-DEPTH-*`) authored new
   content at the composition level using already-defined, already-tested module/population
   building blocks — never invented or wired up a previously-unused piece of content as a
   side-quest within a differently-scoped ticket. `trading_company_hub` is exactly such an
   already-tested building block (proven via `urban_political`'s own anchors); `merchant_caravan`
   is not (zero worlds have ever exercised it end-to-end). Wiring it up for `highland_traverse` is
   a legitimate, separate, smaller future ticket — not silently folded into this one's 3-world
   scope.
3. **Gini/gold-sink second-order interaction: verify via direct measurement, not by touching the
   threshold.** Step 9 below diffs each touched world's `gold_sink_fired`/`inflation_controlled`
   `loop_flags` count (from each `quality_report.json`) before vs. after the content addition and
   records the observed direction of change in Implementation Notes. `EconomyHealthMonitor.
   INFLATION_SPIRAL_GINI_THRESHOLD` (`src/economy/health_monitor.py` L22) is never edited — this is
   pure observation, satisfying the ticket's Out of Scope constraint while still closing the risk
   the investigation flagged.

No question below requires human judgment beyond what this plan already resolves; Step 4's
per-world escalation gate is a bounded, mechanical decision procedure (try default, measure,
escalate within a stated numeric ceiling, otherwise document a partial no-go for that one world
without endangering the ≥2-world AC), not a deferred design choice.

## Steps

### Step 1 — Migrate `frontier_living_world` to `module_refs:` format and add `trading_company_hub`
**Files:** `data/worlds/frontier_living_world/world.yaml`
**Change:** Replace the plain `modules: [...]` list (6 entries: `frontier_village_core`,
`wolf_den_near_forest`, `goblin_camp_conflict`, `old_mine_resource_loop`,
`bandit_road_trade_pressure`, `undead_battlefield`) with a `module_refs:` list preserving the exact
same 6 modules in the same order (`order: 0` through `order: 5`, no `namespace`/`parameters` on
any of them — behavior-preserving for existing content), then append a 7th entry:
```yaml
  - module_id: "trading_company_hub"
    order: 6
    namespace: "trading"
    parameters:
      merchant_count: 3
```
This mirrors `urban_political`'s own proven `module_refs:` pattern
(`data/worlds/urban_political/world.yaml` L8-18) exactly. Do not change `world_id`,
`generation_seed` (42), `faction_tension_overrides`, `information_source_profiles`, or
`pending_information_responses` — those are unrelated to this ticket's content addition.
**Do NOT touch:** `data/content/world_modules/frontier_village_core.yaml`,
`old_mine_resource_loop.yaml`, or any other shared module file — the namespace/parameter change
belongs only in this world's own composition file.
**Verify:** World recompiles without the `ValueError("Duplicate region ID collision ...")` that
would fire without the namespace (confirm by running the standard resolve+compile path used by
`tests/simulation_quality/test_calibrate_world_loading.py`). Resulting
`world_compile_report.json.entity_count` = 46 + 3 = 49, which is `<= 50`
(`ANCHORED_WORLD_BANDS["frontier_living_world"] = (35, 50)` in
`tests/unit/worldassembly/test_corpus_diversity.py` L53) — `test_entity_count_band` must still pass
unmodified. `distinct_populated_factions` expected to remain 6 (merchant_league already populated
via `frontier_village_population`'s 1 `traveling_merchant`) — confirm via recompile;
`test_distinct_populated_factions` must still pass unmodified.

### Step 2 — Migrate `frontier_extended` to `module_refs:` format and add `trading_company_hub`
**Files:** `data/worlds/frontier_extended/world.yaml`
**Change:** Same migration pattern as Step 1, preserving all 8 existing modules
(`frontier_village_core`, `wolf_den_near_forest`, `goblin_camp_conflict`,
`old_mine_resource_loop`, `bandit_road_trade_pressure`, `undead_battlefield`,
`orc_clan_territory`, `forest_warden_grove`) in order (`order: 0`-`7`), append
`trading_company_hub` at `order: 8`, `namespace: "trading"`, `parameters: {merchant_count: 3}`. Do
not change `generation_seed` (43) or any other composition field.
**Do NOT touch:** shared module files; `urban_political`.
**Verify:** Compiles cleanly. `entity_count` = 56 + 3 = 59; `ANCHORED_WORLD_BANDS
["frontier_extended"] = (51, None)` — open-ended ceiling, no risk regardless of eventual
`merchant_count` value. `distinct_populated_factions` expected to remain 9 — confirm via recompile.

### Step 3 — Migrate `swamp_border_world` to `module_refs:` format and add `trading_company_hub`
**Files:** `data/worlds/swamp_border_world/world.yaml`
**Change:** Same migration pattern, preserving all 3 existing modules (`frontier_village_core`,
`wolf_den_near_forest`, `sunken_swamp_border`) in order (`order: 0`-`2`), append
`trading_company_hub` at `order: 3`, `namespace: "trading"`, `parameters: {merchant_count: 3}`. Do
not change `generation_seed` (77).
**Do NOT touch:** shared module files; `urban_political`.
**Verify:** Compiles cleanly. `entity_count` = 26 + 3 = 29;
`ANCHORED_WORLD_BANDS["swamp_border_world"] = (20, 35)` — 9 entities of headroom before violating
the ceiling. `distinct_populated_factions` expected to remain 4 — confirm via recompile.

### Step 4 — Calibrate all 3 worlds at their existing anchored seeds; escalate `merchant_count` only where measurement shows it's needed
**Files:** none (measurement step); may loop back to Steps 1-3's files if escalation is required
**Change:** Run the standard calibration/evaluation path for each of the 3 worlds at their existing
`grade_anchors.json` seed set (`seed42`, `seed123`, `seed456`, all at `200t` — the only tick length
these 3 worlds are currently anchored at). Inspect each resulting `quality_report.json`'s ECONOMY
column (`grade`, `raw_score`, `event_count`, `calibration_hits` for `harvest_active`/
`crafting_active`/`trade_active`).
- If a world's ECONOMY grade moves off C (to B or A) at `merchant_count: 3` for at least its
  `seed42` run, accept the default — no escalation needed for that world.
- If a world's ECONOMY grade is still C at `merchant_count: 3`, escalate that world's
  `parameters.merchant_count` in its own `world.yaml` and recalibrate, subject to a **hard,
  world-specific ceiling** so the entity-count band is never silently violated:
  - `frontier_living_world`: escalate at most to `merchant_count: 4` (46+4=50, exactly the
    `ANCHORED_WORLD_BANDS` ceiling — do not exceed). If still C at count 4, do not force further;
    document this world as a documented no-go and rely on the other 2 worlds for the AC (see
    Acceptance Criteria Map).
  - `frontier_extended`: escalate to `merchant_count: 6` (mirrors `urban_political`'s own proven
    A-grade value; no band ceiling risk, `ANCHORED_WORLD_BANDS` ceiling is `None`).
  - `swamp_border_world`: escalate to `merchant_count: 6` (26+6=32, still within the 35 ceiling).
**Do NOT touch:** `config/simulation_quality/scoring_weights.yaml`, `grade_thresholds.yaml`, or
`src/economy/health_monitor.py` — if escalation to the stated ceiling still does not move a grade,
that is a finding to document, not a reason to touch weights/thresholds (out of scope, owned by
`TCK-20260713-SIMQ-SCORE-CEILING-FIX`).
**Verify:** At least 2 of the 3 worlds show a measurable off-C grade movement at `seed42_200t`
(the AC's own bar). Record each world's before/after `grade`/`raw_score`/`event_count` for all 3
seeds — this is the calibration evidence for AC 1.

### Step 5 — Update `tests/simulation_quality/fixtures/grade_anchors.json`
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`
**Change:** Update the ECONOMY `grade`/`score` fields for the 9 affected keys
(`frontier_living_world_seed{42,123,456}_200t`, `frontier_extended_seed{42,123,456}_200t`,
`swamp_border_world_seed{42,123,456}_200t`) to match Step 4's measured calibration output. Also
update any *other* pillar column that measurably shifts for these same 9 keys (NARRATIVE,
PROGRESSION are the two most likely, per `trading_company_hub`'s own 3 bundled
`quest_definitions` — `trade_fetch_shipment_goods`, `trade_escort_merchant_convoy`,
`trade_investigate_sabotage` — adding new quest/XP-earning surface; COGNITION is a secondary
possibility per the INFORMATION depth-wave precedent). Every changed non-ECONOMY column must be
individually attributed in Implementation Notes to a specific new quest/entity this ticket's
content introduced — do not silently absorb an unexplained diff.
**Do NOT touch:** any anchor key outside the 9 listed above — in particular `urban_political_*`,
`dungeon_crawl_*`, `sandbox_world_*`, and all Stress/Unit/Regression-tier keys must be byte-
identical before and after.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` and
`-m slow -v` pass cleanly for the updated keys; all other keys remain green with their pre-existing
values (they were expected to fail loudly for the 3 touched worlds before this step, per
test_plan.md's own note — this step is what turns that expected failure back to green).

### Step 6 — Reconcile `tests/unit/worldassembly/test_corpus_diversity.py` constants
**Files:** `tests/unit/worldassembly/test_corpus_diversity.py`
**Change:** Recompile all 3 touched worlds and compare actual `entity_count`/
`distinct_populated_factions` against the existing `ANCHORED_WORLD_BANDS`/
`EXPECTED_DISTINCT_POPULATED_FACTIONS` constants for these 3 worlds. Per Steps 1-3's projected math
and Step 4's chosen `merchant_count` values, no edit is expected to be needed (all 3 worlds stay
within their existing band, and `merchant_league` is already counted). If — and only if — actual
recompiled numbers diverge from the projection (e.g. `trading_company_hub`'s `building_recipes`/
`resource_recipes` turn out to count toward `entity_count` in a way not anticipated), update the
specific constant for the specific world with a comment citing this ticket, exactly as prior
tickets in this file's own history have done (see the file's existing per-entry comments
attributing each constant to its origin ticket). Do not touch any constant for a world this ticket
does not touch.
**Do NOT touch:** `NEWLY_ANCHORED_MODULES` (irrelevant — `trading_company_hub` is already anchored
via `urban_political`, not newly anchored), any Stress/Unit/Regression-tier world's entry.
**Verify:** `pytest tests/unit/worldassembly/test_corpus_diversity.py -v` passes in full, including
`test_hazard_kind_completeness`/`test_hazard_kind_matches_populating_faction_immunity` for the 3
touched worlds — `trading_company_hub`'s own `hometown` region (now namespaced, e.g.
`trading_hometown`) declares `hazard_level: 0.5`/`hazard_kind: "NATURAL_TERRAIN"`; confirm
`merchant_league` (the populating faction) has a matching `hazard_immunities` entry in
`data/content/social/factions.yaml`, or that the region-level "any populating faction is immune"
semantics documented in this test file's own docstring (§3b) still resolve it — do not add a new
xfail/skip if it already passes under existing semantics.

### Step 7 — Add an architecture guard confirming `trading_company_hub` composition presence
**Files:** `tests/unit/worldassembly/test_corpus_diversity.py`
**Change:** Add one small parametrized test (new function, not a new file — this file already owns
per-world composition assertions and already has the `_world_modules()` helper that handles both
`modules:` and `module_refs:` formats) asserting `"trading_company_hub" in _world_modules(world_id)`
for `world_id` in `["frontier_living_world", "frontier_extended", "swamp_border_world"]`. This is
the test_plan.md item 3 architecture guard — it protects against a future unrelated edit silently
dropping this ticket's authored content.
**Do NOT touch:** any other test function in this file beyond the new addition.
**Verify:** New test passes for all 3 worlds; fails if any is reverted (sanity-check by temporarily
reverting one world's change locally, confirming the new test catches it, then re-applying —
optional but recommended before Finalize).

### Step 8 — Full regression sweep and unattributed-diff guards
**Files:** none (verification step)
**Change:** Run the full scoped pytest command set from `test_plan.md`'s "Scoped Pytest Commands"
section, in order, plus `python3 tools/evaluate_simq.py --dry-run` then
`python3 tools/evaluate_simq.py`. Specifically re-confirm:
- `dungeon_crawl_seed42_1000t` and `sandbox_world_seed42_1000t` still produce byte-identical
  ECONOMY output (`raw_score=192.0`, `event_count=24`) — the generic `gold_sink_fired` baseline
  must be unaffected by this ticket's changes to unrelated worlds.
- `urban_political`'s ECONOMY anchors are byte-identical to pre-ticket state
  (`pytest tests/simulation_quality/test_grade_regression.py -k urban_political`).
- `data/content/world_modules/frontier_village_core.yaml`, `settled_quarter.yaml`,
  `old_mine_resource_loop.yaml` are byte-identical to pre-ticket state (`git diff` shows no changes).
- `git diff --stat` shows changes only under `data/worlds/{frontier_living_world,
  frontier_extended,swamp_border_world}/world.yaml`,
  `tests/simulation_quality/fixtures/grade_anchors.json`,
  `tests/unit/worldassembly/test_corpus_diversity.py`, `docs/parity_ledger/infrastructure.yaml`,
  `docs/simulation_quality/{current_state.md,eval_matrix_results.md}` — nothing under
  `data/worlds/{crowded_frontier,resource_dense_basin,frontier_marches,unit_*,hero_guild_routing,
  simq_routing_test,urban_political,dungeon_crawl,wilderness_survival,highland_traverse,
  sandbox_world,generated_frontier_3_42}/`.
**Do NOT touch:** anything outside the diff scope listed above.
**Verify:** All scoped pytest commands green; `evaluate_simq.py` full sweep shows 0 unattributed
regressions (any NARRATIVE/PROGRESSION shift for the 3 touched worlds is attributed per Step 5, not
a regression).

### Step 9 — Document the Gini/gold-sink second-order interaction
**Files:** none durable (observation feeds into Implementation Notes / Completion Summary of the
ticket file, and optionally a one-line note in `docs/simulation_quality/eval_matrix_results.md` if
the effect is material)
**Change:** For each of the 3 touched worlds, compare the `loop_flags` field (specifically presence/
absence of `gold_sink_fired`/`inflation_controlled`) in each `quality_report.json` from Step 4's
before-content and after-content calibration runs. Record whether the generic baseline signal
changed as a side effect of the new merchant population's wealth distribution, per
investigation.md Risk 3. This is observation only.
**Do NOT touch:** `src/economy/health_monitor.py`'s `INFLATION_SPIRAL_GINI_THRESHOLD` — explicit
ticket Out of Scope, regardless of what this observation finds.
**Verify:** The comparison is recorded in the ticket's Implementation Notes with concrete
before/after values, closing investigation.md Risk 3 as measured rather than assumed.

### Step 10 — Update docs and parity ledger
**Files:** `docs/parity_ledger/infrastructure.yaml`, `docs/simulation_quality/current_state.md`,
`docs/simulation_quality/eval_matrix_results.md`
**Change:**
- `infrastructure.yaml`: update `INFRA-242`'s `v2_evidence` to cite the 3 new worlds' measured
  ECONOMY event counts (from Step 4) as further corroboration of scorer event-type coverage; cross-
  check (not necessarily edit) `SIMQ-CALIBRATED-001`.
- `current_state.md`: refresh the ECONOMY grade distribution counts (currently "0 S / 1 A / 17 B /
  57 C, across 75 anchor entries / 18 worlds") to reflect the post-ticket counts once Step 5's
  anchor updates land.
- `eval_matrix_results.md`: update the "Zero-Pillar World Confirmation" section (~L1046-1060) to
  remove or annotate the 3 now-covered worlds, explicitly noting `wilderness_survival`,
  `highland_traverse`, and `dungeon_crawl` remain valid zero-pillar/rejected cases (not silently
  dropped from the record).
**Do NOT touch:** `docs/simulation_quality/corpus_tier_taxonomy.md` (tier structure itself is
unchanged by this ticket — no new tier, no world moved between tiers).
**Verify:** `make knowledge-index-update` run after these doc edits (per CLAUDE.md "After Work");
`docs/REGISTRY.yaml` regenerates cleanly at Finalize.

## Scope Guards

- Do not touch `config/simulation_quality/scoring_weights.yaml` or `grade_thresholds.yaml` — owned
  by `TCK-20260713-SIMQ-SCORE-CEILING-FIX`, already landed.
- Do not touch `src/economy/health_monitor.py`'s `INFLATION_SPIRAL_GINI_THRESHOLD` under any
  circumstance, including if Step 9's observation shows a material effect.
- Do not edit `data/content/world_modules/frontier_village_core.yaml`, `settled_quarter.yaml`, or
  `old_mine_resource_loop.yaml` — author only at the composition level
  (`data/worlds/<world>/world.yaml`).
- Do not touch `urban_political` (any file under `data/worlds/urban_political/`) — Regression/
  baseline tier, reference case, not a target.
- Do not add economy content to any Stress/Unit/Regression-tier world (`crowded_frontier`,
  `resource_dense_basin`, `frontier_marches`, any `unit_*` world, `hero_guild_routing`,
  `simq_routing_test`).
- Do not add merchant/crafting content to `dungeon_crawl` or `wilderness_survival` — no settlement
  module, already investigated-and-rejected by prior depth-wave tickets for the same structural
  reason.
- Do not touch `highland_traverse` — not a chosen candidate in this plan; its `merchant_caravan`
  lever is deferred to a possible future ticket.
- Do not add or wire up the `merchant_caravan` population anywhere in this ticket.
- Do not narrow the full regression sweep to ECONOMY's own anchor columns — cross-pillar shifts
  (NARRATIVE/PROGRESSION) must be reviewed and attributed for all 3 touched worlds.
- Do not silently widen an `ANCHORED_WORLD_BANDS` ceiling to accommodate a `merchant_count` that
  exceeds the per-world ceilings stated in Step 4 — if `frontier_living_world` can't clear C within
  its `merchant_count: 4` ceiling, that is a documented partial no-go for that one world, not a
  license to change the band.
- Do not re-open FACTION/INFORMATION/SOCIAL/AGENCY depth work — declared complete by the archived
  roadmap's Phase 5 gate.

## Dependency Map

- Steps 1, 2, 3 are independent of each other (different world files) and can be done in any order,
  but each must individually pass its own compile/band/faction-count check before moving on.
- Step 4 depends on Steps 1-3 (needs all 3 worlds' base module addition in place to calibrate).
- Step 4's escalation branch (if triggered) loops back into the relevant world's Step 1/2/3 file
  before re-measuring — this is expected, not a plan deviation.
- Step 5 depends on Step 4's final measured values (post any escalation).
- Step 6 depends on Steps 1-3 (recompile numbers) and can run in parallel with Step 5.
- Step 7 depends on Steps 1-3 (the composition change it's guarding must exist first) but not on
  Step 4/5/6.
- Step 8 depends on Steps 1-7 all being complete (it is the full-sweep gate).
- Step 9 depends on Step 4's before/after `quality_report.json` data (can be done alongside Step 5).
- Step 10 depends on Steps 4/5/8 (needs final measured numbers and a clean regression sweep before
  documenting).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| ECONOMY grade moves measurably off C in ≥2 additional worlds, with calibration evidence in `eval_matrix_results.md` | Steps 1-5, 10 | `pytest tests/simulation_quality/test_grade_regression.py -v` (updated anchors); Step 4's recorded before/after `quality_report.json` values; `eval_matrix_results.md` diff |
| 0 regressions on a full `evaluate_simq.py` sweep | Steps 6, 7, 8 | Full scoped pytest suite (test_plan.md's "Scoped Pytest Commands"); `python3 tools/evaluate_simq.py` (live, post dry-run) |
| "Fewer than 2-3 candidates" closure is equally valid if honest investigation finds none | N/A — moot | Investigation already found and this plan confirms 3 concrete, verified candidates with a proven lever (`trading_company_hub`, already anchored via `urban_political`); this closure path is not exercised. If Step 4 unexpectedly fails to move ≥2 worlds off C even at each world's escalation ceiling, this clause is the documented fallback for the shortfall, not a reason to expand scope beyond the 3 confirmed candidates. |

## Anti-Drift Notes

- **The region-ID-collision finding is the single most important correction this plan makes to
  investigation.md.** Do not attempt to add `trading_company_hub` via the plain `modules: [...]`
  list to any of the 3 worlds — it will raise `ValueError("Duplicate region ID collision 'hometown'
  ...")` at compile time (`src/worldassembly/resolver.py` L346-347), because `frontier_village_core`
  (already present in all 3 worlds) and `trading_company_hub` both declare a region literally named
  `"hometown"`. The `module_refs:` + `namespace: "trading"` migration is mandatory infrastructure,
  not an optional lever for a non-default `merchant_count`.
- **Do not assume `merchant_count: 3` (the module default) is sufficient to clear C** —
  `urban_political`'s only proven A-grade data point used `merchant_count: 6`. Step 4's calibrate-
  then-escalate procedure is the resolution; do not skip straight to `merchant_count: 6` for all 3
  worlds without checking the default first, since `frontier_living_world`'s entity-count band
  ceiling (50) only has 4 entities of headroom above its current count (46) — going straight to +6
  would silently violate `test_entity_count_band` for that one world.
- **Do not conflate the generic `gold_sink_fired`/`inflation_controlled` baseline with real content-
  driven ECONOMY activity** when reading any of the 3 touched worlds' pre-ticket 1000t+ runs — a B
  grade there (if one exists) is not evidence the content gap was smaller than measured.
- **`merchant_league` is already a populated faction in all 3 worlds** (via `frontier_village_core`'s
  `frontier_village_population`, which includes 1 `traveling_merchant`) — do not treat adding
  `trading_company_hub`'s merchant population as introducing a "new" faction requiring a
  `distinct_populated_factions` constant bump; verify this assumption via recompile in Steps 1-3
  rather than skipping the check because the reasoning sounds airtight.
- **Cross-pillar side effects are expected, not a bug** — `trading_company_hub`'s 3 bundled
  `quest_definitions` will very likely register as new NARRATIVE/PROGRESSION signal for all 3
  worlds; attribute, don't suppress or "fix."

## Deviations (recorded during Implement, TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH)

**Steps 1-3, 6, 7, 8, 10: executed exactly as planned, no deviation.** Module composition migration,
entity-count/faction-count reconciliation, the new architecture guard test, the regression sweep,
and the doc/parity-ledger updates all landed as scoped.

**Step 4: escalation gate never triggered — not because a world individually failed to clear C
within its ceiling, but because escalation provably does nothing, in any of the 3 worlds, at any
tick length tested.** The plan assumed (per investigation.md, carried through without independent
re-verification) that `trading_company_hub` at `merchant_count: 6` is a *proven* lever, evidenced by
`urban_political_seed123_1000t`'s 69-event/grade-A run. Direct measurement during Implement disproves
this: grepping every `data/calibration/*/quality_scores.jsonl` in the corpus for
`resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction` returns zero matches
anywhere, including all 8 of `urban_political`'s own seed/tick combinations — that 69-event run is
100% `gold_sink_fired` (the generic, content-independent baseline), not real economic activity. This
was confirmed by escalating `frontier_extended` to `merchant_count: 6` (the plan's stated ceiling)
at 200t (still 0 ECONOMY events, all 3 seeds) and diagnostically at 1000t (24 events, but 100%
`gold_sink_fired` again, matching the generic baseline shape exactly). Since escalation demonstrably
does not help, **no world was escalated** — all 3 stayed at the module default `merchant_count: 3`,
and Step 4's "document a no-go" fallback applies to **all 3 worlds' ECONOMY movement**, not the
single-world partial-no-go the plan anticipated for `frontier_living_world` alone.

**Step 5: ECONOMY column required no edit for any of the 9 keys (unchanged C/0.0 throughout);
cross-pillar shifts were larger/more numerous than the plan's own COMBAT/WORLD hedging anticipated**
(2 WORLD entries crossed B→A, 1 PROGRESSION entry crossed A→B, plus several within-band SOCIAL/
NARRATIVE/COMBAT score shifts) — all individually attributed in
`docs/simulation_quality/eval_matrix_results.md`'s new calibration-batch section per the plan's own
requirement, not silently absorbed.

**Step 8: the live (non-`--dry-run`) `python3 tools/evaluate_simq.py` full-corpus re-run named in
the plan's Step 8 text was not executed**, per an explicit scope-guard restriction given at
Implement time ("do NOT run a fresh full corpus calibration sweep beyond the 9 targeted keys plus
the regression-guard spot checks") that narrows Step 8's literal text. `--dry-run` (750 pillars
checked, 0 regressions, 0 missing) was used instead, satisfying the "0 regressions on a full sweep"
AC without triggering fresh engine runs for all 75 anchors.

**Overall: AC1 was not achieved, and this is the plan's most significant deviation.** The plan's
central premise — that `trading_company_hub` is an already-proven, already-tested lever needing only
content-level composition — is disproven by direct evidence gathered during Implement, not by a
shortfall in following the plan's steps. See the ticket's Completion Summary and Implementation
Notes, and `docs/parity_ledger/infrastructure.yaml::INFRA-242`'s `support_boundary`, for the full
root-cause record. No file outside the plan's intended scope was touched; `src/simulation_quality/
scorers/economy.py` and `src/economy/health_monitor.py` were never edited.
