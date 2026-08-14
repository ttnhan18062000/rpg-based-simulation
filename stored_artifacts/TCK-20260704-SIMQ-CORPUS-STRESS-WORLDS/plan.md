---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS
artifact_type: plan
tags: [simulation-quality, world, corpus, calibration]
---

# Implementation Plan — TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS

## Summary

This ticket authors 3 new stress-tier worlds from existing catalog modules only (no new module
content — UQ-1 resolves to "existing catalog sufficient" for all 3 gaps, confirmed by investigation.md's
module-composition analysis), each following the same per-world cycle: author `world.yaml` → compile/
register → extend `test_corpus_diversity.py`'s two source-of-truth dicts → run the corpus-diversity/
population-stability/hazard-kind regression guards → run a 3-seed × 200t calibration matrix → add
grade-anchor entries. World C (gap c) additionally authors bespoke `faction_tension_overrides`/
`information_source_profiles`/`pending_information_responses` content and gets a dedicated parity-ledger
step. Three consolidation steps close out documentation and the final regression gate.

**World compositions committed (all from `data/content/world_modules/`, no new module authored):**

| World ID | Gap filled | Modules | Entities | Regions | Resource nodes | Distinct populated factions |
|---|---|---|---|---|---|---|
| `crowded_frontier` | (a) many-factions/small-map | `frontier_village_core`, `hero_adventurers`, `bandit_road_trade_pressure`, `goblin_camp_conflict`, `orc_clan_territory` | 38 | 4 | 23 | 6 (`town_council`, `merchant_league`, `hero_guild`, `bandit_company`, `goblin_warband`, `orc_clan`) |
| `resource_dense_basin` | (b) resource-saturated/small-map | `frontier_village_core`, `old_mine_resource_loop`, `orc_clan_territory` | 23 | 3 | 37 (~12.3/region) | 4 (`town_council`, `merchant_league`, `wild_beast_pack`, `orc_clan`) |
| `frontier_marches` | (c) large-scale FACTION/INFORMATION-from-inception | `frontier_village_core`, `hero_adventurers`, `wolf_den_near_forest`, `goblin_camp_conflict`, `bandit_road_trade_pressure`, `orc_clan_territory`, `undead_battlefield`, `sunken_swamp_border`, `old_mine_resource_loop` | 62 | 9 | 63 | 9 (`town_council`, `merchant_league`, `hero_guild`, `wild_beast_pack`, `goblin_warband`, `bandit_company`, `orc_clan`, `undead_remnants`, `swamp_tribe`) |

All module pairs screened against the two forbidden region-id collisions (`bandit_road_trade_pressure`+
`scalable_bandit_camp`, `wolf_den_near_forest`+`nomadic_herd` — neither pair appears in any of the 3
compositions), and every region-owning module already declares correct `hazard_kind`/`hazard_immunities`
(directly re-verified this session: `goblin_camp_conflict` hazard_level 3.0/`NATURAL_TERRAIN`,
`orc_clan_territory` 3.0/`NATURAL_TERRAIN`, `old_mine_resource_loop` 2.0/`NATURAL_TERRAIN`,
`bandit_road_trade_pressure` 2.0/`NATURAL_TERRAIN`, `sunken_swamp_border` 2.5/`NATURAL_TERRAIN`,
`undead_battlefield` `UNDEAD_CORRUPTION`, `frontier_village_core`/`hero_adventurers` hazard_level 0.0).
`undead_battlefield` is used in preference to `ruins_mystery_quest`'s `haunted_battlefield` variant per
investigation's finding that the latter lacks `hazard_kind` at hazard_level 3.5 (an unfixed pre-existing
gap, not this ticket's job to fix).

### Resolution of the 3 flagged open questions (decided here, not deferred)

**1. "Small-map" = region count, not raw entity count, for gap (a).** Investigation confirms no catalog
combination reaches 6+ distinct populated factions under ~20 entities — every faction-populating module
except `hero_adventurers` (0-region-cost) contributes 5+ entities, and `populations.yaml` has no
faction-bearing recipe under 3 entities besides individual hero recipes. The ticket's own Scope item 1(a)
text says "comparable in entity/**region**" footprint — region count is the axis actually named first and
is the one the corpus's existing scale-diversity gap describes ("faction density and world size [region
count] move together"). `crowded_frontier` at 4 regions matches `wilderness_survival`'s region count
exactly; its 38 entities is the unavoidable cost of reaching 6 populated factions with zero new module
authoring. Committing to the recommended composition
(`frontier_village_core`+`hero_adventurers`+`bandit_road_trade_pressure`+`goblin_camp_conflict`+
`orc_clan_territory`) rather than authoring new, deliberately small population recipes, because: (a)
UQ-1 already resolves toward catalog-only, and inventing new small recipes to chase the entity-count axis
too would be a materially larger, separately-scoped authoring effort: (b) the ticket's AC only requires
"entity/region footprint comparable to `wilderness_survival`/`sandbox_world`" as a description, not an
exact numeric match on both axes simultaneously — a reasonable reading given (a) is impossible without
new content. This reasoning is the Implementation Notes content for Step 1.

