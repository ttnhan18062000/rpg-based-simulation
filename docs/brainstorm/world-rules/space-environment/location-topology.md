---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Location / Topology

**Purpose/scope.** What it means for a subject to be somewhere in the simulated world: location,
containment, adjacency, connection, distance where meaningful, inside/outside, region
membership, occupancy, and movement-path possibility — stated representation-neutrally, never
committing the world to a specific coordinate/grid implementation. **Topological connection is
not the same as geometric closeness**: two locations may be geometrically close but unreachable,
or geometrically distant but connected through a valid route.

**Status.** Batch 04 (Space/Environment/Movement), first domain-facing Milestone B batch, first
draft. Candidates below originated as external-reviewer hypotheses
(`tmp/world-rule-batch-4-ext-ai.md`); each carries this session's disposition and repository
evidence, not the original wording uncritically kept.

---

## LOC-01 — A subject's location is a real, declared, representation-neutral fact

> Where a subject is in the world is a real, authoritative fact about it — not merely an
> implementation detail of how positions happen to be stored. This rule does not require, or
> forbid, any specific representation (coordinates, a graph, a hierarchy of named places); it
> only requires that "where is this subject" have one real, well-defined answer.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED, with a concrete representation kept as evidence, not as the
rule.** `EntityState.navigation.position: tuple[float, float]` and `RegionState.bounds` are this
repository's own chosen representation (grid/coordinate-based, per `movement_actions.py`'s own
comment: "GRID-BASED AUTHORITATIVE MOVEMENT"). The rule itself does not require this
representation — a different implementation using a pure connectivity graph would equally
satisfy it.

