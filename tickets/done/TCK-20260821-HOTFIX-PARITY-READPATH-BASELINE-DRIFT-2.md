---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260821-HOTFIX-PARITY-READPATH-BASELINE-DRIFT-2
phase: done
date: 2026-08-21
tags: [ai, agent-monitoring]
---

# TCK-20260821-HOTFIX-PARITY-READPATH-BASELINE-DRIFT-2

## Title
Fix 2nd recurrence of the parity-readpath real-corpus baseline drift (count 3 -> 4)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tests/tools/test_generate_retro.py::test_parity_index_readpath_call_count_matches_real_corpus_state`
asserts `compute_parity_index_readpath_call_count()` returns `count == 3` against the real
`agent-monitoring/tools.jsonl` corpus — the value set by
`TCK-20260820-HOTFIX-PARITY-READPATH-BASELINE-DRIFT`, the first occurrence of this exact drift
class. Since then, `TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION`'s parity-updater phase
legitimately ran `tools/parity_index.py entry INFRA-366` on 2026-08-21T02:30:02Z, recording a 4th
matching row. The test's own docstring/comment already documents this as expected, welcome drift,
not a bug — the function's own docstring anticipates every future real call site incrementing the
count with zero code change needed. Discovered while triaging a real CI failure on PR #32
(`kernel-concurrency-design-review`, "API / tools / logging" job), which stayed red across 3
consecutive pushes even after fixing an unrelated layer-registry drift and a `docs/REGISTRY.yaml`
staleness gap — confirmed via direct execution of `compute_parity_index_readpath_call_count()`
against the real corpus that the count is now 4, with the 4th example row citing
`TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION`.

## Scope
- Update `test_parity_index_readpath_call_count_matches_real_corpus_state`'s assertion from
  `count == 3` to `count == 4`, with a comment citing the 4th real call-site row as fresh evidence,
  following the exact precedent this same test's own history already documents.

## Out of Scope
- `compute_parity_index_readpath_call_count()` itself — detection logic unchanged, already covered
  by its own synthetic-fixture tests.
- Any other test failure observed in the same CI job — `tests/api/test_live_*`, `tests/cli/*`,
  `tests/observability/*`, and the MCP/gateway-corpus tests remain out of scope, documented as
  environment-dependent soft monitors (`docs/testing/regression_policy.md` §3) or already-confirmed
  pre-existing unrelated noise by `TCK-20260817-STATE-DESIGN-PRIORITY-ORDER`.
- Any change to `agent-monitoring/tools.jsonl` itself — it is an accurate, auto-generated record of
  real tool calls; not touched here.

## Acceptance Criteria
- [x] `test_parity_index_readpath_call_count_matches_real_corpus_state` passes against the real
      current `agent-monitoring/tools.jsonl` corpus.
- [x] The 4th real call-site row is cited as fresh evidence in the test comment.
- [x] `compute_parity_index_readpath_call_count()` itself is unchanged.

## Related Tickets
- TCK-20260820-HOTFIX-PARITY-READPATH-BASELINE-DRIFT (1st occurrence of this exact drift class)
- TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION (source of the 4th real call-site row)
- TCK-20260821-HOTFIX-LAYER-REGISTRY-FRONTEND-BASELINE-DRIFT (sibling fix on the same PR #32 CI triage pass)

## Related Docs
- docs/testing/regression_policy.md (drift-vs-regression decision tree)

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- tests/tools/test_generate_retro.py
- tools/agent-monitoring/generate_retro.py (`compute_parity_index_readpath_call_count`, read-only, not modified)

## Assumptions / Open Questions
None — mechanical fix matching an already-established precedent pattern.

## Implementation Notes
Updated the assertion from `count == 3` to `count == 4` and extended the comment to cite the 4th
real row (`TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION`'s `tools/parity_index.py entry INFRA-366`
call, 2026-08-21T02:30:02Z), matching the exact wording/citation style of the prior fix.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py -k parity_index_readpath -v` — all
passing (the updated real-corpus test plus the synthetic-fixture detection tests, unchanged).

## Files Changed
- tests/tools/test_generate_retro.py

## Completion Summary
Fixed the 2nd recurrence of the parity-readpath real-corpus baseline drift, caused by a legitimate
parity-ledger entry write from an unrelated ticket in the same batch incrementing the real
call-site count from 3 to 4. Mechanical fix matching the established precedent
(`TCK-20260820-HOTFIX-PARITY-READPATH-BASELINE-DRIFT`) exactly; `compute_parity_index_readpath_call_count()`
itself untouched.
