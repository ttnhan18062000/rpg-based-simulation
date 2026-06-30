---
status: active
layer: misc
authority: P1
audience: agent
tags: [plan, audit, fix-plan, backlog, simulation-quality, architecture, testing, content]
---

# Audit Fix Plan — Remaining Open Issues

**Source:** 18-dimension audit programme `TCK-20260618-AUDIT-EPIC` + marker-standardization pass (2026-06-26/27).  
**Date:** 2026-06-27  
**Scope:** All findings that remain open (not RESOLVED/CONFIRMED INVALID) across D01–D18.

Each item below maps to a source audit finding and carries enough context for a ticket to be written directly from this document.

---

## Priority Legend

| Priority | Meaning |
|---|---|
| **P0** | Blocks measurement of other systems — fix first or downstream work is invalid |
| **P1** | Significant functional gap or architecture violation that produces incorrect simulation behaviour |
| **P2** | Architectural debt, quality gap, or diagnostic limitation — should fix before extended test runs |
| **P3** | Content, tuning, or nice-to-have — deferred until P0–P2 are cleared |

---

## P0 — Blockers (must fix before economic/balance measurement is valid)

### P0-A: `ENABLE_ADVENTURE_ROUTING` defaults to `FeatureMode.OFF`

**Source:** D04 §6.1  
**File:** `src/domains/optimization/feature_flags.py:16`  
**Finding:** The entire adventure decision pipeline — route generation, opportunity scoring, blocker-penalty evaluation, strategic project assignment — is inactive in all default simulation runs. Every economic balance measurement is running against a disabled pipeline.  
**Impact:** D04 §6, D06 F1/F4 measurements remain invalid until this is resolved. All 8 feature flags listed in `feature_flags.py:14–22` default to `OFF`.  
**Fix:** Decide the intended default state. Options:
- Enable in non-test runs: change default to `FeatureMode.ON` in `feature_flags.py`
- Keep `OFF` as default but require test harness to set `ON` explicitly for all balance/behavioral tests (document in `docs/engine/known_limitations.md`)

Record the decision in `docs/guidelines/v2_intentional_divergences.md` and update `ENABLE_ADVENTURE_ROUTING` parity ledger entry.

---

### P0-B: `urban_political` world has zero resource nodes after compile — **RESOLVED**

**Source:** D04 §6.2  
**Finding:** `len(state.resource_nodes) == 0` after `WorldCompiler.compile()` for urban_political.  
**Resolution (2026-07-01):** `data/worlds/urban_political/world_compile_report.json` now shows `resource_node_count: 3`, `warnings: []`. Fixed during the worldgen epic (world content authoring pass). P0-B is no longer a blocker.

---

### P0-C: All entity `navigation.region_id` is `None` after world compilation

**Source:** D04 §6.3  
**File:** `WorldCompiler` or `EntityFactory`  
**Finding:** All 30 entities in urban_political have `navigation.region_id = None` after compilation. `ResourceOpportunityProvider` uses `region_id` for node matching — even with P0-B fixed, region-based filtering fails for all entities.  
**Fix:** Fix `WorldCompiler` or `EntityFactory` to assign `region_id` based on each entity's spawn location during world assembly. Verify with a post-compile assertion: `all(e.navigation.region_id is not None for e in state.entities.values())`.

---

## P1 — Functional and Architecture Gaps

### P1-A: Rejection cascade has no backoff — 500K–650K/run at 1,000 ticks

**Source:** D03 F3, D04 §4, D06 F3  
**Files:** `src/core/state.py` (`ProjectState`), `src/engine/apply.py`, `src/engine/interaction.py`  
**Finding:** After the RC1 fix, the opportunity pipeline runs at full volume but many requirements fail every tick (near_service, inventory_space, has_item). Without a cooldown or expiry mechanism, failed requirements are retried every tick indefinitely. Rate: ~650 rejections/tick → ~550K cumulative at tick 1,000. This scales to 3–4M at tick 5,000 — memory and diagnostic noise risk.  
**Fix:** Add one of:
- Max-retry count per project: abandon project after N consecutive rejections (N ~= 20)
- Tick-expiry: mark project stale after M ticks without progress (M ~= 50)
- Requirement cooldown: suppress re-evaluation of a failed requirement for K ticks

Update `ProjectState` dataclass with the chosen mechanism. Add test: rejection count per entity stays below threshold in a 1,000-tick run.

---

### P1-B: Quest system never activates — material blockers not generated

**Source:** D06 F4  
**Files:** `src/systems/world_systems/quests.py`, `src/systems/strategic_systems/intelligence.py`  
**Finding:** `quest_active_count = 0.0` and `quest_completed_count = 0.0` across all 1,000-tick runs. The quest generation pathway (strategic blockers → quest templates → strategic projects) requires a material/access blocker to trigger. While entities are trapped in survival/hunger mode or the adventure pipeline is OFF (P0-A), no material blockers are generated, so the quest system has no entry trigger.  
**Fix:** This has two components:
1. Fix P0-A so entities pursue economic goals (which generate material blockers)
2. Verify independently that `StrategicIntelligenceSystem` generates blocker-triggered quest projects when an entity has a material gap (add unit test)