**Scenarios:** [SPC-S11](../scenarios/space-environment-batch-04.md#spc-s11) (location change ≠
identity change — already implied by ID-01's own worked list, reconfirmed here).

---

## LOC-02 — Topological connection is distinct from geometric closeness

> Two locations being geometrically close does not imply they are topologically connected
> (reachable from one another); two locations being geometrically distant does not imply they
> are topologically disconnected. Connection is its own fact, established by a route, passage, or
> declared link — not derived automatically from distance.

**Disposition: ACCEPT, with a confirmed gap this batch's own investigation found.** This is the
rule the batch instruction most explicitly required, and it is also where the clearest MISSING
finding in this whole batch lives.

**Repository evidence: PARTIAL/MISSING — this repository currently conflates the two.**
`SpatialQueryService.get_region_at(pos)` determines region containment purely by whether a
coordinate falls within a region's `bounds` — a geometric test. Checked directly: no
`adjacent_region_ids`, route, or portal field or mechanism exists anywhere in the repository
(`grep` for `portal`/`one_way`/`route_id`/`class.*Connection` on region/place state returns
nothing beyond a narrow, content-specific `AdventureRouteOption` unrelated to world topology).
Barrier-based unreachability *is* real (`LOS_OBSTRUCTED`, occupancy blocking — see LOC-04), but a
non-geometric long-distance connection (a portal, a maintained trade route treated as a
first-class shortcut) is not currently representable as anything other than "still traverse the
geometry, just faster." This is a genuine, confirmed architectural gap, not an oversight in this
write-up — recorded honestly rather than papered over.

**Scenarios:** [SPC-S01](../scenarios/space-environment-batch-04.md#spc-s01) (near but
unreachable), [SPC-S02](../scenarios/space-environment-batch-04.md#spc-s02) (far but connected).

---

## LOC-03 — Containment is a real, declared relationship

> A location being "inside" another (a place inside a region) is a real, declared fact tracked
> from both sides where the architecture supports it — not an incidental consequence of
> coordinates happening to overlap.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `PlaceState.region_id` (the back-reference) and
`RegionState.places` (the forward reference) are an explicit "dual-sided membership decision," 
per that field's own code comment — containment is a first-class, bidirectionally-tracked fact,
not merely inferred from `PlaceState.position` falling inside `RegionState.bounds`.

**Scenarios:** none newly traced; confirmed by direct code inspection rather than requiring a
scenario.

---

## LOC-04 — Occupancy is exclusive per location where declared

> Where a location's occupancy is declared exclusive (at most one occupant, or a bounded set),
> that exclusivity is real and enforced — not a convention other systems merely happen to
> respect.

**Disposition: ACCEPT.** Reuses Batch 01's ID-05-adjacent evidence and Batch 02's REACH-01
evidence rather than re-deriving occupancy from scratch.

**Repository evidence: SUPPORTED.** `SpatialQueryService.get_occupancy_map()` and
`LegalityServiceV2.verify_occupancy()` (reused from Batch 02) enforce real occupancy exclusivity
at the tile level — a real structural check, not an assumption.

**Scenarios:** [SPC-S06](../scenarios/space-environment-batch-04.md#spc-s06) (capable but
blocked by an occupancy/obstacle conflict).

---

## LOC-05 — Path possibility is a topology fact, distinct from movement's own checks

> Whether a valid path exists between two locations is a fact about the world's topology,
> independent of whether a specific subject is currently authorized, capable, or resourced to
> traverse it. Movement (`movement-navigation.md`) checks capability/authority/cost/reach
> *given* that a path exists; Location/Topology states whether one exists at all.

**Disposition: ACCEPT.** This is the explicit boundary line between this family and Movement,
stated so neither family's future author absorbs the other's job — the same pattern AUTH-04
established between Authority and Reach.

**Repository evidence: SUPPORTED.** `NavigationSystem.get_next_step()` (path resolution) is a
fully separate concern from `MovementSystem.resolve_move()`'s stamina/readiness/environment
checks — a path can exist (topology says yes) while a specific movement attempt still fails for
unrelated capability/cost reasons, and vice versa.

**Scenarios:** [SPC-S07](../scenarios/space-environment-batch-04.md#spc-s07) (destination exists
but no path).

---

## LOC-06 — Directional connections are a legitimate topology shape

> A connection between two locations is not required to be symmetric. `A → B` being possible does
> not imply `B → A` is possible — direction is a real property a connection may have, not an
> assumption the world defaults away from.

**Disposition: ACCEPT.**

**Repository evidence: MISSING, confirmed directly.** No one-way connection, portal, or
directional-route mechanism exists anywhere in this repository — checked directly, nothing
beyond symmetric geometric adjacency exists today. This rule states the semantic possibility
ahead of any mechanism, consistent with this Catalog's established practice (e.g., ID-03's
exception slot) of stating a boundary before a future domain fills it, rather than waiting for
the mechanism to justify the rule after the fact.

**Scenarios:** [SPC-S03](../scenarios/space-environment-batch-04.md#spc-s03) (one-way passage).

---

## Cross-domain links recorded here

- LOC-01 → Identity (ID-01, location as ordinary state that doesn't affect identity)
- LOC-02 → Reach (REACH-01/REACH-02, the same "connection ≠ distance" discipline restated
  spatially), Groups/organizations & institutions (trade routes as a future non-geometric
  connection candidate)
- LOC-04 → Reach (REACH-01, occupancy reused directly)
- LOC-05 → Movement/Navigation (`movement-navigation.md`, the explicit family boundary)
- LOC-06 → Magic/supernatural (portals as the most plausible future domain to fill this gap)

## Open questions carried forward

1. LOC-02's confirmed gap (topology currently = geometry, no route/portal mechanism) is the most
   load-bearing MISSING finding in this batch — it affects every future domain that wants a
   non-geometric spatial shortcut (trade routes, sea lanes, portals). Not designed here, per the
   batch instruction's own non-goal ("do not commit the world to a specific coordinate/grid
   representation" — designing the fix would require exactly that commitment prematurely).
2. LOC-06's directional-connection gap is the same underlying absence as LOC-02's — recorded
   once conceptually, tracked as two rules because they're two distinct semantic claims
   (existence of non-geometric connection; directionality of a connection), even though one
   future mechanism would likely resolve both together.
