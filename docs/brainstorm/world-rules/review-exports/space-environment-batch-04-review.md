---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Batch 04 (Space / Environment / Movement)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

The first domain-facing (Milestone B) batch — Location/Topology, Environment, Movement/
Navigation. Not another foundational batch; this one deepens where Milestone A's foundational
Rules (Identity, State Ownership, Causality, Time, Authority, Reach, Capability, Cost, Capacity,
Resource, Transformation, History/Provenance) already predicted this domain's shape, and its own
genuinely new material is concentrated in a small number of confirmed repository gaps rather
than in contradicting anything already accepted. Files live under `space-environment/`, not
`foundations/`, per the batch instruction's own directory suggestion.

## Canonical files included

- `space-environment/location-topology.md` (LOC-01–06)
- `space-environment/environment.md` (ENV-01–05)
- `space-environment/movement-navigation.md` (MOV-01–06)
- `scenarios/space-environment-batch-04.md` (SPC-S01–S12)

## Rule Inventory

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| LOC-01 | Location Is a Real, Representation-Neutral Fact | Where a subject is has one real answer, independent of implementation. | Accepted |
| LOC-02 | Topological Connection ≠ Geometric Closeness | Distance doesn't determine reachability; connection is its own fact. | Accepted (confirmed repository gap) |
| LOC-03 | Containment Is a Real, Declared Relationship | Place-within-region is tracked bidirectionally, not incidental. | Accepted |
| LOC-04 | Occupancy Is Exclusive Where Declared | A declared exclusivity bound is real and enforced. | Accepted |
| LOC-05 | Path Possibility Is Its Own Topology Fact | Distinct from movement's own capability/authority/cost checks. | Accepted |
| LOC-06 | Directional Connections Are a Legitimate Shape | A → B possible doesn't imply B → A possible. | Accepted (mechanism MISSING) |
| ENV-01 | Environment Creates Causal Conditions When Declared | Environmental state is causal only where a mechanism reads it. | Accepted (one confirmed inert field) |
| ENV-02 | Occupying/Traversing Creates a Real Exposure Fact | The occupy/traverse → condition → exposure → reaction pattern. | Accepted |
| ENV-03 | Environment Establishes Exposure, Doesn't Own the Consequence | OWN-02 restated for Environment specifically. | Accepted |
| ENV-04 | Modifiers May Affect Other Domains Without Owning Their Commit | A weather multiplier feeds Movement's own calculation. | Accepted |
| ENV-05 | Inert State Should Be Recognized, Not Assumed Causal | ENV-01's counter-finding, stated as its own standing standard. | Accepted |
| MOV-01 | Movement's Constituent Facts Are Distinct | Capability, authority, reach, path, cost, destination-validity are six separate checks. | Accepted |
| MOV-02 | Movement Requires a Valid Transition, Never Raw Assignment | A real resolved outcome, not a bare position write. | Accepted |
| MOV-03 | A Movement Attempt Doesn't Guarantee Arrival | CAP-04 restated for movement. | Accepted |
| MOV-04 | Movement Cost May Be Incurred Per Step, Even If the Attempt Fails Later | COST-03 restated for movement. | Accepted |
| MOV-05 | Physical Traversal Isn't the Only Movement Mode | A declared non-physical transition is a legitimate movement relation. | Accepted (mechanism MISSING) |
| MOV-06 | Spatial Reach Instantiates, Doesn't Redefine, Foundational Reach | REACH-01–06 applied concretely to space. | Accepted, by explicit deference |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Deferred domain dependencies | Result |
|---|---|---|---|---|---|
| SPC-S01 | Near but Unreachable | close tiles → wall/chasm → no direct interaction | Location/Topology, Reach | none | Covered |
| SPC-S02 | Far but Connected | distant locations → traversable path exists → travel possible | Location/Topology | Groups/organizations (trade routes) | Partial |
| SPC-S03 | One-Way Passage | A→B possible, B→A hypothetically not | Location/Topology | Magic/supernatural | Blocked |
| SPC-S04 | Enter Hazardous Environment | entity enters region → hazard → exposure → possible HP consequence | Environment | Life/body/survival | Covered |
| SPC-S05 | Leave Hazardous Environment | entity exits region → exposure ends → prior HP loss persists | Environment, State Ownership | Life/body/survival | Covered |
| SPC-S06 | Capable but Blocked | valid path exists → current obstacle blocks passage | Movement, Location/Topology | Conflict & combat | Covered |
| SPC-S07 | Destination Exists but No Path | valid location B → no connection from A → movement impossible | Location/Topology, Movement | none | Covered |
| SPC-S08 | Movement Has Cost but Still Fails | step commits, cost paid → later step interrupted → no arrival | Movement, Cost | none | Covered |
| SPC-S09 | Teleport/Supernatural Travel Boundary | ordinary path unavailable → hypothetical non-physical transition | Movement | Magic/supernatural | Blocked (by design) |
| SPC-S10 | Environment Descriptive but Causally Inert (counter) | region has metadata → no consumer → no effect | Environment | Economy/resources, Ecology/population | Revealed gap |
| SPC-S11 | Location Change ≠ Identity Change | entity moves regions → identity unaffected | Location/Topology, Identity | none | Covered |
| SPC-S12 | Historical Presence ≠ Current Reach | past resident → death/relocation → place's history references them, they have no present reach | Location/Topology, Reach, History/Provenance | Family/lineage, Places | Covered |

