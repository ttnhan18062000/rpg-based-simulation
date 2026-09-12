---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE
phase: done
date: 2026-09-12
tags: [information, cognition, self-model]
---

# TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE

## Title
Fixed: a raw `ActionIntent` could be written into `entity.identity.latest_intent_results` (typed
`List[IntentResult]`) with the shipped default flag state, crashing `StrategicWorkQueue.build()`
mid-tick in real simulations at real population density — routed to a dedicated, correctly-typed
field instead

## Status
DONE

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
- [x] `entity.identity.latest_intent_results` can no longer contain a non-`IntentResult` object
      after a real tick where Branch B routes a self-model query, in both
      `ENABLE_INFORMATION_INTENT_EXECUTION` states. Verified structurally (no write path ever
      merges `pending_action_intent` toward `latest_intent_results`) and empirically (new
      end-to-end regression test materializing through the real `extract_patches()` →
      `IdentityPatch.apply()` path with the flag OFF).
- [x] `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability` (and any
      other test crashing on the identical `AttributeError`) passes or fails only on its own real
      grade/score assertions, never on this `AttributeError`. Confirmed: now passes cleanly, a real
      200-tick run.
- [x] The CI-blind-spot gap (slow lane not covered by routine CI, so a real crash on `main` went
      unnoticed) is written down somewhere durable — this ticket's own notes at minimum, a
      `regression_policy.md` pointer if that's the more correct home. Added
      `docs/testing/regression_policy.md` §12.
