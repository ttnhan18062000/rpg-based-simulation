---
status: authoritative
layer: systems
authority: P1
audience: agent
last_verified: 2026-08-29
tags: [quests, lifecycle, rewards, contract, progression]
---

# Quest System Contract

**Source:** `src/quests/` (3 files: generator.py, service.py, templates.py)  
**Core types:** `src/core/models/quests.py` — `QuestState`, `QuestKind`, `QuestStatus`, `RewardState`  
**Authoritative pipeline:** the Objective Reward stage (`PROG-084`) delivers quest rewards and completion markers.

---

## Authoritative Status

`QuestState` is a frozen dataclass stored on `EntityState` — it participates in the simulation state but is applied through the authoritative pipeline's Objective Reward stage. `QuestService` is stateless and does not directly mutate `AuthoritativeState`.

---

## QuestKind Enum

| Kind | Description |
|---|---|
| `HUNT` | Kill a target count of a specific enemy type |
| `GATHER` | Collect a target quantity of a material |
| `EXPLORE` | Visit a specific location or region |
| `LIBERATE` | Clear and hold an outpost or camp |
| `BOUNTY` | Defeat a named target entity |
| `ESCORT` | Protect/accompany a target to a destination (TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING) |

---

## Quest Lifecycle

```
[generated] → ACTIVE → COMPLETED → REWARD_PENDING → REWARDED
                     ↘ (if progress blocked) stays ACTIVE
```

| Status | Value | Meaning |
|---|---|---|
| `ACTIVE` | 1 | Quest is in progress; progress updates are accepted |
| `COMPLETED` | 2 | Goal reached (`current_value >= goal_value`); awaiting reward delivery |
| `REWARD_PENDING` | 4 | Reward calculated; waiting for delivery |
| `REWARDED` | 3 | Reward delivered; quest is terminal |

**Auto-completion rule:** When `QuestService.add_progress()` is called and `current_value + delta >= goal_value`, status transitions automatically to `COMPLETED`. No manual completion call required.

**Reward terminal rule:** `REWARDED` is terminal — no further status transitions are permitted. `mark_rewarded()` is a no-op if the quest is already `REWARDED`.

**No expiry:** The quest system does not implement time-based expiry. Quests remain `ACTIVE` until completed, rewarded, or explicitly removed from the entity's quest list.

---

## QuestState Fields

| Field | Type | Description |
|---|---|---|
| `quest_kind` | `QuestKind` | Type of quest |
| `quest_status` | `QuestStatus` | Current lifecycle status |
| `goal_value` | `float` | Target progress value for completion |
| `current_value` | `float` | Current accumulated progress |
| `reward` | `RewardState` | XP, gold, and item template IDs to grant on completion |
| `source_building_id` | `Optional[int]` | Building that issued the quest (e.g. guild) |
| `source_entity_id` | `Optional[int]` | NPC entity that issued the quest |
| `name` | `str` | Display name |

`QuestState` is **frozen** — `QuestService` methods return new instances via `dataclasses.replace()`.

`progress_ratio` property: `min(1.0, current_value / goal_value)`. Returns `1.0` if `goal_value <= 0`.  
`is_finished` property: `current_value >= goal_value`.

---

## QuestService Contract (service.py)

All methods are `@staticmethod` and return a new `QuestState` — they do not mutate the input.

### `add_progress(quest, delta) → QuestState`
- If `quest_status != ACTIVE`: returns `quest` unchanged (progress is rejected for non-active quests).
- Adds `delta` to `current_value`.
- If `current_value + delta >= goal_value`: transitions to `COMPLETED`.
- Returns new frozen `QuestState`.

### `mark_rewarded(quest) → QuestState`
- If `quest_status not in (COMPLETED, REWARD_PENDING)`: returns `quest` unchanged.
- Transitions to `REWARDED`.
- Returns new frozen `QuestState`.

---

## Quest Generation Contract (generator.py)

`QuestGenerator.generate(seed, level, tick, existing_ids=None, pressure_profile=None, origin_pos=None) → Optional[QuestState]`

**Determinism:** Uses `DeterministicRNG(seed)` — same `(seed, level, tick)` inputs always produce the same quest (or `None`).

