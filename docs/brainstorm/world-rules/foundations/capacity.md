---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Capacity / Limits

**Purpose/scope.** What bounds how much state, activity, influence, accumulation, or concurrent
commitment a subject or process can sustain. Uses the `LIMIT-` prefix (not `CAP-`) specifically
to avoid collision with the Capability family's `CAP-` prefix — the two are easy to conflate by
name alone, and this batch treats that as reason enough to keep their IDs visually distinct.

**Status.** Foundational Batch 03, first draft. Candidates below originated as external-reviewer
hypotheses (`tmp/world-rule-batch-3-ext-ai.md`); each carries this session's disposition and
repository evidence, not the original wording uncritically kept.

**Explicit non-goal, per the batch instruction.** Do not create one universal `Capacity` stat —
this family's own headline finding is that the repository already avoids that trap, and the
family exists to state why that's correct rather than to invent a counterexample.

---

## LIMIT-01 — Capacity is domain-specific, not a single universal quantity

> A subject's ability to sustain concurrent commitments is expressed as several independent,
> domain-specific bounds — not one generic "Capacity" number that every kind of limit draws down
> from.

**Disposition: ACCEPT.** This is the rule the batch instruction most explicitly required, and it
is unusually well-evidenced: the repository already implements exactly this shape.

**Repository evidence: SUPPORTED.** `CapacityService.derive_profile()` (`src/strategy/
cognition_capacity.py`) produces `max_active_projects`, `max_leads`, `max_concerns`,
`max_candidate_zones`, and `max_hypotheses` — five genuinely independent bounds on one
`CognitionProfile`, each derived from a different combination of attributes (`avg_mind` for
projects, `perception` for leads, `wisdom` for concerns), never collapsed into one shared pool.

