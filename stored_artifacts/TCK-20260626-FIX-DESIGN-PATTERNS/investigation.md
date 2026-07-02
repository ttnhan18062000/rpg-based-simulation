---
ticket_id: TCK-20260626-FIX-DESIGN-PATTERNS
phase: investigation
date: 2026-06-26
---

# Investigation — TCK-20260626-FIX-DESIGN-PATTERNS

## 1. Current Behavior: What design_patterns.md Documents Now

`docs/guidelines/design_patterns.md` (316 lines) documents five patterns under the heading
"Design Patterns & Extension Guide — Technical documentation for the OOP design patterns used in
the simulation engine and how to extend each system."

### Sections present (all V1)

| Section | Classes/Symbols | Location claimed |
|---|---|---|
| §1 Goal Evaluation — Plugin Pattern | `GoalScorer`, `GoalScore`, `GoalEvaluator`, `GOAL_REGISTRY`, `register_goal()` | `src/ai/goals/` |
| §2 Damage Calculation — Strategy Pattern | `DamageCalculator`, `DamageContext`, `DAMAGE_CALCULATORS`, `get_damage_calculator()` | `src/actions/damage.py` |
| §3 Entity Construction — Builder Pattern | `EntityBuilder` fluent API | `src/core/entity_builder.py` |
| §4 Trait Aggregation — Typed Dataclasses | `UtilityBonus`, `TraitStatModifiers`, `aggregate_trait_utility()`, `aggregate_trait_stats()` | `src/core/traits.py` |
| §5 Pattern Summary | Summary table of 4 patterns above | — |
| §7 Metadata API — Shared Schemas | `ItemTemplate`, `SkillDef`, `ClassDef`, etc.; 8 metadata endpoints | `src/core/`, `src/api/routes/metadata.py` |
| §8 File Map | Module tree | — |

### Existence check in src/

| Symbol/File | Still exists? | Status |
|---|---|---|
| `src/ai/goals/base.py` (`GoalScorer`, `GoalEvaluator`, `GOAL_REGISTRY`) | Yes | V1 dead code — D11 confirms no live callers reaching from tick path |
| `src/ai/goals/scorers.py` (9 `GoalScorer` subclasses) | Yes | V1 dead code with compliance IDs |
| `src/ai/goals/registry.py` (`register_all_goals()`) | Yes | V1 dead code |
| `src/actions/damage.py` (`DamageCalculator`, `DAMAGE_CALCULATORS`) | Likely present | Partially live — combat uses DamageCalculator via actions layer |
| `src/core/entity_builder.py` (`EntityBuilder`) | Yes | V1 entity construction — WorldAssemblyResolver is V2 equivalent |
| `src/core/traits.py` (`UtilityBonus`, `TraitStatModifiers`) | Yes | Traits used in engine but `UtilityBonus` is V1 goal-scoring scaffolding |

**Key point from D11 audit:** `src/ai/goals/scorers.py` is structurally identical to what a developer
would write following `design_patterns.md` — so the doc actively guides toward dead V1 code. D11
confirmed the V1 GoalScorer system has live import paths (from compliance-ID-bearing code) but is
not exercised on the simulation tick path. The code exists; the pattern is not how V2 extends the engine.

---

## 2. V2 Patterns to Document

Source: D12 audit §Pattern Strengths and D12/D17 joint finding F3.

### Pattern A — Domain Phase Class

**What it is:** Every domain extension lives in an `XPhase` class with a static `apply()` or
`execute()` method, typed parameters, and a typed return (a `StateUpdate` or domain-specific result
record). Domains read state; they do not mutate it.

**Coverage:** 8/8 domain phases implement this pattern (D12 confirmed).

**Representative class:** `AdventureDecisionPhase` — `src/domains/adventure/phase.py`

```python
class AdventureDecisionPhase:
    @staticmethod
    def apply(
        state: AuthoritativeState,
        context: Optional[dict] = None,
        trace_writer: Optional[Any] = None,
        faction_directives: Optional[list] = None,
        factions: Optional[Any] = None,
    ) -> StateUpdate:
        ...
        return StateUpdate(entity_updates=entity_updates)
```

**How to extend:** Add a new domain under `src/domains/<name>/phase.py` implementing a class with
`apply(state: AuthoritativeState, ...) -> StateUpdate`. Wire it into `src/engine/pipeline.py`
(the single domain integration point). Do not mutate `AuthoritativeState` inside the phase.

