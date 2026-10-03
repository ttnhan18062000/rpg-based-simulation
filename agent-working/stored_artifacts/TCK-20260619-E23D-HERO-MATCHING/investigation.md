---
ticket_id: TCK-20260619-E23D-HERO-MATCHING
phase: investigation
date: 2026-06-20
---

# Investigation — TCK-20260619-E23D-HERO-MATCHING
## Epic 2.3D · HERO Capability Matching for Quest Routes

---

## Current Behavior (file:line refs)

### 1. `RouteFamily` enum — no `QUEST_OPPORTUNITY` member

`src/domains/adventure/schema.py:L16-L28` defines `RouteFamily(str, Enum)` with 13 members:
RECOVER, BUY_UPGRADE, CRAFT_UPGRADE, TRAIN_SKILL, TAKE_EASY_QUEST, HUNT_WEAK_ENEMY,
GATHER_RESOURCE, SELL_LOOT_FOR_GOLD, ASK_INFORMATION, SCOUT_LOCATION, FORM_PARTY,
RETURN_TOWN, DEFER_WITH_REASON.

`QUEST_OPPORTUNITY` is absent. `TAKE_EASY_QUEST` exists but is generic; the ticket requires
a dedicated `QUEST_OPPORTUNITY` family for world-registry-backed quests.

### 2. `AdventureRouteOption` — no `quest_id` field

`src/domains/adventure/schema.py:L31-L64` defines the frozen dataclass. It has `target_node_id: Optional[int]`
for GATHER_RESOURCE routes (L59). There is no `quest_id: Optional[str]` field for QUEST_OPPORTUNITY
routes, which must reference a `QuestOpportunity` in `state.quest_registry`.

### 3. `AdventureRouteScorer.score()` — no QUEST_OPPORTUNITY branch

`src/domains/adventure/scoring.py:L22-L164` handles route families via dict lookup and `if/elif`
branches. There is no branch for `RouteFamily.QUEST_OPPORTUNITY`. The scorer signature is:
```python
def score(entity, route, resource_nodes=None) -> AdventureRouteOption
```
No `state` or `quest_registry` parameter exists. To look up `QuestOpportunity` by `quest_id`,
the scorer needs either a `quest_registry` dict parameter or inline access.

### 4. HERO archetype identification

`src/core/enums.py:L6-L7`: `EntityRole.HERO = 0` (IntEnum).
`src/core/state.py:L432`: `IdentityComponent.role: int = 0  # EntityRole.HERO`
Entity is HERO when `entity.identity.role == EntityRole.HERO` (or `== 0`).
The ticket's suggestion of `entity.identity.properties.get("archetype") == "HERO"` is **incorrect** —
the authoritative HERO marker is `entity.identity.role`.
The E11A tickets (TCK-20260619-E11A-HERO-AUTHORING) confirm HERO entities are created with
`EntityRole.HERO` as their `role` field.

### 5. `capability_tags` — where stored

`IdentityComponent.traits: Set[str]` (`src/core/state.py:L443`) stores entity capability tags as
string tokens (e.g. `"COMBAT"`, `"MAGIC"`, `"STEALTH"`). This is the correct field to compare
against `QuestOpportunity.objective_chain`.

### 6. `QuestOpportunity.objective_chain` — token format

`src/core/models/quests.py:L75`: `objective_chain: Tuple[str, ...]` — ordered objective tokens
e.g. `("fetch:iron_ore:3",)` or `("combat:threat:1",)`. Capability matching extracts the verb
prefix (e.g. `"combat"`, `"fetch"`) and compares against normalized entity traits.

### 7. `state.quest_registry` — confirmed present

`src/core/state.py:L1055`: `quest_registry: Dict[str, "QuestOpportunity"] = field(default_factory=dict)`
on `AuthoritativeState`. This is the correct lookup source.
`src/core/state.py:L1130`: exposed read-only on access. So the scorer needs `quest_registry`
passed as a dict, not the full `AuthoritativeState`.

### 8. `AdventureRouteScorer.score()` — signature extension

