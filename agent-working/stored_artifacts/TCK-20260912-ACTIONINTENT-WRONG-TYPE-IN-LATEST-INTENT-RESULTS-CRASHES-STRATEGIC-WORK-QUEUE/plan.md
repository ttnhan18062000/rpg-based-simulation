# Plan — TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE

## Scope decision
Candidate 3 (stop Branch B writing the wrong type), determined with evidence and peer-endorsed
before implementation. See investigation.md for the full evaluation of all three candidates.

## Implementation steps
1. `src/core/updates.py` — add `pending_action_intent: Optional[ActionIntent] = None` to
   `EntityUpdate`, under a `TYPE_CHECKING`-guarded import of `ActionIntent` (avoids the circular
   import `action_intent.py` already has on `updates.py`). Wire into `is_noop()` and `merge()`
   (last-write-wins).
2. `src/domains/information/phase.py` — Branch B writes `pending_action_intent=result` instead of
   `intent_results=[result]`.
3. `src/engine/pipeline_phases/information_intent_execution.py` — read `ent_upd.pending_action_intent`
   instead of filtering `ent_upd.intent_results`; delete the now-dead stripping filter entirely
   (nothing left to strip once the redirect lands).
4. Update existing tests that constructed the old `intent_results=[ActionIntent(...)]` shape:
   `tests/unit/engine/test_information_intent_execution_phase.py` (rewritten),
   `tests/integration/domains/information/test_phase5_information_belief_phase.py`,
   `tests/integration/domains/information/test_phase5_branch_b_realworld.py`.
5. Add a new end-to-end regression test proving the crash is actually gone with the flag OFF (the
   real-world condition), materializing through the real `extract_patches()` →
   `IdentityPatch.apply()` → `StrategicWorkQueue.build()` path, not just the phase-level mock.
6. Verify against the actual originally-crashing test
   (`test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability`).
7. Verify the fix's own regression test would have caught the original bug (reproduce the OLD
   shape directly against the real apply path, confirm it still crashes) — proves the new test
   isn't vacuously passing.

## Guardrails
- Do not flip `ENABLE_INFORMATION_INTENT_EXECUTION`'s default — explicitly rejected candidate,
  a live gameplay-behavior change outside this ticket's own scope.
- Do not leave the stripping filter "just in case" — per peer review, that would recreate the
  exact "unprovably-load-bearing defensive code" pattern this whole audit batch has been removing
  elsewhere. Delete it; if a test still needs it, that's a signal to return to peer review, not to
  quietly keep it.
