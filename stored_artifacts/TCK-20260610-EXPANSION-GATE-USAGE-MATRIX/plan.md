---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-EXPANSION-GATE-USAGE-MATRIX
artifact_type: plan
tags: [expansion, gate, usage, matrix]
---

# Plan — TCK-20260610-EXPANSION-GATE-USAGE-MATRIX

## Step 1 — Create `tests/helpers/content_usage_gate.py`

New helper module. Exports:
- `ACTIVE_IMPL_STATES: frozenset[str]`
- `GRAPH_EXEMPT_SHORTS: frozenset[str]`
- `collect_family_graph_violations(ref_graph) -> List[str]`

`collect_family_graph_violations` logic (extracted from `test_active_data_consumer.py`):
- For each `(family_key, entry)` in `CONTENT_USAGE_MATRIX.items()`:
  - Skip if `implementation_state not in ACTIVE_IMPL_STATES`
  - Compute `short = FAMILY_TO_SHORT.get(family_key.replace("/", "."))`
  - Skip if `not short or short in GRAPH_EXEMPT_SHORTS`
  - Get `family_nodes` from `ref_graph.nodes` filtered by `f"{short}:"` prefix
  - Skip if no nodes
  - Check if any are consumed (`ref_graph.is_record_used(node_id)`)
  - Append violation string if none consumed
- Return violations list

## Step 2 — Rewrite `test_expansion_gate.py`

**Module docstring** — remove:
- "Items blocked by the pre-existing CAT-REL-099 defect ..." paragraph
- "marked xfail(strict=False)" language
- Update to state all items are hard pass conditions

**Remove** imports: `re`, `Tuple`, `Dict` (from typing)
**Remove** module-level constants: `_ACTIVE_STATES`, `_FAMILIES_WITH_IMPLICIT_CONSUMERS`,
  `_KNOWN_INACTIVE_CONTENT`, `_STATE_RE`, `_ID_RE`
**Remove** the "must stay in sync" comment on the old `_ACTIVE_STATES` block

**Add** import: `from tests.helpers.content_usage_gate import collect_family_graph_violations`

**Rewrite** `test_gate_04_no_new_dead_active_data`:
- Signature: `(ref_graph)` (use fixture, no internal ref_graph construction)
- Body: call `collect_family_graph_violations(ref_graph)`, assert empty
- Updated docstring: mention ContentUsageMatrix, no YAML scanning

## Step 3 — Update `test_active_data_consumer.py`

**Add** import: `from tests.helpers.content_usage_gate import ACTIVE_IMPL_STATES, GRAPH_EXEMPT_SHORTS, collect_family_graph_violations`
**Remove** local `_ACTIVE_IMPL_STATES` and `_GRAPH_EXEMPT_SHORTS` definitions
**Replace** all uses of `_ACTIVE_IMPL_STATES` → `ACTIVE_IMPL_STATES`
**Replace** all uses of `_GRAPH_EXEMPT_SHORTS` → `GRAPH_EXEMPT_SHORTS`
**Replace** body of `test_active_families_have_graph_coverage` with call to `collect_family_graph_violations(ref_graph)`

## Files Changed

- `tests/helpers/content_usage_gate.py` (new)
- `tests/integration/content/test_expansion_gate.py` (modified)
- `tests/integration/content/test_active_data_consumer.py` (modified)
