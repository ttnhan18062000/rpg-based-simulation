---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-MECHANISM-PRIORITY-DERIVATION
artifact_type: plan
tags: [architecture, documentation, schema]
---

# Plan — TCK-20260915-MECHANISM-PRIORITY-DERIVATION

## Summary

Add transitive dependent-count + priority derivation to `tools/mechanism_registry.py`, a mermaid
chart generator (`tools/generate_mechanism_charts.py`) with 3 bounded view types plus pagination,
and derive the wiring map's existing `classDef` state coloring from the registry (the only part of
scope item 3 that's real, per investigation.md's resolved reading). No replacement of the wiring
map's own 3 diagrams.

## Step 1 — Transitive dependent-count + priority (`tools/mechanism_registry.py`)

```python
def transitive_dependents(mechanism_id: str, mechanisms_by_id: Dict[str, dict]) -> Set[str]:
    """BFS over the reverse dependency graph. Safe on a DAG (validate()'s own invariant 2
    guarantees acyclicity for the real file); explicitly re-checked here too (Step 4) rather than
    assumed, since a caller could pass an un-validated dict."""
    ...

def priority(mechanism_id, mechanisms_by_id, layers) -> int:
    """rank * len(transitive_dependents(...)). A multiply, not a two-key sort -- lets a
    heavily-depended-on higher-layer mechanism outrank a low-dependent leaf in a lower layer, per
    the ticket's own explicit design intent."""
    ...

def unverified_priority_ranking(mechanisms, layers) -> List[dict]:
    """The primary, reframed view (peer review): priority-ordered list of the currently-unverified
    mechanisms only (verified is null/absent) -- 'which one to verify next.' Each row: id, layer,
    priority, transitive_dependent_count, state."""
    ...
```

`MechanismRegistry` gains `dependents_of()` (already exists, direct) and a new
`transitive_dependents_of()` mirroring it — both computed by traversal every call, never stored,
per the Foundation ticket's own already-established rule for `depends_on` (AC #1 here is the same
rule one level up: no stored count).

## Step 2 — Chart generator (`tools/generate_mechanism_charts.py`)

