---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS
phase: done
date: 2026-07-03
tags: [simulation-quality, worldbuilding, calibration, content, test-suite]
---

# TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS

## Title
Diversify the SimQ calibration world corpus — more entity/resource scale and content variety, not just more seeds of the same worlds

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260702-SIMQ-EVAL-MATRIX` already extended the calibration corpus from single-seed point
estimates to a multi-seed × multi-tick matrix — but explicitly scoped that as more seeds/ticks of
the *same four worlds already producing signal* (`dungeon_crawl`, `urban_political`,
`simq_routing_test`, `sandbox_world`), and explicitly marked "worlds without confirmed non-C
signal in default mode" as out of scope. `data/worlds/` already has 10 compiled worlds and
`data/content/world_modules/` has 20 modules, but several (`frontier_extended`,
`frontier_living_world`, `generated_frontier_3_42`, `highland_traverse`, `swamp_border_world`,
`wilderness_survival`) are thin in the calibration corpus — some terminate early due to P2-B
(entity attrition outpaces spawn rate) at higher entity counts, per `docs/plans/audit_fix_plan.md`.

Per 2026-07-03 user direction: instead of continuing to seed FACTION/INFORMATION-style content
into just 1-2 more of the *existing* worlds, invest in genuinely broader world diversity — varied
entity counts, resource-node density/types, region counts, and content-module combinations — so
the calibration corpus functions as a real test suite across world *shapes*, not just more runs of
the same handful of world shapes. This is a bigger, longer-horizon investment than the FACTION/
INFORMATION single-world activations.

## Scope
1. Audit the current 10 worlds in `data/worlds/` and 20 modules in `data/content/world_modules/`
   for actual diversity: entity count range, resource node count/type range, region count range,
   which of the 10 SimQ pillars each world can even theoretically produce signal for (some worlds
   are structurally blind to certain pillars, e.g. `sandbox_world` is combat-only per
   `docs/audits/D20_simq_integration.md`).
2. Identify concrete gaps: e.g. no small-entity-count world, no world combining FACTION-relevant
   content with INFORMATION-relevant content, no world at a size between `sandbox_world` (small)
   and `frontier_extended`/`frontier_living_world` (56/46 entities, early-terminating per P2-B).
3. Author 2-4 new world compositions (or substantially extend existing thin ones) filling the
   identified gaps — using existing catalog content/modules where possible, new module content
   only where a genuine content gap blocks a useful scenario shape.
4. If P2-B (spawn/attrition imbalance) is still blocking the existing larger worlds from completing
   full-length calibration runs, either fix it as part of this ticket or file it as an explicit
   sub-blocker (do not silently work around it by only adding small worlds).
5. Add the new/extended worlds to the calibration corpus (`grade_anchors.json`,
   `test_grade_regression.py`) following the pattern `TCK-20260702-SIMQ-EVAL-MATRIX` established.
6. Update `docs/simulation_quality/eval_matrix_results.md` and
   `docs/audits/D20_simq_integration.md` with the expanded corpus's grade distributions.

## Out of Scope
- Re-running more seeds/ticks of the 4 already-well-covered worlds (that's
  `TCK-20260702-SIMQ-EVAL-MATRIX`'s completed scope)
- Fixing any SimQ pillar's underlying scoring/emission logic discovered to be broken by the new
  worlds (file a follow-up ticket instead, per the pattern in
  `TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC`)
- Seeding FACTION/INFORMATION-specific content (tension overrides, information source profiles)
  into the new worlds — that's a natural follow-on once this ticket's worlds exist, not part of
  this ticket's own scope

## Acceptance Criteria
- [x] Current corpus diversity audited and gaps documented (entity/resource/region range, per-world
      pillar-reachability) — see `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md`
- [x] At least 2 new or substantially-extended world compositions exist, filling identified gaps —
      5 existing worlds (`frontier_extended`, `frontier_living_world`, `wilderness_survival`,
      `highland_traverse`, `swamp_border_world`) substantially extended (hazard-kind fix + recompile
      + anchor); 0 brand-new compositions authored (evidence-based decision, see plan.md Step 4)
- [x] P2-B (spawn/attrition imbalance) status re-confirmed for any world this ticket touches —
      **RESOLVED**: code inspection confirms the two-tier cadence is intact; the early-termination
      symptom previously attributed to P2-B was re-attributed to a separate stale-compile/hazard-kind
      bug, fixed in this ticket (see `docs/plans/audit_fix_plan.md` P2-B section)
- [x] New worlds added to `grade_anchors.json`/`test_grade_regression.py` following the established
      pattern — 15 new entries, `FAST_ANCHOR_KEYS` updated
- [x] `docs/simulation_quality/eval_matrix_results.md` and `docs/audits/D20_simq_integration.md`
      updated with the expanded corpus
- [x] `make evaluate --dry-run` exits 0 (0 regressions on existing worlds) — 390 pillars checked,
      0 regressions, 1 pre-existing/unrelated missing-calibration-data skip (`urban_political_seed42_200t`)

## Related Tickets
- TCK-20260702-SIMQ-EVAL-MATRIX (done) — established the seed/tick matrix pattern this ticket
  extends to new world shapes instead
- TCK-20260703-SIMQ-UPLIFT3-FAST-CALIBRATE — should land first so validating this larger corpus
  doesn't take hours
- TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW — benefits from this ticket's expanded corpus existing

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/audits/D20_simq_integration.md`
- `docs/plans/audit_fix_plan.md` — P2-B (spawn cadence tuning), P2-C (archetype distribution,
  already resolved)
