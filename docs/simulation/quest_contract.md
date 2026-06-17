---
status: authoritative
layer: systems
authority: P1
audience: agent
last_verified: 2026-06-12
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

`QuestGenerator.generate(seed, level, tick, existing_ids=None) → Optional[QuestState]`

**Determinism:** Uses `DeterministicRNG(seed)` — same `(seed, level, tick)` inputs always produce the same quest (or `None`).

**Template selection:**
1. Filter `TEMPLATES` by level band (`min_level <= level <= max_level`).
2. Exclude templates whose `id` is in `existing_ids` (prevents quest duplicates).
3. If no candidates remain: returns `None`.
4. Select from candidates using `DeterministicRNG.choice(Domain.QUEST, tick, level, candidates)`.

**Reward scaling:** Linear — 10% increase per level above `template.min_level`.

**Built-in templates by tier:**

| Tier | Level range | Templates |
|---|---|---|
| Tier 1 | 1–8 | `q_slime_cull` (HUNT), `q_wood_survey` (EXPLORE) |
| Tier 2 | 4–12 | `q_wolf_hunt` (HUNT), `q_herb_gather` (GATHER) |
| Tier 3 | 11–100 | `q_bandit_bounty` (BOUNTY), `q_camp_liberate` (LIBERATE) |

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

## RewardState

| Field | Type | Applied by the Objective Reward stage |
|---|---|---|
| `xp` | `int` | Added to entity XP pool |
| `gold` | `int` | Added to entity gold |
| `items` | `List[str]` | Item template IDs added to entity inventory |
