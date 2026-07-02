---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21C-SCORING-WIRE
artifact_type: plan
tags: [resource-ecology, adventure-scoring, cognition, phase-2]
---

# Plan — TCK-20260619-E21C-SCORING-WIRE
## Epic 2.1C · Depletion-Aware Adventure Route Scoring

---

## Ordered Steps

### Step 1 — Add `target_node_id: Optional[int] = None` to `AdventureRouteOption`

**File:** `src/domains/adventure/schema.py`

Add field after `source_opportunity_ids`:
```python
target_node_id: Optional[int] = None
```

This is a backward-compatible addition to the frozen dataclass. All existing construction sites omit it and get `None`.

**AC mapped:** Enables scorer to look up the node in `resource_nodes`.

**Scope guard:** Do NOT modify any other schema fields or add new route families.

---

### Step 2 — Set `target_node_id` in `AdventureRouteGenerator.generate()`

**File:** `src/domains/adventure/generator.py`

In the loop over `opportunities` (around L70-82), for `gather_resource` kind, extract the integer node ID from `opp.target_id` and pass it as `target_node_id`:

```python
target_node_id = None
if opp.kind == "gather_resource":
    try:
        target_node_id = int(opp.target_id)
    except (ValueError, TypeError):
        target_node_id = None

opts.append(
    AdventureRouteOption(
        ...
        target_node_id=target_node_id,
    )
)
```

**AC mapped:** Routes to resource nodes carry the node ID needed for depletion lookup.

**Scope guard:** Only set for `gather_resource` kind. Other opportunity kinds leave `target_node_id=None`.

**Dependency:** Step 1 (field must exist first).

---

### Step 3 — Add `resource_nodes` parameter to `AdventureRouteScorer.score()`

**File:** `src/domains/adventure/scoring.py`

Change signature:
```python
@staticmethod
def score(
    entity: EntityState,
    route: AdventureRouteOption,
    resource_nodes: Optional[Dict[int, "ResourceNodeState"]] = None,
) -> AdventureRouteOption:
```

After `benefit = route.expected_benefit` (current L100), add:
```python
# Depletion-aware scaling for GATHER_RESOURCE routes
if route.family == RouteFamily.GATHER_RESOURCE and resource_nodes is not None:
    node_id = getattr(route, "target_node_id", None)
    if node_id is not None:
        target_node = resource_nodes.get(node_id)
        if target_node is not None and target_node.max_charges > 0:
            depletion_fraction = target_node.remaining_charges / target_node.max_charges
            benefit = benefit * depletion_fraction
```

Add import at top of file:
```python
from typing import Any, Dict, Optional
from src.core.state import ResourceNodeState
```

**AC mapped:** AC1 (depleted ≤ full), AC2 (half → half benefit), AC3 (non-harvest unaffected), AC4 (missing node → no crash), AC5 (max_charges=0 guard), AC6 (resource_nodes=None → backward compat).

**Scope guard:** Only GATHER_RESOURCE family. Guard on `resource_nodes is not None`, `node_id is not None`, `target_node is not None`, `max_charges > 0`.

**Dependency:** Step 1 (target_node_id field).

---

### Step 4 — Thread `resource_nodes` through `AdventureDecisionService.decide()`

**File:** `src/domains/adventure/service.py`

Change signature:
```python
@staticmethod
def decide(
    entity: EntityState,
    candidates: List[AdventureRouteOption],
    tick: int = 0,
    resource_nodes: Optional[Dict[int, Any]] = None,
) -> AdventureDecisionResult:
```

Update the scoring call (around L70):
```python
scored = AdventureRouteScorer.score(entity, cand, resource_nodes=resource_nodes)
```

**AC mapped:** Enables `phase.py` to pass state to scorer without bypassing the service.

**Scope guard:** No other logic changes in `decide()`. Backward-compatible default.

**Dependency:** Step 3 (scorer accepts resource_nodes).

---

### Step 5 — Pass `state.resource_nodes` from `AdventureDecisionPhase`

**File:** `src/domains/adventure/phase.py`

Update the `decide()` call (around L65):
```python
result = AdventureDecisionService.decide(
    hero, candidates, tick=tick,
    resource_nodes=state.resource_nodes,
)
```

**AC mapped:** Live simulation picks up actual node depletion state.

**Scope guard:** No other changes to `phase.py`.

**Dependency:** Step 4.

---

### Step 6 — Write `tests/unit/domains/adventure/test_depletion_scoring.py`

**File:** `tests/unit/domains/adventure/test_depletion_scoring.py` (new)

Implement all 6 tests from test_plan.md:
- `test_gather_route_depleted_node_scores_lower_than_full`
- `test_gather_route_half_depleted_scores_half_benefit`
- `test_non_gather_routes_unaffected_by_resource_nodes`
- `test_gather_route_missing_node_no_scaling`
- `test_gather_route_zero_max_charges_no_crash`
- `test_scorer_no_resource_nodes_backward_compatible`

Use `ResourceNodeState` directly (no ecology dependency). Use `V2EntityBuilder` for minimal entity construction (same pattern as `test_phase3_route_scoring.py`).

**AC mapped:** All ACs from ticket.

**Dependency:** Steps 1–3.

---

### Step 7 — Update `docs/mechanics/04_strategic_cognition.md` §6.2

**File:** `docs/mechanics/04_strategic_cognition.md`

In §6.2 Formula Term Constants table, update the `benefit` row to note:
> For `GATHER_RESOURCE` routes: `benefit = route.expected_benefit × depletion_fraction` where `depletion_fraction = remaining_charges / max_charges` (0.0 if node empty, 1.0 if full). Skipped if node not found or `resource_nodes` not available.

**Scope guard:** Only §6.2. Do not touch §6.1, §6.3, §6.4, §6.5, §6.6.

**Dependency:** Steps 1–5 (doc follows implementation).

---

### Step 8 — Update `docs/parity_ledger/strategic_cognition.yaml` STRAT-227

**File:** `docs/parity_ledger/strategic_cognition.yaml`

Add depletion_fraction to STRAT-227 `v2_evidence` and update `test_path` to include new test file.

**Scope guard:** Only STRAT-227. Status remains `verified`.

---

## Dependency Map

```
Step 1 (schema) → Step 2 (generator) → Step 6 (tests)
Step 1 (schema) → Step 3 (scorer) → Step 4 (service) → Step 5 (phase)
Step 5 → Step 7 (docs) → Step 8 (parity)
```

Steps 2 and 3 can be done in parallel after Step 1.

---

## Scope Guards Summary

- Do NOT modify `ResourceOpportunityProvider` — out of scope
- Do NOT modify `Opportunity` dataclass
- Do NOT touch combat, economic, or other route families
- Do NOT alter `StateUpdate`, `ResourceNodeUpdate`, or any apply-path code
- Do NOT break existing `test_phase3_route_scoring.py` tests

---

## Acceptance Criteria Mapped to Steps

| AC | Steps |
|---|---|
| GATHER_RESOURCE depleted ≤ full score | 1, 3, 6 |
| Half-depleted ≤ 0.5 × full benefit | 1, 3, 6 |
| Non-harvest routes unchanged | 3, 6 |
| `test_depletion_scoring.py` passes | 1-6 |
| Mechanics Bible §6.2 updated | 7 |
| STRAT-227 updated | 8 |

---

## Deviations

_(None yet — to be filled if implementation differs from plan.)_
