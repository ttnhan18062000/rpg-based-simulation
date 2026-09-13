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
       requires a registered `InformationProviderState` (`state.information_providers`), which has
       zero real construction sites anywhere in `src/`, in any world (not flag-gated — the type is
       simply never instantiated by any live code path).
- **Added 2026-09-13, found while scoping `docs/plans/rpg_design_roadmap/
  rpg_knowledge_investigation_closure_plan.md`**: a fifth distinct instance of the same shape, a
  different type from gap #4 above — `src/world/providers/information.py` defines
  `GuideInformationProvider`, `BlacksmithInformationProvider`, and `GuildInformationProvider`, each
  producing `KnowledgeFact`s and `suggested_leads`. **None has any production caller** — the only
  non-test references are `src/worldbuilding/compiler.py` importing the *types* to shape authored
  seed data. Appended here rather than filed as its own ticket, per the governing plan's own
  reasoning: it's the same "one side of a designed interaction built, the connecting call never
  written" shape as the other four gaps, not a new category.
- Determine whether any of the four lead-creation gaps, the fifth provider-caller gap, or the two
  fact-writing gaps, is worth actually fixing (vs. documenting as intentional/deferred), and if so
  which one(s) — this is a real scope/priority decision, not something to resolve unilaterally.
  **Disposition decision, made 2026-09-13** (routed via peer review, recorded here rather than left
  open): **connect, but scoped to one path, not all six/seven.** Provider reliability is declared
  as a gameplay concept in three places (the `KnowledgeFact`/provider dataclass fields, the seed
  schema, and Epic 4.2's own scope in `docs/plans/long_term_development_roadmap.md`) — building
  toward that is closing a declared gap, not inventing gameplay, which is the same declared-intent
  test this whole arc has applied throughout. But six-plus gaps is not one ticket, and fixing every
  lead-creation site at once would be inventing scope beyond what's declared. The scoped
  instruction for whoever picks this up: **connect the single path with the most machinery already
  behind it, prove one real lead reaches one real entity in a real run, then re-decide on the
  remaining gaps with that evidence in hand** — do not attempt all six/seven gaps in one pass.
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
- [ ] A single, consolidated, re-verified statement of the real disposition of the fact-write path,
      all four lead-creation paths, and the fifth provider-caller gap, each with its own distinct
      root cause named (not collapsed into one generic "gated" explanation).
- [ ] The "name the missing behaviour" test applied explicitly and honestly to this combined
      finding: does a player currently notice characters never investigating/following up on
      rumors, or is this still not observable in practice for some other reason (e.g. no other
      system currently reacts differently based on lead presence/absence either)? Answer with real
      evidence, not assumption.
- [x] **Disposition decision made 2026-09-13** (recorded above in Scope): connect, scoped to the
      single provider path with the most machinery already behind it — not all six/seven gaps at
      once. Prove one real lead reaches one real entity in a real run before deciding on the rest.
- [ ] Real before/after evidence (same instrumentation pattern as the originating tickets) that a
      fact/lead is actually created and delivered under real conditions for the one path connected,
      not just that the code compiles/tests pass.
- [ ] Not started this batch (`gameplay-gaps-batch`) — sequencing confirmed via peer, do not pick
      up implementation until a future batch explicitly schedules it.

## Related Tickets
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (closed; facts-never-
  written half of this finding)
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` (closed; leads-never-created
  half of this finding, and the ticket whose own investigation surfaced this consolidated scope)
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (open; downstream of this
  ticket's disposition per `rpg_knowledge_investigation_closure_plan.md` — if this ticket's
  disposition never reaches (a)/connect, that ticket has no real facts to read)
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (open; owns one of the two
  fact-write gaps; sequenced last in the governing plan, after this ticket's disposition)
- `TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING` (open; a fifth-and-a-half,
  genuinely distinct defect found while scoping the governing plan — the intent handler's own
  unpaired gold deduction, not one of this ticket's six/seven gaps; needs no disposition here)
- `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` (owns the `ENABLE_INFORMATION_INTENT_EXECUTION`
  deferral)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_knowledge_investigation_closure_plan.md` (2026-09-13 —
  sequences this ticket against the other three in the same initiative and records the disposition
  decision above)
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
  structurally unreachable `InformationProviderState` type)
- `src/world/providers/information.py` (`GuideInformationProvider`, `BlacksmithInformationProvider`,
  `GuildInformationProvider` — the fifth gap, zero production callers, a different type from the
  one above)
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
