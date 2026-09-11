---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION
phase: open
date: 2026-09-11
tags: [cognition, self-model]
---

# TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION

## Title
`self_model.knowledge.facts` (`KnowledgeFact` store) has no decision-time reader anywhere in `src/` — a wired information-assimilation pipeline producing a store nothing consults

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Surfaced during `TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION`'s own
investigation into whether `effective_certainty()` was abandoned or unfinished: while confirming
there was no existing consumer to wire that function into, found something larger — every real
reference to `self_model.knowledge.facts` outside `src/core/self_model.py` itself is a write, a
passthrough, or a trace, never a decision read:

- `src/domains/information/assimilation.py:44,51,93` — write path (`KnowledgeModelService`
  populates `facts` from `InformationResponse` events)
- `src/cognition/knowledge_model.py:62` — write path (same assimilation flow)
- `src/cognition/self_model_phase.py:117-118` — reads `old_fact`/`new_fact` only to diff
  `recorded_tick` for a `KnowledgeFactLearnedEvent` trace emission, not for any decision
- `src/engine/pipeline_phases/lead_contradiction.py:204` — `facts=current_km.facts`
  reconstruction, a preservation passthrough when rebuilding the component, not consultation

Entities run a real information-assimilation pipeline (query issuance, response normalization,
fact recording — the same machinery `TCK-20260909-...` Batch C's `information_source_profiles`
work threaded routing through) that produces a `KnowledgeFact` store **nothing consults when
deciding anything**. Peer review confirmed this independently and flagged it as squarely in scope
under the wiring-first rule (2026-09-11): a feature that doesn't deliver, not tuning, not
dead-code-cleanup.

**This is a design-intent question, not a settled diagnosis.**
`docs/simulation/belief_and_detour_contract.md` casts `KnowledgeFact` as the deliberate sibling to
`BeliefEntry`/`LeadState`: "capacity-bounded, no decay," with leads carrying the
decision-influencing half of the cognition model. Two real possibilities:
- `KnowledgeFact`s are meant to inform decisions (threat estimation, query-response staleness,
  routing) → this is a wired-but-unconsumed pipeline, a real defect requiring a real consumer.
- They are deliberately write-only provenance — a record of what was learned and when, with
  `LeadState` owning all decision influence — in which case the current behavior is correct as
  built, and `belief_and_detour_contract.md` should say so explicitly instead of leaving it
  implicit.

## Scope
- Confirm the "no decision-time reader" finding is complete: a fresh, careful grep/trace for every
  real access to `self_model.knowledge.facts` (and any per-fact access via
  `self_model.knowledge.facts[...]`/`.get(...)`) across all of `src/`, classifying each as
  write/passthrough/trace/decision-read. Do not trust this ticket's own Request Summary listing as
  final — re-verify.
- Determine design intent: read `docs/simulation/belief_and_detour_contract.md`,
  `docs/simulation/domains/information_contract.md`, and any git history around when
  `KnowledgeFact`/`KnowledgeModelService` were introduced, for evidence of which of the two
  possibilities above was actually intended.
- If intended-but-unconsumed: identify the real, concrete consumer this should feed (threat
  estimation? query-response staleness checks? something else entirely?) and produce a plan for
  wiring it — this ticket's own Investigate/Plan phases, not a follow-up ticket, since the
  disposition itself determines the shape of the fix.
- If deliberately write-only: update `belief_and_detour_contract.md` to state that explicitly
  (currently implicit — the doc describes `KnowledgeFact`'s "no decay" behavior but doesn't say
  facts are never read for decisions), and close this ticket with that documentation fix as the
  full scope, no wiring.

## Out of Scope
- `effective_certainty()` itself — already deleted as abandoned
  (`TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION`, done). Re-adding decay
  is not in scope here regardless of this ticket's own disposition; if a real consumer is found and
  decay turns out to matter for it, that is a new, separate design decision, not an automatic
  revival of the deleted function.
- `LeadState`/`decay_stale_leads()` — already confirmed live and correctly wired
  (`TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`), not reopened here.
- Any change to `information_source_profiles` or the query/response routing machinery itself
  (Batch C's own scope) — this ticket is about what happens to facts *after* they're recorded, not
  how they get recorded.
- Sequencing: per peer review, this is post-Batch-D work, ahead of Batches E and F but behind the
  currently in-flight survivor-collision / trust-accumulation / count-expansion wiring fixes.

## Acceptance Criteria
- [ ] A complete, re-verified classification of every real `self_model.knowledge.facts` access in
      `src/`, confirming or correcting the write/passthrough/trace-only finding above.
- [ ] A design-intent determination (intended-but-unconsumed vs. deliberately write-only), with
      real evidence (docs, git history), not inference alone.
- [ ] If intended-but-unconsumed: a concrete plan for the real consumer, with the wiring
      implemented and tested in this ticket.
- [ ] If deliberately write-only: `belief_and_detour_contract.md` updated to state that
      explicitly, closing the ambiguity for future readers.
- [ ] Either disposition: no regression in `tests/unit/cognition/`, `tests/unit/strategic/`.

## Related Tickets
- `TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION` (done — origin of this
  finding)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (done — the broader audit this arc is part of)
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP` (done — the sibling `LeadState` mechanism,
  confirmed live; the contrast that makes this finding legible)

## Related Docs
- `docs/simulation/belief_and_detour_contract.md` (the contract this ticket's disposition may need
  to sharpen)
- `docs/simulation/domains/information_contract.md` (the `KnowledgeFact` model's own contract)
- `docs/plans/deferred_tuning_decisions_register.md` (adjacent register — not where this belongs;
  this is a reachability/wiring question, not a deferred number, per that register's own test)

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up.

## Related Code Areas
- `src/core/self_model.py` (`KnowledgeFact`, `self_model.knowledge.facts`)
- `src/domains/information/assimilation.py` (write path)
- `src/cognition/knowledge_model.py` (write path, `KnowledgeModelService`)
- `src/cognition/self_model_phase.py` (trace-only read)
- `src/engine/pipeline_phases/lead_contradiction.py` (passthrough reconstruction)

## Assumptions / Open Questions
- Whether `KnowledgeFact`s were ever meant to influence decisions directly, or whether `LeadState`
  was always intended as the sole decision-influencing record type with `KnowledgeFact` as pure
  provenance, is the central question this ticket exists to answer — not assumed either way here.
- If the answer turns out to be "intended-but-unconsumed," the real consumer's shape is itself
  unknown and needs real design work during Investigate/Plan, not just a mechanical wiring pass —
  this may turn out to be a bigger ticket than its own current standard-tier estimate once picked
  up.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
