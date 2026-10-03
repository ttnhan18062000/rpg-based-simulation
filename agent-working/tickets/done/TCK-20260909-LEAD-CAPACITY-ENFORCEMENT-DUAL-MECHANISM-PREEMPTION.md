---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION
phase: done
date: 2026-09-09
tags: [architecture, strategy]
---

# TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION

## Title
Two live mechanisms enforce `max_leads` with different pending-update awareness — the cruder one runs first and preempts the more correct one

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while writing `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`'s own real-pipeline test
for `CapacityEnforcementPhase`'s lead-pruning behavior. This is **not** the "tested but
unreachable" pattern the rest of this session's batch has repeatedly found (see
`TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`) — both mechanisms here are live, reachable, and
run every relevant tick. The defect is different: they are not equivalent implementations of the
same rule, and the one with worse information runs first.

- `DetourSuggestionSystem.enforce_bandwidth()` (`src/systems/strategic_systems/detour.py:146-172`)
  is called from inside `StrategicIntelligenceSystem.fused_strategic_pass()` (much earlier in
  `src/engine/pipeline.py`'s own phase sequence — the `strategic_intelligence` phase). It sorts
  `entity.strategic.leads.values()` (the **current, pre-tick state only**) by `_certainty_score`
  and drops the excess past `profile.max_leads`. It has **no awareness of leads arriving this
  same tick** — not this tick's own new leads, not this tick's own decay/contradiction demotions.
- `CapacityEnforcementPhase.enforce()` (`src/engine/pipeline_phases/capacity_enforcement.py:44-57`)
  is the dedicated phase, running much later (after `lead_contradiction`, `lifecycle`, `groups`,
  etc.). Its own trigger is `len(entity.strategic.leads) + len(strat_upd.leads_add_or_update) >
  profile.max_leads` — it correctly accounts for this tick's own pending lead updates before
  deciding whether/what to prune.

**The consequence, confirmed via direct tracing (not assumed)**: because `enforce_bandwidth()` runs
first and only sees the pre-tick state, it can — and in a real reproduction did — prune an entity's
leads down to `max_leads` *before* `capacity_enforcement.py`'s own dedicated phase ever runs. By
the time the dedicated, pending-update-aware phase evaluates the entity, it is often already at or
under capacity from the cruder mechanism's own earlier action, so its own more correct logic never
gets to fire. The more correct implementation may rarely or never be the one that actually decides
what gets dropped — the same "real, tested code whose behavior is preempted rather than absent"
shape as this session's other findings, just at the level of which live mechanism's decision wins,
not whether either runs at all.

**Direct evidence this is real, not theoretical**: `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-
METHOD-CLEANUP`'s own capacity-interaction test
(`tests/unit/strategic/test_belief_staleness_decay_pipeline.py::
test_capacity_enforcement_prunes_newly_decayed_lead_over_fresh_ones`) could not be run against the
real, full `AuthoritativeApplyPipeline.refine()` — a 9-pre-existing-lead entity got pruned by
`enforce_bandwidth()` during `strategic_intelligence`, before `capacity_enforcement.py`'s own
dedicated phase ever saw it, contaminating the specific interaction that test needed to isolate.
The test had to call `CapacityEnforcementPhase.enforce()` directly, bypassing the earlier phase
entirely, to test the mechanism this AC actually cared about. Needing to route around a live phase
to exercise another live phase's own real logic is itself evidence of the preemption.

## Scope
- Confirm the preemption's real frequency/impact: under what real conditions does an entity
  actually reach `>max_leads` before `strategic_intelligence`'s own `enforce_bandwidth()` call,
  and how often does `capacity_enforcement.py`'s own dedicated logic get a chance to run at all
  for leads specifically once `enforce_bandwidth()` has already acted.
- Determine the real design intent: was `enforce_bandwidth()` meant to be superseded by
  `capacity_enforcement.py`'s later, more careful mechanism (i.e. a migration that never removed
  the old call site), or are the two intentionally layered for a reason not yet identified (e.g.
  `enforce_bandwidth()` as a cheap early guard, `capacity_enforcement.py` as the authoritative
  final pass)?