**All 8 domain phases (with typed return status per D12 F4):**

| Phase | File | Typed return? |
|---|---|---|
| `AdventureDecisionPhase` | `src/domains/adventure/phase.py` | `-> StateUpdate` |
| `ProgressionPhase` | `src/domains/progression/phase.py` | `-> Optional[ProgressionConversionResult]` |
| `CooperationPhase` | `src/domains/cooperation/phase.py` | `-> Optional[CooperationResult]` |
| `CombatEngagementPhase` | `src/domains/combat_engagement/phase.py` | `-> CombatEngagementDecisionResult` |
| `InformationPhase` | `src/domains/information/phase.py` | `-> Optional[InformationResult]` |
| `WorldEmergencePhase` | `src/domains/world_emergence/phase.py` | missing (D12 F4 — P2 gap) |
| `PerceptionPhase` | `src/domains/perception/phase.py` | missing (D12 F4 — P2 gap) |
| `MemoryPhase` | `src/domains/memory/phase.py` | missing (D12 F4 — P2 gap) |

---

### Pattern B — Decision/Mutation Separation via Typed Update Records

**What it is:** Domains never write to `AuthoritativeState`. They return typed update records
(`StateUpdate`, `EntityUpdate`, `StrategicUpdate`, `StaminaUpdate`, `NavigationUpdate`, etc.)
from `src/core/updates.py`. The authoritative apply path (`ApplyPath` in `src/engine/apply.py`)
is the only place durable state is committed.

**Coverage:** All 14 domains — D14 confirmed zero domain-direct `AuthoritativeState` mutation.

**Key classes:**

| Record | File | Purpose |
|---|---|---|
| `StateUpdate` | `src/core/updates.py` | Top-level update container; holds `entity_updates: Dict[int, EntityUpdate]` |
| `EntityUpdate` | `src/core/updates.py` | Per-entity change record; fields for strategic, stamina, navigation, etc. |
| `StrategicUpdate` | `src/core/updates.py` | Strategic-component delta (projects, objectives, directives) |
| `StaminaUpdate` | `src/core/updates.py` | Stamina delta |
| `NavigationUpdate` | `src/core/updates.py` | Movement/position delta |
| `EquipmentUpdate` | `src/core/updates.py` | Equipment slot/durability delta |
| `RejectionEvent` | `src/core/updates.py` | Structured authoritative rejection record (`frozen=True, slots=True`) |

**`ApplyPath`:** `src/engine/apply.py` — `ApplyPath` class; `_compute_entity_changes()` builds
change dicts; the single point where `AuthoritativeState` is reconstructed from update records.
Compliance IDs: PERF-017, RES-202.

**How to extend:** Return a `StateUpdate` from your domain phase. Add new fields to `EntityUpdate`
or create a new typed sub-record (frozen dataclass in `src/core/updates.py`). Never write to
`entity.combat`, `entity.strategic`, etc. directly inside a domain phase.

---

### Pattern C — Presenter / Read-Model Separation

**What it is:** API routes and WebSocket handlers never receive raw `AuthoritativeState` or
`EntityState`. All API shapes are produced by presenters in `src/api/presenters/`. INFRA-210
(parity ledger) codifies this law: "All API read paths are shaped through ReadModelService /
ReadModelCache / StatePresenter."

**Coverage:** All entity/state endpoints — D14 confirmed; architecture test enforces it
(`tests/architecture/test_api_read_model_guard.py`).

**Key classes:**

| Class | File | Purpose |
|---|---|---|
| `StatePresenter` | `src/api/presenters/state_presenter.py` | Transforms `AuthoritativeState` → API dict. Never mutates state. |
| `DecisionPresenter` | `src/api/presenters/decisions.py` | Shapes decision trace data for `/entities/{id}/decisions` |
| `ScenarioPresenter` | `src/api/presenters/scenarios.py` | Shapes scenario status/checkpoint responses |
| `CampaignHistoryResponse` / `NarrativeLedgerEntryPresenter` | `src/api/presenters/campaigns.py` | Campaign history shapes |
| `ReadModelService` | `src/api/read_model_service.py` | Service layer owning cache and presenter dispatch |
| `ReadModelCache` | `src/api/read_model_cache.py` | Cache layer between authoritative state and presenters |

**How to extend:** Add a new presenter class to `src/api/presenters/<name>.py`. Presenter
methods are `@staticmethod` or `@classmethod`; they receive domain objects and return plain dicts
or typed Pydantic models. Presenters must not import `AuthoritativeState` outside `TYPE_CHECKING`.

