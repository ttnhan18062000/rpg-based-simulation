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

> The world has one real, monotonically-advancing tick counter. Events that occur at different
> ticks have a real before/after relationship; that relationship does not change once recorded.

**Disposition: ACCEPT.** This is the semantic root the rest of this family refines.

**Repository evidence: SUPPORTED.** `AuthoritativeState.tick` advances monotonically; entity and
registry records stamp real tick numbers at the moment of the event (`birth_tick`, `death_tick`,
`founded_tick`, `dissolved_tick`, `formation_tick`, `transformed_tick`) rather than recomputing
"when did this happen" after the fact.

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

## TIME-04 — Recurrence is a continuing rule application, not a new causal chain each cycle

> A process that repeats on a cooldown or cycle (regeneration, reproduction eligibility, skill
> readiness) is one continuing rule, re-evaluated over time — each cycle is not a fresh,
> independently-caused event requiring its own CAUSE-01 justification from scratch.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `reproduction_cooldowns: Dict[partner_id, cooldown_expiry_
tick]`, per-skill `cooldowns: Dict[skill_id, tick_when_ready]`, and `regen_rate_per_tick` on
resource nodes are all evaluated as one standing rule against elapsed ticks, not re-derived as new
events; this is what makes TIME-02's "must stay traceable" tractable for recurring effects instead
of requiring a fresh causal justification every cycle.

**Scenarios:** [TAR-S03](../scenarios/foundational-batch-02.md#tar-s03).

---

## TIME-05 — Elapsed time is derived, and aging moves in one direction for a given subject

> How much time has passed for a subject is computed from tick difference, not stored as an
> independent fact, and a subject's own life-stage/aging progression does not run backward.

**Disposition: ACCEPT.** This is the Time-family instance of OWN-03's derived-view principle
(elapsed time/age is derived, not owned state in its own right) combined with a genuinely new
directional constraint (forward-only) this batch's evidence surfaced.

**Repository evidence: SUPPORTED.** `LifeStageService.get_stage_for_age(age_ticks)` computes life
stage from elapsed ticks at read time — age itself is never a stored field. Confirmed directly:
`LifeStageService.is_forward_transition()` exists specifically to reject a life-stage transition
that would move a subject backward — aging is architecturally one-directional per subject, not
merely conventionally so.

**Scenarios:** none yet directly probe the forward-only constraint itself; flagged for the future
Life/Body/Survival batch, where aging content is actually designed.

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

## TIME-07 — The past is fixed; only the present is mutable

> Once a tick has occurred and its state committed, facts about that tick do not change. Later
> ticks may act on their consequences, reinterpret their meaning (per History/Provenance), or
> render them historically less prominent (per CAUSE-06's fading-significance clause) — but they
> cannot rewrite what was true at that tick.

**Disposition: ACCEPT.** This is the Time-family statement of the project's own durable-state
immutability law (`docs/core/state.md`) and of `Do not break determinism` (Hard Rule), stated as a
world-semantic consequence rather than only as an implementation constraint.

**Repository evidence: SUPPORTED architecturally** — the same typed Update→Patch pipeline that
makes OWN-01 true by construction also makes this true by construction: a committed
`AuthoritativeState` at tick T is not itself later edited; tick T+1 is a new state built from it,
never a retroactive rewrite of it.

**Scenarios:** [TAR-S13](../scenarios/foundational-batch-02.md#tar-s13) (a past event's fact does
not change even though the historical actor involved can no longer act).

---

## Cross-domain links recorded here

- TIME-02 → Causality (CAUSE-01, CAUSE-05), History/Provenance (delayed consequences and their
  eventual retention)
- TIME-04 → Capability/progression, Life/body/survival (cooldowns, regeneration, reproduction —
  all future domains' own concrete instances of a foundational recurrence pattern)
- TIME-05 → Life/body/survival (the future batch that actually designs aging content on top of
  this forward-only constraint)
- TIME-07 → History/Provenance (fixed past facts vs. legitimately fading significance),
  Causality (CAUSE-06)

## Open questions carried forward

1. TIME-05's forward-only aging constraint is stated at the foundational level; whether any
   future domain (Magic, most plausibly — reversing age is a classic magic trope) needs an
   *explicit* exception mechanism, analogous to ID-03's identity-ending exception, is not decided
   here. Flagged for the Magic/supernatural batch.
2. Whether TIME-04's "continuing rule, not a new causal chain" framing needs its own explicit
   Evaluation-side implication (e.g., should a recurring effect's *n*th cycle be scored
   differently from its 1st) is an evaluation-semantics question, not a world-rule one — out of
   scope for this family per the established evaluation/governance boundary.
