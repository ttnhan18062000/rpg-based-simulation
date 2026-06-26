---
status: active
layer: guidelines
authority: P1
audience: developer
---

# Design Patterns & Extension Guide

This document describes the V2 extension points used in the RPG Engine V2. These are the canonical
patterns for adding new domains, mutation logic, API shapes, and content packs. V1 patterns are
preserved in a clearly-marked legacy archive section at the bottom of this document — they are
not the extension model for new code.

---

## Overview

| Pattern | Purpose | Primary File(s) |
|---|---|---|
| **1 — Domain Phase Class** | Add new domain logic that reads state and returns typed updates | src/domains/\<name\>/phase.py, `src/engine/pipeline.py` |
| **2 — Decision/Mutation Separation** | Express all state changes as typed update records; never mutate `AuthoritativeState` directly | `src/core/updates.py`, `src/engine/apply.py` |
| **3 — Presenter / Read-Model** | Shape all API responses through presenter classes; never expose raw domain objects | `src/api/presenters/`, `src/api/read_model_service.py` |
| **4 — Feature Pack Registration** | Extend adventure route types and domain behaviors without touching engine internals | `src/domains/feature_packs/registry.py`, `src/domains/feature_packs/loader.py` |

---

## Pattern 1 — Domain Phase Class

### When to use

When you need to add new domain logic that runs on the simulation tick. A domain phase reads
`AuthoritativeState`, computes decisions, and returns a typed update record. It must never
mutate state directly.

### Structure

```
Signature: XPhase.apply(state: AuthoritativeState, ...) -> StateUpdate

Rules:
  - Must NOT mutate AuthoritativeState
  - Must return a typed update record (StateUpdate or domain-specific result)
  - Wire into src/engine/pipeline.py (single integration point)
  - Gate execution via should_run() cadence check (docs/engine/governance_logic.md)
```

**Representative implementation — `AdventureDecisionPhase`** (`src/domains/adventure/phase.py`):

```python
class AdventureDecisionPhase:
    """Simulates subjective routing decisions for heroes."""

    @staticmethod
    def apply(
        state: AuthoritativeState,
        context: Optional[dict] = None,
        trace_writer: Optional[Any] = None,
        faction_directives: Optional[list] = None,
        factions: Optional[Any] = None,
    ) -> StateUpdate:
        update = StateUpdate()
        # ... read state, compute decisions ...
        return StateUpdate(entity_updates=entity_updates)
```

### Reference implementations

All 8 domain phases use this pattern (D12 audit — all confirmed):

| Phase Class | File | Typed Return |
|---|---|---|
| `AdventureDecisionPhase` | `src/domains/adventure/phase.py` | `-> StateUpdate` |
| `ProgressionPhase` | `src/domains/progression/phase.py` | `-> Optional[ProgressionConversionResult]` |
| `CooperationPhase` | `src/domains/cooperation/phase.py` | `-> Optional[CooperationResult]` |
| `CombatEngagementPhase` | `src/domains/combat_engagement/phase.py` | `-> CombatEngagementDecisionResult` |
| `InformationPhase` | `src/domains/information/phase.py` | `-> Optional[InformationResult]` |
| `WorldEmergencePhase` | `src/domains/world_emergence/phase.py` | missing return annotation (P2 gap — D12 F4) |
| `PerceptionPhase` | `src/domains/perception/phase.py` | missing return annotation (P2 gap — D12 F4) |
| `MemoryPhase` | `src/domains/memory/phase.py` | missing return annotation (P2 gap — D12 F4) |

### Engine constraints

- **6-phase deterministic loop** (`docs/engine/kernel.md`): domain phases run in the COLLECTION
  and RESOLUTION phases. New phases must not break phase ordering.
- **Governance/eligibility** (`docs/engine/governance_logic.md`): `should_run()` controls which
  domain phases execute on a given tick.