**Scenarios:** [CTR-S06](../scenarios/foundational-batch-03.md#ctr-s06).

---

## LIMIT-02 — Capacity may be derived from subject state and degrade under strain

> A capacity bound is not necessarily fixed for a subject's lifetime; it may be computed from
> current state and reduced when that state is under strain.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `CapacityService.derive_profile()`'s `fatigue_multiplier`
reduces every derived limit (0.5× when sleep debt or hunger exceeds 70, 0.8× above 40) — capacity
is a live function of biological state, not a static ceiling set once at creation.

**Scenarios:** [CTR-S06](../scenarios/foundational-batch-03.md#ctr-s06).

---

## LIMIT-03 — Exceeding or approaching a declared limit must have explicitly defined semantics

> Exceeding or approaching a declared limit must have explicitly defined semantics — never
> silently accepted past the bound or silently dropped without a traceable cause. This does not
> mean one universal response: rejection, degradation, displacement, overflow with consequence,
> temporary oversubscription, a hard cap, and a soft cap are all legitimate domain-specific
> responses, and a given limit may use a different one than another.

**Disposition: ACCEPT, generalized 2026-09-21 — no longer implies one universal response.** The
original wording listed "rejection, eviction, degradation" as though exceeding capacity always
meant one of those three specific outcomes. That's this repository's own current choice for
cognition capacity specifically, not a universal law — a different domain may legitimately allow
temporary oversubscription with an increasing risk/cost penalty (a soft cap) rather than hard
rejection. The requirement that survives generalization is only that *some* explicit, declared
handling exists — never an assumed default and never silent overflow.

**Repository evidence: SUPPORTED for this repository's own hard-cap choice; a soft-cap
alternative is confirmed possible in principle, not yet exercised by a live mechanism.**
*Hard cap, exercised:* `CapacityEnforcementPhase` (`src/engine/pipeline_phases/
capacity_enforcement.py`) explicitly checks `len(entity.strategic.leads) + len(strat_upd.
leads_add_or_update) > profile.max_leads` (and the same shape for `concerns`/`projects`) before
allowing an addition; `DetourService` (`src/systems/strategic_systems/detour.py`) computes
`excess = active_leads[profile.max_leads:]` and handles it explicitly. *Soft cap:* not currently
implemented anywhere in the repository — recorded as MISSING rather than assumed, per the new
scenario this pass adds specifically to probe it.

**Scenarios:** [CTR-S07](../scenarios/foundational-batch-03.md#ctr-s07),
[CTR-S20](../scenarios/foundational-batch-03.md#ctr-s20) (added 2026-09-21 — a soft capacity
limit, confirming this rule does not force hard rejection).

---

## LIMIT-04 — Crossing a threshold is not automatically a cause unless a rule declares it to be

> A resource reaching zero, a capacity being exceeded, an accumulation crossing a numeric
> threshold, or a condition persisting long enough may *enable* or *trigger* a transition, but
> the threshold-crossing itself is not automatically the cause of that transition unless the
> relevant world rule explicitly defines it that way. This is CAUSE-01's real-causal-path
> requirement, applied specifically to threshold-crossing, and it is deliberately housed here
> (Capacity) rather than given its own family — investigated explicitly, per the batch
> instruction, and found to be a cross-cutting causal discipline rather than a first-class
> semantic domain of its own.

**Disposition: ACCEPT, and explicitly NOT promoted to a separate foundational family.** The
batch instruction asked whether threshold semantics deserve their own Rule family. This session's
finding: no — thresholds recur inside Cost (COST's own "reaches zero" cases), Resource
(depletion), and Transformation (accumulated conditions crossing a trigger point), but in every
one of those cases the *real* cause is whatever produced the accumulation, and the threshold
check is only the point at which a rule notices that accumulation is sufficient — never a novel
kind of cause in its own right. One rule, stated once, cross-linked from every family that needs
it, is more honest than four separately-drafted restatements.

**Repository evidence: SUPPORTED, and cleanly illustrated by the same evidence Batch 02 already
used for a related purpose.** `EvolutionSystem.evaluate()`'s `for threshold in [10, 25, 50]`
checks whether accumulated level/XP has crossed a value — the threshold check is the *trigger*,
not the *cause*; the real cause is the accumulated experience the check is testing for. Crossing
10 XP one tick earlier or later would not itself explain the transformation; the accumulated
history would.

**Scenarios:** [CTR-S10](../scenarios/foundational-batch-03.md#ctr-s10) (the required counter:
threshold crossed, required trigger/context absent, transformation does not occur).

---

## LIMIT-05 — Diminishing returns and saturation are legitimate, but must be explicitly modeled

> A capacity or accumulation may legitimately produce reduced marginal effect as it approaches a
> bound (diminishing returns, saturation), but this must be an explicit, declared part of the
> mechanism — never assumed to apply universally just because a limit exists.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED, for at least one real instance.** `DENSITY_FLOOR` (`src/world/
ecology.py`) confirms a real saturation model: population density reduces a resource node's
regeneration multiplier down to an explicit floor (25%), not linearly to zero and not silently —
the floor and the falloff curve are both declared constants, not implicit behavior.

**Scenarios:** [CTR-S15](../scenarios/foundational-batch-03.md#ctr-s15) (the required
unlimited-growth counter: accumulation continues, a capacity/counterforce prevents infinite
unconstrained scaling).

---

## Cross-domain links recorded here

- LIMIT-01, LIMIT-02, LIMIT-03 → Agency/motivation/decision, Perception/knowledge/information
  (the `CognitionProfile`/`CapacityEnforcementPhase` evidence belongs to those future domains'
  own eventual content; this family only states the foundational shape)
- LIMIT-04 → Cost (COST's own threshold cases), Resource (depletion-to-zero), Transformation
  (accumulated-conditions triggers), Causality (CAUSE-01, the principle this rule restates)
- LIMIT-05 → Ecology/population (the concrete saturation content)

## Open questions carried forward

1. Whether every future domain that introduces a finite bound (combat readiness caps, faction
   influence caps, settlement population caps) must go through an explicit
   `*EnforcementPhase`-shaped mechanism, or whether lighter-weight bound-checking is acceptable,
   is an implementation question deferred to those domains — not decided here.
