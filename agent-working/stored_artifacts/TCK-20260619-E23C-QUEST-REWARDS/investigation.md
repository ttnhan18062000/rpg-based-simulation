---
ticket_id: TCK-20260619-E23C-QUEST-REWARDS
date: 2026-06-20
status: investigation-complete
---

# Investigation: TCK-20260619-E23C-QUEST-REWARDS

## Current Behavior (file:line refs)

### What already exists (prior static quest reward path)

`QuestResolutionSystem.enforce()` (`src/engine/quests.py:L154`) is the authoritative enforcement stage
for entity-level quests stored as `QuestState` in `entity.strategic.projects`.

Key sequence in `enforce()` (`src/engine/quests.py:L193-L230`):
1. Detects when a `QuestUpdate` causes a `ACTIVE → COMPLETED` transition (`is_newly_completed`, line 195).
2. Also handles `REWARD_PENDING` retry (`is_retry_pending`, line 196).
3. Emits a `ResourceTransferIntent(source_kind="QUEST", ...)` with `gold_delta`, `items_add`, and
   `reward_upd=RewardUpdate(xp_gain=...)` (`src/engine/quests.py:L203-L213`).
4. Transitions quest to `REWARD_PENDING` (`src/engine/quests.py:L217`).

The `ResourceTransactionResolver.resolve()` (`src/core/conservation.py:L237-L252`) handles
`source_kind="QUEST"`:
- Checks in-tick reservations and item capacity.
- On success: returns `TransactionResult(accepted=True, inventory_update=..., identity_update=...,
  reward_update=..., quest_update=QuestUpdate(status_set=QuestStatus.REWARDED))`.
- Failing capacity → `accepted=False`, quest stays `REWARD_PENDING`.

XP flows through `reward_upd=RewardUpdate(xp_gain=int)` on the `ResourceTransferIntent`
(`src/core/update_models/resources.py:L38`). `RewardUpdate.xp_gain` (`src/core/updates.py:L460`) is
applied by the reward patch path in `ApplyPath._apply_entity_update_to_dict()`.

Gold flows through `ResourceTransferIntent.gold_delta` resolved to
`InventoryUpdate(gold_delta=...)` in `ResourceTransactionResolver`.

### What does NOT yet exist for `QuestOpportunity` rewards

`QuestOpportunity` (`src/core/models/quests.py:L65`) is a world-level object stored in
`AuthoritativeState.quest_registry` (added in E23B). It has `reward_spec: Dict[str, Any]`
(`src/core/models/quests.py:L78`) rather than a typed `RewardState`.

The existing `QuestResolutionSystem.enforce()` only operates on `QuestState` objects inside
`entity.strategic.projects`. There is no wiring to:
- Read `QuestOpportunity.reward_spec` on opportunity completion.
- Convert `reward_spec["gold"]`/`reward_spec["xp"]` into a `ResourceTransferIntent`.
- Emit a `WorldEvent(category=QUEST_COMPLETED, ...)` into `StateUpdate.world_events_add`.
- Remove a completed `QuestOpportunity` from `quest_registry`.

### `WorldEvent.QUEST_COMPLETED` category

`WorldEventCategory.QUEST_COMPLETED` is already defined (`src/domains/world_emergence/schema.py:L21`).
`WorldEvent` has `subject: Optional[str]` and `payload: Dict[str, float]`
(`src/domains/world_emergence/schema.py:L34-L40`). There is no `str` event_type field;
the ticket AC says `event_type="quest_completed"` — this must be reconciled. See Open Questions.

### `quest_completed` string usage

The string `"quest_completed"` is used in `src/domains/campaigns/` (runner, classifier,
behavior_change) as a narrative/campaign event type, not a typed `WorldEvent`. These are separate
from the authoritative `WorldEvent` schema.

### `QuestStatus` enum mismatch (critical)

There are TWO separate status enums (established in E23B, implementation note):
- `QuestStatus` (`src/core/quests.py`, `src/core/models/quests.py:L14`) — used on `QuestState`
  entity projects: ACTIVE(1)/COMPLETED(2)/REWARDED(3)/REWARD_PENDING(4).
- `QuestOpportunityStatus` (`src/core/models/quests.py:L20`) — used on `QuestOpportunity` in
  world registry: OFFERED/ACTIVE/PROGRESSED/COMPLETED/FAILED/EXPIRED.

The ticket AC refers to `QuestStatusUpdate(new_status=COMPLETED)` in the apply path. This refers to
`QuestOpportunityStatus.COMPLETED` on the registry side, not `QuestStatus.COMPLETED` on the entity
project side. The implementation must not conflate the two.

### `StateUpdate` quest registry fields (from E23B)

`src/core/updates.py:L865-L938`:
- `quest_registry_add: List[QuestOpportunity]`
- `quest_registry_remove: List[str]` (quest IDs)
- `quest_status_updates: Dict[str, QuestOpportunityStatus]`

