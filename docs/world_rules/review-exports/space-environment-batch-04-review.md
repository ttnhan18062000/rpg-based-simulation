---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
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
`foundations/`, per the batch instruction's own directory suggestion. Revised once, per
`tmp/world-rule-batch-4-followup-ext-ai.md`, to remove implementation-specific wording from
seven rules (LOC-01, LOC-03, LOC-05, ENV-01, ENV-02, ENV-05, MOV-02, MOV-04), correct the
topology/environment ownership framing (adding LOC-07 and loosening ENV-03), and add three
scenario probes — before being frozen as ready for high-level external review.

## Canonical files included

- `space-environment/location-topology.md` (LOC-01–07)
- `space-environment/environment.md` (ENV-01–05)
- `space-environment/movement-navigation.md` (MOV-01–06)
- `scenarios/space-environment-batch-04.md` (SPC-S01–S15)

## Rule Inventory

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| LOC-01 | Spatial State Must Be Unambiguous, Not Necessarily Point-Like | Point, area/extent, containment, in-transit, or multi-cell states are all legitimate, per whatever spatial model is declared. | Accepted, refined |
| LOC-02 | Topological Connection ≠ Geometric Closeness | Distance doesn't determine reachability; connection is its own fact. | Accepted (confirmed repository gap) |
| LOC-03 | Containment Is a Real, Authoritative Relationship | Real and queryable, however it is stored — no particular storage shape required. | Accepted, refined |
| LOC-04 | Occupancy Is Exclusive Where Declared | A declared exclusivity bound is real and enforced. | Accepted |
| LOC-05 | Route Accessibility Is Distinct From, and May Be Derived From, Topology | A route may persist while temporarily inaccessible (collapse, closure) without the topology itself changing. | Accepted, refined |
| LOC-06 | Directional Connections Are a Legitimate Shape | A → B possible doesn't imply B → A possible. | Accepted (mechanism MISSING) |
| LOC-07 | Producing a Topology Change ≠ Owning Topology State | A domain that creates/controls/destroys/maintains/uses a connection isn't automatically its canonical owner. | Accepted (new, added by follow-up) |
| ENV-01 | Environmental State Has Causal Significance Only Where a Declared Process Consumes It | World-semantic framing of "causally live"; one confirmed inert field. | Accepted, refined |
| ENV-02 | Presence Creates Exposure Opportunity; Actual Exposure Depends on Declared Conditions | Shelter/immunity/equipment/form may prevent exposure even under a real hazard condition. | Accepted, refined |
| ENV-03 | Environment Establishes Exposure, Doesn't Own the Consequence — Which Domain Does Is Not Decided Here | OWN-02 restated for Environment; the target owner is explicitly left open. | Accepted, refined |
| ENV-04 | Modifiers May Affect Other Domains Without Owning Their Commit | A weather multiplier feeds Movement's own calculation. | Accepted |
| ENV-05 | Inert State Should Be Recognized, Not Assumed Causal | ENV-01's counter-finding, restated in world-semantic terms. | Accepted, refined |
| MOV-01 | Movement's Constituent Facts Are Distinct | Capability, authority, reach, path, cost, destination-validity are six separate checks. | Accepted |
| MOV-02 | Movement Is a Committed Transition Governed by Declared Constraints | World-semantic framing, replacing "not raw assignment." | Accepted, refined |
| MOV-03 | A Movement Attempt Doesn't Guarantee Arrival | CAP-04 restated for movement. | Accepted |
| MOV-04 | Movement Cost May Accrue at Declared Stages of a Process | Per-step is one legitimate accrual model, not the general Rule. | Accepted, refined |
| MOV-05 | Physical Traversal Isn't the Only Movement Mode | A declared non-physical transition is a legitimate movement relation. | Accepted (mechanism MISSING) |
| MOV-06 | Spatial Reach Instantiates, Doesn't Redefine, Foundational Reach | REACH-01–06 applied concretely to space. | Accepted, by explicit deference |

## Scenario Inventory

