---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-10-07"
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

**Repository evidence: SUPPORTED for adjacency, with two known side-effect exceptions;
CONFLICTING for the whole-tile clause until its ticket lands.**
- **Supported:** melee legality uses Manhattan reach (`src/engine/legality.py`), and so does
  pursuit completion (#366). Movement steps orthogonally (`NavigationSystem.get_next_step`,
  `src/systems/world_systems/navigation.py:100-103`).
- **Exceptions (implementation, not semantics):** the yield push may displace an occupant to any
  of 8 neighbours (`src/engine/movement.py:123`), and the bracketing flank can land at distance
  2 on a diagonal. Both can leave a subject diagonal to its target, which this Rule handles: the
  subject steps first.
- **Conflicting (the whole-tile clause):** one movement path breaks it. The flow-field step toward
  the town centre, taken when the distance is over 50 (`navigation.py:92-96`), adds a unit vector
  and leaves the subject between tiles for good. Lane A measured this on main `6e7ef56ec` (seed
  42, 2,000 ticks): by t=2000, 9 of 41 entities on crowded_frontier and 13 of 55 on
  frontier_living_world are between tiles, against 0 at the start. Two reach checks then
  disagree: legality truncates the distance (`src/engine/legality.py:45`) and pursuit reach
  (`src/engine/candidate_selector.py:116`) does not. They disagreed 59 times, and 1 of 17 and 4
  of 28 ATTACK decisions were allowed only because of the truncation. The fix is engineering:
  `TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT` (Lane A).
  The flow step becomes a step along one axis, and one shared distance serves every reach check.
  Long walks to the town centre then follow a Manhattan path, so the corpus re-baselines.
- **The defect this exposed is engineering:**
  `TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED`. A held
  ATTACK task against an OUT_OF_RANGE target was never re-decided, and one entity re-swung at a
  diagonal target 267 times. OUT_OF_RANGE must lead to a re-decision or a closing step.

**Scenarios:** none traced yet. One is owed when the ticket lands: an attacker diagonal to its
target steps one orthogonal tile, then strikes, and never swings from the diagonal.

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
