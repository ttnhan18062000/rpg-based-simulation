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
| **6 — Compile-Time Pillar Activation** | Diagnose and fix a SimQ pillar stuck at `C` because `WorldCompiler.compile()` never constructs a durable-state field | `src/worldbuilding/schema.py`, `src/worldbuilding/compiler.py`, `src/worldassembly/schema.py`, `src/worldassembly/resolver.py` |

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

**Representative implementation — `CombatEngagementPhase`** (`src/domains/combat_engagement/phase.py`):

```python
class CombatEngagementPhase:
    """Resolves pre-combat engagement decisions for entities."""

    @staticmethod
    def apply(
        state: AuthoritativeState,
        context: Optional[dict] = None,
    ) -> CombatEngagementDecisionResult:
        # ... read state, compute decisions ...
        return CombatEngagementDecisionResult(entity_updates=entity_updates)
```

**Formerly also `AdventureDecisionPhase`** (`src/domains/adventure/phase.py`) — deleted by
TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE. Adventure routing now follows a *different* pattern:
it is a tier-5 `GoalScorer` (`AdventureGoalScorer.score(entity, state) -> GoalScore`, registered in
`GoalRegistry`, `src/ai/goals/adventure_scorer.py`), not a dedicated pipeline-phase class — see
`docs/mechanics/04_strategic_cognition.md` §2 for that pattern instead. Do not use the deleted
class as a template for new domain logic; use one of the 7 reference implementations below, or the
`GoalScorer` protocol (`src/ai/goals/base.py`) if the new logic is itself a competing strategic
goal candidate rather than an unconditional per-tick phase.

### Reference implementations

All 7 remaining domain phases use this pattern (D12 audit found 8; `AdventureDecisionPhase` was
deleted by TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE and is no longer one of them):

| Phase Class | File | Typed Return |
|---|---|---|
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

## Pattern 6 — Compile-Time Pillar Activation Pattern

### When to use

When a SimQ pillar is stuck at grade `C` (or lower) with `calibration_hits == 0` on every event
type it scores, and investigation traces the root cause to a durable-state field on
`AuthoritativeState` that is **permanently empty/default for every compiled world** — not a
scoring bug, not a threshold bug, but a bootstrap gap: nothing in `WorldCompiler.compile()` ever
constructs the field at all, so the scoring condition can never be satisfied regardless of what
world content is authored. This pattern was independently discovered and applied twice —
`TCK-20260702-SIMQ-UPLIFT2-FACTION` (for `AuthoritativeState.factions`) and
`TCK-20260702-SIMQ-UPLIFT2-INFORMATION` + `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` (for
`AuthoritativeState.information_source_profiles` / `pending_information_responses`) — with the
exact same shape both times. Reach for this pattern before re-deriving it from scratch.

### The failure signature

Confirm the diagnosis with one grep before doing anything else: find the single
`AuthoritativeState(...)` constructor call inside `WorldCompiler.compile()`
(`src/worldbuilding/compiler.py`) — there is exactly one authoritative init point for a fresh
`AuthoritativeState` — and check whether the suspect field's keyword argument is passed at all.
If it is simply absent from that call, the field falls back to its dataclass default
(`field(default_factory=list, ...)` / `field(default_factory=dict, ...)`) on every compiled world,
with no way for any `world.yaml` content to ever populate it. This is the bug class, not a
one-world content gap.

### The fix shape

```
WorldSpec (src/worldbuilding/schema.py)
  new typed spec field, e.g. FooSpec / List[FooSpec]
    │
    ▼ mirrored onto (both, or normalize() raises ValidationError on every world — see trap below)
WorldCompositionSpec + NormalizedWorldComposition (src/worldassembly/schema.py)
    │
    ▼ resolver passthrough (no catalog) or override-merge (catalog exists)
WorldAssemblyResolver.assemble() (src/worldassembly/resolver.py)
    │
    ▼ constructs domain object(s) from the resolved spec field
WorldCompiler.compile() (src/worldbuilding/compiler.py)
    │
    ▼ passed into the single AuthoritativeState(...) constructor call
AuthoritativeState.<field> is no longer permanently empty
```