One row per scenario, including the required counter, cross-batch checks, and follow-up probe
scenarios. Full traces stay in `scenarios/space-environment-batch-04.md`.

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
| SPC-S13 | Hazardous Region, No Exposure | entity enters hazard region → faction immunity → no actual exposure | Environment | Life/body/survival | Covered |
| SPC-S14 | Spatial Extent | multi-tile city → coherent authoritative spatial state, not point-reduced | Location/Topology | Places/settlements & territory | Covered |
| SPC-S15 | Persistent Route, Temporary Blockage | A connected to B → building obstructs path → route persists, current traversal unavailable | Location/Topology, Movement | Conflict & combat | Covered |

## Coverage Summary

**Location/Topology**
- spatial state, point and area/extent both legitimate — SPC-S11, SPC-S14
- topology ≠ distance (both directions) — SPC-S01, SPC-S02
- directionality — SPC-S03
- containment — none newly traced (direct code inspection)
- occupancy exclusivity — SPC-S06
- accessibility derived from topology + current conditions, distinct from stored topology —
  SPC-S07, SPC-S15
- historical place-reference ≠ present reach — SPC-S12
- producer of topology change ≠ owner of topology state — no scenario yet (LOC-07 stated ahead
  of any mechanism to trace it against)

**Environment**
- causally significant conditions, and one confirmed inert field — SPC-S04, SPC-S05, SPC-S10
- presence creates exposure opportunity; declared conditions (immunity) may prevent actual
  exposure — SPC-S04, SPC-S05, SPC-S13
- exposure without owning the consequence, ownership left open — SPC-S04, SPC-S05
- modifiers feeding other domains' calculations — reused from movement evidence

**Movement/Navigation**
- distinct constituent facts — SPC-S06, SPC-S07
- committed transition governed by declared constraints — SPC-S06
- attempt ≠ arrival — SPC-S06, SPC-S08
- cost accrual at a declared stage (per-step is this repository's own instance) — SPC-S08
- non-physical movement permission — SPC-S09
- spatial reach as Reach's instance — SPC-S01

## Deferred Semantics

An unresolved later-domain question is not the same thing as an incomplete foundational rule —
consistent with every prior batch's own framing:

- LOC-02/LOC-06's confirmed gap (no route/portal/directional-connection mechanism) is the most
  load-bearing MISSING finding in this batch — affects every future domain wanting a
  non-geometric spatial shortcut. **Corrected by follow-up:** this is treated primarily as a
  Space/Movement capability gap (LOC-07); Magic/supernatural (portals) and Groups/
  organizations & institutions (trade routes) are recorded as plausible future
  producers/consumers of a connection mechanism, not as its canonical owner.
- MOV-05's confirmed gap (no non-physical movement mechanism) is the same underlying absence
  from the movement side — deferred to Magic/supernatural as a plausible producer, not an owner.
- ENV-01/ENV-05's confirmed inert field (`service_availability`) — whether to wire it to a real
  consumer or leave it as a forward-declared field awaiting future siege/economy content is not
  decided here.
- SPC-S02's "far but connected" scenario is only weakly covered (ordinary long-distance
  traversal, not a genuine non-geometric shortcut) — the strong version waits on the same
  LOC-02/LOC-06 gap.
- **New, per the follow-up.** ENV-03 deliberately leaves open which domain owns exposure's
  downstream consequences (Life/Body, a future Survival domain, or another not yet named) —
  not settled by this repository's own current `CombatUpdate` wiring, which is evidence of
  today's implementation, not a target-architecture claim.
- **New, per the follow-up.** LOC-07 states the producer/owner distinction for topology ahead of
  any mechanism to check it against — which single mechanism eventually owns topology state,
  once LOC-02/LOC-06's gap is filled, remains for whichever future batch builds it.

## Cross-domain findings

- Location/Topology ↔ Reach: LOC-02/MOV-06 both restate REACH-01/REACH-02's discipline
  spatially — SPC-S01 answers both families' probes at once, the same pattern Batch 02/03 found
  repeatedly (one mechanism, several foundational questions).
- Location/Topology ↔ State Ownership: **new, per the follow-up.** LOC-07 is OWN-01/OWN-02
  applied to topology specifically — the same participation-≠-ownership discipline Environment
  (ENV-03) and Batch 01/02/03 already established repeatedly, now given its topology-specific
  citable home.
- Environment ↔ State Ownership: ENV-03 remains one of the cleanest OWN-02 instances this
  Catalog has found — `calculate_hazard_drain()` returns a plain number, never touching an
  `EntityUpdate`, while `WorldDynamicsSystem` two frames away commits the actual `CombatUpdate`
  — but the follow-up correction keeps this as evidence that *some* other domain owns the
  result, not evidence of *which* domain should.