`ApplyPath.apply_generation()` (`src/engine/apply.py:L316-L325`) already applies
`quest_status_updates` and `quest_registry_remove` to `new_quest_registry`.

### `diplomatic_errand` stub

`QuestOpportunity.kind == "diplomatic_errand"` with `reward_spec={}` → no reward, just transition
to COMPLETED. The ticket explicitly calls this a Phase 5 stub — no items/gold/xp are applied.

---

## Mechanics / Engine Constraints

### Conservation Law (Mechanics Bible Chapter 03)

Gold for quest rewards is sourced from a "world treasury" (not created). The existing
`ResourceTransferIntent(source_kind="QUEST", source_id=q_id, gold_delta=...)` pattern already
satisfies this — the `"QUEST"` source_kind path in `ResourceTransactionResolver` does NOT require a
physical node to exist. Gold conservation is tracked at the `global_resources` level via
`StateUpdate.resource_updates`, not validated as a node depletion. The existing static quest reward
path (`src/engine/quests.py:L203`) uses the same source_kind and does not provide a treasury
source_id for gold — this is intentional for quest rewards (world-injected gold).

### XP bypass of conservation

XP is not a conserved resource. `RewardUpdate.xp_gain` flows through
`identity_update=IdentityUpdate(evolution_points_delta=...)` in `ResourceTransactionResolver`
(`src/core/conservation.py:L249`). No capacity check applies to XP. This path already exists and is
used by the static quest reward.

### Authoritative pipeline: enforcement stage

`QuestResolutionSystem.enforce()` is called from `AuthoritativeApplyPipeline.refine()` (found in
`src/engine/pipeline.py`). This is the correct injection point. The new opportunity-reward logic
must either extend `enforce()` or be placed in the same pipeline stage. Do NOT emit rewards from
`WorldEmergencePhase` or `QuestLifecycleService`.

### Idempotency

`ResourceTransactionResolver.resolve()` checks `processed_transaction_ids`
(`src/core/conservation.py:L58`). The transaction_id must be stable: `f"quest:{quest_id}:reward"`
(same pattern as line 210 in `src/engine/quests.py`) is idempotent across retries.

### `REWARD_PENDING` retry

The existing `enforce()` re-emits the reward intent if `project.quest_status == REWARD_PENDING`
(line 196). The same pattern must apply to `QuestOpportunity` in the registry when the transition
record indicates reward delivery failed (e.g., `QuestOpportunityStatus.COMPLETED` but reward not
yet acknowledged as terminal).

---

## Parity Ledger Overlap

### progression.yaml entries requiring update after this ticket

| ID | Current status | Why this ticket affects it |
|---|---|---|
| PROG-004 | `legacy_verified` (no test_path) | "Combat and progression rewards update gold, XP… through authoritative updates." Quest opportunity rewards are a new authoritative reward path. Upgrade to `verified` with test_path pointing to new test. |
| PROG-064 | `verified` | "XP/reward grant is authoritative and traceable to event." New `quest_completed` WorldEvent provides traceability. Update v2_evidence to include `quest_completed` event path. |

### town_resource.yaml entries requiring update after this ticket

| ID | Current status | Why this ticket affects it |
|---|---|---|
| TOWN-154 | `verified` | "No standalone gameplay system can complete quests without quest lifecycle validation." New reward path must go through enforce() not direct mutation. Confirm v2_evidence is current. |

### Missing entries to add after implementation

No existing parity ledger entry covers:
- `QuestOpportunity.reward_spec` → `ResourceTransferIntent` translation.
- `quest_completed` `WorldEvent` emission on opportunity reward.

Add to `progression.yaml`:
- New entry: `PROG-109` — "Quest opportunity reward (gold + XP) is applied through the authoritative
  resource transfer path, not direct inventory mutation."

---

## Prior Work

### TCK-20260619-E23A-QUEST-OPPORTUNITY (DONE)
Established `QuestOpportunity` dataclass with `reward_spec: Dict[str, Any]`,
`QuestOpportunityStatus` enum. Foundation for E23C's reward_spec read.

### TCK-20260619-E23B-QUEST-LIFECYCLE (DONE)
Added `quest_registry` to `AuthoritativeState`, `quest_status_updates` / `quest_registry_remove` to
`StateUpdate`, `QuestLifecycleService.tick()`, and all apply-path wiring for registry mutations.
Confirmed: `quest_registry_remove` is available and functional in apply.py.

### TCK-20260428-RESOURCE-QUEST-TRANSACTIONS (historical, referenced in context)
Established `REWARD_PENDING` status and atomic resource transfer for entity-level `QuestState`
rewards. The existing `ResourceTransferIntent(source_kind="QUEST")` path in `conservation.py`
directly enables E23C's gold/XP delivery.

### TCK-20260501-E5-REVIEW-HARDENING (historical)
Moved XP/Gold from `CombatUpdate` shadow fields to authoritative pipeline via `RewardUpdate`. The
`reward_upd=RewardUpdate(xp_gain=...)` field on `ResourceTransferIntent` is the correct XP path.

