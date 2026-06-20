---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21C-SCORING-WIRE
artifact_type: test_plan
tags: [resource-ecology, adventure-scoring, cognition, phase-2]
---

# Test Plan — TCK-20260619-E21C-SCORING-WIRE
## Epic 2.1C · Depletion-Aware Adventure Route Scoring

---

## Regression Surface (existing tests that must pass)

| Test file | What it covers |
|---|---|
| `tests/unit/domains/adventure/test_phase3_route_scoring.py` | Existing scoring formula tests — personality bias, urgency, risk, determinism |

All 7 tests in `test_phase3_route_scoring.py` must continue to pass unchanged. They call `AdventureRouteScorer.score(entity, route)` with no `resource_nodes` — the new optional parameter defaults to `None`, so no depletion scaling is applied.

---

## New Tests Required (per AC)

### File: `tests/unit/domains/adventure/test_depletion_scoring.py`

#### AC1: Depleted node → score ≤ score for full node (same route type)

```python
def test_gather_route_depleted_node_scores_lower_than_full():
    """GATHER_RESOURCE to depleted node (remaining=0) scores <= full node."""
```
- Build minimal entity, two GATHER_RESOURCE routes (same benefit, confidence, risk)
- Full node: remaining_charges=10, max_charges=10 → depletion_fraction=1.0
- Depleted node: remaining_charges=0, max_charges=10 → depletion_fraction=0.0
- Assert: score_depleted <= score_full

Note: remaining_charges=0 → depletion_fraction=0.0 → benefit=0.0. Provider filters these out in practice, but scorer must handle them gracefully.

#### AC2: Half-depleted → score ≤ 0.5 × full score (when urgency=0, bias=0, risk=0)

```python
def test_gather_route_half_depleted_scores_half_benefit():
    """With no urgency/bias/risk, half-depleted score == full score * 0.5."""
```
- Route: expected_benefit=0.8, confidence=0.0, expected_risk=0.0, no blockers
- Node half: remaining_charges=5, max_charges=10 → depletion_fraction=0.5
- Node full: remaining_charges=10, max_charges=10 → depletion_fraction=1.0
- Expected: score_half == 0.8 * 0.5 = 0.4, score_full == 0.8 * 1.0 = 0.8
- Assert: score_half <= 0.5 * score_full  (AC from ticket)

#### AC3: Non-GATHER_RESOURCE routes are unaffected

```python
def test_non_gather_routes_unaffected_by_resource_nodes():
    """RECOVER and BUY_UPGRADE routes produce same score regardless of resource_nodes."""
```
- Score RECOVER and BUY_UPGRADE with resource_nodes populated vs None
- Assert: scores are identical

#### AC4: Missing node (target_node_id not in resource_nodes) → no crash, no scaling

```python
def test_gather_route_missing_node_no_scaling():
    """GATHER_RESOURCE route with unknown target_node_id skips depletion scaling."""
```
- resource_nodes = {} (empty)
- route.target_node_id = 999
- Assert: score == AdventureRouteScorer.score(entity, route_without_node_id, resource_nodes={}).score
  (same as no-scaling path)

#### AC5: max_charges=0 guard → no division by zero

```python
def test_gather_route_zero_max_charges_no_crash():
    """GATHER_RESOURCE route with max_charges=0 does not crash (division-by-zero guard)."""
```
- node: remaining_charges=0, max_charges=0
- Assert: no exception; score is deterministic

#### AC6: resource_nodes=None → same score as current behavior

```python
def test_scorer_no_resource_nodes_backward_compatible():
    """Calling score() with resource_nodes=None produces same result as before."""
```
- Verify existing behavior unchanged when resource_nodes not provided

---

## Scoped Pytest Commands

```bash
# New test file (primary)
pytest tests/unit/domains/adventure/test_depletion_scoring.py -x -v

# Existing scoring regression
pytest tests/unit/domains/adventure/test_phase3_route_scoring.py -x -v

# Full adventure domain (smoke)
pytest tests/unit/domains/adventure/ -x -v
```

---

## Anti-Drift Test Guards

1. `test_scoring_does_not_use_hidden_world_truth` (existing) must still pass — scorer only reads `resource_nodes` when explicitly passed; it does not fetch state internally.
2. `test_route_scoring_is_deterministic` (existing) must still pass — depletion fraction is a pure computation from two integer fields.
3. All new tests must construct `ResourceNodeState` directly (not via ecology) to avoid cross-module test dependencies.
