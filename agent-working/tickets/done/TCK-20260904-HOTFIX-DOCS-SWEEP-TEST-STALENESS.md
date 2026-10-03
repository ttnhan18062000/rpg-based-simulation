---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-DOCS-SWEEP-TEST-STALENESS
phase: done
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-HOTFIX-DOCS-SWEEP-TEST-STALENESS

## Title
Fix 2 test-only regressions from `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`: a doc-content test broken by the docs sweep's section-heading rename, and a test hardcoding the retired `agent-monitoring/events.jsonl` path

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Discovered in the same CI-triage pass as the sibling ticket `TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-CONSTANTS` — both test-only, no production code change needed, kept separate since they're a distinct root-cause class (stale test expectations, not a dead-constant crash).

**Regression 1 — `tests/tools/test_current_run_sidecar_orchestrator.py::test_schema_doc_documents_tools_jsonl_phase_agent_fields`.** This test does `doc.index("## \`agent-monitoring/tools.jsonl\`")` to locate the field-reference table in `docs/agent-monitoring/schema.md`. Confirmed by direct read: this heading was renamed to `## \`tools\` (\`agent-monitoring/data/YYYY-Www/tools.jsonl\`)` at some point during the epic's own docs work (children 1/3/7 all touched this file). The actual documented content the test cares about — the `phase`/`agent` field rows and the `TCK-20260719-LIVE-PHASE-AGENT-LABEL` citation — is confirmed still present and correct; only the heading string the test's `.index()` call looks for is stale.

**Regression 2 — `tests/tools/test_duration_utils.py::test_real_corpus_simq_depth_social_reproduces_documented_gap`.** Hardcodes `_REPO_ROOT / "agent-monitoring" / "events.jsonl"` directly (a literal top-level path, `git rm`'d by `TCK-20260903-MONITORING-DATA-MIGRATION`). This is the same class of gap already accepted for `test_agent_monitoring_manifest.py`/`test_agent_monitoring_legacy_reader.py` in child 2's own Deviations section — but this specific file was never named in any of children 1-7's own test inventories, so it fell through.

## Scope
- `tests/tools/test_current_run_sidecar_orchestrator.py`: update the `.index()` call's target string to match the real, current `schema.md` heading. Do not change `schema.md` itself — the rename is the epic's own correct, intentional docs work; the test's literal-string expectation is what's stale.
- `tests/tools/test_duration_utils.py`: repoint the hardcoded `agent-monitoring/events.jsonl` read to a multi-week glob over `agent-monitoring/data/*/events.jsonl` (matching the established pattern every other consumer fix in this epic used), filtering for the same `run_id == "TCK-20260710-SIMQ-DEPTH-SOCIAL"` rows the test already checks for.
- Confirm both tests pass again against the real current corpus/docs state.

## Out of Scope
- Any change to `docs/agent-monitoring/schema.md`'s content or heading — already correct, intentional.
- The 2 production-code bugs (`retrieval_events.py`, `retrieval_baseline_metrics.py`/`skill_usage_metric.py`) — tracked separately in `TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-CONSTANTS`.
- The 24 confirmed environment-noise CI failures and the 8 already-tracked codex/replay failures — out of scope here, same as the sibling ticket.

## Acceptance Criteria
- [x] `test_schema_doc_documents_tools_jsonl_phase_agent_fields` passes against the real, current `schema.md`.
- [x] `test_real_corpus_simq_depth_social_reproduces_documented_gap` passes against the real, current multi-week corpus, still finding the same 10 real `TCK-20260710-SIMQ-DEPTH-SOCIAL` event rows it did before (content parity, not just "doesn't crash").

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (the epic whose docs sweep/migration caused both regressions)
- TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-CONSTANTS (sibling hotfix, production-code bugs found in the same CI triage session)

## Related Docs
`docs/agent-monitoring/schema.md` — read-only reference for Regression 1's fix, not modified.

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
- `tests/tools/test_current_run_sidecar_orchestrator.py`
- `tests/tools/test_duration_utils.py`

## Assumptions / Open Questions
- `layer: observability` matches this repo's established pattern.

## Implementation Notes

**Regression 1 fix** (`tests/tools/test_current_run_sidecar_orchestrator.py`): read the real current
`docs/agent-monitoring/schema.md` (lines 369-418) and confirmed the `## \`tools\`
(\`agent-monitoring/data/YYYY-Www/tools.jsonl\`)` heading, the `phase`/`agent` field rows in the
`### Fields` table, and the `TCK-20260719-LIVE-PHASE-AGENT-LABEL` citation (in the `phase` row's
nullability description) are all still present and correct between that heading and the next
`### Write locking` heading. Updated the single stale `.index()` call in
`test_schema_doc_documents_tools_jsonl_phase_agent_fields` from
`"## \`agent-monitoring/tools.jsonl\`"` to the real current heading string. No other test in the
file referenced the old heading string. `schema.md` itself was not touched.

**Regression 2 fix** (`tests/tools/test_duration_utils.py`): replaced the single hardcoded
`_REPO_ROOT / "agent-monitoring" / "events.jsonl"` read (a path retired by
`TCK-20260903-MONITORING-DATA-MIGRATION`) with a loop over
`sorted((_REPO_ROOT / "agent-monitoring" / "data").glob("*/events.jsonl"))` — the same glob pattern
already used by `tests/tools/test_agent_monitoring_manifest.py`. Filtering logic (per-line JSON
parse, `run_id == "TCK-20260710-SIMQ-DEPTH-SOCIAL"`) is otherwise unchanged. Verified against the
real corpus with a direct grep across all 15 `agent-monitoring/data/*/events.jsonl` shards: all 10
matching rows live in `agent-monitoring/data/2026-W28/events.jsonl` (every other shard has 0), so
`len(events) == 10` still holds — confirmed by actual data, not assumed.

## Test Summary
Ran the exact scope required by the ticket:
```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_duration_utils.py -v
```
Result: 35 passed, including both previously-failing tests
(`test_schema_doc_documents_tools_jsonl_phase_agent_fields`,
`test_real_corpus_simq_depth_social_reproduces_documented_gap`).

Broader sweep:
```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_duration_utils.py -k "not slow" -q
```
Result: 34 passed, 1 deselected (no slow-marked tests in this scope; deselection is the `not slow`
filter finding nothing to exclude beyond marker bookkeeping — no new breakage from this change).

## Files Changed
- `tests/tools/test_current_run_sidecar_orchestrator.py` — updated stale `.index()` heading string.
- `tests/tools/test_duration_utils.py` — repointed hardcoded legacy path to multi-week glob.
- `tickets/inprogress/TCK-20260904-HOTFIX-DOCS-SWEEP-TEST-STALENESS.md` — this file (status,
  acceptance criteria, implementation notes, test summary, completion summary).

No staging artifacts (`staging_artifacts/{ticket_id}/`) — hotfix tier, none required or created.

## Completion Summary
Fixed 2 stale test expectations left over from `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`'s docs
sweep and data migration. `test_current_run_sidecar_orchestrator.py` was looking for a
`schema.md` section heading that had been intentionally renamed; repointed its `.index()` call to
the real current heading with the underlying documented content (field rows, citation) verified
unchanged. `test_duration_utils.py` hardcoded a literal `agent-monitoring/events.jsonl` path that
the epic's migration had `git rm`'d; repointed it to glob across
`agent-monitoring/data/*/events.jsonl` using the same pattern already established elsewhere in the
repo, and confirmed against the real corpus that the same 10 historical rows are still found (now
in the `2026-W28` shard). No production code changed; both fixes are test-only.
