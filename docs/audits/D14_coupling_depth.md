---
status: active
layer: architecture
authority: P1
audience: agent
tags: [audit, coupling, domain-boundaries, architecture, imports, layer-violations]
---

# D14 — Coupling Depth

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | B — Codebase / Architecture |
| **State** | `done` |
| **Impact** | 4 / 5 |
| **Interest** | 3 / 5 |
| **Priority** | 7 |
| **Method** | code-read + scan |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Where do hidden dependencies violate domain ownership,
and which couplings create change-cascade risk if either side evolves?

**Related dimensions:** D09 (System Wiring) — confirms which domain phases are live;
D10 (Test Coverage) — observability→Kernel coupling makes observability hard to test in
isolation; D13 (Type Safety) — some couplings exist because types aren't fully separated.

---

## Classification Method

Coupling findings are scored on three dimensions. Higher score = higher priority to remediate.

### Coupling Risk Scoring

3 dimensions, each 1–5. Maximum: 15.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Contract Breach** | Expected by design, documented exception | Undocumented but tolerable | Named prohibited pattern in architecture docs |
| **Change Sensitivity** | Depended-on module is stable, unlikely to change | Module changes occasionally | Module is a god node — changes propagate to many consumers |
| **Detectability** | Fails immediately / loud import error | Caught by test suite | Invisible without a dedicated import scanner |

---

## Layer Architecture

Expected dependency flow (lower layers must not import from higher):

```
content ─────────────────────────────┐
core  ────────────────────────────── │ (base types — imports nothing)
domains ──────── → core only         │
engine ─────────→ core + domains     │
observability ──→ engine             │
api ────────────→ engine + core      │
lab ────────────→ engine             │
systems ─────────→ core + engine (pinned exceptions, see Coupling Inventory)
```

`src/systems/` had no position in this diagram until
`TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` (2026-08-19) — the 2026-06-18 audit that
produced this doc never assigned it a layer. It is added here as a freeze-at-baseline: the 13
`systems → engine` sites found at that ticket's audit are pinned as grandfathered exceptions
(see Coupling Inventory below), not eliminated. This is not a claim that the boundary is
cleanly honored — it is 13 sites frozen at their current count, with growth past that count
blocked by the new test.

`optimization` domain is explicitly permitted cross-cutting — any domain may use it.

---

## Coupling Inventory

### Layer: `src/domains/` — 14 domains

**Cross-domain import scan** (prohibited by `domain_ownership_map.md` §Prohibited Patterns):

| From | To | File | Finding |
|---|---|---|---|
| `memory` | `time` | `memory/phase.py:20` | ⚠️ Violation |
| any | `optimization` | multiple | ✅ Permitted (explicit exception) |
| all others | all others | — | ✅ Clean |

Only 1 prohibited cross-domain import exists in the entire codebase.

**Engine/Kernel access** (domains must not call `Kernel.tick_once()` except `campaigns`):

- `campaigns` — explicitly permitted per `campaigns_contract.md`. Wraps Kernel internally for multi-tick analysis.
- All other 13 domains — 0 Kernel imports. ✅ Clean.

**AuthoritativeState direct mutation** (domains must not mutate — must return typed records):

- 0 direct `authoritative_state.field =` assignments found in any domain. ✅ Clean.

---

### Layer: `src/core/` — upward dependencies

`core` is the base layer. It must not import from `engine` or `domains`.

| File | Import | Pattern |
|---|---|---|
| `core/state.py:1057` | `src.engine.movement_cache.MovementPlanCache` | Lazy (inside `__post_init__`) |
| `core/updates.py:15` | `src.engine.policy.GovernorPolicy` | Conditional (`TYPE_CHECKING` guard) |

Both are hidden behind lazy/conditional import guards — not hard top-level imports. They exist
to break circular import chains. Neither causes a runtime import at module load time.

---

### Layer: `src/engine/` — domain integration

