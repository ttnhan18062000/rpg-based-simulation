---
ticket_id: TCK-20260619-E23C-QUEST-REWARDS
date: 2026-06-20
status: plan-complete
---

# Implementation Plan: TCK-20260619-E23C-QUEST-REWARDS

## Overview

Extend the existing `QuestRewardPhase` / `QuestResolutionSystem` pipeline stage to handle
`QuestOpportunity` (world-registry) reward delivery in addition to the already-supported
`QuestState` (entity-project) rewards. The reward path is: `QuestRewardPhase.resolve()` →
`QuestResolutionSystem.enforce()` → emits `ResourceTransferIntent(source_kind="QUEST")` →
`_resolve_resource_transactions()` applies gold+XP → `ApplyPath.apply_generation()` commits state.
A `WorldEvent(category=QUEST_COMPLETED)` is emitted alongside the reward intent.

---

## Dependency Map

```
Step 1 (StateUpdate field)
  └─► Step 2 (QuestOpportunityRewardSystem — reads the new field)
        └─► Step 3 (QuestRewardPhase wires Step 2)
              └─► Step 4 (WorldEvent emission inside Step 2)
                    └─► Step 5 (new test file — exercises Steps 1–4)
                          └─► Step 6 (regression run)
                                └─► Step 7 (parity ledger updates)
```

Steps 1–4 are code changes (linear dependency chain). Step 5 can be partially authored in parallel
with Steps 3–4, but requires Steps 1–2 to be importable. Steps 6–7 require all prior steps done.

---

## Step 1 — Add `quest_opportunity_reward_intents` field to `StateUpdate`

### What
Add a new field to `StateUpdate` (and its `EntityUpdate` companion if needed) that carries
`QuestOpportunityRewardIntent` records — each one pairs an `entity_id: int` with a `quest_id: str`.
This is the typed signal that tells the enforce stage "deliver the reward for this
`QuestOpportunity` to this entity."

`QuestOpportunityRewardIntent` is a small dataclass defined in `src/core/updates.py` (alongside
other intent types). It does NOT carry the gold/xp values — those are read from
`state.quest_registry[quest_id].reward_spec` inside the enforce stage.

### Why
Following Option C from the investigation: E23C wires the mechanical reward path; E23D will
populate these intents from hero matching. Tests supply them synthetically.

The field must participate in `StateUpdate.merge()` / `StateUpdate.__add__()` / `is_noop()` so
it behaves consistently with all other list fields.

### Files to change
- `src/core/updates.py`
  - Define `@dataclass(frozen=True) class QuestOpportunityRewardIntent` with fields
    `entity_id: int`, `quest_id: str`.
  - Add `quest_opportunity_reward_intents: List[QuestOpportunityRewardIntent]` to `StateUpdate`
    with `field(default_factory=list)`.
  - Update `StateUpdate.is_noop()` to include the new list.
  - Update `StateUpdate.merge()` / `__add__()` to concatenate the new list (same pattern as
    `resource_transfers` at line 148 and `world_events_add` at line 938).

### Scope guards
- Do NOT add this field to `EntityUpdate` — opportunity rewards are world-level, not per-entity
  update.
- Do NOT modify `ResourceTransferIntent`, `RewardUpdate`, or `InventoryUpdate`.
- Do NOT touch `QuestUpdate` or `QuestState`.

### Verifiable checkpoint
`python3 -c "from src.core.updates import StateUpdate, QuestOpportunityRewardIntent; s = StateUpdate(); assert s.quest_opportunity_reward_intents == []"` passes without import error.

---

## Step 2 — Implement `QuestOpportunityRewardSystem.enforce()`

### What
Create `src/engine/pipeline_phases/quest_opportunity_rewards.py` with class
`QuestOpportunityRewardSystem` and a single static method `enforce(state, update) -> StateUpdate`.

Logic inside `enforce()`:

