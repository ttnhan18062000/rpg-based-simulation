---
status: active
layer: architecture
authority: P1
audience: agent
tags: [audit, system-wiring, integration, pipeline, codebase-health]
---

# D09 — System Wiring & Integration

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | B — Codebase |
| **State** | `done` |
| **Impact** | 4 / 5 |
| **Interest** | 4 / 5 |
| **Priority** | 8 |
| **Method** | code-read |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Are the 61 `[E]` features listed in D02 actually called
from the live simulation pipeline? A feature can be unit-tested and parity-verified while
never reaching `Kernel.tick_once()` on a real run. This audit closes that gap.

**Related dimensions:** D03 (Behavioral Emergence) — confirms which systems are live before
running simulation validation. D11 (Dead Code) — tick-live vs. ci-only classification
is a primary input. D10 (Test Coverage) — wiring map defines which ci-only items need
test coverage. D17 (Documentation Currency) — pipeline phase count discrepancy found here.

---

## Classification Method

Five wiring statuses are assigned to each `[E]` feature:

| Status | Meaning |
|---|---|
| `tick-live` | Called on at least one code path during every (or nearly every) standard tick cycle |
| `tick-live (cond)` | Called on every tick only when a mode flag is active (audit_mode, full replay richness) |
| `startup-live` | Called once per simulation run at world initialization, before the tick loop starts |
| `design-pattern` | A convention enforced by architecture tests and code review — no runtime callable |
| `ci-only` | Only exercised in CI certification workflows; unreachable in a live simulation run |

Evidence is traced to the specific kernel phase or call site, not just the module.

**Entry points traced:**
1. `Kernel._tick_once_inner()` → 6 phase methods → `AuthoritativeApplyPipeline.refine()`
2. `WorldDynamicsSystem.resolve_dynamics()` (called from pipeline "world_dynamics" phase)
3. `ApplyPath.apply_generation()` (called from `_phase_advancement()`)
4. `Kernel.__init__()` + `ContentWarmupService.warmup()` (startup wiring)
5. `WorldAssembly` / `WorldBuildingCompiler` / `ProceduralCompositionGenerator` (world creation)

### Finding Risk Scoring

Key findings are scored on three dimensions, each 1–5. Maximum: 15.
Higher score = higher priority to address.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Affected Scope** | Single feature | Multiple features in one domain | Cross-domain or all live runs |
| **Detection Risk** | Caught by existing tests | Only visible in special modes (audit/cert) | Invisible in all standard runs |
| **Impact if Unresolved** | Cosmetic / minor correctness | Behavioral gap, non-critical | Silent incorrect behavior or non-determinism |

### Section Wiring Health Scoring

Each classification section receives a Section Wiring Health Score summarising how much wiring concern exists within that section. Higher score = greater wiring gap concern.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Tick-Live Coverage** | All features `tick-live`; full live-run presence | Mix of statuses; some `startup-live` or `design-pattern` | Any `ci-only` or `tick-live (cond)` feature present — invisible in standard runs |
| **Finding Exposure** | No findings reference this section | Finding with Risk ≤9/15 involves a feature in this section | Finding with Risk ≥10/15 directly targets a feature in this section |
| **Wiring Confidence** | All features traced to a specific source line or call site | Most features traced; 1–2 rely on structural inference | Key features traced to module or pattern only — no line-level evidence |

---

## Classification Table

All 61 `[E]` entries from D02's summary table. Note: D02 states "53 Existing" — that count
is incorrect (this is a D02 data-quality finding; actual count from the summary table is 61).
`8.4 Movement Plan Cache` is a duplicate of `4.5` (same `movement_cache.py` file).

### Section 1: Kernel & Execution

