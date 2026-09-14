# Test Plan — TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH

## New / extended coverage
- `tests/unit/world/test_guild_pipeline.py::test_guild_visit_leads` — extended: `detail` parses
  as `"x,y"` floats matching `node.position` exactly.
- `tests/unit/strategic/test_detour_suggestion.py::TestSubjectsMatchMaterialBlocker` (new class,
  4 tests): direct-subject match returns True regardless of `detail` format; `resource_node`
  subject matches any material blocker when `detail` is non-empty; `resource_node` subject does
  NOT match with empty `detail` (existing guard preserved); a mismatched, non-`resource_node`
  subject whose narrative `detail` happens to contain the blocker's subject string as a substring
  no longer matches (regression guard against the removed coincidence).
- `tests/unit/strategic/test_belief_integration.py::TestNonCoordinateLeadDetailIsSkippedNotCrashed`
  (new class, 2 tests): a lead with narrative `detail` (the exact pre-fix shape,
  `"Rumors of iron near (48.0, 12.0)"`) is skipped via the narrow `except`, logged at WARNING
  naming the lead, no ERROR-level log, and is not marked tested; a coordinate-`detail` sibling lead
  on the same entity in the same `fused_strategic_pass` call still confirms normally
  (`tested=True`, `test_outcome="SUCCESS"`) — proves the narrow exception doesn't affect the
  working path.
- `tests/unit/strategic/test_phase6_strategic_cognition.py::test_blocker_inference_and_detour` —
  fixed pre-existing fixture that relied on the removed substring coincidence
  (`lead.subject="(5, 5)"`/`detail="Alternative resource source"` only matched blocker
  `subject="resource"` because "resource" was a substring of the narrative text). Changed to
  `lead.subject="resource"` (the real, intentional connection) with `detail="5.0,5.0"` (a real
  parseable location for the "alternative source" the test's own comment describes). Passing.

## Regression sweep run
`tests/unit/strategic/ tests/unit/world/test_guild_pipeline.py
tests/unit/engine/test_guild_visit_phase.py tests/unit/ai/ tests/architecture/test_guild_action_dormancy.py
tests/unit/cognition/ tests/unit/domains/information/ tests/integration/domains/information/
tests/integration/kernel/ tests/certification/` (`-m "not slow and not extra_slow"`) —
691 passed, 1 skipped (unrelated), 6 deselected (slow), no failures.

No regressions found beyond the one pre-existing test fixed above, which relied on the exact
coincidental behavior this ticket's own fix correctly removes.
