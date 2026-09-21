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

## LOC-01 — A subject's authoritative spatial state must be unambiguous according to its declared spatial model

> A simulated subject's authoritative spatial state must be unambiguous according to its
> declared spatial model. This does not require every subject to have exactly one point-like
> location: a declared spatial model may represent a point location, an area/extent, a
> containment relationship, an in-transit state, or multiple occupied cells/areas where valid —
> none of these violate this rule, provided whichever model is declared resolves to one
> unambiguous answer for that subject.

**Disposition: ACCEPT, refined 2026-09-21 — removed the implicit assumption that every subject
has exactly one point-like location.** The original wording ("one real, well-defined answer")
was already representation-neutral about *how* a location is stored, but still read as though
every subject's spatial state must ultimately resolve to a single point. That's too narrow: a
large place, a multi-tile structure, or a subject mid-transit between two locations are all
legitimate spatial states that aren't reducible to one point without loss — the rule now
requires unambiguity *according to whatever spatial model is declared*, not point-likeness
specifically.

**Repository evidence: SUPPORTED for the point-location case; SUPPORTED for area/extent as
well, confirmed directly.** `EntityState.navigation.position: tuple[float, float]` is this
repository's point-location representation for entities (grid/coordinate-based, per
`movement_actions.py`'s own comment: "GRID-BASED AUTHORITATIVE MOVEMENT"). `PlaceState.
footprint: Optional[tuple[int, int, int, int]]` ("Sub-bounds, multi-tile CITY-kind only")
confirms an area/extent spatial model already exists for at least one kind of subject —
`PlaceKind.CITY` — without needing to be reduced to its single `position` point. Both are real,
coexisting spatial models in the same repository, exactly as the refined rule anticipates.

**Scenarios:** [SPC-S11](../scenarios/space-environment-batch-04.md#spc-s11) (location change ≠
identity change — already implied by ID-01's own worked list, reconfirmed here),
[SPC-S14](../scenarios/space-environment-batch-04.md#spc-s14) (added 2026-09-21 — spatial
extent, a subject occupying more than one spatial unit with coherent authoritative state).

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

## LOC-03 — Containment is a real, authoritative relationship

> A location being "inside" another (a place inside a region) is a real, declared, authoritative
> fact — not an incidental consequence of coordinates happening to overlap. This rule does not
> require any particular storage shape (bidirectional references, a single forward pointer, a
> derived index) — only that the containment fact itself be real and queryable, however it is
> stored.

**Disposition: ACCEPT, refined 2026-09-21 — removed the implementation-specific "tracked
bidirectionally" requirement.** The original wording cited this repository's own dual-sided
storage choice as though it were part of the rule itself. It isn't: a future mechanism that
derives containment from a single forward reference, or from a spatial index, would satisfy
this rule exactly as well as bidirectional storage does — what matters semantically is that
containment is a real, authoritative fact, not which storage shape realizes it.

**Repository evidence: SUPPORTED, now read as evidence of one storage choice rather than as the
rule's own requirement.** `PlaceState.region_id` (the back-reference) and `RegionState.places`
(the forward reference) are this repository's own dual-sided storage choice, per that field's
own code comment — real evidence that containment is authoritative here, not proof that
bidirectional storage is what the rule demands.

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

## LOC-05 — Route/path accessibility is semantically distinct from movement capability, authority, reach, and cost

> Route/path accessibility is semantically distinct from movement capability, authority, reach,
> and cost, and may be derived from topology plus current world conditions — it is not
> necessarily a stored topology fact in its own right. This allows a route to persist as a
> topology fact while becoming currently inaccessible (a bridge collapses; a gate closes) without
> that changing the underlying topological connection concept: the connection still exists,
> current conditions have made it temporarily unusable.

**Disposition: ACCEPT, refined 2026-09-21 — no longer requires path accessibility to be a
stored fact.** The original wording ("a fact about the world's topology... states whether one
exists at all") read as though accessibility itself must be a durable, stored property. That's
too strong: accessibility is better understood as *derived* — from the underlying topological
connection plus whatever current conditions (obstruction, collapse, closure) happen to apply —
which is exactly what lets a route's persistence and its current usability vary independently.
The explicit boundary line between this family and Movement is unchanged: Movement
(`movement-navigation.md`) checks capability/authority/cost/reach *given* whatever
Location/Topology's own derivation of accessibility currently says.

**Repository evidence: SUPPORTED, and this refinement is confirmed by a real distinction already
present in the repository.** `LegalityServiceV2`'s occupancy/path checks distinguish static,
permanent blockage (`PATH_NOT_FOUND`, from `WALL`/`blocked_tiles` terrain) from dynamic,
potentially-temporary blockage (`BUILDING_OBSTRUCTION`, from a building occupying a tile — real
evidence that an obstruction can exist independent of the underlying terrain/topology, and can
in principle be removed without the topology itself changing). `NavigationSystem.
get_next_step()` (path resolution) remains a fully separate concern from `MovementSystem.
resolve_move()`'s stamina/readiness/environment checks — a path can exist (topology says yes)
while a specific movement attempt still fails for unrelated capability/cost reasons, and vice
versa.

**Scenarios:** [SPC-S07](../scenarios/space-environment-batch-04.md#spc-s07) (destination exists
but no path), [SPC-S15](../scenarios/space-environment-batch-04.md#spc-s15) (added 2026-09-21 —
a persistent route with a temporary blockage, distinguishing topology persistence from current
accessibility).

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

## LOC-07 — Producing a topology change does not make a domain the owner of topology state

> A later domain may create, control, destroy, maintain, or use a spatial connection (Magic
> creates a portal; an Organization maintains a road; War destroys a bridge) without that domain
> becoming the canonical owner of spatial connectivity itself. This is OWN-01/OWN-02's discipline
> (one authoritative source of truth; participation ≠ ownership) applied to topology
> specifically: topology — which connections exist, and their current state — remains owned by
> Location/Topology (or whichever single mechanism this family's own future design assigns);
> other domains act as producers or consumers of topology *change*, never as owners of the
> underlying connectivity fact.

**Disposition: ACCEPT — added 2026-09-21, per follow-up review.** Added because the original
draft's own "Deferred Semantics"/cross-domain framing (LOC-02/LOC-06's gaps "deferred to Magic/
supernatural" and "Groups/organizations & institutions") read as though whichever domain
eventually builds a route/portal mechanism would also become that connection's canonical owner.
That conflates *who produces or uses* a topology change with *who owns the resulting
authoritative fact* — exactly the OWN-01/OWN-02 distinction this Catalog already established
generally, now stated for topology specifically so it isn't accidentally lost when LOC-02/
LOC-06's gap is eventually filled.

**Repository evidence:** not independently gathered — this rule states a boundary in advance of
the mechanism LOC-02/LOC-06 found missing; there is nothing to check it against yet, which is
the correct, honest state for a rule stated ahead of its own future mechanism (matching LOC-06's
own established pattern).

**Scenarios:** none yet; this rule exists to guide whichever future batch (Magic/supernatural,
Places, Groups/organizations & institutions) actually builds a connection mechanism, so that
mechanism's own design doesn't have to re-derive this boundary.

---

## Cross-domain links recorded here

- LOC-01 → Identity (ID-01, location as ordinary state that doesn't affect identity)
- LOC-02 → Reach (REACH-01/REACH-02, the same "connection ≠ distance" discipline restated
  spatially). **Corrected 2026-09-21:** Magic/supernatural and Groups/organizations &
  institutions are recorded as plausible future *producers/consumers* of a route/portal
  mechanism (per LOC-07), not as the mechanism's canonical *owner* — that distinction matters
  and was previously blurred.
- LOC-04 → Reach (REACH-01, occupancy reused directly)
- LOC-05 → Movement/Navigation (`movement-navigation.md`, the explicit family boundary)
- LOC-06 → **Corrected 2026-09-21:** Magic/supernatural is a plausible future *producer* of a
  portal (per LOC-07), not the gap's canonical owner — the missing general mechanism is
  primarily a Space/Movement capability gap regardless of which domain first exercises it.
- LOC-07 → State Ownership (OWN-01/OWN-02, directly reused), every future domain that will ever
  create/control/destroy/maintain/use a spatial connection

## Open questions carried forward

1. LOC-02's confirmed gap (topology currently = geometry, no route/portal mechanism) is the most
   load-bearing MISSING finding in this batch — it affects every future domain that wants a
   non-geometric spatial shortcut (trade routes, sea lanes, portals). Not designed here, per the
   batch instruction's own non-goal ("do not commit the world to a specific coordinate/grid
   representation" — designing the fix would require exactly that commitment prematurely).
   **Treated primarily as a Space/Movement capability gap** (per LOC-07), not as a gap owned by
   whichever domain eventually produces or consumes a connection.
2. LOC-06's directional-connection gap is the same underlying absence as LOC-02's — recorded
   once conceptually, tracked as two rules because they're two distinct semantic claims
   (existence of non-geometric connection; directionality of a connection), even though one
   future mechanism would likely resolve both together. Same ownership correction applies.
3. **Added 2026-09-21.** LOC-07 states the producer/owner distinction in advance; it does not
   decide which single mechanism will eventually own topology state once LOC-02/LOC-06's gap is
   filled — that remains for whichever future batch actually builds it.