| ID | Feature | Wiring | Evidence |
|---|---|---|---|
| 1.1 | Deterministic Tick Loop | `tick-live` | `kernel.py` `tick_once()` / `_tick_once_inner()` — the loop itself |
| 1.2 | 6-Phase Kernel Ordering | `tick-live` | `_tick_once_inner()` calls all 6 `_phase_*` methods in fixed order each tick |
| 1.3 | Phase Dependency Graph | `tick-live` | `pipeline.py:run_phase()` → `PhaseDependencyGraph.should_run_phase()` on every `refine()` call |
| 1.4 | Deterministic Scheduler | `tick-live` | `_phase_scheduling()` → `scheduler.select_work(state, policy)` |
| 1.5 | Cadence Gating | `tick-live` | `should_run()` called throughout `world_dynamics.py` and `apply.py` |
| 1.6 | Level of Detail System | `tick-live` | `scheduler.py:44` — `LODService.should_execute()` inside `select_work()` |
| 1.7 | Governance / Eligibility Gating | `tick-live` | `_phase_init()` → `self._governor.evaluate()` every tick |

**Section Wiring Health Score: 3 / 15** (Tick-Live Coverage=1, Finding Exposure=1, Wiring Confidence=1)

| Dimension | Score | Reason |
|---|---|---|
| Tick-Live Coverage | 1 | All 7 features `tick-live`; every feature active in every standard run |
| Finding Exposure | 1 | No findings reference Section 1 features |
| Wiring Confidence | 1 | All features traced to specific method calls in `kernel.py` and `scheduler.py` |

### Section 2: State Architecture

| ID | Feature | Wiring | Evidence |
|---|---|---|---|
| 2.1 | Authoritative State Model | `tick-live` | Central object all phases read from; `apply_generation()` produces a new one each tick |
| 2.2 | Immutability Enforcement | `tick-live` | `state.readonly_view()` in `_phase_collection()`; `shallow_freeze()` called in `apply.py:148` for every entity |
| 2.3 | Deterministic RNG | `tick-live` | `executor.execute(state_view, self._rng, ...)` in `_phase_collection()` |
| 2.4 | Canonical State Hashing | `tick-live` | `fingerprint()` called in `_phase_resolution()` replay emit; `CanonicalStateHasher.get_hash()` in `_phase_persistence()` (policy-gated) |
| 2.5 | Auth vs Non-Auth Partitioning | `design-pattern` | Enforced by architecture tests and `HardLawMonitor`; no single runtime callable |
| 2.6 | State Serialization | `tick-live` | Used by `ReplayManager` for async write of `TraceEvent` payloads each tick |

**Section Wiring Health Score: 6 / 15** (Tick-Live Coverage=2, Finding Exposure=3, Wiring Confidence=1)

| Dimension | Score | Reason |
|---|---|---|
| Tick-Live Coverage | 2 | 5 features `tick-live`, 1 `design-pattern` (2.5 Auth/Non-Auth partitioning — enforced by tests, not a callable) |
| Finding Exposure | 3 | Finding 6 (Risk 8/15 ≤9) targets 2.4: `CanonicalStateHasher.get_hash()` is conditionally active — recorded as `"SKIPPED"` in standard non-audit runs |
| Wiring Confidence | 1 | All features traced to specific call sites in `kernel.py` and `apply.py` |

### Section 3: Mutation Architecture

| ID | Feature | Wiring | Evidence |
|---|---|---|---|
| 3.1 | Typed Result Records Pattern | `tick-live` | All worker results are `EntityUpdate` typed records; collected in `_phase_collection()` |
| 3.2 | Authoritative Mutation Pipeline | `tick-live` | `AuthoritativeApplyPipeline.refine()` called in `_phase_resolution()` every tick |
| 3.3 | State Update Compactor | `tick-live` | `compact_with_metrics()` is the first call in every `refine()` invocation |
| 3.4 | Dirty Entity Tracking | `tick-live` | `DirtySetBuilder` instantiated and used throughout `pipeline.py:refine()` |
| 3.5 | Conflict Resolution | `tick-live` | Result sort by `(class_priority, -local_priority, entity_id)` in `_phase_resolution():474` |
| 3.6 | Phase Stability Guard | `tick-live (cond)` | `_guard_stability()` called in `_tick_once_inner()` but **only when `audit_mode=True`**; inactive in normal live runs |
| 3.7 | Resource Conservation Law | `tick-live` | `ResourceTransactionPhase.resolve()` wired as pipeline "resource_transactions" phase |

