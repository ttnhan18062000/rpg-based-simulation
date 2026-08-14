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

**Status refresh (2026-07-03):** a source-level verification pass found 13 items resolved as
side effects of unrelated work (typing passes, doc updates, small fixes) without this backlog
being updated to reflect it. Each is now marked `RESOLVED (verified 2026-07-03)` with the
confirming evidence, inline and in the Summary Table. Items with no evidence found remain marked
open — this document is a living plan (`docs/plans/`), kept current, not a frozen audit snapshot
(unlike `docs/audits/D*.md`, which record point-in-time findings and are not rewritten in place).

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

### P0-A: `ENABLE_ADVENTURE_ROUTING` defaults to `FeatureMode.OFF` — **RESOLVED** (decision recorded; reconfirmed 2026-07-03)

**Source:** D04 §6.1  
**File:** `src/domains/optimization/feature_flags.py:16`  
**Finding:** The entire adventure decision pipeline — route generation, opportunity scoring, blocker-penalty evaluation, strategic project assignment — is inactive in all default simulation runs. Every economic balance measurement is running against a disabled pipeline.  
**Impact:** D04 §6, D06 F1/F4 measurements remain invalid until this is resolved. All 8 feature flags listed in `feature_flags.py:14–22` default to `OFF`.  
**Resolution:** Option B taken — flag stays `OFF` by default (confirmed still `FeatureMode.OFF` in
`feature_flags.py:16` as of 2026-07-03); test/calibration harnesses inject it explicitly where
needed (`simq_routing_test`). Documented in `known_limitations.md §1.5` and
`intentional_divergences.md DEV-002`. Reconfirmed as the correct, intentional state (not a gap) by
`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`, which formally documented AGENCY=C in all non-routing
calibration worlds as archetype-correct given this decision.
**Fix (historical, superseded by the decision above):**
- Enable in non-test runs: change default to `FeatureMode.ON` in `feature_flags.py`
- Keep `OFF` as default but require test harness to set `ON` explicitly for all balance/behavioral tests (document in `docs/engine/known_limitations.md`)

Record the decision in `docs/guidelines/intentional_divergences.md` and update `ENABLE_ADVENTURE_ROUTING` parity ledger entry.

**Cross-reference:** `docs/audits/D20_simq_integration.md`'s Verification section confirms this flag is the sole root cause of AGENCY pillar zero-scores in sandbox_world and all other default-mode SimQ calibration worlds — not an AgencyScorer or EventExtractor defect (TCK-20260701-SIMQ-AGENCY-ROUTING-DOC).

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

### P1-A: Rejection cascade has no backoff — 500K–650K/run at 1,000 ticks — **RESOLVED (verified 2026-07-03)**

**Source:** D03 F3, D04 §4, D06 F3  
**Files:** `src/core/state.py` (`ProjectState`), `src/engine/apply.py`, `src/engine/interaction.py`  
**Finding:** After the RC1 fix, the opportunity pipeline runs at full volume but many requirements fail every tick (near_service, inventory_space, has_item). Without a cooldown or expiry mechanism, failed requirements are retried every tick indefinitely. Rate: ~650 rejections/tick → ~550K cumulative at tick 1,000. This scales to 3–4M at tick 5,000 — memory and diagnostic noise risk.  
**Resolution:** `ProjectState.failure_count` (`src/core/strategic.py:253`) is now tracked and checked
against `_MAX_CONSECUTIVE_REJECTIONS` in `src/systems/strategic_systems/intelligence.py:1162-1180`
— the max-retry-count option from the fix list below, implemented: a project's `failure_count`
increments on rejection, resets to 0 on success, and the project is abandoned once the threshold
is crossed.

Original fix options considered (implemented option: max-retry count):
- Max-retry count per project: abandon project after N consecutive rejections (N ~= 20)
- Tick-expiry: mark project stale after M ticks without progress (M ~= 50)
- Requirement cooldown: suppress re-evaluation of a failed requirement for K ticks

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

### P1-C: Faction & Diplomacy System `[M]` — **RESOLVED (verified 2026-07-03; was already stale when this doc was written 2026-06-27)**

**Source:** D01 §Faction & Diplomacy System  
**Finding:** Faction interaction logic (alliance formation, diplomatic posture, war declarations) is absent. 16 factions exist in the catalog with 14 explicit relationships, but the engine has no system that uses faction stance to drive entity-level behavioural differences in encounters.  
**Resolution:** `docs/audits/D01_rpg_feature_impact.md` itself already marked this
**RESOLVED (2026-06-23)** via `TCK-20260619-E53-FACTION-DIPLOMACY` (16 child tickets,
`docs/systems/faction_contract.md` authoritative) — four days *before* this document was written
(2026-06-27), so this entry was stale from the moment it was authored, not a regression.
`src/engine/faction_decision.py` confirmed to implement `DiplomaticStateMachine` transitions
(NEUTRAL→TENSE→ALLIED/WAR) and `MilitaryConflictPhase`/territory-transfer consequences, driving
real entity-level and world-level behavior from faction stance. Separately, this session's
`TCK-20260702-SIMQ-UPLIFT2-FACTION` fixed a narrower, unrelated SimQ-scoring bug in this same area
(`WorldCompiler` never seeding initial `tension_level`, so `compute_transitions()` never had
nonzero tension to act on) — that ticket did not implement the diplomacy system itself, which
already existed; it only made the SimQ FACTION pillar's calibration signal reachable.

---

### P1-D: Pressure-Driven Quest Generation `[M]` — RESOLVED — TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE

**Source:** D01 §Pressure-Driven Quest Generation  
**Files:** `src/quests/generator.py`  
**Finding:** `QuestGenerator` uses `building_id` for quest assignment, not pressure signals (resource scarcity, threat level, regional trauma). Quest content is static rather than emerging from world state. The `ResourceOpportunityProvider` generates opportunities from world state, but the quest layer does not.  
**Fix:** Extend `QuestGenerator` to accept world-state signals (resource scarcity by region, threat level, trauma score) and select quest templates that match the current pressure. See `docs/mechanics/05_world_evolution.md` §trauma and `docs/mechanics/03_economic_laws.md` §resource pressure for the driving signals.
**2026-07-03 re-check:** `QuestGenerator` (`src/quests/generator.py`) confirmed still using a
static, hero-level-keyed `TEMPLATES` list (`QuestTemplate("q_slime_cull", ..., level 1-5, ...)`
etc.) — no world-state pressure signal input found. Still open, no ticket exists yet.

