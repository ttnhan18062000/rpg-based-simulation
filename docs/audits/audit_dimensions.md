---
status: active
layer: architecture
authority: P1
audience: agent
tags: [audit, planning, roadmap, simulation-quality, codebase-health, developer-tooling]
---

# Engine Audit — Dimension Index

## Purpose

This is the master index for the engine audit programme. The audit answers:
**what we have, what we need, and what we want** — across three goals:

1. **Realistic, fun, rich simulation** — does the engine produce compelling emergent behavior?
2. **Clean codebase, architecture, design** — is the engine well-structured and maintainable?
3. **Strong developer tooling** — is the engine fast and clear to develop against?

Each audit dimension produces a detail file with findings, feature lists, and ratings.
This index tracks state, priority, and method across all 18 dimensions.

Related epic: `tickets/inprogress/TCK-20260618-AUDIT-EPIC.md`

---

## Framework

### Axes

Each audit dimension is characterized by four axes:

| Axis | Purpose | Format |
|---|---|---|
| **State** | How far along is this audit dimension | `none / partial / done` |
| **Impact** | How much closing the gap advances the three goals | 1–5 |
| **Interest** | How much we want this — vision fit, leverage, novelty | 1–5 |
| **Method** | How to actually audit this dimension | see below |

**Priority** = Impact + Interest (max 10). Higher priority dimensions are audited first.

### State

State describes how fully audited the dimension is, not how complete the underlying systems are:

| Value | Meaning |
|---|---|
| `none` | Not yet started |
| `partial` | Investigation begun, findings incomplete or unrecorded |
| `done` | Findings fully documented in detail file |

### Impact (1–5)

| Score | Meaning |
|---|---|
| 5 | Directly advances all three goals, or is a prerequisite for major systems |
| 4 | Clearly advances one or two goals; absence is a visible quality gap |
| 3 | Moderate contribution; absence is noticeable but manageable |
| 2 | Narrow or indirect benefit |
| 1 | Minor, peripheral, or tooling-only scope |

### Interest (1–5)

| Score | Meaning |
|---|---|
| 5 | High vision fit, novel, or high leverage — we want this |
| 4 | Strong value, good timing, clear wins |
| 3 | Useful, standard engineering concern |
| 2 | Necessary but unglamorous |
| 1 | Maintenance or compliance only |

### Method

| Method | Meaning |
|---|---|
| `code-read` | Auditable by reading source files and docs |
| `run-sim` | Requires actually running the simulation to observe output |
| `measure` | Requires tooling: coverage reports, profiling, static analysis |
| `count` | Requires enumerating artifacts: content items, doc files, test counts |
| `review` | Requires human judgment against a defined standard |

Some dimensions require multiple methods. Detail files specify which apply and how to run them.

### Rating within a dimension

Individual features or findings within a dimension are rated by a method specific to
that dimension group. Dimensions in Group 0 (Feature Inventory) use their own scoring
approaches, documented in their detail files. Simulation Quality dimensions use observed
run metrics. Codebase dimensions use coverage metrics or count-based checks.

The Impact + Interest priority scores are for the **audit dimension itself** — how much
does auditing this dimension matter, and how much do we want to do it. Within a detail
file, feature-level ratings use the methodology defined in that file.

---

## Dimension Table

Sorted by priority (Impact + Interest) descending.

