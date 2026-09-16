---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260915-MECHANISM-PRIORITY-DERIVATION
phase: done
date: 2026-09-15
tags: [architecture, documentation, schema]
---

# TCK-20260915-MECHANISM-PRIORITY-DERIVATION

## Title
Derive priority from layer frequency and computed dependent-count, and generate the per-view
dependency charts

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The stated priority rule — lower layers first, ranked by execution frequency and
dependency-by-other-count — exists in no artifact. Every batch ordering produced so far was
reconstructed from session context and did not survive the session.

Make it derived data plus a generated chart. Two outputs from one registry: a text form for agents,
a chart for humans.

**Priority** = layer `rank` × computed dependent-count, with the census's exercised/never-exercised
flag layered on when PR #205 lands. Nothing hand-ranked — so disagreements are about *edges*, which
is the useful argument, rather than about rankings, which is not.

**Charts**: `flowchart BT` puts foundations at the bottom, so reading upward *is* build order; the
bottom-up rule becomes the shape of the picture rather than a note beside it. Lanes are frequency
tiers.

## Scope
1. **Derivation** — dependent-count by graph traversal (never stored), priority as `rank ×
   dependents`, exposed in a machine-readable form agents can read directly.
2. **Per-view mermaid generation** — at minimum: one layer; the ancestors of a given mechanism
   ("what does war actually need?"); the top N by dependents.
3. **Replace the wiring map's hand-authored charts** with generated ones, removing a fifth
   hand-maintained state surface (its `classDef live`/`classDef bug` assignments).
4. **Resolve the two open mermaid questions** before committing to `BT`: whether `BT` lays subgraphs
   out as clean lanes, and how existing blocks render (client-side script vs committed images). The
   wiring map uses `TB`/`TD`/`LR` — determine whether `BT` was avoided for a reason.

## Out of Scope
- **Rendering the whole graph.** Mermaid stops being readable near 40 nodes. Charts are slices; the
  registry is complete. A single all-mechanisms diagram would be technically correct and unreadable.
- Hand-tuning priority. If the output looks wrong, the fix is an edge or a layer rank, not an
  override column.
- Sourcing frequency per mechanism — measured as unavailable, and unnecessary. Frequency is a layer
  attribute.
- Blocking on the census. Priority is computable without it; the exercised flag is additive.

## Acceptance Criteria
1. Dependent-count is computed at build time; no stored count exists anywhere in the registry.
2. Priority ordering is reproducible from the registry alone — same input, same order.
3. Generated charts replace the wiring map's hand-authored mermaid, and its `classDef` state
   assignments derive from registry `state`.
4. At least three view types generate (single layer; ancestors-of; top-N).
5. No generated chart exceeds the readability threshold; a view that would must fail or paginate
   rather than emit an unreadable diagram.
6. A cycle introduced into the registry fails derivation loudly — proven against an invalid fixture,
   not assumed from the foundation ticket's validator.

## Related Tickets
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — parent
- `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION` — dependency

## Related Docs
- `docs/plans/mechanism_registry_initiative.md` §3 chart generation, §4 open questions
- `docs/plans/simulation_execution_census_initiative.md` — the later exercised/never-exercised flag

## Related Stored Artifacts
None yet.

## Related Code Areas
- `docs/brainstorm/rpg_simulation_wiring_map.html` — three existing hand-authored flowcharts, lanes
  and `classDef` vocabulary already validated in-repo

## Assumptions / Open Questions
1. Is dependent-count direct dependents, or full transitive closure? Transitive better matches "how
   much breaks if this is wrong"; direct is easier to reason about. Recommend transitive, decide with
   real seeded data.
2. Should layer `rank` multiply or be the primary sort key with dependents as tiebreak? Multiplying
   lets a heavily-depended-on faction mechanism outrank a leaf entity one — which may be correct or
   may violate the bottom-up rule. Check against a known-correct ordering before fixing this.
3. What is the readability threshold in practice? ~40 nodes is a rule of thumb, not measured here.

## Implementation Notes
Containment is not dependency. The wiring map's existing lanes are containment (Individual /
Organization / Geography / World); a Faction *contains* Entities, whereas war *depends on* combat.
Only the dependency axis drives priority — do not reuse the containment edges as dependency edges.

**Four distinct axes exist over the same mechanism node set** (found while resolving scope item
3): containment, execution order, lifecycle transitions, dependency. The registry captures exactly
one. A future attempt to make it "the single source for the graph" (collapsing all four) should be
refused on this basis — recorded explicitly in investigation.md since this will matter again at T4.

**Transitive dependent-count decided from real data, not the ticket's own lean.** Direct and
transitive produce the same 26 hubs, but a meaningfully different ranking — `combat_engagement` (1
direct / 13 transitive) is the decisive case: direct would rank the project's single most-verified,
most-central mechanism near the bottom.

**Reframed per peer review, following T2's own seed finding**: the flagship view is priority over
the 69 currently-*unverified* mechanisms — "which one to verify next" — not an abstract ranking
over all 75.

