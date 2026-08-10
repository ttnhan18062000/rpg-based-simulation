---
status: historical
layer: observability
authority: P1
audience: developer
tags: [audit, simulation-quality, simq, integration, observability, event-bus]
---

# D20 — Simulation Quality Module Integration

## Summary

SimQ was audited 2026-06-30 and found fully built but disconnected from the kernel — zero events
reached the scoring hub despite a complete, unit-tested pillar-scoring implementation. All three
wiring gaps were fixed the same day. Across 4 "uplift" batches and 2 corpus-expansion epics
(2026-07-02 through 2026-07-11), the module was calibrated to a 71-scenario, 17-world corpus, 81 of
82 scored event types were wired to real engine emissions, and every P1/P2 action item was closed.
This document is the historical record of that work — current corpus/grade tables live in
`docs/simulation_quality/eval_matrix_results.md`; this doc preserves *why* things are the way they
are, not the live numbers.

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | A — Simulation Quality |
| **State** | `done` — see Module Health below for the current-state summary |
| **Impact** | 4 / 5 |
| **Interest** | 5 / 5 |
| **Priority** | 9 |
| **Method** | run-sim + code-read |
| **Audit history** | 2026-06-30 (original, found broken) → 2026-07-01 (wiring fixed, re-verified) → 2026-07-02/07-11 (4 uplift batches + 2 corpus epics, see Batch History below) → 2026-07-10 audit run `SIMQ-AUDIT-20260710T020542Z`: `no_regression` → 2026-08-07 hand-orchestrated audit (post `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`/`-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP`/`-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP`, 79-scenario full corpus): `no_regression` for the push migration itself (AGENCY 79/79 clean); NARRATIVE + PROGRESSION anchors recalibrated (127 pillar entries, 2 already-disclosed causes — see `docs/simulation_quality/current_state.md`'s "2026-08-07 session summary"); 26 COMBAT + 1 COGNITION + 1 SOCIAL score-tolerance drift left unresolved, flagged for a follow-up session → 2026-08-10 audit run `SIMQ-AUDIT-20260810T032558Z` (post `TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`, 8-scenario scoped re-run of `urban_political`/`frontier_extended`/`frontier_living_world`'s fast tier — full-corpus re-run timed out at 590s, a real instance of the chronic tick-budget condition `docs/audits/D06_longrun_health.md` already flags): `regression` verdict — COMBAT anchor C→A/S confirmed and updated in place for 7 run_keys (real cause: role/faction mistagging fix, not the 2026-08-07 finding's own "COMBAT drops toward dormant" direction — this is the opposite, a real unlock, not the same phenomenon). Also surfaced a SEPARATE, broader SOCIAL/ECONOMY/PROGRESSION score-tolerance drift (10 SOCIAL failures across 3 worlds) — NOT simply the 2026-08-07 finding's own narrow "1 SOCIAL" single-draw case (this is 10x the scale) — left un-anchored, disclosed, real cause not yet confirmed, handed to a dedicated follow-up ticket rather than assumed → `TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION` (2026-08-10): confirmed and closed. Two mechanisms, both tracing to the same role/faction fix: PROGRESSION via `CombatRewardClassificationService` (role-keyed reward classification directly changes `xp_granted`); SOCIAL/ECONOMY/COGNITION/AGENCY via a cascading behavioral change (scorers confirmed not to read role/faction directly — correctly-tagged monsters now engage/die differently from tick 1, altering deterministic RNG-consumption order and population composition for the rest of each run). The 2026-08-07 watchdog-throttle hypothesis was directly checked, not assumed: 3 independent re-runs of `urban_political_seed42_500t` showed the watchdog firing repeatedly from tick 25 yet produced a bit-identical SOCIAL score all 3 times, ruling that mechanism out. `grade_anchors.json` recalibrated across 17 run_keys/31 fields total (including 2 extra keys found while regenerating a missing guard-test fixture). Post-fix fast-tier sweep: 35 passed, 15 failed (all pre-existing `[known tick_budget: ...]`-annotated noise), 20 skipped, 18 deselected — zero unexplained failures |

**Related dimensions:**

| Dimension | Relationship |
|---|---|
| D03 (Behavioral Emergence) | Prior run observations that SimQ is now meant to quantify |
| D06 (Long-Run Health) | SimQ should replace manual metric-window inspection for health monitoring |
| D04 (Balance & Tuning) | Calibration of SimQ thresholds is a prerequisite for D04 tuning |

---

## Original Finding (2026-06-30): Wiring Gap — *Resolved same day*

Both 200-tick seeds ran to completion, but the SimQ hub received zero events — all 10 pillars
graded C(0.0), not from degenerate behavior but because nothing reached the scorers. The
infrastructure (10 pillar scorers, `QualityHub`, persistence, REST API) was fully built and
unit-tested; only the event-delivery path was disconnected.

```
Kernel.tick_once() → EventExtractor → EventRecorder.record() → BoundedObservabilityQueue
  → QueueDrainWorker → [quality_fn, if registered] → QualityHub.on_envelope()
```

`QueueDrainWorker` already had a `quality_fn` callback slot; nothing populated it.

| Gap | Location | Description | Fix |
|---|---|---|---|
| G1 | `src/engine/kernel.py` | `EventRecorder`'s `QueueDrainWorker` created without `quality_fn` | `TCK-20260630-SIMQ-WIRE-KERNEL` — pass `quality_fn=hub.on_envelope` at kernel init |
| G2 | `src/api/server.py` | `set_quality_hub()` defined but never called at server startup | `TCK-20260630-SIMQ-WIRE-SERVER` — call it in the `lifespan` handler after manager start |
| G3 | `src/simulation_quality/feed.py` | `InProcessQualityFeed` created a second, competing `QueueDrainWorker` on the same queue | `TCK-20260630-SIMQ-WIRE-KERNEL` — refactored to lifecycle-only, no longer creates a worker |

---

## Verification (2026-07-01)

Re-ran the same world/seeds/ticks after the wiring fix: all three gaps resolved, 81 event types
now emitted, all 10 pillar grades landed B, and final state hashes were bit-identical to the
pre-fix run — confirming the fix changed nothing about simulation determinism, only observability.

**`sandbox_world` schema migration** (`TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE`, same session):
migrated from the retiring `worldtemplate.v1` schema (fully removed shortly after by
`TCK-20260701-WORLDTEMPLATE-REMOVE`, once this was the last world on it) to `worldcomposition.v1`
(`frontier_village_core` + `wolf_den_near_forest`), moving from 23 flat-stat entities to 18
catalog-resolved entities. Compile validation was clean (zero issues); calibration anchors were
regenerated to match. The wolf-population extinction symptom persisted post-migration as expected
— its root cause (hazard-drain not respecting native fauna immunity) was tracked separately and
fixed the same week (`TCK-20260701-HAZARD-NATIVE-IMMUNITY`, `TCK-20260701-HAZARD-KIND-RESOLVER-GAP`,
`TCK-20260701-SANDBOX-MONSTER-BALANCE`) — confirmed via 0/5 wolf deaths post-fix across both seeds.

**Emission gap closure** (simq-emit epic, 2026-07-01): 24 of 27 engine emission gaps closed across
5 tickets (`TCK-20260701-SIMQ-EMIT-AGENCY2`, `TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS`,
`TCK-20260701-SIMQ-EMIT-PROGRESSION`, `TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY`,
`TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS`). The remaining 3 turned out not to need engine changes: `social_memory_created`
was re-derived from `EventExtractor` reading `trust_history` deltas directly
(`TCK-20260701-SIMQ-EMIT-SOCIAL-MEM`); `contract_milestone_completed` needed no schema change,
just an `EventExtractor` rule on existing contract-duration fields
(`TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE`); `camp_constructed` has no engine path at all — camps
are pre-placed at world generation, never dynamically constructed — so its scorer entry is
permanently a documented dead event, not a gap (`TCK-20260701-SIMQ-EMIT-CAMP`).

**Loop-detection tuning** (`TCK-20260701-SIMQ-LOOP-WINDOW-TUNE`, 2026-07-02): swept window sizes
{100,150,200,300} — zero grade change across all of them, since event density at 200 ticks (47–287
events depending on world) never fills the window regardless of size. The 200-event/0.70-threshold
defaults were confirmed correct, not a signal-suppression bug; `--window-size`/`--loop-threshold`
CLI overrides were added to `calibrate_simq.py` for future sweeps.

**Structural C-ceiling pillars in `sandbox_world`** (unchanged by the emission fixes, expected):
AGENCY (gated by `ENABLE_ADVENTURE_ROUTING`, off by default — confirmed not a scorer/emitter
defect by `TCK-20260701-SIMQ-AGENCY-ROUTING-DOC`, later DA-ruled archetype-correct corpus-wide by
Batch 2), COGNITION and INFORMATION (require an active self-model/information-seeking loop, not
present in a pure-combat scenario), ECONOMY (no trades/harvesting in scope) and SOCIAL (no
cooperation events in scope). None of these are SimQ scoring gaps — see
`docs/plans/audit_fix_plan.md §Finding 1`.

**Calibration corpus refresh** (`TCK-20260701-SIMQ-CALIBRATE-REFRESH`, 2026-07-02): re-ran
`dungeon_crawl`/`urban_political` post-emit-epic; one real grade shift found (`dungeon_crawl` 200t
PROGRESSION A→B, from the new plateau-detection emitter). `TCK-20260702-SIMQ-EVAL-MATRIX` then
expanded the corpus from 8 to 25 anchor entries (3 seeds × 2-3 tick counts per signal-producing
world, up from mostly single-seed point estimates) — the baseline Batch 3's `WORLD-CORPUS` ticket
later grew further to 40.

---

## Batch History (2026-07-02 → 2026-07-11)

Every batch below closed with 0 regressions on the corpus scope it touched. Ticket-level detail
(root causes, exact evidence) lives in each ticket's own `tickets/done/` record and
`stored_artifacts/`; this table is the index, not the full account.

### SimQ Uplift Batch 1 (2026-07-02)

| Ticket | Change | Outcome |
|---|---|---|
| `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO` | Activated SOCIAL (`ENABLE_SOCIAL_COOPERATION=ON`) in `urban_political`; fixed a silent bug dropping `feature_flags` each tick; fixed `CooperationPhase` storing a non-serializable object in durable state | SOCIAL C→S in `urban_political` |
| `TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY` | Fixed the `normalized_score` formula's tick-dilution artifact (`raw_score / tick_count` → `raw_score / max(floor_tick, last_event_tick)`) | 24 of 25 anchor grades updated; COMBAT/PROGRESSION now hold A at 500t/1000t for `dungeon_crawl` |
| `TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG` | DA ruling: ECONOMY=C and COGNITION=C in `dungeon_crawl` are archetype-correct (no merchant NPCs; all entities in permanent survival mode) | Documentation only |

### SimQ Uplift Batch 2 (2026-07-02 / 2026-07-03)

| Ticket | Change | Outcome |
|---|---|---|
| `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` | DA ruling: AGENCY=C in every non-`simq_routing_test` world is archetype-correct (`AdventureDecisionPhase` is opt-in per world, gated off by default) | Documentation only; closes the AGENCY follow-up without a rollout decision |
| `TCK-20260702-SIMQ-UPLIFT2-FACTION` | `WorldCompiler.compile()` had never constructed `FactionState` for any world. Added `FactionSpec.initial_tension_level` + `faction_tension_overrides` compiler/resolver plumbing; seeded `urban_political` | FACTION C→S/A in `urban_political` |
| `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` | Same compiler-never-constructs-the-field bug class, for `information_source_profiles`. Shipped scaffolding + `ENABLE_BELIEF_ASSIMILATION=ON`, but `InformationBeliefPhase`'s trigger branches were still unreachable | Scaffolding shipped honestly inactive; activation deferred to the next ticket rather than forced |
| `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` | Seeded `pending_information_responses` at compile time, reaching Branch A. Also found and fixed a real kernel bug: `Kernel._phase_advancement()` compared Resolution-phase-stamped properties against the wrong tick, so `belief_assimilated`/`calamity_spawned`/`GovernorModeChanged` could never fire through the real tick loop | INFORMATION C→B in `urban_political`; COGNITION C→B as a side effect (shared scorer signal) |

### SimQ Uplift Batch 3 (2026-07-03 / 2026-07-04) — 8 tickets

| Ticket | Change | Outcome |
|---|---|---|
| `TCK-20260703-SIMQ-UPLIFT3-FAST-CALIBRATE` | Added `no_frame_pacing` flag to offline calibration's `Kernel(...)` call | ~8.3x calibration speedup; byte-identical output confirmed |
| `TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC` | Documented the FACTION/INFORMATION fix shape as reusable "Pattern 6" (`docs/guidelines/design_patterns.md`) | Documentation only |
| `TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT` | Investigated whether ECONOMY/SOCIAL share FACTION/INFORMATION's construction-gap bug class | They don't — ECONOMY is purely event-driven (duration-gated, not construction-gated); SOCIAL is pure flag-gating. No fix needed |
| `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` | Found and fixed 3 causally-linked bugs blocking self-model Branch B: hardcoded `events=[]`, a missing pipeline merge wrapper, and `self_model_bundle_set` never durably materializing (new `SelfModelPatch` component-patch class) | Mechanism proven correct via test-scoped verification; **not** active in any shipped calibration profile |
| `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` | Recompiled 5 stale worlds (missing `hazard_kind` on 7 modules); caught genuine drift in 8 of `dungeon_crawl`'s 10 shipped anchors via a drift-check the plan initially omitted | Corpus 25→40 anchor entries; `simq_routing_test`'s 3 anchors blocked by a pre-existing, unrelated crash, filed separately (below) |
| `TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW` | Built `tools/simq_audit_gaps.py`, `make simq-full-audit*` targets, and the `simq-audit` agent workflow, formalizing the manual doc-sync process repeated by hand across 3 batches | Tooling only |
| `TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE` | Resolves `audit_fix_plan.md` P1-D — weighted `QuestGenerator` template selection by regional pressure signals | Also fixed a masked test bug (two functions both named `test_quest_generation_determinism`) |
| `TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE` | Investigation found this ticket's scope was already implemented by `TCK-20260627-P1H-GOAL-RUNNERUP` | Closed as a documentation-only duplicate; corrected `audit_fix_plan.md`'s stale P1-H entry |

Follow-up: `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP` — a pre-existing `ResourceRegistry: STONE`
crash in `src/world/ecology.py`'s dynamic resource generation, hit twice this batch (confirmed
pre-existing via git-stash bisection), blocked `simq_routing_test`'s anchors until fixed.