Acceptance: at least 1 quest activation per entity per 500-tick run after P0-A/P0-B/P0-C are fixed.

---

### P1-C: Faction & Diplomacy System `[M]`

**Source:** D01 §Faction & Diplomacy System  
**Finding:** Faction interaction logic (alliance formation, diplomatic posture, war declarations) is absent. 16 factions exist in the catalog with 14 explicit relationships, but the engine has no system that uses faction stance to drive entity-level behavioural differences in encounters.  
**Fix:** Scope a new system (or extend `CooperationPhase` / `StrategicIntelligenceSystem`) to:
- Read faction relationship stances (`ally`, `hostile`, `neutral`)
- Modify entity encounter disposition based on their faction vs. target's faction
- Trigger faction-level events (trade embargo, raid declaration)
Requires a new epic ticket. See D01 acceptance criteria for completeness threshold.

---

### P1-D: Pressure-Driven Quest Generation `[M]`

**Source:** D01 §Pressure-Driven Quest Generation  
**Files:** `src/quests/generator.py`  
**Finding:** `QuestGenerator` uses `building_id` for quest assignment, not pressure signals (resource scarcity, threat level, regional trauma). Quest content is static rather than emerging from world state. The `ResourceOpportunityProvider` generates opportunities from world state, but the quest layer does not.  
**Fix:** Extend `QuestGenerator` to accept world-state signals (resource scarcity by region, threat level, trauma score) and select quest templates that match the current pressure. See `docs/mechanics/05_world_evolution.md` §trauma and `docs/mechanics/03_economic_laws.md` §resource pressure for the driving signals.

---

### P1-E: Domain-phase layer has no audit inventory (D09 Finding 3) — **RESOLVED**

**Source:** D09 Finding 3 — Risk 13/15  
**Resolution:** `docs/audits/D19_domain_phase_inventory.md` created (TCK-20260627-P1E-DOMAIN-INVENTORY). All domain phases in `pipeline.py:refine()` and `world_dynamics.py:resolve_dynamics()` inventoried with wiring status and phase anchors. Used by all SimQ scorers as grounding reference.

---

### P1-F: `AbandonmentEvaluator.evaluate_abandonment()` returns untyped dict

**Source:** D12 F2  
**File:** `src/domains/commitment/abandonment.py`  
**Finding:** Returns `Dict[str, Any]` with mechanical fields `is_betrayal` (bool) and `penalty` (float). A key rename silently breaks callers with no type error.  
**Fix:** Replace with:
```python
@dataclass
class AbandonmentClassification:
    is_betrayal: bool
    penalty: float
    category: AbandonmentCategory  # enum: SURVIVAL / GREEDY_DESERTION / VOLUNTARY_QUIT

class AbandonmentCategory(Enum):
    SURVIVAL = "survival"
    GREEDY_DESERTION = "greedy_desertion"
    VOLUNTARY_QUIT = "voluntary_quit"
```
Update all callers. Add parity test that `evaluate_abandonment()` returns a typed record.

---

### P1-G: Phase Stability Guard is audit-mode only — isolation breaches invisible in standard runs

**Source:** D09 Finding 5 — Risk 11/15  
**File:** `src/engine/kernel.py` (`_guard_stability()`, `_tick_once_inner()`)  
**Finding:** `_guard_stability()` fingerprints `AuthoritativeState` between phases to catch isolation breaches. It is only active when `Kernel` is initialized with `audit_mode=True`. An isolation breach (a phase mutating state outside the authoritative pipeline) would be invisible in normal production runs.  
**Action:** Document which violation types can only be caught in audit mode. Consider enabling a lightweight version of the guard in standard runs (hashing only the entity count and tick number, not the full state) to catch gross violations without performance overhead.

---

### P1-H: Goal score history over ticks — runner-up scores discarded

**Source:** D15 Gap 1 (partial — trace writer added but runner-up scores not retained)  
**Files:** `src/domains/adventure/phase.py`, `src/observability/cognition/recorder.py`  
**Finding:** `source_goal_score` in cognition snapshots captures only the winning project's score. Runner-up scores (why goal X won over Y) are computed transiently in `execute_brain()` and discarded at tick boundary. Developer cannot distinguish "entity stuck because all alternatives scored lower" from "entity stuck on high-priority goal that should be interrupted."  
**Fix:** Retain top-3 candidate scores at tick commit in the cognition snapshot. Add to `EntityInspectionSnapshot.goal_scores` field. Existing `decision_trace.jsonl` infrastructure can carry the data — extend the trace record schema.

---

## P2 — Architectural Debt and Quality Gaps

### P2-A: 200-tick activation delay from initial spawn project locks

