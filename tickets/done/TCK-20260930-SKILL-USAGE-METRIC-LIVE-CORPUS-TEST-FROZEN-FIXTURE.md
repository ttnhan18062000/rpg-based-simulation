---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-SKILL-USAGE-METRIC-LIVE-CORPUS-TEST-FROZEN-FIXTURE
phase: done
date: 2026-09-30
tags: []
---

# TCK-20260930-SKILL-USAGE-METRIC-LIVE-CORPUS-TEST-FROZEN-FIXTURE

## Title
`test_live_corpus_matches_independently_derived_counts` reads live, branch-dependent monitoring shards

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P3

## Request Summary
`tests/tools/test_skill_usage_metric.py::test_live_corpus_matches_independently_derived_counts`
counts Skill rows from the live `agent-monitoring/data/` shards. Any branch that carries its own
shard with a Skill row changes the count, which broke CI twice in two days (92 vs 91 on PR #271,
and the same fix in PR #270). Both PRs patched the file-discovery glob in
`_independently_derive_counts`; neither fixed the cause. Reported by test-architecture-implementer
(2026-10-01), who also noted the test's derivation now shares the production glob, so it no longer
checks file discovery independently.

## Scope
1. Replace the live-corpus read with a small frozen fixture (only what the assertions need, plus a
   handful of extra rows), covering both shard shapes: bare `<week>/tools.jsonl` and
   `<week>/<id>.tools.jsonl`.
2. Keep one independent check of file discovery: a test that creates both shapes in a tmp dir and
   asserts the production loader finds each, without using the production glob in the oracle.
3. Reconcile the duplicate edit from PRs #270 and #271 first (the same line changed in both, comment
   text differs), so this ticket starts from whichever landed.

## Out of Scope
- Changing `monitoring_shard_paths.shard_paths` or the Skill Usage metric itself.

## Acceptance Criteria
1. The test result no longer changes when a branch adds or removes a shard under `agent-monitoring/data/`.
2. A test pins that both shard shapes are discovered.
3. Existing `test_skill_usage_metric.py` tests pass.

## Related Tickets
- PR #264 (same live-shard class, fixed for other tests)

## Related Docs
- `docs/guidelines/regression_policy.md` (§13.2, wrong-oracle test defect)

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/tools/test_skill_usage_metric.py`
- `tools/agent-monitoring/monitoring_shard_paths.py` (unchanged)


## Assumptions / Open Questions
- Resolved: test-architecture-implementer confirmed Epic D does not cover this follow-up (per handover). PR #270's glob fix is on main; PR #271 (still open) edits the same `_independently_derive_counts` line, which this ticket deletes, so whichever of them merges second takes this version of the file section.


## Implementation Notes
Replaced the live-shard count assertion with a tmp_path fixture holding both shard shapes (`<week>/tools.jsonl`, `<week>/<id>.tools.jsonl`) and literal expected counts (graphify 4, implement-ticket 1, create-tickets 1), so file discovery is checked without the production glob. Added a test that a shard elsewhere does not change the fixture result, and kept a live-corpus smoke test (`> 0`, no pinned count). Removed `_independently_derive_counts` and the unused `_REAL_DATA_DIR`.


## Test Summary
`pytest tests/tools/test_cited_evidence_advisory.py tests/tools/test_proof_plan_advisory.py tests/tools/test_done_checker_static.py tests/tools/test_skill_usage_metric.py`: 15 passed in test_skill_usage_metric.py (frozen fixture, both shard shapes, live smoke).

## Files Changed
- `tests/tools/test_skill_usage_metric.py`

## Completion Summary
The Skill-usage corpus test no longer depends on live shards: a frozen fixture covering both shard shapes with literal counts, plus a live smoke test with no pinned count. Production code unchanged.