**Step 1 — schema field, composition-level not module-level.** Add the typed field to `WorldSpec`
directly, then mirror it onto `WorldCompositionSpec`. Author the actual content at the
**composition level** (`data/worlds/<world>/world.yaml`), not on a shared `world_modules/*.yaml`
file — a module can be referenced by several worlds (FACTION's investigation found
`frontier_village_core`/`bandit_road_trade_pressure` alone are shared by 7 worlds), so any field
declared on a module leaks into every world that references it. Composition-level scoping is the
only mechanism that activates exactly one target world.

**The `extra="forbid"` mirroring trap.** `WorldCompositionNormalizer.normalize()` does
`composition.model_dump()` then `NormalizedWorldComposition(**data)`. Since `model_dump()` always
serializes every field on `WorldCompositionSpec` (including the new one, defaulting to
`{}`/`[]` when unset), and `NormalizedWorldComposition` has
`model_config = ConfigDict(frozen=True, extra="forbid")`, **forgetting to mirror the new field
onto `NormalizedWorldComposition` raises `pydantic.ValidationError` on every call to
`normalize()`, for every world composition, not just the target one.** This is the exact omission
the FACTION ticket's architecture review caught before it shipped (see
`stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/plan.md`, "Review Fix Log"). Treat the
`WorldCompositionSpec` field and its `NormalizedWorldComposition` mirror as one atomic change —
never land one without the other.

