---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Space / Environment / Movement (Batch 04)

**Purpose/scope.** Fifteen scenarios used to pressure-test the Location/Topology, Environment,
and Movement/Navigation rule families in `space-environment/location-topology.md`,
`space-environment/environment.md`, and `space-environment/movement-navigation.md`. SPC-S01–S12
are the original seed set (`tmp/world-rule-batch-4-ext-ai.md`), covering all ten required probes
(near but unreachable, far but connected, one-way passage, enter hazardous environment, leave
hazardous environment, capable but blocked, destination exists but no path, movement has cost
but still fails, teleport/supernatural travel boundary, environment descriptive but causally
inert) plus the two explicit cross-batch checks not otherwise covered (location change ≠
identity change; historical presence at a place ≠ current presence/reach). SPC-S13–S15 are a
follow-up expansion (`tmp/world-rule-batch-4-followup-ext-ai.md`), added to directly challenge
the refined ENV-02, LOC-01, and LOC-05 respectively.

Scoring uses the same vocabulary as prior batches: **covered** / **partially covered** /
**blocked** / **revealed missing rule** / **revealed contradiction**, against current
repository behavior, not the ideal design.

---

## SPC-S01 — Near but unreachable

Two entities occupy geometrically close tiles, but a wall or chasm separates them — direct
interaction is unavailable despite the short distance.

- **Rules invoked:** LOC-02 (topological connection ≠ geometric closeness), MOV-06 (spatial
  reach instantiates foundational Reach).