## Coverage Summary

**Location/Topology**
- representation-neutral location — SPC-S11
- topology ≠ distance (both directions) — SPC-S01, SPC-S02
- directionality — SPC-S03
- containment — none newly traced (direct code inspection)
- occupancy exclusivity — SPC-S06
- path existence as its own fact — SPC-S07
- historical place-reference ≠ present reach — SPC-S12

**Environment**
- causally live conditions — SPC-S04, SPC-S05
- exposure without owning the consequence — SPC-S04, SPC-S05
- modifiers feeding other domains' calculations — reused from movement evidence
- inert state, confirmed — SPC-S10

**Movement/Navigation**
- distinct constituent facts — SPC-S06, SPC-S07
- valid transition, not raw assignment — SPC-S06
- attempt ≠ arrival — SPC-S06, SPC-S08
- cost per step, independent of later failure — SPC-S08
- non-physical movement permission — SPC-S09
- spatial reach as Reach's instance — SPC-S01

## Deferred Semantics

An unresolved later-domain question is not the same thing as an incomplete foundational rule —
consistent with every prior batch's own framing:

- LOC-02/LOC-06's confirmed gap (no route/portal/directional-connection mechanism) is the most
  load-bearing MISSING finding in this batch — affects every future domain wanting a
  non-geometric spatial shortcut. Deferred to Magic/supernatural (portals) and Groups/
  organizations & institutions (trade routes) as the most plausible future owners.
- MOV-05's confirmed gap (no non-physical movement mechanism) is the same underlying absence
  from the movement side — deferred to Magic/supernatural.
- ENV-01/ENV-05's confirmed inert field (`service_availability`) — whether to wire it to a real
  consumer or leave it as a forward-declared field awaiting future siege/economy content is not
  decided here.
- SPC-S02's "far but connected" scenario is only weakly covered (ordinary long-distance
  traversal, not a genuine non-geometric shortcut) — the strong version waits on the same
  LOC-02/LOC-06 gap.

## Cross-domain findings

- Location/Topology ↔ Reach: LOC-02/MOV-06 both restate REACH-01/REACH-02's discipline
  spatially — SPC-S01 answers both families' probes at once, the same pattern Batch 02/03 found
  repeatedly (one mechanism, several foundational questions).
- Environment ↔ State Ownership: ENV-03 is one of the cleanest OWN-02 instances this Catalog has
  found — `calculate_hazard_drain()` returns a plain number, never touching an `EntityUpdate`,
  while `WorldDynamicsSystem` two frames away commits the actual `CombatUpdate`.
- Movement ↔ Cost: MOV-04 is a direct, concrete instance of COST-03's lifecycle principle —
  SPC-S08 is this batch's own version of Batch 03's CTR-S17 (a failed committed attempt still
  costs something), now at the movement-specific level.
- Movement ↔ Capability: MOV-03 is CAP-04 restated; no new evidence needed beyond what MOV-01–04
  already establish about movement's own constituent checks.
- Location/Topology ↔ Identity/History-Provenance: SPC-S11/SPC-S12 are both reconfirmations,
  not new findings — location is ordinary state (ID-01) and a place's historical reference
  doesn't grant present reach (REACH-04/HP-01), exactly as already established.

**Where Space supplies inputs to Life/Capability/etc. (explicit call-out, per the batch
instruction):** Environment supplies a real exposure *amount* (via `calculate_hazard_drain()`)
that Life/Body's own `CombatUpdate` commits; Environment supplies a real *multiplier* (via
`get_weather_multipliers()`) that Movement's own resolution consumes. In both cases, Space
computes a plain value; the consuming domain's own authoritative update path commits the
result — Space never writes another domain's state directly.

