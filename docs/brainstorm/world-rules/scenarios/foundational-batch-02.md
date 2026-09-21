---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Foundational Batch 02

**Purpose/scope.** Thirteen scenarios used to pressure-test the Time, Authority, and Reach rule
families in `foundations/time.md`, `foundations/authority.md`, and `foundations/reach.md`, per
`tmp/world-rule-batch-2-ext-ai.md`. Covers all eleven required probes (delayed consequence,
temporary effect expires, recurring process, two events with meaningful temporal ordering,
capability without authority, authority without capability, valid proposal from the wrong actor
rejected, nearby but unreachable target, distant target reachable through information/
institution, event outside declared causal reach, past event persists without present reach)
plus one required positive counterpart (an authorized proposal flowing into committed state) and
one required counter-scenario (two simultaneous but unrelated events).

Scoring uses the same vocabulary as Batch 01: **covered** / **partially covered** / **blocked** /
**revealed missing rule** / **revealed contradiction**, against current repository behavior, not
the ideal design.

---

## TAR-S01 — The dying wish, resolved much later

A dying entity's `dying_wish` seeds an inherited hostility. Many ticks later, the heir encounters
the original antagonist and the inherited feud actually resolves into an action.

- **Rules invoked:** TIME-02 (delayed consequence must stay traceable), CAUSE-01, CAUSE-05.
- **Result: covered.** `_seed_dying_wish()`/`_transfer_inherited_feud()` write the causal link at
  the moment of death; the eventual action, however much later it fires, traces back to that
  exact record via a stable id, not a fabricated or re-derived connection.

## TAR-S02 — A cooldown quietly ends

A skill's cooldown expires; the entity becomes eligible to use it again with no explicit "cooldown
ended" event fired anywhere.

- **Rules invoked:** TIME-03 (expiration must be a declared boundary).
- **Result: covered.** `cooldowns: Dict[skill_id, tick_when_ready]` is compared directly against
  the current tick wherever eligibility is checked — the boundary is declared structurally, even
  though no discrete "expiration event" object exists. Absence of an event is not the same as
  absence of a declared boundary.

## TAR-S03 — The node regrows

A harvested resource node regenerates charges over time via its own recurring rule, cycle after
cycle.

- **Rules invoked:** TIME-04 (recurrence is a continuing rule, not a new causal chain each cycle).
- **Result: covered.** `regen_rate_per_tick` is evaluated as one standing rule against elapsed
  ticks; nothing re-derives a fresh causal justification per regeneration cycle.

## TAR-S04 — Founded before, dissolved after

A clan's `founded_tick` must precede any `dissolved_tick` recorded for it; a query that produced
the reverse would be incoherent.

- **Rules invoked:** TIME-01 (temporal ordering is real and stable).
- **Result: covered.** Both fields are stamped at the real moment of their respective events, on
  a monotonically-advancing shared tick counter — the ordering is structural, not a convention a
  reader has to trust.

## TAR-S05 — Two unrelated things happen on the same tick (COUNTER: simultaneous but unrelated)

An entity ages into `LifeStage.ADULT` on the same tick a calamity strikes an unrelated, distant
region.

- **Rules invoked:** TIME-06 (simultaneity is not causal connectivity), CAUSE-03.
- **Result: covered.** Applying CAUSE-03's four-part test to this pair fails at the first part —
  there is no declared link between an entity's aging and a distant calamity — confirming that
  tick-coincidence alone generates no causal claim, exactly as the counter is designed to check.

## TAR-S06 — Friendly fire, refused

An entity is fully capable (stats, range, readiness) of attacking an ally, and attempts to. The
action is refused.

- **Rules invoked:** AUTH-01 (authority ≠ capability), AUTH-04 (authority ≠ opportunity/reach),
  AUTH-05 (an unauthorized proposal is rejected regardless of content validity).
- **Result: covered.** `LegalityServiceV2` returns `FRIENDLY_FIRE_ILLEGAL` — reach and capability
  are both satisfied; only the actor/target relationship makes the otherwise-identical proposal
  illegitimate.

## TAR-S07 — A leader who cannot currently act

A clan leader holds full authority over join-request decisions while wounded and on a skill
cooldown — their combat capability is reduced, but their leadership authority is untouched.

