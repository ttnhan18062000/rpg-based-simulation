---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW
artifact_type: investigation
tags: [observability, debugging, data-quality]
---

# Investigation — TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW

## Root cause
`compute_kgmcp_cache_efficiency_metrics()` (`tools/agent-monitoring/generate_retro.py:783`)
computes `coverage_rate = total_events / search_calls_total`, where:
- `total_events` derives from `access_log_rows`, which `main()` always passes as the **full,
  unfiltered** `retrieval_cache_access_log` corpus (`all_kgmcp_access_log = read_cache_access_log()`)
  regardless of `--days`/`--week`/`--all` — documented and deliberate, per `generate()`'s own
  docstring (access-log rows are attributed via the `.claude/current_run` sidecar at call time,
  not any `runs.jsonl` timestamp the period filters operate on).
- `search_calls_total` derives from `build_search_count_section(tools or [])`, where `tools` IS
  period-scoped by `main()` (filtered to the run_ids of the reporting window).

Numerator = all-time, denominator = period-scoped → for any period shorter than the full corpus,
the ratio is inflated by however much cache-event history predates the reporting window. On the
live 2026-W35 retro this produced 1059.3% (350 hits + 222 writes = 572 all-time events over 54
period-scoped search calls).

## Two fix directions considered
(a) Scope the numerator to the same window as the denominator, using `retrieval_cache_access_log`'s
real per-row `ts` column.
(b) Scope the denominator to all-time, using `all_tools` — the unfiltered `tools.jsonl` corpus
`main()` already loads once and threads through `generate()` for a different purpose (the
Zero-Invocation Skill Flags section, which is deliberately an all-time question).

**Chosen: (b).** Rationale: `all_tools` is already loaded and threaded through the exact call path
that needs it (`main()` → `generate()`), with zero new I/O or timestamp-domain conversion. Direction
(a) would require converting `retrieval_cache_access_log.ts` (raw `time.time()` epoch floats) into
the same domain as `runs.jsonl`'s ISO `start_ts` cutoff/week-boundary comparisons `main()` already
performs — real, but more invasive, plumbing for no additional correctness benefit here, since both
directions land on the same all-time-vs-all-time reconciliation.

## Existing "never period-sliced" caveat does not block this fix
`generate()`'s own docstring already explains `kgmcp_access_log` is deliberately never
period-sliced — but that rationale is about **run_id-based linkage** (access-log rows aren't
reliably linkable to `runs.jsonl` by run_id), not about whether a `ts`-based or all-time-matched
denominator can be constructed. Confirmed this reading does not conflict with direction (b).

## API path cross-check
`src/api/agent_ops_dashboard/ingest.py`'s own `compute_retro_metrics()` call already passes
`tools=self._tools_all` (the all-time corpus, not period-scoped, per that file's own inline
comment) for its own period-selection semantics — so the JSON API path's `coverage_rate` was
**already** all-time-vs-all-time before this fix and needed no change. The bug is specific to the
CLI Markdown report path (`generate_retro.py`'s `main()`/`generate()`), which does period-scope
`tools`.

## Backward compatibility
`compute_kgmcp_cache_efficiency_metrics()` gains `all_tools: list[dict] | None = None`, preferring
it over `tools` only when explicitly supplied — every pre-existing direct-call test (160 in
`test_generate_retro.py` before this ticket) continues to receive identical behavior since none of
them pass `all_tools`. Verified: full suite green (160 passed) before adding new tests, and 164
passed after.