**Source:** D06 F2  
**Files:** `src/engine/apply.py`, `ProjectState`  
**Finding:** Initial spawn projects lock entities via `lock_until_tick` for ~200 ticks post-combat. 20% of a standard 1,000-tick run is enforced dead time. Lock may be too aggressive if it's a fixed value rather than conditional on threat resolution (entity health restored, combat enemies dead).  
**Fix:** Make `lock_until_tick` conditional: release the lock when the triggering threat is resolved (entity HP > 80%, no hostile in vicinity) rather than at a fixed tick. Add a cap of max 50 ticks. Verify in D06-style run: behavioral activity should begin before tick 50.

---

### P2-B: Late-run attrition exceeds spawn rate — entity count trends toward zero

**Source:** D06 F5  
**Files:** `src/systems/world_systems/spawn.py` (`SpawnService`)  
**Finding:** SpawnService fires at ~tick 500 and adds 3 entities but combat attrition in ticks 800–1000 kills faster than spawn rate. Net entity count at tick 1,000 is below starting count (13.1 vs 15 for seed 42). A 5,000-tick run risks approaching zero.  
**Fix:** Tune `SpawnService` cadence or spawn count so entity population is stable over 5,000 ticks. Target: alive_avg stays ≥ 12 (80% of starting count) throughout. Consider two spawn cadence tiers: early slow spawn, late fast spawn to compensate attrition.

---

### P2-C: Entity archetype distribution skewed — 4 scouts, underrepresented roles

**Source:** D07 F4 — Gap Risk 9/15  
**Files:** `data/content/entity_archetypes/`  
**Finding:** 21 archetypes, but 4/21 are the same role (scout). No dedicated mage/caster role has more than 1 entry. Encounters pull mostly scout-type entities, reducing variety.  
**Fix:** Add 6–8 archetypes weighted toward underrepresented roles (mage, healer, leader variants, rogue). Distribute across existing factions. Verify: no single role exceeds 3/21 distribution.

---

### P2-D: Faction relationships sparse — 14 defined for 16 factions

**Source:** D07 F6 — Gap Risk 8/15  
**Files:** `data/content/faction_relationships/`  
**Finding:** 14 faction relationships for 16 factions (120 directed pairs possible). Factions without explicit relationships default to neutral, reducing encounter variety.  
**Fix:** Define relationships for at least 50% of active cross-faction pairs (30+ entries). Focus on conflict and economy module factions first (highest encounter frequency).

---

### P2-E: Feature-gated phases have no per-scenario default test

**Source:** D09 Finding 4 — Risk 9/15  
**Files:** `src/domains/optimization/feature_flags.py`, `data/content/simulation_scenarios/`  
**Finding:** 8 pipeline phases are gated behind `FeatureMode` flags. No test verifies that the correct default flag values are set per scenario type. A misconfigured scenario silently loses features.  
**Fix:** Add a test in `tests/integration/` or `tests/certification/` that loads each scenario definition and asserts expected flag states. At minimum assert that the flags required for that scenario's content type are `ON` or `SHADOW`.

---

### P2-F: Canonical state hashing conditionally active — recorded as "SKIPPED"

**Source:** D09 Finding 6 — Risk 8/15  
**Files:** `src/engine/kernel.py` (`_phase_persistence()`)  
**Finding:** `CanonicalStateHasher.get_hash()` is only called when `replay_richness == "FULL"` or `audit_mode=True`. Standard runs record `"SKIPPED"`. Full hash traceability is absent in normal runs; only the lighter `fingerprint()` runs.  
**Action:** Document which run configurations produce `"SKIPPED"` hash in `docs/engine/known_limitations.md`. Decide if this is acceptable — if the fingerprint is sufficient for standard determinism verification, update the contract to say so explicitly.

---

### P2-G: `hard_law_monitor.py` imports `WorldIndexService` directly

**Source:** D14 F3 — Risk 8/15  
**File:** `src/observability/hard_law_monitor.py:10`  
**Finding:** Other observability files (`sweeper`, `controller`, `harness`) only import `Kernel`. `hard_law_monitor` reaches into `src.engine.world_index.WorldIndexService` — a concrete engine internal. If `WorldIndexService` interface changes, the monitor breaks without a visible dependency signal.  
**Fix:** Expose the spatial query capability through `Kernel` (a `KernelQueryFacade` method or existing spatial query delegation) so `hard_law_monitor` only touches `Kernel`.

---

### P2-H: `kernel.py:804` direct `entity.timeline.append()` mutation

**Source:** D12 F5 — Priority 6/15  
**File:** `src/engine/kernel.py:804`  
**Finding:** Single direct mutation of `entity.timeline` outside the authoritative pipeline. Minor pattern violation; if timeline management grows, this becomes a coupling risk.  
**Fix:** Move `entity.timeline.append(event)` into the event emission layer (e.g., through `ReplayManager.emit()` or an `EntityTimelineService`). Low-risk change, can be done in any cleanup sprint.

