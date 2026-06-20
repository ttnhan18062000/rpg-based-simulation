---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21C-SCORING-WIRE
artifact_type: investigation
tags: [resource-ecology, adventure-scoring, cognition, phase-2]
---

# Investigation — TCK-20260619-E21C-SCORING-WIRE
## Epic 2.1C · Depletion-Aware Adventure Route Scoring

---

## Current Behavior

### 1. `AdventureRouteScorer.score()` — signature and benefit term

**File:** `src/domains/adventure/scoring.py:L24-L136`

```python
@staticmethod
def score(entity: EntityState, route: AdventureRouteOption) -> AdventureRouteOption:
```

At L100: `benefit = route.expected_benefit` — flat read, no depletion adjustment.

The scorer has no access to `state` or `state.resource_nodes`. It receives only `entity` and `route`.

### 2. Call chain

`AdventureDecisionPhase.apply(state, ...)` (`src/domains/adventure/phase.py:L26`)
→ `AdventureDecisionService.decide(hero, candidates, tick)` (`src/domains/adventure/service.py:L31`)
→ `AdventureRouteScorer.score(entity, cand)` (`src/domains/adventure/service.py:L70`)

`state: AuthoritativeState` (which contains `state.resource_nodes: Dict[int, ResourceNodeState]`)
is available in `AdventureDecisionPhase.apply()` but not threaded further down.

### 3. `AdventureRouteOption` — no `target_node_id` field

`src/domains/adventure/schema.py:L33-L57` — `AdventureRouteOption` fields:
- `family`, `score`, `confidence`, `expected_benefit`, `expected_risk`
- `requirements`, `blockers`, `source_opportunity_ids`, `reason`

**No `target_node_id` field exists.** The node ID is available in:
- `Opportunity.target_id` (string, e.g. `"5"`) in `ResourceOpportunityProvider`
- `source_opportunity_ids` contains `f"opp_resource_{node_id}"` (string, from generator L79)

### 4. `ResourceNodeState` — fields confirmed present (E21A done)

`src/core/state.py:L810-L824`:
- `remaining_charges: int` at L817
- `max_charges: int` at L818
- `regen_rate_per_tick: int = 0` at L822 (added by E21A)

`AuthoritativeState.resource_nodes: Dict[int, ResourceNodeState]` at L999.

### 5. `ResourceOpportunityProvider` — already applies partial depletion

`src/world/providers/resources.py:L71-72`:
```python
depletion_mult = node.remaining_charges / node.max_charges if node.max_charges > 0 else 1.0
reward *= (0.5 + 0.5 * depletion_mult)
```
This adjusts `estimated_reward` (and thus `expected_benefit` = reward/100.0) in the generator. A fully depleted node never reaches the generator (filtered at L55: `if node.remaining_charges <= 0: continue`). A half-depleted node gets `reward *= 0.75`.

**This is a partial depletion adjustment.** The ticket scope requires an additional multiplier in the scorer that reduces `benefit` linearly from 1.0 (full) to 0.0 (empty). The two mechanisms are complementary:
- Provider: adjusts reward estimate (opportunity-level heuristic, 0.5–1.0 range)
- Scorer: applies depletion_fraction multiplier to benefit (0.0–1.0 range, pure linear)

Note: Because `remaining_charges <= 0` nodes are filtered by the provider, a `GATHER_RESOURCE` route can only exist for nodes with `remaining_charges > 0`. The scorer's depletion multiplier thus operates in the range (0.0, 1.0] exclusive of 0.

### 6. How to thread the node ID from route to scorer

The route's `source_opportunity_ids` tuple contains `"opp_resource_{node_id}"`. The node_id integer can be parsed from this string. However, the clean approach is to add a `target_node_id: Optional[int]` field to `AdventureRouteOption` and set it in the generator for `GATHER_RESOURCE` routes.

Alternative (avoids schema change): parse node_id from `source_opportunity_ids[0]` in the scorer. This is fragile — depends on the string format of opportunity IDs.

**Decision: Add `target_node_id: Optional[int] = None` to `AdventureRouteOption`** and thread `state.resource_nodes` as an optional parameter to `score()`. This is the cleanest path and matches the ticket scope pseudocode exactly.

### 7. `AdventureDecisionService.decide()` — no state parameter