Three view types (AC #4), each independently bounded (AC #5 — never emit an unreadable diagram):

1. **Single layer.** Bounded by pagination (below) since `entity` alone (43 mechanisms) already
   exceeds ~40 nodes before any edges are drawn.
2. **Ancestors-of(mechanism_id).** Bounded naturally — `transitive_dependents_of()`'s own reverse
   (ancestors = mechanisms this one depends on, transitively) is a real subgraph, typically small;
   still capped explicitly (see readability check below) in case a future mechanism has an
   unusually deep chain.
3. **Top-N by dependents (unverified-priority).** The flagship view per the reframing — the
   `unverified_priority_ranking()` mechanisms, top N (default N=25, configurable), rendered both as
   a chart and as the plain text/markdown table `MechanismRegistry`-consuming agents can read
   directly (Request Summary's own "two outputs from one registry: a text form for agents, a chart
   for humans").

**Readability threshold, enforced not documented (AC #5)**: a shared `_MAX_CHART_NODES = 40`
constant; any view whose node count would exceed it either (a) paginates (single-layer view: split
into pages of ≤40, numbered) or (b) truncates with an explicit "N more not shown, see the text
table" note (top-N view, if N itself is set above the threshold) — never silently emits an
oversized diagram. A view that would still exceed the threshold after these strategies (e.g., a
single mechanism whose ancestor chain alone is >40) fails loudly (raises/returns an error), per
AC #5's own "must fail or paginate rather than emit an unreadable diagram."

**Direction is a parameter, not a literal** — `direction: str = "BT"` on the generator's own
function signature, per peer's suggestion (investigation.md), so reversing it later is a config
change.

## Step 3 — `classDef` state derivation for the wiring map (the real scope item 3)

Small, targeted edit to `docs/brainstorm/rpg_simulation_wiring_map.html`'s three existing
diagrams: replace each node's hand-assigned `:::live`/`:::bug`/`:::gated`/`:::proposed` class
suffix with one derived from the registry's real `state` for the mechanism that node represents,
via a mapping table (`done`→`live`, `gap`/`orphan`→`bug`, `gated`→`gated`, `partial`/`skeleton`→
closest existing class, decided per node at implementation time since the wiring map's own 4-class
vocabulary doesn't map 1:1 onto the registry's 6-class one — documented inline per substitution,
not silently guessed). This is a **one-time, script-assisted edit**, not a live-regenerated file —
the wiring map's own diagrams are hand-authored prose+diagram documents, not a generated-doc
target; re-running the derivation script after this to check for drift is the ongoing discipline,
not continuous regeneration replacing the file's own authored structure.

**Not implemented in this ticket** (out of scope, confirmed): fixing
`TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS` — that's whether these diagrams render at
all, a separate, already-filed gap.

## Step 4 — Cycle-fails-loudly test (AC #6)

A deliberately invalid fixture (a real cycle, e.g. `a depends_on b`, `b depends_on a`) passed
directly to `transitive_dependents()`/`priority()`/`unverified_priority_ranking()` — proven to fail
loudly (raise, or return an explicit error marker) from *this* ticket's own code, not merely
inherited/assumed from Foundation's `validate()` (which catches the cycle at the schema-validation
layer, a different code path from this ticket's own traversal functions, which must independently
guard against infinite recursion if ever called on unvalidated data).

## Step 5 — Tests

New file `tests/unit/tools/test_mechanism_priority_derivation.py` (separate from
`test_mechanism_registry.py` — this ticket's own new derivation/chart-generation surface, not an
extension of the existing reader/validator tests):
- `test_transitive_dependents_matches_real_data` — against the real registry, asserts
  `action_pacing_readiness` has exactly 23 transitive dependents (the number this investigation
  computed and cited to peer) — a real-data regression guard, not just a fixture check.
- `test_transitive_dependents_raises_on_cycle` (AC #6) — the deliberately invalid fixture.
- `test_priority_is_rank_times_transitive_dependents` — fixture-level arithmetic check.
- `test_unverified_priority_ranking_excludes_verified_mechanisms` — fixture with one verified, one
  unverified mechanism; assert only the unverified one appears.
- `test_chart_generator_single_layer_paginates_when_over_threshold` — real case: generate the
  `entity` layer's own chart, assert it produces >1 page (43 mechanisms, threshold 40).
- `test_chart_generator_ancestors_of_produces_a_real_subgraph` — real mechanism (e.g.
  `combat_resolution`), assert its own known `depends_on` chain appears in the output.
- `test_chart_generator_never_emits_a_diagram_over_the_threshold` — the load-bearing AC #5 test:
  count nodes in every generated diagram's own mermaid source, assert none exceeds
  `_MAX_CHART_NODES`.
- `test_direction_is_a_parameter_not_hardcoded` — call the generator with `direction="TB"`, assert
  the emitted mermaid source says `flowchart TB`, not `BT`.

## Acceptance Criteria Map

| AC | Satisfied by |
|---|---|
| 1. Dependent-count computed at build time, never stored | Step 1's traversal functions, no new YAML field |
| 2. Reproducible from the registry alone | Same input, same deterministic output — no randomness in traversal/sort |
| 3. classDef derives from registry state | Step 3 |
| 4. ≥3 view types | Step 2 (single layer, ancestors-of, top-N/unverified-priority) |
| 5. No oversized diagram; fail/paginate | Step 2's readability enforcement + its dedicated test |
| 6. Cycle fails derivation loudly, proven | Step 4 + its dedicated test |

## Out of Scope (reaffirmed)

Rendering the whole 75-node graph, hand-tuning priority, sourcing per-mechanism frequency, blocking
on the census — all explicitly deferred per the ticket's own Out of Scope section. Also out of
scope, confirmed during investigation: replacing the wiring map's 3 diagrams' own topology; fixing
whether they render at all (separate filed ticket).
