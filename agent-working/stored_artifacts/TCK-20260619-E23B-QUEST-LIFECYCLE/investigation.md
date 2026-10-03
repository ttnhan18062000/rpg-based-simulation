---
ticket_id: TCK-20260619-E23B-QUEST-LIFECYCLE
phase: investigation
date: 2026-06-20
---

# Investigation: Quest Lifecycle State Machine + quest_registry

---

## Current Behavior (file:line refs)

### QuestStatus — existing int enum (CONFLICTS with ticket spec)

`src/core/models/quests.py:14-18` defines:
```python
class QuestStatus(Enum):
    ACTIVE = 1
    COMPLETED = 2
    REWARDED = 3
    REWARD_PENDING = 4
```
This is an `int`-valued `Enum`, not `str`. The ticket specifies converting to `class QuestStatus(str, Enum)` with six new members: `OFFERED`, `ACTIVE`, `PROGRESSED`, `COMPLETED`, `FAILED`, `EXPIRED`. **This is a breaking change to existing uses of `REWARDED` and `REWARD_PENDING`**, which are consumed by `QuestService` (L40), `QuestResolutionSystem.enforce()` (`src/engine/quests.py:195-217`), `QuestPatch.apply()` (`src/engine/patches.py:483-499`), and all existing tests in `tests/unit/quest/test_quest_lifecycle.py`.

**Decision required** — see Open Questions.

### QuestOpportunity — already added by E23A

`src/core/models/quests.py:57-73` contains the complete `QuestOpportunity` frozen dataclass (no `status` field yet). It has `expiry_ticks: int` but no lifecycle state. E23A is DONE and this is the starting point for E23B.

### AuthoritativeState — no quest_registry field

`src/core/state.py:984-1053` (`AuthoritativeState`) has no `quest_registry` field. It does have many `Dict[..., ...]` fields with `default_factory=dict` (e.g. `resource_nodes` L999, `buildings` L1003, `groups` L1028). The class uses `frozen=True` (L984), but mutable dict fields are allowed — they are wrapped by `_readonly_mapping()` on `__post_init__` (L1073). A `quest_registry: Dict[str, QuestOpportunity]` field follows the exact same pattern and is safe to add.

### WorldEmergencePhase — result is discarded in pipeline

`src/domains/world_emergence/phase.py:122-127`: `execute()` returns `(StateUpdate, WorldEmergenceResult)`. The `WorldEmergenceResult` carries `quest_opportunities: Tuple[QuestOpportunity, ...]` (schema.py:119).

`src/engine/pipeline.py:213`:
```python
update = run_phase("world_emergence", update, lambda u: WorldEmergencePhase.execute(state, u, recent_world_events)[0], "ENABLE_WORLD_EMERGENCE")
```
The `[0]` index discards the `WorldEmergenceResult` entirely. **The `quest_opportunities` produced by E23A never reach `quest_registry`**. Wiring them through requires either:
  (a) Capturing `result` from `WorldEmergencePhase.execute()` and converting `quest_opportunities` into `StateUpdate` fields (e.g. `quest_registry_add`), or
  (b) Having `WorldEmergencePhase.execute()` directly emit `quest_registry_add` entries into the returned `StateUpdate`.

Option (b) is cleaner and avoids touching `pipeline.py`'s `run_phase` lambda shape.

### StateUpdate — no quest_registry_add or quest_status_updates fields

`src/core/updates.py:820-864` (`StateUpdate`) has no fields for:
- Adding entries to `quest_registry`
- Updating `QuestOpportunity.status`
- Expiring quests

These must be added.

### QuestUpdate / QuestUpdate import chain

`src/core/update_models/quests.py:6` imports `QuestStatus` from `src.core.quests` under `TYPE_CHECKING`. `src/core/quests.py` is a thin re-export shim (`src/core/quests.py:1-3`) that imports from `src.core.models.quests`. Any rename of `QuestStatus` propagates through this chain to `QuestUpdate`, `QuestPatch`, `QuestResolutionSystem`, and `QuestService`.

### QuestService — ACTIVE/COMPLETED/REWARD_PENDING/REWARDED references

`src/quests/service.py:17,40`: guards use `QuestStatus.ACTIVE`, `QuestStatus.COMPLETED`, `QuestStatus.REWARD_PENDING`. These four names must be preserved or the guards must be updated.

### QuestResolutionSystem.enforce — REWARD_PENDING transition

`src/engine/quests.py:195-217`: transitions ACTIVE → COMPLETED → REWARD_PENDING → REWARDED. `REWARD_PENDING` and `REWARDED` are internal reward delivery states used by the Phase 19 `quest_rewards` pipeline phase. They are **separate** from the world-level lifecycle states `OFFERED/ACTIVE/PROGRESSED/COMPLETED/FAILED/EXPIRED` that this ticket introduces on `QuestOpportunity`.