---

### Pattern D — Opportunity Extension (Feature Packs / Route Families)

**What it is:** New adventure route types and feature behaviors are registered through the
`FeatureRegistry` and `FeaturePackLoader` (INFRA-PACK-001 through INFRA-PACK-003). A feature pack
declares a `manifest.yaml` and registers new route families or domain hooks without touching
`src/engine/` or `src/domains/` directly.

**Coverage:** Verified in INFRA-PACK-003 via demo escort pack.

**Key classes:**

| Class/File | Purpose |
|---|---|
| `FeatureRegistry` (`src/domains/feature_packs/registry.py`) | Canonical registry; `list_all()` returns enum + pack-registered values |
| `FeaturePackLoader` (`src/domains/feature_packs/loader.py`) | Loads packs filtered by `RuntimeProfile.active_pack_names` |
| `content/packs/demo_escort_pack/manifest.yaml` | Example pack registering `ESCORT_DIGNITARY` |

---

## 3. Mechanics/Engine Constraints

The following engine contracts govern the extension points documented above:

| Contract | File | Governs |
|---|---|---|
| **6-phase deterministic loop** | `docs/engine/kernel.md` | Domain phases run in the COLLECTION and RESOLUTION phases; extension phases must not break phase ordering |
| **Authoritative pipeline (17-phase)** | `docs/engine/authoritative_pipeline.md` | `ApplyPath` is phase 13–17 of the refinement sequence; all domain updates funnel through here |
| **Mutation rules** | `docs/engine/authoritative_mutation_pipeline_contract.md` | Only `ApplyPath` commits durable state; all other code is read-only |
| **Governance/eligibility** | `docs/engine/governance_logic.md` | `should_run()` cadence gate controls which domain phases execute on a given tick |
| **Phase domain permissions** | `src/engine/phase_domain_permissions.py` | `PHASE_READ_DOMAINS` / `PHASE_WRITE_DOMAINS` / `PHASE_EMIT_DOMAINS` per authoritative phase (INFRA-206/207/208) |
| **Core state immutability** | `docs/core/state.md` | `AuthoritativeState` is immutable by convention; `replace()` in `apply.py` constructs new instances |
| **Content hot-path guard** | `src/content/repository.py` | `CatalogRepository.load_all()` must not be called during a kernel tick (INFRA-202) |

---

## 4. Parity Ledger Overlap

Searched `docs/parity_ledger/infrastructure.yaml` (2581 lines) for entries referencing
`design_patterns.md` or doc-currency tracking. **No existing entry references `design_patterns.md`
directly.** Closest related entries:

| Entry ID | Text summary | Relevance |
|---|---|---|
| INFRA-210 | All API read paths shaped through ReadModelService / ReadModelCache / StatePresenter | Directly governs Pattern C (presenter layer) — doc must cite this |
| INFRA-206/207/208 | Phase domain permissions (read/write/emit) | Governs extension point constraints for Pattern A |
| INFRA-204 | `AuthoritativeState` does not import from `src/engine/` | Core boundary that Pattern B depends on |
| INFRA-TYPE-001 | mypy gate configured for src/ (excluding V1 modules: `src/ai/`, `src/town/`, `src/quests/`, `src/entities/`, `src/progression/`) | Confirms V1 modules are explicitly excluded from type-checking — supports V1-is-legacy framing |
| INFRA-180 | Frontmatter validator enforces doc schema | Governs the frontmatter compliance of `design_patterns.md` itself |

**Action required:** Add a new parity ledger entry `INFRA-220` (next available ID after INFRA-219
and INFRA-PACK/TYPE entries) to record: "`docs/guidelines/design_patterns.md` documents V2
extension patterns (Domain Phase, typed update records, presenter layer, feature packs) and does
not present V1 GoalScorer/src/ai/goals/ as active extension points."

---

## 5. Prior Work

### TCK-20260619-P0-DOC-REPAIR

Fixed 5 of 6 stale D17 docs in a single session. The 6th — `design_patterns.md` — was explicitly
deferred with the note: "this doc requires a substantial rewrite rather than a targeted fix, and
is scoped as a separate P1 ticket." This ticket is that P1 follow-up.

Working log entry: `TCK-20260619-P0-DOC-REPAIR,docs,...`

### TCK-20260619-P0-CODE-INTEGRITY