**Which movement constraints are semantic vs. pathfinding implementation (explicit call-out):**
Semantic: capability/authority/reach/cost/destination-validity as distinct checks (MOV-01);
attempt ≠ arrival (MOV-03); cost-per-step lifecycle (MOV-04); non-physical movement permission
(MOV-05). Pathfinding implementation, cited as evidence only, never as the rule: the specific
congestion-ladder tiers (yielding/sidestepping/waiting/congestion/path-exhausted),
`NavigationSystem.get_next_step()`'s actual algorithm, and the grid/coordinate representation
itself.

**Whether any rule accidentally assumes Euclidean/grid-only movement (explicit call-out):**
Checked directly — no. LOC-01 explicitly states location representation-neutrally and cites the
grid as evidence, not as the rule; LOC-02/LOC-06's own confirmed gaps exist precisely *because*
this batch declined to assume the grid is the only possible topology, instead naming the
absence of a non-geometric alternative as a gap rather than silently treating geometric
adjacency as topology's full definition.

## Open questions

1. LOC-02/LOC-06's confirmed gap — same underlying absence, tracked as two rules (existence of
   non-geometric connection; directionality) since a future mechanism would likely resolve both
   together, but they remain distinct semantic claims.
2. MOV-05's confirmed gap — deferred to Magic/supernatural; not designed here.
3. Should `service_availability` be wired to a real consumer in a future batch, or left
   forward-declared? Not decided.
4. `price_modifiers` is confirmed live (`market.py`); `weather`/`active_modifiers` beyond
   `"MIASMA"` were not exhaustively re-verified — flagged for Economy/resources or Ecology/
   population.

## Repository evidence

No CONFLICTING or UNKNOWN findings. Two confirmed MISSING mechanisms (LOC-02/LOC-06's route/
portal/directional-connection gap; MOV-05's non-physical-movement gap) recorded honestly as
absent, not assumed. One confirmed inert field (`service_availability`, ENV-01/ENV-05).

Key evidence, all confirmed by direct code inspection: `src/engine/spatial_query.py`
(`get_region_at`, `get_occupancy_map`), `src/core/state.py` (`RegionState.bounds`,
`PlaceState.region_id`/`RegionState.places` dual-reference), `src/engine/movement.py`
(`MovementSystem.resolve_move`, `COMB-201`, the congestion ladder, `stamina_upd ... if
success`), `src/engine/domain/movement_actions.py` ("GRID-BASED AUTHORITATIVE MOVEMENT"),
`src/world/environment.py` (`EnvironmentService.calculate_hazard_drain`,
`get_weather_multipliers`), `src/engine/world_dynamics.py` (`WorldDynamicsSystem.
resolve_dynamics`, the `CombatUpdate` commit), `src/engine/military_conflict.py`
(`service_availability_delta`, write-only), `src/systems/economy_systems/market.py`
(`price_modifiers` consumption, confirming that field is live).

## Owner-attention decisions

- Whether LOC-02/LOC-06's route/portal/directional-connection gap should be prioritized ahead
  of its "natural" place in the design order, given how many future domains (trade, magic,
  places) would benefit from it.
- Whether `service_availability` should be wired to a consumer now or left forward-declared.

## Starter-candidate disposition summary

17 rules drafted across three families (6 Location/Topology, 5 Environment, 6 Movement/
Navigation) — all 17 accepted, 0 rejected, 0 split, 0 merged. The batch instruction's own file
grouping (`space-environment/location-topology.md`, `environment.md`,
`movement-navigation.md`) was kept as suggested — no cleaner semantic boundary was found that
would justify merging or further splitting. No rule was rejected as an implementation concern;
pathfinding algorithms and the grid representation were treated as evidence throughout, per the
batch instruction's own non-goal, never promoted to rule status.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/space-environment-batch-04-report.md` (local review report, not part of this catalog).

---

> **BATCH 04 (SPACE / ENVIRONMENT / MOVEMENT) READY FOR HIGH-LEVEL EXTERNAL REVIEW.**

All required artifacts exist: three rule-family files (17 rules), one scenario file (12
scenarios covering all 10 required probes plus both cross-batch checks not otherwise covered),
this review export with all nine required sections plus every explicitly-required call-out, and
a local disposition report. No contradiction was found against any prior batch or within this
one — this batch's own genuinely new material is concentrated in confirmed gaps (LOC-02/LOC-06,
MOV-05, ENV-01/ENV-05's inert field), not in tension with anything already accepted. Per the
batch instruction's stop condition: all ten checklist items are satisfied. Do not begin Life /
Body / Survival / Ecology until this batch receives high-level review.