| ID | Dimension | Group | State | Impact | Interest | Priority | Method | Detail |
|---|---|---|---|---|---|---|---|---|
| D01 | RPG Feature Impact | Feature Inventory | `done` | 5 | 5 | 10 | code-read | [D01](D01_rpg_feature_impact.md) |
| D03 | Behavioral Emergence Quality | Simulation Quality | `done` | 5 | 5 | 10 | run-sim | [D03](D03_behavioral_emergence.md) |
| D02 | Foundation Feature Inventory | Feature Inventory | `done` | 5 | 4 | 9 | code-read | [D02](D02_foundation_features.md) |
| D06 | Long-Run Simulation Health | Simulation Quality | `done` | 4 | 5 | 9 | run-sim | [D06](D06_longrun_health.md) |
| D09 | System Wiring & Integration | Codebase | `done` | 4 | 4 | 8 | code-read | [D09](D09_system_wiring.md) |
| D15 | Entity Decision Inspection Tooling | Developer Tooling | `done` | 4 | 5 | 9 | review | [D15](D15_entity_decision_inspection.md) |
| D20 | Simulation Quality Module Integration | Simulation Quality | `done` | 4 | 5 | 9 | run-sim + code-read | [D20](D20_simq_integration.md) |
| D05 | Entity Differentiation | Simulation Quality | `done` | 4 | 4 | 8 | run-sim | [D05](D05_entity_differentiation.md) |
| D04 | Balance & Tuning | Simulation Quality | `partial` | 4 | 3 | 7 | run-sim | [D04](D04_balance_tuning.md) |
| D07 | Content Depth & Variety | Simulation Quality | `done` | 4 | 3 | 7 | count | [D07](D07_content_depth.md) |
| D10 | Test Coverage & Regression Risk | Codebase | `done` | 4 | 3 | 7 | measure | [D10](D10_test_coverage.md) |
| D14 | Coupling Depth | Codebase | `done` | 4 | 3 | 7 | code-read | [D14](D14_coupling_depth.md) |
| D16 | Scenario & Content Authoring DX | Developer Tooling | `done` | 3 | 4 | 7 | review | [D16](D16_scenario_authoring_dx.md) |
| D17 | Documentation Currency | Developer Tooling | `done` | 4 | 3 | 7 | review | [D17](D17_documentation_currency.md) |
| D12 | Pattern Consistency | Codebase | `done` | 3 | 3 | 6 | code-read | [D12](D12_pattern_consistency.md) |
| D08 | Multi-Scenario Consistency | Simulation Quality | `done` | 3 | 2 | 5 | run-sim | [D08](D08_multi_scenario.md) |
| D13 | Type Safety & Validation Boundary | Codebase | `done` | 3 | 2 | 5 | measure | [D13](D13_type_safety.md) |
| D18 | CI / Release Pipeline Completeness | Developer Tooling | `done` | 3 | 2 | 5 | review | [D18](D18_ci_release_pipeline.md) |
| D11 | Dead Code & Orphaned Modules | Codebase | `done` | 2 | 2 | 4 | measure | [D11](D11_dead_code.md) |

---

## Groups

### Group 0 — Feature Inventory
Pre-audit context documents produced before the formal audit programme began.
They inform all downstream dimensions and serve as the factual foundation for prioritization.

| ID | Dimension | State | Detail |
|---|---|---|---|
| D01 | RPG Feature Impact | `done` | [D01_rpg_feature_impact.md](D01_rpg_feature_impact.md) |
| D02 | Foundation Feature Inventory | `done` | [D02_foundation_features.md](D02_foundation_features.md) |

---

### Group A — Simulation Quality
**Goal:** Does the engine produce realistic, fun, rich simulation behavior?

| ID | Dimension | Priority | State | Method | What it answers |
|---|---|---|---|---|---|
| D03 | Behavioral Emergence Quality | 10 | `done` | run-sim | Do entities behave like RPG characters, or do they loop? |
| D06 | Long-Run Simulation Health | 9 | `done` | run-sim | Does the world stay alive past 1000 ticks? |
| D20 | Simulation Quality Module Integration | 9 | `done` | run-sim + code-read | Is SimQ actually receiving events and scoring live runs? |
| D05 | Entity Differentiation | 8 | `done` | run-sim | Do classes and personalities produce observably different arcs? |
| D04 | Balance & Tuning | 7 | `partial` | run-sim | Are numerical constants calibrated to produce interesting dynamics? |
| D07 | Content Depth & Variety | 7 | `done` | count | Is there enough authored content to populate interesting runs? |
| D08 | Multi-Scenario Consistency | 5 | `done` | run-sim | Does quality hold across different world configs and seeds? |

**Note:** All Group A dimensions except D07 require running the simulation.
D03 and D06 are prerequisites for the others — they establish what "good" looks like
before measuring more specific qualities.

---

### Group B — Codebase / Architecture
**Goal:** Is the engine well-structured, correct, and maintainable?

| ID | Dimension | Priority | State | Method | What it answers |
|---|---|---|---|---|---|
| D09 | System Wiring & Integration | 8 | `done` | code-read | Are all implemented systems actually called from the live pipeline? |
| D10 | Test Coverage & Regression Risk | 7 | `done` | measure | Which behaviors are regression-protected and which are not? |
| D14 | Coupling Depth | 7 | `done` | code-read | Where do hidden dependencies violate domain ownership? |
| D12 | Pattern Consistency | 6 | `done` | code-read | Are established patterns applied uniformly across all domains? |
| D13 | Type Safety & Validation Boundary | 5 | `done` | measure | Where do untyped surfaces and missing validation create risk? |
| D11 | Dead Code & Orphaned Modules | 4 | `done` | measure | What code exists but is never reached from the live pipeline? |

