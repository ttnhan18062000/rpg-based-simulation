---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW
artifact_type: plan
tags: [observability, debugging, data-quality]
---

# Plan — TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW

## Decision
Adopt fix direction (b): reconcile `coverage_rate`'s denominator to all-time via `all_tools`,
not a caveat-only disclosure (not needed — a real reconciliation is adopted) and not direction
(a)'s `ts`-based windowing (more invasive for no added correctness benefit here). See
`investigation.md` for the full rationale.

## Steps
1. `compute_kgmcp_cache_efficiency_metrics(access_log_rows, tools=None, all_tools=None)` — add
   `all_tools` param; `search_calls_total = build_search_count_section(all_tools if all_tools is
   not None else (tools or []))["total"]`. Docstring addendum explaining the window-mismatch root
   cause and the resolution.
2. `compute_retro_metrics(..., all_tools=None)` — add param, forward into the
   `compute_kgmcp_cache_efficiency_metrics()` call.
3. `generate()` — forward its own existing `all_tools` parameter into `compute_retro_metrics()`
   (currently only used for `zif`/Zero-Invocation Flags).
4. No change needed to `main()` — it already loads `all_tools` and passes it into `generate()`.
5. No change needed to `src/api/agent_ops_dashboard/ingest.py` — confirmed already all-time
   correct (see investigation.md's API path cross-check).
6. Tests: unit-level reconciliation test + never-capped-when-genuinely->100% test in the
   `compute_kgmcp_cache_efficiency_metrics` section; integration-level tests proving `all_tools`
   threads through `compute_retro_metrics()` and `generate()` end-to-end.
7. Run full `test_generate_retro.py` + `test_agent_ops_dashboard_stats.py` to confirm zero
   regressions and whether any frozen golden fixture needs updating (none of the existing
   fixtures exercise a `tools`/`all_tools` mismatch, so none require updating — confirmed by full
   green run before any new test was added).
8. Update `docs/parity_ledger/infrastructure.yaml`'s `INFRA-379` entry (per ticket's explicit
   instruction to update that entry, not create a new one) — append `text`/`v2_evidence`
   describing this distinct, later fix, keeping the original caveat-fix history intact.
9. No caveat text needed in `_kgmcp_verdict()`/rendered Markdown (ticket's caveat-only path is
   conditional on "if neither reconciliation direction is adopted" — one is adopted here).

## Acceptance criteria mapping
- AC1 (direction (a) or (b) chosen + verified by test) → Step 1-2, verified by
  `test_compute_kgmcp_cache_efficiency_metrics_coverage_rate_window_matched_via_all_tools`.
- AC2 (caveat if neither direction adopted) → N/A, direction (b) adopted.
- AC3 (never capped) → verified by
  `test_compute_kgmcp_cache_efficiency_metrics_coverage_rate_never_capped_even_when_over_one`.
- AC4 (INFRA-379 updated) → Step 8.
