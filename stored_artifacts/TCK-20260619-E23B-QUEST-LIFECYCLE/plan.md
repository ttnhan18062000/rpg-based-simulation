---
ticket_id: TCK-20260619-E23B-QUEST-LIFECYCLE
phase: plan
date: 2026-06-20
---

# Plan: Quest Lifecycle State Machine + quest_registry

## Overview

Six files change across seven ordered steps. Steps 1-3 are data-model changes with no inter-file dependencies. All must complete before Step 4 (ApplyPath) can compile. Steps 5-6 depend on Step 4. Step 7 (tests) depends on all prior steps.

## Dependency Map

```
Step 1 (quests.py: enum + field)
  └─> Step 2 (state.py: field)
  └─> Step 3 (updates.py: three new fields)
        └─> Step 4 (apply.py: apply logic for new fields)
              └─> Step 5 (services.py: QuestLifecycleService)
                    └─> Step 6 (phase.py: wire tick() + quest_registry_add)
                          └─> Step 7 (tests)
```

## Architecture Decisions (resolved)

- **Option B**: Introduce `QuestOpportunityStatus(str, Enum)` for world-level lifecycle. Do NOT modify existing `QuestStatus(Enum)` — it has ACTIVE/COMPLETED/REWARDED/REWARD_PENDING and is used by the Phase 19 reward delivery pipeline.
- `QuestLifecycleService` goes in `src/domains/world_emergence/services.py` (existing file), called from `WorldEmergencePhase.execute()`.
- Wiring: B1 — `WorldEmergencePhase.execute()` emits `quest_opportunities` into new `StateUpdate.quest_registry_add` field. pipeline.py stays untouched.
- Expiry sweep: sorted key iteration for determinism.

---

## Step 1 — Add `QuestOpportunityStatus` enum and `status` field to `QuestOpportunity`

**File**: `src/core/models/quests.py`

**Changes**:
1. After line 18 (end of `QuestStatus` class), insert new `class QuestOpportunityStatus(str, Enum)` with six members: OFFERED, ACTIVE, PROGRESSED, COMPLETED, FAILED, EXPIRED.
2. On `QuestOpportunity` dataclass (lines 57-73), add one field at the end: `status: QuestOpportunityStatus = QuestOpportunityStatus.OFFERED` (with default so existing constructors work).

**Scope guards**:
- Do NOT touch `QuestStatus` (lines 14-18). Do not change its name, values, or base class.
- Do NOT change `QuestState` or `RewardState`.

**AC covered**: AC-2, AC-3; regression guard for AC-10.

---

## Step 2 — Add `quest_registry` field to `AuthoritativeState`

**File**: `src/core/state.py`

**Changes**:
1. After `recent_world_events` field (line 1053), add: `quest_registry: Dict[str, "QuestOpportunity"] = field(default_factory=dict)`
2. Add `QuestOpportunity` to the TYPE_CHECKING import block (match pattern used for `WorldEvent`).
3. In `to_readonly()`: add `quest_registry=ReadOnlyDict(self.quest_registry)` to the `replace(self, ...)` call alongside other ReadOnlyDict conversions.

**Scope guards**:
- Do NOT modify `__post_init__` (no readonly-mapping wrap needed — only `entities` uses `_readonly_mapping`; other dicts like `resource_nodes`, `buildings` are not wrapped there).
- Do NOT change any existing field definition.

**AC covered**: AC-1.

---

## Step 3 — Add three new fields to `StateUpdate`

**File**: `src/core/updates.py`

**Changes**:
1. After line 864 (`world_events_add` field), add three new fields:
   - `quest_registry_add: List["QuestOpportunity"] = field(default_factory=list)`
   - `quest_registry_remove: List[str] = field(default_factory=list)`
   - `quest_status_updates: Dict[str, "QuestOpportunityStatus"] = field(default_factory=dict)`
2. Add `QuestOpportunity`, `QuestOpportunityStatus` to the TYPE_CHECKING import block.
3. Update `is_noop()`: append `and not self.quest_registry_add and not self.quest_registry_remove and not self.quest_status_updates` to the return expression.
4. Update `merge_many()`: add three accumulators before the loop, extend/update inside the loop, and add three keyword args to the final `return replace(self, ...)` call.

**Scope guards**:
- Do NOT touch any existing field in `StateUpdate`.
- Do NOT modify `pipeline.py`.
- Do NOT change the `merge` method (it delegates to `merge_many`).