**2. Gap (c) is kept, reframed as "authoring-from-inception, not retrofitted" — not dropped.** The
premise that no large-scale world has FACTION/INFORMATION content is now stale (`frontier_extended`,
`frontier_living_world` both gained it via the sibling `E2E-CONTENT-EXPANSION` ticket, added
retroactively to already-anchored worlds). Reframing rather than dropping, because: the ticket's Scope
item 1(c) and AC are literal ("author... a NEW world... first data point... at large scale" — the
*deliverable* is unaffected by the staleness, only the *rationale*), and because a from-inception data
point is a genuinely distinct signal from a retrofit — it tests whether bespoke FACTION/INFORMATION
content designed alongside a world's initial composition (this ticket) differs from content added to an
already-stable, already-anchored world after the fact (E2E ticket), mirroring exactly how
`hero_guild_routing` was accepted as a second, distinct AGENCY-active archetype rather than redundant with
`simq_routing_test`. `frontier_marches` is authored as a new world (not a variant of `frontier_extended`)
using a genuinely different module subset — it shares 6 of `frontier_extended`'s 8 modules but swaps out
`forest_warden_grove` for `hero_adventurers`+`sunken_swamp_border`, so its faction mix (includes
`hero_guild`/`swamp_tribe`, excludes `forest_wardens`/`spirit_court`) and region set (9 regions, one
short of `frontier_extended`'s 10, but 62 vs. 56 entities) are not a duplicate composition. Step 11 (the
`corpus_tier_taxonomy.md` update) corrects the stale gap-3 text and the "no stress-tier world exists yet"
sentence in the same edit, per investigation's own flag that this doc-update step is the right place to
fix it, not leave it silently inconsistent.