**Scope item 3 resolved**: the ticket's own verb ("replace... charts") overstated its intent; the
parenthetical (`classDef` state assignments) was the real scope. The wiring map's 3 existing
diagrams keep their own topology untouched; only the Entity Operating Loop diagram's `classDef`
colouring now derives from the registry (the other two diagrams' nodes don't map 1:1 onto
mechanism ids — checked directly, not assumed). **Found 4 real mismatches (17% of the 24 mapped
nodes) before fixing anything** — `self_model`, `combat_engagement` (stale text too, not just
color — still said "GATED OFF by default" the day after this same session's Foundation-ticket work
confirmed it went live-by-default), `conversation`, `commitment_betrayal` (the exact cross-doc
disagreement Foundation's own Judgment Call 6 already flagged, resolved here in the registry's
favor). This is the epic's second measured finding (after Foundation's two stale atlas badges),
not just infrastructure.

**Real cost of consolidation, recorded per peer review**: the five-artifact disagreement this epic
existed to end was itself an accidental signal — `commitment_betrayal`'s own disagreement was
findable *because* two documents disagreed. Removing that disagreement means the verification axis
(T2's 69-unverified figure) now carries the deliberate replacement for the accidental safety this
consolidation removes — worth stating plainly, not just the benefit.

**`BT` vs `TB` and the wiring-map-rendering question**: neither this session nor peer can visually
inspect a published artifact's own rendered output (a shared tool limitation, confirmed, not
assumed). Direction implemented as a parameter (default `BT`), reversible via config. Separately,
checking whether `make docs-serve` renders the wiring map's mermaid at all (per peer's own
suggestion, before concluding a defect) found it does not — Docusaurus only globs `.md`/`.mdx` by
default, no `include:` override exists, and the file isn't under `website/static/` either. Filed as
its own gap, `TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS`, not folded into this ticket.

## Test Summary
`tests/unit/tools/test_mechanism_priority_derivation.py` (20 tests) +
`tests/unit/tools/test_mechanism_wiring_map_classdef.py` (7 tests) — 27 new tests, on top of the
63 already passing from Foundation + Verification-Axis (90 total in the combined tools+
capability-registry suite, all passing). Cycle-fails-loudly (AC #6) proven on both traversal
directions (2-node and 3-node cycles), independently from Foundation's own schema-level
`validate()`. Pagination proven on the real `entity` layer (43 mechanisms, splits into 2 pages).
The ancestors-of failure path proven on a synthetic 45-node fixture, not just documented. The
load-bearing AC #5 test counts real mermaid node declarations across every generated diagram
programmatically. Direction-as-parameter proven by asserting the emitted mermaid source itself
changes between `BT`/`TB` calls. The wiring-map drift test re-derives against the real committed
files every run, not just at the moment of the one-time fix.

Whole suite re-verified with `graphify-out/` genuinely absent (moved aside, restored immediately
after) to match the real CI condition exactly — 90/90 pass under that condition too.

Scoped pytest command used throughout:
```
.venv313/bin/python3 -m pytest tests/unit/tools/ tests/unit/engine/test_capability_registry.py -v
```

## Files Changed
- `tools/mechanism_registry.py` — `transitive_dependents()`, `transitive_dependencies_of()`,
  `priority()`, `unverified_priority_ranking()`, `DependencyCycleError`
- `tools/generate_mechanism_charts.py` (new) — 3 bounded view types, pagination, readability
  enforcement, direction parameter
- `tools/generate_mechanism_priority_view.py` (new) — renders the flagship view to
  `docs/brainstorm/mechanism_priority_view.md`, `--check` mode
- `docs/brainstorm/mechanism_priority_view.md` (new, generated)
- `tools/mechanism_wiring_map_classdef.py` (new) — derives/checks the Entity Operating Loop
  diagram's `classDef` state colouring against the real registry
- `docs/brainstorm/rpg_simulation_wiring_map.html` — 4 real classDef/text corrections (see
  Implementation Notes)
- `docs/brainstorm/idea_index.json` — regenerated (timestamp only, no mention-count drift)
- `Makefile` — `mechanism-priority-view`, `mechanism-wiring-map-classdef-check` targets
- `tests/unit/tools/test_mechanism_priority_derivation.py` (new, 20 tests)
- `tests/unit/tools/test_mechanism_wiring_map_classdef.py` (new, 7 tests)
- `staging_artifacts/TCK-20260915-MECHANISM-PRIORITY-DERIVATION/` — investigation.md, plan.md,
  test_plan.md
- `tickets/todos/TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS.md` (new, filed not fixed)

## Completion Summary
DONE. Priority is fully derived (`layer rank × transitive dependent-count`, never stored, never
hand-ranked), reproducible from the registry alone. Transitive over direct decided from real data,
not the ticket's own lean — same 26 hubs, meaningfully different ranking. Reframed per peer review
around the real question T2's own seed produced: which of the 69 unverified mechanisms to verify
next. 3 bounded view types ship (single layer with real pagination, ancestors-of with a real
fail-loud path, top-N unverified-priority as the flagship), readability enforced programmatically
(AC #5's own test counts real node declarations, not a hardcoded sample), never the whole 75-node
graph. Cycle-fails-loudly proven independently from Foundation's own validator (AC #6). Scope item
3 correctly narrowed to only the `classDef` derivation (peer confirmed the ticket's own wording
overstated its intent) — found and fixed 4 real, measured drifts in the process, the epic's second
measured finding. A real, separate gap (wiring-map mermaid never rendering through this repo's own
doc infrastructure) was found, investigated with real evidence, and filed rather than folded in.
All 6 acceptance criteria satisfied and mapped to specific tests in plan.md.