- `docs/guides/content_authoring.md` — world/composition authoring process

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-EVAL-MATRIX/` (if present)

## Related Code Areas
- `data/worlds/` — existing compiled worlds
- `data/content/world_modules/` — existing content modules
- `src/world/spawn.py`, `src/world/spawn_config.py` — spawn cadence (P2-B)
- `tools/calibrate_simq.py`, `tests/simulation_quality/fixtures/grade_anchors.json`,
  `tests/simulation_quality/test_grade_regression.py`

## Assumptions / Open Questions
- UQ-1: Should new worlds be entirely new compositions, or substantial rework of the existing
  early-terminating ones (`frontier_extended`, `frontier_living_world`)? Investigate P2-B's actual
  current status first (per `docs/plans/audit_fix_plan.md`'s 2026-07-03 refresh, this was marked
  "unverified" — confirm before deciding whether new worlds or fixing existing ones is the right
  path).
- UQ-2: What is "good enough" for this test suite — is there a target number of worlds, or a target
  coverage matrix (e.g. every pillar reachable by at least 2 worlds of different sizes)? This
  should be decided during investigation/planning, not left implicit.

## Implementation Notes

Followed `staging_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/plan.md` exactly, step by step.

**Step 1 — hazard_kind/hazard_immunities content fix (7 modules, 6 factions):** Added
`hazard_kind: "NATURAL_TERRAIN"` to `orc_clan_territory` (`orc_stronghold`),
`bandit_road_trade_pressure` (`bandit_road`), `old_mine_resource_loop` (`old_mine`),
`forest_warden_grove` (`sacred_grove`, `deep_forest`), `nomadic_herd` (`near_forest`, `wolf_den`),
`sunken_swamp_border` (`swamp_border_territory`); added `hazard_kind: "UNDEAD_CORRUPTION"` (new
value) to `undead_battlefield` (`haunted_battlefield`). Added matching `hazard_immunities` to the
native faction only in `data/content/social/factions.yaml`: `orc_clan`, `bandit_company`,
`forest_wardens`, `spirit_court`, `undead_remnants`, `swamp_tribe`. Deliberately did NOT add
immunity to `merchant_league` (hostile/transient encounter target in `bandit_road_trade_pressure`,
per the original ticket's AC3 guard) or to non-populating faction listings (`spirit_court` in
`undead_battlefield`, `wild_beast_pack` in `sunken_swamp_border`).

**Step 2 — recompiled all 8 stale worlds:** `simq_routing_test`, `dungeon_crawl`,
`generated_frontier_3_42`, `frontier_extended`, `frontier_living_world`, `swamp_border_world`,
`highland_traverse`, `wilderness_survival` — each `resolve` + `compile --seed <world's own
generation_seed> --from-resolved`. Verified `hazard_kind` present on every non-zero-hazard region
and `provenance_manifest.json::created_at` postdates 2026-07-01 for all 8.

**Step 3 — population-stability re-verification:** Drove `frontier_extended`,
`frontier_living_world`, `wilderness_survival`, `highland_traverse`, `swamp_border_world` via
`Kernel.tick_once()` for 300 ticks at seed 42, sampling `alive_count` at 50-tick checkpoints. All 5
held ≥60% of starting entity count at every checkpoint (frontier_extended: 91.1%→85.7%;
frontier_living_world: 89.1% flat; wilderness_survival: 100% flat; highland_traverse: 100%→61.1%;
swamp_border_world: 100% flat) — a materially different result from the pre-fix
23% (13/56) collapse-by-tick-50 documented in investigation.md Finding 3.

**Step 4a — existing-anchor drift check (dungeon_crawl 10 keys, simq_routing_test 3 keys):**
Confirmed the exact 13 existing anchor keys from `grade_anchors.json` (not assumed). Refreshed all
10 `dungeon_crawl` calibration reports (200/500/1000/2000t x seeds 42/123/456, with duplicates
collapsed correctly per the documented key set) and diffed against pre-refresh committed values:
**8 of 10 keys drifted** — `dungeon_crawl_seed42_200t` (WORLD A→B); `dungeon_crawl_seed{42,123,456}_500t`
(COMBAT A→B, PROGRESSION A→B, NARRATIVE B→A); `dungeon_crawl_seed{42,456}_1000t` (COMBAT A→B,
NARRATIVE B→A); `dungeon_crawl_seed123_1000t` (COMBAT A→B only); `dungeon_crawl_seed42_2000t`
(NARRATIVE B→A only). `dungeon_crawl_seed123_2000t` and `dungeon_crawl_seed456_2000t` showed **no
drift**. All 8 drifted keys were attributed to the Step 1a/Step 2 hazard-kind recompile of
`old_mine_resource_loop`/`old_mine_spider_cluster` changing survival/engagement dynamics (not a new
regression) and updated in place in `grade_anchors.json`, with the attribution documented in
`docs/simulation_quality/eval_matrix_results.md`.

Attempting to refresh `simq_routing_test`'s 3 keys (`ENABLE_ADVENTURE_ROUTING=ON`,
500t, seeds 42/123/456) hit an unrelated crash: `KeyError: Resource not found in
ResourceRegistry: STONE`, raised from `ResourceOpportunityProvider.get_opportunities`
(`src/world/providers/resources.py:60`) when `AdventureDecisionPhase` walks a resource node whose
`kind` was dynamically generated as `"STONE"`/`"WOOD"`/`"IRON"` by
`ResourceEcologyService.process_ecology` (`src/world/ecology.py:124`, an always-on
"governance_ecology" phase, not gated by `ENABLE_WORLD_EMERGENCE`). `ResourceRegistry`'s catalog
(`data/content/world/resources.yaml`) has no `STONE`/`WOOD`/`IRON` entries at all — only
lowercase, differently-named ids (`wood_node`, `iron_vein`, etc.) — so this is a genuine content/
registry gap in the dynamic resource-generation path, unrelated to `hazard_kind`.
**Verified via `git stash` bisection that this crash reproduces identically with the ORIGINAL
(pre-Step-1) module/faction content** — i.e. it is 100% pre-existing and NOT introduced by this
ticket's Step 1/2 changes. `simq_routing_test`'s 3 pre-existing anchor entries are left unchanged
(not silently marked verified); a follow-up ticket is recommended for the `ResourceRegistry` gap
(`layer: world` or `layer: engine`, P1 — it blocks any future re-calibration of
`ENABLE_ADVENTURE_ROUTING`-gated worlds run long enough to trigger dynamic ecology resource spawns).

**Step 4 — anchored 5 existing worlds:** `frontier_extended` (56 entities/10 regions),
`frontier_living_world` (46/7), `wilderness_survival` (11/4), `highland_traverse` (18/5),
`swamp_border_world` (26/4) — 3 seeds x 200t each, 15 new `grade_anchors.json` entries. All show
uniform C on AGENCY/FACTION/INFORMATION/SOCIAL (expected, structural, out of scope) and genuine
COMBAT/NARRATIVE/PROGRESSION/WORLD signal. `generated_frontier_3_42` was recompiled (Step 2, stale)
but deliberately NOT anchored (scope boundary — its `moon_cult_ruins` module's own missing
`hazard_kind` gap is a separate unit of investigation, filed as a follow-up recommendation rather
than expanded into this ticket).

**Step 5 — tests:** `FAST_ANCHOR_KEYS` gained the 15 new keys. New
`tests/unit/worldassembly/test_corpus_diversity.py` (16 tests): entity-count band, population
stability (>=60% floor, 300 ticks, `@pytest.mark.slow`), hazard-kind completeness, and
module-family-anchored guard (asserts the 10 newly-anchored modules appear in an anchored world's
module list, and `moon_cult_ruins` remains the sole unanchored module).
`tests/integration/worldassembly/test_real_content_world_modules.py::MODULE_MATRIX` already
contained all 7 touched modules — no edit needed (content-value change only).

**Step 6 — docs:** `docs/mechanics/05_world_evolution.md` §3 — added `"UNDEAD_CORRUPTION"` to the
example list with a production-vs-synthetic-test-only note, and a staleness-note addendum
documenting this ticket's corpus-wide extension. `docs/parity_ledger/world_dynamics.yaml` —
WORLD-029/WORLD-060 `v2_evidence` extended, `test_path` gained
`tests/unit/worldassembly/test_corpus_diversity.py`. `docs/simulation_quality/eval_matrix_results.md`
— new drift-check NOTE block, updated `dungeon_crawl` grade tables (500t/1000t/2000t), new
"Newly-Anchored Worlds" section with full per-seed tables for the 5 worlds, updated top-of-doc and
"Zero-Pillar World Confirmation" framing. `docs/audits/D20_simq_integration.md` — corpus-size
reference updated (13-run → 28-run: 13 refreshed + 15 new), new "5 newly-anchored worlds" table,
State/Audit-date metadata updated.

**Step 7 — `docs/plans/audit_fix_plan.md` P2-B correction:** Added a RESOLVED note to the P2-B
section distinguishing the (resolved) urban_political late-run mechanism from the (separately
fixed) early-tick stale-compile symptom; updated the 13-run corpus table's 5 affected rows (removed
`†`/`‡` early-termination markers, replaced with fresh 200t seed-42 grades and a pointer note);
superseded Findings 5/6's P2-B misattribution with a correction note; updated the Summary Table's
P2-B row to RESOLVED; removed P2-B from both "genuinely open" mentions in the Suggested Fix Order
section. Did not touch P2-D or P2-K (unrelated, out of scope).

**Step 8 — test gate:** All commands from the corrected Step 8 passed — see Test Summary below.
`make knowledge-index-update` run after docs/ changes (4 files re-embedded, 1843 cached).

## Test Summary
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` — 29 passed, 1 skipped
  (`urban_political_seed42_200t` — pre-existing missing calibration data, unrelated to this ticket),
  11 deselected