```
for intent in sorted(update.quest_opportunity_reward_intents, key=lambda i: (i.quest_id, i.entity_id)):
    quest_opp = state.quest_registry.get(intent.quest_id)
    if quest_opp is None:
        continue  # already removed (idempotency guard)

    entity = state.entities.get(intent.entity_id)
    if entity is None:
        continue

    reward_spec = quest_opp.reward_spec  # {"gold": int, "xp": int, "faction_rep": float}
    gold = int(reward_spec.get("gold", 0))
    xp   = int(reward_spec.get("xp", 0))
    # faction_rep silently skipped (Phase 5); debug-log if non-zero

    if gold > 0 or xp > 0:
        reward_intent = ResourceTransferIntent(
            source_id=intent.quest_id,
            source_kind="QUEST",
            gold_delta=gold,
            reward_upd=RewardUpdate(xp_gain=xp),
            transfer_kind="QUEST_REWARD",
            transaction_id=f"quest:{intent.quest_id}:reward",
            group_id=f"quest:{intent.quest_id}:reward",
            is_group_required=True,
        )
        # Append to entity's resource_transfers
        ent_upd = update.entity_updates.get(intent.entity_id, EntityUpdate(entity_id=intent.entity_id))
        ent_upd = replace(ent_upd, resource_transfers=list(ent_upd.resource_transfers) + [reward_intent])
        update = replace(update, entity_updates={**update.entity_updates, intent.entity_id: ent_upd})

    # Emit WorldEvent(category=QUEST_COMPLETED) regardless of whether gold/xp > 0
    event = WorldEvent(
        category=WorldEventCategory.QUEST_COMPLETED,
        subject=intent.quest_id,
        payload={"gold": float(gold), "xp": float(xp), "entity_id": float(intent.entity_id)},
    )
    update = replace(update, world_events_add=list(update.world_events_add) + [event])

    # Mark opportunity as terminal: remove from registry
    # Only remove immediately when reward_spec is empty (diplomatic_errand stub) OR
    # when gold/xp == 0 so no capacity check is needed.
    # When gold > 0, removal is deferred to post-ResourceTransactionPhase
    # (handled in Step 3b below) — mirror the REWARD_PENDING pattern.
    if gold == 0 and xp == 0:
        update = replace(update,
            quest_registry_remove=list(update.quest_registry_remove) + [intent.quest_id])

return update
```

**REWARD_PENDING analogue for opportunity rewards**: When gold or items are involved, the
`ResourceTransactionResolver` may reject delivery (full inventory). In that case the
`quest_opportunity_reward_intents` must be re-emitted on the next tick so the phase retries. This
is achieved by keeping the `QuestOpportunity` in the registry (not removing it) until the
transaction succeeds. The success-side removal is handled in Step 3b.

### Files to change
- `src/engine/pipeline_phases/quest_opportunity_rewards.py` (new file)
  - `QuestOpportunityRewardSystem` class with `enforce()` static method.
  - Imports: `ResourceTransferIntent`, `RewardUpdate`, `EntityUpdate`, `WorldEvent`,
    `WorldEventCategory` from their canonical modules.
  - DO NOT import from `src.engine.quests` (wrong layer for this phase).

### Scope guards
- Do NOT read `entity.strategic.projects` — that is the `QuestState` path.
- Do NOT call `QuestService.mark_rewarded()` — that operates on entity-level `QuestState`.
- Do NOT emit `ResourceTransferIntent` from world emergence or lifecycle phases.
- Do NOT set `xp_reward` (legacy int field on `ResourceTransferIntent`) — use
  `reward_upd=RewardUpdate(xp_gain=...)`.
- DO use `reward_upd=RewardUpdate(xp_gain=xp)` (field at `resources.py:L38`), NOT `xp_reward`.

### Verifiable checkpoint
`from src.engine.pipeline_phases.quest_opportunity_rewards import QuestOpportunityRewardSystem`
imports without error and `enforce(state, StateUpdate())` with an empty state returns the same
`StateUpdate` unchanged.

---

## Step 3 — Wire `QuestOpportunityRewardSystem` into `QuestRewardPhase` and pipeline

### Step 3a — Extend `QuestRewardPhase.resolve()`

`src/engine/pipeline_phases/quests.py` currently calls only `QuestResolutionSystem.enforce()`.
Extend it to also call `QuestOpportunityRewardSystem.enforce()`:

```python
@staticmethod
def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
    update = QuestResolutionSystem.enforce(state, update)   # entity-project quests (unchanged)
    update = QuestOpportunityRewardSystem.enforce(state, update)  # opportunity rewards (new)
    return update
```

Order matters: entity-project rewards first (existing behavior unchanged), then opportunity
rewards. Both operate on the same `StateUpdate` pass; the pipeline stage (`quest_rewards`) already
runs before `resource_transactions` (pipeline.py:L221-L223), so the generated
`ResourceTransferIntent`s are picked up by the conservation resolver.

### Step 3b — Post-transaction opportunity registry removal