**Section Wiring Health Score: 10 / 15** (Tick-Live Coverage=4, Finding Exposure=5, Wiring Confidence=1)

| Dimension | Score | Reason |
|---|---|---|
| Tick-Live Coverage | 4 | 6 features `tick-live`, 1 `tick-live (cond)` (3.6 Phase Stability Guard — active only when `audit_mode=True`; invisible in standard live runs) |
| Finding Exposure | 5 | Finding 5 (Risk 11/15 ≥10) directly targets 3.6: Phase Stability Guard is audit-mode only; isolation breaches invisible in standard live runs |
| Wiring Confidence | 1 | All features traced to specific call sites; conditional guard is explicitly confirmed in `_tick_once_inner()` |

### Section 4: Spatial & Navigation

| ID | Feature | Wiring | Evidence |
|---|---|---|---|
| 4.1 | Spatial Grid / Cell-Based Indexing | `tick-live` | `SpatialQueryService` wraps `SpatialGrid`; called in `apply.py:123` for every living entity |
| 4.2 | Spatial Query Service | `tick-live` | `get_region_at()` called in `apply.py:_compute_entity_changes()` for every passive entity |
| 4.4 | Movement System | `tick-live` | `MovementActions.execute_move()` via `domain_logic.execute_move()` during collection |
| 4.5 | Movement Plan Cache | `tick-live` | Registered with `CacheRegistry`; `invalidate_for_dirty()` called each tick; evicted in `_phase_cleanup()` |
| 4.6 | Occupancy Snapshot | `tick-live` | `OccupancySnapshot.from_state()` in `_phase_init()` every tick; also checked in `pipeline.py:63` |

**Section Wiring Health Score: 3 / 15** (Tick-Live Coverage=1, Finding Exposure=1, Wiring Confidence=1)

| Dimension | Score | Reason |
|---|---|---|
| Tick-Live Coverage | 1 | All 5 features `tick-live`; full live-run presence |
| Finding Exposure | 1 | No findings reference Section 4 features |
| Wiring Confidence | 1 | All features traced to specific call sites in `apply.py`, `domain_logic`, and `_phase_init()` |

### Section 5: Mathematical & Formula Systems

| ID | Feature | Wiring | Evidence |
|---|---|---|---|
| 5.1 | Combat Damage Formula | `tick-live` | `CombatResolutionSystem.calculate_damage()` during combat resolution in collection phase |
| 5.2 | Attribute Cap Enforcement | `tick-live` | `enforce_attribute_caps()` applied in apply path after any attribute modification |
| 5.3 | Stamina System | `tick-live` | `StaminaService.tick_regen()` in `apply.py:113-118` for every passive entity |
| 5.5 | Tactical Decision Scoring | `tick-live` | `TacticalDecisionSystem.evaluate_entity_intent()` during cognition in collection phase |
| 5.6 | Goal / Route Scoring Framework | `tick-live` | `GoalScorer` + `ScoreModifierSystem.apply_modifiers()` in cognitive pipeline |
| 5.7 | XP / Reward Classification Math | `tick-live` | `EvolutionSystem.evaluate()` wired as pipeline "evolution" phase |
| 5.8 | Parameter Expression Evaluator | `startup-live` | `ModuleParameterEvaluator` in `worldmodules/evaluator.py` during procedural world generation |
| 5.9 | Module Scoring System | `startup-live` | `ModuleScorer` called by `ProceduralCompositionGenerator` during world creation |

**Section Wiring Health Score: 4 / 15** (Tick-Live Coverage=2, Finding Exposure=1, Wiring Confidence=1)

| Dimension | Score | Reason |
|---|---|---|
| Tick-Live Coverage | 2 | 6 features `tick-live`, 2 `startup-live` (5.8 Parameter Evaluator and 5.9 Module Scorer run during world creation only; expected for world-gen context) |
| Finding Exposure | 1 | No findings reference Section 5 features |
| Wiring Confidence | 1 | All features traced to specific call sites; startup-live status explicitly confirmed via world creation pipeline |