### Existing tests — will break on QuestStatus change

`tests/unit/quest/test_quest_lifecycle.py:74`: asserts `new_quest.quest_status == QuestStatus.REWARDED`. `tests/unit/quest/test_quest_lifecycle.py:114`: asserts `QuestStatus.REWARDED`. Any removal of `REWARDED` or `REWARD_PENDING` from `QuestStatus` breaks these tests.

### QuestLifecycleService — does not exist

`src/domains/world_emergence/` contains: `__init__.py`, `aggregators.py`, `models.py`, `phase.py`, `schema.py`, `services.py`. No `QuestLifecycleService` exists anywhere in the codebase.

---

## Mechanics / Engine Constraints

- **Immutability Law** (`docs/core/state.md`): All state components are `frozen=True`. `quest_registry` must be added as a `Dict[str, QuestOpportunity]` field with `default_factory=dict` — same pattern as `resource_nodes`, `buildings`, `groups`.
- **Singular Bottleneck Law** (`docs/engine/authoritative_pipeline.md`): All mutations to `quest_registry` must flow through a `StateUpdate` → `AuthoritativeApplyPipeline` → `ApplyPath`. No system may directly assign to `state.quest_registry`.
- **Pipeline Phase 18** (`world_emergence`): The correct insertion point for registering new `QuestOpportunity` objects is at the tail of Phase 18, not Phase 19 (quest_rewards). Expiry sweeps are a world-state maintenance concern — also Phase 18 or a new Phase 18.5. Adding a new phase between 18 and 19 is valid per the pipeline doc's open slot between them.
- **Durable State Rule**: `quest_registry` survives tick boundaries — it must have a typed model, stable location, defined lifecycle, and tests. Completed/expired quests are removed from registry and recorded via `world_events_add` (already in `StateUpdate:864`).
- **Determinism**: Expiry sweeps must iterate `quest_registry` in sorted key order.

---

## Parity Ledger Overlap

| ID | File | Status | Relevance |
|---|---|---|---|
| WORLD-098 | `world_dynamics.yaml` | `verified` | QuestOpportunity generation (E23A); no change needed for E23B itself |
| WORLD-099 | `world_dynamics.yaml` | `verified` | Determinism of QuestOpportunity.id (E23A); no change needed for E23B itself |
| PROG-084 | `progression.yaml` | `verified` | Phase 14 objective reward — text says "active skills require legality checks" (misleadingly named); the `quest_rewards` phase (Phase 19) already handles reward delivery; **no change needed** |

**New parity entries required for E23B** (none exist yet):
- `WORLD-100`: `quest_registry` field on `AuthoritativeState` — OFFERED quests persist across ticks until accepted or expired.
- `WORLD-101`: `QuestOpportunity` transitions `OFFERED → EXPIRED` when `state.tick > expiry_ticks` via authoritative expiry sweep.
- `WORLD-102`: `QuestOpportunity` in `quest_registry` with `status=OFFERED` is created deterministically when `WorldEmergencePhase` produces `quest_opportunities` — keyed by `QuestOpportunity.id`.

---

## Prior Work

### E23A (DONE — 2026-06-20)
Delivered `QuestOpportunity` dataclass (`src/core/models/quests.py:57-73`) and `QuestOpportunityGenerator` in `src/domains/world_emergence/services.py`. Wired step 5b into `WorldEmergencePhase.execute()`. Added `quest_opportunities: Tuple[QuestOpportunity, ...]` to `WorldEmergenceResult`. The generator output is in `result.quest_opportunities` but is never consumed by the apply path — **E23B must close this gap**.

### TCK-20260612-QUESTS-CONTRACT
Confirmed `QuestStatus` has ACTIVE(1)/COMPLETED(2)/REWARDED(3)/REWARD_PENDING(4) and no expiry logic. The existing reward delivery pipeline is Phase 19 and `QuestService`/`QuestResolutionSystem` handle the `ACTIVE → COMPLETED → REWARD_PENDING → REWARDED` machine for `QuestState` (entity-level). E23B introduces a **separate** world-level lifecycle on `QuestOpportunity` — these are two distinct state machines on two distinct types.

### TCK-20260427-QUEST-IDENTITY
Quest state reversion issue — confirms that quest state stored in `entity.strategic.projects` (as `QuestState`) must be mutated only through authoritative path. The same constraint applies to `quest_registry`.

### docs/audits/D06_longrun_health.md — F4: Quest system never activates
Root cause: no world-level registry and no `OFFERED` state. E23B directly addresses F4. After this ticket `quest_registry` exists and `WorldEmergencePhase` populates it.

---

## Risks and Open Questions

### DECISION REQUIRED: QuestStatus namespace collision