**RESOLVED (2026-07-04, TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE)** — `GuildAction.visit()`
(`src/town/guild.py`) now derives a `QuestPressureProfile` (region `trauma_score`/`hazard_level`
plus a node-charge-ratio-derived scarcity signal) at read time and passes it to
`QuestGenerator.generate()`, which weights template selection via a new
`DeterministicRNG.weighted_choice()` primitive while leaving hero-level gating untouched. A
neutral/`None` profile collapses to the exact pre-existing `rng.choice()` draw (proven
byte-identical). See `docs/mechanics/05_world_evolution.md` §3 "Derived Scarcity Ratio".

---

### P1-E: Domain-phase layer has no audit inventory (D09 Finding 3) — **RESOLVED**

**Source:** D09 Finding 3 — Risk 13/15  
**Resolution:** `docs/audits/D19_domain_phase_inventory.md` created (TCK-20260627-P1E-DOMAIN-INVENTORY). All domain phases in `pipeline.py:refine()` and `world_dynamics.py:resolve_dynamics()` inventoried with wiring status and phase anchors. Used by all SimQ scorers as grounding reference.

---

### P1-F: `AbandonmentEvaluator.evaluate_abandonment()` returns untyped dict — **RESOLVED (verified 2026-07-03)**

**Source:** D12 F2  
**File:** `src/domains/commitment/abandonment.py`  
**Finding:** Returns `Dict[str, Any]` with mechanical fields `is_betrayal` (bool) and `penalty` (float). A key rename silently breaks callers with no type error.  
**Resolution:** `AbandonmentCategory(str, Enum)` and `AbandonmentClassification` dataclass now exist
in `src/domains/commitment/abandonment.py` exactly as specified below (`SURVIVAL`,
`GREEDY_DESERTION`, `VOLUNTARY_QUIT` variants confirmed in use).

Original fix (implemented as specified):
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

---

### P1-G: Phase Stability Guard is audit-mode only — isolation breaches invisible in standard runs — **RESOLVED (verified 2026-07-03)**

**Source:** D09 Finding 5 — Risk 11/15  
**File:** `src/engine/kernel.py` (`_guard_stability()`, `_tick_once_inner()`)  
**Finding:** `_guard_stability()` fingerprints `AuthoritativeState` between phases to catch isolation breaches. It is only active when `Kernel` is initialized with `audit_mode=True`. An isolation breach (a phase mutating state outside the authoritative pipeline) would be invisible in normal production runs.  
**Resolution:** `docs/engine/known_limitations.md` §"Isolation breaches in non-audit phases are only
fully caught in `audit_mode=True`" documents exactly which violation types are caught in standard
mode vs. `audit_mode=True` (including a table of violation types by mode), satisfying the
documentation half of the action item. The lightweight-guard-in-standard-mode enhancement was not
pursued — documentation of the current boundary was judged sufficient.

---

### P1-H: Goal score history over ticks — runner-up scores discarded — **RESOLVED (verified 2026-07-04; the 2026-07-03 "still open" re-check was a false negative)**

**Source:** D15 Gap 1 (partial — trace writer added but runner-up scores not retained)  
**Files:** `src/domains/adventure/phase.py`, `src/observability/cognition/recorder.py`  
**Finding:** `source_goal_score` in cognition snapshots captures only the winning project's score. Runner-up scores (why goal X won over Y) are computed transiently in `execute_brain()` and discarded at tick boundary. Developer cannot distinguish "entity stuck because all alternatives scored lower" from "entity stuck on high-priority goal that should be interrupted."  
**Fix (historical, already implemented):** Retain top-3 candidate scores at tick commit in the cognition snapshot. Add to `EntityInspectionSnapshot.goal_scores` field. Existing `decision_trace.jsonl` infrastructure can carry the data — extend the trace record schema.
**Resolution:** `TCK-20260627-P1H-GOAL-RUNNERUP` (done 2026-06-27) already implemented exactly this
fix — `src/observability/cognition/decision_trace_writer.py::DecisionTraceWriter.write_trace()`
(lines 84-133) sorts candidates descending and emits `source_goal_score` (winner) +
`runner_up_scores` (ranks 2-3, gracefully truncated below 3 candidates), maintaining a bounded
per-entity cache (`_latest_goal_scores`) matching the repo's established O(1)-memory-boundedness
pattern (§2.16/§2.10 in `docs/guidelines/intentional_divergences.md`).
`src/observability/live/entity_inspector.py::EntityInspectionSnapshot.goal_scores` (line 31) is
populated from that cache. `docs/observability/decision_trace_contract.md` documents the full
schema ("Goal Score Cache" section). `tests/unit/observability/test_decision_trace.py` has 4
dedicated tests (`test_decision_trace_runner_up_scores_present`, `_source_goal_score_present`,
`_runner_up_fewer_than_3`, `_runner_up_single_candidate`) — confirmed passing (24/24) 2026-07-04.
**2026-07-03 re-check correction:** the prior "still open" re-check grepped `recorder.py` and
`phase.py` — the files named in the *original pre-fix* finding above — and found nothing, a false
negative. The actual fix landed in `decision_trace_writer.py` and `entity_inspector.py`, neither of
which was checked. `recorder.py` is a genuinely separate system (the cognition graph-snapshot/diff
recorder feeding narrative diffing, with its own single-value `source_goal_score` copied from
`ProjectState.score`) that was never in scope for the 2026-06-27 fix and is not what this finding's
acceptance criteria target — confirmed via `TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE`'s investigation.

---

## P2 — Architectural Debt and Quality Gaps

### P2-A: 200-tick activation delay from initial spawn project locks — **RESOLVED (verified 2026-07-03)**

**Source:** D06 F2  
**Files:** `src/engine/apply.py`, `ProjectState`  
**Finding:** Initial spawn projects lock entities via `lock_until_tick` for ~200 ticks post-combat. 20% of a standard 1,000-tick run is enforced dead time. Lock may be too aggressive if it's a fixed value rather than conditional on threat resolution (entity health restored, combat enemies dead).  
**Resolution:** `src/systems/strategic_systems/intelligence.py:1266,1340` now sets
`lock_until_tick=min(current_tick + 20, current_tick + 50)` (and similar), explicitly capped at
50 ticks as the fix requested — well under the original ~200-tick fixed delay.