**`pipeline.py` is the single engine→domain integration point.** All 7 domain phase imports
live in `pipeline.py` only:

```
pipeline.py → domains.optimization (feature flags)
pipeline.py → domains.information  (InformationBeliefPhase)
pipeline.py → domains.cooperation  (CooperationPhase)
pipeline.py → domains.adventure    (AdventureDecisionPhase)
pipeline.py → domains.combat_engagement (CombatEngagementPhase)
pipeline.py → domains.world_emergence   (WorldEmergencePhase)
pipeline.py → domains.progression  (ProgressionConversionPhase)
```

All imports are of `Phase` orchestration classes — not domain model types. ✅ Clean structure.

Note: 7 of 14 domains are wired into `pipeline.py`. The other 7 (perception, time, memory,
motivation, commitment, emotion, campaigns) are either invoked through co-scheduling, event
triggers, or are analysis-only. This is expected per the domain ownership map.

---

### Layer: `src/api/` — engine access and route model exposure

**`engine_manager.py` imports:**

| Import | File | Assessment |
|---|---|---|
| `src.engine.kernel.Kernel` | `engine_manager.py:9` | Expected — manager controls engine |
| `src.engine.metrics.MetricsService` | `engine_manager.py:144` | Expected — lazy metrics access |
| `src.engine.cache_registry.*` | `read_model_cache.py:7` | Expected — read cache uses engine registry |

**Route handlers raw model exposure:**

All 4 entity/state endpoints go through a DTO or presenter layer:

| Endpoint | Returns | Presenter? |
|---|---|---|
| `GET /api/v1/entities/{id}` | `read_cache.get_entity_dto()` | ✅ DTO |
| `GET /api/v1/entities` | `read_cache.get_entities_paged()` | ✅ DTO |
| `GET /api/v1/state` | `read_cache.get_minimal_summary()` | ✅ DTO |
| `GET /api/v1/inspect` | `StatePresenter.present_full()` | ✅ Presenter (deprecated) |

No raw domain model is directly serialized from a route handler. ✅ Clean.

---

### Layer: `src/observability/` — engine coupling

| File | Import | Assessment |
|---|---|---|
| `sweeper.py` | `src.engine.kernel.Kernel` | Expected — sweeper drives engine |
| `controller.py` | `src.engine.kernel.Kernel` | Expected — controller orchestrates engine |
| `harness.py` | `src.engine.kernel.Kernel` | Expected — harness wraps engine |
| `hard_law_monitor.py` | `src.engine.world_index.WorldIndexService` | ⚠️ Tighter than needed |

The first three are expected: observability instruments and drives the engine.
`hard_law_monitor.py` importing `WorldIndexService` (a concrete service class, not the kernel)
is tighter — it depends on a specific engine internal rather than the kernel boundary.

---

### Layer: `src/content/` — fully isolated

0 imports from `engine` or `domains`. Content is a pure data layer. ✅ Exemplary.

---

## Key Findings

### F1 — `memory` → `time` prohibited cross-domain import — Risk: 7 / 15

> **RESOLVED: TCK-20260619-P0-CODE-INTEGRITY (2026-06-19):** TemporalPressureService injected via pipeline orchestrator; direct cross-domain import removed.

| Dimension | Score | Reason |
|---|---|---|
| Contract Breach | 5 | Explicit prohibited pattern: "A domain must not import from another domain package" |
| Change Sensitivity | 1 | `time.service.TemporalPressureService` is stable; unlikely to change frequently |
| Detectability | 1 | Immediately visible with an import scanner; not hidden |
| **Total** | **7** | |

`src/domains/memory/phase.py:20` imports `TemporalPressureService` from `src.domains.time`.
Both `memory` and `time` share the "Memory Update" pipeline stage — they are co-scheduled,
which explains why the author reached across. But co-scheduling is not an architecture exemption.

