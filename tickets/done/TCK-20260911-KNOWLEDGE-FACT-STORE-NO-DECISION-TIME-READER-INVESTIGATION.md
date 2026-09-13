---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION
phase: done
date: 2026-09-11
tags: [cognition, self-model]
---

# TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION

## Title
Confirmed: the information-assimilation subsystem (`KnowledgeFact`) is inert end to end — facts are
almost never written (two gates, both owned elsewhere) and never read when they are; documented at
its real size rather than built, since no design intent declares a consumer

## Status
DONE

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
- [x] A complete, re-verified classification of every real `self_model.knowledge.facts` access in
      `src/`, confirming or correcting the write/passthrough/trace-only finding above. Confirmed
      unchanged on current `main` via a fresh grep sweep, plus a broader `KnowledgeFact`-type-name
      sweep catching everything the narrower grep could have missed. One correction made: a prior
      ticket's own "real consumers" listing included `cognition_extras.py`, which actually reads
      the sibling `.unknowns` field, not `.facts`.
- [x] A design-intent determination (intended-but-unconsumed vs. deliberately write-only), with
      real evidence (docs, git history), not inference alone. **Neither cleanly** — real
      instrumentation of a 500-tick run found the write side itself never fires
      (`assimilate()`: 0 calls), for two already-known, already-owned-elsewhere reasons. The
      reader-gap is structurally real but practically moot; peer review's own "two competing
      memory models" reframe doesn't apply either, since `KnowledgeFact` and `LeadState` aren't
      competing for the same decisions — one simply never reaches a decision at all. Documented at
      this real, more nuanced size rather than forced into either original framing.
