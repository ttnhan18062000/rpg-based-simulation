---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Capability

**Purpose/scope.** What it means for a subject or process to be *capable* of producing a
transition — semantic eligibility, not an implementation API. Capability is deliberately kept
distinct from Authority (legitimacy, `authority.md`), Reach (possibility of affecting a target,
`reach.md`), and Resource (availability of consumable substance, `resource.md`) — a subject may
have any one of these without the others, and this family exists to keep that boundary explicit
rather than letting later domains blur it.

**Status.** Foundational Batch 03, first draft. Candidates below originated as external-reviewer
hypotheses (`tmp/world-rule-batch-3-ext-ai.md`); each carries this session's disposition and
repository evidence, not the original wording uncritically kept.

**Explicit non-goal, per the batch instruction.** Do not design skills/combat/progression
mechanics here — Capability states semantic eligibility only; concrete skill trees, combat
formulas, and progression curves belong to Capability & progression and Conflict & combat, later
domains that will consume this family's boundary, not redefine it.

---

## CAP-01 — Capability is distinct from authority

> Being mechanically able to attempt a transition (capability) and being legitimately authorized
> to cause it (authority) are independent facts. This restates AUTH-01 from the Capability side
> of the same boundary — the two families were drafted together in Batch 02/03 specifically so
> neither would have to re-derive the other's half.

**Disposition: ACCEPT.** Not a new idea — AUTH-01 (`authority.md`) already established this;
recorded here so a Capability-focused author has the boundary stated from their own side too.

**Repository evidence: SUPPORTED**, reusing AUTH-01's own evidence: `LegalityServiceV2`'s
`FRIENDLY_FIRE_ILLEGAL`/`SELF_ATTACK_ILLEGAL` reject a mechanically-capable, fully-in-range
attack purely on authority grounds — capability was never in question in that evidence.

**Scenarios:** [CTR-S01](../scenarios/foundational-batch-03.md#ctr-s01),
[CTR-S02](../scenarios/foundational-batch-03.md#ctr-s02) (the other direction: authorized but
currently incapable).

---

## CAP-02 — Capability is distinct from opportunity/reach

> Being able to perform an action, in the abstract, does not mean the present situation gives a
> subject the opportunity to exercise it against a particular target — that is Reach's question
> (`reach.md`), not Capability's.

**Disposition: ACCEPT.** Restates REACH-01/AUTH-04's boundary from the Capability side.

**Repository evidence: SUPPORTED**, reusing REACH-01's evidence: `LOS_OBSTRUCTED`/`OUT_OF_RANGE`
reject an attempt from a fully-capable actor purely on reach grounds.

**Scenarios:** [CTR-S14](../scenarios/foundational-batch-03.md#ctr-s14) (the explicit
`capable ≠ reachable` cross-batch check the instruction required).

---

## CAP-03 — Capability is distinct from resource availability

> Knowing or being able to perform a technique does not mean the resource that technique requires
> is currently available. Capability is the eligibility to act; Resource (`resource.md`) is the
> substance the act consumes — a subject may hold one without the other.

**Disposition: ACCEPT.** This is the boundary the batch instruction most specifically asked
Capability to establish against the new Resource family.

**Repository evidence: SUPPORTED.** `StaminaService.can_use_skill(stamina, skill_cost)` checks
capability-adjacent readiness, but a crafting or shop-purchase attempt is gated *separately* by
`resource_conservation_contract.md`'s Gate 3 (source existence/stock check) — an entity can know
a recipe (capability) while lacking the materials or gold (resource), and the two checks never
collapse into one.

**Scenarios:** [CTR-S03](../scenarios/foundational-batch-03.md#ctr-s03).

---

## CAP-04 — Capability does not guarantee success

> A subject being eligible to attempt a transition does not mean the attempt necessarily
> succeeds. Capability establishes that an attempt is possible, not that its outcome is assured.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `can_use_skill()` and `can_equip_item()` gate *whether an
attempt may be made at all* — they say nothing about combat resolution's own contested outcome
(readiness, defense, resistance) once the attempt proceeds. A capable, authorized, in-range actor
can still miss, be resisted, or fail a check downstream of capability being satisfied.

**Scenarios:** [CTR-S05](../scenarios/foundational-batch-03.md#ctr-s05) (the cross-batch check
`cost paid ≠ outcome guaranteed`, folded into the same scenario as Cost's own probe).

---

## CAP-05 — Capability may depend on several independent factors, not all of which are confirmed to matter equally

> A capability may depend on subject state, learned ability, equipment, body/form, environment,
> relationships, or institutional support. These are independent potential sources, not a fixed
> checklist every capability must draw from.

**Disposition: ACCEPT, with evidence recorded per factor rather than as one blanket claim —
the honest finding this batch made is that not all seven listed factors are equally evidenced.**

**Repository evidence, per factor:**
- **Subject state:** SUPPORTED (`can_use_skill`'s stamina check).
- **Learned ability:** SUPPORTED (`SKILL_NOT_LEARNED` reason code).
- **Equipment:** SUPPORTED (`can_equip_item`'s slot-requirement check).
- **Body/form:** PARTIAL. `EvolutionSystem` changes an entity's `kind`, but this session
  confirmed as far back as Batch 01 (ID-02) that nothing currently *reads* the evolved kind to
  gate any capability — the architecture supports body/form-gated capability, but no live
  consumer exercises it yet.
- **Environment:** MISSING as a capability gate specifically. `TerrainCostService` (`src/engine/
  rpg_depth.py`) modifies movement *cost*, not whether an action is capability-eligible at all —
  checked directly, no capability check anywhere reads terrain/environment as an eligibility
  condition. This is a real, confirmed gap, not an oversight in this write-up.
- **Relationships, institutional support:** MISSING as direct capability gates. (Institutional
  *authority* is real — AUTH-06 — but authority is not capability; nothing currently makes an
  institution's support a precondition for a subject's own capability to act.)

**Scenarios:** [CTR-S03](../scenarios/foundational-batch-03.md#ctr-s03),
[CTR-S04](../scenarios/foundational-batch-03.md#ctr-s04).

---

## Cross-domain links recorded here

- CAP-01 → Authority (AUTH-01, shared boundary and evidence)
- CAP-02 → Reach (REACH-01, shared boundary and evidence)
- CAP-03 → Resource (the new family this batch introduces)
- CAP-05 → Capability & progression (a future domain that will need to decide whether body/form
  and environment become real capability gates, not inherit this batch's confirmed absence as
  permanent)

## Open questions carried forward

1. CAP-05's body/form and environment gaps are confirmed MISSING, not merely unexplored — flagged
   for the Capability & progression and Space/environment batches respectively, whichever is
   reached first.
2. Whether relationships/institutional support should ever become a direct capability gate
   (rather than only an authority one) is not decided here — deferred to whichever future domain
   first needs it (most plausibly Groups/organizations & institutions).