### SimQ Corpus Tiers Epic (2026-07-06 / 2026-07-07) — `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC`, 10 tickets

Product-philosophy redirection: world data should exercise every engine feature, not just what
already looks good, organized as a test-pyramid tier structure (Unit/End-to-end/Stress/Regression —
see `docs/simulation_quality/corpus_tier_taxonomy.md`).

| Ticket | Change |
|---|---|
| `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` | Documented the 4-tier taxonomy and classification criteria |
| `TCK-20260704-SIMQ-CORPUS-SCALE-METRIC` | Added `distinct_populated_factions` to compile reports (purely additive, hash-preserving) |
| `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE` | Migrated `ENABLE_ADVENTURE_ROUTING` off a hardcoded scenario-name special case onto the standard per-world flag mechanism |
| `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO` | Authored `unit_faction_tension`, `unit_information_source` (first unit-tier worlds); found and fixed a corpus-wide blocking catalog bug (missing `stone` material) |
| `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT` | Authored `unit_selfmodel_pilot` — first multi-entity, multi-tick, multi-seed live evidence Branch B's mechanism actually works |
| `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` | Authored `hero_guild_routing` — new routing-capable world at archetype scale |
| `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` | Authored bespoke FACTION/INFORMATION content into 8 of the original 10 worlds |
| `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` | Authored `crowded_frontier`, `resource_dense_basin`, `frontier_marches` — 3 new stress-tier worlds filling named scale-diversity gaps |
| `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS` | Resolves `audit_fix_plan.md` P2-D — expanded `faction_relationships.yaml` coverage (global catalog content) |
| `TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL` | Resolves P2-E — added a static flag/content-pairing guardrail test (17 worlds, 55 cases); found and resolved a false-alarm regression (stale local cache, not real) |