- [x] No regression in `tests/unit/domains/information/`, `tests/integration/domains/information/`,
      `tests/unit/config/test_phase10_feature_flags.py`,
      `tests/integration/test_world_profile_feature_flag_guardrail.py`. All pass (133 in the
      combined targeted run; see Test Summary for the full sweep).

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
- `docs/testing/regression_policy.md` §12 (new — the CI-blind-spot finding, added per this
  ticket's own AC)
- `docs/parity_ledger/infrastructure.yaml` INFRA-270 (the flag/phase this bug routes around;
  unchanged — the flag's own default and semantics are untouched by this fix)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-
  STRATEGIC-WORK-QUEUE/` (this ticket's own investigation.md/plan.md/test_plan.md)

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
- ~~Which of the three candidate fixes is correct~~ **Resolved**: candidate 3, determined with
  evidence and peer-endorsed before implementation. See Implementation Notes.
- The right structural fix for the underlying "`-m slow` lane isn't routinely watched" gap is left
  genuinely open — `docs/testing/regression_policy.md` §12 flags it without resolving it, per that
  section's own explicit scope boundary.

## Implementation Notes
Determined the fix via three independent evaluations, not the first plausible one, per this
session's established discipline for scope decisions:
1. **Flip `ENABLE_INFORMATION_INTENT_EXECUTION` default ON** — rejected. `TCK-20260713-SIMQ-
   COGNITION-PIPELINE-WIRE`'s own Out of Scope explicitly deferred this as a live gameplay-behavior
   change needing its own calibration validation; smuggling it into a crash fix would be exactly
   the "pick the plausible option without confirming intent" trap this whole audit has hit before.
2. **Defensive typing in `StrategicWorkQueue.build()`** — rejected. `latest_intent_results` has 5
   real readers assuming `IntentResult` shape (`work_queue.py`, `intelligence.py` x3,
   `entity_inspector.py`, `state_presenter.py`); a fix at one site leaves the other four equally
   exposed. Peer review additionally flagged `state_presenter.py:128` as an API-boundary exposure
   (a raw/malformed object reaching a public read surface), sharpening why this candidate is
   insufficient even as a stopgap.
3. **Chosen: stop `InformationBeliefPhase` Branch B writing the wrong type at all.** Confirmed via
   `isinstance(x, ActionIntent)` grep: exactly one write site, one intended consumer
   (`InformationIntentExecutionPhase`). The write site already discriminates the type at
   construction (`if isinstance(result, ActionIntent):`), so the fix routes an existing
   distinction into a correctly-typed container rather than introducing a new one.

Implementation: `EntityUpdate` gained `pending_action_intent: Optional[ActionIntent] = None`
(`src/core/updates.py`, under a `TYPE_CHECKING`-guarded import to avoid the existing circular
import `action_intent.py` has on this module), wired into `is_noop()`/`merge()`. Branch B
(`phase.py`) writes to this field instead of `intent_results`.
`InformationIntentExecutionPhase` reads it directly and — per peer review's explicit instruction —
its own stripping filter was deleted entirely rather than kept "just in case": once the redirect
lands, no `ActionIntent` can reach `intent_results` by construction, so the filter would have been
defensive code guarding a condition that can no longer occur, the exact pattern this whole audit
batch has spent multiple tickets removing elsewhere. No test required the filter's continued
presence after deletion — confirming the redirect actually closed the hole rather than leaving a
gap the filter was silently still covering.

Verified the new regression test's own methodology, not just its "it passes" result: reproduced
the OLD write shape (`EntityUpdate(intent_results=[ActionIntent(...)])`) through the identical real
`extract_patches()` → `IdentityPatch.apply()` → `StrategicWorkQueue.build()` path in a standalone
script and confirmed it still crashes with the identical `AttributeError` — proof the test would
have caught the original bug, not a vacuous pass regardless of the fix.

**Second occurrence of this exact bug class**: `TCK-20260907-INFORMATION-INTENT-EXECUTION-RESULT-
TYPE-MISMATCH` (referenced in the pre-existing test file this ticket rewrote) already fixed a
"mixed intent_results list" variant of this same problem once, by adding the stripping filter this
ticket now deletes. That fix assumed `InformationIntentExecutionPhase` would run; it didn't account
for the flag being off by default, so the underlying type-safety gap survived and resurfaced here.
Worth noting as a real instance of "the second fix that removes what the first fix's own filter
was defending against" — not a criticism of the earlier ticket, whose narrower scope was reasonable
at the time, but a confirmation that candidate 3 (fixing the write site, not the read site) is the
fix that actually closes the class of bug rather than one more instance of it.

Added `docs/testing/regression_policy.md` §12 documenting the CI-blind-spot finding (the `-m slow`
lane not being part of routine CI, so a real crash sat on `main` unnoticed) per peer review's
explicit instruction not to let it evaporate into prose with no durable trace. Left the actual
structural remediation (scheduled slow-lane runs, a lighter always-on smoke subset, or something
else) as an explicitly open question — out of this ticket's own scope to resolve.

## Test Summary
**Real CI failures found and fixed post-push, before landing**: the first PR push failed 2 real CI
jobs.
1. `Integration` — `tests/integration/domains/test_fused_loop.py` had 2 more assertions on the old
   `intent_results`-based shape, missed on the first grep sweep because this file checks
   `.kind == "ASK_INFORMATION"` without the literal string `"ActionIntent"` anywhere in it (my
   first sweep grepped for files containing both `"intent_results"` and `"ActionIntent"`
   together). Fixed the same way as the other 3 files; re-ran a broader grep pattern
   (`"intent_results"` combined with `"ASK_INFORMATION"`/`"routed_query"`/`"Branch B"` instead of
   `"ActionIntent"`) afterward and found no further instances.
2. `API / tools / logging` — `tests/tools/test_entity_event_ledger.py::
   test_entity_ledger_covers_every_entity_update_field` correctly flagged the new
   `pending_action_intent` field as missing a ledger entry. Added it to the same exclusion set
   `intent_results` itself is already in, for the identical reason (a same-tick transient routing
   signal, not an independently-observable durable mutation).
Both confirmed via real CI job failures, not assumed; both fixed and re-verified locally against
the exact CI commands before re-pushing.

- `tests/unit/engine/test_information_intent_execution_phase.py` — fully rewritten (the old shape
  no longer exists to test); 6 passed, including a new
  `test_action_intent_execution_phase_clears_pending_action_intent_after_execution` and
  `test_action_intent_execution_phase_leaves_intent_results_untouched`.
- `tests/integration/domains/information/test_phase5_information_belief_phase.py` — 3 existing
  assertions updated from `intent_results[0]` to `pending_action_intent`; 1 new end-to-end
  regression test added
  (`test_routed_action_intent_never_reaches_durable_latest_intent_results_flag_off`) — real
  materialization through `extract_patches()`/`IdentityPatch.apply()`/`StrategicWorkQueue.build()`
  with the flag OFF, the exact real-world crashing condition. 6 passed.
- `tests/integration/domains/information/test_phase5_branch_b_realworld.py` — 1 assertion updated;
  3 passed (parametrized across 3 seeds).
- Standalone verification script (not committed): reproduced the OLD write shape through the same
  real materialization path — confirmed it still crashes with the identical `AttributeError`,
  validating the new regression test's own methodology against a known-bad input.
- `pytest tests/unit/worldassembly/test_corpus_diversity.py::
  test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability -q` — the
  originally-crashing test — now passes (30.87s, a real 200-tick x 3-trial run).
- `pytest tests/unit/domains/information/ tests/integration/domains/information/
  tests/unit/engine/test_information_intent_execution_phase.py
  tests/unit/domains/optimization/test_strategic_work_queue.py
  tests/unit/config/test_phase10_feature_flags.py
  tests/integration/test_world_profile_feature_flag_guardrail.py -q` — 133 passed.
- `pytest tests/unit/core/ tests/integration/pipeline/ tests/unit/domains/optimization/ -m "not
  slow and not extra_slow" -q` (broad sweep for `EntityUpdate` consumers generally) — 471 passed.
- `pytest tests/helpers/assertions.py tests/unit/strategic/test_rejection_backoff.py
  tests/unit/strategic/test_strategic_lifecycle.py tests/unit/strategic/test_strategic_memory_v2.py
  tests/integration/kernel/test_phase10_replay.py tests/integration/kernel/
  test_p1_replay_fidelity.py -q` (remaining files referencing `latest_intent_results`) — 17 passed.
- `tests/api tests/cli tests/tools tests/logging tests/engine tests/observability tests/integration
  -m "not slow and not extra_slow" -q` (the real `Integration` + `API / tools / logging` CI
  commands combined, covering `state_presenter.py:128`, the API-boundary read site) — 3666 passed,
  23 skipped, 1 xfailed, re-run after both real CI failures above were fixed. This is the exact
  final, post-fix confirmation before the PR reported green.

## Files Changed
- `src/core/updates.py` — `EntityUpdate` gains `pending_action_intent`
- `src/domains/information/phase.py` — Branch B writes to the new field
- `src/engine/pipeline_phases/information_intent_execution.py` — reads the new field, stripping
  filter deleted
- `tests/unit/engine/test_information_intent_execution_phase.py` — rewritten
- `tests/integration/domains/information/test_phase5_information_belief_phase.py` — 3 assertions
  updated, 1 new end-to-end regression test added
- `tests/integration/domains/information/test_phase5_branch_b_realworld.py` — 1 assertion updated
- `tests/integration/domains/test_fused_loop.py` — 2 assertions updated (found via a real CI
  `Integration` job failure — missed on the first grep sweep since this file checks `.kind ==
  "ASK_INFORMATION"` without the literal string `"ActionIntent"` anywhere in it)
- `tests/tools/test_entity_event_ledger.py` — added `pending_action_intent` to the field-ledger
  exclusion set (found via a real CI `API / tools / logging` job failure); excluded for the same
  reason `intent_results` itself already is: a same-tick transient routing signal, never merged
  toward durable state, with no independently-observable entity mutation of its own to ledger
- `docs/testing/regression_policy.md` — new §12, CI-blind-spot finding

## Completion Summary
Determined, with evidence rather than the first plausible option, that the real fix for this crash
is to stop `InformationBeliefPhase` Branch B from ever writing a raw `ActionIntent` into the
`IntentResult`-typed `intent_results` field — not to flip an unrelated, deliberately-deferred
feature flag, and not to patch defensively at one of five real read sites (one of which reaches the
API boundary). Implemented via a new, correctly-typed `pending_action_intent` field that no write
path ever merges toward durable state, making the original type violation structurally impossible
rather than merely defended against. Deleted the now-provably-dead stripping filter this fix
obsoletes, rather than leaving it as unverifiable defensive code — the second time this exact class
of bug has been hit (the first fix, `TCK-20260907-INFORMATION-INTENT-EXECUTION-RESULT-TYPE-
MISMATCH`, fixed the read side and left the write side able to resurface it).

Verified end to end: the originally-crashing real 200-tick test now passes; a new regression test
proves the fix through the real apply pipeline, not a mock; that test's own methodology was
independently validated against the known-bad shape to confirm it isn't a vacuous pass. Documented
the structural CI-blind-spot finding (the `-m slow` lane not being part of routine CI) in
`docs/testing/regression_policy.md` §12, deliberately left open as its own unresolved question
rather than assumed away. Zero regressions across 621 tests in the directly-relevant and broader
sweep suites.
