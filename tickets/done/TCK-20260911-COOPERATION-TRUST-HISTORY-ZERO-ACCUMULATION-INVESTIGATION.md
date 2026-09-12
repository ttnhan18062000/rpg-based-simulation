---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION
phase: done
date: 2026-09-11
tags: [cognition, social, observability]
---

# TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION

## Title
`entity.social.trust_history` produced zero entries across 2470 real `cooperation_event`s —
determined to be two dead trust-writing mechanisms plus two live-but-party-gated ones (party
formation never occurred); repaired the one confirmed inline-shortcut bug, transferred "trust
demonstrably accumulates" to `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Surfaced during `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`: grief's mid-episode trigger
(`EventExtractor.detect_grief_triggers()`) requires some alive entity's real
`entity.social.trust_history` toward a newly-dead entity to meet `ALLY_TRUST_THRESHOLD=0.30`. A
real 500-tick `frontier_living_world` episode produced 4 real deaths and 2470 real
`cooperation_event`s, yet a direct check of every alive entity's `trust_history` toward each dead
entity — at the real point of death, not inferred — found it **uniformly empty for the entire
run**. That result closed the grief investigation as inconclusive (the trigger's own precondition
was never met, not evidence the detection code is broken) but left open a real, more consequential
question this ticket exists to answer.

**This is not the usual "unwired path" shape** — the chain looks complete end to end, unlike prior
findings in this arc (`decay_stale_leads`, the raid-discard stub):
- `src/systems/social_systems/cooperation/services.py:350-372` computes **real** trust deltas
  (concrete values observed: `0.08`, `0.22`, `-0.25`, `-0.75` — not placeholders or zero).
- `src/systems/social_systems/cooperation/phase.py:156` builds a real `SocialUpdate` from them
  (`new_trust = dict(soc_up.trust_delta)`).
- `src/systems/social_systems/relationships.py:39` applies them
  (`for eid, delta in update.trust_delta.items()`).

Every step in the chain is real, non-stub code, and yet the end state — `trust_history` as
actually read by `entity.social.trust_history` — never carries an entry. Something between
"computed" and "applied" (or between "applied" and "read back") drops it, or a gate somewhere in
this chain rarely/never opens under real gameplay conditions. **Neither hypothesis is confirmed —
this ticket exists to determine which, not to assume either one.**

**Why this matters beyond grief.** Every other real consumer of trust reads it as
`entity.social.trust_history.get(other_id, 0.5)` — defaulting to a neutral value
(`src/systems/social_systems/appraisal.py:53,526`, `party.py:60`, `party_composition.py:126`).
Those consumers behave plausibly either way, since a missing key silently reads as "neutral trust"
rather than erroring or looking obviously wrong. Grief is the one real consumer that requires an
actual populated entry (no default it can fall back to and still mean something), which is why it
is the mechanism that surfaced this at all. If trust genuinely never accumulates in practice, then
`SocialBond`, cooperation partner selection, and the episode-boundary `relationship_scores`
carry-forward may all be silently operating on defaults rather than real history — with nothing
about their own behavior looking visibly wrong from the outside, the same "documented/complete-
looking but never actually populated" pattern this whole follow-up arc has repeatedly found.

## Scope
- Trace the real trust-delta chain end to end with direct instrumentation (not just reading code):
  confirm `CooperationService`'s own computed deltas actually reach `phase.py`'s `SocialUpdate`
  construction for a real cooperation event, confirm that `SocialUpdate` actually reaches
  `RelationshipService.process_update()` (`relationships.py:39`) unmodified, and confirm the
  resulting `trust_history` dict is actually written back onto the entity state the pipeline
  carries forward tick-to-tick (not silently discarded by an unrelated reconstruction elsewhere,
  matching this arc's own recurring shape of a downstream constructor dropping a field it never
  explicitly threads).
- Identify whether there's a gate (a condition, a feature flag, a cadence/skip check) between any
  of these steps that rarely or never opens under real gameplay conditions, distinct from an
  outright unwired/dropped-field bug.
- Determine the real, confirmed root cause — do not stop at "confirmed reproducible," go one level
  further to "confirmed why," matching this whole batch's own established standard.
- Once root-caused: decide the fix approach and route it through peer review before implementing,
  given the blast radius this ticket's own Request Summary already identifies (every real trust
  consumer, not just grief).

## Out of Scope
- `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`'s own scope — already closed with real
  evidence; this ticket investigates the deeper question that closure surfaced, not a re-litigation
  of that ticket's own grief/nemesis-specific findings.
- Any other real or perceived correctness gap in `cooperation_event` processing beyond trust-value
  accumulation specifically (e.g. partner selection logic, cooperation outcome fairness) — not
  investigated here unless directly implicated by this ticket's own root cause.