After `ResourceTransactionPhase` resolves transactions, successful opportunity reward intents must
trigger `quest_registry_remove`. The cleanest approach is to check transaction results inside
`QuestOpportunityRewardSystem` by inspecting whether the transaction_id appears in
`update.processed_transaction_ids` (or the equivalent resolved flag). However, the existing
pattern from `QuestResolutionSystem` does NOT do this inside the enforce phase — it relies on the
`ResourceTransactionResolver.resolve()` returning `quest_update=QuestUpdate(status_set=REWARDED)`
for entity-level quests.

For opportunity quests, mirror this: extend `ResourceTransactionResolver.resolve()`
(`src/core/conservation.py`) in the `source_kind="QUEST"` branch to optionally emit a
`quest_opportunity_registry_remove: Optional[str]` signal, OR handle removal in a dedicated
post-transaction cleanup phase.

**Simpler approach (preferred):** Add a step in `QuestRewardPhase.resolve()` that runs AFTER
`QuestResolutionSystem.enforce()` to scan `update.entity_updates[*].resource_transfers` for
already-committed `transaction_id`s that are in `state.processed_transaction_ids` — those
represent previously-accepted opportunity rewards that were not removed. Emit
`quest_registry_remove` for them.

**Implementation**: Add a private helper
`QuestOpportunityRewardSystem._emit_terminal_removals(state, update)` that:
1. Iterates `state.quest_registry`.
2. For each `QuestOpportunity` whose `transaction_id` (`f"quest:{q_id}:reward"`) is in
   `state.processed_transaction_ids`, appends `q_id` to `quest_registry_remove`.
3. Returns updated `StateUpdate`.

Call this helper at the START of `QuestOpportunityRewardSystem.enforce()` before processing new
intents.

### Files to change
- `src/engine/pipeline_phases/quests.py`
  - Import `QuestOpportunityRewardSystem`.
  - Extend `QuestRewardPhase.resolve()` as shown above.
- `src/engine/pipeline_phases/quest_opportunity_rewards.py` (from Step 2)
  - Add `_emit_terminal_removals()` helper.

### Scope guards
- Do NOT add a new pipeline phase entry in `pipeline.py` — the existing `quest_rewards` phase
  slot at line 221 is sufficient.
- Do NOT modify `_resolve_quest_rewards()` in `pipeline.py`.
- Do NOT modify `ResourceTransactionResolver` in `conservation.py` — the existing
  `source_kind="QUEST"` path already handles conservation correctly.

### Verifiable checkpoint
With a synthetic `StateUpdate` carrying one `QuestOpportunityRewardIntent`, calling
`QuestRewardPhase.resolve(state, update)` produces an updated `StateUpdate` where
`entity_updates[entity_id].resource_transfers` contains exactly one intent with
`source_kind="QUEST"` and `transaction_id=f"quest:{quest_id}:reward"`.

---

## Step 4 — `WorldEvent(category=QUEST_COMPLETED)` emission (integrated in Step 2)

### What
The `WorldEvent` emission is already included in Step 2's `enforce()` logic. This step documents
the field mapping and confirms nothing else is needed.

`WorldEvent` schema (`src/domains/world_emergence/schema.py:L34-L40`):
- `category: WorldEventCategory` → `WorldEventCategory.QUEST_COMPLETED` (already defined, L21)
- `subject: Optional[str]` → `quest_id`
- `payload: Dict[str, float]` → `{"gold": float(gold), "xp": float(xp), "entity_id": float(entity_id)}`

The event is appended to `update.world_events_add` (list field on `StateUpdate`, L865). This is
picked up by `ApplyPath.apply_generation()` which writes it to `new_state.world_events`.

The string `"quest_completed"` used in `src/domains/campaigns/` is a SEPARATE campaign-narrative
event type. Do NOT change campaign code.

### Files to change
- None beyond Step 2 (the emission is part of `QuestOpportunityRewardSystem.enforce()`).

### Scope guards
- Do NOT add a free-form `event_type: str` field to `WorldEvent`.
- Do NOT modify campaign classifier/runner — they use a separate string-keyed event system.

### Verifiable checkpoint
`any(e.category == WorldEventCategory.QUEST_COMPLETED for e in refined.world_events_add)` is
`True` after `QuestRewardPhase.resolve()` processes a non-empty intent list.

---

## Step 5 — Write `tests/unit/quest/test_quest_rewards.py`

### What
New test file with 7 test functions + 3 anti-drift guards. All tests use synthetic
`QuestOpportunityRewardIntent` (no E23D dependency). Each test is independently runnable.

### Test functions (from test_plan.md)