`src/domains/adventure/service.py:L31-L35`:
```python
def decide(entity, candidates, tick=0) -> AdventureDecisionResult:
```
No `resource_nodes` parameter. Must add `resource_nodes: Optional[Dict[int, ResourceNodeState]] = None` and pass it through to `AdventureRouteScorer.score()`.

### 8. STRAT-227 — parity entry for scoring constants

`docs/parity_ledger/strategic_cognition.yaml:L2405-L2423`:
- Text describes fixed constants: blocker_penalty=2.0, personality_bias weight=0.25, confidence_bonus weight=0.15, risk weight=0.5.
- **No mention of `depletion_fraction` multiplier** — must be added after implementation.
- Status: `verified`, Priority: P1.

### 9. `docs/mechanics/04_strategic_cognition.md` §6 — no depletion term

Section 6.2 Formula Term Constants table (`L94-L101`) lists: urgency, benefit, personality_bias, confidence_bonus, risk_penalty, blocker_penalty. The `benefit` term is documented as `route.expected_benefit` — no depletion modifier documented. Must add a §6.2.1 or inline note after implementation.

---

## Mechanics/Engine Constraints

- **Scoring formula** (`docs/mechanics/04_strategic_cognition.md §6.1`):
  ```
  score = urgency + benefit + personality_bias + confidence_bonus − risk_penalty − blocker_penalty
  ```
  The `benefit` term is the injection point. Multiplying by `depletion_fraction` before computing `final_score` is formula-compliant.

- **Read-only constraint:** `AdventureRouteScorer.score()` reads state. It must not mutate anything. Adding `resource_nodes` as a read-only dict parameter satisfies this.

- **Guard against missing node:** ticket scope explicitly requires guard if `target_node is None` or `max_charges == 0`.

- **Frozen dataclass:** `AdventureRouteOption` is `frozen=True, slots=True`. Adding `target_node_id: Optional[int] = None` with a default is safe — `dataclasses.replace()` is already used in the scorer return.

---

## Parity Ledger Overlap

| ID | Text | Status | Relevance |
|---|---|---|---|
| STRAT-227 | AdventureRouteScorer scoring constants (blocker=2.0, bias=0.25, etc.) | `verified` | Must update v2_evidence to include depletion_fraction modifier after implementation |

No other entries in `strategic_cognition.yaml` cover the `benefit` term directly.

---

## Prior Work

- **E21A (TCK-20260619-E21A-NODE-SCHEMA) — DONE:** Added `regen_rate_per_tick`, `RESOURCE_RECOVERED` enum.
- **E21B (TCK-20260619-E21B-REGEN-SERVICE) — DONE:** Added regen loop in ecology.py, RESOURCE_DEPLETED emission in economy.py, recent_world_events on AuthoritativeState.
- `depletion_fraction` logic confirmed absent from scoring.py (current L100: flat read).

---

## Risks and Open Questions

All open questions are resolvable from code inspection — no human decision required.

1. **Schema change to `AdventureRouteOption`:** Adding `target_node_id: Optional[int] = None` is a backward-compatible addition to a frozen dataclass. All existing `AdventureRouteOption(...)` calls omit it (defaults to None). Low risk.

2. **`AdventureDecisionService.decide()` signature change:** Adding `resource_nodes: Optional[Dict[int, ResourceNodeState]] = None` is backward-compatible. Existing tests that call `decide()` without `resource_nodes` continue to work — scorer falls back to no depletion scaling when `resource_nodes` is None.

3. **Double-depletion effect:** Provider already applies partial depletion (0.5–1.0 scale on reward). Scorer applies additional linear depletion_fraction (0.0–1.0). The combined effect is not double-counting the same concept — the provider adjusts the estimated_reward heuristic at opportunity-generation time; the scorer applies the depletion multiplier to whatever benefit value the route carries. This is intentional per the ticket AC.

---

## Anti-Drift Hazards

1. **Do not modify the provider's depletion logic** — it is out of scope.
2. **Do not add `target_node_id` to `Opportunity`** — it already has `target_id: str`; use that when constructing `AdventureRouteOption`.
3. **Do not apply depletion scaling to non-GATHER_RESOURCE families** — the guard must be `if route.family == RouteFamily.GATHER_RESOURCE`.
4. **Do not mutate `state.resource_nodes`** — read-only access only.
5. **Existing tests in `test_phase3_route_scoring.py` pass `AdventureRouteScorer.score(entity, route)` with no resource_nodes** — must not break; default `resource_nodes=None` means no depletion scaling applied.