**If a global catalog exists for the content (e.g. the faction catalog,
`data/content/social/factions.yaml`), a plain per-world field is not enough.**
`WorldAssemblyResolver.assemble()` may pre-seed the composed dict from the *entire* catalog before
any module merge — check for this before assuming an override will apply cleanly. FACTION's
`faction_tension_overrides` had to be applied as an explicit override-merge *after* the
catalog+module merge completes, validated against the already-merged keys (fail fast with
`ValueError` on an unknown ID — don't silently no-op a typo). If no catalog exists for the content
(both INFORMATION cases), the resolver step is a direct passthrough with no merge and no
membership validation needed.

**Compiler construction is additive, not conditional.** Build the domain object(s) for every spec
entry (including ones at their default value) and pass the result into the single
`AuthoritativeState(...)` call. Do not add a second construction path anywhere else — that call is
the one seeding point.

### The verification shape

Verify at every layer, not just the end state:
1. **Schema round-trip tests** — the new field defaults correctly when absent, round-trips when
   present, and rejects out-of-bound values; the `NormalizedWorldComposition` mirror round-trips
   unchanged for both the empty and populated case (this is the direct regression guard for the
   `extra="forbid"` trap above).
2. **Compiler seeding tests** — a hand-built `WorldSpec` fixture (no resolver needed) proves
   `AuthoritativeState.<field>` is populated correctly, including the "no entries declared → empty
   result" regression guard.
3. **Resolver passthrough/override tests** — a composition declaring the field is passed straight
   through (or merged/overridden) correctly, and a composition that does **not** declare it is
   provably byte-identical to prior behavior (every other world must be unaffected).
4. **A direct-pipeline integration test** that loads the real resolved YAML for the target world,
   compiles it, and asserts the seeded value reaches `AuthoritativeState` and produces the correct
   effect one layer up (e.g. `compute_transitions()` firing a transition, or
   `InformationBeliefPhase.apply()` assimilating a fact) — proves the full compile path, not just
   isolated unit fixtures.
5. **Real recalibration through the live loop** — run `tools/calibrate_simq.py` against the target
   world/scenario set and confirm `calibration_hits > 0` in the actual `quality_report.json`, not
   just a compile-time assertion. A unit test proving the domain object is constructed correctly is
   not sufficient proof that the pillar activated — `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`
   found a *second*, unrelated bug (a kernel tick-alignment mismatch,
   `Kernel._phase_advancement()` comparing a post-advance `tick` against a pre-advance-stamped
   property) that kept `calibration_hits` at `0` through the real live loop even after the
   compile-time plumbing was fully correct and unit-tested. Only the live recalibration run catches
   this class of gap. Spot-check at least one untouched sibling world in the same recalibration
   pass to confirm zero leakage.

### The known pitfall: compile-time seeding is not automatically persistent across ticks

`WorldCompiler.compile()` only runs once, at world-load time. From tick 1 onward,
`ApplyPath.apply_generation()` (`src/engine/apply.py`, called every tick from
`Kernel._phase_advancement()`) rebuilds `AuthoritativeState` from `prior_state` via its own
`AuthoritativeState(...)` constructor call — a **second**, separate construction site from the
compiler's. **Whether a compile-time-seeded field survives into that rebuild is a per-field,
explicit choice in `apply_generation()`'s merge logic — it is not automatic just because the field
exists on `AuthoritativeState`.**

- `factions` was explicitly added to `apply_generation()`'s carry-forward logic — `FactionState`
  persists and accumulates (`tension_level` deltas, etc.) across the whole run.
- `information_source_profiles` and `pending_information_responses` were **not** added to
  `apply_generation()`'s carry-forward logic. `pending_information_responses` in particular is
  visible to `InformationBeliefPhase.apply()` for exactly one `refine()` call — the initial
  compiled state at tick 0 — and is silently reset to `[]` (its dataclass default) on every
  subsequent tick advancement. The seed fires **once, then stops**; it does not re-fire and it is
  not an inbox that accumulates. This is not a bug: a bounded, single-fire assimilation is a
  correct and fully-verified outcome for `pending_information_responses` (documented as rationale
  class **Bounded** in `docs/guidelines/intentional_divergences.md`), and it is a deliberate
  difference from `factions`' persistent-across-ticks behavior, not an oversight in either
  direction.

Whenever you add a new compile-time-seeded field, **decide explicitly** whether it must persist
across ticks (add it to `apply_generation()`'s merge/reconstruction logic and test that it survives
tick 2, tick N) or is intentionally single-fire/one-shot (leave `apply_generation()` untouched, but
say so explicitly in the parity ledger entry and, if the single-fire behavior is a deliberate
divergence worth flagging, in `docs/guidelines/intentional_divergences.md`). Do not leave this
question implicit — grep `src/engine/apply.py`'s final `AuthoritativeState(...)` call for the new
field's keyword to confirm which behavior actually ships, rather than assuming either one.

### Reference implementations

| Ticket | Field(s) activated | Catalog? | Persistence | Parity ledger |
|---|---|---|---|---|
| `TCK-20260702-SIMQ-UPLIFT2-FACTION` | `AuthoritativeState.factions` (`FactionState.tension_level`) | Yes — global faction catalog forced a composition-level override-merge (`faction_tension_overrides`), not a plain passthrough | Persistent — carried forward every tick by `apply_generation()` | `docs/parity_ledger/faction.yaml::FAC-012` |
| `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` | `AuthoritativeState.information_source_profiles` | No catalog — direct passthrough | N/A (static source-profile data, not a per-tick mutable record) | `docs/parity_ledger/infrastructure.yaml::INFRA-256` |
| `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` | `AuthoritativeState.pending_information_responses` | No catalog — direct passthrough | Single-fire only — not carried forward by `apply_generation()`; fires once at tick 0 (documented, correct, not a bug) | `docs/parity_ledger/infrastructure.yaml::INFRA-257` |

Read `FAC-012` and `INFRA-256`/`INFRA-257` for the exact `v2_evidence` file:line references and
measured `calibration_hits` outcomes before starting a new application of this pattern — they are
the canonical worked examples this section summarizes.

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