**3. All 3 new worlds are added directly to `ANCHORED_WORLD_BANDS`/`EXPECTED_DISTINCT_POPULATED_FACTIONS`
at authoring time (confirmed, not deferred).** `POPULATION_STABILITY_WORLDS` is computed as
`list(ANCHORED_WORLD_BANDS.keys()) + [...unit worlds...]` (test_corpus_diversity.py line 52) — adding a
world to `ANCHORED_WORLD_BANDS` automatically cascades it into `POPULATION_STABILITY_WORLDS` too, and
also drives `test_hazard_kind_completeness` (parametrized over the same dict's keys, line 219). So each
world needs exactly **2** dict edits (`ANCHORED_WORLD_BANDS`, `EXPECTED_DISTINCT_POPULATED_FACTIONS`), not
3 separate list edits, to get all 4 regression guards (`test_entity_count_band`,
`test_distinct_populated_factions`, `test_population_stability`, `test_hazard_kind_completeness`) running
against them. This is the normal precedent every prior corpus-authoring ticket followed at creation time
(`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` for the original 5, this ticket for these 3) — the separate
backfill ticket (`TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP`) exists only because 3 *old*
worlds were missed, not because deferral is the norm.

**4. (Flagged in investigation, resolved here too.) Extend both `FAC-012` and `INFRA-256` additively for
World C, closing the inconsistency rather than perpetuating it.** `INFRA-256` has already been extended
twice for the same `information_source_profiles`/`pending_information_responses` mechanism; `FAC-012` was
not extended by the E2E ticket even though that ticket added `faction_tension_overrides` to 8 worlds — an
inconsistency, not a rule. Since gap (c)'s world is explicitly about this exact mechanism at a new scale,
extending `FAC-012` additively now (Step 10) closes the gap rather than leaving it permanently stale.

## Steps

### Step 1 — Author, compile, and register `crowded_frontier` (gap a)

**Files:** new `data/worlds/crowded_frontier/world.yaml`; `data/worlds/crowded_frontier/world_compile_report.json`
and `data/worlds/crowded_frontier/resolved/world.resolved.yaml` (generated by compile, not hand-written);
`data/worlds/world_index.json` (registered via the repository's index-update path, same mechanism that
registered `hero_guild_routing`/`swamp_border_world`).

**Change:** Author `data/worlds/crowded_frontier/world.yaml` with exactly this composition (flat
`modules:` list, mirroring `frontier_extended`'s/`swamp_border_world`'s style — no `feature_flags:`
needed, all defaults):

```yaml
# STATE: ADDITIONAL
schema_version: "worldcomposition.v1"
world_id: "crowded_frontier"
name: "Crowded Frontier"
description: "A single frontier settlement pressed on three sides by a bandit-controlled road, a goblin war-camp, and an orc clan's stronghold — six distinct factions contest a footprint no larger than the corpus's smallest worlds."
modules:
  - "frontier_village_core"
  - "hero_adventurers"
  - "bandit_road_trade_pressure"
  - "goblin_camp_conflict"
  - "orc_clan_territory"
default_perspectives:
  - "hero_guild_perspective"
  - "goblin_warband_perspective"
  - "merchant_league_perspective"
generation_seed: 601
```

Compile: resolve + `WorldCompiler.compile(spec, seed)` (mirror the exact procedure used in
`stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/plan.md` and
`stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY/plan.md` Step 1 for producing
`resolved/world.resolved.yaml` and `world_compile_report.json`, and registering the `world_index.json`
entry via `WorldRepository`). Confirm directly against the compile report (do not assume):
`warnings: []`, `entity_count == 38`, `region_count == 4`,
`distinct_populated_factions == 6` (per Scope item 3 — numeric confirmation from
`WorldCompiler.compile()`'s report, not eyeballing `world.yaml`). If the measured numbers differ from
the table above, treat the measured value as ground truth for Steps 2-3 (do not force the test to match
an assumed target).

**Do NOT touch:** `data/content/world_modules/*.yaml` (shared catalog — no module content edits), any
existing world's `world.yaml`/`world_compile_report.json`, `data/content/world_compositions/crowded_frontier.yaml`
(do not create — that directory is a stale, diverged mirror; only `data/worlds/crowded_frontier/world.yaml`
is authoritative).

**Verify:** Manual read of `world_compile_report.json` confirming `warnings: []` and the 3 numeric facts
above. No pytest yet (guards not wired until Step 2).

---

### Step 2 — Wire `crowded_frontier` into the corpus-diversity regression guards

**Files:** `tests/unit/worldassembly/test_corpus_diversity.py` — `ANCHORED_WORLD_BANDS` (lines 39-45),
`EXPECTED_DISTINCT_POPULATED_FACTIONS` (lines 62-73).

**Change:** Add exactly one entry to each dict:
```python
ANCHORED_WORLD_BANDS: dict[str, tuple[int, int | None]] = {
    ...
    "crowded_frontier": (35, 50),
}
```
```python
EXPECTED_DISTINCT_POPULATED_FACTIONS: dict[str, int] = {
    ...
    "crowded_frontier": 6,   # use the ACTUAL measured value from Step 1's compile report
}
```
Use the entity-count band `(35, 50)` because Step 1's measured `entity_count` (38) falls inside it
(same band tuple `frontier_living_world` uses — sharing a band tuple across worlds is normal, each dict
key is independent). If Step 1's measured entity_count differs from 38, pick the band that actually
brackets it instead of forcing `(35, 50)`.

**Do NOT touch:** `POPULATION_STABILITY_WORLDS` (line 52) directly — it is computed from
`ANCHORED_WORLD_BANDS.keys()` plus the unit-world list; adding `crowded_frontier` to
`ANCHORED_WORLD_BANDS` alone is sufficient and correct (see Summary resolution #3). Do not touch any
existing dict entry's value. Do not touch `NEWLY_ANCHORED_MODULES`/`STILL_UNANCHORED_MODULE` — no new
module was authored.

**Verify:**
```
pytest tests/unit/worldassembly/test_corpus_diversity.py -k crowded_frontier -q
```
Must cover and pass `test_entity_count_band[crowded_frontier]`,
`test_distinct_populated_factions[crowded_frontier]`, `test_hazard_kind_completeness[crowded_frontier]`
(fast), and `test_population_stability[crowded_frontier]` (`@pytest.mark.slow` — run explicitly, not
swept by `-m "not slow"`).

**Depends on:** Step 1.

---

### Step 3 — Calibrate `crowded_frontier` (3 seeds × 200t) and anchor

**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`,
`tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`, lines 41-90).

**Change:** Run (no profile needed — all feature flags default):
```
.venv/bin/python3 tools/calibrate_simq.py --name crowded_frontier --seed 42  --ticks 200
.venv/bin/python3 tools/calibrate_simq.py --name crowded_frontier --seed 123 --ticks 200
.venv/bin/python3 tools/calibrate_simq.py --name crowded_frontier --seed 456 --ticks 200
```
Add 3 new keys — `crowded_frontier_seed42_200t`, `crowded_frontier_seed123_200t`,
`crowded_frontier_seed456_200t` — to `grade_anchors.json`, recording the actual measured grade for all
10 pillars, following the exact structural shape of an existing 200t entry (e.g.
`swamp_border_world_seed42_200t`). Add the same 3 keys to `FAST_ANCHOR_KEYS`. Record grades honestly —
this is a stress-tier world with an unusually dense faction mix in a small region count; do not assume
any particular grade.

**Do NOT touch:** Any other world's entries in `grade_anchors.json` or `FAST_ANCHOR_KEYS`.

**Verify:**
```
pytest tests/simulation_quality/test_grade_regression.py -k crowded_frontier -q
```

**Depends on:** Step 1 (world must exist and compile cleanly); independent of Step 2's ordering but
both must land before Step 12 (final sweep).

---

### Step 4 — Author, compile, and register `resource_dense_basin` (gap b)

**Files:** new `data/worlds/resource_dense_basin/world.yaml`; generated `world_compile_report.json` /
`resolved/world.resolved.yaml`; `data/worlds/world_index.json`.

**Change:** Author `data/worlds/resource_dense_basin/world.yaml`:
```yaml
# STATE: ADDITIONAL
schema_version: "worldcomposition.v1"
world_id: "resource_dense_basin"
name: "Resource-Dense Basin"
description: "A frontier village pressed between an orc-held stronghold and an old mine riddled with resource nodes — three regions carry a resource-node density roughly 7x the corpus average, the inverse of frontier_extended's sparse-large-map profile."
modules:
  - "frontier_village_core"
  - "old_mine_resource_loop"
  - "orc_clan_territory"
default_perspectives:
  - "merchant_league_perspective"
  - "wild_beast_pack_perspective"
generation_seed: 602
```
Compile and confirm (do not assume): `warnings: []`, `entity_count == 23`, `region_count == 3`,
`distinct_populated_factions == 4`, resource-node count `== 37` (~12.3/region, vs. the corpus's existing
max of 1.75/region in `swamp_border_world` — this is the numeric evidence for the gap-b justification,
recorded in Step 10's doc update). This is the lower-risk direction of gap (b) per investigation's
recommendation (resource-saturated/small-map, not sparse-resources/large-map — the sparse direction would
need ~7-8 modules and carries materially higher recompile-drift risk for the same gap, per investigation's
Current Behavior analysis).

**Do NOT touch:** Any existing module or world file; do not create
`data/content/world_compositions/resource_dense_basin.yaml`.

**Verify:** Manual read of `world_compile_report.json` confirming the 4 numeric facts above and 0
warnings.

---

### Step 5 — Wire `resource_dense_basin` into the corpus-diversity regression guards

**Files:** `tests/unit/worldassembly/test_corpus_diversity.py` — same two dicts as Step 2.

**Change:**
```python
ANCHORED_WORLD_BANDS: dict[str, tuple[int, int | None]] = {
    ...
    "resource_dense_basin": (20, 35),
}
EXPECTED_DISTINCT_POPULATED_FACTIONS: dict[str, int] = {
    ...
    "resource_dense_basin": 4,   # use the ACTUAL measured value from Step 4
}
```
Band `(20, 35)` mirrors `swamp_border_world`'s tuple since Step 4's measured entity_count (23) falls
inside it; adjust if the measured value differs.

**Do NOT touch:** Same guards as Step 2 (no edits to `POPULATION_STABILITY_WORLDS` list literal,
`NEWLY_ANCHORED_MODULES`, `STILL_UNANCHORED_MODULE`, or any existing dict entry).

**Verify:**
```
pytest tests/unit/worldassembly/test_corpus_diversity.py -k resource_dense_basin -q
```
(covers entity-band, distinct-factions, hazard-kind, and the slow population-stability test).

**Depends on:** Step 4.

---

### Step 6 — Calibrate `resource_dense_basin` (3 seeds × 200t) and anchor

**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`,
`tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`).

**Change:** Run and anchor identically to Step 3's procedure, substituting `resource_dense_basin`:
```
.venv/bin/python3 tools/calibrate_simq.py --name resource_dense_basin --seed 42  --ticks 200
.venv/bin/python3 tools/calibrate_simq.py --name resource_dense_basin --seed 123 --ticks 200
.venv/bin/python3 tools/calibrate_simq.py --name resource_dense_basin --seed 456 --ticks 200
```
Add `resource_dense_basin_seed{42,123,456}_200t` to `grade_anchors.json` and `FAST_ANCHOR_KEYS`.
Given the ECONOMY-pillar-relevant nature of this world (resource-node saturation), pay particular
attention to whether the ECONOMY grade looks anomalous — record honestly either way.

**Do NOT touch:** Any other world's entries.

**Verify:**
```
pytest tests/simulation_quality/test_grade_regression.py -k resource_dense_basin -q
```

**Depends on:** Step 4.

---

### Step 7 — Resource-node source-region-tag spot-check for `resource_dense_basin` (contingent)

**Files:** `data/content/world/resources.yaml` (read-only unless a gap is confirmed);
`tests/unit/strategic/test_opportunities.py` (extend only if a real gap is found).

**Change:** Per the `hero_guild_routing` precedent's Step 2 method, verify that `old_mine` and
`orc_stronghold` (the 2 regions this world introduces beyond `hometown`, which is already covered) each
have at least one resource-kind whose `source_region_tags` in `data/content/world/resources.yaml` covers
them, so no entity native to these regions hits a zero-legal-opportunity condition.
Note: unlike `hero_guild_routing`, none of this ticket's 3 worlds enable `ENABLE_ADVENTURE_ROUTING`, so
this is a lower-stakes check (it does not gate AGENCY route-legality here) — but resource-opportunity
coverage is still worth a quick confirmation given gap (b)'s resource-density framing. If a real gap is
found: add one targeted spot-check test to `test_opportunities.py` mirroring
`test_resource_opportunities_hometown_wood_node`'s pattern; do not touch the shared catalog file itself.
If no gap is found: document the clean pass in Step 10, add no test (per test_plan's "honest result"
norm — do not add a synthetic test for a gap that doesn't exist).

**Do NOT touch:** `data/content/world/resources.yaml` speculatively; the existing `hometown`-tag entries.

**Verify:** `pytest tests/unit/strategic/test_opportunities.py -q` (existing tests stay green; new test,
if added, passes).

**Depends on:** Step 4 (needs the world's resolved region set).

---

### Step 8 — Author, compile, and register `frontier_marches` (gap c) with bespoke FACTION/INFORMATION content

**Files:** new `data/worlds/frontier_marches/world.yaml`; generated `world_compile_report.json` /
`resolved/world.resolved.yaml`; `data/worlds/world_index.json`.

**Change:** Author `data/worlds/frontier_marches/world.yaml`:
```yaml
# STATE: ADDITIONAL
schema_version: "worldcomposition.v1"
world_id: "frontier_marches"
name: "Frontier Marches"
description: "A sprawling borderland where a frontier village, a hero guild, a wolf-infested forest, a goblin war-camp, a bandit-held road, an orc stronghold, a haunted battlefield, a sunken swamp, and an old mine all sit within reach of one another — comparable in scale to frontier_extended, but authored with FACTION tension and INFORMATION content from its very first compile rather than retrofitted after anchoring."
modules:
  - "frontier_village_core"
  - "hero_adventurers"
  - "wolf_den_near_forest"
  - "goblin_camp_conflict"
  - "bandit_road_trade_pressure"
  - "orc_clan_territory"
  - "undead_battlefield"
  - "sunken_swamp_border"
  - "old_mine_resource_loop"
default_perspectives:
  - "hero_guild_perspective"
  - "wild_beast_pack_perspective"
  - "goblin_warband_perspective"
  - "merchant_league_perspective"
  - "undead_remnants_perspective"
  - "swamp_tribe_perspective"
generation_seed: 603
faction_tension_overrides:
  bandit_company: 0.5
  orc_clan: 0.5
information_source_profiles:
  - source_id: "town_notice_board"
    source_kind: "guide"
    knowledge_scopes: ["regional_danger", "common_resource_sources"]
    accuracy: 0.4
    freshness: 0.6
    bias: 0.1
    cost_gold: 0
    max_answers_per_query: 2
pending_information_responses:
  - target_population_id: "frontier_village_population_frontier_guard"
    subject: "bandit_road_conditions"
    query_kind: "danger_rating"
    source_id: "town_notice_board"
    answer_kind: "KNOWN_FACT"
    certainty: 0.72
    details:
      danger_level: "elevated"
      region: "bandit_road"
    cost_paid: 0
```

**Bespoke-content rationale (must be recorded, not silently reused):** tension pair is
`bandit_company`+`orc_clan` — a pairing no other existing world declares together (`frontier_extended`
declares `orc_clan`+`forest_wardens`; `frontier_living_world` declares `bandit_company`+`merchant_league`)
— chosen because this world is the only one where both the bandit-road module and the orc-clan module are
simultaneously present with neither's counterpart tension partner (`forest_wardens`/`merchant_league` are
not the focus here), giving an honest "dual external-threat" framing distinct from either sibling world.
The information subject (`bandit_road_conditions`, region `bandit_road`, certainty `0.72`) is deliberately
different in subject, region, and certainty value from `frontier_extended`'s `orc_clan_encroachment`
(region `orc_stronghold`, certainty `0.75`) and from `swamp_border_world`'s `swamp_border_danger` (region
`swamp_border_territory`, certainty `0.7`) — not a copy-paste, per the anti-drift hazard's explicit
instruction.

Compile and confirm (do not assume): `warnings: []`, `entity_count == 62`, `region_count == 9`,
`distinct_populated_factions == 9`.

**Do NOT touch:** Any existing module or world file, including `frontier_extended`'s or
`frontier_living_world`'s own `faction_tension_overrides`/`information_source_profiles`/
`pending_information_responses` blocks (read for rationale only, never copied verbatim); do not create
`data/content/world_compositions/frontier_marches.yaml`.

**Verify:** Manual read of `world_compile_report.json` confirming the 3 numeric facts and 0 warnings.

---

### Step 9 — Wire `frontier_marches` into the corpus-diversity regression guards

**Files:** `tests/unit/worldassembly/test_corpus_diversity.py` — same two dicts as Steps 2/5.

**Change:**
```python
ANCHORED_WORLD_BANDS: dict[str, tuple[int, int | None]] = {
    ...
    "frontier_marches": (51, None),
}
EXPECTED_DISTINCT_POPULATED_FACTIONS: dict[str, int] = {
    ...
    "frontier_marches": 9,   # use the ACTUAL measured value from Step 8
}
```
Band `(51, None)` mirrors `frontier_extended`'s open-ended ">50-entity" tuple since Step 8's measured
entity_count (62) exceeds it too.

**Do NOT touch:** Same guards as Steps 2/5.

**Verify:**
```
pytest tests/unit/worldassembly/test_corpus_diversity.py -k frontier_marches -q
```
(covers entity-band, distinct-factions, hazard-kind, and the slow population-stability test — this is
the authoritative population-stability evidence for this world; no per-world standalone test is needed
since, unlike `hero_guild_routing`, no non-default feature flag is forced on here).

**Depends on:** Step 8.

---

### Step 10 — Calibrate `frontier_marches` (3 seeds × 200t), anchor, and extend `FAC-012`/`INFRA-256`

**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`,
`tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`),
`docs/parity_ledger/faction.yaml` (`FAC-012`), `docs/parity_ledger/infrastructure.yaml` (`INFRA-256`).

**Change (calibration):** Run and anchor identically to Steps 3/6, substituting `frontier_marches`:
```
.venv/bin/python3 tools/calibrate_simq.py --name frontier_marches --seed 42  --ticks 200
.venv/bin/python3 tools/calibrate_simq.py --name frontier_marches --seed 123 --ticks 200
.venv/bin/python3 tools/calibrate_simq.py --name frontier_marches --seed 456 --ticks 200
```
Add `frontier_marches_seed{42,123,456}_200t` to `grade_anchors.json` and `FAST_ANCHOR_KEYS`. Record the
FACTION and INFORMATION grades honestly (this is the "first authored-from-inception" data point at this
scale — do not assume they match `frontier_extended`'s retrofitted grades).

**Change (parity ledger, per Summary resolution #4):** Extend `FAC-012`'s `v2_evidence`/text additively
with one appended clause citing `frontier_marches` as a second, authored-from-inception data point for
`faction_tension_overrides` compile-time plumbing at large scale (mirror exactly how `INFRA-256` has
already been extended twice — one appended clause, no rewording of existing text). Extend `INFRA-256`'s
text with a third additive clause citing `frontier_marches` for `information_source_profiles`/
`pending_information_responses` at this new scale. Do not change `status`, `priority`, `test_path`, or
`divergence_note` on either entry.

**Do NOT touch:** Any other world's `grade_anchors.json`/`FAST_ANCHOR_KEYS` entries; any other field or
entry in `faction.yaml`/`infrastructure.yaml`; `INFRA-237`/`SIMQ-CALIBRATED-001` (routing-specific, not
touched by this ticket since none of the 3 worlds enable `ENABLE_ADVENTURE_ROUTING` — confirm this with
`grep -L ENABLE_ADVENTURE_ROUTING data/worlds/{crowded_frontier,resource_dense_basin,frontier_marches}/world.yaml`
returning all 3 files, i.e. none contain the flag).

**Verify:**
```
pytest tests/simulation_quality/test_grade_regression.py -k frontier_marches -q
```
Manual diff review of `faction.yaml`/`infrastructure.yaml` confirming only the 2 additive clauses
changed.

**Depends on:** Step 8.

---

### Step 11 — Documentation update: `eval_matrix_results.md` and `corpus_tier_taxonomy.md`

**Files:** `docs/simulation_quality/eval_matrix_results.md`, `docs/simulation_quality/corpus_tier_taxonomy.md`.

**Change (`eval_matrix_results.md`):**
1. Add 3 new rows to the "Corpus World-Scale Summary" table (line ~774-785), one per new world, with
   their actual measured seed/entities/regions/resource-nodes/buildings/quests/distinct-populated-factions
   values from Steps 1/4/8's compile reports.
2. Add a new `## Stress-Tier Worlds (TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS)` section (place after
   "Unit-Tier Isolation Worlds", before any closing section), with one `###` subsection per world
   (`crowded_frontier`, `resource_dense_basin`, `frontier_marches`), each containing: the gap it fills
   (cite the gap number from `corpus_tier_taxonomy.md`), its module composition, a `#### 200t (seeds 42 /
   123 / 456)` 10-pillar grade table with actual measured grades from Steps 3/6/10, and (for
   `frontier_marches` only) the bespoke-content rationale from Step 8 and the Step 10 parity-ledger
   extension note. Include Step 7's resource-tag finding (clean pass or gap+follow-up) in
   `resource_dense_basin`'s subsection.

**Change (`corpus_tier_taxonomy.md`):**
1. Correct the stale "no stress-tier world exists yet" sentence at line 108/115 to name the 3 new worlds
   and this ticket.
2. Correct gap-3's text (lines 152-156) to note that `frontier_extended`/`frontier_living_world` already
   carry this content (via the E2E ticket, retrofitted) and that `frontier_marches` (this ticket) is the
   first *authored-from-inception* data point at this scale — do not leave the stale "there's no data
   point" wording standing unqualified.
3. Add 3 new rows to the "Current tier mapping" table (after line 132), tier = `Stress`, citing this
   ticket and the gap each fills.

**Do NOT touch:** Any other section or existing sentence in either file — both changes are additive/
corrective only, scoped exactly to the staleness investigation.md flagged. Do not touch the "9 existing
worlds" End-to-end/Regression rows, the Unit-tier table, or the AGENCY Cross-World Design Note.

**Verify:** Manual diff review — `eval_matrix_results.md` gains 3 table rows + 1 new section;
`corpus_tier_taxonomy.md`'s only changes are the 2 corrected sentences + 3 new table rows.

**Depends on:** Steps 1-10 (needs every actual measured value).

---

### Step 12 — Full-corpus regression sweep and index refresh

**Files:** none (verification-only step).

**Change:** Run, in order:
```
pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow" -q
pytest tests/unit/worldassembly/test_corpus_diversity.py -k "crowded_frontier or resource_dense_basin or frontier_marches" -q
pytest tests/unit/worldassembly/test_assembly.py -q
pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/content/test_catalog.py tests/unit/content_semantics/test_semantics.py -q
pytest tests/unit/strategic/test_opportunities.py -q
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
pytest tests/simulation_quality/test_grade_regression.py -q
pytest tests/unit/faction/test_diplomacy.py -q
python3 tools/evaluate_simq.py --dry-run
make knowledge-index-update
```
Confirm `tools/evaluate_simq.py --dry-run` exits 0 with 0 regressions across the full existing corpus
(not just the 3 new worlds). Confirm `grade_anchors.json` gained exactly 9 new keys (55 → 64 total).
Confirm `ANCHORED_WORLD_BANDS`/`EXPECTED_DISTINCT_POPULATED_FACTIONS` each gained exactly 3 new keys and
no existing key's value changed.

**Do NOT touch:** Nothing is edited in this step — final verification gate only.

**Verify:** All commands exit 0 / show 0 regressions / show the expected +9 anchor-key delta.

**Depends on:** All prior steps.

## Scope Guards

- Do not touch any of the 9 existing non-stress worlds' `world.yaml`, `world_compile_report.json`, or
  `grade_anchors.json`/`FAST_ANCHOR_KEYS` entries, or their AGENCY/any-pillar grades.
- Do not reverse or reword the AGENCY-DA ruling or any of its existing byte-identical sentences in
  `eval_matrix_results.md` or the parity ledger.
- Do not author any new module in `data/content/world_modules/` — all 3 worlds are built entirely from
  existing catalog modules (UQ-1 resolved: catalog-only).
- Do not compose `bandit_road_trade_pressure` + `scalable_bandit_camp`, or `wolf_den_near_forest` +
  `nomadic_herd`, in any of the 3 worlds — both pairs collide on region id and will raise `ValueError`.
- Do not use `ruins_mystery_quest`'s `haunted_battlefield` variant — use `undead_battlefield` (the
  pre-fixed, `hazard_kind`-complete variant) wherever this region/faction is needed.