**Note:** D09 should run first — it verifies which `[E]` features in D02 are actually
integrated, and its findings define the risk surface for D10, D12, and D14.

---

### Group C — Developer Tooling
**Goal:** Is the engine fast and clear to develop against?

| ID | Dimension | Priority | State | Method | What it answers |
|---|---|---|---|---|---|
| D15 | Entity Decision Inspection Tooling | 9 | `done` | review | Can a developer see why an entity made a decision on tick N? |
| D16 | Scenario & Content Authoring DX | 7 | `done` | review | How many files must change to add a new module or content type? |
| D17 | Documentation Currency | 7 | `done` | review | Which docs are stale or inaccurate beyond known_limitations.md? |
| D18 | CI / Release Pipeline Completeness | 5 | `done` | review | Is there a reproducible path from passing code to certified release? |

---

## Key Insights from Completed Dimensions

### From D03 (Behavioral Emergence Quality)
- **Root cause confirmed: `AdventureDecisionPhase` never calls `ResourceOpportunityProvider` (F5, RC1 — PRIMARY).** `adventure/phase.py:60` calls `generate(hero, state)` with no `opportunities=` argument. The generator's primary route-mapping path (`for opp in opportunities:`) loops zero times every tick. Healthy entities receive `DEFER_WITH_REASON` and are silently skipped — no project update, no action, no output. This is a 3-line wiring fix.
- **`near_service` requirement hardcoded to `"hometown"` blocks all resource opportunities (RC2).** `world/providers/requirements.py:154` only passes `near_service` checks if `region_id == "hometown"`. `sandbox_world` uses `"town_center"` and `"woods"`. Even if RC1 is fixed, all generated resource opportunities would be blocked by this check.
- **`PerformanceBudgets` class-level counter would cap opportunities at tick ~25 (RC3).** Cap of 500 provider calls at 20 entities/tick = exhausted at tick 25. `reset()` exists but is not confirmed called between runs in the same process.
- **Rejection cascade (194-926) is a symptom, not a root cause (RC4).** Rejections come from `engine/interaction.py`, `movement.py`, `economy.py` — stale initial-spawn projects retrying failed objectives indefinitely. Would stop once RC1 gives entities fresh project assignments.
- **`STANDARD` lab mode maps to `LIGHT` engine mode — no richer data (F5).** All three lab modes (`LIGHTWEIGHT`, `MINIMAL`, `STANDARD`) map to `ObservabilityMode.LIGHT` in `lab/orchestrator.py:147-153`. Richer cognition data requires `SIM_OBS_MODE=DEBUG` env var.
- **P0 follow-up:** Wire `ResourceOpportunityProvider` into `AdventureDecisionPhase` (phase.py:60), fix `near_service` hardcode (requirements.py:154), confirm `PerformanceBudgets.reset()` is called per run.

### From D01 (RPG Feature Impact)
- **One missing Tier-1 system:** Resource Ecology Regeneration (score 22/25) is the
  single highest-leverage missing RPG system. Its absence means the economy never
  stresses, quests have no organic demand, and faction conflict has nothing to fight over.
- **Three missing Tier-2 systems form the product gap:** Persistent Campaign Runtime,
  Faction & Diplomacy, and Scenario Runtime Service together represent the distance
  between "lab tooling" and "a product that runs an RPG simulation."
- **CampaignRunner naming risk:** `src/domains/campaigns/runner.py` is analysis-only but
  is commonly mistaken for a real campaign runtime. Should be renamed before Campaign epic.

### From D02 (Foundation Feature Inventory)
- **61 Existing, 8 Partial, 3 Missing** across 72 foundation features. (D02's summary
  line incorrectly states "53 E / 9 P / 3 M" — actual count from table is 61/8/3. Fix
  tracked in D09 Finding 1.)
- **Three missing:** Per-Phase Read/Write Domain Permissions (1.9), Macro-Economy Health
  Metrics (5.10), Resource Node Regeneration (10.5).