**AC covered**: structural prerequisite for AC-4, AC-5, AC-7, AC-8.

---

## Step 4 — Add apply logic for the three new `StateUpdate` fields in `ApplyPath`

**File**: `src/engine/apply.py`

**Changes**:
1. In `apply_generation()`, before the `AuthoritativeState(...)` constructor call, insert:
   ```python
   new_quest_registry = dict(getattr(prior_state, "quest_registry", {}))
   for opp in update.quest_registry_add:
       if opp.id not in new_quest_registry:  # idempotent
           new_quest_registry[opp.id] = opp
   for quest_id in update.quest_registry_remove:
       new_quest_registry.pop(quest_id, None)
   for quest_id, new_status in update.quest_status_updates.items():
       existing = new_quest_registry.get(quest_id)
       if existing is not None:
           new_quest_registry[quest_id] = replace(existing, status=new_status)
   ```
2. Add `quest_registry=new_quest_registry` to the `AuthoritativeState(...)` constructor call.
3. Add imports for `QuestOpportunity`, `QuestOpportunityStatus` from `src.core.models.quests` (check existing import at line 36 from `src.core.quests` re-export shim; add there or as local import if circular risk exists).

**Scope guards**:
- Do NOT modify `_compute_entity_changes`, `_fast_replace_entity`, `apply_partial`, or `apply_passive`.
- The `getattr(..., {})` guard is defensive for legacy state compatibility.

**AC covered**: AC-1 (immutability enforcement), AC-4, AC-5, AC-7, AC-8.

---

## Step 5 — Implement `QuestLifecycleService` in `services.py`

**File**: `src/domains/world_emergence/services.py`

**Changes**: Append new class at the bottom of the file (after `WorldToEntitySignalBridge`):

```python
class QuestLifecycleService:
    """
    World-level quest opportunity lifecycle management.
    Expires OFFERED quests past their expiry_ticks.
    Returns StateUpdate with quest_registry_remove and world_events_add.
    Never mutates state directly. Iterates sorted keys for determinism.
    """

    @staticmethod
    def tick(state: AuthoritativeState) -> StateUpdate:
        from src.core.updates import StateUpdate
        from src.core.models.quests import QuestOpportunityStatus
        # WorldEvent import: match pattern already in services.py

        registry = getattr(state, "quest_registry", {})
        if not registry:
            return StateUpdate()

        to_remove: list[str] = []
        events: list = []

        for quest_id in sorted(registry.keys()):
            opp = registry[quest_id]
            if opp.status in (
                QuestOpportunityStatus.COMPLETED,
                QuestOpportunityStatus.FAILED,
                QuestOpportunityStatus.EXPIRED,
            ):
                to_remove.append(quest_id)
            elif state.tick > opp.expiry_ticks:
                to_remove.append(quest_id)
                # emit expiry event using WorldEvent pattern in services.py
                events.append(_make_quest_expired_event(state.tick, quest_id))

        if not to_remove and not events:
            return StateUpdate()

        return StateUpdate(
            quest_registry_remove=to_remove,
            world_events_add=events,
        )
```

Note: `_make_quest_expired_event` is a module-level helper that constructs a `WorldEvent` with category matching existing QUEST_FAILED or a new QUEST_EXPIRED category — use whichever exists in `WorldEventCategory`. If neither exists, use `WorldEventCategory.SOCIAL` with `subject=quest_id` as a fallback and add a TODO comment. Verify against `schema.py` before implementing.

**Scope guards**:
- Do NOT modify `WorldOpportunityPressureService`, `DynamicQuestSeedService`, `RumorSeedService`, `QuestOpportunityGenerator`, or `WorldToEntitySignalBridge`.
- Service never writes to `state.quest_registry` directly.

**AC covered**: AC-5, AC-6, AC-9.

---

## Step 6 — Wire `QuestLifecycleService` into `WorldEmergencePhase.execute()`

**File**: `src/domains/world_emergence/phase.py`

**Changes**:
1. Add `QuestLifecycleService` to the import from `services.py`.
2. After step 5b (quest_opps construction, lines 60-72), before step 6 (rumor seeds, line 75), insert:
   ```python
   # 5c. Quest lifecycle: expire stale opportunities
   lifecycle_upd = QuestLifecycleService.tick(state)
   if not lifecycle_upd.is_noop():
       update = update.merge(lifecycle_upd)
   ```
3. In the final `return replace(update, ...)` call (lines 122-127), add `quest_registry_add=list(quest_opps)` to the keyword arguments.