---

### P2-I: `lab/workflows.py` all `run()` methods return `dict[str, Any]`

**Source:** D13 F4 — Risk 7/15  
**File:** `src/lab/workflows.py`  
**Finding:** All 7 `Workflow.run()` methods return `dict[str, Any]`. Callers access keys (`result["summary"]`, `result["health_score"]`) by string convention. A renamed key only surfaces at runtime.  
**Fix:** Define `WorkflowResult` TypedDicts (or dataclasses) per workflow type and annotate all 7 `run()` returns. `SweepWorkflowResult`, `MutationWorkflowResult`, `SandboxWorkflowResult` at minimum.

---

### P2-J: `engine/patches.py` `merge()` returns `Any`

**Source:** D13 F5 — Risk 6/15  
**File:** `src/engine/patches.py:29`  
**Finding:** Only `Any`-return in an engine-tier module that is not a serialization helper. A type error in a merged patch value is invisible until the downstream pipeline consumer processes it.  
**Fix:** Narrow return type from `Any` to the actual merged type (likely the same type as inputs, or a `MergedPatch` TypedDict). Low-effort, high-signal improvement.

---

### P2-K: `ContentUsageMatrix` is a manual registry — no authoring-time feedback

**Source:** D16 Task 3 — DX Gap 12/15  
**Files:** `src/content/repository.py:353`, `ContentUsageMatrix`  
**Finding:** Adding a new YAML file to `data/content/` requires manually registering the family in `ContentUsageMatrix`. No authoring-time prompt exists; the only feedback is a CI test failure (`ValueError: Ignored active YAML files`).  
**Fix (preferred):** Auto-generate `ContentUsageMatrix` from directory scan at load time.  
**Fix (alternative):** Add a `make content-check` target and invoke it in `make world-validate` so authors get immediate feedback before CI.

---

### P2-L: No content author guide — **RESOLVED**

**Source:** D16 Structural Gap  
**Resolution:** `docs/guides/content_authoring.md` created (2026-06-30). Covers step-by-step module/composition/scenario authoring, allowed module types, valid `initial_conditions` keys, `make` targets, and sharp edges (catalog ID validation, ContentUsageMatrix). Moved from `docs/content/authoring_guide.md`.

---

### P2-M: Release reports are ephemeral — no CI artifact upload

**Source:** D18 F5 — Risk 5/15  
**Files:** `.github/workflows/test.yml`  
**Finding:** `reports/certification/` and `reports/release_proof/` are local ephemeral output. CLAUDE.md §After Work instructs `rm -rf reports/release_proof/*`. No CI artifact preserves these per commit SHA.  
**Fix:** Add `actions/upload-artifact` step to the `slow` job in `test.yml` to archive `reports/certification/` as a CI artifact tied to the commit SHA.

---

### P2-N: D02 §6.6 — Hardcoded fallback content source path

**Source:** D02 §6.6 `[P]`  
**File:** `src/domains/optimization/degradation.py` or equivalent  
**Finding:** `runtime_content_source = "legacy_hardcoded"` persists as the default in non-strict modes. Content loading falls back to hardcoded paths rather than the catalog system in degraded mode.  
**Fix:** Replace the hardcoded default with a catalog-driven fallback. In strict mode, raise immediately; in degraded mode, select the lowest-cost catalog entry for the requested content type rather than a static path. Update `GracefulDegradationManager` contract.

---

## P3 — Tuning, Content, and Deferred Capabilities

### P3-A: Remaining `[P]` items in D01 (RPG Feature Impact)

These are partially implemented and tracked at the D01 level. Each may spawn its own epic when P0–P2 are cleared:

| Item | Gap | Notes |
|---|---|---|
| Resource Ecology Regeneration | Content gaps — no authored regeneration-cycle modules | Mechanics and regen service exist; content layer thin |
| World Evolution System | World evolution events fire but trauma/sovereignty feedback loop not validated long-run | Run D06 at 5,000 ticks after P0 fixes |
| Narrative Consequence Layer | Consequence tracking exists (chronicle, social memory) but not surfaced in scenario feedback | E51/E43B episode-boundary systems |
| Full Party Adventure Loop | Multi-hero orchestration scoped (E61B) but not yet implemented | Campaigns domain; depends on HERO role population |
| Personality → Long-Run Behavior Calibration | Personality seeded (F1 resolved) but calibration across 1,000+ ticks not verified | Run D05-style audit post P0-A fix |
| Combat Ecology Extension | AoE and wound system verified [E]; ecology pressure-driven encounter spawning missing | Requires D06 5,000-tick data |
| Long-Horizon Regression Suite | No automated 5,000-tick regression test exists | Depends on P1-A rejection cascade fix |

---

### P3-B: ObservabilityMode naming mismatch — STANDARD maps to LIGHT engine mode

