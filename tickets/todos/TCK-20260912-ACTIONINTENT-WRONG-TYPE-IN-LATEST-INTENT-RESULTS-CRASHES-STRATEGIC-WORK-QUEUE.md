---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE
phase: open
date: 2026-09-12
tags: [information, cognition, self-model]
---

# TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE

## Title
A raw `ActionIntent` can be written into `entity.identity.latest_intent_results` (typed
`List[IntentResult]`) with the shipped default flag state, crashing `StrategicWorkQueue.build()`
mid-tick in real simulations at real population density — and the slow-gated test lane that
would catch it doesn't run in CI

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while verifying `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`'s own
fix caused no regressions. `tests/unit/worldassembly/test_corpus_diversity.py::
test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability` crashes mid-run:

```
src/systems/strategic_systems/work_queue.py:55: in build
    intent_fail = any(not r.accepted for r in entity.identity.latest_intent_results)
AttributeError: 'ActionIntent' object has no attribute 'accepted'
```

**Confirmed pre-existing on unmodified `main`, unrelated to that ticket's fix** — reproduced
identically via `git stash` (reverting the count-expansion changes) and re-running the exact same
test against clean `main`: same crash, same traceback. Real cause was initially mis-attributed to
the count-expansion fix in a peer-review exchange; corrected once the counterfactual was actually
run instead of assumed.

**Root cause, fully diagnosed, not guessed** — the crashing code path is already self-documented
in the codebase:

- `entity.identity.latest_intent_results: List["IntentResult"]` (`src/core/state.py:601`) is typed
  for `IntentResult` objects only.
- `InformationBeliefPhase` Branch B (self-model query-routing, `src/domains/information/
  phase.py:94-101`) can construct a raw `ActionIntent` (`InformationIntentResolver.resolve()`
  returning one) and store it directly into `EntityUpdate(intent_results=[result], ...)` —
  `intent_results` itself typed `List[IntentResult]` (`src/core/updates.py:718`) but populated here
  with the wrong type.
- `EntityUpdate.merge()` (`src/core/updates.py:779`) concatenates `intent_results` additively, with
  no type filtering.
- `IdentityPatch.apply()` (`src/engine/patches.py:236-247`) — the sole authoritative writer for
  `latest_intent_results` — carries whatever is in `update.intent_results` straight into durable
  state, again with no type filtering anywhere in this path.
- `InformationIntentExecutionPhase` (`src/engine/pipeline_phases/information_intent_execution.py`)
  exists specifically to strip raw `ActionIntent` entries from `intent_results` *before* this
  happens — its own module docstring predicts this exact crash verbatim: "Without this, they
  survive unchanged..., get installed as entity.identity.latest_intent_results, and crash
  StrategicWorkQueue.build() (reads .accepted unconditionally off every entry, a field only real
  IntentResult objects have)." But that phase is gated `ENABLE_INFORMATION_INTENT_EXECUTION`,
  **default OFF** (`docs/parity_ledger/infrastructure.yaml` INFRA-270; confirmed via
  `tickets/done/TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE.md` that "off by default" here just
  follows the standard cautious-default convention for new, not-yet-activated phases — not a
  documented reason the write itself is safe).

**So in the shipped default configuration, this is not a rare edge case gated behind an opt-in
flag — it is a durable-state type violation that fires whenever Branch B successfully routes a
self-model query for any entity**, which needs enough real population/content for that condition to
occur. Confirmed via `isinstance(x, ActionIntent)` grep: `InformationIntentExecutionPhase` is the
*only* code that ever expects to find an `ActionIntent` mixed into `intent_results` — nothing else
in `src/` reads it from there, meaning removing that possibility at the source has no other
consumer to preserve.

**Why this has stayed invisible**: `tests/unit/worldassembly/test_corpus_diversity.py` is
`@pytest.mark.slow`, so the routine test/CI lane skips it — confirmed via peer review checking the
marker directly. `main` has been carrying this crash for as long as Branch B has existed and real
corpus worlds have had enough population for it to fire, and nothing routinely watching CI would
see it. This is a structural gap, not a one-off miss: whoever next runs the slow lane (`-m slow`)
against a real corpus world hits a wall of failures with no context connecting them to this cause.
That gap itself is bigger than this one bug and is disclosed here rather than silently absorbed —
see Related Docs/`docs/testing/regression_policy.md` for where it should be tracked structurally.