- **Phase domain permissions** (`src/engine/phase_domain_permissions.py`): `PHASE_READ_DOMAINS`,
  `PHASE_WRITE_DOMAINS`, and `PHASE_EMIT_DOMAINS` define per-phase read/write/emit scopes
  (compliance IDs: INFRA-206, INFRA-207, INFRA-208).

### How to add a new domain phase

1. Create src/domains/\<name\>/phase.py with a class \<Name\>Phase.
2. Implement a `@staticmethod apply(state: AuthoritativeState, ...) -> StateUpdate` method.
3. Do not mutate `state` or any entity directly inside the phase body.
4. Wire the phase into `src/engine/pipeline.py`.
5. Add the phase's read/write/emit scopes to `src/engine/phase_domain_permissions.py`
   (INFRA-206/207/208).
6. Add tests in tests/unit/\<name\>/ and `tests/architecture/` for isolation.

---

## Pattern 2 — Decision/Mutation Separation via Typed Update Records

### When to use

Whenever you need to express a durable state change. Domain phases must never write to
`entity.combat`, `entity.strategic`, or any `AuthoritativeState` field directly. Instead they
construct typed update records and return them. The `ApplyPath` (`src/engine/apply.py`) is the
only place durable state is committed.

### Structure

```
Domain phase computes → returns StateUpdate
  └─► ApplyPath._compute_entity_changes() merges typed update records
      └─► AuthoritativeState is reconstructed (immutable replace())
          └─► Durable state committed
```

### Key types

All update records live in `src/core/updates.py`:

| Record | Purpose |
|---|---|
| `StateUpdate` | Top-level container; holds `entity_updates: Dict[int, EntityUpdate]` |
| `EntityUpdate` | Per-entity change record; fields for strategic, stamina, navigation, etc. |
| `StrategicUpdate` | Strategic-component delta (projects, objectives, directives) |
| `StaminaUpdate` | Stamina delta |
| `NavigationUpdate` | Movement / position delta |
| `EquipmentUpdate` | Equipment slot / durability delta |
| `RejectionEvent` | Structured authoritative rejection record (`frozen=True, slots=True`) |

**`ApplyPath`** lives in `src/engine/apply.py`. Compliance IDs: PERF-017, RES-202.

### Engine constraints

- **Authoritative pipeline** (`docs/engine/authoritative_pipeline.md`): `ApplyPath` is phases
  13–17 of the 17-phase refinement sequence. All domain updates funnel through here.
- **Mutation rules** (`docs/engine/authoritative_mutation_pipeline_contract.md`): only `ApplyPath`
  commits durable state; all other code is read-only.
- **Core state boundary** (INFRA-204): `AuthoritativeState` does not import from `src/engine/`.
  Domain phases can safely receive state without circular import risk.

### How to add a new update record

1. Add a frozen dataclass to `src/core/updates.py`:
   ```python
   @dataclass(frozen=True, slots=True)
   class MyUpdate:
       some_field: int = 0
   ```
2. Add the field to `EntityUpdate` (or `StateUpdate` if it is entity-independent).
3. Handle the field in `ApplyPath._compute_entity_changes()` in `src/engine/apply.py`.
4. Add a parity ledger entry in `docs/parity_ledger/` and a test in `tests/architecture/`.

---

## Pattern 3 — Presenter / Read-Model Separation

### When to use

Whenever you add a new API endpoint or WebSocket event that exposes world state. API routes and
handlers must never receive raw `AuthoritativeState` or `EntityState`. All API shapes are produced
by presenter classes in `src/api/presenters/`. This law is enforced at import level by
`tests/architecture/test_api_read_model_guard.py`.

### Structure

```
API route / handler
  └─► ReadModelService (src/api/read_model_service.py)
      └─► ReadModelCache (src/api/read_model_cache.py)
          └─► Presenter.present_*(state_or_entity) -> dict | Pydantic model
                  └─► Returns plain data — never the domain object itself
```

Rules:
- Presenter methods are `@staticmethod` or `@classmethod`.
- Presenters must not import `AuthoritativeState` outside `TYPE_CHECKING`.
- Return plain dicts or typed Pydantic models — never raw `EntityState` etc.