**Correct fix:** inject `TemporalPressureService` into `MemoryUpdatePhase.__init__` from the
engine's pipeline orchestrator — the same way all other cross-domain services are provided.

---

### F2 — `core` → `engine` upward lazy imports — Risk: 10 / 15

> **RESOLVED: TCK-20260619-P0-CODE-INTEGRITY (2026-06-19):** MovementPlanCache construction moved to pipeline bootstrap; injected into AuthoritativeState as dependency.

| Dimension | Score | Reason |
|---|---|---|
| Contract Breach | 3 | Upward dependency is an architecture smell but not a named prohibited pattern; lazy guards soften it |
| Change Sensitivity | 4 | `core/state.py` is imported by nearly every file in the codebase; any engine change that touches `MovementPlanCache` or `GovernorPolicy` ripples through core |
| Detectability | 3 | Hidden behind `__post_init__` / `TYPE_CHECKING` guard — not found by naive import grep; requires a scanner |
| **Total** | **10** | |

Two files in `core` carry lazy upward imports:

**`core/state.py:1057`** — inside `AuthoritativeState.__post_init__`:
```python
from src.engine.movement_cache import MovementPlanCache
object.__setattr__(self, "movement_cache", MovementPlanCache())
```
The core state model is initializing an engine-layer cache object inside its own constructor.
This conflates data model and engine service — `AuthoritativeState` should not know that
`MovementPlanCache` exists, let alone construct one.

**`core/updates.py:15`** — inside `TYPE_CHECKING` guard:
```python
from src.engine.policy import GovernorPolicy
```
Used for type annotation only. Lower-risk than the state.py case, but still couples the
core updates type to an engine policy concept.

**Risk:** `core/state.py` is the most-imported file in the codebase. Engine changes to
`MovementPlanCache` or its constructor will touch core state without a visible dependency signal.

---

### Layer: `src/domains/` — upward dependency into `src/observability/`

`domains` is documented (`domains → core only`, above) as never importing `observability`. 2
real, currently-shipping violations exist — both lazy, method-body imports of the same pure
`SimulationEvent` dataclass, guarded by an event-recorder-present check immediately above each
call site:

| File | Line | Import | Pattern |
|---|---|---|---|
| `domains/campaigns/narrative_ledger.py:71` | `src.observability.events.SimulationEvent` | Lazy (inside `emit_chronicle_event`, guarded by `if self._event_recorder is not None:`) |
| `domains/campaigns/orchestrator.py:418` | `src.observability.events.SimulationEvent` | Lazy (inside shared helper `_emit_domain_event()`, guarded by `if self._event_recorder is None: return` at each of its 3 callers — `_emit_chronicle_events()`, `_emit_grief_urgency_events()`, `_emit_nemesis_event()` — before every call) |

Both sites are enforced-pinned by
`tests/architecture/test_phase18_import_boundaries.py::test_domains_do_not_import_observability_outside_pinned_exceptions`
(added by `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`) — a `(file, lineno)`-exact
grandfather list, not a general allowlist. Expanding this set requires updating both this doc
and that test together, not a silent addition.

---

### Layer: `src/systems/` — upward dependency into `src/engine/`

`src/systems/` has no documented position prior to this ticket (see Layer Architecture above).
13 real, currently-shipping `systems → engine` imports exist across 5 files, both module-level
and lazy:

| File | Lines | Modules |
|---|---|---|
| `systems/strategic_systems/intelligence.py` | 70, 76, 79, 84, 663, 828, 832, 904, 957 | `engine.policy`, `engine.spatial_query`, `engine.cadence`, `engine.domain_logic`, `engine.cognition` |
| `systems/strategic_systems/detour.py` | 22 | `engine.domain.lead_routing` |
| `systems/strategic_systems/redirection.py` | 25 | `engine.cadence` |
| `systems/economy_systems/market.py` | 50 | `engine.legality` |
| `systems/world_systems/routine.py` | 180 | `engine.legality` |

