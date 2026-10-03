# Test Plan — TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION

## Real reproduction (primary investigative evidence, not a regression test)
- Instrumented monkeypatch reproduction of the exact original scenario
  (`frontier_living_world`, seed 7, 500 ticks) that produced the original 2470-cooperation-
  events/zero-trust-history finding.
- Instrumentation points: `CooperationLearningService.learn`, `RelationshipService.process_update`,
  `PartyCohesionService.evaluate`, `SocialPatch.apply`, `SocialAppraisalSystem.recalibrate_trust`,
  `SocialAppraisalSystem.process_betrayal` — each wrapped to increment a call counter and capture
  samples, cross-checked against each other (three independent instrumentation layers on the same
  write path: `learn()` → `SocialUpdate` construction → `SocialPatch.apply()`) so a zero-call result
  at one layer couldn't be mistaken for a broken patch rather than a real finding.
- Result: zero calls to `learn()`, zero calls to `recalibrate_trust()`/`process_outcome()`, zero
  calls to `SocialPatch.apply()` of any kind (not just zero non-empty `trust_delta`), zero groups
  ever formed (`state.groups` empty for the entire run), zero final `trust_history` entries across
  all 16 entities.

## New test
- `test_party_cohesion_leader_lost_writes_trust_and_grudge_via_real_learning_service`
  (`tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`) — constructs a real
  `LEADER_LOST` party-cohesion-collapse scenario (dead leader, alive member, real `GroupRecord`),
  runs the real `CooperationPhase.execute()`, and asserts the resulting `SocialUpdate.trust_delta`/
  `.grudge_delta` for the member match `CooperationLearningService.learn()`'s own real output for
  the same inputs exactly — not a re-derived literal, the actual service's return value. Also
  explicitly asserts `grudge_delta != 0.0`, confirming this isn't the old hardcoded `-0.25`-only
  branch that silently dropped it.

## Regression suites run
- `pytest tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ -q` — 36 passed
  immediately after the `phase.py` fix, before the new test was added.
- `pytest tests/unit/domains/cooperation/ tests/integration/domains/cooperation/
  tests/unit/social/ -q` — 325 passed, after the new test was added — full relevant suite, no
  regression.
- `pytest tests/integrity/test_no_duplicate_content_blocks.py -q` — 1 passed.

## Acceptance criteria mapping
- Real instrumentation confirming zero calls across the chain → real reproduction above.
- Two-failure-mode determination (dead code vs. never-opening gate) → investigation.md Step 1 +
  Determination section.
- Alternatives-vs-complements determination for `learn()`/`recalibrate_trust()` → investigation.md
  Step 2 (git chronology + design doc + test coverage asymmetry).
- Confirmed-and-fixed inline-duplicate bug → `phase.py` diff + new test above.
- Explicit statement that this repair does not make trust demonstrably accumulate → ticket's own
  Acceptance Criteria + Completion Summary, plus the transferred AC line in
  `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`.
