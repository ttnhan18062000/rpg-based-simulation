---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Time

**Purpose/scope.** What it means for the world to have a real, stable temporal order: before/
after, duration, delay, expiration, recurrence, elapsed time, and simultaneity — as distinct from
*execution* time (tick scheduling, same-cadence ordering between systems), which stays out of
scope. This family operationalises `simulation-rule-world-law-design-preparation.md` §3.2's
already-anticipated `Time` foundational law family.

**Status.** Foundational Batch 02, first draft. Candidates below originated as external-reviewer
hypotheses (`tmp/world-rule-batch-2-ext-ai.md`); each carries this session's disposition and
repository evidence, not the original wording uncritically kept.

**Explicit non-goal, per the batch instruction.** Do not design engine tick ordering or scheduler
execution order — `roadmap.md`'s Batch 02 clarification already disposed of this as an
implementation/execution-order concern, consistent with Batch 01's own rejected same-tick
ordering candidate (`foundations/state-ownership.md`).

---

## TIME-01 — Temporal ordering is real and stable

> The world has a stable temporal ordering/reference sufficient to establish before, after,
> simultaneity where meaningful, and elapsed duration between events. This ordering does not
> change once established.

**Disposition: ACCEPT, refined 2026-09-21 — implementation detail removed from the world rule
itself.** The original wording tied this directly to "one real, monotonically-advancing tick
counter." A monotonic tick counter is how *this* repository happens to realize temporal ordering
— it is repository evidence for the rule, not part of the rule. The world-semantic requirement is
only that before/after, simultaneity, and elapsed duration be well-defined and stable; a
different implementation (e.g., a continuous clock, or per-region local clocks with a declared
synchronization rule) would satisfy the same rule without a global tick counter at all.

**Repository evidence: SUPPORTED, as an implementation of this rule, not as the rule itself.**
`AuthoritativeState.tick` advances monotonically and is the concrete mechanism realizing stable
temporal ordering here; entity and registry records stamp real tick numbers at the moment of the
event (`birth_tick`, `death_tick`, `founded_tick`, `dissolved_tick`, `formation_tick`,
`transformed_tick`) rather than recomputing "when did this happen" after the fact.