All 13 sites are enforced-pinned by
`tests/architecture/test_phase18_import_boundaries.py::test_systems_do_not_import_engine_outside_pinned_exceptions`
(added by `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`) — a `(file, lineno)`-exact
grandfather list, not a general allowlist. This is a freeze-at-baseline, not a clean, fully
honored boundary: the pinned sites remain exactly as found, no new violation past the pinned 13
is permitted, and expanding the pinned set requires updating both this doc and that test
together, not a silent addition.

---

### F3 — `hard_law_monitor` → `WorldIndexService` (tighter-than-needed engine coupling) — Risk: 8 / 15

> **Ticket:** TCK-20260627-P2G-KERNEL-FACADE

| Dimension | Score | Reason |
|---|---|---|
| Contract Breach | 2 | Observability→engine coupling is expected; importing a concrete internal service (not Kernel) is tighter |
| Change Sensitivity | 3 | `WorldIndexService` is a concrete class — any signature change ripples to the monitor |
| Detectability | 3 | Not caught by standard domain-boundary checks; requires layer-specific scanning |
| **Total** | **8** | |

`src/observability/live/hard_law_monitor.py` imports `WorldIndexService` from
`src.engine.world_index`. The other three observability files (`sweeper`, `controller`,
`harness`) only import `Kernel` — a stable integration boundary. `WorldIndexService` is
an internal engine service; if its interface evolves the monitor breaks.

**Correct fix:** expose spatial query capability through `Kernel` or a `KernelQueryFacade`
rather than letting observability reach into engine internals.

---

### Coupling Risk Summary

| Finding | Description | Risk Score |
|---|---|---|
| F2 | `core` → `engine` upward lazy imports | **10 / 15** |
| F3 | `hard_law_monitor` → `WorldIndexService` tight coupling | **8 / 15** |
| F1 | `memory` → `time` prohibited cross-domain import | **7 / 15** |

---

## Positive Findings

These coupling boundaries are clean and worth preserving:

| Area | Assessment |
|---|---|
| `src/content/` | Zero imports from engine or domains — exemplary isolation |
| `src/engine/pipeline.py` | Single integration point for all domain phase imports |
| API route handlers | All entity/state endpoints go through DTO or presenter — no raw domain model |
| 13 / 14 domains | Zero prohibited cross-domain imports |
| 0 domains (except campaigns) | Zero Kernel imports |
| 0 domains | Zero direct `AuthoritativeState` mutations |

---

## Recommended Follow-Up Tickets

| Priority | Action | Finding |
|---|---|---|
| P1 | Inject `TemporalPressureService` into `MemoryUpdatePhase` from pipeline orchestrator; remove `memory`→`time` import | F1 |
| P1 | Move `MovementPlanCache` construction out of `AuthoritativeState.__post_init__`; pass via engine factory | F2 |
| P2 | Add import boundary enforcement test (`test_no_cross_domain_imports.py`) so violations are caught in CI | F1/F2 |
| P2 | Replace `hard_law_monitor` direct `WorldIndexService` import with a query method on `Kernel` | F3 |
| P2 | Remove `GovernorPolicy` from `core/updates.py` TYPE_CHECKING block; use string annotation instead | F2 |

---

## Related Dimensions

- **D09 (System Wiring)** — confirms `pipeline.py` domain imports are all live and intentional.
- **D10 (Test Coverage)** — observability→Kernel tight coupling (F3) means observability integration tests require a full engine; increases test setup cost.
- **D13 (Type Safety)** — the `GovernorPolicy` TYPE_CHECKING import in `core/updates.py` exists because of type annotation needs; proper type separation would eliminate it.
- **D15 (Entity Decision Inspection)** — noted potential raw model exposure at `GET /api/v1/entities/{entity_id}`; this audit confirms all routes go through DTOs (concern was unfounded).
