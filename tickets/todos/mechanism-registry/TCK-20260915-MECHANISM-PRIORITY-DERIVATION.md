---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260915-MECHANISM-PRIORITY-DERIVATION
phase: open
date: 2026-09-15
tags: [architecture, documentation, schema]
---

# TCK-20260915-MECHANISM-PRIORITY-DERIVATION

## Title
Derive priority from layer frequency and computed dependent-count, and generate the per-view
dependency charts

## Status
OPEN

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

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.