- **Rules invoked:** AUTH-01 (authority ≠ capability, from the other direction).
- **Result: partially covered.** The authority side is SUPPORTED (`core_actions.py`'s
  join-handling reads `clan.leader_entity_id` and uses the leader's appraisal regardless of the
  leader's own combat/stamina state). Whether this is *intentionally* capability-independent, or
  an unexamined gap (should an incapacitated leader's authority be suspended?), was not
  conclusively verified this batch — flagged as an open question in `authority.md`, not resolved
  here.

## TAR-S08 — Wrong actor, same proposal, rejected

Two otherwise-identical "attack target X" proposals are submitted: one from a hostile actor
(accepted), one from X's own ally (rejected) — the content of the proposal never changes.

- **Rules invoked:** AUTH-03 (authority ≠ knowledge), AUTH-05 (unauthorized proposal rejected
  regardless of content).
- **Result: covered.** `FRIENDLY_FIRE_ILLEGAL`/`SELF_ATTACK_ILLEGAL` are checked purely on the
  actor/target relationship; the same attack content is legal or illegal solely depending on who
  is proposing it against whom.

## TAR-S09 — Authorized proposal becomes real (positive counterpart to TAR-S08)

An authorized clan leader accepts a join request. The acceptance becomes actual, durable clan
membership — not merely a decision-logic outcome.

- **Rules invoked:** AUTH-05, OWN-04 (proposed change ≠ committed state).
- **Result: covered.** The leader's appraisal produces an accepted `ContractState`; the actual
  membership write happens afterward, through the separate `ClanLifecyclePhase` in the
  authoritative apply pipeline — the authorized decision and the committed state are two
  distinct steps, exactly as OWN-04 requires, with authority as the gate between them.

## TAR-S10 — Adjacent, but blocked

Two entities occupy adjacent tiles, but a line-of-sight obstruction sits between them.

- **Rules invoked:** REACH-01 (reach is a precondition for a direct causal claim).
- **Result: covered.** `LOS_OBSTRUCTED` is a real, structural rejection — spatial adjacency alone
  does not establish reach; the obstruction check is a separate, necessary condition.

## TAR-S11 — A rumor reaches a distant leader

A witness far from a clan's leader reports what they saw. The rumor travels through the belief
system and reaches the leader, who was never spatially close to the original event.

- **Rules invoked:** REACH-02 (reach is not reducible to physical distance), REACH-05 (mediated
  reach differs in kind from direct reach).
- **Result: covered.** `process_rumor()` establishes real information-mediated reach across
  arbitrary distance; its `certainty=LeadCertainty.VAGUE`/`0.3` (vs. `process_observation()`'s
  `PRECISE`/`1.0`) confirms this reach is evidentially distinct in kind, not merely a weaker
  version of direct perception.

## TAR-S12 — An event outside the declared reach

A causal chain occurs outside Campaign mode, where chronicle retention is not declared to reach.
A later query relying on that retention should not be able to treat the event as if it had been
recorded.

- **Rules invoked:** REACH-06 (reach must be declared per mechanism, not assumed universal),
  CAUSE-05.
- **Result: covered — reconfirms CAUSE-05's own finding, restated at the Reach-family level.**
  The Campaign-mode-only boundary is an honestly declared reach limit, not a silent gap; nothing
  in the chronicle system claims retention it doesn't have.

## TAR-S13 — A dead rival, still explaining present hostility

A deceased antagonist's identity persists inside an inherited feud record. The deceased performs
no action at any point after death; only the living heir carries the hostility forward.

- **Rules invoked:** REACH-04 (historical relevance ≠ present reach), ID-05, OWN-06, TIME-07
  (the past is fixed).
- **Result: covered — the explicit cross-batch check the instruction required.**
  `_transfer_inherited_feud()` keeps the dead antagonist's identity fully legitimate as a
  historical/causal reference while granting it zero present agency; every subsequent effect is
  produced by the living heir, who alone has real present reach.

---

## Cross-batch note

TAR-S06/S08 and TAR-S09 form a matched pair by design: the same combat-legality mechanism
(`LegalityServiceV2`) is simultaneously the cleanest evidence that authority is actor/target-
relative (S06/S08) and, via the separate join-acceptance path, that an authorized proposal still
has to flow through the authoritative apply pipeline to become real (S09) — one repository
mechanism family answering two different foundational questions is itself a small piece of
evidence that Authority and State Ownership are correctly kept as separate families rather than
merged.

TAR-S11 and TAR-S12 both instantiate REACH-06/CAUSE-05's "declared reach" discipline from two
different angles (information-mediated reach across space; chronicle retention across a mode
boundary) — recorded once here rather than as two unrelated findings, since a future domain
author designing a new reach-constrained mechanism should expect to declare its boundary the same
way regardless of which channel (space, information, mode) constrains it.