| Test | AC mapped | What it guards |
|---|---|---|
| `test_quest_completion_adds_gold_and_xp` | AC-1 | Gold delta + XP via RewardUpdate applied end-to-end |
| `test_quest_completion_is_authoritative` | AC-2 | Intent in resource_transfers, not direct EntityUpdate mutation |
| `test_quest_completed_event_emitted` | AC-3 | `WorldEvent(category=QUEST_COMPLETED)` in world_events_add |
| `test_diplomatic_errand_no_reward` | AC-4 | `reward_spec={}` → no ResourceTransferIntent, quest removed |
| `test_full_inventory_defers_opportunity_reward` | AC-5 | Full inventory → quest stays in registry, gold not granted |
| `test_reward_idempotency_via_transaction_id` | AC-6 | Same transaction_id applied twice → reward once |
| `test_reward_spec_faction_rep_silently_skipped` | AC-7 | `faction_rep` key ignored, no exception |

### Anti-drift guards

| Guard | What it catches |
|---|---|
| `test_no_direct_entity_mutation_from_quest_opportunity` | `QuestLifecycleService.tick()` must not emit ResourceTransferIntent |
| `test_quest_opportunity_status_enum_not_confused_with_quest_status` | `QuestOpportunityStatus` ≠ `QuestStatus` (type and value) |
| `test_entity_project_quest_state_unaffected_by_opportunity_reward` | Opportunity reward does not touch entity.strategic.projects |

### Setup pattern (used by AC-1, AC-2, AC-3, AC-4, AC-6, AC-7)

```python
quest_opp = QuestOpportunity(
    quest_id="q-001",
    kind="bounty",
    reward_spec={"gold": 200, "xp": 500},
    status=QuestOpportunityStatus.COMPLETED,
)
state = make_minimal_state(entities={entity_id: hero_entity}, quest_registry={"q-001": quest_opp})
update = StateUpdate(
    quest_opportunity_reward_intents=[
        QuestOpportunityRewardIntent(entity_id=entity_id, quest_id="q-001")
    ]
)
refined = QuestRewardPhase.resolve(state, update)
new_state = ApplyPath.apply_generation(state, refined)
```

### Files to change
- `tests/unit/quest/test_quest_rewards.py` (new file)
- No changes to existing test files.

### Scope guards
- Do NOT modify `tests/unit/quest/test_quest_transactions.py` (must stay green as-is).
- Do NOT modify `tests/unit/quest/test_quest_lifecycle.py` (E23B tests).
- Helper factories (`make_minimal_state`, `make_hero_entity`) may be extracted to
  `tests/unit/quest/conftest.py` if one already exists; otherwise inline in the new file.

### Verifiable checkpoint
`pytest tests/unit/quest/test_quest_rewards.py -x -v` — all 10 tests pass.

---

## Step 6 — Run regression suites

### Commands (in order)

```bash
# 1. New tests
pytest tests/unit/quest/test_quest_rewards.py -x -v

# 2. Full quest domain regression
pytest tests/unit/quest/ -x -v

# 3. Conservation path regression
pytest tests/rpg/test_resource_conservation_v2.py -x -v

# 4. World emergence regression (E23B wiring)
pytest tests/unit/domains/world_emergence/ -x -v

# 5. Full non-slow suite
pytest -m "not slow" -x
```

### Scope guards
- Do NOT run `pytest tests/` (full suite) — too broad per project testing rule.
- Fix any failures before proceeding to Step 7.

### Verifiable checkpoint
All five commands exit 0 with no unexpected failures.

---

## Step 7 — Parity ledger updates

### Entries to update

**`docs/parity_ledger/progression.yaml`**

1. **PROG-004** (line 32, currently `legacy_verified`, no `test_path`):
   - Change `status` → `verified`
   - Set `v2_evidence` to reference `QuestOpportunityRewardSystem.enforce()` in
     `src/engine/pipeline_phases/quest_opportunity_rewards.py`
   - Set `test_path` → `tests/unit/quest/test_quest_rewards.py::test_quest_completion_adds_gold_and_xp`

2. **PROG-064** (line 654, currently `verified`):
   - Update `v2_evidence` to also cite `WorldEvent(category=QUEST_COMPLETED)` emission from
     `QuestOpportunityRewardSystem.enforce()` as the traceability path for quest opportunity
     rewards.
   - `test_path` → add `tests/unit/quest/test_quest_rewards.py::test_quest_completed_event_emitted`

