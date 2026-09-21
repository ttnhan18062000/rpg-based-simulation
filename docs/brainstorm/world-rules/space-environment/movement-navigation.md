---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
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

## MOV-02 — Movement requires a valid world-semantic transition, never raw location assignment

> A movement outcome is the result of resolving a real transition (checking path, occupancy,
> cost, environment), not a bare overwrite of a position field.

**Disposition: ACCEPT strongly.**

**Repository evidence: SUPPORTED, and explicitly declared as an architectural principle already.**
`MovementSystem.resolve_move()`'s own docstring cites "Logic ID: COMB-201 (Movement intentions
are distinct from results)" — the repository already treats a movement *intent* and its
*resolved outcome* as two different things, resolved through path lookup, a congestion ladder,
and environment multipliers, never a direct field write.

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

## MOV-04 — Movement cost may be incurred per committed step, even when the overall attempt is later interrupted

> Where movement resolves incrementally (step by step, tick by tick), the cost of a step that
> genuinely succeeds is incurred at that step, independent of whether a later step in the same
> overall attempt fails. This is COST-03's declared-lifecycle principle, applied to movement
> specifically — a committed step's cost is not refunded by a later interruption of the broader
> journey.

**Disposition: ACCEPT.** Directly required by the batch instruction's own cross-batch challenge
("movement attempt begins/commits → declared cost incurred → interruption prevents arrival").

**Repository evidence: SUPPORTED.** `MovementSystem.resolve_move()` applies
`StaminaUpdate(current_delta=-entity.stamina.MOVE_COST)` conditioned on `success` — meaning
*this tick's step* succeeding, not the entity's overall multi-tick destination being reached. An
earlier tick's step can genuinely succeed (cost paid) while a later tick's step toward the same
ultimate destination is blocked (arrival never occurs) — the earlier cost is never revisited or
refunded.

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

---

## Cross-domain links recorded here

- MOV-01 → Authority, Reach, Capability, Cost (the five families this rule's own boundary
  reuses directly)
- MOV-02, MOV-03 → Causality (CAUSE-01), Capability (CAP-04, directly reused)
- MOV-04 → Cost (COST-03, directly reused)
- MOV-05 → Magic/supernatural (the most plausible future domain to fill this gap)
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