**Source:** D03 F5 — Score 8/15  
**File:** `src/lab/orchestrator.py:147–153`  
**Finding:** Lab mode `"STANDARD"` maps to engine `ObservabilityMode.LIGHT`. A developer switching to STANDARD expecting richer data gets identical output to LIGHTWEIGHT. Diagnosis tooling gap.  
**Fix:** Rename lab modes or remap `"STANDARD"` → `ObservabilityMode.NORMAL`. Add `make sim-debug` target that sets `SIM_OBS_MODE=DEBUG` for cognition snapshot access.

---

### P3-C: Documentation currency — P2 verification items

**Source:** D17 P2 items (all stale findings resolved; these are unverified uncertain claims)

| File | Uncertain claim | Action |
|---|---|---|
| `docs/mechanics/02_combat_laws.md` | Cover `+0.30` Def, Bond Synergy `+0.10` Atk | Verify `COVER_REDUCTION` and `BOND_SYNERGY_BONUS` constants |
| `docs/mechanics/03_economic_laws.md` | Slot Limit 16, Weight 100.0 kg; Home Storage 32/200 kg; selling formula | Verify `InventoryComponent` defaults and `ShopSystem.enforce()` formula |
| `docs/mechanics/04_strategic_cognition.md` | Goal tier numbering; blocker types; perception radius 10–15; info decay 100 ticks | Audit 4 uncertain claims against source |
| `docs/mechanics/06_worldbuilding_foundation.md` | "Certified Level 1" self-certification claim | Update to reflect chapters 01/04 had stale claims (now fixed); re-certify |

---

### P3-D: Catalog ID browser and scenario template discoverability

**Source:** D16 Structural Gaps  
**Finding:** No way to list valid biome/ecology/population/faction IDs without running assembly code. 10 scenario templates in `src/scenarios/templates.py` are undocumented.  
**Fix:** Add `make catalog-list` / `make content-browse` to list catalog IDs by type. Document the 10 scenario templates in the content author guide (P2-L).

---

---

## D20 — Simulation Quality Integration Gaps — **ALL RESOLVED (2026-06-30)**

**Source:** D20 audit (2026-06-30) — `docs/audits/D20_simq_integration.md`  
**Date found:** 2026-06-30  
**Resolved:** 2026-06-30 — TCK-20260630-SIMQ-WIRE-KERNEL, TCK-20260630-SIMQ-WIRE-SERVER, TCK-20260630-SIMQ-RECALIBRATE all done.

### D20-G1: quality_fn slot never populated at kernel init — **RESOLVED**

**File:** `src/observability/queue.py:97`, `src/observability/event_recorder.py:95–99`,
`src/engine/kernel.py:226`  
**Finding:** `QueueDrainWorker` has a `quality_fn: Optional[Callable]` slot for feeding
events to the hub on each drain. EventRecorder creates this worker but never passes a
`quality_fn`. The integration slot exists; it is just not connected.  
**Ticket:** `TCK-20260630-SIMQ-WIRE-KERNEL` (standard) — **DONE**

---

### D20-G2: set_quality_hub() never called from server or CLI — **RESOLVED**

**File:** `src/api/dependencies.py:22–24`, `src/api/server.py`  
**Finding:** `set_quality_hub()` is defined but called nowhere. `get_quality_hub()`
always returns `None`. REST quality endpoints silently return disabled-hub responses
for the entire lifetime of any server process.  
**Ticket:** `TCK-20260630-SIMQ-WIRE-SERVER` (hotfix) — **DONE**

---

### D20-G3: InProcessQualityFeed creates competing consumer — **RESOLVED**

**File:** `src/simulation_quality/feed.py:33–61`  
**Finding:** `InProcessQualityFeed` creates a second `QueueDrainWorker` on the same
global observability queue as EventRecorder's worker. Both race to drain items.
EventRecorder's worker (started first at kernel init) wins the race; `hub.on_envelope()`
is never called. Result: `tick_count=0`, all pillar `event_count=0`, all grades C across
all seeds verified in D20.  
**Ticket:** `TCK-20260630-SIMQ-WIRE-KERNEL` (same ticket as G1 — G3 is the cleanup after G1 is fixed) — **DONE**

---

### D20-F5: Calibration blocked until G1 is fixed — **RESOLVED**

**Finding:** `tools/calibrate_simq.py` calibrated against zero-signal runs. Thresholds were
placeholder estimates. Also: `--name` arg ignored (all worlds ran same generic sim).  
**Ticket:** `TCK-20260630-SIMQ-RECALIBRATE` (hotfix) — **DONE**  
**Follow-on:** `TCK-20260630-SIMQ-CALFIX` (standard) — **DONE** — world loading fixed,
goblin spawn staggered, `--profile` arg added. Deep audit tracked in `docs/plans/archive/simq_deep_audit_plan.md`.

---

---

## SimQ Re-evaluation — 2026-07-01

