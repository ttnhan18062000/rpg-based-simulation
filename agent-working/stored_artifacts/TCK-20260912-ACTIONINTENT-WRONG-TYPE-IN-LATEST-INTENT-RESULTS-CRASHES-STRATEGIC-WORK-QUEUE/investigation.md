# Investigation — TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE

## Root cause (fully diagnosed before this ticket was filed — see its own Request Summary)
`InformationBeliefPhase` Branch B (`src/domains/information/phase.py`) constructed a raw
`ActionIntent` and stored it directly into `EntityUpdate.intent_results`, a field typed
`List[IntentResult]`. `EntityUpdate.merge()` concatenates `intent_results` additively with no type
filtering; `IdentityPatch.apply()` — the sole authoritative writer of
`entity.identity.latest_intent_results` — carries whatever is in `update.intent_results` straight
into durable state, also with no type filtering. `InformationIntentExecutionPhase` existed
specifically to strip raw `ActionIntent` entries before this happened, but is gated
`ENABLE_INFORMATION_INTENT_EXECUTION`, default OFF — so in the shipped default configuration, any
tick where Branch B successfully routes a self-model query writes a wrongly-typed value into a
durable, `IntentResult`-typed field.

## Fix-approach determination (peer-reviewed before implementation, per this ticket's own AC)
Three candidates evaluated with evidence, not the first plausible one:
1. Flip `ENABLE_INFORMATION_INTENT_EXECUTION` default ON — rejected. `TCK-20260713-SIMQ-COGNITION-
   PIPELINE-WIRE`'s own Out of Scope explicitly deferred this as a live gameplay-behavior change
   needing its own calibration validation, not something to smuggle in via an unrelated crash fix.
2. Defensive typing in `StrategicWorkQueue.build()` — rejected. Confirmed via grep that
   `latest_intent_results` has 5 real readers total (`work_queue.py`,
   `intelligence.py:207/224/1306`, `entity_inspector.py:118`, `state_presenter.py:128`) all
   assuming `IntentResult` shape; a fix at one site leaves the other four equally exposed. Also
   confirmed `state_presenter.py:128` means the wrong type can reach the API boundary — a
   violation of this repo's own Architecture Rule ("APIs present shaped read models... not raw
   domain objects"), not just an internal crash risk.
3. **Chosen**: stop Branch B writing the wrong type at all. Confirmed via `isinstance(x,
   ActionIntent)` grep that `InformationIntentExecutionPhase` is the only code anywhere in `src/`
   that ever expects an `ActionIntent` inside `intent_results` — one write site
   (`phase.py`), one intended consumer. The write site already discriminates the type at
   construction time (`if isinstance(result, ActionIntent):`), so redirecting it to a dedicated
   field routes an existing distinction rather than introducing a new one — a smaller change than
   it first appears.

## Implementation
- `EntityUpdate` (`src/core/updates.py`) gains `pending_action_intent: Optional[ActionIntent] =
  None`, handled in both `is_noop()` and `merge()` (last-write-wins, matching the existing
  `self_model_bundle_set`/`cognition_bundle_set` pattern for single-value "set" fields). No write
  path (`extract_patches()`, `IdentityPatch`) ever reads this field, so it structurally cannot
  reach `latest_intent_results`.
- `InformationBeliefPhase` Branch B writes to `pending_action_intent` instead of `intent_results`.
- `InformationIntentExecutionPhase` reads `pending_action_intent` instead of filtering
  `intent_results`, and its own stripping filter is deleted — per peer review's explicit
  instruction, since once the redirect lands there is nothing left to strip. If any test still
  required that filter after the redirect, that would be evidence the redirect didn't fully close
  the hole; no such case was found (see Test Summary).

## Verification the fix is actually complete, not just plausible
Wrote a standalone script reproducing the OLD write shape directly (`EntityUpdate(entity_id=1,
intent_results=[ActionIntent(...)])`), materialized it through the real `extract_patches()` →
`IdentityPatch.apply()` path, and called `StrategicWorkQueue.build()` on the result — confirmed it
still crashes with the identical `AttributeError`, proving the new regression test's own methodology
is validated against a known-bad input, not vacuously passing. Then confirmed the NEW write shape
(`pending_action_intent=`) through the same materialization path does not crash and
`latest_intent_results` never contains an `ActionIntent`.

The original crashing test, `tests/unit/worldassembly/test_corpus_diversity.py::
test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability`, now passes cleanly
end to end (a real 200-tick run, not a mock).
