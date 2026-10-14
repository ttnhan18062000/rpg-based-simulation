---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-10-08"
---

# World Rule Family: Movement / Navigation

**Purpose/scope.** What makes movement from one valid location/state to another possible.
Movement capability, movement authority, movement reach, path accessibility, movement cost, and
destination validity are kept distinct — a subject may have any one without the others.
Movement should require a valid world-semantic transition, not merely assignment of a location
field.

**Status.** Batch 04 (Space/Environment/Movement), first draft. Candidates below originated as
external-reviewer hypotheses (`tmp/world-rule-batch-4-ext-ai.md`); each carries this session's
disposition and repository evidence, not the original wording uncritically kept.

**Explicit non-goal, per the batch instruction.** Do not design pathfinding algorithms —
pathfinding implementation is evidence only, not the rule.

---

## MOV-01 — Movement's constituent facts are distinct and independently checkable

> Movement capability (can this subject move at all), movement authority (is this specific
> movement legitimate), movement reach (can this subject possibly affect/reach the destination),
> path accessibility (does a valid route exist — `location-topology.md`'s own question), movement
> cost (what is consumed), and destination validity (is the target itself a legitimate place to
> be) are six distinct facts. A subject may satisfy any subset of them without satisfying the
> rest.

**Disposition: ACCEPT.** This is the family's own restatement of the same discipline
CAP-01–05/AUTH-01–06/REACH-01–06 already established generally — Movement is where all of them
apply simultaneously to one concrete action, and this rule exists so a future domain author
checking movement specifically doesn't have to re-derive the boundary from five other files.

**Repository evidence: SUPPORTED, across the distinct checks.** `entity.lifecycle.active`
(capability-adjacent), `LegalityServiceV2.verify_occupancy`/`get_region_for_position` (reach/
destination), `NavigationSystem.get_next_step` (path accessibility, `location-topology.md`'s
LOC-05), `StaminaService.drain_move`/`MOVE_COST` (cost) are all independent checks inside
`MovementSystem.resolve_move()`, never collapsed into one combined gate.

**Scenarios:** [SPC-S06](../scenarios/space-environment-batch-04.md#spc-s06),
[SPC-S07](../scenarios/space-environment-batch-04.md#spc-s07).

---

## MOV-02 — Movement is a committed spatial transition governed by declared world constraints

> Movement is a committed spatial transition governed by declared world constraints, not an
> unconstrained change of spatial state. What resolves a movement outcome (checking path,
> occupancy, cost, environment) is this rule's semantic content; that this repository happens to
> implement that resolution as opposed to a bare field write is evidence of the rule holding,
> not the rule's own wording.

**Disposition: ACCEPT strongly, refined 2026-09-21 — "raw overwrite of a position field"
replaced with world-semantic language.** The original wording described the violation case in
implementation terms (a bare field write) rather than stating the positive semantic requirement
directly. The rule now states what movement *is* (a constrained transition) rather than what it
must not look like in code.

**Repository evidence: SUPPORTED, and explicitly declared as an architectural principle
already.** `MovementSystem.resolve_move()`'s own docstring cites "Logic ID: COMB-201 (Movement
intentions are distinct from results)" — the repository already treats a movement *intent* and
its *resolved outcome* as two different things, resolved through path lookup, a congestion
ladder, and environment multipliers, never a direct field write. This remains evidence for the
rule, not the rule's own definition.

**Scenarios:** [SPC-S06](../scenarios/space-environment-batch-04.md#spc-s06).

---

## MOV-03 — A movement attempt does not guarantee arrival

> Beginning or committing to a movement attempt does not entail reaching the intended
> destination. Obstruction, congestion, or interruption may prevent arrival even after the
> attempt has genuinely begun.

**Disposition: ACCEPT.** Direct instance of CAP-04 (capability doesn't guarantee success),
restated for movement specifically.

**Repository evidence: SUPPORTED.** The congestion ladder (`YIELDING`, `SIDESTEPPING`,
`WAITING`, `CONGESTION`, `PATH_EXHAUSTED` reason codes) is a real, multi-tier mechanism for
partial or failed arrival — movement resolution is explicitly designed around the possibility
that an attempt does not fully succeed.

**Scenarios:** [SPC-S06](../scenarios/space-environment-batch-04.md#spc-s06),
[SPC-S08](../scenarios/space-environment-batch-04.md#spc-s08).

---

## MOV-04 — Movement cost may accrue at declared stages of a movement process

> Movement cost may accrue at declared stages or portions of a movement process, including
> before eventual arrival or failure. This is COST-03's declared-lifecycle principle, applied to
> movement — a cost incurred at some declared stage is not refunded by a later interruption of
> the broader journey. This rule does not require a *per-step* accrual model specifically; a
> per-step model is one legitimate way to realize it, not the general Rule.

**Disposition: ACCEPT, refined 2026-09-21 — generalized beyond the per-step model this
repository happens to implement.** The original wording made "per committed step" the Rule
itself, when the underlying requirement is broader: cost accrues at whatever stages a movement
process declares (which could be per-step, per-leg-of-a-journey, on-commitment-only, or some
other declared schedule), and a later failure never retroactively un-incurs a cost already
accrued at an earlier declared stage. Per-step accrual remains this repository's own
implementation choice, kept as evidence, not elevated to the general Rule.

**Repository evidence: SUPPORTED for the per-step instance; this is one instance of the
general rule, not proof the general rule requires per-step accrual specifically.**
`MovementSystem.resolve_move()` applies `StaminaUpdate(current_delta=-entity.stamina.
MOVE_COST)` conditioned on `success` — meaning *this tick's step* succeeding, not the entity's
overall multi-tick destination being reached. An earlier tick's step can genuinely succeed (cost
paid) while a later tick's step toward the same ultimate destination is blocked (arrival never
occurs) — the earlier cost is never revisited or refunded. This confirms the general principle
via this repository's own chosen stage granularity (the step), not evidence that the stage must
always be a step.

**Amendment, terrain cost is declared by the terrain (decided by the owner directly, 2026-10-13;
row 72 of the memo):** Lane C found that the terrain cost table (`TERRAIN_COST`,
`src/core/state.py`) is keyed in upper case while compiled terrain is lower case, so forest,
swamp, mountain and road all cost 1.0 instead of 1.5, 3.0, 4.0 and 0.5, in 20 of 24 corpus
worlds. Roads give no advantage (`frontier_living_world`: 1,455 forest, 170 swamp and 947 road
tiles mispriced). Cave, ruin and river had no cost at all.
- **The cost lives in content:** each terrain declares its movement cost in terrain content.
  A terrain without one is a content error at compile, never a silent 1.0, and code reads no
  terrain names (decision 56).
- **Values:** the existing values are kept. New placeholders (decision 33): cave 1.5, ruin 1.5
  (rubble) and river 3.0 (wading, like swamp). A river stays walkable. Movement styles per body
  (a swimmer, a climber) come with milestone 1's body properties.
- **Sequencing:** it lands before baseline v1 as its own measured step, so v1 records the world
  as authored.
- **Alternatives not taken:** after v1 as a change against it; a river that blocks walking,
  which changes which places connect; keeping the code table with the three values added.
- **What the cost does (decided by the owner directly, 2026-10-14; row 75 of the memo):** with
  decision 72 built, the only reader is the readiness pre-check (`legality.py`, `readiness <
  move_cost * terrain_cost`). Movement spends no readiness (chapter 2, section 7), so that check
  refuses steps on rough ground when readiness is low but charges nothing. On
  `frontier_living_world` all 5 seeds move both ways; `urban_political` is byte-identical. Route
  choice ignores the cost.
  - **Ruling:** rough ground is slower, and routes are chosen by cost. A step on a tile costing
    N takes N times as long (road 0.5 is half, mountain 4.0 four times). Routes weigh the cost,
    so roads get used and mountains avoided.
  - **Sequencing:** before baseline v1, each part its own measured step: time first, then route
    choice. Decision 72 ships first as built, with its pre-check effect disclosed.
  - **Applied (rpg-designer):** the cost is paid in time, not gated on readiness. When the time
    step lands, the terrain multiplier leaves the readiness pre-check; the plain `move_cost`
    readiness check stays as it is.
  - **Road below one tick (decided by the owner directly, 2026-10-14):** the engine allows one
    step per entity per tick, so a cost below 1 cannot take less than a tick. A step on a tile
    costing N lets the next step come N ticks after entry (mountain 4; 1.5 alternates 1 and 2),
    and a cost below 1 is capped at one tick, so road and plain take the same time. Road's
    advantage comes through route choice. A faster road (more than one step per tick) is a
    possible later measured step, and the cap is disclosed. **Alternatives not taken:** two
    steps per tick on road; halving all walking (plain 2 ticks, road 1, mountain 8).
  - **Later:** tiring the body on rough ground (a fatigue cost) can be added on top later.
  - **Alternatives not taken:** slower only; route choice only; a fatigue cost now; both parts
    in one step; after v1.
- **Cover, high ground and walls (rpg-designer, 2026-10-14, applying decisions 33, 56 and 72):**
  Lane C found more terrain checks that compare upper-case names, which never match catalog
  terrain. Cover (`check_cover`, COMB-262: forest, mountain, "WALL") and high ground
  (`check_high_ground`: mountain, "HILL") never apply. No terrain is a wall. Walking is already
  blocked by structures through `blocked_tiles`, so the "WALL" branch of the walk check is dead,
  and the chokepoint finder (which looks for "WALL" tiles only) never finds one.
  - **Terrain declares it:** each terrain declares `gives_cover` and `high_ground` in content,
    and a missing value is a compile error. Code drops its terrain names, and the "HILL" name
    goes with them.
  - **Values (placeholders by each terrain's fiction):** forest, mountain, ruin (rubble and
    broken walls) and cave (rock walls) give cover. Mountain is high ground. Plain, grass, road,
    swamp, river, snow and volcanic ground give neither.
  - **Walls are structures:** the walk check reads only `blocked_tiles`, and the dead "WALL"
    branch is removed. This must be hash-identical.
  - **Chokepoints:** reading structures' `blocked_tiles` turns on a mechanic that has never run,
    so it is its own measured step, after cover and high ground.
  - **Sequencing:** the same reason as decision 72 (v1 records the world as authored). Cover and
    high ground land before baseline v1 as one measured step after the terrain route step, then
    chokepoints. Each reports cover and high-ground hits, perception, flight and pursuit counts
    per world. The rendering checks are a separate presentation cleanup.

**Scenarios:** [SPC-S08](../scenarios/space-environment-batch-04.md#spc-s08).

---

## MOV-05 — Physical traversal is not assumed to be the only movement mode

> Movement from one valid location/state to another does not have to occur through ordinary
> physical traversal of connected space. A different, explicitly declared mechanism (a
> supernatural transition, an abstracted "commit to a destination" mechanic) may establish
> another valid movement relation, provided it is a real, declared transition (MOV-02) and not a
> bare position overwrite.

**Disposition: ACCEPT.** Directly required by the batch instruction's own teleport/supernatural
probe — stated as a semantic permission, not a designed mechanism, matching ID-03's own
exception-slot pattern.

**Repository evidence: MISSING, confirmed directly.** No teleport, portal, or non-physical
movement mechanism exists anywhere in this repository — checked directly, every movement path
found resolves through `MovementSystem`'s grid-based, incremental step model. This rule states
the permission ahead of any mechanism, consistent with this Catalog's established practice of
not waiting for a mechanism to justify stating a boundary.

**Scenarios:** [SPC-S09](../scenarios/space-environment-batch-04.md#spc-s09) (teleport/
supernatural travel boundary — explicitly not designing Magic here).

---

## MOV-06 — Spatial reach instantiates, but does not redefine, foundational Reach

> Adjacency, line of sight, distance, and connected routes are how the Space domain supplies
> reach facts to other mechanisms (combat targeting, perception, movement itself). This is
> REACH-01–06 applied concretely to space — it does not restate or modify those foundational
> rules, only shows their spatial instance.

**Disposition: ACCEPT, by explicit deference — matching TRANS-03's deference to ID-03 and
HP-06's consolidation pattern.** This rule's entire content is "REACH-01/REACH-02 apply here,
concretely," not an independent claim.

**Repository evidence:** none newly gathered — reuses REACH-01/REACH-02's own evidence
(`LegalityServiceV2.verify_occupancy`/`is_adjacent`, `OUT_OF_RANGE`/`LOS_OBSTRUCTED`,
`PerceptionGate.can_perceive`'s distance falloff) directly.

**Scenarios:** [SPC-S01](../scenarios/space-environment-batch-04.md#spc-s01) (same scenario as
LOC-02 — reach and topology are both probed by the same near-but-unreachable case).

## MOV-07 — Adjacency is orthogonal, and every spatial check that asks "is it adjacent?" uses that same adjacency

> On the world grid, two positions are adjacent when they share an edge: the four cardinal
> neighbours. A diagonal neighbour is not adjacent. Melee reach, engagement, the end of a
> pursuit, and movement itself all use this one adjacency, so a subject that can step to a
> tile in one move is exactly a subject that could strike from it. A subject standing diagonal
> to its target must first step to an adjacent tile.
>
> A subject's position is always a whole tile. Every step moves it to an adjacent tile, so no
> movement leaves it between tiles, and every check that measures distance between positions
> measures the same whole-tile distance.

**Disposition: ACCEPT — decided by world-rule-catalog-design under owner delegation, 2026-10-06**
(row 20 of `docs/plans/systemic_world/owner_decision_memo.md`). This is MOV-06's adjacency fact
made explicit, because three call sites were found to depend on it at once. It adopts the
existing authoritative definition rather than inventing one:
`docs/combat/combat_movement_overhaul_spec.md:17-18` says "All distance checks (weapon range,
vision, movement) use L1 distance… Adjacency is strictly defined as cardinal neighbors…
Diagonal movement and adjacency are not supported."
- **Alternatives not taken:** Chebyshev melee reach (the 8-neighbourhood). Melee would then
  disagree with movement, which steps one axis at a time, and with the spec's orthogonal
  engagement and opportunity-attack definitions.
- **Scope:** this Rule fixes adjacency only. Ranges beyond adjacency, line of sight and
  perception falloff are unchanged.
- **Amendment, positions are tiles (decided by world-rule-catalog-design under owner delegation,
  2026-10-07; row 25 of the memo):** the whole-tile clause states the premise that the adjacency
  above already rests on. It is an amendment, not a new Rule: a step that does not land on a tile
  is not a step to an adjacent tile, so it already breaks this Rule's "movement itself". Every
  lookup that reads a position (occupancy, terrain, buildings, legality) reads whole tiles.
  **Alternative not taken:** accept sub-tile positions and choose floor, round or float for
  distance. That would make a leak legitimate and give every whole-tile lookup a second meaning
  to define.

**Repository evidence: SUPPORTED, for adjacency (with two known side-effect exceptions) and,
since #424 (`2a50072f2`, 2026-10-08), for the whole-tile clause.**
- **Supported:** melee legality uses Manhattan reach (`src/engine/legality.py`), and so does
  pursuit completion (#366). Movement steps orthogonally (`NavigationSystem.get_next_step`,
  `src/systems/world_systems/navigation.py:100-103`).
- **Exceptions (implementation, not semantics):** the yield push may displace an occupant to any
  of 8 neighbours (`src/engine/movement.py:123`), and the bracketing flank can land at distance
  2 on a diagonal. Both can leave a subject diagonal to its target, which this Rule handles: the
  subject steps first.
- **Supported since #424 (the whole-tile clause):** the flow-field step toward the town centre is a
  one-tile step along the flow vector's dominant axis (a tie takes y, as the local step does;
  `NavigationSystem.get_next_step`). Attack legality and pursuit reach both measure
  `LegalityServiceV2.get_manhattan_dist`, the distance between the tiles the positions stand on
  (`src/engine/legality.py`, `src/engine/candidate_selector.py::_target_in_attack_reach`). It is
  recorded as divergence 2.83 (`docs/guidelines/intentional_divergences.md`, Bug Fix), Bible 02's
  Whole-Tile Reach Distance, and parity entry COMB-337 (`docs/parity_ledger/combat_movement.yaml`,
  verified). It is pinned by `tests/unit/engine/test_attack_reach_distance.py` and
  `tests/unit/movement/test_flow_field_navigation.py`.
  - **Measured** (Lane A, relayed, not re-measured here; seed 42, 2,000 ticks, `audit_mode`, budget
    off, governor pinned NORMAL, main `753f98ea9` vs the fix, `crowded_frontier` /
    `frontier_living_world`): entities between tiles at any tick went from 1 / 3 to 0 / 0, and
    legality-versus-pursuit reach disagreements from 4 / 110 to 0 / 0. ATTACK decisions went from
    46 / 49 to 45 / 109 (a re-baseline). The fixed arm ran twice per world with identical digests.
  - **Re-baseline, disclosed by the ticket:** walks to the town centre now follow a Manhattan path,
    so trajectories diverge from older main, and SimQ grade anchors were not re-measured.
- **Previously CONFLICTING, as found on main `6e7ef56ec`** (seed 42, 2,000 ticks): the flow-field
  step added a unit vector (`navigation.py:92-96`) and left the subject between tiles for good. By
  t=2000, 9 of 41 entities on crowded_frontier and 13 of 55 on frontier_living_world were between
  tiles. Legality truncated the distance (`legality.py:45`) and pursuit reach
  (`candidate_selector.py:116`) did not, so they disagreed 59 times, and 1 of 17 and 4 of 28
  ATTACK decisions were allowed only because of the truncation. Fixed by
  `TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT` (Lane A).
- **The defect this exposed is engineering:**
  `TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED`. A held
  ATTACK task against an OUT_OF_RANGE target was never re-decided, and one entity re-swung at a
  diagonal target 267 times. OUT_OF_RANGE must lead to a re-decision or a closing step.

**Scenarios:** SPC-S17 (`docs/world_rules/scenarios/space-environment-batch-04.md`, 2026-10-11),
covered since #385: an attacker diagonal to its target steps one orthogonal tile, then strikes
within two brain cadences, and never swings from the diagonal (OUT_OF_RANGE ends the task).

---

## Cross-domain links recorded here

- MOV-01 → Authority, Reach, Capability, Cost (the five families this rule's own boundary
  reuses directly)
- MOV-02, MOV-03 → Causality (CAUSE-01), Capability (CAP-04, directly reused)
- MOV-04 → Cost (COST-03, directly reused)
- MOV-05 → Magic/supernatural (the most plausible future domain to fill this gap)
- MOV-07 → Reach (REACH-01/02, through MOV-06), Conflict/Combat (`conflict-combat.md`: melee reach
  is this adjacency)
- MOV-06 → Reach (REACH-01–06, explicit deference, not a new link)

## Open questions carried forward

1. MOV-05's confirmed absence of any non-physical movement mechanism is the same underlying gap
   LOC-02/LOC-06 already found from the topology side — recorded once conceptually (a future
   Magic/supernatural or Places mechanism would likely need to satisfy both this family's
   MOV-05 and Location/Topology's LOC-02/LOC-06 together), tracked as separate rules because
   they are separate semantic claims.
2. Whether the congestion ladder's specific tiers (yielding, sidestepping, waiting, congestion,
   path-exhausted) should themselves be treated as world-semantic categories or purely
   implementation detail was not resolved here — this batch treats the ladder's *existence* as
   evidence for MOV-03, not its specific tier structure as semantically meaningful.