**Scenarios:** [TAR-S04](../scenarios/foundational-batch-02.md#tar-s04).

---

## TIME-02 — A cause may have a consequence that occurs later, and it must stay traceable

> A causal chain is not required to resolve within the tick that produced it. A delayed
> consequence remains subject to Causality's own rules (CAUSE-01/CAUSE-03) — it must still trace
> to a real producer, not merely to elapsed time.

**Disposition: ACCEPT.** This is the Time-family statement of something CAUSE-01/CAUSE-05 already
implied but never said explicitly: *delay itself* is not what makes a cause real or fabricated —
the same real-causal-path standard applies regardless of how much time elapses before the
consequence lands.

**Repository evidence: SUPPORTED.** `LifecycleSystem._seed_dying_wish()` and
`_transfer_inherited_feud()` both write a real record at the moment of death that only resolves
into an actual effect (an heir acting on the inherited hostility) at a later, unspecified tick —
the delay is real and the eventual effect still traces back to the original death event via a
stable id (`inherited_nemesis_{antagonist}`), not a fabricated or recomputed link.

**Scenarios:** [TAR-S01](../scenarios/foundational-batch-02.md#tar-s01).

---

## TIME-03 — Expiration must be a declared boundary, not a silent one

> An effect, cooldown, or state that ends after some duration must have its expiration condition
> declared as part of the mechanism itself, not inferred after the fact.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `expires_tick`, `cooldown_remaining`, and `respawn_cooldown`
are real, explicitly declared fields checked directly against the current tick — expiration is a
structural property of the state, not something a consumer has to guess at from absence of other
signals.

**Scenarios:** [TAR-S02](../scenarios/foundational-batch-02.md#tar-s02).

---

## TIME-04 — Recurrence is a continuing rule, but each occurrence remains its own traceable event

> A process that repeats on a cooldown or cycle (regeneration, reproduction eligibility, skill
> readiness, a persistent poison) is one continuing recurring rule — it does not need a fresh
> causal justification invented each cycle. But each individual occurrence remains its own
> distinct, independently traceable event or transition:
>
> ```text
> persistent recurring process
>         → occurrence 1
>         → occurrence 2
>         → occurrence 3
> ```
>
> The occurrences share a recurring source/rule but remain independently traceable where causally
> relevant — e.g., a specific occurrence may itself be the thing a further consequence points
> back to.

**Disposition: ACCEPT, refined 2026-09-21 — the "one continuing rule" framing kept, but
corrected so it no longer implies individual occurrences aren't real, separately-traceable
events.** The original wording leaned entirely on "not a fresh, independently-caused event
requiring its own CAUSE-01 justification from scratch," which is true for *why the process keeps
happening* but was too strong if read as also meaning no single occurrence can stand as its own
cause of something. Both halves hold: the recurrence itself doesn't need re-justifying every
cycle, and any one cycle's occurrence can still be the specific, individually-traceable producer
of a further consequence.

**Repository evidence: SUPPORTED for both halves.** `reproduction_cooldowns: Dict[partner_id,
cooldown_expiry_tick]`, per-skill `cooldowns: Dict[skill_id, tick_when_ready]`, and
`regen_rate_per_tick` on resource nodes are evaluated as one standing rule against elapsed ticks
(the recurring-source half). Each occurrence is also architecturally a real, separately-applied
state delta through the same typed Update→Patch pipeline every other tick's changes go through —
tick N's regeneration and tick N+1's regeneration are distinguishable, individually-committed
events, not one undifferentiated ongoing blob, even though nothing in the current repository
happens to need to trace back to "which specific cycle's occurrence mattered" yet (PARTIAL on
that specific consuming use case, not on the architectural capability).

**Scenarios:** [TAR-S03](../scenarios/foundational-batch-02.md#tar-s03),
[TAR-S15](../scenarios/foundational-batch-02.md#tar-s15) (added 2026-09-21 — a persistent
recurring process whose individual occurrences are separately identifiable).

---

## TIME-05 — Elapsed time is a real semantic quantity, measured from a reference point

> How much time has passed for a subject is meaningful relative to an origin or reference point
> in its own history (e.g., since it began, since a prior event). This is a semantic quantity the
> world can reference — not merely an artifact of how any particular implementation happens to
> compute it.

**Disposition: ACCEPT, refined 2026-09-21 — implementation detail and an over-generalized
biological claim both removed.** The original wording said elapsed time "is computed from tick
difference, not stored" — that is how this repository happens to implement it (a fact about
`LifeStageService`, not a world rule) and belongs in repository evidence, not the rule text. The
original also asserted "aging progression does not run backward" as a universal Time law; aging
is a biological/Life-Body concept, not a foundational Time one, and stating it here would
pre-empt that future domain's own investigation. TIME-05 now claims only that elapsed-time-from-
a-reference-point is real and meaningful — nothing about which subjects experience it
monotonically.

**Repository evidence: SUPPORTED for the semantic quantity itself.** `LifeStageService.
get_stage_for_age(age_ticks)` treats elapsed time as a real, referenceable quantity (derived from
a tick difference in this implementation, but the semantic point is that "time since birth" is a
meaningful thing to ask about a subject, independent of how it's computed). The forward-only
aging finding this session made directly (`LifeStageService.is_forward_transition()` rejects a
backward life-stage transition) is real and repository-confirmed, but is recorded here explicitly
as a **later-domain refinement candidate for Life/Body/Survival**, not as this rule's own claim —
that future batch should decide whether forward-only aging is a Life/Body law, and for which
kinds of subjects, rather than inheriting it as an already-settled Time rule.

**Scenarios:** none yet directly probe elapsed-time-as-reference; the forward-only-aging question
is explicitly deferred to the future Life/Body/Survival batch, not scenario-traced here.

---

## TIME-06 — Simultaneity is not causal connectivity

> Two events occurring at the same tick does not, by itself, make one the cause of the other.
> This is CAUSE-03's own standard, restated for the specific case of temporal coincidence rather
> than mere correlation in general.

**Disposition: ACCEPT strongly.** Deliberately not a new idea — CAUSE-03 already covers this in
general; this rule exists so a future domain author checking Time specifically doesn't have to
re-derive that same-tick coincidence is a special case of "correlation," not an exception to it.

**Repository evidence: SUPPORTED**, in the same sense CAUSE-03 was SUPPORTED — nothing in the
repository generates a causal claim from mere tick-coincidence; the four-part test (declared link
/ producer consequence / consumer reaction / causal-or-provenance relation) applies unchanged.

**Scenarios:** [TAR-S05](../scenarios/foundational-batch-02.md#tar-s05) (the required
counter-scenario: two same-tick events with no real link between them).

---

## TIME-07 — Authoritative past world facts are not retroactively rewritten by ordinary forward simulation

> Authoritative past world facts are not retroactively rewritten by ordinary forward simulation.
> This is explicitly narrower than "the past never changes in any sense":
>
> ```text
> belief          — may change
> knowledge       — may change
> interpretation  — may change
> chronicle representation — may change
> historical significance  — may fade (per CAUSE-06)
> authoritative world fact of what happened — does not change by ordinary forward simulation
> ```
>
> This rule does not prohibit a future domain from defining an explicit, declared mechanism for
> genuine temporal alteration (e.g., a Magic/supernatural rule permitting true retroactive
> change) — it only states that *ordinary* forward simulation never does this implicitly.

**Disposition: ACCEPT, refined 2026-09-21 — scoped to the authoritative fact specifically, and
explicitly left open to a future declared exception.** The original wording ("once a tick has
occurred... facts about that tick do not change") was correct about the authoritative fact but
did not distinguish it clearly enough from belief/knowledge/interpretation/chronicle/significance,
several of which this same batch and Batch 01 already established *do* legitimately change over
time (contradicted beliefs, fading significance). Left unscoped, a future domain author could
misread this rule as forbidding those already-accepted kinds of change. The revision also removes
an implicit universal prohibition on temporal alteration altogether — this rule governs *ordinary*
forward simulation only, and stays silent on whether some future, explicitly declared mechanism
(most plausibly Magic/supernatural) could ever cause genuine retroactive change; that possibility
is neither asserted nor foreclosed here.

**Repository evidence: SUPPORTED architecturally, for the authoritative-fact claim.** The same
typed Update→Patch pipeline that makes OWN-01 true by construction also makes this true by
construction: a committed `AuthoritativeState` at tick T is not itself later edited; tick T+1 is a
new state built from it, never a retroactive rewrite of it. For the "belief/interpretation may
change" half: `BeliefCycleSystem.apply_contradiction()` reduces a hypothesis's confidence when
contradicted — confirms belief legitimately changes without the underlying fact being rewritten.

**Scenarios:** [TAR-S13](../scenarios/foundational-batch-02.md#tar-s13) (a past event's fact does
not change even though the historical actor involved can no longer act),
[TAR-S16](../scenarios/foundational-batch-02.md#tar-s16) (added 2026-09-21 — later evidence
changes belief/interpretation while the original world fact stays unchanged).

---

## Cross-domain links recorded here

- TIME-02 → Causality (CAUSE-01, CAUSE-05), History/Provenance (delayed consequences and their
  eventual retention)
- TIME-04 → Capability/progression, Life/body/survival (cooldowns, regeneration, reproduction —
  all future domains' own concrete instances of a foundational recurrence pattern)
- TIME-05 → Life/body/survival (the future batch that owns aging content, including whether
  forward-only progression is a Life/Body law at all — not inherited pre-decided from Time)
- TIME-07 → History/Provenance (fixed authoritative fact vs. legitimately fading significance,
  and vs. changeable belief/knowledge/interpretation/chronicle representation), Causality
  (CAUSE-06), Perception/knowledge/information (belief/interpretation change)
- TIME-07 → Magic/supernatural (the explicitly-left-open possibility of a declared, non-ordinary
  temporal-alteration mechanism — not designed or foreclosed here)

## Open questions carried forward

1. **Reframed 2026-09-21.** Whether forward-only aging is a Life/Body/Survival law at all, and
   for which kinds of subjects, is no longer treated as an already-settled Time-family constraint
   with an open exception question — it is the Life/Body/Survival batch's own question to answer
   from scratch, informed by (not inherited from) this repository's current
   `LifeStageService.is_forward_transition()` behavior.
2. Whether TIME-04's "continuing rule, not a new causal chain" framing needs its own explicit
   Evaluation-side implication (e.g., should a recurring effect's *n*th cycle be scored
   differently from its 1st) is an evaluation-semantics question, not a world-rule one — out of
   scope for this family per the established evaluation/governance boundary.
3. **Added 2026-09-21.** Whether any future domain will ever define an explicit, declared
   temporal-alteration mechanism (TIME-07's left-open possibility) is not decided — flagged for
   Magic/supernatural if and when that domain's own investigation raises it, not assumed in
   advance either way.