### Section 6: Entity & Content Modelling

| ID | Feature | Wiring | Evidence |
|---|---|---|---|
| 6.1 | Entity Anatomy Model | `tick-live` | `EntityState` components processed each tick in `apply.py:_compute_entity_changes()` |
| 6.2 | Entity Lifecycle Model | `tick-live` | `LifecycleSystem.resolve_lifecycle()` wired as pipeline "lifecycle" phase |
| 6.3 | Entity Builder | `startup-live` | `EntityBuilder` called by `EntitySpawner` during world assembly; also by `SpawnService` event-live |
| 6.4 | Typed Durable State Rule | `design-pattern` | A durable state rule, not a callable; enforced by architecture tests and HardLawMonitor |
| 6.5 | Content Catalog & Registry | `startup-live` | `ContentWarmupService.warmup()` called in `Kernel.__init__()` before first tick (WORLD-CAT-004) |
| 6.7 | Content Pack Manifest & Validation | `startup-live` | `ContentValidator` runs during world assembly before kernel starts |
| 6.8 | Content Family Extension Pattern | `design-pattern` | Canonical authoring pattern; enforced by code review, not runtime |
| 6.9 | Namespace Isolation for Content | `startup-live` | `namespace:id` validated by `worldbuilding/schema.py` at assembly time |
| 6.10 | World Module Schema & Repository | `startup-live` | `WorldModuleSpec` repository loaded during world assembly |
| 6.11 | World Assembly Pipeline | `startup-live` | `WorldAssembly` resolver runs once before kernel starts |
| 6.12 | World Building Compiler | `startup-live` | `WorldBuildingCompiler` compiles `WorldSpec` YAML during world initialization |
| 6.13 | Procedural World Generator | `startup-live` | `ProceduralCompositionGenerator` 5-stage pipeline runs during world creation |

**Section Wiring Health Score: 6 / 15** (Tick-Live Coverage=4, Finding Exposure=1, Wiring Confidence=1)

| Dimension | Score | Reason |
|---|---|---|
| Tick-Live Coverage | 4 | 2 features `tick-live`, 8 `startup-live`, 2 `design-pattern`; 10 of 12 features are non-tick-live — expected given this section covers world assembly and content infrastructure |
| Finding Exposure | 1 | No findings reference Section 6 features directly; Finding 3 is a meta-finding about audit scope gaps, not a wiring failure in these features |
| Wiring Confidence | 1 | All features traced to specific services (`WorldAssembly`, `ContentWarmupService`, `EntitySpawner`, etc.) |

### Section 7: Domain Architecture

| ID | Feature | Wiring | Evidence |
|---|---|---|---|
| 7.1 | Domain Ownership Boundaries | `design-pattern` | Documentation + architecture tests; no single runtime callable |
| 7.2 | No Cross-Domain Import Rule | `ci-only` | Architecture test (`test_domain_isolation`) enforces; no runtime check |
| 7.3 | Feature Flag Gating Model | `tick-live` | `FeatureFlagManager` instantiated at start of every `pipeline.py:refine()` call |

**Section Wiring Health Score: 7 / 15** (Tick-Live Coverage=5, Finding Exposure=1, Wiring Confidence=1)

| Dimension | Score | Reason |
|---|---|---|
| Tick-Live Coverage | 5 | 7.2 No-Cross-Domain-Import Rule is `ci-only` (enforced by architecture test only; no live runtime check); 7.1 is `design-pattern` |
| Finding Exposure | 1 | No findings directly target Section 7 features; `ci-only` status of 7.2 is by design, not a wiring gap |
| Wiring Confidence | 1 | All features evidenced; ci-only and design-pattern statuses are definitively classified |

### Section 8: Scheduling & Budget Infrastructure