**Net effect:** 10 worlds → 17; 0 regressions across 610 pillars post-epic.

### SimQ Uplift Batch 4 / Deep Coverage Epic (2026-07-07 / 2026-07-09) — `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC`, 10 tickets

Follow-up to the Corpus Tiers epic: closed the long-run blind spot it left behind (only 3/17 worlds
had any anchor ≥1000 ticks; long-run AGENCY/COMBAT/PROGRESSION/WORLD grades were suspiciously
invariant).

| Ticket | Change |
|---|---|
| `TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP` | Fixed a resource-tag gap before `hero_guild_routing`'s long-run anchor |
| `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP` | Resolved a dormant resource gap before `urban_political`'s 2000t extension |
| `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT` | Corpus-wide resource/region coverage audit |
| `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP` | Extended population-stability test coverage — surfaced the 2 collapse defects below |
| `TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER`, `TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING` | Parallel doc-hygiene chores |
| `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` | Added 1000t/2000t anchors for the worlds already known to drive those pillars to peak grades |
| `TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS` | `generated_frontier_3_42`'s first-ever anchors (200t×3 + 1000t); surfaced the late-tick collapse below |
| `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC` | No 11th pillar justified — 4 candidate dimensions each already owned by dedicated systems outside SimQ |
| `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL` | Closed the one genuine gap found (`building_sabotage`) as a new WORLD-pillar rule, not a new pillar |