## Acceptance Criteria
- [x] Real, direct instrumentation (not code-reading alone) confirms exactly which step in the
      chain — computation, `SocialUpdate` construction, `RelationshipService.process_update()`
      application, or downstream state carry-forward — is where a real trust delta stops reaching
      `entity.social.trust_history` as actually read back. Confirmed via monkeypatch
      instrumentation on every real trust-writing function found (not just the three originally
      cited) across a real 500-tick reproduction (same scenario/seed as the original finding):
      `RelationshipService.process_update()` and `SocialPatch.apply()` (the sole authoritative
      gateway for any `SocialUpdate`) were each called **zero times total** across the entire run —
      not zero times with a non-empty `trust_delta`, zero calls of any kind. Nothing is computed
      and then discarded anywhere in this chain; every function that computes a trust_delta applies
      it correctly if it's ever called with one.
- [x] The determination distinguishes "a gate rarely/never opens under real gameplay" from "the
      value is computed but discarded/dropped by a downstream constructor" — cleanly, with real
      evidence for each of the four real trust-writing functions found (two more than the ticket's
      original three):
      - **Genuinely unwired dead code** (not a gate — zero callers anywhere in `src/`, confirmed by
        static grep and the live 500-tick run): `CooperationLearningService.learn()`, and
        `SocialAppraisalSystem.recalibrate_trust()`'s own real intended path via
        `StrategicIntelligenceSystem.process_outcome()` (itself also zero callers).
      - **A gate that never opened in this real run** (a real, live, correctly-wired mechanism
        whose precondition wasn't met, not a dropped value): the party-cohesion-collapse trust
        penalty (`CooperationPhase.execute()`) and the same-party-betrayal penalty
        (`SocialAppraisalSystem.process_betrayal()`, called from `combat_actions.py`) — both
        require `state.groups` to be non-empty, which it was not, for the entire 500-tick run.
- [x] The original ticket's own central framing was itself wrong and is corrected here, not
      quietly dropped: it stated "this is not the usual unwired-path shape... the chain looks
      complete end to end." It isn't — `CooperationLearningService.learn()` has zero callers
      anywhere, the exact "unwired path" shape this whole audit arc has repeatedly found elsewhere.
- [x] Determined, with real evidence rather than a guess, whether `learn()` and `recalibrate_trust()`
      are alternatives or complements (a real trap this batch has hit three times before): **not
      the same job.** `recalibrate_trust()`/`process_outcome()` predates `CooperationLearningService`
      by roughly a month (git chronology: `appraisal.py` 2026-04-28 vs. `cooperation/services.py`
      2026-05-30), lives in a different, generic subsystem (`StrategicIntelligenceSystem`, a bare
      `subject_id`+`success: bool` signature), has zero test coverage anywhere, and no design-doc
      reference was found for it. `CooperationLearningService.learn()` is Phase 7's own explicitly-
      specified "Task 11 — Implement cooperation outcome learning"
      (`docs/archive/entity-enhance/entity_enhance_phase7.md`), has a real dedicated passing TDD
      test file matching its own spec exactly, and — the deciding evidence — that same design doc
      states explicitly (line 280): "Cooperation logic is isolated from raw social contract
      appraisal." The project's own stated intent is separation, not supersession.
      `recalibrate_trust()` is a separate, adjacent, likely-different-domain question, correctly
      not touched by this ticket's own fix.
- [x] If a real bug is confirmed: a fix-approach decision is obtained via peer review before
      implementation, and a real test confirms the fix. **Confirmed and fixed, narrowly**: the
      party-cohesion-collapse branch's own inline `trust_delta = -0.25` hardcode exactly matches
      `CooperationLearningService.learn()`'s own "abandoned" outcome computation — not a
      coincidence, a hand-copied shortcut for a call that should have been made, silently dropping
      `grudge_delta` (0.3) in the process. Replaced with a real call to
      `CooperationLearningService.learn()`, confirmed via
      `test_party_cohesion_leader_lost_writes_trust_and_grudge_via_real_learning_service`
      (`tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`) — the fix and the
      test are both asserted against the real service's own output, not a re-derived literal.
- [x] **This repair alone does not make trust demonstrably accumulate in a real run** — it's the
      same live gate (party formation) that never opened in the reproduction, confirmed unchanged
      by this fix. Per peer review's own explicit direction, this ticket closes on its own real,
      narrower claim rather than overclaiming; "trust demonstrably accumulates in a real run" is
      transferred, as its own explicit Acceptance Criteria line (not a note), to
      `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`.

## Related Tickets
- `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` (origin of this finding — closed with the
  grief mid-episode leg recorded inconclusive; this ticket investigated the open question that
  closure deliberately did not chase further, per its own scope)
- `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION` (filed from this ticket's own finding
  — owns the "trust demonstrably accumulates" acceptance bar transferred explicitly from here, and
  the deeper keystone question of whether party formation is ever reachable at all)
- `TCK-20260912-CONTRACT-EXPIRY-ALWAYS-RESOLVES-SUCCESS-REGARDLESS-OF-OUTCOME` (filed from this
  ticket's own search for a real cooperation-outcome signal; explicitly declined to wire trust
  through that path, since its `success=True` hardcode would have produced meaningless uniformly-
  positive trust values)

## Related Docs
- `docs/archive/entity-enhance/entity_enhance_phase7.md` (Phase 7's own design spec for
  `CooperationLearningService` — "Task 11," including the explicit "Cooperation logic is isolated
  from raw social contract appraisal" statement that settled the alternatives-vs-complements
  question)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION/
  investigation.md` (the full real-reproduction investigation trail)

## Related Code Areas
- `src/domains/cooperation/services.py` (`CooperationLearningService.learn()`,
  `CooperationOutcomeEvent` — real path corrected from `src/systems/social_systems/cooperation/
  services.py`, a stale citation in this ticket's own original Request Summary)
- `src/domains/cooperation/phase.py` (`CooperationPhase.execute()` — both the main per-entity
  decision loop, which never touches trust, and the party-cohesion-collapse branch, now fixed)
- `src/systems/social_systems/relationships.py` (`RelationshipService.process_update()` — correct
  when reached, confirmed by direct code read)
- `src/engine/patches.py` (`SocialPatch.apply()` — the sole authoritative gateway any
  `SocialUpdate` must pass through; confirmed zero calls in the real reproduction)
- `src/systems/social_systems/appraisal.py` (`SocialAppraisalSystem.recalibrate_trust()`,
  `.process_betrayal()` — one dead, one live-but-gated)
- `src/systems/strategic_systems/intelligence.py` (`StrategicIntelligenceSystem.process_outcome()`
  — `recalibrate_trust()`'s own only real caller, itself dead)
- `src/engine/domain/combat_actions.py` (real, live caller of `process_betrayal()`, gated on
  same-party friendly fire)
- `src/observability/event_extractor.py` (`detect_grief_triggers()`, the real consumer that
  surfaced this originally)

## Assumptions / Open Questions
- ~~Whether the root cause is a rarely-opening gate or a silently-dropped value~~ **Resolved**:
  both, for different functions — see Acceptance Criteria for the full determination.
- ~~Whether `learn()` and `recalibrate_trust()` are alternatives or complements~~ **Resolved**:
  neither — different domains, deliberately isolated by the project's own design intent. Not
  alternatives to choose between, not complements needing both wired for this ticket's purpose.
- **New, deliberately not chased here**: is party formation itself ever reachable under real
  conditions? Filed as its own ticket, since this question's blast radius (party cohesion, leader
  dynamics, `FORM_PARTY`, both live trust writers, plausibly `SocialBond.role`) is bigger than this
  ticket's own trust-specific scope.
- **New, deliberately not chased here**: does `resolve_contract_outcome()`'s own hardcoded
  `success=True` matter for cooperation's own recruitment contracts specifically? Filed as its own
  ticket, since it's a different social axis (`bonds`/`heroism`/`notoriety`, not `trust_history`)
  and a real design decision (what signal should drive contract resolution), not an incidental
  drop.

## Implementation Notes
Investigated with real, direct instrumentation throughout, per peer review's explicit "reproduce,
don't just trace" steer — every claim in this ticket's own Acceptance Criteria is backed by a real
500-tick reproduction (same scenario, same seed as the original finding), not code-reading alone.

Found the original ticket's own three cited files had a stale path prefix
(`src/systems/social_systems/cooperation/`) — the real files live under `src/domains/cooperation/`.
Corrected in Related Code Areas rather than silently used without flagging.

Found two more real trust-writing functions beyond the three the ticket named
(`SocialAppraisalSystem.recalibrate_trust()`/`.process_betrayal()`), and traced
`recalibrate_trust()`'s own real caller (`StrategicIntelligenceSystem.process_outcome()`) to
confirm it is ALSO dead code, not reachable in practice despite being "reachable in principle."

Determined `learn()`/`recalibrate_trust()` are not alternatives using three independent lines of
evidence together (git chronology, design-doc provenance, test coverage) rather than picking the
more plausible reading — this session's arc has hit that exact trap (treating a plausible
mechanism as the finding without testing it) at least twice before.

Found the real, non-guessed trigger for `learn()`'s "abandoned" outcome type by noticing the
inline `-0.25` in `phase.py`'s party-cohesion-collapse branch exactly matched `learn()`'s own
computed value for that outcome type — not assumed to be a coincidence, and correct: replacing it
with a real `learn()` call also picks up `grudge_delta`, which the inline version silently dropped.

Explicitly declined to guess `learn()`'s trigger for "success"/"rescue"/"betrayal" — the closest
real candidate (`ContractService.process_active_contracts()`'s contract-expiry resolution) was
investigated and found disqualified on two independent grounds (writes a different social axis;
its own `success` flag is hardcoded `True` with a self-disclosed gap) rather than wired anyway.
Filed as its own ticket instead of guessing.

## Test Summary
- `pytest tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ tests/unit/social/
  -q` — 325 passed (existing suite entirely unaffected by the fix).
- `test_party_cohesion_leader_lost_writes_trust_and_grudge_via_real_learning_service` (new,
  `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`) — 1 passed. Constructs
  a real `LEADER_LOST` party-cohesion-collapse scenario, runs the real `CooperationPhase.execute()`,
  and asserts both `trust_delta` and `grudge_delta` match `CooperationLearningService.learn()`'s
  own real output exactly — not a re-derived literal, the actual service's return value.
- Real 500-tick instrumented reproduction (`frontier_living_world`, seed 7, matching the original
  finding's own scenario exactly) — the primary investigative evidence for this ticket's own
  Acceptance Criteria, not a regression-style automated test. Confirmed via direct monkeypatch
  counters: zero calls to `CooperationLearningService.learn()`, zero calls to
  `StrategicIntelligenceSystem.process_outcome()`/`recalibrate_trust()`, zero calls to
  `SocialPatch.apply()`/`RelationshipService.process_update()` (any kind, not just non-empty
  trust_delta), zero groups formed, zero final `trust_history` entries across all 16 entities.
- `tests/integrity/test_no_duplicate_content_blocks.py` — passed.

## Files Changed
- `src/domains/cooperation/phase.py` — party-cohesion-collapse branch now calls
  `CooperationLearningService.learn()` instead of hardcoding `trust_delta = -0.25` inline; picks
  up `grudge_delta` that the old inline version silently dropped; `CooperationOutcomeEvent` import
  added
- `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py` — new real test for the
  fixed branch
- `tickets/todos/TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION.md` — new
- `tickets/todos/TCK-20260912-CONTRACT-EXPIRY-ALWAYS-RESOLVES-SUCCESS-REGARDLESS-OF-OUTCOME.md` —
  new

## Completion Summary
Investigated with real, direct instrumentation rather than tracing, and found the original
ticket's own central claim was wrong: the trust-writing chain is not "complete end to end" —
`CooperationLearningService.learn()`, the rich cooperation-outcome trust computation the ticket
cited as evidence the chain was real, has zero callers anywhere in the codebase. A second,
independent dead-code instance was found one hop away
(`SocialAppraisalSystem.recalibrate_trust()`, reachable in principle only through a caller that is
itself dead). Exactly two real, live, correctly-wired trust-writing mechanisms exist — a party-
cohesion-collapse penalty and a same-party-betrayal penalty — and both require party/group
formation, which never occurred once across a real 500-tick reproduction.

Determined, using git chronology, the original design doc, and test coverage together rather than
picking the more plausible reading, that `learn()` and `recalibrate_trust()` are not alternatives
for the same job — the project's own design doc explicitly states cooperation logic is meant to be
isolated from raw social-contract appraisal. Found the real, non-guessed trigger for `learn()`'s
"abandoned" case (an inline `-0.25` hardcode in the one live party-gated branch, exactly matching
`learn()`'s own computed value) and repaired it, confirmed by a real test asserting against the
service's own output. Explicitly declined to guess a trigger for the "success"/"rescue"/"betrayal"
cases — investigated the closest real candidate, found it disqualified on two independent grounds,
and filed it as its own ticket rather than wiring a decision nothing in the codebase actually
supports.

This ticket closes on its own real, narrower, fully-confirmed claim: two dead trust-writing
mechanisms identified with real evidence, one confirmed inline-shortcut bug repaired, and the
cooperation/appraisal separation confirmed as the project's own intended design rather than
guessed. It does not claim trust demonstrably accumulates in a real run — that repair, while
correct, is itself party-gated and therefore not yet demonstrable. That acceptance bar is
transferred explicitly, as its own Acceptance Criteria line, to
`TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`, which now carries the keystone question
for this entire thread: whether party formation itself is reachable at all.