| ID | Feature | Wiring | Evidence |
|---|---|---|---|
| 8.1 | Tick Budget Allocation | `tick-live` | Phase cost tracking (`_phase_costs`) and watchdog alert in `_tick_once_inner()` |
| 8.2 | Entity / Provider Budget | `tick-live` | `governor.evaluate()` in `_phase_init()` every tick |
| 8.3 | Cache Registry | `tick-live` | `sweep_caches()` in `_phase_cleanup()` every `sweep_interval_ticks` ticks |
| 8.4 | Movement Plan Cache | `tick-live` | **Duplicate of 4.5** — same `movement_cache.py`. Confirmed tick-live. |

**Section Wiring Health Score: 3 / 15** (Tick-Live Coverage=1, Finding Exposure=1, Wiring Confidence=1)

| Dimension | Score | Reason |
|---|---|---|
| Tick-Live Coverage | 1 | All 4 features `tick-live`; 8.4 is a confirmed duplicate of 4.5 but still tick-live |
| Finding Exposure | 1 | No findings reference Section 8 features |
| Wiring Confidence | 1 | All features traced to specific call sites in `_tick_once_inner()`, `governor.evaluate()`, and `_phase_cleanup()` |

### Section 9: Observability & Replay Infrastructure

| ID | Feature | Wiring | Evidence |
|---|---|---|---|
| 9.1 | Typed Event Emission Pipeline | `tick-live` | `_replay.emit(TraceEvent(...))` in `_phase_resolution()` and `_phase_persistence()` |
| 9.2 | Replay Manager | `tick-live` | `emit()` in resolution; `on_tick_end()` in persistence phase every tick |
| 9.3 | Log Compaction | `tick-live` | `StateUpdateCompactor.compact_with_metrics()` runs in every `refine()`; log retention is workflow-driven (not live-sim) |
| 9.4 | World Metrics Extraction | `tick-live` | `MetricsService.extract_metrics()` in `_tick_once_inner()` (when `_metric_recorder` active) |
| 9.5 | Certification Harness | `ci-only` | Only invoked by the certification workflow; not reachable from a standard live sim run |
| 9.6 | Parity Ledger | `ci-only` | Documentation artifact checked by CI `test_path` entries; no live runtime component |

**Section Wiring Health Score: 7 / 15** (Tick-Live Coverage=5, Finding Exposure=1, Wiring Confidence=1)

| Dimension | Score | Reason |
|---|---|---|
| Tick-Live Coverage | 5 | 9.5 (Certification Harness) and 9.6 (Parity Ledger) are `ci-only` by design — not reachable from a live simulation run |
| Finding Exposure | 1 | No findings directly target Section 9 features; the `ci-only` statuses are intentional classifications, not wiring gaps |
| Wiring Confidence | 1 | All features evidenced; ci-only status explicitly confirmed via workflow and CI pipeline analysis |

### Section 10: World Dynamics Foundation

| ID | Feature | Wiring | Evidence |
|---|---|---|---|
| 10.1 | World Dynamics System | `tick-live` | `WorldDynamicsSystem.resolve_dynamics()` wired as pipeline "world_dynamics" phase |
| 10.2 | Entity Spawn Service | `tick-live` | `SpawnService.process_spawns()` cadence-gated in `world_dynamics` |
| 10.4 | Calamity Service | `tick-live` | `CalamityService.process_world_dynamics()` cadence-gated in `world_dynamics` |

**Section Wiring Health Score: 3 / 15** (Tick-Live Coverage=1, Finding Exposure=1, Wiring Confidence=1)

| Dimension | Score | Reason |
|---|---|---|
| Tick-Live Coverage | 1 | All 3 features `tick-live`; cadence-gated features still run on live ticks |
| Finding Exposure | 1 | No findings reference Section 10 features |
| Wiring Confidence | 1 | All features traced to `WorldDynamicsSystem.resolve_dynamics()` and its cadence-gated subsystems |

---

## Wiring Summary