---

### P2-B: Late-run attrition exceeds spawn rate — entity count trends toward zero

**Source:** D06 F5  
**Files:** `src/systems/world_systems/spawn.py` (`SpawnService`)  
**Finding:** SpawnService fires at ~tick 500 and adds 3 entities but combat attrition in ticks 800–1000 kills faster than spawn rate. Net entity count at tick 1,000 is below starting count (13.1 vs 15 for seed 42). A 5,000-tick run risks approaching zero.  
**Fix:** Tune `SpawnService` cadence or spawn count so entity population is stable over 5,000 ticks. Target: alive_avg stays ≥ 12 (80% of starting count) throughout. Consider two spawn cadence tiers: early slow spawn, late fast spawn to compensate attrition.

**RESOLVED (verified 2026-07-04, TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS)** — code inspection
confirms `SpawnService.process_spawns()`'s two-tier cadence (`src/world/spawn.py`) is present and
functioning exactly as `TCK-20260627-P2B-SPAWN-CADENCE` designed; no logic regression from the
file relocation. **Distinct finding:** the "159†"/"101‡" early-termination markers recorded in
the 13-run corpus table below for `frontier_extended`/`frontier_living_world`/
`wilderness_survival` were NOT caused by spawn cadence (P2-B is a *late*-run, tick 500+ mechanism;
the collapse there happens by tick 50) — they were a stale-compile / missing `hazard_kind` content
gap, separately root-caused and fixed under this ticket. See
`stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md` Findings 1-4.

**2026-07-09 follow-up (`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`,
`TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`):** the same missing-`hazard_kind`
bug class recurred in 4 more world modules the 2026-07-04 sweep didn't cover
(`ruins_mystery_quest`, `scalable_bandit_camp`, `trading_company_hub`, `moon_cult_ruins`),
collapsing `dungeon_crawl` (early-tick), `urban_political` (two-phase), and `generated_frontier_3_42`
(late-tick, 800→1000). All fixed via the same per-module `hazard_kind`/`hazard_immunities`
authoring pattern. This is now the **third** time this exact bug class has recurred across
separate sweeps (2026-06-30 sandbox_world, 2026-07-04 5-world sweep, 2026-07-09 this pass) — each
time because a newly-anchored or newly-investigated module wasn't in the prior sweep's list, not
because the mechanism itself is broken. See **P2-O** below for a proposed structural fix (a
corpus-wide completeness test) rather than continuing to fix this reactively, module by module.

---

### P2-C: Entity archetype distribution skewed — 4 scouts, underrepresented roles — **RESOLVED (verified 2026-07-03)**

**Source:** D07 F4 — Gap Risk 9/15  
**Files:** `data/content/entity_archetypes/` (now consolidated to `data/content/entities/entity_archetypes.yaml`)  
**Finding:** 21 archetypes, but 4/21 are the same role (scout). No dedicated mage/caster role has more than 1 entry. Encounters pull mostly scout-type entities, reducing variety.  
**Resolution:** Now 29 archetypes across 18 distinct roles, including 3 `mage`, 2 `healer`, 3
`leader`, 2 `hunter`, 2 `predator_hunter`, 2 `raider` — the previously-single mage/healer/leader
roles now have dedicated variants. `scout` remains the largest single role at 4/29 (~14%), down
from 4/21 (~19%) proportionally, and no role dominates the distribution.

---

### P2-D: Faction relationships sparse — 14 defined for 16 factions — **RESOLVED (verified 2026-07-07)**

**Source:** D07 F6 — Gap Risk 8/15  
**Files:** `data/content/social/faction_relationships.yaml`  
**Finding:** 14 faction relationships for 16 factions (120 directed pairs possible). Factions without explicit relationships default to neutral, reducing encounter variety.  
**Fix:** Define relationships for at least 50% of active cross-faction pairs (30+ entries). Focus on conflict and economy module factions first (highest encounter frequency).  
**Resolution:** `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS` took the catalog from 34 entries
(20/120 raw pairs, 16.7%) to **75 entries (41/120 raw pairs, 34.2%)**. Graded against the
populated-only 66-pair basis (the 12 factions with a live module-population path today — see the
ticket's Implementation Notes for UQ-1's resolution), coverage reached **34/66 (51.5%)**, exceeding
the 50%+ target. `neutral` gained its first-ever explicit relationship entry
(`hostility: "none"`, deliberately bounded blast radius since `neutral` is the universal
`get_faction_id_str()` fallback ID). The investigation for this ticket found the catalog is a live
input to `LegalityServiceV2.verify_attack_legality()` (Friendly Fire law) and
`CombatRewardClassificationService.classify_defeated_target()` (`COMB-280`), not inert content —
the implementation added targeted regression tests for every newly-affected faction pair and a new
parity ledger entry (`COMB-294`, `docs/parity_ledger/combat_movement.yaml`) documenting the two
consumers' independent fallback mechanisms. `make evaluate-full` (real engine re-run): 610 pillars
checked, 0 regressions.

---

### P2-E: Feature-gated phases have no per-scenario default test — **RESOLVED (verified 2026-07-07)**

**Source:** D09 Finding 4 — Risk 9/15  
**Files:** `src/domains/optimization/feature_flags.py`, `data/content/simulation_scenarios/`  
**Finding:** 8 pipeline phases are gated behind `FeatureMode` flags. No test verifies that the correct default flag values are set per scenario type. A misconfigured scenario silently loses features.  
**Fix:** Add a test in `tests/integration/` or `tests/certification/` that loads each scenario definition and asserts expected flag states. At minimum assert that the flags required for that scenario's content type are `ON` or `SHADOW`.  
**Resolution:** This finding spans two distinct mechanisms, only one of which had prior coverage.
`TCK-20260627-P2E-FEATURE-FLAG-TEST` (`INFRA-221`, `tests/integration/test_scenario_feature_flag_defaults.py`)
closed the scenario-definition half (`data/content/simulation_scenarios/*.yaml`, flag defaults
derived from the `perspective` field). `TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL`
(`INFRA-262`, `tests/integration/test_world_profile_feature_flag_guardrail.py`) closes the
calibration-profile half (`config/simulation_quality/profiles/<world>.yaml`, the
`_load_profile_feature_flags()` mechanism `tools/calibrate_simq.py` uses to apply per-world flag
overrides) — asserting expected `ENABLE_ADVENTURE_ROUTING`/`ENABLE_BELIEF_ASSIMILATION`/
`ENABLE_SELF_MODEL_COGNITION` state for all 17 corpus worlds, both directions of the Pattern-6
content/flag pairing, and the `ENABLE_ADVENTURE_ROUTING` AGENCY-DA anti-drift guard as a standalone
named test.

