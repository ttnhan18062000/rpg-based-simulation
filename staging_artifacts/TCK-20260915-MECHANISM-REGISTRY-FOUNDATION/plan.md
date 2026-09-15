---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-MECHANISM-REGISTRY-FOUNDATION
artifact_type: plan
tags: [architecture, documentation, schema]
---

# Plan — TCK-20260915-MECHANISM-REGISTRY-FOUNDATION

## Summary

Build `docs/brainstorm/mechanisms.yaml` (layers block + 73 hand-authored mechanisms, per
investigation.md's Real Mechanism Candidate List), a validator enforcing the four invariants, a
`make` target, and a report-only graphify cross-check. Fix two stale atlas/wiring-map badges found
during investigation before seeding (seeding known-wrong data would propagate the error into every
future consumer at once). Seed all 73 — decided by peer review 2026-09-16, not curated toward the
ticket's own 30–50 estimate.

## Step 1 — Fix the two stale source badges (done, ahead of this plan)

Already completed as part of investigation follow-up, both independently re-verified against real
source before editing:
- `docs/brainstorm/rpg_feature_atlas.html`: "XP, Attribute Points, Breakthrough & Mastery" card
  badge `gap`→`done`; "Race-Keyed Evolution Chains" card's `orphan` badge removed (the duplicate
  file it cited, `progression/evolution.py`, was deleted by `TCK-20260824-WIRE-ORPHANED-MECHANISMS`).
- `docs/brainstorm/rpg_simulation_wiring_map.html`: `BRK` flowchart node de-styled from `:::bug`
  to plain (added to the `live` class list); Buildup table's Breakthrough Bonuses row badge
  `bug`→`live`.
- `docs/brainstorm/simulation_capabilities.html`: "Deeper Mastery & Breakthroughs" card
  `tier: built`→`tier: live`, plain-language desc corrected — per the standing rule that any atlas
  edit with gameplay-visible impact mirrors into this page the same turn.

Regression check before moving on: `make brainstorm-idea-index` must still succeed (idea count
unchanged at 68, no `SystemExit` from the generator's own JSON-structure assertions) — proves the
`id="card-sections-data"` JSON block's structure wasn't disturbed by the badge edits.

## Step 2 — `docs/brainstorm/mechanisms.yaml`

Shape (ticket's own Request Summary — no `verified` field, that's child ticket 2):

```yaml
layers:
  entity:  { cadence: per_tick, rank: 1 }
  group:   { cadence: per_tick, rank: 2 }
  faction: { cadence: daily,    rank: 3 }
  region:  { cadence: slow,     rank: 4 }
  world:   { cadence: rare,     rank: 5 }

mechanisms:
  - id: combat_resolution
    layer: entity
    depends_on: [tactical_decision, combat_engagement]
    state: done
  # ... 72 more, transcribed directly from investigation.md's Real Mechanism Candidate List tables
```

All 73 rows transcribed verbatim from investigation.md's tables (ids, layers, depends_on, states
already finalized there, including every judgment call already made and recorded — no new
judgment calls introduced at authoring time). `race_collective_force` and `settlement_capacity_axis`
get `layer: faction` per Judgment Call 8, with a YAML comment marking both as a placeholder
layer assignment (not a citation-backed one) so a future layer-design ticket can find it flagged
rather than silently decided, matching investigation.md's Anti-Drift Hazards instruction.

A short header comment block states: source (atlas + wiring map, 2026-09-16), the containment vs.
dependency vs. execution-order distinction (so a future hand-editor doesn't populate `depends_on`
from wiring-map sequence arrows), and a one-line pointer to investigation.md for full provenance.

## Step 3 — Reader + validator module

New file `tools/mechanism_registry.py` (repo-root `tools/`, alongside `tools/tag_registry.py` /
`tools/layer_registry.py` — the other hand-authored, validated, non-append-only registry-adjacent
tools already live there; not `src/engine/` since this is authoring/tracking tooling, not a
runtime engine dependency, unlike `capability.py`).

Pattern imitated from `src/engine/capability.py` (confirmed precedent in investigation.md), adapted
for this registry's extra invariants:

```python
VALID_STATES = frozenset({"done", "partial", "gap", "orphan", "gated", "skeleton"})

class MechanismRegistry:
    def __init__(self, registry_path=_DEFAULT_PATH):
        data = yaml.safe_load(open(registry_path))
        self.layers = data.get("layers", {})
        self._mechanisms = {m["id"]: m for m in data.get("mechanisms", [])}

    def get_state(self, mechanism_id) -> Optional[str]: ...
    def all_mechanisms(self) -> List[dict]: ...
    def dependents_of(self, mechanism_id) -> List[str]:
        """Computed by traversal over depends_on -- never stored (AC #2)."""
        ...

def validate(data: dict) -> List[str]:
    """Returns a list of human-readable error strings, empty if valid. Never raises for a
    business-logic violation -- only for a structurally malformed file (missing top-level keys)."""
    errors = []
    # invariant 1: every depends_on id resolves
    # invariant 2: dependency graph is acyclic (DFS with a visiting-set, not pairwise-only --
    #              test_plan.md's fixture 5 explicitly requires catching a 3-node cycle too)
    # invariant 3: every layer is declared in layers block
    # invariant 4: every state in VALID_STATES
    return errors
```