Removed the upward coupling in `src/core/state.py` (lazy import to `src/engine/`), establishing
INFRA-204. This directly informs Pattern B: the boundary between core state and engine is now
architecturally enforced, making it safe to cite `AuthoritativeState` as a pure data type that
domain phases read without risk of circular imports.

### TCK-20260618-AUDIT-D12-PATTERNS

Produced the D12 audit. Finding F3 (this ticket's primary source) scored 8/15 priority, with
Adoption Gap = 5 (entire doc wrong), Risk = 2, Detection = 1. The low Risk/Detection scores mean
the bug is silent — the codebase won't break from following V1 patterns immediately, but the
guidance is structurally wrong and compounds over time.

### TCK-20260618-AUDIT-D11-DEAD-CODE (implied)

Confirmed `src/ai/goals/` is live dead code with compliance IDs — not safe to delete yet (D11
F1 priority 12/15), but also not the V2 extension point. This means the V1 section in
`design_patterns.md` must be archived inline (not removed), because:
1. The files still exist and imports succeed.
2. Some compliance IDs reference them.
3. A developer scanning the codebase will see the files and may look for documentation.

---

## 6. Risks and Open Questions

### Decision: Archive inline vs. remove V1 section

**Recommendation: Archive inline with a clear `## Legacy Patterns (V1 — do not use in new code)`
header.** Rationale:
- `src/ai/goals/` still exists and imports succeed — removing the section entirely creates a doc
  vacuum that might lead developers to think the code is undocumented by accident.
- `docs/engine_future_epics_roadmap.md` (line 140) explicitly cites the V1 dead code removal as a
  future "cheap-fix cluster" after parity ledger audit for SOC/STRAT compliance IDs. Until that
  deletion happens, V1 should be documented as historical.
- The archive approach mirrors the existing `docs/archive/` convention used for superseded content.

### Cross-references to design_patterns.md

From grep results:

| File | Reference | Action |
|---|---|---|
| `docs/guidelines/README.md:14` | `"[Design Patterns](design_patterns.md)": Architectural spines (Aspects, Systems, Presenters)."` | Update description after rewrite — the blurb is also V1-era |
| `docs/plans/open_audit_findings_backlog.md:30` | Mentions the open item and its deferral | No change needed — this is a tracking note |
| `docs/plans/engine_future_epics_roadmap.md:140` | Cross-references design_patterns.md and GoalScorer together in V1 dead-code context | No change needed — that roadmap note is accurate |
| `docs/audits/D11_dead_code.md` | Multiple references to D12/design_patterns.md as context | No change needed — historical audit |
| `docs/audits/D12_pattern_consistency.md` | Primary source of this ticket | No change needed |

### Section numbering gap

Current doc jumps from §5 to §7 (missing §6). The rewrite should renumber sections cleanly.

### Does DamageCalculator belong in V2 patterns?

The `DamageCalculator` strategy pattern (`src/actions/damage.py`) is partially live — combat uses
it via the actions layer. It is not V1-dead. However, it is also not a primary V2 extension point
that parallels domain phases or presenters. Recommendation: include it in a "Combat Extension"
subsection within the new doc, but not as a primary tier-1 pattern alongside Domain Phase/typed
updates/presenters.

---

## 7. Anti-Drift Hazards

If `design_patterns.md` drifts again from V2 patterns, the following categories of harm occur:

1. **Wrong abstractions added to codebase.** A developer following the doc adds `GoalScorer`
   subclasses to V2 code — classes that import from `src/ai/goals/` (excluded from mypy, INFRA-TYPE-001)
   and that the tick path never invokes.

2. **Presenter law bypassed.** If the doc doesn't document the presenter requirement, API routes
   will return raw `AuthoritativeState` or `EntityState` dicts, violating INFRA-210 and
   breaking the architecture test `test_api_read_model_guard.py`.

3. **Mutation in domain phases.** If the doc doesn't explain typed update records, developers
   will mutate `entity.strategic.*` directly in domain phase code, bypassing `ApplyPath` and
   breaking replay determinism (INFRA-101/102).

4. **Type exclusion confusion.** V1 modules (`src/ai/`, etc.) are mypy-excluded (INFRA-TYPE-001).
   If a developer adds new code to `src/ai/goals/` thinking they're following the pattern guide,
   that code escapes type checking silently.

**The key anti-drift guard is a test that fails if `design_patterns.md` still contains V1 symbols
as primary extension-point guidance.** See test_plan.md for the proposed test.