**The blast radius is not internal-only — it reaches the API boundary.** `src/api/presenters/
state_presenter.py:128` also reads `entity.identity.latest_intent_results` directly. A wrongly-typed
`ActionIntent` reaching that presenter is not just an internal crash risk — it is a raw domain
object (or a malformed shape) leaking toward a public read surface, which this repo's own
Architecture Rule explicitly forbids ("API/routes present shaped read models through presenters/
schemas, not raw domain objects"). This sharpens why candidate 2 (defensive typing at one call
site) is insufficient even as a stopgap: the exposure isn't confined to `StrategicWorkQueue`.

**Independent significance for the Dormant Mechanism thread**: this is the same "previously
unreachable in practice, now reachable" pattern this whole audit arc keeps finding — except here
the trigger is a *correct* population-density improvement (the classic `WorldCompiler.compile()`
pipeline already expands `count` correctly, so any real corpus world at real density already
exercises this), not an investigation deliberately probing for it. Directly corroborates
`TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`'s central premise: real population
density changes which code paths actually execute, for better (mechanisms that finally fire) and
for worse (bugs that finally fire too).

## Scope
- **Determine the fix, don't assume the obvious one** — three real candidates, evaluated with
  evidence before picking:
  1. Flip `ENABLE_INFORMATION_INTENT_EXECUTION` to default ON. The phase exists specifically to
     strip these. But it is a live production behavior change (self-model query routing actually
     executing against the world), not a bug fix — `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE`'s
     own Out of Scope explicitly deferred turning it on in any shipped profile as future work
     requiring its own calibration validation. Flipping it as a side effect of fixing this crash
     would be exactly the "picking the plausible option without confirming intent" trap this whole
     audit has hit before.
  2. Make `StrategicWorkQueue.build()` defensive (`isinstance(r, IntentResult)` filter, or
     `getattr(r, "accepted", False)`) before reading `.accepted`. Cheapest — but leaves a
     wrongly-typed value sitting in a field the Durable State Rule (`CLAUDE.md`) requires be
     properly typed, and every *other* reader of `latest_intent_results`
     (`src/systems/strategic_systems/intelligence.py:207,224,1306`,
     `src/observability/live/entity_inspector.py:118`,
     `src/api/presenters/state_presenter.py:128`) would need the same defensive treatment or stay
     equally exposed.
  3. **Determined (peer-reviewed, endorsed): stop `InformationBeliefPhase` Branch B from writing a
     raw `ActionIntent` into the `IntentResult`-typed `intent_results` field at all.** A new,
     separate, explicitly-typed `EntityUpdate` field (`pending_action_intent: Optional[ActionIntent]
     = None`) that `InformationIntentExecutionPhase` reads directly, never merged into
     `entity.identity.latest_intent_results` regardless of flag state. This is the only option that
     makes the type violation structurally impossible rather than defended-against at every read
     site, matching `CLAUDE.md`'s Durable State Rule directly. Confirmed low blast radius two ways:
     (a) the only write site is `phase.py:94-101`, the only consumer expecting `ActionIntent` there
     is `InformationIntentExecutionPhase` itself; (b) the write site already discriminates the type
     at the exact point of construction (`phase.py:98`, `if isinstance(result, ActionIntent):`) —
     the redirect routes an *existing* distinction into the right container, it does not introduce
     a new one.