- Movement ↔ Cost: MOV-04 is a direct, concrete instance of COST-03's lifecycle principle —
  SPC-S08 is this batch's own version of Batch 03's CTR-S17 (a failed committed attempt still
  costs something), now at the movement-specific level, generalized beyond the per-step case
  this repository happens to implement.
- Movement ↔ Capability: MOV-03 is CAP-04 restated; no new evidence needed beyond what MOV-01–04
  already establish about movement's own constituent checks.
- Location/Topology ↔ Identity/History-Provenance: SPC-S11/SPC-S12 are both reconfirmations,
  not new findings — location is ordinary state (ID-01) and a place's historical reference
  doesn't grant present reach (REACH-04/HP-01), exactly as already established.

**Where Space supplies inputs to Life/Capability/etc. (explicit call-out, per the batch
instruction):** Environment supplies a real exposure *amount* (via `calculate_hazard_drain()`)
that some other domain's own authoritative update path commits (this repository's current
wiring happens to be Combat/Life's `CombatUpdate` — evidence, not a settled target-ownership
claim, per the follow-up correction); Environment supplies a real *multiplier* (via
`get_weather_multipliers()`) that Movement's own resolution consumes. In both cases, Space
computes a plain value; the consuming domain's own authoritative update path commits the
result — Space never writes another domain's state directly.

**Which movement constraints are semantic vs. pathfinding implementation (explicit call-out):**
Semantic: capability/authority/reach/cost/destination-validity as distinct checks (MOV-01); a
committed transition governed by declared constraints (MOV-02); attempt ≠ arrival (MOV-03);
cost accrual at a declared stage (MOV-04, generalized beyond per-step); non-physical movement
permission (MOV-05). Pathfinding implementation, cited as evidence only, never as the rule: the
specific congestion-ladder tiers (yielding/sidestepping/waiting/congestion/path-exhausted),
`NavigationSystem.get_next_step()`'s actual algorithm, the grid/coordinate representation
itself, and the per-step cost-accrual granularity specifically.

**Whether any rule accidentally assumes Euclidean/grid-only movement (explicit call-out):**
Checked directly — no. LOC-01 (refined by the follow-up to explicitly allow non-point spatial
models) states location representation-neutrally and cites the grid as evidence, not as the
rule; LOC-02/LOC-06's own confirmed gaps exist precisely *because* this batch declined to
assume the grid is the only possible topology, instead naming the absence of a non-geometric
alternative as a gap rather than silently treating geometric adjacency as topology's full
definition.

## Open questions

1. LOC-02/LOC-06's confirmed gap — same underlying absence, tracked as two rules (existence of
   non-geometric connection; directionality) since a future mechanism would likely resolve both
   together, but they remain distinct semantic claims. LOC-07 clarifies that whichever domain
   fills this gap does not thereby become topology's owner.
2. MOV-05's confirmed gap — deferred to Magic/supernatural as a plausible producer, not owner;
   not designed here.
3. Should `service_availability` be wired to a real consumer in a future batch, or left
   forward-declared? Not decided.
4. `price_modifiers` is confirmed live (`market.py`); `weather`/`active_modifiers` beyond
   `"MIASMA"` were not exhaustively re-verified — flagged for Economy/resources or Ecology/
   population.
5. **Added by follow-up.** Which domain owns exposure's downstream consequences (ENV-03)? Not
   decided — Life/Body, a future Survival domain, and "another not yet named" are all live
   possibilities; this batch only established that Environment itself is not a candidate.
6. **Added by follow-up.** Once LOC-02/LOC-06's connection mechanism is eventually built, which
   single mechanism owns the resulting topology state (LOC-07)? Not decided here.

## Repository evidence

No CONFLICTING or UNKNOWN findings, in either pass. Two confirmed MISSING mechanisms (LOC-02/
LOC-06's route/portal/directional-connection gap; MOV-05's non-physical-movement gap) recorded
honestly as absent, not assumed. One confirmed inert field (`service_availability`, ENV-01/
ENV-05). The follow-up pass added no new MISSING findings — its three new scenarios (SPC-S13–
S15) each confirmed a revised rule's wording against evidence already partly known
(`get_hazard_immunities`, `PlaceState.footprint`, `BUILDING_OBSTRUCTION`) rather than
discovering a new gap.