- **This is a real design decision — do not resolve which one should win, or unify them,
  without a decision.** Get a design decision (peer-routed, per this repo's standing convention)
  before implementing any fix.

## Out of Scope
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`'s own decay-staleness wiring — already
  closed; this ticket is a sibling finding from that ticket's own test-writing process, not a
  reopening of it.
- `enforce_bandwidth()`'s/`capacity_enforcement.py`'s own handling of concerns, hypotheses,
  projects, or candidate zones — this ticket is scoped to the `leads`/`max_leads` divergence found;
  if Investigate finds the same asymmetry for other capacity-bounded collections, record it here
  rather than silently expanding scope.
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`'s own scope (unreferenced code) — both
  mechanisms here are live and reachable; this finding does not belong in that audit.

## Acceptance Criteria
- [x] Real evidence (not assumption) establishes how often, and under what conditions,
      `enforce_bandwidth()`'s own pruning actually preempts `capacity_enforcement.py`'s dedicated
      lead logic in practice. **Answer: never, under real conditions** — `entity.strategic.leads`
      is empty for every entity at every tick in a real 500-tick `frontier_living_world` run,
      confirmed three independent ways. The shared trigger condition never evaluates true.
- [x] Real evidence establishes the design intent (superseded-but-never-removed vs. intentionally
      layered) — git history, related tickets, or design docs, not guessed. **Neither framing
      fits**: both presuppose the preemption is actually happening in real play, which it isn't.
      The question the ticket asked is moot given real data, not answerable within its own frame.
- [x] A design decision on the fix approach (unify into one mechanism, remove the redundant one,
      or document the layering as intentional) is obtained via peer review before any
      implementation. **Decision: document the narrower true claim, implement nothing** — approved
      by peer review after independent verification of the instrumentation.
- [x] If a fix is implemented: real test evidence that the correct, pending-update-aware logic is
      the one that actually decides what gets pruned, not merely that "some" pruning still occurs.
      **N/A — no fix implemented**, per the peer-approved disposition above.

## Related Tickets
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP` (origin of this finding)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (a related but distinct class of finding —
  unreferenced code, not preempted-but-reachable code; explicitly out of that audit's own scope)
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (sibling "inert end to
  end under real defaults" finding on the fact-writing half of the same knowledge/investigation
  layer)
- `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (new, filed from this
  ticket's own investigation — the correctly-sized combined finding: facts and leads are both
  never created under real defaults, spun out separately per peer review rather than expanded into
  here)

## Related Docs
- `docs/simulation/belief_and_detour_contract.md` (amended in this ticket's own PR to note that
  leads are also never created under real defaults, correcting its prior framing)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION/`
  (`investigation.md`, `plan.md`, `test_plan.md`)

## Related Code Areas
- `src/systems/strategic_systems/detour.py` (`DetourSuggestionSystem.enforce_bandwidth()`)
- `src/engine/pipeline_phases/capacity_enforcement.py` (`CapacityEnforcementPhase.enforce()`)
- `src/systems/strategic_systems/intelligence.py` (`fused_strategic_pass()`, the call site that
  invokes `enforce_bandwidth()` early)
- `src/engine/pipeline.py` (the phase ordering itself)

## Assumptions / Open Questions
- Which mechanism should be authoritative (or whether both should be, in a coordinated way) is the
  central, deliberately-unresolved design question this ticket exists to raise, not answer here.
  **Resolved as moot**: with the shared collection confirmed always empty under real conditions,
  there is no live conflict for either mechanism to be authoritative over today. Left explicitly
  unreconciled (not fixed) so the question is recoverable if leads ever start being created for
  real — see Implementation Notes.

## Implementation Notes
Instrumented both `DetourSuggestionSystem.enforce_bandwidth()` and
`CapacityEnforcementPhase.enforce()` directly against a real 500-tick `frontier_living_world`
episode (seed 7, `hero_guild_perspective` — same scenario/seed used throughout this audit arc),
per peer review's explicit instruction to "instrument a real run and count how often the dedicated
phase actually changes anything after the earlier pass has run."

Confirmed both mechanisms are live and frequently invoked (`enforce_bandwidth()`: 10,570 real
calls; `CapacityEnforcementPhase.enforce()`: 500 calls, once per tick, 11,703 entity-update
evaluations) — ruling out "unreachable code" before drawing any conclusion about the shared data.
Then confirmed, three independent ways, that `entity.strategic.leads` was empty for every entity at
every tick for the entire run: a running `len()` tally at every `enforce_bandwidth()` call; a
snapshot of pending `leads_add_or_update` on entry to the dedicated phase; and a direct read of live
`state.entities` at the last-observed tick (0/49 entities had any lead). Max headroom observed
(`leads_len - profile.max_leads`) was -8 — never close to the cap.

This means the ticket's own framed question ("which mechanism wins, and how often") is moot as
asked: neither mechanism ever removes a lead under real conditions, because their shared trigger
condition never evaluates true. None of the three originally-proposed dispositions (supersedes,
genuinely complementary, sequencing bug) fits, since all three presuppose the preemption is
actually occurring — the honest finding is a fourth one the ticket didn't originally frame: there
is currently no live conflict to resolve.

Traced one level further (read-only, no fix attempted) to confirm this wasn't an instrumentation
artifact: all four real `LeadState(...)` construction sites in `src/` are unreachable under real
defaults, each for a distinct reason — see investigation.md for the full trace. This additional
finding was reported to peer review before any further action, per standing "no building without
declared intent" / "bring scope decisions to peer" discipline, and was spun out as its own,
separately-scoped, correctly-sized standard-tier ticket
(`TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`) rather than folded into this
ticket's own implementation, per peer review's explicit instruction.

Amended `docs/simulation/belief_and_detour_contract.md` in this same PR (per peer review's
explicit instruction, to avoid a separate one-paragraph PR) to correct its prior framing —
`KnowledgeFact` as provenance and leads as the model that drives detour/routing decisions was
already documented as one working half being inert (the fact-writing half); this amendment states
plainly that the other half (lead creation) is inert too, so the division of labour it describes is
design intent, not live behaviour.

No changes made to `enforce_bandwidth()`, `CapacityEnforcementPhase.enforce()`, or their call
sites — nothing to fix given real conditions, and peer review explicitly agreed reconciling two
mechanisms that never fire would be a fix with no observable effect.

## Test Summary
Documentation-only disposition — no `src/`/`tests/` code changed. Verification is the real
500-tick instrumented reproduction itself (see `stored_artifacts/.../investigation.md` and
`test_plan.md` for full detail): three independent measurement angles agreeing the collection is
always empty; call-count evidence ruling out "dead code" as the explanation; a root-cause trace of
all four lead-creation paths confirming the finding generalizes beyond this one scenario/seed.
`tests/unit/strategic/test_belief_staleness_decay_pipeline.py::
test_capacity_enforcement_prunes_newly_decayed_lead_over_fresh_ones` (the ticket's own originating
test, which constructs the precondition synthetically) is left unchanged — it remains valid
evidence the interaction is real *given* a pre-existing over-capacity lead set.
`tests/integrity/test_no_duplicate_content_blocks.py` and `validate_frontmatter.py --content-type
ticket` passed on both this ticket and the newly-filed one.

## Files Changed
- `docs/simulation/belief_and_detour_contract.md` — amended to state leads are also never created
  under real defaults, correcting the provenance/decision-influence framing.
- `tickets/todos/TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS.md` — new,
  filed as the correctly-sized combined finding per peer review.
- `stored_artifacts/TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION/{investigation.md,plan.md,test_plan.md}`
  — full evidence trail.
- `tickets/done/TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION.md` — this file,
  closed.
- No `src/` or `tests/` files changed.

## Completion Summary
Closed on the narrower true claim: both `enforce_bandwidth()` and `CapacityEnforcementPhase.
enforce()` are real, live, frequently-invoked mechanisms, but their shared precondition
(`len(entity.strategic.leads) > profile.max_leads`) never holds in a real run — the collection is
always empty, confirmed via real instrumented reproduction, three independent ways. There is no
live preemption today for either mechanism to win or lose. The unreconciled ordering is left
explicitly documented (not fixed) rather than silently accepted, so it remains recoverable if leads
ever start being created for real. Peer review confirmed this disposition and explicitly credited
the instrumentation for dissolving the ticket's own question rather than answering it within its
original three-way frame — the third time this batch that measuring beat reasoning.

The investigation surfaced a materially larger finding while sanity-checking the headline result:
none of the four real lead-creation paths in `src/` are reachable under real defaults, each for a
distinct reason. Combined with the already-closed knowledge-fact ticket's own "facts are never
written" finding, this is one investigation, not two — the entire knowledge/investigation layer
produces nothing in a real run, a nameable missing behaviour (characters never investigate, chase a
rumor, or follow up on what they heard). Per peer review's explicit instruction, this was spun out
as its own, correctly-sized, standard-tier ticket
(`TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`) rather than resolved here,
and `docs/simulation/belief_and_detour_contract.md` was amended in this same PR to reflect the
corrected framing.
