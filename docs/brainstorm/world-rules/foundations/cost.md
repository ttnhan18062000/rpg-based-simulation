---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Cost

**Purpose/scope.** What must be consumed, risked, committed, degraded, or foregone for an action
or process to occur — broader than currency, and explicitly distinct from a precondition (what
must already be true to attempt something) and a consequence (a downstream effect the action
produces, not what the action itself pays).

**Status.** Foundational Batch 03, first draft. Candidates below originated as external-reviewer
hypotheses (`tmp/world-rule-batch-3-ext-ai.md`); each carries this session's disposition and
repository evidence, not the original wording uncritically kept.

---

## COST-01 — Cost is broader than currency

> Resource consumption, time, energy, health, durability, attention, opportunity cost, risk, and
> social/political consequence are all legitimate cost categories. Gold/currency is one instance,
> not the definition.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED, across several categories already.** *Energy/stamina:*
`StaminaService.drain_attack/drain_move/drain_harvest/drain_skill`. *Durability:* equipment wear
from use (referenced throughout Batch 01's Objects-domain evidence). *Time:* skill cooldowns
(`cooldowns: Dict[skill_id, tick_when_ready]`, Batch 02's TIME-03). *Currency:* gold costs in
crafting/shop transactions (`resource_conservation_contract.md`). No repository evidence yet for
attention or social/political consequence as an explicit *cost* category specifically (as
opposed to a consequence) — flagged, not fabricated.

**Scenarios:** [CTR-S05](../scenarios/foundational-batch-03.md#ctr-s05).

---

## COST-02 — Precondition, cost, and consequence are three distinct things

> Whether an action may be attempted (precondition), what the action itself consumes when it
> proceeds (cost), and what the action produces downstream (consequence) are not automatically
> the same thing, and a single action may have any combination of the three.

**Disposition: ACCEPT strongly.** This is the core distinction the batch instruction asked this
family to establish, and it is cleanly evidenced by the same repository mechanism from three
angles at once.

**Repository evidence: SUPPORTED, with all three roles visible in one action.**
`skill_actions.py`'s attack-skill handler: the **precondition** is `StaminaService.
can_use_skill(stamina, skill_cost)` (checked before anything proceeds); the **cost** is
`stamina_update=StaminaUpdate(current_delta=-stamina_cost)` (paid by the attacker, once the
action is committed); the **consequence** is the wound/combat outcome applied to the *defender*
(`defender_up`'s `wound_update`/`combat`) — a completely separate entity, a completely separate
`EntityUpdate`, produced by the same action that paid the attacker's cost. Precondition, cost,
and consequence are three distinct code paths here, not three names for the same check.

**Scenarios:** [CTR-S05](../scenarios/foundational-batch-03.md#ctr-s05).

---

## COST-03 — Costs are incurred according to the declared lifecycle of the attempted action

> Costs are incurred according to the declared lifecycle of the attempted action/process. A
> proposal rejected before execution does not silently incur execution cost, unless making the
> proposal/attempt itself has an explicitly declared cost. A committed attempt that later fails
> to achieve its intended outcome is not the same case as a proposal rejected before execution —
> a committed attempt may legitimately have already consumed time, stamina, mana, durability,
> attention, or risk exposure by the point it fails, and failure does not retroactively refund
> those.

**Disposition: ACCEPT, refined 2026-09-21 — the original wording was too universal.** "A cost is
paid only when the action is actually committed... a rejected attempt never incurs the action's
cost" was correct for the *rejected-before-execution* case but was overbroad if read as "failure
never costs anything" — those are two different cases. A proposal that never gets past a
precondition check (self-attack, insufficient stamina to even attempt) correctly incurs no cost.
A committed action that proceeds, consumes its declared costs, and *then* fails to land its
intended effect (a committed attack that consumes stamina but misses) is a different case
entirely — the cost was already incurred by the point of commitment, and the later failure of
the *consequence* doesn't undo that. The rule now distinguishes these explicitly rather than
treating "rejected" and "failed" as the same outcome.

**Repository evidence: SUPPORTED, for both cases distinctly.** *Rejected before execution:*
`resource_conservation_contract.md`'s atomicity gate (Gate 4) — "If any check fails, the world
state is unchanged — no item vanishes, no charge is consumed, no gold is spent"; `can_use_skill()`
is checked *before* `drain_skill()`'s cost is applied, so a rejected attempt never reaches the
deduction step at all. *Committed attempt that later fails:* `skill_actions.py`'s attack handler
deducts `stamina_cost` (`StaminaUpdate(current_delta=-stamina_cost)`) on the attacker's
`EntityUpdate` as part of committing the action, *before* and independent of whatever the
defender's combat-resolution outcome turns out to be — the stamina cost is paid whether or not
the attack actually connects.

**Scenarios:** [CTR-S05](../scenarios/foundational-batch-03.md#ctr-s05),
[CTR-S17](../scenarios/foundational-batch-03.md#ctr-s17) (added 2026-09-21 — a failed committed
attempt that still costs something).

---

## COST-04 — Not every action requires a cost

> A cost is not a universal requirement of action. Many transitions are legitimately free.

**Disposition: ACCEPT.** Stated explicitly per the batch instruction, to head off a future
domain author assuming every action needs an invented cost to feel "complete."

**Repository evidence: SUPPORTED, by absence rather than by a positive mechanism.** Many
navigation, perception, and query-style actions in the repository carry no cost field at all —
cost is opt-in per action type, not a mandatory property every `EntityUpdate`-producing action
must declare.

**Scenarios:** none newly traced; this is a negative claim confirmed by the absence of a
universal cost requirement anywhere in the action-handling code, not something a scenario trace
would add evidence to.

---

## COST-05 — A cost paid by the actor and a consequence experienced by another subject are independently tracked

> When an action's cost falls on the acting subject and its consequence falls on a different
> subject, the two are tracked as genuinely separate facts about two different subjects, not one
> shared "cost of the interaction."

**Disposition: ACCEPT.** This sharpens COST-02 for the specific (and common) case where cost and
consequence land on different subjects entirely — worth stating on its own since it is the shape
most combat/social interactions will take.

**Repository evidence: SUPPORTED**, by the same `skill_actions.py` evidence as COST-02: the
attacker's stamina cost and the defender's wound consequence are two separate `EntityUpdate`
objects, keyed by two different entity ids, applied through the same authoritative apply step but
never merged into one record.

**Scenarios:** [CTR-S05](../scenarios/foundational-batch-03.md#ctr-s05) (same scenario as
COST-02/COST-03 — one repository mechanism answering three related but distinct Cost-family
questions at once).

---

## Cross-domain links recorded here

- COST-01 → Objects & material culture (durability), Capability & progression (time/cooldowns),
  Economy/resources (currency)
- COST-02, COST-05 → Conflict & combat (the attacker-cost/defender-consequence shape), Causality
  (CAUSE-01 — a consequence still needs a real producer, which COST-02 doesn't relax)
- COST-03 → Resource (the atomicity guarantee `resource.md` also relies on)

## Open questions carried forward

1. COST-01's attention and social/political-consequence categories are named by the starter
   hypothesis but not yet repository-evidenced as *cost* specifically (as opposed to a
   consequence of some other action) — flagged for whichever future domain (Agency/decision,
   Politics/authority & war) first models an action that spends attention or political capital as
   its own cost, rather than assumed to already exist.