- **Highest-risk partials:** AoE legality (P0 parity bug COMB-006), flow-field navigation
  (local minima risk), hardcoded fallback paths (silent failure risk).

### From D15 (Entity Decision Inspection Tooling)
- **"What" is answered; "Why" is not.** Live inspect API (`/api/v1/observability/live/entities/{id}`)
  shows current goal ID, action, rejection reason, anomaly flags — but not why that goal beat alternatives.
  Goal scoring is computed transiently in `execute_brain()` and discarded at tick boundary.
- **6 capabilities present, 6 missing.** The 6 missing all cluster around the "why" question: goal
  score comparison, tick-N state reconstruction, cognition snapshot REST API, route trace persistence,
  BehaviorTimeline REST API, and cognition capture in LIGHT (default) mode.
- **Cognition snapshot system exists but is effectively hidden.** Rich `cognition_graph_snapshots.jsonl`
  artifacts are written per run but: (a) only in DEBUG/CERTIFICATION mode for strategic changes; (b)
  no REST query API; (c) not indexed by tick. Developer must `grep` JSONL files manually.
- **D01 confirmation:** Route trace "generated every tick but not stored durably" — still true.
  Promotion of existing computed data to a queryable API would close the P0 gap without new simulation logic.

### From D17 (Documentation Currency)
- **`authoritative_pipeline.md` is the most stale doc (P0):** The 17-phase table is from an earlier
  version — current `pipeline.py` has 30+ named phases. Phase names, order, and count all differ.
  Any agent implementing against this doc will use wrong insertion points.
- **`kernel.md` has two conflicting phase tables in the same file.** The first (stale, 6-phase
  with wrong names) appears before the correct 7-phase table. Reading linearly gives wrong info first.
- **Biological thresholds in mechanics/01 are numerically wrong:** Hunger trigger is 95.0 (doc: 100.0),
  damage is +2 (doc: 5). Sleep debt trigger is 98.0 (doc: 80.0); penalty is HP damage, not ATK/DEF multiplier.
- **Interruption margin formula:** mechanics/04 says `Profile_Resistance * 30.0`; code uses
  `profile.resistance_multiplier` (profile-defined constant, not 30.0 universally).
- **Best-maintained doc:** `mechanics/02_combat_laws.md` — all damage formula and tactical modifier
  values are current and verified.
- **Summary:** 9 stale / 25 current / 7 uncertain across 9 target files. See D17 for P0/P1/P2 fix backlog.

### From D12 (Pattern Consistency)
- **V2 patterns are largely well-applied — 5 findings, all moderate severity.** Domain Phase class (8/8), decision/mutation separation (0 violations), presenter layer (clean), metadata blobs (1 case) are consistent.
- **Top risk: unstable sorts on tick path (F1, 10/15).** `generator.py` and `selector.py` sort candidates by score with no entity_id tiebreaker — score ties produce non-deterministic ordering. Directly compounds D10 F3 (bare random determinism breach).
- **`commitment/abandonment.py` encodes categorical decisions as reason strings (F2, 9/15).** `"greedy_desertion"`, `"survival"`, `"voluntary_quit"` should be an enum; `penalty` float and `is_betrayal` bool should be a typed dataclass. Classic §3.3 violation from architecture_reference.md.
- **`design_patterns.md` describes V1 patterns entirely (F3, 8/15).** GoalScorer, StateHandler, EntityBuilder — none are the V2 extension points. A developer following this doc would add V1 abstractions to a V2 codebase. Joint D12/D17 finding.

### From D07 (Content Depth & Variety)
- **430 catalog entries across 35 files — foundation layer is mature, narrative layer is critical.** Traits (25), themes (24), roles (23), stat/combat profiles are well-populated. The blocking gap is narrative content.
- **Quest definitions: only 4 (Gap Risk 15/15, P0).** Only 3 of 14 world modules have any quests. Without quests, entities have strategic goals but no narrative missions — conflict produces combat loops, not RPG story arcs. This is the single most urgent content gap.
- **No terrain or population module types (Gap Risk 10/15).** 2 of 7 registered module types have zero entries. Current worlds are composed only of conflict/ecology/settlement. Terrain traversal and population distribution modules don't exist.
- **3 of 5 world compositions have zero scenarios** — `dungeon_crawl`, `urban_political`, `wilderness_survival` cannot be entered from the scenario layer. All 8 existing scenarios are frontier-world variants.
- **Crafting recipes: 8 for 34 items (Gap Risk 10/15).** Most items have no production path; the economy loop has no "gather→craft→upgrade" chain available.