- **Implementation requirement, not optional cleanup**: once Branch B writes to the new field,
  `InformationIntentExecutionPhase` must (a) read the new field instead of `ent_upd.intent_results`
  (line 52), and (b) **delete its own stripping filter** (line 62's `remaining_results = [r for r in
  ent_upd.intent_results if not isinstance(r, ActionIntent)]`) — once the fix lands, no
  `ActionIntent` can ever enter `intent_results` by construction, so that filter becomes dead
  defensive code guarding a condition that can no longer occur. Leaving it in place would recreate,
  inside the very fix for this bug, the exact "defensive code nobody can prove is still load-bearing"
  pattern this whole audit batch has spent multiple tickets removing elsewhere. Document in this
  ticket's own Implementation Notes why deletion is safe (the type can no longer reach that
  container by construction) — if any test still requires the filter after the redirect, that is
  itself evidence the redirect didn't fully close the hole, and must be brought back to peer review
  before proceeding, not silently patched around.
- Add a real regression test proving a routed `ActionIntent` no longer reaches
  `entity.identity.latest_intent_results` (with the flag both ON and OFF), and that
  `StrategicWorkQueue.build()` no longer crashes on an entity that had Branch B route a query for
  it this tick.
- Re-run `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability` and the
  rest of `tests/unit/worldassembly/test_corpus_diversity.py -m slow` to confirm the crash is gone
  (does not require every other failure in that file to also be resolved — see Related Tickets).
- Note the CI-blind-spot structural gap (slow lane not routinely run/watched) in this ticket's own
  Implementation Notes or a pointer into `docs/testing/regression_policy.md`, per peer review's
  explicit instruction not to let it evaporate into prose with no durable trace.

## Out of Scope
- Fixing every other pre-existing failure in `test_corpus_diversity.py` — tracked separately (see
  Related Tickets). This ticket only needs to fix the crash blocking that one test (and any other
  entity that would hit the identical `.accepted` AttributeError).
- The NARRATIVE-pillar grade/score baseline drift found in the same investigation — a different,
  separately-tracked finding (deterministic C→A-style drift from correct population density, not a
  crash), routed to its own ticket.
- Turning on `ENABLE_INFORMATION_INTENT_EXECUTION` for any shipped world profile, unless Scope's own
  candidate-1 investigation concludes that's the right fix with real evidence — not decided here in
  advance.

## Acceptance Criteria
- [x] Fix-approach determination recorded with real evidence for all three candidates, not the
      first plausible one — reported to peer review before implementation, per this session's
      established scope-decision discipline. **Determined and peer-endorsed: candidate 3** (see
      Scope). Independently re-verified by peer review: 5 real consumers of
      `latest_intent_results` assume `IntentResult` shape; exactly one write site and one intended
      consumer for the `ActionIntent` case.
- [ ] `entity.identity.latest_intent_results` can no longer contain a non-`IntentResult` object
      after a real tick where Branch B routes a self-model query, in both
      `ENABLE_INFORMATION_INTENT_EXECUTION` states.
- [ ] `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability` (and any
      other test crashing on the identical `AttributeError`) passes or fails only on its own real
      grade/score assertions, never on this `AttributeError`.
- [ ] The CI-blind-spot gap (slow lane not covered by routine CI, so a real crash on `main` went
      unnoticed) is written down somewhere durable — this ticket's own notes at minimum, a
      `regression_policy.md` pointer if that's the more correct home.
- [ ] No regression in `tests/unit/domains/information/`, `tests/integration/domains/information/`,
      `tests/unit/config/test_phase10_feature_flags.py`,
      `tests/integration/test_world_profile_feature_flag_guardrail.py`.

## Related Tickets
- `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE` (the ticket during whose
  verification this was found — confirmed via `git stash` to be unrelated to that ticket's own fix,
  which lands independently)
- `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION` (this finding directly corroborates its
  central premise: real population density changes which code paths execute)
- `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` (added the flag and the stripping phase this bug
  routes around; its own Out of Scope already flagged that turning the flag on needs its own
  validation, relevant to candidate 1 above)
- `TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD` (confirmed, over a month prior, that
  `test_corpus_diversity.py` already had "12 failures/1 error... pre-existing via git stash" —
  this bug has likely been present at least that long, unnoticed for the same structural reason)
- `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH` (most recent prior comprehensive
  triage of this same test file's failures; did not previously catalog this specific crash, since
  its own triage batch didn't include `urban_political_selfmodel_probe_seed42_200t`)
- New NARRATIVE-drift ticket filed alongside this one (see working_log/REGISTRY once filed) for the
  separate, non-crash grade/score drift found in the same verification pass

## Related Docs
- `docs/testing/regression_policy.md` (this ticket's own CI-blind-spot finding likely belongs here
  as a new subsection, alongside the existing §9 corpus_diversity triage precedent)
- `docs/parity_ledger/infrastructure.yaml` INFRA-270 (the flag/phase this bug routes around)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/systems/strategic_systems/work_queue.py` (`StrategicWorkQueue.build()`, the crash site)
- `src/domains/information/phase.py` (`InformationBeliefPhase` Branch B, the write site)
- `src/engine/pipeline_phases/information_intent_execution.py` (the flag-gated stripping phase that
  should but doesn't always run)
- `src/core/updates.py` (`EntityUpdate.intent_results`, `.merge()`)
- `src/engine/patches.py` (`IdentityPatch.apply()`, the sole authoritative writer of
  `latest_intent_results`)
- `src/systems/strategic_systems/intelligence.py` (three more real readers of
  `latest_intent_results` that assume `IntentResult` shape)
- `src/domains/optimization/feature_flags.py` (`ENABLE_INFORMATION_INTENT_EXECUTION`)

## Assumptions / Open Questions
- Which of the three candidate fixes is correct is the central, deliberately-unresolved question
  this ticket exists to answer with evidence — peer review's own lean is candidate 3, but explicitly
  flagged as a lean, not a decision.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