The scorer is a static method. To avoid passing `AuthoritativeState` (which would couple scorer
to full state), we pass `quest_registry: Optional[Dict[str, QuestOpportunity]] = None` — parallel
to how `resource_nodes` is passed. This keeps the scorer testable in isolation.

### 9. Mechanics Bible §6.4 — QUEST_OPPORTUNITY not listed

`docs/mechanics/04_strategic_cognition.md:L140-L151` (§6.4 Personality Bias table) does not
include `QUEST_OPPORTUNITY`. A new row must be added: `QUEST_OPPORTUNITY | greed | 0.25` (quests
yield gold/reward, so greedy entities like them; HERO override then multiplies benefit).

### 10. Parity ledger — STRAT-228 entry required

`docs/parity_ledger/strategic_cognition.yaml` has no STRAT-228 entry. The ticket scope requires
adding one for quest route scoring.

---

## Mechanics / Engine Constraints

- **Information opacity rule** (`docs/mechanics/04_strategic_cognition.md §5`): Scorer reads only
  subjective state. `quest_registry` is world-level authoritative state — passing it as a parameter
  is the correct pattern (same as `resource_nodes`), not storing it on the entity.
- **Determinism**: capability_match scoring must be deterministic. No randomness. Sort-based
  comparison only.
- **No durable mutation**: `AdventureRouteScorer` reads only. It must not write to `quest_registry`
  or `entity.strategic`.
- **Architecture rule**: `AdventureRouteScorer` is a read-only decision scorer. New parameter
  `quest_registry` is `Optional[Dict[str, QuestOpportunity]]` with safe default `None`.

---

## Parity Ledger Overlap

- `strategic_cognition.yaml`: STRAT-228 (new — quest route scoring capability matching) — add.
- No existing entries are changed by this ticket.

---

## Prior Work

- **E23A** (TCK-20260619-E23A-QUEST-OPPORTUNITY, DONE): Added `QuestOpportunity` model and
  `QuestOpportunityGenerator`. `objective_chain` is `Tuple[str, ...]`.
- **E23B** (TCK-20260619-E23B-QUEST-LIFECYCLE, DONE): Added `quest_registry` to `AuthoritativeState`,
  `QuestOpportunityStatus`, `quest_registry_add/remove/status_updates` to `StateUpdate`.
- **E23C** (TCK-20260619-E23C-QUEST-REWARDS, DONE): Added `QuestRewardSystem` and reward emission
  on `QUEST_OPPORTUNITY` completion.
- **E21C** (TCK-20260619-E21C-SCORING-WIRE, DONE): Added depletion-aware GATHER_RESOURCE scoring;
  introduced `resource_nodes` optional parameter pattern — this ticket follows the same pattern.

---

## Risks and Open Questions

1. **`capability_tags` → `traits` mapping**: The ticket says `entity.identity.properties.get("archetype")`
   but the correct field is `entity.identity.role == EntityRole.HERO` and capability tags are in
   `entity.identity.traits`. This must not use `properties` for HERO detection.

2. **Objective-chain token parsing**: Tokens are `"verb:target:count"` format. Matching the verb
   prefix against entity traits is sufficient for P1 capability matching. Full token parsing not
   required — only verb extraction.

3. **`quest_id` field on `AdventureRouteOption`**: Must be added as `Optional[str]` with default
   `None` to carry the registry key. The dataclass is `frozen=True, slots=True` — addition is
   safe but callers constructing routes without quest_id use the default.

4. **Scorer signature change**: Existing callers of `AdventureRouteScorer.score()` pass only
   `(entity, route)` or `(entity, route, resource_nodes)`. New optional `quest_registry` param
   is backward-compatible.

---

## Anti-Drift Hazards

- Do not touch `QuestState` (entity-level quest projects) — distinct from `QuestOpportunity`.
- Do not modify `WorldEmergencePhase` or `StateUpdate` — out of scope for E23D.
- Do not alter existing scoring weights (0.25, 0.15, 0.5, 2.0) for existing route families.
- `RouteFamily` is `str, Enum` — new member must follow the pattern: `QUEST_OPPORTUNITY = "quest_opportunity"`.