- [ ] ~~If intended-but-unconsumed: a concrete plan for the real consumer~~ N/A — no design intent
      declares a consumer (unlike `JOIN_PARTY`'s own explicit `intent_mapping`), so building one
      would be inventing gameplay design, not completing a declared one. Not done, per explicit
      peer-review instruction.
- [x] If deliberately write-only: `belief_and_detour_contract.md` updated to state that
      explicitly, closing the ambiguity for future readers. Updated to state the subsystem is
      inert end to end (not merely "no reader") and to flag the downstream consequence for whoever
      eventually revisits `ENABLE_INFORMATION_INTENT_EXECUTION`.
- [x] Either disposition: no regression in `tests/unit/cognition/`, `tests/unit/strategic/`. N/A —
      no `src/`/`tests/` code changed; documentation-only disposition.

## Related Tickets
- `TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION` (done — origin of this
  finding)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (done — the broader audit this arc is part of)
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP` (done — the sibling `LeadState` mechanism,
  confirmed live; the contrast that makes this finding legible)
- `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION` (done — its own "real consumers"
  listing for `KnowledgeFact` included `cognition_extras.py`, corrected here: that file reads the
  sibling `.unknowns` field, not `.facts`)
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (open — one of the two
  real reasons `assimilate()` never fires in Campaign mode: `state.pending_information_responses`
  is never threaded)
- `TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE`
  (done — confirmed `ENABLE_INFORMATION_INTENT_EXECUTION` default OFF, the second reason
  `assimilate()` never fires via the `ASK_INFORMATION` ActionIntent path)
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (new — filed from this
  investigation's own search for a real consumer; an independent, always-empty decision input,
  not conditioned on this ticket's own disposition)

## Related Docs
- `docs/simulation/belief_and_detour_contract.md` — updated: the information-assimilation
  subsystem is inert end to end, stated at its real size, with the downstream consequence for
  `ENABLE_INFORMATION_INTENT_EXECUTION` named explicitly.
- `docs/simulation/domains/information_contract.md` (the `KnowledgeFact` model's own contract —
  read, not modified; its own description of the model itself was already accurate)
- `docs/plans/deferred_tuning_decisions_register.md` (confirmed, per the ticket's own original
  note: this is a reachability question, not a deferred number — correctly not used here)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION/`
  (this ticket's own investigation.md/plan.md/test_plan.md, including the full real-instrumentation
  evidence trail)

## Related Code Areas
- `src/core/self_model.py` (`KnowledgeFact`, `self_model.knowledge.facts` — unmodified)
- `src/domains/information/assimilation.py` (write path, confirmed real but never called in
  practice — unmodified)
- `src/cognition/knowledge_model.py` (write path, `KnowledgeModelService` — unmodified)
- `src/cognition/self_model_phase.py` (trace-only read — unmodified)
- `src/engine/pipeline_phases/lead_contradiction.py` (passthrough reconstruction — unmodified)
- `src/engine/pipeline.py` (the two real gates confirmed: `pending_information_responses`
  threading, `ENABLE_INFORMATION_INTENT_EXECUTION`)
- `src/cognition/capability_estimate.py` (`CapabilityContext.region_data`/`.enemy_data`, the
  independent always-empty finding filed as its own ticket)

## Assumptions / Open Questions
- ~~Whether `KnowledgeFact`s were ever meant to influence decisions directly, or whether `LeadState`
  was always intended as the sole decision-influencing record type~~ **Resolved, but not as
  cleanly as either original framing**: the honest finding is that the whole subsystem is inert
  end to end for reasons owned elsewhere, so the question of what *should* consult facts is
  currently moot rather than answered either way.
- New, deliberately not chased here: whether `KnowledgeFact` should eventually feed
  `CapabilityContext.region_data`/`.enemy_data` once (a) `ENABLE_INFORMATION_INTENT_EXECUTION` is
  revisited and (b) that ticket determines a real source for those fields. Recorded as an unproven
  observation in both tickets, not a predetermined answer.

## Implementation Notes
No `src/`/`tests/` code changed — a documentation disposition, per peer review's explicit approval
after the real evidence ruled out both of this ticket's own original framings and its "two
competing memory models" reframe. See `stored_artifacts/TCK-20260911-KNOWLEDGE-FACT-STORE-NO-
DECISION-TIME-READER-INVESTIGATION/investigation.md` for the full evidence trail: the re-verified
static reader survey, the real 500-tick instrumented reproduction showing `assimilate()` fires zero
times, the git chronology, and the "name the missing behaviour" test applied honestly (no
observable gap exists today, because the fact that would demonstrate one is never created under
real default settings).

Filed `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` as its own, independent, P2
ticket for the one concrete, real defect found along the way — an always-empty decision input,
confirmed via direct grep of every real `CapabilityContext` construction site. Deliberately did
NOT propose `KnowledgeFact` as its source: no design doc declares that correspondence, so recording
it as an explicitly unproven observation is the correct scope, not a decision to make unilaterally.

## Test Summary
No new tests — documentation-only disposition. Verification is the investigation's own real
evidence: a fresh grep re-verification (confirms the original finding, with one correction to a
prior ticket's imprecise citation) and a real, instrumented 500-tick `frontier_living_world`
reproduction (seed 7) proving `InformationAssimilationService.assimilate()` is called zero times in
practice, traced to two already-known, already-owned-elsewhere gates.

## Files Changed
- `docs/simulation/belief_and_detour_contract.md` — new section stating the subsystem is inert end
  to end, at its real size
- `tickets/todos/TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY.md` — new

## Completion Summary
Re-verified the ticket's own premise before investigating further, per peer review's explicit
instruction — the "no decision-time reader" finding holds unchanged on current `main`, with one
correction to a prior ticket's imprecise consumer citation. Went further than the static survey:
real 500-tick instrumentation found the write side itself essentially never fires either, tracing
to two already-known, already-owned-elsewhere gates (`pending_information_responses` never
threaded in Campaign mode; `ENABLE_INFORMATION_INTENT_EXECUTION` default off). This makes the
reader-gap structurally real but practically moot — there is rarely a fact in existence to read.

Applied peer review's "name the missing behaviour" test honestly rather than as a hurdle to clear:
found a real, concrete, plausible candidate (`KnowledgeFact`'s own `"danger_rating"` fact type,
fully wired on the query/routing side, paired with `CapabilityContext.region_data`/`.enemy_data`,
a real decision-time structure shaped for exactly this data) — but confirmed no observable gap
exists *today*, because the fact that would demonstrate one is never created under real default
settings. Declined to build the correspondence between the two, since no design doc declares it —
building it would be inventing gameplay design, matching the exact caution peer review raised
against repeating the party-formation shape without an equivalent declared intent.

Closed on the honest, real-size finding: the information-assimilation subsystem is inert end to
end, for reasons this ticket doesn't own, with no currently-observable gameplay consequence.
Documented that explicitly in `belief_and_detour_contract.md` rather than building a speculative
consumer. Filed the one concrete, independent, actionable defect found along the way
(`CapabilityContext`'s always-empty decision inputs) as its own separate ticket, strictly as the
finding, with the `KnowledgeFact` shape-match recorded as an explicitly unproven observation, not a
proposal.