---

### P2-F: Canonical state hashing conditionally active — recorded as "SKIPPED" — **RESOLVED (verified 2026-07-03)**

**Source:** D09 Finding 6 — Risk 8/15  
**Files:** `src/engine/kernel.py` (`_phase_persistence()`)  
**Finding:** `CanonicalStateHasher.get_hash()` is only called when `replay_richness == "FULL"` or `audit_mode=True`. Standard runs record `"SKIPPED"`. Full hash traceability is absent in normal runs; only the lighter `fingerprint()` runs.  
**Resolution:** `docs/engine/known_limitations.md` §"Canonical State Hash Availability by Runtime
Mode" documents exactly which `RuntimeMode`/`replay_richness` combinations produce `"SKIPPED"`
(a full table by mode), and confirms the final canonical hash at `Kernel.shutdown()` is always
computed regardless of mode. Documentation action item satisfied as specified.

---

### P2-G: `hard_law_monitor.py` imports `WorldIndexService` directly — **RESOLVED (verified 2026-07-03)**

**Source:** D14 F3 — Risk 8/15  
**File:** `src/observability/hard_law_monitor.py:10`  
**Finding:** Other observability files (`sweeper`, `controller`, `harness`) only import `Kernel`. `hard_law_monitor` reaches into `src.engine.world_index.WorldIndexService` — a concrete engine internal. If `WorldIndexService` interface changes, the monitor breaks without a visible dependency signal.  
**Resolution:** `hard_law_monitor.py`'s imports now only reach `src.core.state`, `src.core.dirty`,
`src.observability.config`, and `src.engine.kernel.Kernel` — no direct `WorldIndexService` import
remains.

---

### P2-H: `kernel.py:804` direct `entity.timeline.append()` mutation — **RESOLVED (verified 2026-07-03)**

**Source:** D12 F5 — Priority 6/15  
**File:** `src/engine/kernel.py:804`  
**Finding:** Single direct mutation of `entity.timeline` outside the authoritative pipeline. Minor pattern violation; if timeline management grows, this becomes a coupling risk.  
**Resolution:** No `entity.timeline.append(...)` pattern remains anywhere in `kernel.py` — confirmed
by grep. Timeline management has since moved to the event emission layer as recommended.

---

### P2-I: `lab/workflows.py` all `run()` methods return `dict[str, Any]` — **RESOLVED (verified 2026-07-03)**

**Source:** D13 F4 — Risk 7/15  
**File:** `src/lab/workflows.py`  
**Finding:** All 7 `Workflow.run()` methods return `dict[str, Any]`. Callers access keys (`result["summary"]`, `result["health_score"]`) by string convention. A renamed key only surfaces at runtime.  
**Resolution:** All 7 `run()` methods now return dedicated typed result classes:
`GenerateSimulationSetupResult`, `PrepareSimulationExecutionResult`,
`RegisterSimulationResultResult`, `CompactSimulationDataResult`,
`InvestigateSimulationResultResult`, `ProposeSimulationEnhancementsResult`,
`UpdateSimulationKnowledgeResult` — no `dict[str, Any]` return remains.

---

### P2-J: `engine/patches.py` `merge()` returns `Any` — **RESOLVED (verified 2026-07-03)**

**Source:** D13 F5 — Risk 6/15  
**File:** `src/engine/patches.py:29`  
**Finding:** Only `Any`-return in an engine-tier module that is not a serialization helper. A type error in a merged patch value is invisible until the downstream pipeline consumer processes it.  
**Resolution:** Every `merge()` method across all patch classes (`KindPatch`, `LifecyclePatch`,
`BiologicalPatch`, `InteractionPatch`, `IdentityPatch`, `NavigationPatch`, `CombatPatch`,
`StaminaPatch`, `InventoryPatch`, `EquipmentPatch`, `StrategicPatch`, `QuestPatch`, `SocialPatch`,
`TaskPatch`, `AttributePatch`, `RewardPatch`, `WoundPatch`, and the generic `Self`-typed base)
now returns its own specific type — no `Any` return remains.

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

### P2-M: Release reports are ephemeral — no CI artifact upload — **RESOLVED (verified 2026-07-03)**

**Source:** D18 F5 — Risk 5/15  
**Files:** `.github/workflows/test.yml`  
**Finding:** `reports/certification/` and `reports/release_proof/` are local ephemeral output. CLAUDE.md §After Work instructs `rm -rf reports/release_proof/*`. No CI artifact preserves these per commit SHA.  
**Resolution:** `.github/workflows/test.yml` now has an `actions/upload-artifact@v4` step
("Upload certification report") archiving `reports/certification/` as `certification-report-${{ github.sha }}`,
exactly as specified.

---

### P2-N: D02 §6.6 — Hardcoded fallback content source path

**Source:** D02 §6.6 `[P]`  
**File:** `src/domains/optimization/degradation.py` or equivalent  
**Finding:** `runtime_content_source = "legacy_hardcoded"` persists as the default in non-strict modes. Content loading falls back to hardcoded paths rather than the catalog system in degraded mode.  
**Fix:** Replace the hardcoded default with a catalog-driven fallback. In strict mode, raise immediately; in degraded mode, select the lowest-cost catalog entry for the requested content type rather than a static path. Update `GracefulDegradationManager` contract.

---

### P2-O: `hazard_kind` completeness has recurred 3 times as a reactive, per-sweep fix — needs a structural test — **RESOLVED (verified 2026-07-11)**