`validate()` returns a list (not raise/bool) so the CLI entrypoint (Step 4) can print every
violation in one run rather than stopping at the first, matching the ticket's own Implementation
Notes ("build the failure loud").

A `__main__` block: `python3 tools/mechanism_registry.py` loads the real file, runs `validate()`,
prints each error, exits 1 if any, exits 0 (with an "OK, N mechanisms" line) otherwise.

## Step 4 — `make` target

```makefile
mechanism-registry-validate: ## Validate docs/brainstorm/mechanisms.yaml against its 4 invariants
	$(PYTHON3) tools/mechanism_registry.py
```

Registered alongside `brainstorm-idea-index` (Scope item 4), same file, adjacent lines.

## Step 5 — Graphify cross-check (report-only)

Per investigation.md's Graphify Cross-Check Feasibility section: a bare "does any path exist"
check is not a reliable detector at this codebase's scale (confirmed by direct testing — unrelated
services route through near-universal hub types within a few hops). Scope item 5 only asks for a
report-only flag, so this step ships a real, deliberately-conservative version rather than the
full hub-exclusion-tuned tool investigation.md sketches as future work:

New file `tools/mechanism_registry_graphify_check.py`:
- Loads `graphify-out/graph.json` directly (not `graphify path` per edge — 105k edges is too many
  for repeated subprocess calls, per investigation.md).
- For each `depends_on` edge in `mechanisms.yaml`, attempts a bounded-hop (≤3) BFS between the two
  mechanism ids' nearest matching graph nodes (best-effort string match against node names --
  mechanism ids are snake_case registry ids, not code symbol names, so this is inherently
  approximate; a mechanism id with no plausible node match is reported as `no_match`, not `FAIL`).
- Only counts edges whose `relation` implies a real call/import/use (`uses`, `calls`, `imports`,
  `references`) — never `contains`, per investigation.md's finding that `contains` produces false
  positives.
- Reports three buckets: `supported` (real path found), `suspicious` (no path found within the
  bound), `no_match` (couldn't even locate one of the two ids in the graph — not itself a defect
  signal, since ids are hand-authored and graph nodes are code symbols).
- **Never fails the build.** Exits 0 always; prints a report. Wired as informational output in the
  `make mechanism-registry-validate` target's own run, appended after the hard-invariant
  `validate()` call, clearly separated so a reader can't mistake `suspicious`/`no_match` lines for
  a validation failure.

This is intentionally the conservative, no-hub-exclusion-list version — investigation.md's
`suggested future refinement (hub-node exclusion via community-detection or degree-count)` is
explicitly left for a later pass if the `suspicious` bucket proves too noisy in practice. Shipping
something real and conservative beats not shipping the report-only check Scope item 5 asks for.

## Step 6 — Tests

New file `tests/unit/tools/test_mechanism_registry.py`, following test_plan.md's 11 cases exactly:
existence/parses, layers+mechanisms shape (AC #2/#3), the four invalid-fixture validator tests (one
invariant violated per fixture, never two at once — test_plan.md's own Anti-Drift Test Guard), the
valid-fixture happy-path canary (using real seeded ids, not synthetic `a`/`b`/`c`), reader-class
accessor tests mirroring `test_capability_registry.py`'s own shape, the `make`-target subprocess
test (against a `tmp_path` copy with an injected defect, never the real committed file), and the
graphify cross-check's never-fails-the-build test.

## Acceptance Criteria Map

| AC | Satisfied by |
|---|---|
| 1. Registry exists, valid, seeded with real set | Step 2 + `test_registry_yaml_exists`, `test_registry_seed_meets_expected_scale` |
| 2. `depends_on` only hand-authored edge, no stored dependent-count | Step 2 (no such field in the YAML shape) + `test_registry_has_layers_and_mechanisms_blocks` + `MechanismRegistry.dependents_of()` computed, not stored |
| 3. Frequency only on layers | Step 2 shape + same test |
| 4. Validator fails on each of 4 invariants via broken fixtures | Step 3 + the four invalid-fixture tests |
| 5. `make` target regenerates/validates with no manual steps | Step 4 + `test_make_target_validates_registry` |

## Out of Scope (reaffirmed, not touched by this plan)

`verified` block, priority/chart derivation, making any artifact read from this file, auto-deriving
`depends_on` from code — all explicitly deferred to child tickets 2–4 per the ticket's own Out of
Scope section.

## Open Item Carried Forward (not blocking this ticket)

investigation.md Risk 2: `race_collective_force` / `settlement_capacity_axis` have no clean layer
home in the 5-layer scheme; both seeded under `faction` with an explicit YAML comment flagging the
placement as a placeholder guess, not a citation-backed decision. A future layer-design ticket may
revisit this; not blocking Foundation's own acceptance criteria.