Parity law: INFRA-210 — "All API read paths are shaped through `ReadModelService` /
`ReadModelCache` / `StatePresenter`."

### Key classes

| Class | File | Purpose |
|---|---|---|
| `StatePresenter` | `src/api/presenters/state_presenter.py` | Transforms `AuthoritativeState` → API dict; never mutates state |
| `DecisionPresenter` | `src/api/presenters/decisions.py` | Shapes decision trace data for `/entities/{id}/decisions` |
| `ScenarioPresenter` | `src/api/presenters/scenarios.py` | Shapes scenario status / checkpoint responses |
| `CampaignHistoryResponse` / `NarrativeLedgerEntryPresenter` | `src/api/presenters/campaigns.py` | Campaign history shapes |
| `ReadModelService` | `src/api/read_model_service.py` | Service layer owning cache and presenter dispatch |
| `ReadModelCache` | `src/api/read_model_cache.py` | Cache layer between authoritative state and presenters |

### Engine constraints

- INFRA-210 (parity ledger) codifies this law.
- `tests/architecture/test_api_read_model_guard.py` enforces it at import level.

### How to add a new presenter

1. Create src/api/presenters/\<name\>.py with a class \<Name\>Presenter.
2. Implement `@staticmethod` or `@classmethod` methods that accept domain objects and return
   plain dicts or typed Pydantic models.
3. Import `AuthoritativeState` only under `TYPE_CHECKING`.
4. Call the presenter from `ReadModelService` (or a dedicated route handler).
5. Add or update a parity ledger entry referencing the new presenter.

---

## Pattern 4 — Feature Pack Registration (Opportunity Extension)

### When to use

When adding new adventure route families or domain-level behaviors that should be loadable
at runtime without touching `src/engine/` or core domain files. Feature packs declare a
`manifest.yaml` under `content/packs/<name>/` and are loaded by `FeaturePackLoader`.

### Structure

```
content/packs/<name>/manifest.yaml   ← declares route type or domain hook
  └─► FeaturePackLoader.load()       ← filters by RuntimeProfile.active_pack_names
      └─► FeatureRegistry.register() ← makes hook available in FeatureRegistry.list_all()
```

### Key classes and files

| Class / File | Purpose |
|---|---|
| `FeatureRegistry` (`src/domains/feature_packs/registry.py`) | Canonical registry; `list_all()` returns enum + pack-registered values, canonical first |
| `FeaturePackLoader` (`src/domains/feature_packs/loader.py`) | Loads packs filtered by `RuntimeProfile.active_pack_names`; skips absent packs |
| `content/packs/demo_escort_pack/manifest.yaml` | Example pack registering `ESCORT_DIGNITARY` route type |

### Engine constraints

- INFRA-PACK-001: `FeatureRegistry.list_all()` returns canonical enum values before
  pack-registered keys; both groups sorted alphabetically.
- INFRA-PACK-002: `FeaturePackLoader` skips packs absent from `RuntimeProfile.active_pack_names`.
- INFRA-PACK-003: Demo escort pack registers `ESCORT_DIGNITARY` without modifying `src/engine/`
  or `src/domains/`.

### How to add a new feature pack

1. Create `content/packs/<name>/manifest.yaml` declaring the route type or hook.
2. Add the pack name to `RuntimeProfile.active_pack_names` for the target environment.
3. `FeaturePackLoader` will load and register the pack on next startup.
4. Add unit tests in `tests/unit/feature_packs/`.

---

## Pattern 5 — Combat Extension (Strategy Pattern, Partially Live)

**Location:** src/actions/damage.py (V1 — file removed)

The `DamageCalculator` strategy pattern is partially live — combat uses it via the actions layer
for physical and magical damage resolution. It is not a primary V2 extension point for new domain
logic (use Domain Phase for that), but it is documented here to avoid confusion.