**Template selection:**
1. Filter `TEMPLATES` by level band (`min_level <= level <= max_level`).
2. Exclude templates whose `id` is in `existing_ids` (prevents quest duplicates).
3. If no candidates remain: returns `None`.
4. Select from candidates using `DeterministicRNG.choice(Domain.QUEST, tick, level, candidates)`
   (or `DeterministicRNG.weighted_choice(...)` when `pressure_profile` differentiates the
   candidates' weights).

**Reward scaling:** Linear — 10% increase per level above `template.min_level`.

**Metadata population (TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP,
TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP):**
`QuestState.metadata` is the contract `QuestResolutionSystem`'s evaluators read to detect
completion (`target_pos` for EXPLORE, `target_archetype_id`/`target_faction_id`/
`target_projected_label`/`target_kind` for HUNT). Prior to these fixes, `generate()` never
populated `metadata` for any kind, making every generated quest permanently uncompletable.

- **EXPLORE**: when the drawn template is `QuestKind.EXPLORE` and the caller supplies `origin_pos`
  (the requesting entity's position — `GuildAction.visit()` passes `entity.navigation.position`),
  `generate()` computes a deterministic target position offset `[15.0, 40.0]` tiles from
  `origin_pos` (random angle/distance via `DeterministicRNG`) and sets
  `metadata={"target_pos": (x, y)}`. Without `origin_pos`, `metadata` stays without a
  `target_pos` key.
- **HUNT**: `QuestTemplate` gained a `target_kind: Optional[str] = None` field — a real,
  corpus-grounded `EntityState.kind` value (derived from the archetype's `race` catalog entry,
  e.g. `"wolf"` for both `hungry_wolf`/`alpha_wolf`) a killed entity must match for
  `evaluate_combat_victory()`'s legacy `target_kind` fallback path to advance the quest. Only
  `q_wolf_hunt` has one set (`"wolf"`) — `q_slime_cull` deliberately has none: no `"slime"`
  race/archetype exists anywhere in the real content corpus
  (`data/content/entities/entity_archetypes.yaml`), so this quest stays honestly uncompletable
  rather than matching against a fabricated kind string. When set, `generate()` sets
  `metadata={"target_kind": template.target_kind}` for HUNT templates.
- **GATHER/BOUNTY/LIBERATE/ESCORT remain uncompletable**: they have no `evaluate_*` method in
  `QuestResolutionSystem` at all (out of scope for both tickets above). `ESCORT`
  (TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING) is architecturally different from the other
  three, though: `QuestResolutionSystem.enforce()` reacts to an ESCORT quest's generic
  ACTIVE→COMPLETED transition (the same `is_newly_completed` check every kind gets) by calling
  `ReputationUpdateService.process_witnessed_event(..., "successful_escort")` — it does not itself
  *detect* completion the way HUNT/EXPLORE's evaluators do. No live driver (generator template or
  world-content compiler) currently advances `current_value` toward `goal_value` for a compiled or
  generated ESCORT quest, so this reaction is real and correctly wired but not yet reachable in a
  live simulation run — see `docs/simulation/domains/commitment_contract.md`'s "Engine Pipeline
  Phase" section for the reputation side of this wiring.

**Built-in templates by tier:**

| Tier | Level range | Templates |
|---|---|---|
| Tier 1 | 1–8 | `q_slime_cull` (HUNT), `q_wood_survey` (EXPLORE) |
| Tier 2 | 4–12 | `q_wolf_hunt` (HUNT), `q_herb_gather` (GATHER) |
| Tier 3 | 11–100 | `q_bandit_bounty` (BOUNTY), `q_camp_liberate` (LIBERATE) |

---

## Live Entry Point: Guild Visit (TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING)

`QuestGenerator.generate()` is deterministic pure logic — something must actually call it during
live gameplay to produce a real `QuestState` an entity carries. That caller is
`GuildAction.visit()` (`src/town/guild.py`), which computes a `QuestPressureProfile` (trauma/
hazard/scarcity) from the entity's region and calls `QuestGenerator.generate_quests()`.

**Dispatch mechanism:** `GuildVisitPhase` (`src/engine/pipeline_phases/guild_visit.py`) — a
dedicated authoritative-pipeline phase (`run_phase("guild_visit", ...)` in `pipeline.py`), gated
behind `ENABLE_GUILD_QUEST_GENERATION` (default `OFF`; see `docs/guides/feature_flags.md`). An
entity's own AI decision layer selects a `GoalKind.GUILD` goal (scored by `GuildNeedScorer`,
`src/ai/goals/scorers.py`, targeting the nearest `town_hall` building — no dedicated "guild"
building kind exists in any real world content, so this is deliberately rebased onto `town_hall`)
when it has spare project capacity; once the entity physically arrives (Manhattan distance ≤ 1),
`GuildVisitPhase` detects the arrival independently (mirroring `_resolve_active_objective`'s own
"detour" arrival-check pattern) and calls `GuildAction.visit()` directly with full `state` access.