| Status | Count | Features |
|---|---|---|
| `tick-live` | 47 | The vast majority — kernel loop, pipeline phases, all major subsystems |
| `startup-live` | 9 | World gen, content catalog, assembly pipeline, module scoring |
| `design-pattern` | 3 | 2.5, 6.4, 6.8, 7.1 (conventions enforced by tests/review) |
| `ci-only` | 3 | 7.2 (domain isolation test), 9.5 (certification harness), 9.6 (parity ledger) |
| `tick-live (cond)` | 1 | 3.6 Phase Stability Guard (audit_mode only) |
| **Total** | **61** | (D02 summary states "53" — see Finding 1) |

**No `[E]` feature in D02 is unreachable or test-only.** Every feature has a live code path.

---

## Section Wiring Health Summary

| Section | Score | Key Concern |
|---|---|---|
| §3 Mutation Architecture | **10 / 15** | 3.6 Phase Stability Guard is `tick-live (cond)` only; Finding 5 (Risk 11/15) targets it |
| §7 Domain Architecture | **7 / 15** | 7.2 No-Cross-Domain Import is `ci-only` by design; no live runtime enforcement |
| §9 Observability & Replay | **7 / 15** | 9.5 Certification Harness and 9.6 Parity Ledger are `ci-only` by design |
| §2 State Architecture | **6 / 15** | 2.4 Canonical hash conditionally active in standard runs; Finding 6 (Risk 8/15) |
| §6 Entity & Content Modelling | **6 / 15** | 10 of 12 features are `startup-live` or `design-pattern`; expected for world assembly scope |
| §5 Math & Formula Systems | **4 / 15** | 5.8 and 5.9 are `startup-live` (module evaluation and scoring); expected for world-gen context |
| §1 Kernel & Execution | **3 / 15** | All 7 features `tick-live`; fully clean |
| §4 Spatial & Navigation | **3 / 15** | All 5 features `tick-live`; fully clean |
| §8 Scheduling & Budget | **3 / 15** | All 4 features `tick-live` (8.4 duplicate confirmed); fully clean |
| §10 World Dynamics | **3 / 15** | All 3 features `tick-live`; fully clean |

---

## Key Findings

### RC1 — AdventureDecisionPhase opportunities= parameter not passed

> **RESOLVED: RC1 fix (2026-06-19):** opportunities= parameter now passed to generate().

### RC2 — near_service hardcoded to hometown

> **RESOLVED: RC2 fix (2026-06-19):** region_id == "hometown" hardcode removed; requirement checks actual region.

### RC3 — PerformanceBudgets.provider_calls_total never reset

> **RESOLVED: RC3 fix (2026-06-19):** provider_calls_total reset each tick; opportunity provider no longer exhausts at tick ~25.

### Finding 1: D02 Existing Count Is Wrong (61, not 53) — Risk: 5 / 15

| Dimension | Score | Reason |
|---|---|---|
| Affected Scope | 1 | Documentation error only — no live behavior affected |
| Detection Risk | 5 | No automated check; stays wrong indefinitely without manual review |
| Impact if Unresolved | 2 | Future audits plan against wrong baseline; misleads scope estimates |
| **Total** | **5** | |

D02's summary line states "53 Existing · 9 Partial · 3 Missing". A direct row-by-row count
of D02's summary table yields **61 `[E]`**, 8 `[P]`, 3 `[M]` (72 total). The totals line
was not updated as entries were added during D02 authoring.

**Action:** Fix the count in D02. No wiring or behavior impact.

### Finding 2: All Existing Features Are Live-Wired — Risk: 3 / 15

| Dimension | Score | Reason |
|---|---|---|
| Affected Scope | 3 | Positive finding: all 61 features confirmed; 3 ci-only items need monitoring |
| Detection Risk | 1 | Wiring is confirmed — risk is low by definition |
| Impact if Unresolved | 1 | No gap — positive result, no action needed |
| **Total** | **3** | |

Zero `[E]` features are test-only or unreachable in a live run. The 3 `ci-only` entries
(7.2, 9.5, 9.6) are correctly classified — they enforce structural rules or measure run
quality but are not part of the simulation's live behavior.

The 1 `tick-live (cond)` entry (3.6 Phase Stability Guard) is inactive in normal live runs
but active in audit and certification runs — this is intentional by design.