The ticket spec calls for `QuestStatus(str, Enum)` with `OFFERED/ACTIVE/PROGRESSED/COMPLETED/FAILED/EXPIRED`. The **existing** `QuestStatus(Enum)` has `ACTIVE/COMPLETED/REWARDED/REWARD_PENDING` — used by:
- `src/quests/service.py:17,40`
- `src/engine/quests.py:195,196,217`
- `src/engine/patches.py:497`
- `tests/unit/quest/test_quest_lifecycle.py:74,114`
- `src/core/update_models/quests.py:6`

**Option A — Extend**: Add `OFFERED`, `PROGRESSED`, `FAILED`, `EXPIRED` to the existing `QuestStatus` and convert to `str` enum. Preserve `REWARDED` and `REWARD_PENDING`. This is the least-invasive path and keeps both state machines using one enum. Risk: enum conflates two concerns (world-level opportunity lifecycle vs entity-level reward delivery).

**Option B — New enum**: Introduce `QuestOpportunityStatus(str, Enum)` for the world-level lifecycle (`OFFERED/ACTIVE/PROGRESSED/COMPLETED/FAILED/EXPIRED`) and leave `QuestStatus` unchanged. Add `status: QuestOpportunityStatus = QuestOpportunityStatus.OFFERED` to `QuestOpportunity`. This is architecturally cleaner and breaks no existing code. Risk: naming diverges from ticket spec.

**Recommendation**: Option B. The two state machines are on different types (`QuestOpportunity` vs `QuestState`). Option A would conflate them. The ticket note "coordinate with E23A implementer" on adding `status` to `QuestOpportunity` supports Option B naming.

### DECISION REQUIRED: Where does QuestLifecycleService live?

Ticket says `src/domains/world_emergence/` or `src/systems/`. Given that `WorldEmergencePhase` is Phase 18 and already handles world-level pressure signals, adding `QuestLifecycleService` to `src/domains/world_emergence/services.py` is consistent. However, the expiry sweep (`tick()`) would need to be called from inside `WorldEmergencePhase.execute()` — which already returns a `StateUpdate` that could carry `quest_registry_remove` entries. **Preferred**: add to `src/domains/world_emergence/services.py`, wire into `WorldEmergencePhase.execute()` step 6.5 (after rumor seeds, before metrics).

### DECISION REQUIRED: How to wire quest_opportunities → quest_registry

Two sub-options for E23B:
- **B1**: Modify `WorldEmergencePhase.execute()` to append `quest_opportunities` from step 5b into `StateUpdate.quest_registry_add` (new field). Apply path handles insertion to `state.quest_registry`.
- **B2**: Modify `pipeline.py:213` to capture the `WorldEmergenceResult` and convert it before passing to `run_phase`. This breaks the `run_phase` lambda contract.

**B1 is correct**: keep `pipeline.py` untouched; let `WorldEmergencePhase` own the conversion of typed outputs into `StateUpdate` fields.

### Anti-drift: `QuestUpdate` import chain

`src/core/update_models/quests.py:6` imports `QuestStatus` under `TYPE_CHECKING`. If Option B is chosen, this import is unaffected. If Option A is chosen, the import and all callers must be audited.

### Anti-drift: `quest_registry` ReadOnlyDict wrapping

`AuthoritativeState.__post_init__` (state.py:1055-1079) wraps `self.entities` via `_readonly_mapping()`. The `quest_registry` dict should follow the same pattern — wrap in `__post_init__` if the project enforces read-only access on dict fields. Check whether `resource_nodes` is similarly wrapped; if not, `quest_registry` need not be.

---

## Anti-Drift Hazards

1. **Do not remove `REWARDED`/`REWARD_PENDING` from existing `QuestStatus`** — the Phase 19 reward delivery pipeline (`QuestResolutionSystem.enforce`, `QuestPatch.apply`, `QuestService.mark_rewarded`) depends on them. Breaking these silently disables reward delivery.
2. **Do not mutate `state.quest_registry` directly** — must go through `StateUpdate` → `ApplyPath`. Any direct `state.quest_registry[id] = ...` is an immutability law violation.
3. **Do not add `quest_opportunities` consumption to pipeline.py via `[0]`/`[1]` indexing** — if pipeline phase lambda shape changes, the whole phase 18 wiring breaks. Keep `WorldEmergencePhase` self-contained.
4. **Expiry sweep must use sorted key iteration** — `for quest_id in sorted(state.quest_registry.keys())` — to preserve determinism.
5. **`quest_registry` must not store COMPLETED/FAILED/EXPIRED quests** — these are removed and recorded via `world_events_add` (StateUpdate field already exists at `updates.py:864`). Retention in registry would make the collection unbounded.
6. **`QuestOpportunity` lacks a `status` field** — E23B must add it (with Option B: `status: QuestOpportunityStatus = QuestOpportunityStatus.OFFERED`). This is a breaking change to the E23A dataclass; tests in `test_quest_generation.py` may need updating if they construct `QuestOpportunity` without `status`.