- `pytest tests/simulation_quality/test_grade_regression.py -m "slow"` — 11 passed, 30 deselected
- `pytest tests/integration/worldassembly/test_real_content_world_modules.py` — 6 passed
- `pytest tests/unit/world/test_spawn_cadence.py` — 16 passed (P2-B regression guard, untouched code)
- `pytest tests/unit/worldassembly/test_corpus_diversity.py` (new, both marks together) — 16 passed
- `pytest tests/unit/content/test_catalog.py tests/unit/content_semantics/test_semantics.py` — 20 passed
- `make evaluate` — 390 pillars checked, 0 regressions, 1 pre-existing/unrelated missing-data skip

## Files Changed
- `data/content/world_modules/orc_clan_territory.yaml`
- `data/content/world_modules/bandit_road_trade_pressure.yaml`
- `data/content/world_modules/old_mine_resource_loop.yaml`
- `data/content/world_modules/forest_warden_grove.yaml`
- `data/content/world_modules/undead_battlefield.yaml`
- `data/content/world_modules/nomadic_herd.yaml`
- `data/content/world_modules/sunken_swamp_border.yaml`
- `data/content/social/factions.yaml`
- `data/worlds/{simq_routing_test,dungeon_crawl,generated_frontier_3_42,frontier_extended,frontier_living_world,swamp_border_world,highland_traverse,wilderness_survival}/resolved/*`
  and `world_compile_report.json` (regenerated)
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py`
- `tests/unit/worldassembly/test_corpus_diversity.py` (new)
- `docs/mechanics/05_world_evolution.md`
- `docs/parity_ledger/world_dynamics.yaml`
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/audits/D20_simq_integration.md`
- `docs/plans/audit_fix_plan.md`

## Completion Summary
Diversified the SimQ calibration corpus from 25 to 40 anchor entries (28 distinct run_keys
including the 13 pre-existing dungeon_crawl/simq_routing_test keys) by fixing a corpus-wide
hazard-kind content gap (7 modules, 6 factions), recompiling 8 stale worlds, verifying population
stability, and anchoring 5 previously-unanchored worlds (frontier_extended, frontier_living_world,
wilderness_survival, highland_traverse, swamp_border_world) — closing the entity-count-band and
module-family coverage gaps `investigation.md` identified, without authoring any new world
compositions. Re-attributed the `frontier_extended`/`frontier_living_world`/`wilderness_survival`
early-termination symptom from P2-B (now confirmed resolved) to the actual root cause (stale
compile / missing hazard_kind), correcting `docs/plans/audit_fix_plan.md`. Discovered and
documented (but did not fix, per scope) a pre-existing, unrelated `ResourceRegistry: STONE` crash
blocking `simq_routing_test`'s `ENABLE_ADVENTURE_ROUTING` recalibration — confirmed via git-stash
bisection to predate this ticket's changes; recommend a follow-up ticket.