**Source:** `docs/audits/D20_simq_integration.md` §"SimQ Uplift Batch 4"; new, added 2026-07-09  
**Files:** `tests/unit/worldassembly/test_corpus_diversity.py` (`HAZARD_KIND_MATCH_WORLDS`, `test_hazard_kind_matches_populating_faction_immunity`)  
**Finding:** The same bug class — a world module declares `hazard_level > 0` on a region but never
declares `hazard_kind`, so `src/worldassembly/resolver.py:798` silently defaults it to `"PHYSICAL"`,
which no faction is ever immune to, causing unconditional lethal drain to the region's own populating
faction — has now been found and fixed **three separate times**: 2026-06-30 (`sandbox_world`'s
`woods`/`wolf_den`), 2026-07-04 (7 modules across 5 worlds, `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`),
and 2026-07-09 (4 more modules across `dungeon_crawl`/`urban_political`/`generated_frontier_3_42`,
`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` + `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`).
Each time, the fix was correct and narrow, but the *coverage* was reactive — limited to whichever
modules that specific investigation happened to touch. `test_hazard_kind_matches_populating_faction_immunity`
exists but is scoped to an explicit allowlist (`HAZARD_KIND_MATCH_WORLDS`), not run corpus-wide, so a
5th/6th recurrence in an unlisted world/module would not be caught until another investigation
stumbles onto it.  
**Fix:** Extend `test_hazard_kind_matches_populating_faction_immunity` (or add a sibling test) to run
against every world in the corpus, not just the allowlist — for every populated region with
`hazard_level > 0`, assert its `hazard_kind` is declared and matches at least one entry in its
populating faction's `hazard_immunities` (or is explicitly documented as intentional exposure, per the
P2-P question below). This converts a reactive per-investigation fix pattern into a corpus-wide
completeness guarantee, closing the gap class permanently rather than one sweep at a time.
**Sequenced as Phase 1.1** in `docs/plans/archive/simq_development_roadmap.md`.
**Resolution:** `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` (2026-07-11) replaced
`HAZARD_KIND_MATCH_WORLDS`'s 3-world allowlist with `ALL_CORPUS_WORLDS`, parametrizing
`test_hazard_kind_matches_populating_faction_immunity` over every world under `data/worlds/*`
(17 worlds). The corpus-wide run passed cleanly — 0 mismatches across 45 hazardous-populated-
region checks, including every `bandit_road`/`town_council` occurrence (that case passes under
the test's existing region-level "any populating faction" matching semantics; see the code
comment on the test itself and `docs/guidelines/intentional_divergences.md` §2.30). No `src/`
or content changes were required; test-file-only change.

---

### P2-P: Wall-clock-dependent non-determinism past ~tick 300-320 (tick-budget throttle) — long-run SimQ anchor reliability unverified — **RESOLVED (verified 2026-07-11)**

**Source:** `docs/audits/D06_longrun_health.md` F6; new, added 2026-07-09 (`TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`)  
**Files:** `src/engine/kernel.py` (tick-budget watchdog `kernel.py:420-442`, mid-tick emergency throttle `kernel.py:574-601`)  
**Finding:** Two back-to-back same-seed, same-code runs of `generated_frontier_3_42` diverged by
100+ ticks in when the 60%-alive floor is first violated, and by more than 2× in the tick-1000
population endpoint. Root cause: both throttle paths measure real wall-clock compute time and drop
resolution work mid-tick when it's exceeded — which entities get dropped depends on system load/
scheduler timing, not the deterministic seed. This is documented, intentional engine behavior
(`docs/engine/kernel.md` §"Emergency Throttling"), not a bug to fix here — see D06 F6 for full detail
and the explicit scope guard against touching `kernel.py`'s throttle logic.  
**Fix (documentation/verification, not an engine change):** Determine whether any already-shipped
1000t/2000t SimQ calibration anchor (`tests/simulation_quality/fixtures/grade_anchors.json`,
`SLOW_ANCHOR_KEYS`) is throttle-timing-sensitive — i.e. would a fresh re-run at the same seed produce
a different grade purely from throttle-timing variance, not genuine behavior drift? If so, either (a)
re-verify those anchors with a multi-run tolerance check (same pattern as
`test_generated_frontier_3_42_extended_population_stability`), or (b) explicitly document in
`eval_matrix_results.md` that single-run long-tick anchors carry unquantified throttle-variance risk.
Cross-reference D06 F6's "Recommended Follow-Up" entry — same finding, tracked in both places since
D06 owns the engine-health angle and this doc owns the actionable-backlog angle.
**Sequenced as Phase 0.1** in `docs/plans/archive/simq_development_roadmap.md` — the roadmap's first,
blocking phase.
**Resolution:** `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` (2026-07-11) re-ran all 18
`SLOW_ANCHOR_KEYS` 3 times each at the same seed (54 total runs, real throttled `Kernel`, no
`audit_mode`) — **18/18 keys stable**, none required a tolerance-guard conversion, none flagged
unverified. Every one of 540 pillar/trial data points fell within the existing ±1-`GRADE_ORDER`
band despite confirmed throttle variance (`budget_warnings` 41–539/run, `watchdog_trips` 1–3/run,
up to ~4× elapsed-time spread for identical seed/code). Full per-key evidence documented in
`docs/simulation_quality/eval_matrix_results.md`'s "Anchor Reliability Verification" section.
`kernel.py` and `grade_anchors.json` left untouched, per this finding's own scope guard.

---

### P2-Q: Non-native factions stationed in a hazardous region with no immunity — recurring open design question, never formally resolved

**Source:** `stored_artifacts/TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE/investigation.md` Risk #2;
recurred verbatim in `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`'s investigation
(Root cause 2). New, added 2026-07-09.  
**Files:** `data/content/social/factions.yaml` (`town_council`), `bandit_road`-composing world modules  
**Finding:** In both `urban_political` and `generated_frontier_3_42`, `town_council`'s
`merchant_caravan_frontier_guard` entities are stationed at `bandit_road` (a `NATURAL_TERRAIN`-hazard
region correctly exempting its native `bandit_company` occupants) but `town_council` itself declares
no `hazard_immunities`, so its 2 guards there take slow, continuous hazard drain over a long run. Both
investigations independently found this, both correctly declined to fix it (per the Anti-Drift
guidance against blanket/wildcard immunities), and both deferred it as "may be intentional
'conflict-pressure' flavor — a guard escort posted to a bandit-contested road taking losses over a
campaign" — but neither made or recorded an actual decision. This is now the **second** time the
identical question has surfaced and been silently re-deferred rather than resolved once.  
**Fix:** Make an explicit DA (design-acknowledgment) ruling, once, applicable to both worlds (and any
future world reusing this pattern): either (a) rule it intentional flavor and record the decision in
`docs/guidelines/intentional_divergences.md` so future investigations cite the ruling instead of
re-deriving the question, or (b) rule it a genuine gap and add a `NATURAL_TERRAIN` (or a new,
narrower) `hazard_immunities` entry for `town_council`. Either answer is fine — what's missing is a
recorded answer, not more investigation.
**Sequenced as Phase 1.2** in `docs/plans/archive/simq_development_roadmap.md`.
**Resolved (2026-07-10):** Ruled (a) intentional by `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` — see
`docs/guidelines/intentional_divergences.md` §2.30. `town_council`'s bandit_road exposure is
ratified as designed non-native conflict-pressure flavor; no content or code change made.

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