Key evidence, all confirmed by direct code inspection: `src/engine/spatial_query.py`
(`get_region_at`, `get_occupancy_map`), `src/core/state.py` (`RegionState.bounds`,
`PlaceState.region_id`/`RegionState.places`, `PlaceState.footprint`), `src/engine/movement.py`
(`MovementSystem.resolve_move`, `COMB-201`, the congestion ladder, `stamina_upd ... if
success`), `src/engine/domain/movement_actions.py` ("GRID-BASED AUTHORITATIVE MOVEMENT"),
`src/world/environment.py` (`EnvironmentService.calculate_hazard_drain`,
`get_hazard_immunities`, `get_weather_multipliers`), `src/engine/world_dynamics.py`
(`WorldDynamicsSystem.resolve_dynamics`, the `CombatUpdate` commit), `src/engine/
military_conflict.py` (`service_availability_delta`, write-only), `src/systems/
economy_systems/market.py` (`price_modifiers` consumption), `src/engine/legality.py`
(`PATH_NOT_FOUND` for static terrain vs. `BUILDING_OBSTRUCTION` for dynamic obstruction — the
distinction confirming LOC-05's revised accessibility-vs-topology boundary).

## Owner-attention decisions

- Whether LOC-02/LOC-06's route/portal/directional-connection gap should be prioritized ahead
  of its "natural" place in the design order, given how many future domains (trade, magic,
  places) would benefit from it — LOC-07 clarifies this is a Space/Movement capability gap
  regardless of prioritization, not a question of which domain "owns" fixing it.
- Whether `service_availability` should be wired to a consumer now or left forward-declared.
- **Added by follow-up.** Whether to pre-decide exposure's downstream owner (ENV-03) now, or
  leave it genuinely open until Life/Body/Survival (Batch 05, next) is actually designed —
  current disposition: left open, per the follow-up's own explicit instruction.

## Starter-candidate disposition summary

17 rules drafted across three families in the original pass (6 Location/Topology, 5
Environment, 6 Movement/Navigation) — all 17 accepted, 0 rejected, 0 split, 0 merged, in both
the original pass and the follow-up revision pass. The follow-up pass refined 8 rules (LOC-01,
LOC-03, LOC-05, ENV-01, ENV-02, ENV-05, MOV-02, MOV-04 — see Rule Inventory's "Accepted,
refined" rows), loosened ENV-03's specific target-ownership claim without changing
its core boundary, and added one new rule (LOC-07) plus 3 further scenarios (SPC-S13–S15) —
without rejecting, splitting, or merging any of the original 17. None of the refinements
reversed a rule's substance: each removed implementation-specific wording (LOC-01, LOC-03,
ENV-01, ENV-05, MOV-02), distinguished a case the original wording had conflated (LOC-05,
ENV-02), generalized beyond one implementation choice (MOV-04), or corrected an ownership
framing that had drifted from this Catalog's own established OWN-01/OWN-02 discipline (LOC-07,
ENV-03). The batch instruction's own file grouping was kept as suggested throughout — no
cleaner semantic boundary was found that would justify merging or further splitting. No rule
was rejected as an implementation concern; pathfinding algorithms and the grid representation
were treated as evidence throughout, never promoted to rule status.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/space-environment-batch-04-report.md` (local review report, not part of this catalog).

---

> **BATCH 04 (SPACE / ENVIRONMENT / MOVEMENT) PASS — READY TO FREEZE**

All required artifacts reflect the follow-up revision: three rule-family files (18 rules, 8
refined and 1 added this pass), one scenario file (15 scenarios: the original 12 plus 3
follow-up probes), this review export with all required sections plus every
explicitly-required call-out, and a local disposition report. No new contradiction appeared —
each of the follow-up's three new scenarios confirmed a revised rule's wording holds against a
real case the original wording would have handled incorrectly (immunity preventing exposure;
area/extent spatial state; a temporarily-blocked-but-topologically-persistent route), and the
ownership-framing correction (LOC-07, ENV-03) fixed a real drift from this Catalog's own
established discipline rather than discovering a new one. Per the follow-up instruction:
proceed next to Batch 05 (Life / Body / Survival / Ecology).