### From D16 (Scenario & Content Authoring DX)
- **Highest friction: adding a new content pack family (DX Gap 12/15).** `ContentUsageMatrix` must be manually updated; no authoring-time warning exists. Confirmed by D10 F6: 3 new pack files were added without registry update, causing 3 CI test failures.
- **Simulation scenario authoring is best-in-class (DX Gap 6/15).** Schema is minimal (6 fields), validation fires immediately at load time, and 10 structural templates exist. Primary gap: allowed initial_condition categories are only documented in `schema.py`.
- **World module authoring is workable but has sharp edges (DX Gap 7/15).** `make world-validate` exists. Key traps: `observability_tags` not `tags`; no `provided_features`; catalog ID errors deferred to assembly. No authoring guide.
- **No content author guide exists.** `docs/world/modules_contract.md` is accurate and complete as a technical contract but is not structured as an authoring walkthrough. P1 gap.
- **`make world-template` and 10 scenario templates are undiscovered strengths** — valid scaffold generators that no doc currently points to.

### From D14 (Coupling Depth)
- **Codebase is architecturally clean — only 3 findings total.** 13 of 14 domains have zero cross-domain imports; all API routes go through DTOs/presenters; `content` has zero imports from engine or domains.
- **Only 1 prohibited cross-domain import:** `memory/phase.py` imports `TemporalPressureService` from `time`. Fix: inject via pipeline orchestrator constructor rather than direct import.
- **Highest-risk coupling: `core/state.py` → `engine.movement_cache`** (upward lazy import, Risk 10/15). `AuthoritativeState.__post_init__` constructs a `MovementPlanCache` — a core data model should not instantiate engine-layer services. This is the single most dangerous coupling because `core/state.py` is imported by nearly every file in the codebase.
- **`pipeline.py` is the clean single integration point** for all 7 live domain phase imports — well-structured, no leakage.

### From D10 (Test Coverage & Regression Risk)
- **95.7% pass rate (3,150 / 3,292) — but 9 distinct root-cause clusters.** Failures are not random; they cluster around 3 critical engine invariants: determinism (bare random), kernel phase contract (milestone A/B), and spatial indexing (`ItemStack.position`).
- **Highest regression risk: teardown mode contamination (F1, 14/15).** `catalog_with_compatibility` mode leaks from `test_registry_bridge.py` into unrelated cognition tests. 15 cognition errors are contamination victims, not real failures.
- **Determinism breach is a P0 engine contract violation (F3, 11/15).** Bare `random.` calls outside `rng.py` produce silently non-deterministic runs — replay diverges without any observable error during simulation.
- **Inventory defaults changed without test update (F4, 10/15).** Confirmed D17's uncertain finding: slot/weight defaults changed; the `INVENTORY_FULL` / `INSUFFICIENT_GOLD` ReasonCode mismatch silently affects upstream callers.
- **Well-covered domains: strategic AI (41 files, 0 failures), unit observability (81 files, 0 failures), world (33 files, 0 failures).** These three domains are the most regression-protected in the codebase.

### From D11 (Dead Code & Orphaned Modules)
- **9 top-level `src/` directories are entirely orphaned — 36 files, ~109 KB, 2,955 lines of unreachable V1 code.** None are imported by the live pipeline or test suite. All represent V1 systems superseded by the V2 domain phase architecture.
- **`src/ai/` is the highest-risk orphan cluster (F1, 12/15).** `ai/goals/scorers.py` implements the V1 `GoalScorer` subclass pattern — the same pattern `design_patterns.md` (D12 F3) still documents as the extension point. Files carry compliance IDs (SOC-142, COMB-093–099, STRAT-166–174) requiring parity ledger audit before deletion.
- **`src/town/` (10 files) and `src/entities/` (4 files) are the next priorities.** `src/town/guild.py` cross-imports `src/quests/`, making both clusters co-dependent orphans — delete together. `src/entities/` name-collides with live `WorldAssemblyResolver` and `EntityArchetypeResolver`.
- **The rest of `src/` is clean.** No commented-out def/class blocks, no backup-named files, no `# DEPRECATED` markers targeting live code, no `src_legacy/` or `tests_legacy/` directories.
- **P1 follow-up: audit `src/ai/` parity ledger compliance IDs, then delete in safe order** — `views/runtime/actions/` first, then `town/quests/`, then `entities/progression/content_semantics/`, finally `ai/` after ledger audit.