- Do not edit `data/content/world_compositions/{world}.yaml` for any of the 3 new worlds — only
  `data/worlds/{world}/world.yaml` is authoritative.
- Do not assume `moon_cult`/`dwarven_mine_clan` count toward `distinct_populated_factions` — neither
  module using them (`moon_cult_ruins`, and `old_mine_resource_loop`'s declared-but-unpopulated
  `dwarven_mine_clan`) is used in a way that would incorrectly inflate the count; `old_mine_resource_loop`
  is used in `resource_dense_basin`/`frontier_marches` but its only actually-populated faction is
  `wild_beast_pack` (already counted from `wolf_den_near_forest` in `frontier_marches`, or newly counted
  in `resource_dense_basin`) — verify against the compiled report, not the module's `factions:` list.
- Do not add `faction_tension_overrides`/`information_source_profiles` content to `crowded_frontier` or
  `resource_dense_basin` — per `corpus_tier_taxonomy.md`'s tier-purity rule, these two worlds' primary
  justification is scale, not Pattern-6 richness; only `frontier_marches` (gap c) gets this content.
- Do not silently reuse `frontier_extended`'s, `frontier_living_world`'s, or `swamp_border_world`'s exact
  `faction_tension_overrides`/`information_source_profiles` values for `frontier_marches` — Step 8's
  content is independently bespoke (different tension pair, different information subject/region/
  certainty), and this must be verifiable by diff, not asserted.