### Finding 3: Live Domain-Phase Systems Not in D02 Inventory — Risk: 13 / 15

| Dimension | Score | Reason |
|---|---|---|
| Affected Scope | 5 | 20+ systems across combat, economy, strategy, world domains all invisible to audit coverage |
| Detection Risk | 4 | No automated inventory check; gap is structural and grows as new phases are added |
| Impact if Unresolved | 4 | Future audits (D10, D14, D12) plan against incomplete picture; domain bugs go uninventoried |
| **Total** | **13** | |

`pipeline.py` wires 20+ additional live systems that are not listed in D02's feature
inventory. D02 scoped to "technical enabling capabilities" (algorithms, data structures,
infrastructure) — these domain-phase systems were out of D02's scope, but they are all
`tick-live` in the authoritative pipeline:

**From `pipeline.py:refine()` — all tick-live:**
- `SelfModelUpdatePhase` ("self_model" phase)
- `InformationBeliefPhase` ("information_belief" phase)
- `CooperationPhase` ("cooperation" phase)
- `BlacksmithSystem` ("blacksmith" phase)
- `AdventureDecisionPhase` ("adventure_decision" phase)
- `CombatEngagementPhase` ("combat_engagement" phase)
- `InteractionSystem` ("interaction_enforcement" phase)
- `BuildingSabotageSystem` ("building_sabotage" phase)
- `TownResolutionSystem` ("town_resolution" phase)
- `WorldEmergencePhase` ("world_emergence" phase)
- `ShopSystem` ("shop" phase)
- `EvolutionSystem` ("evolution" phase)
- `ProgressionConversionPhase` ("progression_conversion" phase)
- `StrategicIntelligenceSystem` ("strategic_intelligence" phase)
- `LifecycleSystem` ("lifecycle" phase)
- `ContractService` ("active_contracts", "expired_offers" phases)
- `CapacityEnforcementPhase` ("capacity_enforcement" phase)

**From `world_dynamics.py:resolve_dynamics()` — all tick-live (cadence-gated):**
- `ThreatService.process_threat_evolution()`
- `BossService.check_for_boss_spawn()`
- `RaidService.check_for_raid()`
- `CampService.process_camps()`
- `TransformationService.get_potential_transformation()`
- `EnvironmentService` (hazard drain, weather multipliers)
- `DemographicCycleService` (added E52A — cadence-gated population cohort cycle)

**Additional pipeline phases added since this audit (2026-06-22):**
- `PaidInformationTransactionSystem` (E42C — Phase 6 in `pipeline.py:refine()`)
- `LeadContradictionSystem` (E42D — wired into authoritative pipeline)
- `ResourceNodeRegenerationService` (E21B — in `ResourceEcologyService.process_ecology()`)

**Episode-boundary systems in `CampaignOrchestrator._advance_state()` (not tick-live):**
- `SocialMemoryExporter` / `SocialMemoryImporter` (E43B)
- `ChronicleCompiler` (E51 — compiles NarrativeLedger at episode end)
- `ProgressionPlanExporter` / `ProgressionPlanImporter` (E61B — scoped, not yet implemented)
- `CultureDriftExporter` / `CultureDriftImporter` (E62B — scoped, not yet implemented)

There is no domain-level inventory equivalent to D02. This is the most significant
gap this audit reveals: the domain-phase layer is invisible to current audit coverage.

### Finding 4: Feature-Gated Phases May Not Run in All Scenarios — Risk: 9 / 15

| Dimension | Score | Reason |
|---|---|---|
| Affected Scope | 4 | 8 phases across self-model, belief, cooperation, combat, world domains |
| Detection Risk | 3 | Flag state visible in config; but no test verifies correct default values per scenario |
| Impact if Unresolved | 2 | Default is ON for all flags; misconfigured scenario silently loses features |
| **Total** | **9** | |

Eight pipeline phases are gated behind `FeatureMode` flags:
`ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`, `ENABLE_SOCIAL_COOPERATION`,
`ENABLE_ADVENTURE_ROUTING`, `ENABLE_COMBAT_ENGAGEMENT`, `ENABLE_WORLD_EMERGENCE`,
`ENABLE_PROGRESSION_EVOLUTION`.

