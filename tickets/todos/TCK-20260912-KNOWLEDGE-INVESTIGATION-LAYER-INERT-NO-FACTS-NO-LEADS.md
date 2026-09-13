---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS
phase: open
date: 2026-09-12
tags: [cognition, self-model, information]
---

# TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS

## Title
The entire knowledge/investigation layer produces nothing in a real run — characters never acquire facts or leads, so they never investigate anything

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Two independent investigations this arc found the same shape on the two halves of what was
believed to be one working system:

- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (closed): real
  500-tick `frontier_living_world` instrumentation confirmed `InformationAssimilationService.
  assimilate()` — the only function that ever writes a `KnowledgeFact` — fires **zero times** in a
  real run. Facts are, in practice, never written.
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` (closed): real 500-tick
  instrumentation of the same scenario confirmed `entity.strategic.leads` is **empty for every
  entity at every tick** for the whole run. Leads are, in practice, never created.

Individually, each finding was disposed of as "document the real state, build nothing" — the
knowledge-fact ticket because no design doc declares a consumer for facts; the lead-capacity
ticket because there was no live preemption to resolve between the two enforcement mechanisms once
the shared collection is confirmed always empty.

Taken together they are a different, bigger finding, per peer review: this is not two separate
inert mechanisms, it is **one system** — the entire knowledge/investigation layer (facts +
leads) — producing nothing under real defaults. Characters never acquire facts, never acquire
leads, and therefore never investigate anything, never chase a rumor, never follow up on what they
heard. Unlike the knowledge-fact finding alone (a fact that never existed to be ignored — no
observable player-facing gap), the absence of leads means an entire category of behaviour never
occurs at all — this is a nameable missing behaviour, not merely an inert data structure.

## Scope
- Consolidate and re-verify, in one place, the full real-condition disposition of both halves:
  - Facts: two real write call sites, both structurally empty today (`pending_information_
    responses` never threaded into Campaign's `AuthoritativeState`;
    `ENABLE_INFORMATION_INTENT_EXECUTION` default off).
  - Leads: four real `LeadState(...)` construction sites, each unreachable for a **distinct**
    reason — do not collapse them into one explanation, since each needs its own answer:
    1. `GuildIntelSystem.update()` (`src/systems/social_systems/guilds.py`, rumor-on-guild-visit) —
       **dead code**, zero callers anywhere in `src/` outside its own definition and a passthrough
       re-export (`src/systems/guild_system.py`).
    2. `GuildAction.visit()` (`src/town/guild.py`, the guild-visit lead grant) — **flag-gated
       off**, wired via `src/engine/pipeline_phases/guild_visit.py` but gated
       `ENABLE_GUILD_QUEST_GENERATION`, default `OFF`
       (`src/domains/optimization/feature_flags.py:91`), not overridden by any shipped world
       checked so far.
    3. The belief-confirmation loop in `src/systems/strategic_systems/intelligence.py:405-434` —
       **update-only**, only iterates and confirms/denies already-existing leads; the "new"
       `LeadState` it builds is immediately overwritten with the original lead's own `id`, so it
       can never seed the collection from empty.
    4. `PaidInformationTransactionSystem.enforce()`
       (`src/engine/pipeline_phases/paid_information.py`) — **structurally unreachable type**,
       requires a registered `InformationProvider`, which has zero real construction sites
       anywhere in `src/`, in any world (not flag-gated — the type is simply never instantiated by
       any live code path).
- Determine whether any of the four lead-creation gaps, or the two fact-writing gaps, is worth
  actually fixing (vs. documenting as intentional/deferred), and if so which one(s) — this is a
  real scope/priority decision, not something to resolve unilaterally. Bring it to peer review
  before implementing anything.
- Amend or supersede `docs/simulation/belief_and_detour_contract.md`'s framing as needed once a
  disposition is reached — a first-pass amendment noting both halves are inert was already carried
  in `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION`'s own PR; this ticket may
  need to go further once a real disposition (fix vs. document) is decided.

## Out of Scope
- Actually implementing a fix for any of the six gaps (two fact-writing, four lead-creation)
  without an explicit peer-routed design decision on which, if any, is worth fixing.
- `CapabilityContext.region_data`/`.enemy_data` always-empty
  (`TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`) — already filed as its own
  independent, narrower finding; do not fold it into this ticket.
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION`'s own question (whether
  `enforce_bandwidth()` preempts `CapacityEnforcementPhase.enforce()`) — already closed on its own
  narrower claim (no live preemption given the always-empty collection); do not reopen it here.
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` — already open, already
  owns the pending-responses threading gap; this ticket cross-references it, does not duplicate it.

## Acceptance Criteria
- [ ] A single, consolidated, re-verified statement of the real disposition of both the fact-write
      path and all four lead-creation paths, each with its own distinct root cause named (not
      collapsed into one generic "gated" explanation).
- [ ] The "name the missing behaviour" test applied explicitly and honestly to this combined
      finding: does a player currently notice characters never investigating/following up on
      rumors, or is this still not observable in practice for some other reason (e.g. no other
      system currently reacts differently based on lead presence/absence either)? Answer with real
      evidence, not assumption.
- [ ] A peer-routed design decision on disposition: document-only (same as the two originating
      tickets), or a scoped fix for one or more of the six specific gaps — obtained before any
      implementation.
- [ ] If a fix is approved for any gap: real before/after evidence (same instrumentation pattern as
      the originating tickets) that facts/leads are actually created under real conditions
      afterward, not just that the code compiles/tests pass.

## Related Tickets
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (closed; facts-never-
  written half of this finding)
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` (closed; leads-never-created
  half of this finding, and the ticket whose own investigation surfaced this consolidated scope)
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (open; a related but distinct,
  narrower always-empty-decision-input finding — explicitly out of this ticket's scope)
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (open; owns one of the two
  fact-write gaps)
- `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` (owns the `ENABLE_INFORMATION_INTENT_EXECUTION`
  deferral)

## Related Docs
- `docs/simulation/belief_and_detour_contract.md` (amended once already for the leads-never-created
  finding; may need a further, disposition-driven update once this ticket concludes)
- `docs/simulation/domains/information_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION/`
- `stored_artifacts/TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION/`

## Related Code Areas
- `src/domains/information/assimilation.py` (`InformationAssimilationService.assimilate()`)
- `src/systems/social_systems/guilds.py` (`GuildIntelSystem.update()`, dead)
- `src/town/guild.py` (`GuildAction.visit()`, flag-gated)
- `src/systems/strategic_systems/intelligence.py` (belief-confirmation loop, update-only)
- `src/engine/pipeline_phases/paid_information.py` (`PaidInformationTransactionSystem.enforce()`,
  structurally unreachable provider type)
- `src/core/self_model.py` (`KnowledgeFact`), `src/core/strategic.py` (`LeadState`)

## Assumptions / Open Questions
- Whether any of these six gaps is worth fixing at all is genuinely open — the codebase's default
  finding pattern this whole arc has been "document, don't build" absent a declared design intent,
  but this combined finding is a real, nameable missing behaviour in a way most prior findings in
  this arc were not, which may tip the balance differently. Not pre-judged here.
- `ENABLE_GUILD_QUEST_GENERATION` and `ENABLE_INFORMATION_INTENT_EXECUTION` are both existing,
  named, already-deferred flags — flipping either is a decision for whoever owns that deferral, not
  a default outcome of this ticket.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