**Trigger:** Three world-data tickets completed (TCK-20260630-WORLD-QUEST-LOCATION, TCK-20260630-WORLD-DEPLOY-MODULES, TCK-20260630-WORLD-TEST-MATRIX). Calibration corpus expanded from 8 to 13 runs.

### Changes that informed this re-evaluation

| Ticket | Change | Impact on SimQ |
|---|---|---|
| TCK-20260630-WORLD-QUEST-LOCATION | Compiler now matches `required_location_tags` against `region.type` + `region.tags`; 28 compile warnings → 0 | Removes false validation failures at compile time; no direct runtime grade change (quests fire via P1-B path, not location-tag block) |
| TCK-20260630-WORLD-DEPLOY-MODULES | 5 new compiled worlds deployed; calibration corpus now 13 runs | Provides empirical grade data across more world types and entity counts |
| TCK-20260630-WORLD-TEST-MATRIX | MODULE_MATRIX 15 → 20; all modules covered by integration tests | Test coverage gap closed; no grade change |

### Current calibration corpus (13 runs)

| World | Seed | Ticks | COMBAT | NARRATIVE | PROGRESSION | AGENCY | COGNITION | ECONOMY | FACTION | INFO | SOCIAL | WORLD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sandbox_world | 42 | 200 | B | A | B | C | C | C | C | C | C | C |
| sandbox_world | 137 | 200 | B | A | C | C | C | C | C | C | C | C |
| sandbox_world | 999 | 200 | B | A | C | C | C | C | C | C | C | C |
| sandbox_world | 42 | 1000 | B | A | B | C | C | C | C | C | C | B |
| dungeon_crawl | 42 | 200 | A | B | A | C | C | C | C | C | C | A |
| dungeon_crawl | 42 | 1000 | B | B | B | C | C | C | C | C | C | B |
| urban_political | 42 | 200 | B | A | B | C | C | C | C | C | C | A |
| simq_routing_test | 42 | 500 | B | A | B | **B** | C | C | C | C | C | B |
| frontier_extended | 42 | 159† | A | A | A | C | C | C | C | C | C | A |
| frontier_living_world | 42 | 159† | A | A | A | C | C | C | C | C | C | A |
| swamp_border_world | 42 | 200 | B | A | B | C | C | C | C | C | C | B |
| highland_traverse | 42 | 164 | B | B | B | C | C | C | C | C | C | B |
| wilderness_survival | 42 | 101‡ | B | C | B | C | C | C | C | C | C | A |

†Early termination — large entity count (56/46) accelerates combat attrition. See P2-B.  
‡Early termination — only 11 entities; survivor_camp_shelter now included (combat-heavy). Confirms P2-B at small scale.

### Findings

**Finding 1: Systemic C ceiling on 5 pillars is confirmed engine-structural.**  
COGNITION, ECONOMY, FACTION, INFORMATION, and SOCIAL are uniformly C across all 13 runs — across every world type, every seed, every tick count. This is not a calibration or content problem. It is 100% attributable to the 27 engine emission gaps documented in `docs/simulation_quality/event_type_coverage.md §3`. These pillars have complete scoring infrastructure but no upstream event emitters in the engine. No world content change, calibration run, or tuning will move these grades until the engine emits the missing event types. Tracking as a standing structural gap — not a new finding, confirmed.

**Finding 2: P0-A (ENABLE_ADVENTURE_ROUTING) is the sole confirmed blocker for AGENCY.**  
AGENCY is C in all 12 default-mode runs and B only in simq_routing_test (where `ENABLE_ADVENTURE_ROUTING=ON` is injected via env var). No world content, tick count, or entity density changes this pattern. Fixing P0-A (change default or mandate env-var in calibration harness) is a direct, confirmed path to AGENCY ≥ B.

**Finding 3: P0-B is RESOLVED.**  
`urban_political` now has `resource_node_count: 3` in its compile report (fixed during worldgen epic). P0-B is no longer blocking economic measurement for that world. Updated above.

**Finding 4: WORLD grade reflects ecology complexity, not entity count.**  
sandbox_world (2 regions, 10 nodes, 0 quests) scores WORLD=C despite high resource density. dungeon_crawl, frontier_extended, urban_political, and wilderness_survival all score WORLD=A. The differentiator is ecology events: hazard_drain, region_trauma_delta, raid_party_spawned. Worlds with ecology/danger modules score higher. sandbox_world has none. This is expected behavior, not a gap.

**Finding 5: NARRATIVE = C is a short-run / low-entity signal, not a gap in wilderness_survival.**  
wilderness_survival terminates at tick 101 with 11 entities. NARRATIVE is C because quest_started events require living entities pursuing quest objectives; with rapid attrition the narrative event rate is too low to cross the B threshold. NARRATIVE=C here confirms P2-B (entity attrition outpaces spawning) rather than indicating a narrative system gap.