### From D13 (Type Safety & Validation Boundary)
- **No type checker is configured anywhere: annotation discipline is documentation only (F1, 15/15).** No `mypy.ini`, no `[tool.mypy]` in `pyproject.toml`, no `pyrightconfig.json`, no `make typecheck` target. 455 `Any` usages and 186 missing return annotations create zero automated enforcement.
- **`api/server.py` 18 route handlers have no return annotation and no `response_model=` (F2, 11/15).** FastAPI only validates response shape when `response_model=` is specified. A shape regression in `EngineManager.get_state()` serializes silently to clients with no tooling signal.
- **`api/engine_manager.py` state-query bridge returns `Dict[str, Any]` for 4 key methods (F3, 10/15).** `get_state()`, `get_full_snapshot()`, `get_entities_paged()`, `get_entity()` all return untyped dicts. A key rename in engine state propagates silently through the chain to the client.
- **91% of public functions have return annotations — good discipline, but unenforced.** The annotation work is valuable as documentation and IDE hints; it needs a type checker to become a correctness guarantee.
- **FastAPI input validation and content-loading boundaries are well-typed.** `api/routes/search.py` uses `Query()` with range constraints; WorldModuleSpec / WorldCompositionSpec use Pydantic `extra="forbid"`. These surfaces are strong.
- **P1 follow-up: add `[tool.mypy]` + `make typecheck` + wire into CI `test.yml`.** F1 and D18 F1 close together — the type checker configuration is wasted without a CI step to run it.

### From D18 (CI / Release Pipeline Completeness)
- **One CI workflow exists (`deploy-docs.yml`) — zero test automation.** Every push to `main` goes through CI that runs only `mkdocs gh-deploy`. No `test.yml` exists. No tests, no lint, no architecture guards run automatically at merge time.
- **All three release-readiness conditions from `project_lawbook.md` are manually enforced (F2, 10/15).** CertificationHarness CLASS_B 100% pass, zero doc drift, and contributor guardrails all require local invocation. A release could exit while the cert harness is failing.
- **The Makefile gate infrastructure is mature; the CI wrapper is missing.** `lane-architecture`, `lane-all-fast`, `gate-expansion`, `lane-legacy-regression`, and `check-resources` all exist as local targets — the fix is a single `test.yml` file calling them.
- **Certification harness is ~10 test files with thorough coverage (determinism, resource envelopes, rollout gates, long-run stability) and none run in CI.** The most valuable automated quality gate in the project is also completely invisible to the merge pipeline.
- **P0 follow-up: add `.github/workflows/test.yml`.** `make lane-all-fast` + `make gate-expansion` + `pytest tests/docs/` on every PR. `make lane-legacy-regression` on `main` push only (slow). Estimated <30 lines of YAML.

### From D09 (System Wiring & Integration)
- **Zero `[E]` features are unreachable or test-only.** All 61 `[E]` features in D02
  have confirmed live code paths.
- **47 tick-live, 9 startup-live, 3 design-pattern, 3 ci-only, 1 tick-live (audit only).**
- **20+ additional live systems found that are not in D02's inventory:** The domain-phase
  layer (BlacksmithSystem, TownResolutionSystem, StrategicIntelligenceSystem, LifecycleSystem,
  ThreatService, BossService, RaidService, CampService, TransformationService, etc.) is
  fully wired and tick-live but absent from D02's feature inventory. A domain-phase
  inventory ticket is recommended.
- **Phase Stability Guard (3.6)** is inactive in normal live runs — only fires in
  `audit_mode=True` runs (certification). Isolation breaches are undetected in standard runs.

---

## Related Documents

| Document | Role |
|---|---|
| `docs/plans/engine_future_epics_roadmap.md` | Authoritative gap analysis and epic backlog |
| `foundation_feature_framework.md` | Scoring framework used by D02 |
| `tickets/inprogress/TCK-20260618-AUDIT-EPIC.md` | Epic ticket tracking all audit work |
| `staging_artifacts/TCK-20260618-AUDIT-EPIC/plan.md` | Audit sequencing plan |
| `staging_artifacts/TCK-20260618-AUDIT-EPIC/investigation.md` | Investigation that defined the 18 dimensions |