**Scope guards**:
- Do NOT touch `pipeline.py`.
- Do NOT change the signature or return type of `execute()`.
- Steps 1-4 of `execute()` are untouched.

**AC covered**: AC-4, AC-5, AC-6.

---

## Step 7 — Tests

**File A** (extend existing): `tests/unit/quest/test_quest_lifecycle.py`

Append new test functions (do NOT modify lines 1-115):
- `test_quest_registry_field_on_authoritative_state` (AC-1)
- `test_quest_opportunity_status_enum_values` (AC-2)
- `test_quest_opportunity_defaults_to_offered` (AC-3)
- `test_quest_expires_after_expiry_ticks` (AC-5)
- `test_quest_not_expired_before_expiry_ticks` (AC-6)
- `test_quest_offered_to_active_transition` (AC-7)
- `test_quest_registry_add_is_idempotent` (AC-8)
- `test_expiry_sweep_deterministic_order` (AC-9)
- `test_entity_quest_status_unaffected_by_e23b` (AC-10)

**File B** (new): `tests/unit/domains/world_emergence/test_quest_registry_wiring.py`
- `test_world_emergence_populates_quest_registry` (AC-4)

**Scope guards**:
- Do NOT modify existing test functions (lines 1-115) in `test_quest_lifecycle.py`.
- Do NOT touch `test_quest_generation.py` — existing constructors omit `status` and will pick up the OFFERED default automatically.

**AC covered**: all 10 ACs.

---

## Acceptance Criteria → Step Mapping

| AC | Step(s) |
|---|---|
| AC-1: `quest_registry` field exists, serializes, immutable | 2, 4, 7A |
| AC-2: `QuestOpportunityStatus` enum with 6 values | 1, 7A |
| AC-3: `QuestOpportunity.status` defaults to OFFERED | 1, 7A |
| AC-4: `WorldEmergencePhase` populates `quest_registry` | 3, 4, 6, 7B |
| AC-5: OFFERED → EXPIRED after expiry_ticks | 5, 6, 7A |
| AC-6: Quest not expired before expiry_ticks | 5, 7A |
| AC-7: OFFERED → ACTIVE transition authoritative | 3, 4, 7A |
| AC-8: `quest_registry_add` is idempotent | 4, 7A |
| AC-9: Expiry sweep deterministic (sorted iteration) | 5, 7A |
| AC-10: `QuestStatus.REWARDED`/`REWARD_PENDING` unaffected | 1 (scope guard), 7A |

## Review Notes (architecture review 2026-06-20)

Verdict: APPROVED with implementation constraints (all violations are implementation-level, not architectural blockers):

- **V1 [CRITICAL]**: In `apply_generation()`, the `AuthoritativeState(...)` constructor call enumerates every field by name. `quest_registry=new_quest_registry` MUST appear explicitly in that call — without it the registry resets to `{}` every tick.
- **V2 [CRITICAL]**: `to_readonly()` wraps every dict with `ReadOnlyDict`. `quest_registry=ReadOnlyDict(self.quest_registry)` MUST be added to the `replace(self, ...)` call in `to_readonly()` or workers receive a mutable reference to the live dict.
- **V3**: `QuestOpportunity` is `frozen=True, slots=True`. Adding `status` field is safe — slots are rebuilt at class definition time. Apply path's custom `replace()` uses `object.__setattr__` which works correctly for slots+frozen.
- **V4**: Terminal-status quests (COMPLETED/FAILED/EXPIRED already in registry) removed silently without WorldEvent — acceptable per scope (only tick-expired OFFERED quests emit events).
- **V5**: In `is_noop()`, move the closing `)` to after the three new `and not self.quest_registry_*` conditions.
- **V6**: In `merge_many()`, use `.extend()` for list fields (`quest_registry_add`, `quest_registry_remove`) and `.update()` for the dict field (`quest_status_updates`).
- **V7**: Ticket AC corrected — `QuestOpportunityStatus.OFFERED` (not `QuestStatus.OFFERED`).

Parity entries affected: WORLD-098, WORLD-099, WORLD-100, WORLD-101, WORLD-102
Mechanics chapters to read: docs/mechanics/05_world_evolution.md, docs/engine/authoritative_mutation_pipeline_contract.md

## Deviations

None. Implementation followed plan exactly. `WorldEventCategory.QUEST_FAILED` was used for expiry events (confirmed present in schema.py).