3. **PROG-109** (new entry — does not yet exist):
   - Add at bottom of `progression.yaml`:
   ```yaml
   - id: PROG-109
     text: "Quest opportunity reward (gold + XP) is applied through the authoritative resource
       transfer path (QuestOpportunityRewardSystem → ResourceTransferIntent → ResourceTransactionResolver),
       not via direct inventory mutation."
     status: verified
     priority: P1
     v2_evidence: "src/engine/pipeline_phases/quest_opportunity_rewards.py QuestOpportunityRewardSystem.enforce()"
     test_path: "tests/unit/quest/test_quest_rewards.py::test_quest_completion_is_authoritative"
     divergence_note: ""
   ```

**`docs/parity_ledger/town_resource.yaml`**

4. **TOWN-154** (line 1605):
   - Confirm `v2_evidence` field is current. Update to include reference to the new enforce
     stage so the entry reflects that the reward path goes through `QuestRewardPhase`, not a
     standalone service.
   - No status change needed if already `verified`; only update `v2_evidence` if stale.

### Files to change
- `docs/parity_ledger/progression.yaml`
- `docs/parity_ledger/town_resource.yaml`

### Verifiable checkpoint
`python3 -c "import yaml; data = yaml.safe_load(open('docs/parity_ledger/progression.yaml')); ids = [e['id'] for e in data['entries']]; assert 'PROG-109' in ids and 'PROG-004' in ids and 'PROG-064' in ids"` passes (adjust key path to match actual YAML schema).

---

## Acceptance Criteria → Step Mapping

| Acceptance Criterion | Covered By |
|---|---|
| Completing entity's gold increases by `reward_spec["gold"]` | Step 2 (ResourceTransferIntent), Step 5 AC-1 |
| XP increases by `reward_spec["xp"]` via `RewardUpdate.xp_gain` | Step 2 (reward_upd field), Step 5 AC-1 |
| `quest_completed` WorldEvent appears in event log | Step 4 (integrated in Step 2), Step 5 AC-3 |
| `test_quest_completion_adds_gold_and_xp` passes | Step 5, Step 6 |
| `test_quest_completion_is_authoritative` passes | Step 5, Step 6 |
| `reward_spec={}` (diplomatic_errand) → no reward, clean transition | Step 2 guard, Step 5 AC-4 |
| Idempotent reward delivery (same transaction_id) | Step 2 (transaction_id pattern), Step 5 AC-6 |
| Parity ledger entries updated | Step 7 |

---

## Scope Guards (Global)

The following must NOT be touched by this ticket:

- `src/engine/quests.py` — `QuestResolutionSystem.enforce()` handles entity-project quests and
  must not be modified.
- `src/core/conservation.py` — `ResourceTransactionResolver` already handles `source_kind="QUEST"`
  correctly; do not add opportunity-specific branches.
- `src/engine/pipeline.py` — the `quest_rewards` phase slot at line 221 is sufficient; no new
  phase entries needed.
- `src/domains/campaigns/` — campaign string event types are separate from authoritative
  `WorldEvent`; do not conflate.
- `src/core/models/quests.py` — `QuestOpportunity` dataclass shape is frozen for E23C; E23D adds
  `assigned_entity_id`.
- `QuestLifecycleService` (`src/domains/world_emergence/services.py`) — must not emit
  `ResourceTransferIntent`; guarded by anti-drift test.
- `QuestStatus` (entity-project enum) — used only by `QuestResolutionSystem`; opportunity rewards
  use `QuestOpportunityStatus`.
- Faction reputation fields in `reward_spec` — silently skipped (Phase 5).
- Multi-entity shared rewards — out of scope (Phase 4).

---

## Deviations

### Phase graph dirty-set bypass (not in plan)

The plan did not anticipate that `resource_transactions` would be skipped when quest_opportunity_reward_intents are the only signal in the incoming `StateUpdate`.

Root cause: The pipeline refreshes the dirty_set at line 219 (before `quest_rewards`), using the update state before `quest_rewards` generates entity_updates. So `resource_transactions`' dirty-set check sees a stale clean dirty_set and skips entity 1 entirely. The `ResourceTransferIntent` then remains unconsumed, and `RewardUpdate.xp_gain` is never processed by the conservation resolver or evolution system.

Fix: Added a phase-specific trigger in `src/engine/phase_graph.py` so both `quest_rewards` and `resource_transactions` bypass the dirty-set gate when `update.quest_opportunity_reward_intents` is non-empty. This mirrors how `must_run_every_tick` works but is scoped to the specific signal that drives these two phases.

The fix does not touch `pipeline.py` or `conservation.py`, consistent with the scope guards.
