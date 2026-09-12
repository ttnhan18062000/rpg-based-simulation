---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW
phase: done
date: 2026-08-26
tags: [observability, debugging, data-quality]
---

# TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW

## Title
Fix or honestly disclose KGMCP coverage_rate exceeding 100% from a numerator/denominator window mismatch

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
coverage_rate in tools/agent-monitoring/generate_retro.py divides an all-time cache-event numerator by a period-scoped search-call denominator, producing values such as 1059.3% -- a metric that no longer means what it claims. retrieval_cache_access_log rows carry a real per-row ts REAL NOT NULL column and read_cache_access_log() already returns rows ordered by ts with no since/until filter, so period-scoping the numerator is technically feasible; alternatively, main() already loads an all-time all_tools list separately (used for the Zero-Invocation Skill Flags section) that could serve as an all-time denominator instead. Both fix directions are feasible and currently undone; the metric must either be reconciled to a single consistent time window or the >100% case must be honestly and explicitly disclosed rather than silently capped or hidden. This is a distinct, previously undiscovered defect from the near-zero ~1.4% coverage_rate issue TCK-20260824-RETRO-METRIC-CAVEATS already addressed.

## Scope
- Investigate and choose one of two fix directions: (a) scope the cache-event numerator to the same time window as the period-scoped search_calls_total denominator using retrieval_cache_access_log's per-row ts column, or (b) compute search_calls_total from the all-time all_tools list (already loaded separately in main() for the Zero-Invocation Skill Flags section) so both sides of the ratio are all-time.
- If neither reconciliation direction is adopted, add an explicit caveat -- distinct from the two existing caveats -- to _kgmcp_verdict()'s docstring, its parts.append() text, compute_kgmcp_cache_efficiency_metrics()'s docstring, and the rendered '## KGMCP Cache Efficiency' Markdown section, stating coverage_rate can exceed 100% due to the window mismatch and that this is not an error signal.
- Ensure coverage_rate is never silently capped/floored/clamped in the numeric path, whichever direction is chosen.
- Update docs/parity_ledger/infrastructure.yaml's INFRA-379 entry with v2_evidence reflecting the chosen fix direction.
- Update the frozen full-text golden fixtures in tests/tools/test_generate_retro.py (e.g. _FIXED_CORPUS_EXPECTED_REPORT) if rendered KGMCP-section text changes as a result.

## Out of Scope
- Any change to KGMCP capability or investment itself -- already ratified as 'keep as-is, no further investment' by TCK-20260824-KGMCP-KEEP-OR-DEPRECATE. This ticket is reporting-metric honesty only.
- The separate, already-addressed near-zero (~1.4%) coverage_rate failure mode from TCK-20260824-RETRO-METRIC-CAVEATS (a different root cause: two independently-instrumented tools).

## Acceptance Criteria
- [x] Either: coverage_rate's numerator (cache events) is scoped to the same time window as the period-scoped search_calls_total denominator using retrieval_cache_access_log's per-row ts column, verified by a new test where total cache events > search_calls_total under mismatched raw inputs no longer produces coverage_rate > 1.0 once both are window-matched; OR search_calls_total is computed from the all-time all_tools list (already loaded separately in main() for the Zero-Invocation Skill Flags section) to match the all-time numerator, verified by a corresponding test. **Chose the latter (direction b).**
- [x] If neither reconciliation direction is adopted, _kgmcp_verdict()'s docstring... — N/A, direction (b) was adopted.
- [x] A test confirms coverage_rate is never silently capped/floored/clamped anywhere in the numeric path -- the raw uncapped value renders even when > 1.0.
- [x] docs/parity_ledger/infrastructure.yaml's INFRA-379 entry (the KGMCP Cache Efficiency parity entry) is updated with v2_evidence reflecting whichever fix direction is chosen.

## Related Tickets
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD
- TCK-20260824-RETRO-METRIC-CAVEATS
- TCK-20260705-RETRO-METRIC-ACCURACY
- TCK-20260824-KGMCP-KEEP-OR-DEPRECATE

## Related Docs
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
- stored_artifacts/TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW/{plan,investigation,test_plan}.md

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/retrieval_cache.py
- tests/tools/test_generate_retro.py

## Assumptions / Open Questions
- Confirmed: the existing 'never period-sliced' rationale in generate()'s docstring concerns
  run_id-based linkage, not timestamp-based window scoping -- does not block direction (b).
- Confirmed: none of test_generate_retro.py's frozen golden-text fixtures exercise a
  tools/all_tools mismatch, so none required updating (full suite green both before and after,
  160 → 164 passed with 4 new tests, zero fixture edits needed).
- Confirmed: src/api/agent_ops_dashboard/ingest.py's own compute_retro_metrics() call already
  passes tools=self._tools_all (all-time), so its coverage_rate was already correct and needed
  no change.

## Implementation Notes
Adopted fix direction (b): `compute_kgmcp_cache_efficiency_metrics()` gained an `all_tools`
parameter, preferring it over the period-scoped `tools` for the coverage denominator when
supplied (falls back to `tools` otherwise, preserving exact prior behavior for the 160
pre-existing direct-call tests). Threaded `all_tools` through `compute_retro_metrics()` and
`generate()`'s existing call chain — `main()` already loads and passes `all_tools` to `generate()`
for the Zero-Invocation Skill Flags section, so no CLI-level change was needed. See
`stored_artifacts/TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW/investigation.md` for the full root
cause and direction-(a)-vs-(b) tradeoff, and `plan.md` for the step-by-step implementation record.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py -q -m "not slow"` -- 164 passed (160
pre-existing + 4 new), 0 failed. `.venv/bin/python3 -m pytest tests/tools/test_agent_ops_dashboard_stats.py -q -m "not slow"`
-- 19 passed (confirms the JSON API path, unaffected by this fix, still works). Parity ledger YAML
re-validated via `yaml.safe_load()` -- 397 entries, zero duplicate IDs.

## Files Changed
- `tools/agent-monitoring/generate_retro.py` -- `compute_kgmcp_cache_efficiency_metrics()`,
  `compute_retro_metrics()`, `generate()` all gain/thread the new `all_tools` parameter for the
  coverage-rate denominator.
- `tests/tools/test_generate_retro.py` -- 4 new tests.
- `docs/parity_ledger/infrastructure.yaml` -- INFRA-379 entry extended with this fix's evidence.

## Completion Summary
Fixed the confirmed root cause of KGMCP `coverage_rate` exceeding 100%: an all-time cache-event
numerator was being divided by a period-scoped search-call denominator. Reconciled both sides to
the same all-time window by preferring the already-loaded, unfiltered `all_tools` corpus for the
denominator, with zero new I/O and full backward compatibility for existing callers/tests. The
JSON dashboard API path was investigated and confirmed already correct (no change needed there).
`coverage_rate` is never capped — a genuinely-uncapped all-time ratio still renders its real value.