**Net effect:** corpus grew to **71 scenarios / 17 worlds** (final state — see Module Health).

**Population-collapse defects found as a byproduct (2026-07-08), same root-cause class** (the
worldassembly resolver's `hazard_kind` default of `"PHYSICAL"` matching no faction's declared
`hazard_immunities`, causing unconditional lethal drain):

- `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` — `dungeon_crawl` (43.8% alive at tick 50) and
  `urban_political` (56.7% alive at tick 300) both failed population-stability. Fixed via
  `hazard_kind` declarations on 3 modules (`ruins_mystery_quest.yaml`, `scalable_bandit_camp.yaml`,
  `trading_company_hub.yaml`) plus one new immunity entry; post-fix both worlds pass cleanly.
- `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE` — `generated_frontier_3_42`
  collapsed from 81.8% to 9.1% between tick 800–1000. Same bug class, `moon_cult_ruins.yaml`'s
  `moon_cave` region (introduced a new `hazard_kind: "ARCANE_CORRUPTION"` value). Also surfaced a
  genuine, **not fixed** architecture finding: the kernel's wall-clock tick-budget throttle causes
  real run-to-run population variance past ~tick 300-400 — documented, intentional engine behavior,
  explicitly out of scope to change. A tolerance-based regression guard was added instead of a
  tight assertion.

