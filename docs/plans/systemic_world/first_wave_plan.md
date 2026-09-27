---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
last_verified: "2026-09-27"
---

# Systemic World — First-Wave Epic Plan — PROPOSED / FOR REVIEW

**Status: `PROPOSED / FOR REVIEW`. Not owner-approved.** The frontmatter `status: active` is the
repository's "live working document" value. The schema has no "proposed" value, and `active` does
not mean approved; only the visible status above does. A schema correction is proposed separately.

**What this document is.** The epic-level plan for the first wave recommended by
`docs/plans/systemic_world/roadmap.md` §8. It defines epics, their outcomes and boundaries,
cross-epic dependencies, proof gates, and failure branches.

**What it is not.** It is not a ticket list and prescribes no code change, schema, test file or API.
A separate ticket planner decomposes approved epics into tickets, and two implementation agents
implement and verify them. Handoff material is in `ticket_planner_handoff.md`; genuine owner choices
are in `owner_decision_memo.md` (both in this folder). Nothing here starts before the owner reviews
this plan.

---

## 1. The four proof claims, and what this wave does with each

| # | Proof claim | First-wave treatment |
|---|---|---|
| 1 | **World correctness.** Real natural aging and succession, and bounded temporal composition, with no forced player surface. | **Establishes it**, for life/death continuity (Epic A) and for three named authority boundaries (Epic C). |
| 2 | **Evidence-path design.** A plausible, domain-owned route from a world event to a legitimate, viewpoint-scoped clue. | **Establishes it at design level** (Epic B): a decision and a downstream ticket set, not a built path. |
| 3 | **Player inference.** A blinded human reasons from only the legitimately encounterable clues. | **Prepares only.** `BLOCKED` today, because no clue is encounterable (roadmap §7.2). It becomes `PENDING` once a path is built, and is resolved only by a real human exercise. |
| 4 | **Changed life trajectory.** A later opportunity or decision, and a durable outcome. | **Future work.** Not claimable from a death→heir transfer or a differentiated reaction. |

A hidden foundation can be complete on world-side evidence without ever being surfaced to a player.
Fair evidence is required only where player understanding is an intended outcome.

---

## 2. First-wave epics

### Epic A — Authoritative life, death and cross-tick world continuity

**Outcome.** Every death reached through ordinary world processes is recorded under one declared
authority, with a cause and a time. Its lineage consequences follow and persist across later ticks.
This is shown for a bounded two-hop sequence (predecessor → heir → next heir). It advances the north
star's persistence and history claims: ordinary subjects accumulate consequential history without
anyone watching.

**Semantic contract.** A persistent fact has one canonical authority, and a world effect never
commits from a stale assumption without a declared resolution rule (roadmap §3.1). Lineage
consequences are specified in the Mechanics Bible (`05_world_evolution.md`) and in roadmap §3.2.

**Domain owners.** Engine-core authoritative apply; lifecycle/lineage.

**In scope**:
- natural-aging death, meaning cause, time, and succession;
- a regression check of other death causes;
- one bounded composed two-hop run.

**Out of scope**:
- player surfacing;
- natural frequency or population-wide emergence;
- multi-generation arcs;
- the closed-loop trajectory proof;
- a general apply-path redesign.

**Known evidence** (by roadmap §3 layer):

| Finding | Status | Evidence layer |
|---|---|---|
| Single death→heir hop works in staged state | Verified | Runtime realization, scenario |
| Natural-aging death is recorded with no cause and no succession | Defect reproduced (seed 42) | Runtime realization, scenario |
| Two-hop composition through ordinary aging | `BLOCKED` by the defect above | Cross-domain composition |
| Starvation/sleep-debt death may be equally silent | `UNKNOWN` (inspection only) | Runtime realization |
| Spawns created inactive may depend on today's behaviour | `UNKNOWN` (inspection only) | Runtime realization |

**Completion evidence (finite).**
- A bounded run shows natural-aging death with a recorded cause and working succession, with no
  silent inactive state.
- A bounded two-hop run through ordinary ticks preserves identity, chronology, and at least one
  carried-forward effect.
- Verified and unverified death paths are named.
- Registry evidence for `aging_death`/`succession` is updated.

**Failure branches — return to the roadmap, do not expand scope.**
- If resolving the defect turns out to require deciding what an inactive-at-spawn entity *means* in
  the world, that is a semantic question for the roadmap/owner, not an engineering default.
- If a second, different composition blocker appears, record it `BLOCKED_WITH_REASON` and re-plan.

**Gate.** Composed-run verification happens only after natural-aging death is correct. That gate is
internal to Epic A. **Epic A is never gated on Epic B.**

### Epic B — Situated evidence and observer contract (design)

**Outcome.** An agreed, domain-owned route from one world event to a legitimate, viewpoint-scoped
clue, together with an observer contract:
- who could encounter the clue, where, and when;
- what stays hidden;
- what must never leak.

It is established first on one probe event and written to be reusable by later epics, such as
individual history propagation. It advances the north star's situated-inference claim without
claiming player understanding.

**Semantic contract.** The epistemic principle (roadmap §2):
- every surface is a projection with a viewpoint;
- no omniscient surface reveals hidden truth;
- private events may stay private;
- direct participation, uninvolved witnessing, and hearsay stay distinct (roadmap §3.4).

**Domain owners.** Perception/observation, and the domain that owns the probe event (lifecycle/
lineage by default).

**In scope**:
- choose the probe event;
- choose the minimum evidence-production and carrier route;
- the observer contract;
- a downstream ticket set for building it.

**Out of scope**:
- building the route;
- any player-facing surface or renderer;
- a permanent gameplay lens;
- a global history, event or reputation feed;
- the human exercise itself.