**Finding 6: Larger multi-module worlds show COMBAT=A and PROGRESSION=A.**  
frontier_extended (56 entities, 10 regions) and frontier_living_world (46 entities, 7 regions) both score COMBAT=A and PROGRESSION=A at 200 ticks. These are currently the highest-activity worlds in the corpus. They also terminate early (tick 159) — confirming P2-B applies at higher entity counts too.

**Finding 7: Quest location fix has no grade impact (correct).**  
The TCK-20260630-WORLD-QUEST-LOCATION fix eliminated 28 compile warnings by validating `required_location_tags` against `region.type`/`region.tags` instead of `region.id`. This fix was compile-time validation only — the runtime quest activation path (P1-B) is not gated by this validation. quest_completed grades remain 0 across all worlds, as expected until P0-A and P1-B are addressed.

### Revised blocker assessment after re-evaluation

| Blocker | Status |
|---|---|
| P0-A ENABLE_ADVENTURE_ROUTING | **RESOLVED** — TCK-20260627-P0A-ADVENTURE-FLAG. Option B: all Phase 10 flags remain OFF by default; documented in `known_limitations.md §1.5` and `intentional_divergences.md DEV-002`. AGENCY=B achievable via env-var inject (confirmed by simq_routing_test). |
| P0-B urban_political resource nodes | **RESOLVED** — TCK-20260627-P0B-URBAN-RESOURCE-NODES + confirmed in compile report (3 nodes). |
| P0-C entity navigation.region_id None | **RESOLVED** — TCK-20260627-P0C-ENTITY-REGION-ASSIGN. Entity region assignment fixed at compile. |
| P1-B quest activation | **RESOLVED** — TCK-20260627-P1B-QUEST-ACTIVATION. quest_to_project() bug fixed; 12-test suite added. |
| 7 SimQ emit tickets | **ALL DONE** — SIMQ-EMIT-STATE-DIFF, AGENCY, COGNITION, WORLD, ECONOMY, SOCIAL-FACTION, NARRATIVE all committed (2026-06-29/30). |
| 5-pillar C ceiling | **Remaining** — 27 specific event types still have no engine emitter (see `event_type_coverage.md §3`). The emit tickets wired the event_extractor for events already in the engine's data flow; the §3 gaps require new signal paths in deeper engine subsystems (progression tracking, cognitive state diffing, ecology cycle detection). No tickets exist for these yet. |

### Genuine remaining work

**One body of work remains:** the 27 engine emission gaps listed in `docs/simulation_quality/event_type_coverage.md §3`. Scoring infrastructure (scorers, registry, thresholds) is complete for all 27. What's missing is the upstream signal — a new `emit()` call in the right engine subsystem when the event occurs.

Grouped by effort and pillar:

| Group | Gaps | Pillar impact |
|---|---|---|
| PROGRESSION signals | skill_unlocked, trait_expressed, pillar_trait_unlocked, progression_conversion_applied, progression_plateau_detected | PROGRESSION: C→B/A in combat-active worlds |
| INFORMATION / COGNITION signals | lead_certainty_updated, lead_contradiction_resolved, paid_info_changed_goal, belief_stale, decision_diverged_by_belief; decision_divergence_detected | INFORMATION: C→B; COGNITION: marginal gain |
| WORLD dynamics signals | ecology_cycle_completed, spawn_cadence_fired, camp_constructed, threat_evolved, node_recharged | WORLD: already A/B; ecology worlds gain more |
| AGENCY tracking signals | defer_with_reason, commitment_abandoned, rejection_cascade_tick, route_family_first_use | AGENCY: richer signal when routing ON |
| Misc small gaps | paid_info_transaction (ECONOMY), conservation_law_verified (ECONOMY), alliance_proposed (FACTION), resource_seized (FACTION), social_memory_created (SOCIAL), contract_milestone_completed (SOCIAL), scenario_objective_progressed (NARRATIVE) | ECONOMY/FACTION/SOCIAL/NARRATIVE: marginal gains |

Tickets created: `tickets/todos/simq-emit/` (5 tickets, 2026-07-01).

---

## Summary Table