---

## Risks and Open Questions

### Q1 — `quest_completed` event: `WorldEvent` vs string event_type [DECISION REQUIRED]

The ticket AC says emit `event_type="quest_completed"`. However:
- `WorldEvent` (schema.py:L34) uses `category: WorldEventCategory` (typed enum), not `event_type: str`.
- `WorldEventCategory.QUEST_COMPLETED` already exists (schema.py:L21).
- The string `"quest_completed"` is only used in campaign narrative code (classifier, runner).

**Decision needed**: Should the reward emit a `WorldEvent(category=QUEST_COMPLETED)` into
`StateUpdate.world_events_add`? Or emit a separate campaign-style string event? The clean V2 path
is a typed `WorldEvent`. The `payload` field can carry `quest_id`, `entity_id`, `gold`, `xp`.
Recommend: emit `WorldEvent(category=QUEST_COMPLETED, subject=quest_id, payload={"gold": ..., "xp":
...})`. Do NOT use a free-form string field — that violates durable state rules.

### Q2 — Who triggers opportunity reward delivery? [DECISION REQUIRED]

The ticket says "when a quest transitions to COMPLETED, the completing entity receives rewards." But
`QuestOpportunity` in the registry is a world-level object — it is not tied to an entity's
`strategic.projects`. E23B/E23D (HERO matching) was intended to wire a hero to an opportunity.

Without E23D, how does the system know which `entity_id` completed an opportunity?

**Options**:
- A: Add `assigned_entity_id: Optional[int]` to `QuestOpportunity` (requires model change in E23A's
  type — coordinate with E23A stored artifact).
- B: The reward delivery is triggered by a new `QuestOpportunityRewardIntent` carrying both
  `quest_id` and `entity_id`, emitted by whatever system detects completion (e.g., world emergence
  phase or a new QuestOpportunitySystem).
- C: E23C only wires the mechanical reward path (resolve `reward_spec` → `ResourceTransferIntent`);
  E23D provides the entity matching. For now, tests call the resolver directly with an explicit
  entity_id.

**Recommend Option C** to stay in scope. The implementation adds a function
`QuestOpportunityRewardSystem.enforce(state, update)` that processes any
`quest_opportunity_reward_intents` in the `StateUpdate`, but E23D populates those. E23C tests use
a synthetic intent.

### Q3 — `diplomatic_errand` with `reward_spec={}` [CONFIRMED SAFE]

`reward_spec.get("gold", 0) == 0` and `reward_spec.get("xp", 0) == 0` → no
`ResourceTransferIntent` emitted. Quest transitions to COMPLETED and is removed from registry via
`quest_registry_remove`. No conservation violation. Stub is safe.

### Q4 — Removal from registry after reward [DESIGN GAP]

The ticket says COMPLETED/REWARDED quests are "removed from `quest_registry`" (from E23B's scope
definition). The apply path has `quest_registry_remove`. The reward enforce stage must also emit
`quest_registry_remove=[quest_id]` in the `StateUpdate` alongside the `ResourceTransferIntent`.

Failure case: if inventory is full and reward delivery fails, should the quest remain in the
registry as `QuestOpportunityStatus.COMPLETED` (for retry)? Yes — mirror the `REWARD_PENDING`
pattern from entity quests. Only remove from registry when terminal (`REWARDED` or
`FAILED`/`EXPIRED`).

### Q5 — `faction_rep` in `reward_spec` [CONFIRMED OUT OF SCOPE]

`reward_spec["faction_rep"]` is explicitly out of scope (Phase 5). The implementation must silently
skip this key. Log a debug-level warning if non-zero, do not raise.

---

## Anti-Drift Hazards

1. **Do not call `QuestService.mark_rewarded()` for `QuestOpportunity` rewards.** That method
   operates on `QuestState` (entity projects), not on `QuestOpportunity`. The opportunity
   completion is signalled via `quest_status_updates` in `StateUpdate`.

2. **Do not emit `ResourceTransferIntent` from `WorldEmergencePhase` or
   `QuestLifecycleService`.** Resource intents must come from an enforce/refinement stage called
   by `AuthoritativeApplyPipeline.refine()`, not from world emergence.

3. **Do not read `quest_registry` from `entity.strategic.projects`.** These are two separate state
   locations: `state.quest_registry` (world-level `QuestOpportunity`) vs
   `entity.strategic.projects` (entity-level `QuestState`).

4. **The `reward_upd=RewardUpdate(xp_gain=...)` field on `ResourceTransferIntent` must be used for
   XP** — not `xp_reward: int` on the same dataclass (that field exists but is only used for
   legacy paths). Check `src/core/update_models/resources.py:L27` vs `L38`.

5. **Conservation resolver already handles `source_kind="QUEST"` idempotency.**
   `processed_transaction_ids` check at `conservation.py:L58` prevents double-reward. The
   transaction_id must be stable across ticks (e.g., `f"quest:{quest_id}:reward"`).