This is **not** an `ENTITY_ACT`/`ActionRouter` dispatch (unlike `EAT`/`REST`/`INTERACT`) —
`GuildAction.visit()` needs `state.regions`/`state.resource_nodes` for its pressure/lead
computation, which the concurrent-worker `ENTITY_ACT` path's `WorkerPacket` cannot provide by
design ("Law: A worker must receive a compact, bounded, and read-only context",
`src/core/worker_protocol.py`).

---

## Template System (templates.py)

`QUEST_TEMPLATES: Dict[QuestKind, QuestTemplate]` — one entry per `QuestKind`.

`QuestTemplate` fields: `kind`, `base_name` (with `{subject}` placeholder), `base_goal`, `base_xp`, `base_gold`, `subject_options`.

Subject selection from `subject_options` is deterministic (uses generator's RNG). `base_name.format(subject=chosen_subject)` produces the display name.

---

## Objective Reward Integration (Authoritative Pipeline)

The **Objective Reward** stage (`PROG-084`) is the only place quest rewards are applied to `AuthoritativeState`.

**What this stage does:**
1. Iterates entities whose `QuestState.quest_status == COMPLETED`.
2. Delivers `RewardState` (XP → `EntityState.xp`, gold → entity inventory, items → entity inventory).
3. Calls `QuestService.mark_rewarded(quest)` to produce the terminal `REWARDED` state.
4. Applies the new `QuestState` to `AuthoritativeState`.

**What the quest system does NOT do:**
- It does not apply rewards directly — only the Objective Reward stage does.
- It does not call `EntityState` mutators — `QuestService` is read-only logic.

---

## Quest Opportunity Reward Integration (E23C — Pressure-Generated Quests)

`QuestOpportunity` entries in `state.quest_registry` (world-level registry, not entity projects) use a separate reward path implemented in E23C.

**Source:** `src/engine/pipeline_phases/quest_opportunity_rewards.py` — `QuestOpportunityRewardSystem`  
**Intent type:** `QuestOpportunityRewardIntent` (field `quest_opportunity_reward_intents` on `StateUpdate`)  
**Parity entry:** `PROG-109`

**Lifecycle for opportunity quests:**

```
QuestOpportunityStatus.COMPLETED → QuestOpportunityRewardIntent emitted
    → ResourceTransferIntent(source_kind=QUEST, reward_upd=RewardUpdate(xp_gain=...))
    → WorldEvent(category=QUEST_COMPLETED)
    → registry removal deferred until transaction confirmed in processed_transaction_ids
```

**Key distinctions from entity-project quest rewards (PROG-084):**

| | Entity-project quests (PROG-084) | Opportunity quests (E23C) |
|---|---|---|
| Status enum | `QuestStatus` (int) on `QuestState` | `QuestOpportunityStatus` (str) on `QuestOpportunity` |
| Storage | `entity.strategic.projects` | `state.quest_registry` |
| XP field | `RewardState.xp` | `RewardUpdate(xp_gain=...)` via `reward_upd` |
| Registry removal | N/A | Deferred until `transaction_id` confirmed |
| Faction rep | Delivered | Stubbed (Phase 5 future work) |

**Caller contract:** The reward mechanism is wired in `QuestRewardPhase.resolve()`. The caller supplies `entity_id` and `quest_id` via `QuestOpportunityRewardIntent`. Multi-entity targeting (Phase 4 / E23D HERO matching) is out of scope for E23C.

---

## RewardState

| Field | Type | Applied by the Objective Reward stage |
|---|---|---|
| `xp` | `int` | Added to entity XP pool |
| `gold` | `int` | Added to entity gold |
| `items` | `List[str]` | Item template IDs added to entity inventory |