- Do not touch `data/content/world/resources.yaml` speculatively — only edit it if Step 7's investigation
  confirms a real gap (and even then, this ticket only documents/flags it if the fix would touch shared
  catalog content beyond a narrow, confirmed case — mirror the `hero_guild_routing` precedent exactly).
- Do not add a new standalone population-stability test file — none of the 3 worlds force a non-default
  feature flag on, so the existing generic `test_population_stability` guard (via `ANCHORED_WORLD_BANDS`
  membership) is sufficient authoritative evidence, unlike `hero_guild_routing`'s ON-flag case.
- Do not touch `INFRA-237`/`SIMQ-CALIBRATED-001` (routing-specific parity entries) — none of the 3 worlds
  enable `ENABLE_ADVENTURE_ROUTING`.
- Do not run `pytest tests/` in full, and do not use `make evaluate --dry-run` (the double `--dry-run`
  no-ops silently under GNU Make per the E2E ticket's documented trap) — use
  `python3 tools/evaluate_simq.py --dry-run` directly.

## Dependency Map

- Steps 1-3 (`crowded_frontier`): Step 2 depends on Step 1; Step 3 depends on Step 1; Steps 2 and 3 are
  independent of each other.
- Steps 4-7 (`resource_dense_basin`): Step 5 depends on Step 4; Step 6 depends on Step 4; Step 7 depends
  on Step 4; Steps 5, 6, 7 are independent of each other.
- Steps 8-10 (`frontier_marches`): Step 9 depends on Step 8; Step 10 depends on Step 8; Step 9 and the
  calibration half of Step 10 are independent of each other; the parity-ledger half of Step 10 needs no
  other step's output beyond Step 8's world existing.
- The three per-world groups (1-3, 4-7, 8-10) have no dependency on each other and may be done in any
  order.
- Step 11 depends on all of Steps 1-10 (needs every actual measured value for doc tables).
- Step 12 depends on all prior steps (final gate).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Many-factions/small-map world exists, 6-9 distinct populated factions confirmed numerically | Steps 1-2 | `test_distinct_populated_factions[crowded_frontier]` |
| Resource-saturated/small-map (or sparse/large-map) world exists, choice justified | Steps 4-5 (choice justified in Summary + Step 4) | `test_entity_count_band[resource_dense_basin]`, manual compile-report read |
| Large-scale FACTION/INFORMATION world exists, bespoke content | Steps 8-10 | `test_hazard_kind_completeness[frontier_marches]`, `pytest tests/unit/faction/test_diplomacy.py`, manual diff of `world.yaml` |
| All 3 worlds compile 0 warnings, population-stable (>=60%) through 200-300 ticks | Steps 1, 4, 8 (compile); Steps 2, 5, 9 (stability guard) | `test_population_stability[<world>]` for each of the 3 worlds |
| All 3 worlds have 3-seed grade-anchor entries | Steps 3, 6, 10 | `pytest tests/simulation_quality/test_grade_regression.py -k "<world>"` for each |
| `eval_matrix_results.md` updated with stress-tier grade tables | Step 11 | Manual diff review |
| `make evaluate --dry-run` exits 0 with 0 regressions | Step 12 | `python3 tools/evaluate_simq.py --dry-run` |

## Anti-Drift Notes

- **UQ resolution 1 (region-count reading of "small-map")**: `crowded_frontier`'s 38 entities is larger
  than `wilderness_survival`(11)/`sandbox_world`(18) — this is the necessary and accepted cost of the
  region-count reading, not an error to "fix" by shrinking the composition further (no catalog
  combination achieves 6+ factions at under ~20 entities; see Summary resolution #1).
- **UQ resolution 2 (gap c reframing)**: `frontier_marches` is not "the first" data point at this scale —
  it is the first *authored-from-inception* one, distinct from `frontier_extended`/`frontier_living_world`'s
  retrofitted content. Step 11's doc language must say this explicitly, not silently reuse "first data
  point" phrasing.
- **UQ resolution 3 (test-list wiring)**: adding a world to `ANCHORED_WORLD_BANDS` alone cascades it into
  `POPULATION_STABILITY_WORLDS` (computed from `.keys()`) and `test_hazard_kind_completeness`
  (parametrized over the same dict) — do not also hand-edit `POPULATION_STABILITY_WORLDS`'s list literal,
  that would double-count the world in its parametrize list.
- **Region-id-collision guard**: `ValueError` on a duplicate region id (if it should ever occur through a
  future edit) is correct resolver behavior, not a bug to fix by renaming a region id in shared catalog
  content — the fix is always choosing a non-colliding module pair, which this plan's 3 compositions
  already do.
- **`old_mine_resource_loop` reuse across two worlds**: it appears in both `resource_dense_basin` and
  `frontier_marches`. In `resource_dense_basin` it contributes a *new* faction count (`wild_beast_pack` is
  new there, since `wolf_den_near_forest` is not composed); in `frontier_marches` it does *not* add a new
  distinct faction (since `wolf_den_near_forest` already contributes `wild_beast_pack`) — the
  `distinct_populated_factions` numbers in this plan's table already account for this; do not double-count
  `wild_beast_pack` in `frontier_marches`'s expected count of 9.
- **Tier-purity discipline**: resist the temptation to add FACTION/INFORMATION content to
  `crowded_frontier`/`resource_dense_basin` just because their faction/module mixes could support it —
  their tier justification is scale alone, per `corpus_tier_taxonomy.md`'s explicit rule that a world
  should not straddle tiers.
- **Honest-grade discipline**: none of the 3 new worlds' calibration grades should be assumed in advance
  (matching every prior corpus-authoring ticket's discipline) — record whatever `calibrate_simq.py`
  actually measures, and trace (not silently "fix") any anomalously low grade before treating it as a
  scoring defect, per the stasis-collapse precedent's method (even though none of these worlds are
  routing-active, the same "measure honestly, trace before assuming a bug" discipline applies to any
  pillar).

## Deviations

1. **Step 4's resource-node-density arithmetic was wrong; corrected against the authoritative
   metric, not silently kept.** The plan's Summary/Step 4 quote "~37 resource nodes (~12.3/region)"
   for `resource_dense_basin`, derived by summing each resource definition's `count:`/charge field
   across the 3 composed modules (13+14+10). The actual `world_compile_report.json`
   `resource_node_count` field — the same metric `eval_matrix_results.md`'s "Corpus World-Scale
   Summary" table already uses for every other world, confirmed by cross-checking
   `swamp_border_world`'s own "1.75/region" claim against its compile report — measures **7**
   distinct resource-node definitions (2 in `hometown`, 3 in `old_mine`, 2 in `orc_stronghold`), not
   37. Density is therefore ~2.33 nodes/region, not ~12.3/region. This is still the corpus's new
   maximum (prior max: `swamp_border_world` at 1.75/region), so gap (b)'s justification is
   unaffected — only the specific number was wrong. Corrected in
   `docs/simulation_quality/eval_matrix_results.md`'s scale-summary table (with an explanatory note)
   and in the ticket's Implementation Notes; `ANCHORED_WORLD_BANDS`/`EXPECTED_DISTINCT_POPULATED_FACTIONS`
   were unaffected since those only ever used `entity_count`/`distinct_populated_factions`, both of
   which matched the plan exactly.

2. **Step 8/10 required a new calibration profile file the plan did not call for.**
   `frontier_marches`'s first calibration pass measured `INFORMATION=C`/`event_count=0` despite
   `AuthoritativeState.pending_information_responses` compiling correctly (verified directly: 1
   well-formed entry, `actor_id=9`, correct subject). Traced to `ENABLE_BELIEF_ASSIMILATION`
   defaulting OFF (`src/domains/optimization/feature_flags.py:18`) with no
   `config/simulation_quality/profiles/frontier_marches.yaml` to turn it ON via
   `calibrate_simq.py`'s `_resolve_profile()` — every other `information_source_profiles`-bearing
   world in the corpus has exactly such a profile file, and this world was missing the equivalent.
   Added `config/simulation_quality/profiles/frontier_marches.yaml`
   (`feature_flags: {ENABLE_BELIEF_ASSIMILATION: "ON"}`, mirroring `frontier_extended.yaml`
   byte-for-byte) and recalibrated all 3 seeds; INFORMATION moved to B/event_count=1 in all 3,
   matching the established C→B pattern the other 8 worlds already show. This was traced as a
   missing-infrastructure gap, not treated as a scoring-formula defect, per the plan's own
   "honest-grade discipline" instruction. No other step's guidance was affected.

3. **Step 7's contingent gap check found a real gap, per the plan's own explicit branch.** The
   plan's Step 7 was written as "add a test only if a real gap is found." `orc_stronghold` (one of
   `resource_dense_basin`'s 2 new regions) has no resource kind with a matching
   `source_region_tags` entry — a genuine, pre-existing registry-omission gap (same class as the
   `hero_guild_routing`/`mountain_pass_zone` precedent), left unfixed per the plan's own
   instruction not to touch the shared catalog file speculatively. Two tests were added instead of
   the plan's anticipated "at most one" (`test_resource_opportunities_old_mine_iron_vein` for the
   clean `old_mine` pass, `test_resource_opportunities_orc_stronghold_tag_gap` for the documented
   gap) — both outcomes needed a test since Step 7 asked for verification of *both* new regions,
   not just the one where a gap might exist.