- **Result: covered.** `LOS_OBSTRUCTED` (reused from Batch 02's REACH-01) confirms geometric
  proximity alone does not establish reach or connection — the obstruction is a real, structural
  rejection.

## SPC-S02 — Far but connected

Two geometrically distant locations have a valid route between them (in this repository's
current implementation, a traversable path through open terrain); travel between them remains
possible despite the distance.

- **Rules invoked:** LOC-02 (the other direction of the same rule).
- **Result: partially covered.** Distance-independent traversability is confirmed for ordinary
  geometric paths (`NavigationSystem.get_next_step()` will route across arbitrary distance
  given open terrain) — but this repository has no non-geometric "connection" (a portal, a
  privileged route) that would let two distant points be connected *faster or differently* than
  raw distance implies. The rule's positive claim (distant-but-connected is possible) holds only
  in the weak "nothing prevents a long walk" sense, not the strong "genuinely non-geometric
  shortcut" sense LOC-02 also anticipates — recorded as partial, matching LOC-02's own confirmed
  gap.

## SPC-S03 — One-way passage

A hypothetical connection allows movement from A to B but not from B to A.

- **Rules invoked:** LOC-06 (directional connections are a legitimate topology shape).
- **Result: blocked.** No one-way or directional connection mechanism exists anywhere in this
  repository — confirmed by direct search. LOC-06 states the semantic possibility; this
  scenario cannot progress past confirming the mechanism's absence, which is the correct,
  honest result for a deliberately-stated-ahead-of-mechanism rule (matching LOC-06's own
  disposition).

## SPC-S04 — Enter hazardous environment

An entity moves into a region with a nonzero `hazard_level`. Exposure becomes a real fact; a
downstream HP consequence becomes possible.

- **Rules invoked:** ENV-02 (occupying/traversing creates exposure), ENV-03 (environment
  establishes exposure, doesn't own the consequence).
- **Result: covered.** `WorldDynamicsSystem.resolve_dynamics()` calls `EnvironmentService.
  calculate_hazard_drain()` for every entity in a hazardous region every tick; the returned
  amount is committed via a `CombatUpdate`, not by Environment itself — both halves of ENV-02/
  ENV-03 confirmed in one mechanism.

## SPC-S05 — Leave hazardous environment

An entity exits a hazardous region. Direct exposure ends immediately; any HP already lost
remains lost (the previously-acquired consequence persists after exposure ends).

- **Rules invoked:** ENV-03 (environment vs. downstream state ownership).
- **Result: covered.** `calculate_hazard_drain()` is only ever called for the region the entity
  currently occupies — once the entity's position resolves outside the hazardous region's
  bounds, no further drain is calculated. The HP already lost is Life/Body-owned state
  (`CombatUpdate.hp_delta`, already committed) and does not un-commit itself; Environment never
  held any authority over it to begin with, so there is nothing for Environment to "release" on
  exit.

## SPC-S06 — Capable but blocked

An entity that can normally move has a geometrically valid path to its destination, but a
current obstacle (occupancy conflict, congestion) blocks passage.

- **Rules invoked:** MOV-01 (movement's constituent facts are distinct), MOV-02 (movement is a
  real transition), MOV-03 (attempt ≠ guaranteed arrival), LOC-04 (occupancy exclusivity).
- **Result: covered.** The congestion ladder (`YIELDING`/`SIDESTEPPING`/`WAITING`/`CONGESTION`)
  and `LegalityServiceV2.verify_occupancy()` together confirm capability and path existence can
  both hold while a current, specific obstacle still prevents the attempt from succeeding this
  tick.

## SPC-S07 — Destination exists but no path

A valid location B exists; an entity at location A has no valid connection to it (e.g., fully
enclosed by impassable terrain).

- **Rules invoked:** LOC-05 (path possibility is a topology fact), MOV-01.
- **Result: covered.** `NavigationSystem.get_next_step()` returning no viable step, distinct
  from `LegalityServiceV2`'s occupancy/reach checks, confirms path-existence is checked
  independently from the other movement facts — exactly LOC-05's boundary claim.

## SPC-S08 — Movement has cost but still fails

A movement attempt begins; a step succeeds and its declared stamina cost is incurred; a later
step in the same overall journey is interrupted, and the entity never reaches its original
destination.

- **Rules invoked:** MOV-04 (cost may be incurred per step, even when the overall attempt is
  later interrupted), COST-03 (reused directly).
- **Result: covered — the explicit cross-batch challenge the instruction required.**
  `StaminaUpdate(current_delta=-entity.stamina.MOVE_COST) if success else None` ties cost to
  *this tick's* step succeeding, not the overall journey completing — an earlier successful
  step's cost is never revisited when a later step in the same journey fails.

## SPC-S09 — Teleport/supernatural travel boundary

An ordinary spatial path is unavailable. A hypothetical supernatural mechanism establishes
another valid movement relation instead.

- **Rules invoked:** MOV-05 (physical traversal is not the only movement mode).
- **Result: blocked, by design — confirms the semantic slot exists, not that a mechanism
  fills it.** No non-physical movement mechanism exists in this repository, checked directly.
  This scenario's job (per the batch instruction's own framing) is to confirm Space's own laws
  don't assume physical traversal is the *only* possible movement mode — MOV-05 states that
  permission explicitly, without designing Magic here.

## SPC-S10 — Environment is descriptive but causally inert (counter)

A region has environmental metadata (`service_availability`) that nothing currently consumes.

- **Rules invoked:** ENV-01 (environment creates causal conditions when a mechanism declares
  them), ENV-05 (inert state should be recognized, not assumed causal).
- **Result: revealed a real, confirmed gap, not a rule violation.** `service_availability` is
  written by siege mechanics but checked directly: read by nothing. This is exactly the kind of
  state the counter-scenario exists to detect — bookkeeping without a causal consumer — and
  ENV-01/ENV-05 are written precisely so this finding is a recognized, honest fact rather than
  an unnoticed one.

## SPC-S11 — Location change ≠ identity change (cross-batch check)

An entity moves from one region to another. Its identity is obviously unaffected by the move.

- **Rules invoked:** LOC-01, ID-01 (reused directly — location is explicitly named in ID-01's
  own worked list of ordinary state changes identity survives).
- **Result: covered.** Nothing about `MovementSystem.resolve_move()` touches `entity_id`;
  location is unambiguously ordinary state, exactly as ID-01 already established at the
  foundational level. This scenario confirms Space/Environment introduces no tension with that
  already-settled finding.

## SPC-S12 — Historical presence at a place ≠ current presence or reach (cross-batch check)

An entity once resided at a settlement. The entity has since died or relocated. The settlement's
own history references the entity's past presence, but the entity itself has no current reach
to affect that place.

- **Rules invoked:** REACH-04, HP-01 (both reused directly).
- **Result: covered — reconfirms rather than newly discovers.** No new repository evidence was
  needed: `_transfer_inherited_feud()` (REACH-04's own evidence) already establishes that a
  historically-referenced subject has zero present reach; this scenario confirms that finding
  extends cleanly to a *place*-anchored historical reference, not only a person-anchored one.

## Expansion: follow-up probes (SPC-S13–S15)

Added per `tmp/world-rule-batch-4-followup-ext-ai.md`, directly challenging the three Rules that
follow-up revised: ENV-02 (exposure depends on declared conditions being satisfied, not
automatic from presence), LOC-01 (spatial state need not be point-like), and LOC-05/the
Movement-Reach boundary (a route may persist while temporarily inaccessible).

## SPC-S13 — Hazardous region, no exposure

An entity enters a region with a nonzero `hazard_level`, but its faction has a declared immunity
to that region's `hazard_kind`. Actual exposure does not occur.

- **Rules invoked:** ENV-02 (presence creates an exposure *opportunity*; actual exposure depends
  on declared conditions being satisfied).
- **Result: covered.** `EnvironmentService.calculate_hazard_drain()` checks
  `get_faction_semantics_service().get_hazard_immunities(faction_id)` before computing any
  drain, returning `0` when the entity's faction is immune to the region's `hazard_kind` —
  confirming presence/traversal alone does not guarantee exposure; a declared condition (here,
  immunity) legitimately intervenes.

## SPC-S14 — Spatial extent

A large place occupies more than one spatial unit (a multi-tile city), yet has coherent,
unambiguous authoritative spatial state — it is not forced into a single point representation.

- **Rules invoked:** LOC-01 (authoritative spatial state must be unambiguous according to its
  declared spatial model, not necessarily point-like).
- **Result: covered.** `PlaceState.footprint: Optional[tuple[int, int, int, int]]`
  ("Sub-bounds, multi-tile CITY-kind only") confirms an area/extent spatial model already
  coexists with the point-location model (`position`) in the same repository — a `CITY`-kind
  place's authoritative spatial state is unambiguous (its footprint) without being reducible to
  one point.

## SPC-S15 — Persistent route, temporary blockage

A path connects A to B. A building comes to occupy a tile along that path, blocking current
traversal. The underlying route relation persists; only current accessibility is affected.

- **Rules invoked:** LOC-05 (route/path accessibility is derived from topology plus current
  conditions, not necessarily a stored topology fact itself), MOV-01/Movement-Reach boundary.
- **Result: covered.** `LegalityServiceV2` distinguishes static, permanent blockage
  (`PATH_NOT_FOUND`, from `WALL`/`blocked_tiles` terrain) from dynamic, potentially-temporary
  blockage (`BUILDING_OBSTRUCTION`, from a building occupying a tile) — confirming the
  repository already treats an obstruction as separable from the underlying terrain/topology:
  the building can in principle be removed without anything about the route's own topological
  existence changing.

---

## Cross-batch note

SPC-S04/S05 and SPC-S08 both instantiate the same OWN-02/COST-03 discipline (participation ≠
ownership; cost follows the declared lifecycle) that Batches 01–03 already established —
recorded as reconfirmations from the Space/Environment domain's own concrete cases, not as new
foundational findings. This is the expected, healthy pattern for a first domain-facing batch:
the foundational Rules should already predict most of what a domain's own investigation finds,
and where this batch's own genuinely new material lives is in the confirmed gaps (LOC-02/LOC-06's
missing route/portal/directional mechanism, MOV-05's missing non-physical movement mechanism,
ENV-01/ENV-05's confirmed-inert `service_availability`) rather than in contradicting anything
already accepted.

The follow-up expansion's own most useful result was not a new scenario finding but an
ownership-framing correction: the original review deferred the LOC-02/LOC-06 route/portal gap
"primarily to Magic and Organizations," which read as though whichever domain eventually builds
a connection mechanism would also become its canonical owner. LOC-07 (added by the follow-up)
corrects this by applying OWN-01/OWN-02's discipline to topology specifically — a domain may
produce, control, destroy, maintain, or use a spatial connection without owning spatial
connectivity itself, which remains this family's own concern. The same correction was applied
to ENV-03 (Environment never owns exposure's consequence, but this batch does not decide which
domain does) rather than letting the repository's own `CombatUpdate` wiring quietly settle a
question this batch was never meant to answer.