| Class | Purpose |
|---|---|
| `DamageCalculator` | ABC: `damage_type`, `resolve(attacker, defender) -> DamageContext` |
| `DamageContext` | Dataclass: `atk_power`, `def_power`, `atk_mult`, `def_mult`, `train_action` |
| `DAMAGE_CALCULATORS` | Registry dict: `DamageType -> DamageCalculator` |

When to use `DamageCalculator` vs. Domain Phase: use `DamageCalculator` only for extending
combat damage resolution math (new damage types). Use Domain Phase for any new domain-level
decision logic that reads state and produces strategic updates.

---

## Legacy Patterns (V1 — do not use in new code)

> **Historical archive.** The patterns below were used in V1 and are preserved here because the
> source files (src/ai/goals/, src/core/entity_builder.py) still exist for compliance reasons.
> They are **not** exercised by the V2 tick path. Do not add new code following these patterns.
> See `docs/plans/open_audit_findings_backlog.md` §2 for the D11/D12 audit findings that deprecated them.
> `src/ai/` is explicitly excluded from mypy type checking (INFRA-TYPE-001).

---

### V1 Pattern A — Goal Evaluation (GoalScorer Plugin)

**Location:** `src/ai/goals/`

Each AI goal is a self-contained `GoalScorer` subclass. The `GoalEvaluator` iterates all
registered scorers without knowing their internals. New goals were added by creating a class and
registering it in `GOAL_REGISTRY` via `register_goal()`.

```
GoalScorer (ABC)
├── CombatGoal      → AIState.HUNT
├── FleeGoal        → AIState.FLEE
├── ExploreGoal     → AIState.WANDER
├── LootGoal        → AIState.LOOTING
├── TradeGoal       → AIState.VISIT_SHOP
├── RestGoal        → AIState.RESTING_IN_TOWN
├── CraftGoal       → AIState.VISIT_BLACKSMITH
├── SocialGoal      → AIState.VISIT_GUILD
└── GuardGoal       → AIState.GUARD_CAMP
```

| Class | File | Purpose |
|---|---|---|
| `GoalScorer` | `src/ai/goals/base.py` | ABC: `name`, `target_state`, `score(ctx)` |
| `GoalScore` | `src/ai/goals/base.py` | Dataclass: `(goal, score, target_state)` |
| `GoalEvaluator` | `src/ai/goals/base.py` | `evaluate(ctx)` → sorted scores, `select(scores, rng)` → winner |
| `GOAL_REGISTRY` | `src/ai/goals/base.py` | Module-level list of registered `GoalScorer` instances |
| `register_goal()` | `src/ai/goals/base.py` | Append a scorer to the registry |

**Status:** Dead code on the V2 tick path (D11 audit). V2 equivalent is Domain Phase (Pattern 1).

---

### V1 Pattern B — Entity Construction (EntityBuilder)

**Location:** src/core/entity_builder.py (V1 — file removed)

The `EntityBuilder` provides a fluent API for constructing `Entity` instances. All V1 spawn sites
used the same builder, eliminating construction code duplication.

```python
hero = (
    EntityBuilder(rng, eid, tick=0)
    .kind("hero")
    .at(pos)
    .with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3)
    .build()
)
```

**Status:** V1 entity construction. The V2 equivalent is `WorldAssemblyResolver`.

---

### V1 Pattern C — Trait Aggregation (UtilityBonus)

**Location:** src/core/traits.py (V1 — file removed)

Trait aggregation in V1 used typed dataclasses (`UtilityBonus`, `TraitStatModifiers`) as goal-scoring
scaffolding. `UtilityBonus` is excluded from mypy (INFRA-TYPE-001) and is V1 goal-scoring
infrastructure.

| Dataclass | Purpose (V1) |
|---|---|
| `UtilityBonus` | Additive modifiers for V1 goal scoring — all fields default `0.0` |
| `TraitStatModifiers` | Passive stat modifiers — used in trait resolution |

**Status:** `UtilityBonus` is V1 goal-scoring scaffolding; not used in V2 domain phase decisions.
`TraitStatModifiers` may be partially live for stat resolution but is not a V2 extension point.