| ID | Source | Priority | Type | Effort |
|---|---|---|---|---|
| P0-A | D04 §6.1 | **P0** | Configuration | XS — change default or document policy |
| P0-B | D04 §6.2 | **P0** | Content | **RESOLVED** — 3 resource nodes confirmed (2026-07-01) |
| P0-C | D04 §6.3 | **P0** | Engine | S — WorldCompiler entity region assignment |
| P1-A | D03 F3 / D06 F3 | **P1** | Engine | M — stale-project expiry on ProjectState |
| P1-B | D06 F4 | **P1** | Engine | M — quest activation preconditions |
| P1-C | D01 §Faction | **P1** | Feature | XL — new epic ticket |
| P1-D | D01 §Quest | **P1** | Feature | L — extend QuestGenerator |
| P1-E | D09 F3 | **P1** | Docs | **RESOLVED** — D19 exists |
| P1-F | D12 F2 | **P1** | Refactor | S — AbandonmentClassification dataclass |
| P1-G | D09 F5 | **P1** | Docs/Engine | S — document audit-mode guard scope |
| P1-H | D15 Gap 1 | **P1** | Observability | S — top-3 runner-up scores in trace |
| P2-A | D06 F2 | **P2** | Engine | S — conditional spawn-lock expiry |
| P2-B | D06 F5 | **P2** | Engine | S — tune SpawnService cadence |
| P2-C | D07 F4 | **P2** | Content | M — 6–8 archetype YAML files |
| P2-D | D07 F6 | **P2** | Content | M — 16+ faction relationship entries |
| P2-E | D09 F4 | **P2** | Testing | S — per-scenario feature flag test |
| P2-F | D09 F6 | **P2** | Docs | XS — document canonical hash scope |
| P2-G | D14 F3 | **P2** | Refactor | S — KernelQueryFacade for hard_law_monitor |
| P2-H | D12 F5 | **P2** | Refactor | XS — move timeline.append to event layer |
| P2-I | D13 F4 | **P2** | Typing | S — WorkflowResult TypedDicts |
| P2-J | D13 F5 | **P2** | Typing | XS — narrow patches.py merge() return |
| P2-K | D16 Task 3 | **P2** | DX | S — auto-generate or validate ContentUsageMatrix |
| P2-L | D16 Gap | **P2** | Docs | **RESOLVED** — docs/guides/content_authoring.md exists |
| P2-M | D18 F5 | **P2** | CI | XS — upload-artifact in slow CI job |
| P2-N | D02 §6.6 | **P2** | Engine | S — catalog-driven degraded fallback |
| P3-A | D01 [P] items | **P3** | Feature | varies — see individual epics |
| P3-B | D03 F5 | **P3** | DX | XS — remap STANDARD lab mode |
| P3-C | D17 P2 | **P3** | Docs | S — verify 4 uncertain claims |
| P3-D | D16 | **P3** | DX | S — catalog browser + template docs |
| D20-G1 | D20 | **P1** | Engine | **RESOLVED** — TCK-20260630-SIMQ-WIRE-KERNEL (2026-06-30) |
| D20-G2 | D20 | **P1** | API | **RESOLVED** — TCK-20260630-SIMQ-WIRE-SERVER (2026-06-30) |
| D20-G3 | D20 | **P1** | Engine | **RESOLVED** — TCK-20260630-SIMQ-WIRE-KERNEL (2026-06-30) |
| D20-F5 | D20 | **P1** | Tooling | **RESOLVED** — TCK-20260630-SIMQ-RECALIBRATE + TCK-20260630-SIMQ-CALFIX (2026-06-30/07-01) |

**Effort legend:** XS ≤ 1h · S = 2–4h · M = 1–2 days · L = 3–5 days · XL = epic

---

## Suggested Fix Order

Tickets should be created in this sequence to avoid blocked work:

All original P0–P3 items, all D20 gaps, all SimQ emit tickets, and all P3-A child epics are **DONE** as of 2026-07-01. The full sequence was completed; what remains is a single body of follow-on work:

**Remaining:** Engine emission gaps (`tickets/todos/simq-emit/`, 5 tickets created 2026-07-01)

1. `TCK-20260701-SIMQ-EMIT-PROGRESSION` — 5 progression signal events
2. `TCK-20260701-SIMQ-EMIT-INFORMATION2` — 5 information/cognition signal events
3. `TCK-20260701-SIMQ-EMIT-WORLD2` — 5 world dynamics signal events
4. `TCK-20260701-SIMQ-EMIT-AGENCY2` — 4 agency tracking events
5. `TCK-20260701-SIMQ-EMIT-SOCIAL2` — 7 misc gaps (ECONOMY ×2, FACTION ×2, SOCIAL ×2, NARRATIVE ×1)

---

## Related Documents

- `docs/audits/D01_rpg_feature_impact.md` — [P]/[M] items are sources for P1-C, P1-D, P3-A
- `docs/audits/D04_balance_tuning.md` — P0-A/B/C findings in §6
- `docs/audits/D06_longrun_health.md` — P1-A/B, P2-A/B
- `docs/audits/D09_system_wiring.md` — P1-E/G, P2-E/F
- `docs/audits/D12_pattern_consistency.md` — P1-F, P2-H
- `docs/audits/D13_type_safety.md` — P2-I/J
- `docs/audits/D20_simq_integration.md` — D20-G1/G2/G3/F5
- `docs/audits/D14_coupling_depth.md` — P2-G
- `docs/audits/D15_entity_decision_inspection.md` — P1-H
- `docs/audits/D16_scenario_authoring_dx.md` — P2-K/L, P3-D
- `docs/audits/D17_documentation_currency.md` — P3-C
- `docs/audits/D18_ci_release_pipeline.md` — P2-M
- `docs/plans/long_term_development_roadmap.md` — longer-horizon context for P1-C/D and P3-A