### P3-B: ObservabilityMode naming mismatch — STANDARD maps to LIGHT engine mode — **RESOLVED (verified 2026-07-03)**

**Source:** D03 F5 — Score 8/15  
**File:** `src/lab/orchestrator.py:147–153`  
**Finding:** Lab mode `"STANDARD"` maps to engine `ObservabilityMode.LIGHT`. A developer switching to STANDARD expecting richer data gets identical output to LIGHTWEIGHT. Diagnosis tooling gap.  
**Resolution:** `src/lab/orchestrator.py` now maps `"STANDARD": ObservabilityMode.NORMAL`, with an
explicit comment confirming the remap was intentional ("STANDARD maps to NORMAL (not LIGHT) so
developers switching to STANDARD..."). `make sim-debug` target also exists in the Makefile.

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

### P3-D: Catalog ID browser and scenario template discoverability — **PARTIALLY RESOLVED (verified 2026-07-03)**

**Source:** D16 Structural Gaps  
**Finding:** No way to list valid biome/ecology/population/faction IDs without running assembly code. 10 scenario templates in `src/scenarios/templates.py` are undocumented.  
**Resolution:** `make catalog-list` target exists ("List catalog IDs by type (biomes, ecologies,
populations, factions, regions)") — the catalog-browser half of this item is done. The 10
scenario-template documentation half was not verified — check `docs/guides/content_authoring.md`
(P2-L) for scenario template coverage before closing this item fully.

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
| dungeon_crawl | 42 | 200 | A | B | B* | C | C | C | C | C | C | A |
| dungeon_crawl | 42 | 1000 | B | B | B | C | C | C | C | C | C | B |
| urban_political | 42 | 200 | B | A | B | C | C | C | C | C | C | A |
| simq_routing_test | 42 | 500 | B | A | B | **B** | C | C | C | C | C | B |
| frontier_extended | 42 | 200 | B | A | B | C | C | C | C | C | C | B |
| frontier_living_world | 42 | 200 | B | A | B | C | C | C | C | C | C | B |
| swamp_border_world | 42 | 200 | C | A | C | C | C | C | C | C | C | B |
| highland_traverse | 42 | 200 | B | A | C | C | B | C | C | C | C | B |
| wilderness_survival | 42 | 200 | C | C | C | C | C | C | C | C | C | B |

\*Refreshed 2026-07-02 (TCK-20260701-SIMQ-CALIBRATE-REFRESH): dungeon_crawl/urban_political re-run post-emit-epic. PROGRESSION dropped A→B in dungeon_crawl 200t — new progression emitters add both positive and negative deltas net-reducing normalized score. grade_anchors.json updated to B. All other refreshed grades unchanged from prior corpus.
**Update 2026-07-04 (TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS):** The `frontier_extended`/
`frontier_living_world`/`wilderness_survival` rows above no longer show early termination — the
`159†`/`101‡` markers previously recorded here were misattributed to P2-B (see the P2-B section
above, now RESOLVED with a distinct-finding note) and were actually a stale-compile / missing
`hazard_kind` content gap. All five rows above reflect fresh 200-tick, seed-42 calibration runs
taken after that gap was fixed and each world was recompiled and re-verified for population
stability (>=60% alive floor through 300 ticks — see
`stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md` Findings 1-4 and
`docs/simulation_quality/eval_matrix_results.md` §Newly-Anchored Worlds for the full 3-seed
tables). All five worlds are now anchored in `tests/simulation_quality/fixtures/grade_anchors.json`.

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
**Superseded 2026-07-04 (TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS):** the original text here read
"wilderness_survival terminates at tick 101 with 11 entities ... confirms P2-B" — that
early-termination and P2-B attribution were incorrect (see the P2-B section's Distinct Finding and
the 13-run corpus table's 2026-07-04 update above). wilderness_survival now runs the full 200+
ticks without early termination; NARRATIVE=C is a genuine low-entity/short-run signal (11
entities, few quest-pursuing agents), not evidence of attrition outpacing spawning.

**Finding 6: Larger multi-module worlds show COMBAT and PROGRESSION signal.**  
**Superseded 2026-07-04 (TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS):** the original text here read
"frontier_extended ... and frontier_living_world ... both score COMBAT=A and PROGRESSION=A at 200
ticks ... They also terminate early (tick 159) — confirming P2-B" — that early-termination and
P2-B attribution were incorrect (same root cause as Finding 5). Both worlds now run the full 200
ticks without early termination; post-recompile they score COMBAT=B and PROGRESSION=B (down from
the pre-fix A/A, itself an artifact of the population having already collapsed to a small,
easily-saturated residual — see `docs/simulation_quality/eval_matrix_results.md` §Newly-Anchored
Worlds for the current, stable grades).

**Finding 7: Quest location fix has no grade impact (correct).**  
The TCK-20260630-WORLD-QUEST-LOCATION fix eliminated 28 compile warnings by validating `required_location_tags` against `region.type`/`region.tags` instead of `region.id`. This fix was compile-time validation only — the runtime quest activation path (P1-B) is not gated by this validation. quest_completed grades remain 0 across all worlds, as expected until P0-A and P1-B are addressed.

### Revised blocker assessment after re-evaluation

| Blocker | Status |
|---|---|
| P0-A ENABLE_ADVENTURE_ROUTING | **RESOLVED** — TCK-20260627-P0A-ADVENTURE-FLAG. Option B: all Phase 10 flags remain OFF by default; documented in `known_limitations.md §1.5` and `intentional_divergences.md DEV-002`. AGENCY=B achievable via env-var inject (confirmed by simq_routing_test). (seed456 specifically now carries a documented D-grade exception post-TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE — see eval_matrix_results.md AC6 section; seed42/seed123 remain unaffected, A/A) |
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
| WORLD dynamics signals | ecology_cycle_completed, spawn_cadence_fired, threat_evolved, node_recharged (camp_constructed excluded — no viable engine path, not an emitter gap; see `event_type_coverage.md` §3.9) | WORLD: already A/B; ecology worlds gain more |
| AGENCY tracking signals | defer_with_reason, commitment_abandoned, rejection_cascade_tick, route_family_first_use | AGENCY: richer signal when routing ON |
| Misc small gaps | paid_info_transaction (ECONOMY), conservation_law_verified (ECONOMY), alliance_proposed (FACTION), resource_seized (FACTION), social_memory_created (SOCIAL), contract_milestone_completed (SOCIAL), scenario_objective_progressed (NARRATIVE) | ECONOMY/FACTION/SOCIAL/NARRATIVE: marginal gains |

Tickets created: `tickets/todos/simq-emit/` (5 tickets, 2026-07-01).

---

## Summary Table

| ID | Source | Priority | Type | Effort |
|---|---|---|---|---|
| P0-A | D04 §6.1 | **P0** | Configuration | **RESOLVED** — decision recorded (flags stay OFF by default); reconfirmed 2026-07-02 by `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` |
| P0-B | D04 §6.2 | **P0** | Content | **RESOLVED** — 3 resource nodes confirmed (2026-07-01) |
| P0-C | D04 §6.3 | **P0** | Engine | S — WorldCompiler entity region assignment |
| P1-A | D03 F3 / D06 F3 | **P1** | Engine | **RESOLVED (verified 2026-07-03)** — `failure_count`/`_MAX_CONSECUTIVE_REJECTIONS` in `intelligence.py` |
| P1-B | D06 F4 | **P1** | Engine | **RESOLVED** — `TCK-20260627-P1B-QUEST-ACTIVATION` |
| P1-C | D01 §Faction | **P1** | Feature | **RESOLVED (verified 2026-07-03; already resolved 2026-06-23 via E53, this doc was stale from authoring)** |
| P1-D | D01 §Quest | **P1** | Feature | **RESOLVED** — TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE |
| P1-E | D09 F3 | **P1** | Docs | **RESOLVED** — D19 exists |
| P1-F | D12 F2 | **P1** | Refactor | **RESOLVED (verified 2026-07-03)** — `AbandonmentClassification` dataclass exists |
| P1-G | D09 F5 | **P1** | Docs/Engine | **RESOLVED (verified 2026-07-03)** — documented in `known_limitations.md` |
| P1-H | D15 Gap 1 | **P1** | Observability | **RESOLVED (verified 2026-07-04)** — `TCK-20260627-P1H-GOAL-RUNNERUP` already implemented this; 2026-07-03 "still open" was a false negative (wrong files grepped) |
| P2-A | D06 F2 | **P2** | Engine | **RESOLVED (verified 2026-07-03)** — conditional lock, capped at 50 ticks, in `intelligence.py` |
| P2-B | D06 F5 | **P2** | Engine | **RESOLVED (verified 2026-07-04)** — TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS; two-tier cadence intact, frontier_extended/frontier_living_world/wilderness_survival symptom re-attributed to hazard-kind staleness (separately fixed, same ticket) |
| P2-C | D07 F4 | **P2** | Content | **RESOLVED (verified 2026-07-03)** — 29 archetypes, 18 roles, no single-role dominance |
| P2-D | D07 F6 | **P2** | Content | **RESOLVED (verified 2026-07-07)** — TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS; `data/content/social/faction_relationships.yaml` 34→75 entries, 34/66 (51.5%) populated-only coverage / 41/120 (34.2%) raw coverage, `neutral` entry added, `COMB-294` parity entry added |
| P2-E | D09 F4 | **P2** | Testing | **RESOLVED (verified 2026-07-07)** — scenario-definition half closed by `INFRA-221`/`TCK-20260627-P2E-FEATURE-FLAG-TEST`; calibration-profile half closed by `INFRA-262`/`TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL` |
| P2-F | D09 F6 | **P2** | Docs | **RESOLVED (verified 2026-07-03)** — documented in `known_limitations.md` §2.4 |
| P2-G | D14 F3 | **P2** | Refactor | **RESOLVED (verified 2026-07-03)** — `hard_law_monitor.py` only imports `Kernel` now |
| P2-H | D12 F5 | **P2** | Refactor | **RESOLVED (verified 2026-07-03)** — no `timeline.append()` pattern remains in `kernel.py` |
| P2-I | D13 F4 | **P2** | Typing | **RESOLVED (verified 2026-07-03)** — all 7 `run()` methods return typed `*Result` classes |
| P2-J | D13 F5 | **P2** | Typing | **RESOLVED (verified 2026-07-03)** — all `merge()` methods return typed patch classes |
| P2-K | D16 Task 3 | **P2** | DX | UNVERIFIED (2026-07-03) — `ContentUsageMatrix` relocated to `src/content/matrix.py`; auto-generation not confirmed — S — verify or add auto-generation |
| P2-L | D16 Gap | **P2** | Docs | **RESOLVED** — docs/guides/content_authoring.md exists |
| P2-M | D18 F5 | **P2** | CI | **RESOLVED (verified 2026-07-03)** — `upload-artifact@v4` step exists in `test.yml` |
| P2-N | D02 §6.6 | **P2** | Engine | OPEN (not re-checked 2026-07-03) — S — catalog-driven degraded fallback |
| P2-O | D20 (new) | **P2** | Testing | **RESOLVED (2026-07-11)** — `test_hazard_kind_matches_populating_faction_immunity` now runs corpus-wide (17/17 worlds) — `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` |
| P2-P | D06 F6 (new) | **P2** | Docs/Verification | **RESOLVED (verified 2026-07-11)** — `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` — 18/18 shipped anchors re-verified stable |
| P2-Q | D06/D20 (new) | **P2** | Docs/DA | **RESOLVED (2026-07-10)** — ruled (a) intentional, see `intentional_divergences.md` §2.30 — `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` |
| P3-A | D01 [P] items | **P3** | Feature | varies — see individual epics (not re-checked 2026-07-03) |
| P3-B | D03 F5 | **P3** | DX | **RESOLVED (verified 2026-07-03)** — `"STANDARD": ObservabilityMode.NORMAL` confirmed |
| P3-C | D17 P2 | **P3** | Docs | OPEN (not re-checked 2026-07-03) — S — verify 4 uncertain claims |
| P3-D | D16 | **P3** | DX | **PARTIALLY RESOLVED (verified 2026-07-03)** — `make catalog-list` exists; scenario-template doc coverage unverified |
| D20-G1 | D20 | **P1** | Engine | **RESOLVED** — TCK-20260630-SIMQ-WIRE-KERNEL (2026-06-30) |
| D20-G2 | D20 | **P1** | API | **RESOLVED** — TCK-20260630-SIMQ-WIRE-SERVER (2026-06-30) |
| D20-G3 | D20 | **P1** | Engine | **RESOLVED** — TCK-20260630-SIMQ-WIRE-KERNEL (2026-06-30) |
| D20-F5 | D20 | **P1** | Tooling | **RESOLVED** — TCK-20260630-SIMQ-RECALIBRATE + TCK-20260630-SIMQ-CALFIX (2026-06-30/07-01) |

**Effort legend:** XS ≤ 1h · S = 2–4h · M = 1–2 days · L = 3–5 days · XL = epic

---

## Suggested Fix Order

Tickets should be created in this sequence to avoid blocked work:

~~All original P0–P3 items, all D20 gaps, all SimQ emit tickets, and all P3-A child epics are
DONE as of 2026-07-01.~~ **Correction (verified 2026-07-03): this claim was inaccurate even at
the time it was written** — it conflated "the 2026-07-01 SimQ emit-gap sequence is done" (true)
with "every P0–P3 item in this document is done" (false). The 2026-07-03 status refresh above
found several P1/P2/P3 items were never resolved and remain genuinely open: **P1-D** (pressure-driven
quest generation), **P1-H** (runner-up goal scores in trace),
**P2-D** (faction relationship coverage %, unverified), **P2-E** (per-scenario flag
test), **P2-K** (ContentUsageMatrix auto-generation, unverified), **P2-N** (degraded-mode catalog
fallback), **P3-A** (feature epics), **P3-C** (mechanics doc verification). The SimQ emit-gap
sequence below was completed as stated — that specific claim holds. (**P2-B** was in this list as
of 2026-07-03; **RESOLVED (verified 2026-07-04)** by TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — see
the P2-B section above. **P1-D** was also in this list as of 2026-07-03; **RESOLVED (2026-07-04)**
by TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE — see the P1-D section above. **P1-H** was also in this
list as of 2026-07-03 but that was itself a false negative — **RESOLVED (verified 2026-07-04)**,
already implemented by the pre-existing `TCK-20260627-P1H-GOAL-RUNNERUP`, discovered during
`TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE`'s investigation — see the P1-H section above. **P2-D** was
also in this list as of 2026-07-03; **RESOLVED (verified 2026-07-07)** by
`TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS` — see the P2-D section above.)

**Completed as of 2026-07-01:** Engine emission gaps (`tickets/todos/simq-emit/`, 5 tickets created 2026-07-01)

1. `TCK-20260701-SIMQ-EMIT-PROGRESSION` — 5 progression signal events
2. `TCK-20260701-SIMQ-EMIT-INFORMATION2` — 5 information/cognition signal events
3. `TCK-20260701-SIMQ-EMIT-WORLD2` — 5 world dynamics signal events
4. `TCK-20260701-SIMQ-EMIT-AGENCY2` — 4 agency tracking events
5. `TCK-20260701-SIMQ-EMIT-SOCIAL2` — 7 misc gaps (ECONOMY ×2, FACTION ×2, SOCIAL ×2, NARRATIVE ×1)

**Still open, no ticket exists yet (per 2026-07-03 status refresh):** P2-N,
P3-A, P3-C — and P2-K pending re-verification against its relocated files. (P2-E resolved
2026-07-07, TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL — no longer pending.) (P2-D resolved
2026-07-07, TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS — no longer pending; see P2-D section
above.) (P2-B resolved 2026-07-04, TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — no longer pending.
P1-D resolved 2026-07-04, TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE — no longer pending. P1-H
resolved 2026-07-04 — was already fixed by TCK-20260627-P1H-GOAL-RUNNERUP, a false negative in the
2026-07-03 refresh — no longer pending.)

**New, added 2026-07-09, from `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`
and `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`'s investigations:** P2-O
(hazard_kind corpus-wide completeness test — 3rd recurrence of the same bug class, highest-leverage
of the three since it prevents future recurrences rather than reacting to them, ticket exists at
`tickets/inprogress/TCK-20260710-HAZARD-KIND-CORPUS-WIDE.md`), P2-P (verify long-run SimQ anchor
reliability against F6's throttle-timing variance — **RESOLVED 2026-07-11**,
`TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`), P2-Q (one DA ruling closes two recurring open
questions — lowest-effort item in this whole document, XS, ticket exists at
`tickets/inprogress/TCK-20260710-TOWN-COUNCIL-HAZARD-DA.md`).

---

## Related Documents

- `docs/audits/D01_rpg_feature_impact.md` — [P]/[M] items are sources for P1-C, P1-D, P3-A
- `docs/audits/D04_balance_tuning.md` — P0-A/B/C findings in §6
- `docs/audits/D06_longrun_health.md` — P1-A/B, P2-A/B, P2-P (F6, new 2026-07-09)
- `docs/audits/D09_system_wiring.md` — P1-E/G, P2-E/F
- `docs/audits/D12_pattern_consistency.md` — P1-F, P2-H
- `docs/audits/D13_type_safety.md` — P2-I/J
- `docs/audits/D20_simq_integration.md` — D20-G1/G2/G3/F5, P2-O/P2-Q (SimQ Uplift Batch 4, new 2026-07-09)
- `docs/audits/D14_coupling_depth.md` — P2-G
- `docs/audits/D15_entity_decision_inspection.md` — P1-H
- `docs/audits/D16_scenario_authoring_dx.md` — P2-K/L, P3-D
- `docs/audits/D17_documentation_currency.md` — P3-C
- `docs/audits/D18_ci_release_pipeline.md` — P2-M
- `docs/plans/long_term_development_roadmap.md` — longer-horizon context for P1-C/D and P3-A