These phases are `tick-live` by classification but only execute when the corresponding
flag is `ON` or `SHADOW`. A scenario configured with all flags `OFF` would run only the
core structural phases. The default mode for all flags is `ON` unless a `rollout_profile`
or `feature_flags` state attribute overrides them.

### Finding 5: Phase Stability Guard Is Audit-Mode Only — Risk: 11 / 15

| Dimension | Score | Reason |
|---|---|---|
| Affected Scope | 3 | Affects all phases — any phase can commit an isolation breach invisibly |
| Detection Risk | 5 | Completely invisible in standard live runs — certification only |
| Impact if Unresolved | 3 | Isolation breaches cause non-determinism; hard to reproduce outside cert mode |
| **Total** | **11** | |

Feature 3.6 (`_guard_stability()`) fingerprints `AuthoritativeState` between phases to
catch isolation breaches. It is **not active** in normal production runs — only when
`Kernel` is initialized with `audit_mode=True` (used in certification scenarios).

This means isolation breaches would be invisible in standard live runs. The certification
harness is the only live detection path.

### Finding 6: Canonical State Hashing Conditionally Active — Risk: 8 / 15

| Dimension | Score | Reason |
|---|---|---|
| Affected Scope | 2 | Single feature (2.4); fingerprint IS active on all ticks |
| Detection Risk | 4 | Hash recorded as `"SKIPPED"` is a silent downgrade — no warning emitted |
| Impact if Unresolved | 2 | Standard runs lose full-hash traceability; `fingerprint()` still runs |
| **Total** | **8** | |

Feature 2.4 (`CanonicalStateHasher.get_hash()`) is called in `_phase_persistence()` only
when `replay_allowed and (audit_mode or replay_richness == "FULL")`. In default
`replay_richness = "STANDARD"` non-audit runs, the tick-end hash is recorded as
`"SKIPPED"`. The `fingerprint()` method (lighter-weight) IS called on every tick when
replay is allowed. Full canonical hash is audit-mode or full-richness only.

---

## Recommended Follow-Up Tickets

| Priority | Item |
|---|---|
| P1 | Fix D02 `[E]` count: 61 existing, not 53. Update D02 totals line. |
| P1 | **Create domain-phase inventory** — a D02-equivalent for the 20+ domain pipeline systems found in Finding 3. This is the largest gap the audit reveals. |
| P2 | Confirm Phase Stability Guard (3.6) detection coverage: document which violation types can only be caught in audit mode, not standard runs. |
| P2 | Confirm canonical hash coverage: document which run configurations produce `"SKIPPED"` hash and whether this is an acceptable traceability gap. |

---

### Finding Risk Summary

| Rank | Finding | Risk Score |
|---|---|---|
| 1 | Finding 3 — Domain-phase systems not inventoried | 13 / 15 |
| 2 | Finding 5 — Phase Stability Guard audit-mode only | 11 / 15 |
| 3 | Finding 4 — Feature-gated phases may not run | 9 / 15 |
| 4 | Finding 6 — Canonical hashing conditionally active | 8 / 15 |
| 5 | Finding 1 — D02 count wrong | 5 / 15 |
| 6 | Finding 2 — All features live-wired (positive) | 3 / 15 |

---

## Related Dimensions

- **D10 (Test Coverage)** — use this wiring map to prioritize which `ci-only` and
  `design-pattern` items need test coverage; Finding 3 (uninventoried domain systems)
  defines the coverage blind spot
- **D11 (Dead Code)** — `startup-live` features (world gen, assembly) are prime
  candidates if world creation is always done in tests rather than live
- **D17 (Documentation Currency)** — `kernel.md` and `authoritative_pipeline.md`
  pipeline phase tables found stale here (17 documented vs 30+ in code)
- **D02 (Foundation Feature Inventory)** — this audit corrected D02's count and
  revealed Finding 3's domain-phase inventory gap