**Known evidence** (roadmap §7.2, read-only inspection 2026-09-27):

| Finding | Status | Evidence layer |
|---|---|---|
| The inheritance state change is real | Verified | Runtime realization |
| No in-world carrier delivers another entity's inventory/equipment to an observer; the perception update phase has no production caller | `BLOCKED` | Situated evidence |
| No inheritance-origin signal exists | `ABSENT` | Situated evidence |
| Inference | `BLOCKED` | Player inference |
| The existing grief trigger reaches trusted allies regardless of location — a possible epistemic-principle conflict | `UNKNOWN`; owner: §3.4 track | Situated evidence |

**Completion evidence (finite).**
- A recorded design decision naming the probe event, the route, the owning domains, the viewpoint
  scope and the non-leak list.
- A downstream ticket set ready for the ticket planner.
- An explicit player-side status: `BLOCKED` until the route is built, then `PENDING` until a human
  exercise runs.

**Failure branches.**
- If the owner decides the default probe event (inheritance) should remain a private world fact
  (owner memo, decision 2), Epic B re-selects a probe event whose understanding *is* intended. It
  does not force inheritance to become visible.
- If no domain-appropriate route is acceptable to its owners, return the objection to the roadmap.

**Gate.** None inside the wave. Its built route (future) feeds the later player-inference proof.

### Epic C — Authority-boundary verification program (reusable foundation)

**Outcome.** Named cross-domain boundaries each resolve to `CONFIRMED_FINE_WITHIN_SCOPE`,
`DEFECT_CONFIRMED` (routed separately) or `BLOCKED_WITH_REASON`. Each outcome is bounded and stated,
never "no such defect exists in the engine."

**Semantic contract.** The same authority invariant as Epic A, applied at boundaries where more than
one producer writes a durable fact.

**Domain owners.** One per boundary, each **independently scheduled and independently complete**:

| Boundary | Owner | Current status (roadmap §3.1 audit) |
|---|---|---|
| Entity death, `alive_set` (combat vs hazard) | combat + world dynamics | `UNKNOWN_WITH_REASON` |
| Faction diplomacy, `diplomatic_relations_set` (autonomous transition vs auto-alliance) | faction | `UNKNOWN_WITH_REASON` |
| Public reputation, `reputation_set` (two producers) | social | `UNKNOWN_WITH_REASON`. A mechanical check only; the world meaning of `public_reputation` stays an open owner question |

**Out of scope**:
- fixing defects found (routed to separate work);
- region ownership / FAC-010, which stays on its existing track;
- boundaries not in the named set.

**Completion evidence (finite).** Each boundary has one bounded outcome and reason, recorded back
into roadmap §3.1. A harness limitation is never reported as fine. The program does not wait for all
three before any one completes.

**Gate.** None; no dependency on Epic A or B.

---

## 3. Cross-epic dependencies

```text
Epic A: natural-aging death correct ──internal gate──> composed two-hop run    (world side)
Epic B: evidence route + observer contract (design)                             (player side, design)
Epic C: boundary 1 · boundary 2 · boundary 3, each independent                  (foundation)

Hard edges inside the wave: only Epic A's internal gate.
No world-side work (A, C) waits on Epic B.
Future: Epic B's route built  ──> human inference exercise (claim 3)
        Epic A + built route  ──> observer follow-on on the composed sequence
```

---

## 4. Why these three epics, and the tradeoffs

- **Lineage is one probe, not the organizing axis.** It is the only trajectory with a real
  mechanism-level proof (roadmap §7.4). Two blockers make it useful precisely because each is a
  general problem: a world-side authority defect (Epic A), and a missing situated-evidence route
  (Epic B). Solving them produces reusable foundations for other domains.
- **Epic C is foundation work that serves every domain.** Its three checks are cheap, independent,
  and directly answer §3.1's open enforcement question.
- **Alternative first waves considered.**
  - Individual history propagation (roadmap §3.4's witness/hearsay producer gap) is larger. It would
    also need Epic B's observer contract, so it sits later.
  - Wealth/office conversion lacks its declared conversion edges entirely (`ME-S12`), which makes
    it a realization program rather than a first proof.
- **The first-wave choice is open (owner memo decision 1).** This plan details option (a).
  - Since it was written, the planner has leaned towards option (b), reachability-first. The reasons
    are roadmap §11 items 1, 3 and 5: no visible payoff, a possible engine-level perception gap, and
    "done" mechanisms that don't fire.
  - If (b) is chosen, this plan is revised: Epic C stays, perception verification moves in, and
    Epics A and B move later.
  - Separately, Epic B's probe event depends on memo decision 2, and whether lineage can ever be
    shown unstaged depends on decision 5.

---

## 5. Candidate workstreams (historical labels, for the ticket planner)

Earlier drafts used milestone labels M1, M4a, M2, and M3a/b/c. They remain useful as candidate
workstreams, not as a ticket list:
- M1 and M4a belong to Epic A.
- M2 belongs to Epic B.
- M3a/b/c belong to Epic C.

The earlier "M4b" (closed-loop groundwork) is future portfolio work, not a first-wave item. The
ticket planner decides actual ticket granularity.

---

## 6. Feeding results back

- Verified epic outcomes are recorded in roadmap §3.1 (the authority audit) and §7 (the gate tables).
- Mechanism-registry evidence changes go through the registry's normal process.
- SCP mappings are added only through the SCP's own validation. None of the first-wave fields is
  currently SCP-mapped, and mapping coverage is not a completion gate.

Unreviewed prototype results are never recorded as fixes. Implementer findings come back through
the ticket planner.