**Follow-up, resolved 2026-07-10/11:** `town_council`'s hazard-immunity gap at `bandit_road`
(shared by `dungeon_crawl`/`urban_political`, deliberately left open by both collapse tickets) —
ruled **intentional** by `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` (contested-road-posted forces
enduring unmitigated drain by design; recorded as `docs/guidelines/intentional_divergences.md`
§2.30). Zero code/content changes. `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` separately made the
`hazard_kind` completeness check unconditional across all 17 worlds (was a 3-world allowlist) — 0
mismatches found, closing the recurrence risk this defect class had shown 3 times.

---

## Module Health (current state)

All integration gaps resolved. Module is fully wired, calibrated, and producing live scores.

| Component | Status |
|---|---|
| 10 pillar scorers | Implemented, unit-tested, live |
| `QualityHub` | Wired — `quality_fn=hub.on_envelope` at `kernel.py:264` |
| `PillarAccumulator` | Sliding window (200 events, 0.70 loop threshold) — defaults confirmed correct |
| `QualityPersistence` | Write-through to `data/runs/`, verified |
| REST API | `set_quality_hub()` called at server startup (`server.py:34`) — live |
| `EventExtractor` emissions | 81 of 82 scored event types emitted; `camp_constructed` has no engine path (documented dead event, not a gap) |
| Calibration tooling | `calibrate_simq.py` with `--window-size`/`--loop-threshold` overrides, run-scoped (no YAML mutation) |
| Calibration corpus | **71 scenarios across 17 worlds** (`FAST_ANCHOR_KEYS` 53 + `SLOW_ANCHOR_KEYS` 18, `tests/simulation_quality/test_grade_regression.py`) — see `docs/simulation_quality/corpus_tier_taxonomy.md` for tier structure and `eval_matrix_results.md` for current grade tables |
| Parity ledger | SOC-237, SOC-238, INFRA-251 added and `verified` |

---

## Findings Summary

| # | Finding | Severity | Status |
|---|---|---|---|
| F1 | `QueueDrainWorker.quality_fn` slot never populated at kernel init | High | **RESOLVED** — `TCK-20260630-SIMQ-WIRE-KERNEL` |
| F2 | `set_quality_hub()` never called; REST endpoints always returned `hub=None` | High | **RESOLVED** — `TCK-20260630-SIMQ-WIRE-SERVER` |
| F3 | `InProcessQualityFeed` created a competing consumer, racing `EventRecorder` | Medium | **RESOLVED** — `TCK-20260630-SIMQ-WIRE-KERNEL` |
| F4 | Zero events scored — SimQ produced no actionable signal | High | **RESOLVED** — hub wired; 81/82 event types emitted; `camp_constructed` has no engine path |
| F5 | Threshold calibration blocked until F1 fixed | Medium | **RESOLVED** — unblocked by F1, calibration corpus built out fully |

---

*Superseded as the live action list by `docs/plans/archive/simq_development_roadmap.md` (archived
2026-07-13, all 6 phases complete) — this document is the historical wiring/calibration record, not
a current task list. No open follow-up work remains from any batch above.*

*For the current, periodically-refreshed status picture (post-roadmap), see
`docs/audits/D20_simq_quality_status_review.md` — a broader-view synthesis document, distinct from
both this integration-history record and `docs/simulation_quality/current_state.md`'s own
numbers-only snapshot.*
